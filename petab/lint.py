import numpy as np
from . import core
import numbers

"""Integrity checks and tests for specific features used"""

def assert_measured_observables_present_in_model(measurement_df, sbml_model):
    """Check if all observables in measurement files have been specified in the model"""
    measurement_observables = [f'observable_{x}' for x in measurement_df.observableId.values]

    model_observables = core.get_observables(sbml_model)
    undefined_observables = set(measurement_observables) - set(model_observables.keys())

    if len(undefined_observables):
        raise AssertionError(f'Unknown observables in measurement file: {undefined_observables}')


def condition_table_is_parameter_free(condition_df):
    """Check if all entries in the condition table are numeric (no parameter IDs)"""

    constant_parameters = list(set(condition_df.columns.values.tolist()) - {'conditionId', 'conditionName'})

    for column in constant_parameters:
        if np.any(np.invert(condition_df.loc[:, column].apply(isinstance, args=(numbers.Number,)))):
            return False
    return True


def measurement_table_has_timepoint_specific_mappings(measurement_df):
    """Are there time-point or replicate specific parameter assignments in the measurement table"""

    measurement_df.loc[
        measurement_df.noiseParameters.apply(isinstance, args=(numbers.Number,)), 'noiseParameters'] = np.nan

    grouping_cols = core.get_notnull_columns(measurement_df, ['observableId',
                                                              'simulationConditionId',
                                                              'preequilibrationConditionId',
                                                              'observableParameters',
                                                              'noiseParameters'
                                                              ])
    grouped_df = measurement_df.groupby(grouping_cols).size().reset_index()
    grouping_cols = core.get_notnull_columns(grouped_df,
                                             ['observableId',
                                              'simulationConditionId',
                                              'preequilibrationConditionId'])
    grouped_df2 = grouped_df.groupby(grouping_cols).size().reset_index()

    if len(grouped_df.index) != len(grouped_df2.index):
        return True
    return False


def measurement_table_has_observable_parameter_numeric_overrides(measurement_df):
    """Are there any numbers to override observable parameters?"""

    for i, row in measurement_df.iterrows():
        for override in core.split_parameter_replacement_list(row.observableParameters):
            if isinstance(override, numbers.Number):
                return True
    return False


def assert_overrides_match_parameter_count(measurement_df, observables, noise):
    """Ensure that number of parameters in the observable definition matches the number of overrides in `measurement_df`

    Arguments:
        :param measurement_df:
        :param observables: dict: obsId => {obsFormula}
        :param noise: dict: obsId => {obsFormula}
    """

    # sympify only once and save number of parameters
    observable_parameters_count = {oid[len('observable_'):]:
                                       core.get_num_placeholders(value['formula'], oid[len('observable_'):],
                                                                 'observable')
                                   for oid, value in observables.items()}

    noise_parameters_count = {oid[len('sigma_'):]:
                                  core.get_num_placeholders(value['formula'], oid[len('sigma_'):], 'noise')
                              for oid, value in noise.items()}

    for _, row in measurement_df.iterrows():
        try:
            expected = observable_parameters_count[row.observableId]
        except KeyError:
            raise ValueError(f'Observable {row.observableId} used in measurement table but not defined in model {observables.keys()}')
        actual = len(core.split_parameter_replacement_list(row.observableParameters))
        # No overrides are also allowed
        if not (actual == 0 or actual == expected):
            raise AssertionError(f'Mismatch of observable parameter overrides for {observables[f"observable_{row.observableId}"]} in:\n{row}\n'
                                 f'Expected 0 or {expected} but got {actual}')

        expected = noise_parameters_count[row.observableId]
        actual = len(core.split_parameter_replacement_list(row.noiseParameters))
        # No overrides are also allowed
        if not (actual == 0 or actual == expected):
            raise AssertionError(f'Mismatch of noise parameter overrides in:\n{row}'
                                 f'Expected 0 or {expected} but got {actual}')
