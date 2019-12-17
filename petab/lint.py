"""Integrity checks and tests for specific features used"""

import copy
import logging
import numbers
import re
from typing import Optional, Iterable

import libsbml
import numpy as np
import pandas as pd

import petab
from . import (core, parameters, sbml, measurements)

logger = logging.getLogger(__name__)


def _check_df(df: pd.DataFrame, req_cols: Iterable, name: str) -> None:
    """Check if given columns are present in DataFrame

    Arguments:
        df: Dataframe to check
        req_cols: Column names which have to be present
        name: Name of the DataFrame to be included in error message

    Raises:
          AssertionError: if a column is missing
    """
    cols_set = df.columns.values
    missing_cols = set(req_cols) - set(cols_set)
    if missing_cols:
        raise AssertionError(
            f"DataFrame {name} requires the columns {missing_cols}.")


def assert_no_leading_trailing_whitespace(
        names_list: Iterable[str], name: str) -> None:
    """Check that there is no trailing whitespace in elements of Iterable

    Arguments:
        names_list: strings to check for whitespace
        name: name of `names_list` for error messages

    Raises:
        AssertionError: if there is trailing whitespace
    """
    r = re.compile(r'(?:^\s)|(?:\s$)')
    for i, x in enumerate(names_list):
        if isinstance(x, str) and r.search(x):
            raise AssertionError(f"Whitespace around {name}[{i}] = '{x}'.")


def check_condition_df(
        df: pd.DataFrame, sbml_model: Optional[libsbml.Model]) -> None:
    """Run sanity checks on PEtab condition table

    Arguments:
        df: PEtab condition DataFrame
        sbml_model: SBML Model for additional checking of parameter IDs

    Raises:
        AssertionError: in case of problems
    """
    req_cols = []
    _check_df(df, req_cols, "condition")

    if not df.index.name == 'conditionId':
        raise AssertionError(
            f"Condition table has wrong index {df.index.name}."
            "expected 'conditionId'.")

    assert_no_leading_trailing_whitespace(df.index.values, "conditionId")

    for column_name in req_cols:
        if not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    if sbml_model is not None:
        for column_name in df.columns:
            if column_name != 'conditionName' \
                    and sbml_model.getParameter(column_name) is None:
                raise AssertionError(
                    "Condition table contains column for unknown parameter"
                    f" {column_name}. Column names must match parameter Ids "
                    "defined in the SBML model.")


def check_measurement_df(df: pd.DataFrame) -> None:
    """Run sanity checks on PEtab measurement table

    Arguments:
        df: PEtab measurement DataFrame

    Raises:
        AssertionError: in case of problems
    """

    required_columns = [
        "observableId", "simulationConditionId", "measurement", "time"
    ]
    optional_columns = [
        "preequilibrationConditionId",
        "observableParameters", "noiseParameters"
    ]

    _check_df(df, required_columns, "measurement")

    for column_name in required_columns:
        if not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    for column_name in optional_columns:
        if column_name in df \
                and not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)


def check_parameter_df(
        df: pd.DataFrame,
        sbml_model: Optional[libsbml.Model],
        measurement_df: Optional[pd.DataFrame],
        condition_df: Optional[pd.DataFrame]) -> None:
    """Run sanity checks on PEtab parameter table

    Arguments:
        df: PEtab condition DataFrame
        sbml_model: SBML Model for additional checking of parameter IDs
        measurement_df: PEtab measurement table for additional checks
        condition_df: PEtab condition table for additional checks

    Raises:
        AssertionError: in case of problems
    """

    req_cols = [
        "parameterName", "parameterScale",
        "lowerBound", "upperBound", "nominalValue", "estimate"
    ]
    _check_df(df, req_cols, "parameter")

    if not df.index.name == 'parameterId':
        raise AssertionError(
            f"Parameter table has wrong index {df.index.name}."
            "expected 'parameterId'.")

    assert_no_leading_trailing_whitespace(df.index.values, "parameterId")

    for column_name in req_cols:
        if not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    assert_parameter_id_is_string(df)
    assert_parameter_scale_is_valid(df)
    assert_parameter_bounds_are_numeric(df)
    assert_parameter_estimate_is_boolean(df)
    assert_parameter_id_is_unique(df)
    check_parameter_bounds(df)

    if sbml_model and measurement_df is not None \
            and condition_df is not None:
        assert_all_parameters_present_in_parameter_df(
            df, sbml_model, measurement_df, condition_df)


def assert_all_parameters_present_in_parameter_df(
        parameter_df: pd.DataFrame,
        sbml_model: libsbml.Model,
        measurement_df: pd.DataFrame,
        condition_df: pd.DataFrame) -> None:
    """Ensure all required parameters are contained in the parameter table
    with no additional ones

    Arguments:
        parameter_df: PEtab parameter DataFrame
        sbml_model: PEtab SBML Model
        measurement_df: PEtab measurement table
        condition_df: PEtab condition table

    Raises:
        AssertionError: in case of problems
    """

    expected = parameters.get_required_parameters_for_parameter_table(
        sbml_model=sbml_model, condition_df=condition_df,
        measurement_df=measurement_df)

    actual = set(parameter_df.index)

    missing = expected - actual
    extraneous = actual - expected

    if missing:
        raise AssertionError('Missing parameter(s) in parameter table: '
                             + str(missing))

    if extraneous:
        raise AssertionError('Extraneous parameter(s) in parameter table: '
                             + str(extraneous))


def assert_measured_observables_present_in_model(
        measurement_df: pd.DataFrame,
        sbml_model: libsbml.Model) -> None:
    """Check if all observables in measurement files have been specified in
    the model

    Arguments:
        sbml_model: PEtab SBML Model
        measurement_df: PEtab measurement table

    Raises:
        AssertionError: in case of problems
    """

    measurement_observables = [f'observable_{x}' for x in
                               measurement_df.observableId.values]

    model_observables = sbml.get_observables(sbml_model)
    undefined_observables = set(measurement_observables) - set(
        model_observables.keys())

    if len(undefined_observables):
        raise AssertionError(
            f"Unknown observables in measurement file: "
            f"{undefined_observables}.")


def condition_table_is_parameter_free(condition_df: pd.DataFrame) -> bool:
    """Check if all entries in the condition table are numeric
    (no parameter IDs)

    Arguments:
        condition_df: PEtab condition table

    Returns:
        True if there are no parameter overrides in the condition table,
        False otherweise.
    """

    constant_parameters = list(
        set(condition_df.columns.values.tolist()) - {'conditionId',
                                                     'conditionName'})

    for column in constant_parameters:
        if np.any(np.invert(condition_df.loc[:, column].apply(
                isinstance, args=(numbers.Number,)))):
            return False
    return True


def assert_parameter_id_is_string(parameter_df: pd.DataFrame) -> None:
    """
    Check if all entries in the parameterId column of the parameter table
    are string and not empty.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """

    for parameter_id in parameter_df:
        if isinstance(parameter_id, str):
            if parameter_id[0].isdigit():
                raise AssertionError('parameterId ' + parameter_id
                                     + ' starts with integer')
        else:
            raise AssertionError('Empty parameterId found')


def assert_parameter_id_is_unique(parameter_df: pd.DataFrame) -> None:
    """
    Check if the parameterId column of the parameter table is unique.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """
    if len(parameter_df.index) != len(set(parameter_df.index)):
        raise AssertionError(
            'parameterId column in parameter table is not unique')


def assert_parameter_scale_is_valid(parameter_df: pd.DataFrame) -> None:
    """
    Check if all entries in the parameterScale column of the parameter table
    are 'lin' for linear, 'log' for natural logarithm or 'log10' for base 10
    logarithm.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """

    for parameter_scale in parameter_df['parameterScale']:
        if parameter_scale not in ['lin', 'log', 'log10']:
            raise AssertionError(
                'Expected "lin", "log" or "log10" but got "' +
                parameter_scale + '"')


def assert_parameter_bounds_are_numeric(parameter_df: pd.DataFrame) -> None:
    """
    Check if all entries in the lowerBound and upperBound columns of the
    parameter table are numeric.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """
    parameter_df["lowerBound"].apply(float).all()
    parameter_df["upperBound"].apply(float).all()


def check_parameter_bounds(parameter_df: pd.DataFrame) -> None:
    """
    Check if all entries in the lowerBound are smaller than upperBound column
    in the parameter table and that bounds are positive for parameterScale
    log|log10.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems

    """
    for _, row in parameter_df.iterrows():
        if int(row['estimate']):
            if not row['lowerBound'] <= row['upperBound']:
                raise AssertionError(
                    f"lowerBound greater than upperBound for parameterId "
                    f"{row.name}.")
            if (row['lowerBound'] <= 0.0 or row['upperBound'] < 0.0) \
                    and row['parameterScale'] in ['log', 'log10']:
                raise AssertionError(
                    f'Bounds for {row["parameterScale"]} scaled parameter'
                    f' {row.name} must be positive.')


def assert_parameter_estimate_is_boolean(parameter_df: pd.DataFrame) -> None:
    """
    Check if all entries in the estimate column of the parameter table are
    0 or 1.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """
    for estimate in parameter_df['estimate']:
        if int(estimate) not in [True, False]:
            raise AssertionError(
                f"Expected 0 or 1 but got {estimate} in estimate column.")


def measurement_table_has_timepoint_specific_mappings(
        measurement_df: pd.DataFrame) -> bool:
    """
    Are there time-point or replicate specific parameter assignments in the
    measurement table.

    Arguments:
        measurement_df: PEtab measurement table

    Returns:
        True if there are time-point or replicate specific parameter
        assignments in the measurement table, False otherwise.
    """
    # since we edit it, copy it first
    measurement_df = copy.deepcopy(measurement_df)

    measurement_df.loc[
        measurement_df.noiseParameters.apply(isinstance, args=(
            numbers.Number,)), 'noiseParameters'] = np.nan

    grouping_cols = core.get_notnull_columns(
        measurement_df,
        ['observableId',
         'simulationConditionId',
         'preequilibrationConditionId',
         'observableParameters',
         'noiseParameters'
         ])
    grouped_df = measurement_df.groupby(grouping_cols).size().reset_index()

    grouping_cols = core.get_notnull_columns(
        grouped_df,
        ['observableId',
         'simulationConditionId',
         'preequilibrationConditionId'])
    grouped_df2 = grouped_df.groupby(grouping_cols).size().reset_index()

    if len(grouped_df.index) != len(grouped_df2.index):
        logger.warning(
            "Measurement table has timepoint specific mappings:\n"
            + str(grouped_df))
        return True
    return False


def measurement_table_has_observable_parameter_numeric_overrides(
        measurement_df: pd.DataFrame) -> bool:
    """Are there any numbers to override observable parameters?

    Arguments:
        measurement_df: PEtab measurement table

    Returns:
        True if there any numbers to override observable parameters,
        False otherwise.
    """
    if 'observableParameters' not in measurement_df:
        return False

    for i, row in measurement_df.iterrows():
        for override in measurements.split_parameter_replacement_list(
                row.observableParameters):
            if isinstance(override, numbers.Number):
                return True

    return False


def assert_noise_distributions_valid(measurement_df: pd.DataFrame) -> None:
    """
    Check whether there are not multiple noise distributions for an
    observable, and that the names are correct.

    Arguments:
        measurement_df: PEtab measurement table

    Raises:
        AssertionError: in case of problems
    """
    df = measurement_df.copy()

    # insert optional columns into copied df

    if 'observableTransformation' not in df:
        df['observableTransformation'] = ''
    if 'noiseDistribution' not in df:
        df['noiseDistribution'] = ''

    # check for valid values

    for trafo in df['observableTransformation']:
        if trafo not in ['', 'lin', 'log', 'log10'] \
                and not (isinstance(trafo, numbers.Number)
                         and np.isnan(trafo)):
            raise ValueError(
                f"Unrecognized observable transformation in measurement "
                f"file: {trafo}.")
    for distr in df['noiseDistribution']:
        if distr not in ['', 'normal', 'laplace'] \
                and not (isinstance(distr, numbers.Number)
                         and np.isnan(distr)):
            raise ValueError(
                f"Unrecognized noise distribution in measurement "
                f"file: {distr}.")

    # Check for positivity of measurements in case of log-transformation
    for mes, trafo in zip(df['measurement'],
                          df['observableTransformation']):
        if mes <= 0.0 and trafo in ['log', 'log10']:
            raise ValueError('Measurements with observable transformation '
                             f'{trafo} must be positive, but {mes} <= 0.')

    # check for unique values per observable

    distrs = df.groupby(['observableId']).size().reset_index()

    distrs_check = df.groupby(
        ['observableId', 'observableTransformation', 'noiseDistribution'])

    if len(distrs) != len(distrs_check):
        raise AssertionError(
            f"The noiseDistribution for an observable in the measurement "
            f"file is not unique: \n{distrs_check}")


def lint_problem(problem: 'petab.Problem') -> bool:
    """Run PEtab validation on problem

    Arguments:
        problem: PEtab problem to check

    Returns:
        True is errors occurred, False otherwise
    """
    errors_occurred = False

    # Run checks on individual files
    if problem.sbml_model is not None:
        logger.info("Checking SBML model...")
        errors_occurred |= not sbml.is_sbml_consistent(
            problem.sbml_model.getSBMLDocument())
        sbml.log_sbml_errors(problem.sbml_model.getSBMLDocument())
    else:
        logger.warning("SBML model not available. Skipping.")

    if problem.measurement_df is not None:
        logger.info("Checking measurement table...")
        try:
            check_measurement_df(problem.measurement_df)
            assert_noise_distributions_valid(problem.measurement_df)
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True
    else:
        logger.warning("Measurement table not available. Skipping.")

    if problem.condition_df is not None:
        logger.info("Checking condition table...")
        try:
            check_condition_df(problem.condition_df, problem.sbml_model)
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True
    else:
        logger.warning("Condition table not available. Skipping.")

    if problem.parameter_df is not None:
        logger.info("Checking parameter table...")
        try:
            check_parameter_df(problem.parameter_df, problem.sbml_model,
                               problem.measurement_df, problem.condition_df)
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True
    else:
        logger.warning("Parameter table not available. Skipping.")

    if problem.measurement_df is not None and problem.sbml_model is not None \
            and not errors_occurred:
        try:
            assert_measured_observables_present_in_model(
                problem.measurement_df, problem.sbml_model)
            measurements.assert_overrides_match_parameter_count(
                problem.measurement_df,
                sbml.get_observables(problem.sbml_model, remove=False),
                sbml.get_sigmas(problem.sbml_model, remove=False)
            )
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True

    if problem.sbml_model is not None and problem.condition_df is not None \
            and problem.parameter_df is not None:
        try:
            assert_model_parameters_in_condition_or_parameter_table(
                problem.sbml_model,
                problem.condition_df,
                problem.parameter_df
            )
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True

    if errors_occurred:
        logger.error('Not OK')
    elif problem.measurement_df is None or problem.condition_df is None \
            or problem.sbml_model is None or problem.parameter_df is None:
        logger.warning('Not all files of the PEtab problem definition could '
                       'be checked.')
    else:
        logger.info('OK')

    return errors_occurred


def assert_model_parameters_in_condition_or_parameter_table(
        sbml_model: libsbml.Model,
        condition_df: pd.DataFrame,
        parameter_df: pd.DataFrame) -> None:
    """Model parameters that are targets of AssignmentRule must not be present
    in parameter table or in condition table columns. Other parameters must
    only be present in either in parameter table or condition table columns.
    Check that.

    Arguments:
        parameter_df: PEtab parameter DataFrame
        sbml_model: PEtab SBML Model
        condition_df: PEtab condition table

    Raises:
        AssertionError: in case of problems
    """

    for parameter in sbml_model.getListOfParameters():
        parameter_id = parameter.getId()

        if parameter_id.startswith('observableParameter'):
            continue
        if parameter_id.startswith('noiseParameter'):
            continue

        is_assignee = \
            sbml_model.getAssignmentRuleByVariable(parameter_id) is not None
        in_parameter_df = parameter_id in parameter_df.index
        in_condition_df = parameter_id in condition_df.columns

        if is_assignee and (in_parameter_df or in_condition_df):
            raise AssertionError(f"Model parameter '{parameter_id}' is target "
                                 "of AssignmentRule, and thus, must not be "
                                 "present in condition table or in parameter "
                                 "table.")

        if in_parameter_df and in_condition_df:
            raise AssertionError(f"Model parameter '{parameter_id}' present "
                                 "in both condition table and parameter "
                                 "table.")
