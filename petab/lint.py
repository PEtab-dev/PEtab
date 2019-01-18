"""Integrity checks and tests for specific features used"""

from . import core

import numpy as np
import numbers
import libsbml


def _check_df(df, req_cols, name):
    cols_set = df.columns.values
    missing_cols = set(req_cols) - set(cols_set)
    if missing_cols:
        raise AssertionError(
            f"Dataframe {name} requires the columns {missing_cols}.")


def check_condition_df(df):
    req_cols = [
        "conditionId", "conditionName"
    ]
    _check_df(df, req_cols, "condition")


def check_measurement_df(df):
    req_cols = [
        "observableId", "preequilibrationConditionId", "simulationConditionId",
        "measurement", "time", "observableParameters", "noiseParameters",
        "observableTransformation"
    ]
    _check_df(df, req_cols, "measurement")


def check_parameter_df(df):
    req_cols = [
        "parameterId", "parameterName", "parameterScale",
        "lowerBound", "upperBound", "nominalValue", "estimate"
    ]
    _check_df(df, req_cols, "parameter")


def _check_df(df, req_cols, name):
    cols_set = df.columns.values
    missing_cols = set(req_cols) - set(cols_set)
    if missing_cols:
        raise AssertionError(
            f"Dataframe {name} requires the columns {missing_cols}.")

def check_condition_df(df):
    req_cols = [
        "conditionId", "conditionName"
    ]
    _check_df(df, req_cols, "condition")

def check_measurement_df(df):
    req_cols =  [
        "observableId", "preequilibrationConditionId", "simulationConditionId",
        "measurement", "time", "observableParameters", "noiseParameters",
        "observableTransformation"
    ]
    _check_df(df, req_cols, "measurement")

def check_parameter_df(df):
    req_cols = [
        "parameterId", "parameterName", "parameterScale",
        "lowerBound", "upperBound", "nominalValue", "estimate"
    ]
    _check_df(df, req_cols, "parameter")

def assert_measured_observables_present_in_model(measurement_df, sbml_model):
    """Check if all observables in measurement files have been specified in the model"""
    measurement_observables = [f'observable_{x}' for x in
                               measurement_df.observableId.values]

    model_observables = core.get_observables(sbml_model)
    undefined_observables = set(measurement_observables) - set(
        model_observables.keys())

    if len(undefined_observables):
        raise AssertionError(
            f'Unknown observables in measurement file: {undefined_observables}')


def condition_table_is_parameter_free(condition_df):
    """Check if all entries in the condition table are numeric (no parameter IDs)"""

    constant_parameters = list(
        set(condition_df.columns.values.tolist()) - {'conditionId',
                                                     'conditionName'})

    for column in constant_parameters:
        if np.any(np.invert(condition_df.loc[:, column].apply(isinstance,
                                                              args=(
                                                              numbers.Number,)))):
            return False
    return True

def check_parameter_sheet(problem):
    check_parameter_df(problem.parameter_df)
    parameterId_is_string(problem.parameter_df)
    parameterScale_is_valid(problem.parameter_df)
    parameterBounds_are_numeric(problem.parameter_df)
    parameterEstimate_is_boolean(problem.parameter_df)
    parameterId_is_unique(problem.parameter_df)
    check_parameterBounds(problem.parameter_df)
    return True

def parameterId_is_string(parameter_df):
    """Check if all entries in the parameterId column of the parameter table are string and not empty"""

    for parameterId in parameter_df['parameterId']:
        if isinstance(parameterId, str):
            if parameterId[0].isdigit():
                raise ValueError('parameterId ' + parameterId + ' starts with integer')
        else:
            raise ValueError('Empty parameterId found')

    return True

def parameterId_is_unique(parameter_df):
    """Check if the parameterId column of the parameter table is unique"""
    if len(parameter_df['parameterId']) == len(set(parameter_df['parameterId'])):
        return True
    else:
        raise AssertionError('parameterId column in parameter table is not unique')


def parameterScale_is_valid(parameter_df):
    """Check if all entries in the parameterScale column of the parameter table are
    'lin' for linear, 'log' for natural logarithm or 'log10' for base 10 logarithm """

    for parameterScale in parameter_df['parameterScale']:
        if parameterScale not in ['lin', 'log', 'log10']:
            raise AssertionError('Expected "lin", "log" or "log10" but got "'+parameterScale+'"')

    return True

def parameterBounds_are_numeric(parameter_df):
    """Check if all entries in the lowerBound and upperBound column of the parameter table are
    numeric """

    for lowBound in parameter_df['lowerBound']:
        try:
            float(lowBound)
        except:
            raise AssertionError(f'Expected float but got {lowBound, type(lowBound)} as lower bound')

    for upBound in parameter_df['upperBound']:
        try:
            float(upBound)
        except:
            raise AssertionError(f'Expected float but got {upBound, type(upBound)} as upper bound')

    return True

def check_parameterBounds(parameter_df):
    """Check if all entries in the lowerBound are smaller than upperBound column in the parameter table"""
    for element in range(len(parameter_df['lowerBound'])):
        if not parameter_df['lowerBound'][element] <= parameter_df['upperBound'][element]:
            raise AssertionError(f'lowerbound larger than upperBound in {parameter_df["parameterId"][element]}')


def parameterEstimate_is_boolean(parameter_df):
    """Check if all entries in the estimate column of the parameter table are boolean """

    for estimate in parameter_df['estimate']:
        if not int(estimate) in [True, False]:
            raise AssertionError(f'Expected boolean but got {estimate, type(estimate)} in estimate')

    return True

def measurement_table_has_timepoint_specific_mappings(measurement_df):
    """Are there time-point or replicate specific parameter assignments in the measurement table"""

    measurement_df.loc[
        measurement_df.noiseParameters.apply(isinstance, args=(
        numbers.Number,)), 'noiseParameters'] = np.nan

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


def measurement_table_has_observable_parameter_numeric_overrides(
        measurement_df):
    """Are there any numbers to override observable parameters?"""

    for i, row in measurement_df.iterrows():
        for override in core.split_parameter_replacement_list(
                row.observableParameters):
            if isinstance(override, numbers.Number):
                return True
    return False


def assert_overrides_match_parameter_count(measurement_df, observables, noise):
    """Ensure that number of parameters in the observable definition matches
    the number of overrides in `measurement_df`

    Arguments:
        :param measurement_df:
        :param observables: dict: obsId => {obsFormula}
        :param noise: dict: obsId => {obsFormula}
    """

    # sympify only once and save number of parameters
    observable_parameters_count = {oid[len('observable_'):]:
                                       len(core.get_placeholders(
                                           value['formula'],
                                           oid[len('observable_'):],
                                           'observable'))
                                   for oid, value in observables.items()}
    noise_parameters_count = {
        oid[len('observable_'):]: len(core.get_placeholders(
            value, oid[len('observable_'):], 'noise'))
        for oid, value in noise.items()
    }

    for _, row in measurement_df.iterrows():
        try:
            expected = observable_parameters_count[row.observableId]
        except KeyError:
            raise ValueError(
                f'Observable {row.observableId} used in measurement table but not defined in model {observables.keys()}')
        actual = len(
            core.split_parameter_replacement_list(row.observableParameters))
        # No overrides are also allowed
        if not (actual == 0 or actual == expected):
            raise AssertionError(
                f'Mismatch of observable parameter overrides for '
                f'{observables[f"observable_{row.observableId}"]} '
                f'in:\n{row}\n'
                f'Expected 0 or {expected} but got {actual}')

        expected = noise_parameters_count[row.observableId]
        actual = len(
            core.split_parameter_replacement_list(row.noiseParameters))
        # No overrides are also allowed
        if not (actual == 0 or actual == expected):
            raise AssertionError(
                f'Mismatch of noise parameter overrides in:\n{row}\n'
                f'Expected 0 or {expected} but got {actual}')


def print_sbml_errors(sbml_document, minimum_severity=libsbml.LIBSBML_SEV_WARNING):
    """Print libsbml errors

    Arguments:
        sbml_document: libsbml.Document
        minimum_severity: minimum severity level to print
        (see libsbml.LIBSBML_SEV_*)
    """

    for error_idx in range(sbml_document.getNumErrors()):
        error = sbml_document.getError(error_idx)
        if error.getSeverity() >= minimum_severity:
            category = error.getCategoryAsString()
            severity = error.getSeverityAsString()
            message = error.getMessage()
            print(f'libSBML {severity} ({category}): {message}')


def lint_problem(problem):
    """Run PEtab validation on problem

    Arguments:
        problem: petab.Problem
    """

    check_measurement_df(problem.measurement_df)
    check_condition_df(problem.condition_df)
    check_parameter_sheet(problem)
    assert_measured_observables_present_in_model(
        problem.measurement_df, problem.sbml_model)
    assert_overrides_match_parameter_count(
        problem.measurement_df,
        core.get_observables(problem.sbml_model, remove=False),
        core.get_sigmas(problem.sbml_model, remove=False)
    )
