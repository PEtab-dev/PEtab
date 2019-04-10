"""Integrity checks and tests for specific features used"""

from . import core
from . import sbml
import numpy as np
import numbers
import re
import copy
import logging
import libsbml
import pandas as pd

logger = logging.getLogger(__name__)


def _check_df(df, req_cols, name):
    cols_set = df.columns.values
    missing_cols = set(req_cols) - set(cols_set)
    if missing_cols:
        raise AssertionError(
            f"Dataframe {name} requires the columns {missing_cols}.")


def assert_no_leading_trailing_whitespace(names_list, name):
    r = re.compile(r'(?:^\s)|(?:\s$)')
    for i, x in enumerate(names_list):
        if isinstance(x, str) and r.search(x):
            raise AssertionError(f"Whitespace around {name}[{i}] = '{x}'.")


def check_condition_df(df):
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


def check_measurement_df(df):
    req_cols = [
        "observableId", "preequilibrationConditionId", "simulationConditionId",
        "measurement", "time", "observableParameters", "noiseParameters"
    ]

    for column_name in req_cols:
        if not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    _check_df(df, req_cols, "measurement")


def check_parameter_df(df):
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


def assert_measured_observables_present_in_model(measurement_df, sbml_model):
    """Check if all observables in measurement files have been specified in
    the model"""

    measurement_observables = [f'observable_{x}' for x in
                               measurement_df.observableId.values]

    model_observables = core.get_observables(sbml_model)
    undefined_observables = set(measurement_observables) - set(
        model_observables.keys())

    if len(undefined_observables):
        raise AssertionError(
            f"Unknown observables in measurement file: "
            f"{undefined_observables}.")


def condition_table_is_parameter_free(condition_df):
    """Check if all entries in the condition table are numeric
    (no parameter IDs)"""

    constant_parameters = list(
        set(condition_df.columns.values.tolist()) - {'conditionId',
                                                     'conditionName'})

    for column in constant_parameters:
        if np.any(np.invert(condition_df.loc[:, column].apply(
                isinstance, args=(numbers.Number,)))):
            return False
    return True


def assert_parameter_id_is_string(parameter_df):
    """
    Check if all entries in the parameterId column of the parameter table
    are string and not empty.
    """

    for parameterId in parameter_df:
        if isinstance(parameterId, str):
            if parameterId[0].isdigit():
                raise AssertionError('parameterId ' + parameterId
                                     + ' starts with integer')
        else:
            raise AssertionError('Empty parameterId found')


def assert_parameter_id_is_unique(parameter_df):
    """
    Check if the parameterId column of the parameter table is unique.
    """
    if len(parameter_df.index) != len(set(parameter_df.index)):
        raise AssertionError(
            'parameterId column in parameter table is not unique')


def assert_parameter_scale_is_valid(parameter_df):
    """
    Check if all entries in the parameterScale column of the parameter table
    are 'lin' for linear, 'log' for natural logarithm or 'log10' for base 10
    logarithm.
    """

    for parameterScale in parameter_df['parameterScale']:
        if parameterScale not in ['lin', 'log', 'log10']:
            raise AssertionError(
                'Expected "lin", "log" or "log10" but got "' +
                parameterScale + '"')


def assert_parameter_bounds_are_numeric(parameter_df):
    """
    Check if all entries in the lowerBound and upperBound columns of the
    parameter table are numeric.
    """
    parameter_df["lowerBound"].apply(float).all()
    parameter_df["upperBound"].apply(float).all()


def check_parameter_bounds(parameter_df):
    """
    Check if all entries in the lowerBound are smaller than upperBound column
    in the parameter table.
    """
    for element in range(len(parameter_df['lowerBound'])):
        if int(parameter_df['estimate'][element]):
            if not parameter_df['lowerBound'][element] \
                    <= parameter_df['upperBound'][element]:
                raise AssertionError(
                    f"lowerbound greater than upperBound for parameterId "
                    f"{parameter_df.index[element]}.")


def assert_parameter_estimate_is_boolean(parameter_df):
    """
    Check if all entries in the estimate column of the parameter table are
    0 or 1.
    """
    for estimate in parameter_df['estimate']:
        if not int(estimate) in [True, False]:
            raise AssertionError(
                f"Expected 0 or 1 but got {estimate} in estimate column.")


def measurement_table_has_timepoint_specific_mappings(measurement_df):
    """
    Are there time-point or replicate specific parameter assignments in the
    measurement table.
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
        measurement_df):
    """Are there any numbers to override observable parameters?"""

    for i, row in measurement_df.iterrows():
        for override in core.split_parameter_replacement_list(
                row.observableParameters):
            if isinstance(override, numbers.Number):
                return True
    return False


def assert_noise_distributions_valid(measurement_df):
    """
    Check whether there are not multiple noise distributions for an
    observable, and that the names are correct.
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

    # check for unique values per observable

    distrs = df.groupby(['observableId']).size().reset_index()

    distrs_check = df.groupby(
        ['observableId', 'observableTransformation', 'noiseDistribution'])

    if len(distrs) != len(distrs_check):
        raise AssertionError(
            f"The noiseDistribution for an observable in the measurement "
            f"file is not unique: \n{distrs_check}")


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
        # check observable parameters
        try:
            expected = observable_parameters_count[row.observableId]
        except KeyError:
            raise ValueError(
                f"Observable {row.observableId} used in measurement table "
                f"but not defined in model {observables.keys()}.")
        actual = len(
            core.split_parameter_replacement_list(row.observableParameters))
        # No overrides are also allowed
        if not (actual == 0 or actual == expected):
            raise AssertionError(
                f'Mismatch of observable parameter overrides for '
                f'{observables[f"observable_{row.observableId}"]} '
                f'in:\n{row}\n'
                f'Expected 0 or {expected} but got {actual}')

        # check noise parameters
        replacements = core.split_parameter_replacement_list(
            row.noiseParameters)
        try:
            expected = noise_parameters_count[row.observableId]

            # No overrides are also allowed
            if not (len(replacements) == 0 or len(replacements) == expected):
                raise AssertionError(
                    f'Mismatch of noise parameter overrides in:\n{row}\n'
                    f'Expected 0 or {expected} but got {actual}')
        except KeyError:
            # no overrides defined, but a numerical sigma can be provided
            # anyways
            if not len(replacements) == 1 \
                    or not isinstance(replacements[0], numbers.Number):
                raise AssertionError(
                    f'No placeholders have been specified in the noise model '
                    f'SBML AssigmentRule for: '
                    f'\n{row}\n'
                    f'But parameter name or multiple overrides were specified '
                    'in the noiseParameters column.')


def lint_problem(problem: 'core.Problem'):
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
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True
    else:
        logger.warning("Measurement table not available. Skipping.")

    if problem.condition_df is not None:
        logger.info("Checking condition table...")
        try:
            check_condition_df(problem.condition_df)
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True
    else:
        logger.warning("Condition table not available. Skipping.")

    if problem.parameter_df is not None:
        logger.info("Checking parameter table...")
        try:
            check_parameter_df(problem.parameter_df)
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
            assert_overrides_match_parameter_count(
                problem.measurement_df,
                core.get_observables(problem.sbml_model, remove=False),
                core.get_sigmas(problem.sbml_model, remove=False)
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
        parameter_df: pd.DataFrame):
    """Model parameters that are targets of AssignmentRule must not be present
    in parameter table or in condition table columns. Other parameters must
    only be present in either in parameter table or condition table columns.
    Check that."""

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
