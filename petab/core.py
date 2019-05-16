import pandas as pd
import numpy as np
import libsbml
import sympy as sp
import re
import itertools
import os
import numbers
from collections import OrderedDict
import logging
from . import lint
from . import sbml
from . import parameter_mapping
from typing import Optional, List, Union, Iterable
import warnings


logger = logging.getLogger(__name__)


class Problem:
    """
    PEtab parameter estimation problem as defined by
    - SBML model
    - condition table
    - measurement table
    - parameter table [optional]

    Attributes:
        condition_df: @type pandas.DataFrame
        measurement_df: @type pandas.DataFrame
        parameter_df: @type pandas.DataFrame
        sbml_reader: @type libsbml.SBMLReader
            Stored to keep object alive.
        sbml_document: @type libsbml.Document
            Stored to keep object alive.
        sbml_model: @type libsbml.Model
    """

    def __init__(self,
                 sbml_model: libsbml.Model = None,
                 sbml_reader: libsbml.SBMLReader = None,
                 sbml_document: libsbml.SBMLDocument = None,
                 condition_df: pd.DataFrame = None,
                 measurement_df: pd.DataFrame = None,
                 parameter_df: pd.DataFrame = None):

        self.condition_df: Optional[pd.DataFrame] = condition_df
        self.measurement_df: Optional[pd.DataFrame] = measurement_df
        self.parameter_df: Optional[pd.DataFrame] = parameter_df

        self.sbml_reader: Optional[libsbml.SBMLReader] = sbml_reader
        self.sbml_document: Optional[libsbml.SBMLDocument] = sbml_document
        self.sbml_model: Optional[libsbml.Model] = sbml_model

    def __getstate__(self):
        """Return state for pickling"""
        state = self.__dict__.copy()

        # libsbml stuff cannot be serialized directly
        if self.sbml_model:
            sbml_document = self.sbml_model.getSBMLDocument()
            sbml_writer = libsbml.SBMLWriter()
            state['sbml_string'] = sbml_writer.writeSBMLToString(sbml_document)

        exclude = ['sbml_reader', 'sbml_document', 'sbml_model']
        for key in exclude:
            state.pop(key)

        return state

    def __setstate__(self, state):
        """Set state after unpickling"""
        # load SBML model from pickled string
        sbml_string = state.pop('sbml_string', None)
        if sbml_string:
            self.sbml_reader = libsbml.SBMLReader()
            self.sbml_document = \
                self.sbml_reader.readSBMLFromString(sbml_string)
            self.sbml_model = self.sbml_document.getModel()

        self.__dict__.update(state)

    @staticmethod
    def from_files(sbml_file: str = None,
                   condition_file: str = None,
                   measurement_file: str = None,
                   parameter_file: str = None) -> 'Problem':
        """
        Factory method to load model and tables from files.

        Arguments:
            sbml_file: PEtab SBML model
            condition_file: PEtab condition table
            measurement_file: PEtab measurement table
            parameter_file: PEtab parameter table
        """

        sbml_model = sbml_document = sbml_reader = None
        condition_df = measurement_df = parameter_df = None

        if condition_file:
            condition_df = get_condition_df(condition_file)
        if measurement_file:
            measurement_df = get_measurement_df(measurement_file)
        if parameter_file:
            parameter_df = get_parameter_df(parameter_file)
        if sbml_file:
            sbml_reader = libsbml.SBMLReader()
            sbml_document = sbml_reader.readSBML(sbml_file)
            sbml_model = sbml_document.getModel()

        return Problem(condition_df=condition_df,
                       measurement_df=measurement_df,
                       parameter_df=parameter_df,
                       sbml_model=sbml_model,
                       sbml_document=sbml_document,
                       sbml_reader=sbml_reader)

    @staticmethod
    def from_folder(folder: str, model_name: str = None) -> 'Problem':
        """
        Factory method to use the standard folder structure
        and file names, i.e.
            ${model_name}/
              +-- experimentalCondition_${model_name}.tsv
              +-- measurementData_${model_name}.tsv
              +-- model_${model_name}.xml
              +-- parameters_${model_name}.tsv

        Arguments:
            folder:
                Path to the directory in which the files are located.
            model_name:
                If specified, overrides the model component in the file names.
                Defaults to the last component of `folder`.
        """

        folder = os.path.abspath(folder)
        if model_name is None:
            model_name = os.path.split(folder)[-1]

        return Problem.from_files(
            condition_file=get_default_condition_file_name(model_name, folder),
            measurement_file=get_default_measurement_file_name(model_name,
                                                               folder),
            parameter_file=get_default_parameter_file_name(model_name, folder),
            sbml_file=get_default_sbml_file_name(model_name, folder),
        )

    def get_constant_parameters(self):
        """
        Provide list of IDs of parameters which are fixed (i.e. not subject
        to optimization, no sensitivities w.r.t. these parameters are
        required).
        """
        warnings.warn("This function will be removed in future releases. ",
                      DeprecationWarning)

        columns_set = set(self.condition_df.columns.values)
        return list(columns_set - {'conditionId', 'conditionName'})

    def get_optimization_parameters(self):
        """
        Return list of optimization parameter IDs.

        See get_optimization_parameters.
        """
        return get_optimization_parameters(self.parameter_df)

    def get_dynamic_simulation_parameters(self):
        """See `get_model_parameters`"""
        return get_model_parameters(self.sbml_model)

    def get_observables(self, remove: bool = False):
        """
        Returns dictionary of observables definitions
        See `assignment_rules_to_dict` for details.
        """

        return get_observables(sbml_model=self.sbml_model, remove=remove)

    def get_sigmas(self, remove: bool = False):
        """
        Return dictionary of observableId => sigma as defined in the SBML
        model.
        This does not include parameter mappings defined in the measurement
        table.
        """

        return get_sigmas(sbml_model=self.sbml_model, remove=remove)

    def get_noise_distributions(self):
        """
        See `get_noise_distributions`.
        """
        return get_noise_distributions(
            measurement_df=self.measurement_df)

    @property
    def x_ids(self) -> List[str]:
        """Parameter table parameter IDs"""
        return list(self.parameter_df.reset_index()['parameterId'])

    @property
    def x_nominal(self) -> List:
        """Parameter table nominal values"""
        return list(self.parameter_df['nominalValue'])

    @property
    def lb(self) -> List:
        """Parameter table lower bounds"""
        return list(self.parameter_df['lowerBound'])

    @property
    def ub(self) -> List:
        """Parameter table upper bounds"""
        return list(self.parameter_df['upperBound'])

    @property
    def x_fixed_indices(self) -> List[int]:
        """Parameter table non-estimated parameter indices"""
        estimated = list(self.parameter_df['estimate'])
        return [j for j, val in enumerate(estimated) if val == 0]

    @property
    def x_fixed_vals(self) -> List:
        """Nominal values for parameter table non-estimated parameters"""
        return [self.x_nominal[val] for val in self.x_fixed_indices]

    def get_simulation_conditions_from_measurement_df(self):
        """See petab.get_simulation_conditions"""
        return get_simulation_conditions(self.measurement_df)

    def get_optimization_to_simulation_parameter_mapping(
            self, warn_unmapped: bool = True):
        """
        See get_simulation_to_optimization_parameter_mapping.
        """
        return parameter_mapping\
            .get_optimization_to_simulation_parameter_mapping(
                self.condition_df,
                self.measurement_df,
                self.parameter_df,
                self.sbml_model,
                warn_unmapped=warn_unmapped)

    def create_parameter_df(self, *args, **kwargs):
        """Create a new PEtab parameter table

        See create_parameter_df
        """
        return create_parameter_df(self.sbml_model,
                                   self.condition_df,
                                   self.measurement_df,
                                   *args, **kwargs)


def get_default_condition_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"experimentalCondition_{model_name}.tsv")


def get_default_measurement_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"measurementData_{model_name}.tsv")


def get_default_parameter_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"parameters_{model_name}.tsv")


def get_default_sbml_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"model_{model_name}.xml")


def get_condition_df(condition_file_name: str) -> pd.DataFrame:
    """Read the provided condition file into a `pandas.Dataframe`

    Conditions are rows, parameters are columns, conditionId is index.
    """

    condition_df = pd.read_csv(condition_file_name, sep='\t')
    lint.assert_no_leading_trailing_whitespace(
        condition_df.columns.values, "condition")

    try:
        condition_df.set_index(['conditionId'], inplace=True)
    except KeyError:
        raise KeyError(
            'Condition table missing mandatory field `conditionId`.')

    return condition_df


def get_parameter_df(parameter_file_name: str) -> pd.DataFrame:
    """
    Read the provided parameter file into a `pandas.Dataframe`.
    """

    parameter_df = pd.read_csv(parameter_file_name, sep='\t')
    lint.assert_no_leading_trailing_whitespace(
        parameter_df.columns.values, "parameter")

    try:
        parameter_df.set_index(['parameterId'], inplace=True)
    except KeyError:
        raise KeyError(
            'Parameter table missing mandatory field `parameterId`.')

    return parameter_df


def get_measurement_df(measurement_file_name: str) -> pd.DataFrame:
    """
    Read the provided measurement file into a `pandas.Dataframe`.
    """

    measurement_df = pd.read_csv(measurement_file_name, sep='\t')
    lint.assert_no_leading_trailing_whitespace(
        measurement_df.columns.values, "measurement")

    return measurement_df


def sbml_parameter_is_observable(sbml_parameter: libsbml.Parameter) -> bool:
    """
    Returns whether the `libsbml.Parameter` `sbml_parameter`
    matches the defined observable format.
    """
    return sbml_parameter.getId().startswith('observable_')


def sbml_parameter_is_sigma(sbml_parameter: libsbml.Parameter) -> bool:
    """
    Returns whether the `libsbml.Parameter` `sbml_parameter`
    matches the defined sigma format.
    """
    return sbml_parameter.getId().startswith('sigma_')


def get_observables(sbml_model: libsbml.Model, remove: bool = False) -> dict:
    """
    Returns dictionary of observable definitions.
    See `assignment_rules_to_dict` for details.
    """
    observables = sbml.assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_observable,
        remove=remove
    )
    return observables


def get_sigmas(sbml_model: libsbml.Model, remove: bool = False) -> dict:
    """
    Returns dictionary of sigma definitions.

    Keys are observable IDs, for values see `assignment_rules_to_dict` for
    details.
    """
    sigmas = sbml.assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_sigma,
        remove=remove
    )
    # set correct observable name
    sigmas = {re.sub(f'^sigma_', 'observable_', key): value['formula']
              for key, value in sigmas.items()}
    return sigmas


def get_noise_distributions(measurement_df: pd.DataFrame) -> dict:
    """
    Returns dictionary of cost definitions per observable, if specified.

    Looks through all parameters satisfying `sbml_parameter_is_cost` and
    return as dictionary.

    Parameters:
        measurement_df: PEtab measurement table

    Returns:
        {observableId: cost definition}
    """
    lint.assert_noise_distributions_valid(measurement_df)

    # read noise distributions from measurement file
    observables = measurement_df.groupby(['observableId']) \
        .size().reset_index()

    noise_distrs = {}
    for _, row in observables.iterrows():
        # prefix id to get observable id
        id_ = 'observable_' + row.observableId

        # extract observable transformation and noise distribution,
        # use lin+normal as default if none provided
        obs_trafo = row.observableTransformation \
            if 'observableTransformation' in row \
            and row.observableTransformation \
            else 'lin'
        noise_distr = row.noiseDistribution \
            if 'noiseDistribution' in row \
            and row.noiseDistribution \
            else 'normal'
        # add to noise distributions
        noise_distrs[id_] = {
            'observableTransformation': obs_trafo,
            'noiseDistribution': noise_distr}

    return noise_distrs


def parameter_is_scaling_parameter(parameter: str, formula: str) -> bool:
    """
    Returns true if parameter `parameter` is a scaling
    parameter in formula `formula`.
    """

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula / sym_parameter).free_symbols


def parameter_is_offset_parameter(parameter: str, formula: str) -> bool:
    """
    Returns true if parameter `parameter` is an offset
    parameter with positive sign in formula `formula`.
    """

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula - sym_parameter).free_symbols


def get_simulation_conditions(measurement_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a table of separate simulation conditions. A simulation condition
    is a specific combination of simulationConditionId and
    preequilibrationConditionId.

    Arguments:
        measurement_df: PEtab measurement table

    Returns:
        Dataframe with columns 'simulationConditionId' and
        'preequilibrationConditionId'. All-NULL columns will be omitted.
    """
    # find columns to group by (i.e. if not all nans).
    # can be improved by checking for identical condition vectors
    grouping_cols = get_notnull_columns(
        measurement_df,
        ['simulationConditionId', 'preequilibrationConditionId'])

    # group by cols and return dataframe containing each combination
    # of those rows only once (and an additional counting row)
    simulation_conditions = measurement_df.groupby(
        grouping_cols).size().reset_index()

    return simulation_conditions


def get_rows_for_condition(measurement_df: pd.DataFrame,
                           condition: Union[pd.DataFrame, dict]
                           ) -> pd.DataFrame:
    """
    Extract rows in `measurement_df` for `condition` according
    to 'preequilibrationConditionId' and 'simulationConditionId' in
    `condition`.

    Returns
    -------

    cur_measurement_df: pd.DataFrame
        The subselection of rows in `measurement_df` for the
        condition `condition`.
    """
    # filter rows for condition
    row_filter = 1
    # check for equality in all grouping cols
    if 'preequilibrationConditionId' in condition:
        row_filter = (measurement_df.preequilibrationConditionId ==
                      condition['preequilibrationConditionId']) & row_filter
    if 'simulationConditionId' in condition:
        row_filter = (measurement_df.simulationConditionId ==
                      condition['simulationConditionId']) & row_filter
    # apply filter
    cur_measurement_df = measurement_df.loc[row_filter, :]

    return cur_measurement_df


def get_measurement_parameter_ids(measurement_df: pd.DataFrame) -> list:
    """
    Return list of ID of parameters which occur in measurement table as
    observable or noise parameter overrides.
    """

    def unique_preserve_order(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def get_unique_parameters(series):
        return unique_preserve_order(
            itertools.chain.from_iterable(
                series.apply(split_parameter_replacement_list)))

    return unique_preserve_order(
        get_unique_parameters(measurement_df.observableParameters)
        + get_unique_parameters(measurement_df.noiseParameters))


def split_parameter_replacement_list(list_string: Union[str, numbers.Number],
                                     delim: str = ';'
                                     ) -> List:
    """
    Split values in observableParameters and noiseParameters in measurement
    table. Convert numeric values to float.

    Arguments:
        delim: delimiter
        list_string: delim-separated stringified list
    """

    def to_float_if_float(x):
        try:
            return float(x)
        except ValueError:
            return x

    if isinstance(list_string, numbers.Number):
        # Empty cells in pandas might be turned into nan
        # We might want to allow nan as replacement...
        if np.isnan(list_string):
            return []
        return [list_string]

    result = [x.strip() for x in list_string.split(delim) if len(x.strip())]
    return [to_float_if_float(x) for x in result]


def get_placeholders(formula_string: str, observable_id: str,
                     override_type: str) -> set:
    """
    Get placeholder variables in noise or observable definition for the
    given observable ID.

    Arguments:
        formula_string: observable formula (typically from SBML model)
        observable_id: ID of current observable
        override_type: 'observable' or 'noise', depending on whether `formula`
            is for observable or for noise model

    Returns:
        (Un-ordered) set of placeholder parameter IDs
    """
    pattern = re.compile(
        re.escape(override_type) + r'Parameter\d+_' + re.escape(observable_id))
    placeholders = set()
    for free_sym in sp.sympify(formula_string).free_symbols:
        free_sym = str(free_sym)
        if pattern.match(free_sym):
            placeholders.add(free_sym)
    return placeholders


def get_model_parameters(sbml_model: libsbml.Model) -> List[str]:
    """Return list of SBML model parameter IDs which are not AssignmentRule
    targets for observables or sigmas"""
    return [p.getId() for p in sbml_model.getListOfParameters()
            if sbml_model.getAssignmentRuleByVariable(p.getId()) is None]


def get_optimization_parameters(parameter_df: pd.DataFrame) -> List[str]:
    """
    Get list of optimization parameter ids from parameter dataframe.
    """
    return list(parameter_df.reset_index()['parameterId'])


def get_notnull_columns(df: pd.DataFrame, candidates: Iterable):
    """
    Return list of df-columns in candidates which are not all null/nan.
    The output can e.g. be used as input for pandas.DataFrame.groupby.
    """
    return [col for col in candidates
            if col in df and not np.all(df[col].isnull())]


def create_condition_df(parameter_ids: Iterable[str],
                        condition_ids: Iterable[str] = None) -> pd.DataFrame:
    """Create empty condition dataframe

    Arguments:
        parameter_ids: the columns
        condition_ids: the rows
    Returns:
        An pandas.DataFrame with empty given rows and columns and all nan
        values
    """

    data = {'conditionId': []}
    for p in parameter_ids:
        data[p] = []

    df = pd.DataFrame(data)
    df.set_index(['conditionId'], inplace=True)

    if not condition_ids:
        return df

    for c in condition_ids:
        df[c] = np.nan

    return df


def create_measurement_df() -> pd.DataFrame:
    """Create empty measurement dataframe"""

    df = pd.DataFrame(data={
        'observableId': [],
        'preequilibrationConditionId': [],
        'simulationConditionId': [],
        'measurement': [],
        'time': [],
        'observableParameters': [],
        'noiseParameters': [],
        'observableTransformation': [],
        'noiseDistribution': [],
    })

    return df


def create_parameter_df(sbml_model: libsbml.Model,
                        condition_df: pd.DataFrame,
                        measurement_df: pd.DataFrame,
                        parameter_scale: str = 'log10',
                        lower_bound: Iterable = None,
                        upper_bound: Iterable = None) -> pd.DataFrame:
    """Create a new PEtab parameter table

    All table entries can be provided as string or list-like with length
    matching the number of parameters

    Arguments:
        sbml_model: @type libsbml.Model
        condition_df: @type pandas.DataFrame
        measurement_df: @type pandas.DataFrame
        parameter_scale: parameter scaling
        lower_bound: lower bound for parameter value
        upper_bound: upper bound for parameter value
    """

    observables = get_observables(sbml_model)
    sigmas = get_sigmas(sbml_model)

    # collect placeholder parameters
    placeholders = set()
    for k, v in observables.items():
        placeholders |= get_placeholders(v['formula'], get_observable_id(k),
                                         'observable')
    for k, v in sigmas.items():
        placeholders |= get_placeholders(v, get_observable_id(k), 'noise')

    # grab all from model and measurement table
    # without condition table parameters
    # and observables assigment targets
    # and sigma assignment targets
    # and placeholder parameters (only partial overrides are not supported)

    # should not go into parameter table
    blackset = set()
    # collect assignment targets
    blackset |= set(observables.keys())
    blackset |= {'sigma_' + get_observable_id(k) for k in sigmas.keys()}
    blackset |= placeholders
    blackset |= set(condition_df.columns.values) - {'conditionName'}
    # use ordered dict as proxy for ordered set
    parameter_ids = OrderedDict.fromkeys(
        p.getId() for p in sbml_model.getListOfParameters()
        if p.getId() not in blackset)

    # Append parameters from measurement table,
    # unless they are fixed parameters
    def append_overrides(overrides):
        for p in overrides:
            if isinstance(p, str) and p not in condition_df.columns:
                parameter_ids[p] = None
    for _, row in measurement_df.iterrows():
        # we trust that the number of overrides matches
        append_overrides(
            split_parameter_replacement_list(row.observableParameters))
        append_overrides(
            split_parameter_replacement_list(row.noiseParameters))

    # Append parameter overrides from condition table
    condition_parameters = list(
        set(condition_df.columns.values.tolist()) - {'conditionId',
                                                     'conditionName'})
    for overridee in condition_parameters:
        # non-numeric entries are parameter overrides
        overrides = condition_df[overridee][
            ~condition_df[overridee].apply(isinstance, args=(numbers.Number,))]
        for overrider in overrides:
            parameter_ids[overrider] = None

    parameter_ids = list(parameter_ids.keys())

    df = pd.DataFrame(
        data={
            'parameterId': parameter_ids,
            'parameterName': parameter_ids,
            'parameterScale': parameter_scale,
            'lowerBound': lower_bound,
            'upperBound': upper_bound,
            'nominalValue': np.nan,
            'estimate': 1,
            'priorType': '',
            'priorParameters': ''
        })
    df.set_index(['parameterId'], inplace=True)

    # For SBML model parameters set nominal values as defined in the model
    for parameter_id in df.index:
        try:
            parameter = sbml_model.getParameter(parameter_id)
            if parameter:
                df.loc[parameter_id, 'nominalValue'] = parameter.getValue()
        except ValueError:
            # parameter was introduced as condition-specific override and
            # is potentially not present in the model
            pass
    return df


def get_observable_id(parameter_id: str) -> str:
    """Get observable id from sigma or observable parameter_id
    e.g. for observable_obs1 -> obs1
             sigma_obs1 -> obs1
    """

    if parameter_id.startswith(r'observable_'):
        return parameter_id[len('observable_'):]

    if parameter_id.startswith(r'sigma_'):
        return parameter_id[len('sigma_'):]

    raise ValueError('Cannot extract observable id from: ' + parameter_id)


def measurements_have_replicates(measurement_df: pd.DataFrame) -> bool:
    """Tests whether the measurements come with replicates

    Arguments:
        measurement_df: Measurement table

    Returns:
        True if there are replicates, False otherwise
    """
    return np.any(measurement_df.groupby(
        get_notnull_columns(
            measurement_df,
            ['observableId', 'simulationConditionId',
             'preequilibrationConditionId', 'time'])).size().values - 1)
