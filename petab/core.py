import pandas as pd
import numpy as np
import libsbml
import sympy as sp
import re
import itertools
import os
import numbers
from collections import OrderedDict
from . import lint


class Problem:
    """
    PEtab parameter estimation problem as defined by
    - sbml model
    - condition table
    - measurement table
    - parameter table [optional]

    Attributes:
        sbml_file: PEtab SBML model
        condition_file: PEtab condition table
        measurement_file: PEtab measurement table
        parameter_file: PEtab parameter table
        model_name: name of the model
        condition_df: @type pandas.DataFrame
        measurement_df: @type pandas.DataFrame
        parameter_df: @type pandas.DataFrame
        sbml_reader: @type libsbml.SBMLReader
        sbml_document: @type libsbml.Document
        sbml_model: @type libsbml.Model
    """

    def __init__(self,
                 sbml_file,
                 condition_file,
                 measurement_file,
                 parameter_file=None,
                 model_name=None):

        if model_name is None:
            model_name = os.path.splitext(os.path.split(sbml_file)[-1])[0]
        self.model_name = model_name

        self.measurement_file = measurement_file
        self.condition_file = condition_file
        self.parameter_file = parameter_file
        self.sbml_file = sbml_file

        self.condition_df = None
        self.measurement_df = None
        self.parameter_df = None
        self._load_dfs()

        self.sbml_reader = None
        self.sbml_document = None
        self.sbml_model = None
        self._load_sbml()

    def __getstate__(self):
        state = self.__dict__.copy()
        # libsbml stuff cannot be serialized
        # dfs can be recreated
        for key in ['sbml_reader', 'sbml_document', 'sbml_model',
                    'condition_df', 'measurement_df', 'parameter_df']:
            state.pop(key)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        # load sbml from file name
        self._load_sbml()

        # reload dfs
        self._load_dfs()

    @staticmethod
    def from_folder(folder):
        """
        Factory method to use the standard folder structure
        and file names.
        """

        folder = os.path.abspath(folder)
        model_name = os.path.split(folder)[-1]

        return Problem(
            condition_file=get_default_condition_file_name(model_name, folder),
            measurement_file=get_default_measurement_file_name(
                model_name, folder),
            parameter_file=get_default_parameter_file_name(model_name, folder),
            sbml_file=get_default_sbml_file_name(model_name, folder),
            model_name=model_name
        )

    def _load_dfs(self):
        """
        Load condition, measurement, and parameter dataframes.
        """
        self.condition_df = get_condition_df(self.condition_file)
        self.measurement_df = get_measurement_df(self.measurement_file)
        if self.parameter_file:
            self.parameter_df = get_parameter_df(self.parameter_file)
        else:
            self.parameter_df = None

    def _load_sbml(self):
        """
        Load SBML model.
        """
        # sbml_reader and sbml_document must be kept alive.
        # Otherwise operations on sbml_model will segfault
        self.sbml_reader = libsbml.SBMLReader()
        self.sbml_document = self.sbml_reader.readSBML(self.sbml_file)
        self.sbml_model = self.sbml_document.getModel()

    def get_constant_parameters(self):
        """
        Provide list of IDs of parameters which are fixed (i.e. not subject
        to optimization, no sensitivities w.r.t. these parameters are
        required).
        """
        columns_set = set(self.condition_df.columns.values)
        return list(columns_set - {'conditionId', 'conditionName'})

    def get_optimization_parameters(self):
        """
        Return list of optimization parameter ids.
        """
        return get_optimization_parameters(self.parameter_df)

    def get_dynamic_simulation_parameters(self):
        return get_dynamic_simulation_parameters(
            self.sbml_model, self.parameter_df)

    def get_dynamic_parameters_from_sbml(self):
        """
        Provide list of IDS of parameters which are dynamic, i.e. not
        fixed.
        See get_dynamic_parameters_from_sbml.
        """
        return get_dynamic_parameters_from_sbml(self.sbml_model)

    def get_observables(self, remove=False):
        """
        Returns dictionary of observables definitions
        See `assignment_rules_to_dict` for details.
        """

        return get_observables(sbml_model=self.sbml_model, remove=remove)

    def get_sigmas(self, remove=False):
        """
        Return dictionary of observableId => sigma as defined in the SBML
        model.
        This does not include parameter mappings defined in the measurement
        table.
        """

        return get_sigmas(sbml_model=self.sbml_model, remove=remove)

    @property
    def x_ids(self):
        return list(self.parameter_df.reset_index()['parameterId'])

    @property
    def x_nominal(self):
        return list(self.parameter_df['nominalValue'])

    @property
    def lb(self):
        return list(self.parameter_df['lowerBound'])

    @property
    def ub(self):
        return list(self.parameter_df['upperBound'])

    @property
    def x_fixed_indices(self):
        estimated = list(self.parameter_df['estimate'])
        return [j for j, val in enumerate(estimated) if val == 0]

    @property
    def x_fixed_vals(self):
        return [self.x_nominal[val] for val in self.x_fixed_indices]

    def get_simulation_conditions_from_measurement_df(self):
        return get_simulation_conditions_from_measurement_df(
            self.measurement_df)

    def get_optimization_to_simulation_parameter_mapping(self):
        """
        See get_simulation_to_optimization_parameter_mapping.
        """
        return get_optimization_to_simulation_parameter_mapping(
            self.condition_df,
            self.measurement_df,
            self.parameter_df,
            self.sbml_model)

    def create_parameter_df(self, *args, **kwargs):
        """Create a new PEtab parameter table"""
        return create_parameter_df(self.sbml_model,
                                   self.condition_df,
                                   self.measurement_df,
                                   *args, **kwargs)


def get_default_condition_file_name(model_name, folder=''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, "experimentalCondition_" + model_name + ".tsv")


def get_default_measurement_file_name(model_name, folder=''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, "measurementData_" + model_name + ".tsv")


def get_default_parameter_file_name(model_name, folder=''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, "parameters_" + model_name + ".tsv")


def get_default_sbml_file_name(model_name, folder=''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, "model_" + model_name + ".xml")


def get_condition_df(condition_file_name):
    """Read the provided condition file into a `pandas.Dataframe`

    Conditions are rows, parameters are columns, conditionId is index.
    """

    condition_df = pd.read_csv(condition_file_name, sep='\t')
    lint.assert_no_trailing_whitespace(
        condition_df.columns.values, "condition")

    try:
        condition_df.set_index(['conditionId'], inplace=True)
    except KeyError:
        raise KeyError(
            'Condition table missing mandatory field `conditionId`.')

    return condition_df


def get_parameter_df(parameter_file_name):
    """
    Read the provided parameter file into a `pandas.Dataframe`.
    """

    parameter_df = pd.read_csv(parameter_file_name, sep='\t')
    lint.assert_no_trailing_whitespace(
        parameter_df.columns.values, "parameter")

    try:
        parameter_df.set_index(['parameterId'], inplace=True)
    except KeyError:
        raise KeyError(
            'Parameter table missing mandatory field `parameterId`.')

    return parameter_df


def get_measurement_df(measurement_file_name):
    """
    Read the provided measurement file into a `pandas.Dataframe`.
    """

    measurement_df = pd.read_csv(measurement_file_name, sep='\t')
    lint.assert_no_trailing_whitespace(
        measurement_df.columns.values, "measurement")

    return measurement_df


def assignment_rules_to_dict(
        sbml_model, filter_function=lambda *_: True, remove=False):
    """
    Turn assignment rules into dictionary.

    Parameters
    ----------

    sbml_model:
        an sbml model instance.
    filter_function:
        callback function taking assignment variable as input
        and returning True/False to indicate if the respective rule should be
        turned into an observable.

    Returns
    -------

    A dictionary(assigneeId:{
        'name': assigneeName,
        'formula': formulaString
    })
    """
    result = {}

    # iterate over rules
    for rule in sbml_model.getListOfRules():
        if rule.getTypeCode() != libsbml.SBML_ASSIGNMENT_RULE:
            continue
        assignee = rule.getVariable()
        parameter = sbml_model.getParameter(assignee)
        # filter
        if parameter and filter_function(parameter):
            result[assignee] = {
                'name': parameter.getName(),
                'formula': rule.getFormula()
            }

    # remove from model?
    if remove:
        for parameter_id in result:
            sbml_model.removeRuleByVariable(parameter_id)
            sbml_model.removeParameter(parameter_id)

    return result


def sbml_parameter_is_observable(sbml_parameter):
    """
    Returns whether the `libsbml.Parameter` `sbml_parameter`
    matches the defined observable format.
    """
    return sbml_parameter.getId().startswith('observable_')


def sbml_parameter_is_sigma(sbml_parameter):
    """
    Returns whether the `libsbml.Parameter` `sbml_parameter`
    matches the defined sigma format.
    """
    return sbml_parameter.getId().startswith('sigma_')


def get_observables(sbml_model, remove=False):
    """
    Returns dictionary of observable definitions.
    See `assignment_rules_to_dict` for details.
    """
    observables = assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_observable,
        remove=remove
    )
    return observables


def get_sigmas(sbml_model, remove=False):
    """
    Returns dictionary of sigma definitions.
    See `assignment_rules_to_dict` for details.
    """
    sigmas = assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_sigma,
        remove=remove
    )
    # set correct observable name
    sigmas = {re.sub(f'^sigma_', 'observable_', key): value['formula']
              for key, value in sigmas.items()}
    return sigmas


def parameter_is_scaling_parameter(parameter, formula):
    """
    Returns true if parameter `parameter` is a scaling
    parameter in formula `formula`.
    """

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula / sym_parameter).free_symbols


def parameter_is_offset_parameter(parameter, formula):
    """
    Returns true if parameter `parameter` is an offset
    parameter with positive sign in formula `formula`.
    """

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula - sym_parameter).free_symbols


def get_simulation_conditions_from_measurement_df(measurement_df):
    grouping_cols = get_notnull_columns(
        measurement_df,
        ['simulationConditionId', 'preequilibrationConditionId'])
    simulation_conditions = \
        measurement_df.groupby(grouping_cols).size().reset_index()

    return simulation_conditions


def get_optimization_to_simulation_parameter_mapping(
        condition_df,
        measurement_df,
        parameter_df=None,
        sbml_model=None,
        par_opt_ids=None,
        par_sim_ids=None):
    """
    Create array of mappings. The length of the array is n_conditions, each
    entry is an array of length n_par_sim, listing the optimization parameters
    or constants to be mapped to the simulation parameters.

    Parameters
    ----------

    condition_df, measurement_df, parameter_df:
        The dataframes in the petab format.

        parameter_df is optional if par_sim_ids is provided

    sbml_model:
        The sbml model with observables and noise specified according to the
        petab format. Optional if par_sim_ids is provided.

    par_opt_ids, par_sim_ids: list of str, optional
        Ids of the optimization and simulation parameters. If not passed,
        these are generated from the files automatically. However, passing
        them can ensure having the correct order.
    """
    perform_mapping_checks(condition_df, measurement_df)

    simulation_conditions = \
        get_simulation_conditions_from_measurement_df(measurement_df)
    condition_ids = [
        condition_id for condition_id in condition_df.index
        if condition_id in measurement_df.simulationConditionId.values
    ]

    # if par_opt_ids is None:
    #    par_opt_ids = get_optimization_parameters(parameter_df)
    if par_sim_ids is None:
        par_sim_ids = get_dynamic_simulation_parameters(sbml_model,
                                                        parameter_df)

    n_conditions = simulation_conditions.shape[0]

    # initialize mapping matrix of shape n_par_dyn_sim_ids x n_conditions
    # for the case of matching simulation and optimization parameter vector
    mapping = [par_sim_ids[:] for _ in range(0, n_conditions)]

    sim_condition_id_to_idx = {
        name: idx for idx, name in enumerate(condition_ids)
    }
    par_sim_id_to_idx = {
        name: idx for idx, name in enumerate(par_sim_ids)
    }

    def _apply_overrides(
            overrides, condition_id, observable_id, override_type):
        """
        Apply parameter-overrides for observables and noises to mapping
        matrix.
        """
        condition_idx = sim_condition_id_to_idx[condition_id]
        for i, override in enumerate(overrides):
            par_sim_idx = par_sim_id_to_idx[
                f'{override_type}Parameter{i+1}_{observable_id}']
            mapping[condition_idx][par_sim_idx] = override

    for _, row in measurement_df.iterrows():
        # we trust that the number of overrides matches (see above)
        overrides = split_parameter_replacement_list(row.observableParameters)
        _apply_overrides(
            overrides, row.simulationConditionId,
            row.observableId, override_type='observable')
        overrides = split_parameter_replacement_list(row.noiseParameters)
        _apply_overrides(
            overrides, row.simulationConditionId,
            row.observableId, override_type='noise')

    return mapping


def perform_mapping_checks(condition_df, measurement_df):

    # we cannot handle those cases yet
    if not lint.condition_table_is_parameter_free(condition_df):
        raise ValueError(
            "Parameterized condition table currently unsupported.")
    if lint.measurement_table_has_timepoint_specific_mappings(measurement_df):
        # we could allow that for floats, since they don't matter in this
        # function and would be simply ignored
        raise ValueError(
            "Timepoint-specific parameter overrides currently unsupported.")


def get_optimization_to_simulation_scale_mapping(
        parameter_df,
        mapping_par_opt_to_par_sim):

    n_condition = len(mapping_par_opt_to_par_sim)
    n_par_sim = len(mapping_par_opt_to_par_sim[0])

    par_opt_ids_from_df = list(parameter_df.reset_index()['parameterId'])
    par_opt_scales_from_df = list(parameter_df.reset_index()['parameterScale'])

    mapping_scale_opt_to_scale_sim = []

    # iterate over conditions
    for j_condition in range(0, n_condition):
        # prepare vector of scales for j_condition
        scales_for_j_condition = []

        # iterate over simulation parameters
        for j_par_sim in range(n_par_sim):
            # extract entry in mapping table for j_par_sim
            val = mapping_par_opt_to_par_sim[j_condition][j_par_sim]

            if isinstance(val, numbers.Number):
                # fixed value assignment
                scale = 'lin'
            else:
                # is par opt id, thus extract its scale
                scale = par_opt_scales_from_df[par_opt_ids_from_df.index(val)]

            # append to scales for condition j
            scales_for_j_condition.append(scale)

        # append to mapping
        mapping_scale_opt_to_scale_sim.append(scales_for_j_condition)

    return mapping_scale_opt_to_scale_sim


def get_measurement_parameter_ids(measurement_df):
    """
    Return list of ID of parameters which occur in measurement table as
    observable or noise parameter.
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


def split_parameter_replacement_list(list_string):
    """
    Split values in observableParameters and noiseParameters in measurement
    table.
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

    result = [x.strip() for x in list_string.split(';') if len(x.strip())]
    return [to_float_if_float(x) for x in result]


def get_placeholders(formula_string, observable_id, override_type):
    """
    Get placeholder variables in noise or observable definition.
    """
    pattern = re.compile(
        re.escape(override_type) + r'Parameter\d+_' + re.escape(observable_id))
    placeholders = set()
    for free_sym in sp.sympify(formula_string).free_symbols:
        free_sym = str(free_sym)
        if pattern.match(free_sym):
            placeholders.add(free_sym)
    return placeholders


def get_dynamic_parameters_from_sbml(sbml_model):
    """
    Get list of non-constant parameters in sbml model.
    TODO: This is not what Y would expect. Remove?
    """
    return [p.getId() for p in sbml_model.getListOfParameters()
            if not p.getConstant()]


def get_dynamic_simulation_parameters(sbml_model, parameter_df):
    par_opt_ids = get_optimization_parameters(parameter_df)
    sbml_pars = sbml_model.getListOfParameters()
    par_ids = [
        p.getId() for p in sbml_pars
        if p.getId().startswith("noiseParameter")
        or p.getId().startswith("observableParameter")
        or p.getId() in par_opt_ids
    ]
    return par_ids


def get_optimization_parameters(parameter_df):
    """
    Get list of optimization parameter ids from parameter
    dataframe.
    """
    return list(parameter_df.reset_index()['parameterId'])


def get_notnull_columns(df, candidates):
    """
    Return list of df-columns in candidates which are not all null/nan.
    The output can e.g. be used as input for pandas.DataFrame.groupby.
    """
    return [col for col in candidates
            if col in df and not np.all(df[col].isnull())]


def create_condition_df(parameter_ids, condition_ids=None):
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


def create_measurement_df():
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


def create_parameter_df(sbml_model, condition_df, measurement_df,
                        parameter_scale='log10',
                        lower_bound=None,
                        upper_bound=None):
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

    # We do not handle that yet, once we do, we need to add those parameters
    # as well
    assert lint.condition_table_is_parameter_free(condition_df)

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

    return df


def get_observable_id(parameter_id):
    """Get observable id from sigma or observable parameter_id
    e.g. for observable_obs1 -> obs1
             sigma_obs1 -> obs1
    """

    if parameter_id.startswith(r'observable_'):
        return parameter_id[len('observable_'):]

    if parameter_id.startswith(r'sigma_'):
        return parameter_id[len('sigma_'):]

    raise ValueError('Cannot extract observable id from: ' + parameter_id)
