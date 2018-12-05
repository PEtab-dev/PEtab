import pandas as pd
import numpy as np
import libsbml
import sympy as sp
import re
import itertools

from . import lint
import numbers

class OptimizationProblem:

    def __init__(self, sbml_file_name, measurement_file_name, condition_file_name, parameter_file_name):
        self.measurement_file_name = measurement_file_name
        self.condition_file_name = condition_file_name
        self.parameter_file_name = parameter_file_name
        self.sbml_file = sbml_file_name

        self.condition_df = get_condition_df(condition_file_name)
        self.parameter_df = get_parameter_df(parameter_file_name)
        self.measurement_df = get_measurement_df(measurement_file_name)

        self._load_sbml()

    def _load_sbml(self):
        """Load SBML model"""

        # sbml_reader and sbml_document must be kept alive. Otherwise operations on sbml_model will segfault
        self.sbml_reader = libsbml.SBMLReader()
        self.sbml_document = self.sbml_reader.readSBML(self.sbml_file)
        self.sbml_model = self.sbml_document.getModel()

    def get_constant_parameters(self):
        """Provide list of IDs of parameters which are fixed (i.e. not subject to optimization, no sensitivities w.r.t. these parameters are required)"""

        return list(set(self.condition_df.columns.values.tolist()) - {'conditionId', 'conditionName'})

    def get_observables(self):
        """Returns dictionary of observables definitions

        see `assignment_rules_to_dict` for details"""

        return get_observables(self.sbml_model)

    def get_sbml_sigmas(self):
        """Return dictionary of observableId => sigma as defined in the SBML model

        This does not include parameter mappings defined in the measurement table.
        """

        return get_sigmas(sbml_model=self.sbml_model)

    def get_simulation_to_optimization_parameter_mapping(self):
        """See get_simulation_to_optimization_parameter_mapping"""
        return get_simulation_to_optimization_parameter_mapping(self.measurement_df,
                                                                self.condition_df,
                                                                get_dynamic_parameters_from_sbml(self.sbml_model))


def get_condition_df(condition_file_name):
    """Read the provided condition file into a `pandas.Dataframe`

    Conditions are rows, parameters are columns, conditionId is index
    """

    condition_df = pd.read_csv(condition_file_name, sep='\t')
    condition_df.set_index(['conditionId'])

    return condition_df


def get_parameter_df(parameter_file_name):
    """Read the provided parameter file into a `pandas.Dataframe`"""

    parameter_df = pd.read_csv(parameter_file_name, sep='\t')

    try:
        parameter_df.set_index(['parameterId'], inplace=True)
    except KeyError:
        raise KeyError('Parameter table missing mandatory field `parameterId`.')

    return parameter_df


def get_measurement_df(measurement_file_name):
    """Read the provided measurement file into a `pandas.Dataframe`"""

    measurement_df = pd.read_csv(measurement_file_name, sep='\t')

    return measurement_df


def assignment_rules_to_dict(sbml_model, filter_function=lambda *_: True, remove=False):
    """Turn assignment rules into dictionary.

    Arguments:
    sbml_model: an sbml Model instance

    filter_function: callback function taking assignment variable as input
    and returning True/False to indicate if the respective rule should be
    turned into an observable

    Returns:
    A dictionary(assigneeId:{
        'name': assigneeName,
        'formula': formulaString
    })

    Raises:

    """
    result = {}
    for p in sbml_model.getListOfParameters():
        parameter_id = p.getId()
        if filter_function(p):
            result[parameter_id] = {
                'name': p.getName(),
                'formula': sbml_model.getAssignmentRuleByVariable(
                    parameter_id
                ).getFormula()
            }

    if remove:
        for parameter_id in result:
            sbml_model.removeRuleByVariable(parameter_id)
            sbml_model.removeParameter(parameter_id)

    return result


def sbml_parameter_is_observable(sbml_parameter):
    """If the `libsbml.Parameter` `sbml_parameter` is target of an assignment rule, this function returns True
    if the ID matches the defined format"""
    return sbml_parameter.getId().startswith('observable_')


def sbml_parameter_is_sigma(sbml_parameter):
    return sbml_parameter.getId().startswith('sigma_')


def get_observables(sbml_model, remove=False):
    """Returns dictionary of observables definitions

    see `assignment_rules_to_dict` for details"""

    observables = assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_observable,
        remove=remove
    )
    return observables


def get_sigmas(sbml_model, remove=False):
    """Returns dictionary of sigmas definitions

    see `assignment_rules_to_dict` for details"""

    sigmas = assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_sigma,
        remove=remove
    )
    return sigmas


def parameter_is_scaling_parameter(parameter, formula):
    """Returns true if parameter `parameter` is a scaling parameter in formula `formula`"""

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula / sym_parameter).free_symbols


def parameter_is_offset_parameter(parameter, formula):
    """Returns true if parameter `parameter` is an offset parameter with positive sign in formula `formula`"""

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula - sym_parameter).free_symbols


def get_simulation_to_optimization_parameter_mapping(
        measurement_df, condition_df, sbml_parameter_ids,
        observables=None, noise=None):
    """
    Create `np.array` n_parameters_simulation x n_conditions with indices of respective parameters in parameters_optimization

    If `observables` and `noise` arguments (as obtained from `get_observables`, `get_sbml_sigmas`)
    are provided, we check for correct numbers of parameter overrides. Otherwise it is
    the users responsibility to ensure to ensure correctness.
    """

    # We cannot handle those cases yet:
    if not lint.condition_table_is_parameter_free(condition_df):
        raise ValueError('Parameterized condition table currently unsupported.')
    if lint.measurement_table_has_timepoint_specific_mappings(measurement_df):
        # We could allow that for floats, since they don't matter in this function and
        # would be simply ignored
        raise ValueError('Timepoint-specific parameter overrides currently unsupported.')
    if lint.measurement_table_has_observable_parameter_numeric_overrides(measurement_df):
        # I guess we could simply ignore them, since they should not go into the optimization parameter vector
        raise ValueError('Numeric observable parameter overrides currently unsupported.')

    # We rely on that:
    if observables is not None and noise is not None:
        lint.assert_overrides_match_parameter_count(measurement_df, observables, noise)

    # Number of simulation conditions will be number of unique preequilibrationCondition-simulationCondition pairs
    # Can be improved by checking for identical condition vectors

    grouping_cols = get_notnull_columns(measurement_df,
                                        ['simulationConditionId',
                                         'preequilibrationConditionId'])
    simulation_conditions = measurement_df.groupby(grouping_cols) \
        .size().reset_index()

    num_simulation_parameters = len(sbml_parameter_ids)
    num_conditions = simulation_conditions.shape[0]

    # initialize mapping matrix (num_simulation_parameters x num_conditions) for the case of matching
    # simulation and optimization parameter vector
    mapping = np.repeat(np.transpose([np.arange(0, num_simulation_parameters)]),
                        axis=1, repeats=num_conditions)

    # optimization parameters are model parameters + condition specific parameters
    optimization_parameter_ids = list(sbml_parameter_ids) + get_measurement_parameter_ids(measurement_df)

    condition_ids = [condition_id for condition_id in condition_df.conditionId.values if
                     condition_id in measurement_df.simulationConditionId.values]

    # create inverse mappings
    optimization_parameter_name_to_index = {
        name: idx for idx, name in enumerate(optimization_parameter_ids)
    }
    condition_id_to_idx = {
        name: idx for idx, name in enumerate(condition_ids)
    }
    model_parameter_id_to_idx = {
        name: idx for idx, name in enumerate(sbml_parameter_ids)
    }

    def _apply_overrides(overrides, condition_id, observable_id, override_type):
        """Apply parameter-overrides to mapping matrix
        override_type: observable / noise
        """
        for i, override in enumerate(overrides):
            if isinstance(override, numbers.Number):
                # absence of float observable parameter overrides has been asserted above
                # float noise parameter overrides are ignored here
                continue
            model_parameter_idx = model_parameter_id_to_idx[f'{override_type}Parameter{i + 1}_{observable_id}']
            condition_idx = condition_id_to_idx[condition_id]
            optimization_parameter_idx = optimization_parameter_name_to_index[override]
            mapping[model_parameter_idx, condition_idx] = optimization_parameter_idx

    for _, row in measurement_df.iterrows():
        # We trust that number of overrides matches (see above)
        overrides = split_parameter_replacement_list(row.observableParameters)
        _apply_overrides(overrides, row.simulationConditionId, row.observableId, override_type='observable')

        overrides = split_parameter_replacement_list(row.noiseParameters)
        _apply_overrides(overrides, row.simulationConditionId, row.observableId, override_type='noise')

    # Some model parameters might always be overwritten by measurements.observableIds, they can be removed
    unused_optimization_parameter_idxs = set(range(len(optimization_parameter_ids))) - set(np.unique(mapping))

    # update index mapping
    old_optimization_parameter_ids = optimization_parameter_ids
    optimization_parameter_ids = [pid for i, pid in enumerate(old_optimization_parameter_ids) if
                                  not i in unused_optimization_parameter_idxs]
    optimization_parameter_name_to_index = {
        name: idx for idx, name in enumerate(optimization_parameter_ids)
    }
    # This can probably be done more efficiently
    for i in range(mapping.shape[0]):
        for j in range(mapping.shape[1]):
            mapping[i, j] = optimization_parameter_name_to_index[old_optimization_parameter_ids[mapping[i, j]]]

    return optimization_parameter_ids, mapping


def get_measurement_parameter_ids(measurement_df):
    """Return list of ID of parameters which occur in measurement table as observable or noise parameter"""

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
    """Split values in observableParameters and noiseParameters in measurement table"""

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


def get_num_placeholders(formula_string, observable_id, override_type):
    """Get number of unique placeholder variables in noise or observable definition"""

    pattern = re.compile(re.escape(override_type) + r'Parameter\d+_' + re.escape(observable_id))
    placeholders = set()
    for free_sym in sp.sympify(formula_string).free_symbols:
        free_sym = str(free_sym)
        if pattern.match(free_sym):
            placeholders.add(free_sym)
    return len(placeholders)


def get_dynamic_parameters_from_sbml(sbml_model):
    """Get list of non-constant parameters in sbml model"""

    return [p.getId() for p in sbml_model.getListOfParameters() if not p.getConstant()]


def get_notnull_columns(df, candidates):
    """"Return list of df-columns in candidates which are not all null/nan

    The output can e.g. be used as input for pandas.DataFrame.groupby"""
    return [col for col in candidates if col in df and not np.all(df[col].isnull())]
