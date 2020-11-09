"""Integrity checks and tests for specific features used"""

import copy
import logging
import numbers
import re
from typing import Optional, Iterable
from collections import Counter

import libsbml
import numpy as np
import pandas as pd
import sympy as sp

import petab
from . import (core, parameters, sbml, measurements)
from .C import *  # noqa: F403

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
        df: pd.DataFrame, sbml_model: Optional[libsbml.Model] = None) -> None:
    """Run sanity checks on PEtab condition table

    Arguments:
        df: PEtab condition DataFrame
        sbml_model: SBML Model for additional checking of parameter IDs

    Raises:
        AssertionError: in case of problems
    """

    # Check required columns are present
    req_cols = []
    _check_df(df, req_cols, "condition")

    # Check for correct index
    if not df.index.name == CONDITION_ID:
        raise AssertionError(
            f"Condition table has wrong index {df.index.name}."
            f"expected {CONDITION_ID}.")

    check_ids(df.index.values, kind='condition')

    for column_name in req_cols:
        if not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    if sbml_model is not None:
        for column_name in df.columns:
            if column_name != CONDITION_NAME \
                    and sbml_model.getParameter(column_name) is None \
                    and sbml_model.getSpecies(column_name) is None \
                    and sbml_model.getCompartment(column_name) is None:
                raise AssertionError(
                    "Condition table contains column for unknown entity '"
                    f"{column_name}'. Column names must match parameter, "
                    "species or compartment IDs specified in the SBML model.")


def check_measurement_df(df: pd.DataFrame,
                         observable_df: Optional[pd.DataFrame] = None) -> None:
    """Run sanity checks on PEtab measurement table

    Arguments:
        df: PEtab measurement DataFrame
        observable_df: PEtab observable DataFrame for checking if measurements
            are compatible with observable transformations.

    Raises:
        AssertionError, ValueError: in case of problems
    """

    _check_df(df, MEASUREMENT_DF_REQUIRED_COLS, "measurement")

    for column_name in MEASUREMENT_DF_REQUIRED_COLS:
        if not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    for column_name in MEASUREMENT_DF_OPTIONAL_COLS:
        if column_name in df \
                and not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    if observable_df is not None:
        # Check all observables are defined
        observables_defined = set(observable_df.index.values)
        observables_used = set(df[OBSERVABLE_ID])
        observables_undefined = observables_used - observables_defined
        if observables_undefined:
            raise ValueError(f"Observables {observables_undefined} used in "
                             "measurement table but not defined in "
                             "observables table.")

        if OBSERVABLE_TRANSFORMATION in observable_df:
            # Check for positivity of measurements in case of
            #  log-transformation
            assert_unique_observable_ids(observable_df)
            # If the above is not checked, in the following loop
            # trafo may become a pandas Series
            for measurement, obs_id in zip(df[MEASUREMENT], df[OBSERVABLE_ID]):
                trafo = observable_df.loc[obs_id, OBSERVABLE_TRANSFORMATION]
                if measurement <= 0.0 and trafo in [LOG, LOG10]:
                    raise ValueError('Measurements with observable '
                                     f'transformation {trafo} must be '
                                     f'positive, but {measurement} <= 0.')

    if observable_df is not None:
        assert_measured_observables_defined(df, observable_df)
        measurements.assert_overrides_match_parameter_count(
            df, observable_df)


def check_parameter_df(
        df: pd.DataFrame,
        sbml_model: Optional[libsbml.Model] = None,
        observable_df: Optional[pd.DataFrame] = None,
        measurement_df: Optional[pd.DataFrame] = None,
        condition_df: Optional[pd.DataFrame] = None) -> None:
    """Run sanity checks on PEtab parameter table

    Arguments:
        df: PEtab condition DataFrame
        sbml_model: SBML Model for additional checking of parameter IDs
        observable_df: PEtab observable table for additional checks
        measurement_df: PEtab measurement table for additional checks
        condition_df: PEtab condition table for additional checks

    Raises:
        AssertionError: in case of problems
    """

    _check_df(df, PARAMETER_DF_REQUIRED_COLS[1:], "parameter")

    if not df.index.name == PARAMETER_ID:
        raise AssertionError(
            f"Parameter table has wrong index {df.index.name}."
            f"expected {PARAMETER_ID}.")

    check_ids(df.index.values, kind='parameter')

    for column_name in PARAMETER_DF_REQUIRED_COLS[1:]:  # 0 is PARAMETER_ID
        if not np.issubdtype(df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                df[column_name].values, column_name)

    # nominal value is generally optional, but required if any for any
    #  parameter estimate != 1
    non_estimated_par_ids = list(
        df.index[(df[ESTIMATE] != 1) | (
            pd.api.types.is_string_dtype(df[ESTIMATE])
            and df[ESTIMATE] != '1')])
    if non_estimated_par_ids:
        if NOMINAL_VALUE not in df:
            raise AssertionError("Parameter table contains parameters "
                                 f"{non_estimated_par_ids} that are not "
                                 "specified to be estimated, "
                                 f"but column {NOMINAL_VALUE} is missing.")
        try:
            df.loc[non_estimated_par_ids, NOMINAL_VALUE].apply(float)
        except ValueError:
            raise AssertionError("Expected numeric values for "
                                 f"`{NOMINAL_VALUE}` in parameter table for "
                                 "all non-estimated parameters.")

    assert_parameter_id_is_string(df)
    assert_parameter_scale_is_valid(df)
    assert_parameter_bounds_are_numeric(df)
    assert_parameter_estimate_is_boolean(df)
    assert_unique_parameter_ids(df)
    check_parameter_bounds(df)
    assert_parameter_prior_type_is_valid(df)

    if sbml_model and measurement_df is not None \
            and condition_df is not None:
        assert_all_parameters_present_in_parameter_df(
            df, sbml_model, observable_df, measurement_df, condition_df)


def check_observable_df(observable_df: pd.DataFrame) -> None:
    """Check validity of observable table

    Arguments:
        observable_df: PEtab observable DataFrame

    Raises:
        AssertionError: in case of problems
    """
    _check_df(observable_df, OBSERVABLE_DF_REQUIRED_COLS[1:], "observable")

    check_ids(observable_df.index.values, kind='observable')

    for column_name in OBSERVABLE_DF_REQUIRED_COLS[1:]:
        if not np.issubdtype(observable_df[column_name].dtype, np.number):
            assert_no_leading_trailing_whitespace(
                observable_df[column_name].values, column_name)

    for column_name in OBSERVABLE_DF_OPTIONAL_COLS:
        if column_name in observable_df \
                and not np.issubdtype(observable_df[column_name].dtype,
                                      np.number):
            assert_no_leading_trailing_whitespace(
                observable_df[column_name].values, column_name)

    assert_noise_distributions_valid(observable_df)
    assert_unique_observable_ids(observable_df)

    # Check that formulas are parsable
    for row in observable_df.itertuples():
        obs = getattr(row, OBSERVABLE_FORMULA)
        try:
            sp.sympify(obs)
        except sp.SympifyError as e:
            raise AssertionError(f"Cannot parse expression '{obs}' "
                                 f"for observable {row.Index}: {e}")

        noise = getattr(row, NOISE_FORMULA)
        try:
            sp.sympify(noise)
        except sp.SympifyError as e:
            raise AssertionError(f"Cannot parse expression '{noise}' "
                                 f"for noise model for observable "
                                 f"{row.Index}: {e}")


def assert_all_parameters_present_in_parameter_df(
        parameter_df: pd.DataFrame,
        sbml_model: libsbml.Model,
        observable_df: pd.DataFrame,
        measurement_df: pd.DataFrame,
        condition_df: pd.DataFrame) -> None:
    """Ensure all required parameters are contained in the parameter table
    with no additional ones

    Arguments:
        parameter_df: PEtab parameter DataFrame
        sbml_model: PEtab SBML Model
        observable_df: PEtab observable table
        measurement_df: PEtab measurement table
        condition_df: PEtab condition table

    Raises:
        AssertionError: in case of problems
    """

    required = parameters.get_required_parameters_for_parameter_table(
        sbml_model=sbml_model, condition_df=condition_df,
        observable_df=observable_df, measurement_df=measurement_df)

    allowed = parameters.get_valid_parameters_for_parameter_table(
        sbml_model=sbml_model, condition_df=condition_df,
        observable_df=observable_df, measurement_df=measurement_df)

    actual = set(parameter_df.index)

    missing = required - actual
    extraneous = actual - allowed

    if missing:
        raise AssertionError('Missing parameter(s) in parameter table: '
                             + str(missing))

    if extraneous:
        raise AssertionError('Extraneous parameter(s) in parameter table: '
                             + str(extraneous))


def assert_measured_observables_defined(
        measurement_df: pd.DataFrame,
        observable_df: pd.DataFrame) -> None:
    """Check if all observables in the measurement table have been defined in the
    observable table

    Arguments:
        measurement_df: PEtab measurement table
        observable_df: PEtab observable table

    Raises:
        AssertionError: in case of problems
    """

    used_observables = set(measurement_df[OBSERVABLE_ID].values)
    defined_observables = set(observable_df.index.values)
    undefined_observables = used_observables - defined_observables

    if undefined_observables:
        raise AssertionError(
            "Undefined observables in measurement file: "
            f"{undefined_observables}.")


def condition_table_is_parameter_free(condition_df: pd.DataFrame) -> bool:
    """Check if all entries in the condition table are numeric
    (no parameter IDs)

    Arguments:
        condition_df: PEtab condition table

    Returns:
        True if there are no parameter overrides in the condition table,
        False otherwise.
    """

    return len(petab.get_parametric_overrides(condition_df)) == 0


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
                raise AssertionError(
                    f"{PARAMETER_ID} {parameter_id} starts with integer.")
        else:
            raise AssertionError(f"Empty {PARAMETER_ID} found.")


def assert_unique_parameter_ids(parameter_df: pd.DataFrame) -> None:
    """
    Check if the parameterId column of the parameter table is unique.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """
    non_unique_ids = get_non_unique(parameter_df.index)
    if len(non_unique_ids) > 0:
        raise AssertionError(
            f"Non-unique values found in the {PARAMETER_ID} column"
            " of the parameter table: " + str(non_unique_ids))


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
    for parameter_scale in parameter_df[PARAMETER_SCALE]:
        if parameter_scale not in [LIN, LOG, LOG10]:
            raise AssertionError(f"Expected {LIN}, {LOG}, or {LOG10}, but "
                                 f"got {parameter_scale}.")


def assert_parameter_bounds_are_numeric(parameter_df: pd.DataFrame) -> None:
    """
    Check if all entries in the lowerBound and upperBound columns of the
    parameter table are numeric.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """
    parameter_df[LOWER_BOUND].apply(float).all()
    parameter_df[UPPER_BOUND].apply(float).all()


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
        if int(row[ESTIMATE]):
            if not row[LOWER_BOUND] <= row[UPPER_BOUND]:
                raise AssertionError(
                    f"{LOWER_BOUND} greater than {UPPER_BOUND} for "
                    f"{PARAMETER_ID} {row.name}.")
            if (row[LOWER_BOUND] <= 0.0 or row[UPPER_BOUND] < 0.0) \
                    and row[PARAMETER_SCALE] in [LOG, LOG10]:
                raise AssertionError(
                    f"Bounds for {row[PARAMETER_SCALE]} scaled parameter "
                    f"{ row.name} must be positive.")


def assert_parameter_prior_type_is_valid(
        parameter_df: pd.DataFrame) -> None:
    """Check that valid prior types have been selected

    Arguments:
        parameter_df: PEtab parameter table

    Raises:
        AssertionError in case of invalid prior
    """
    for col in [INITIALIZATION_PRIOR_TYPE, OBJECTIVE_PRIOR_TYPE]:
        if col not in parameter_df.columns:
            continue
        for _, row in parameter_df.iterrows():
            if row[col] not in PRIOR_TYPES and not core.is_empty(row[col]):
                raise AssertionError(
                    f"{col} must be one of {PRIOR_TYPES} but is "
                    f"'{row[col]}'.")


def assert_parameter_prior_parameters_are_valid(
        parameter_df: pd.DataFrame) -> None:
    """Check that the prior parameters are valid.

    Arguments:
        parameter_df: PEtab parameter table

    Raises:
        AssertionError in case of invalide prior parameters
    """
    prior_type_cols = [INITIALIZATION_PRIOR_TYPE,
                       OBJECTIVE_PRIOR_TYPE]
    prior_par_cols = [INITIALIZATION_PRIOR_PARAMETERS,
                      OBJECTIVE_PRIOR_PARAMETERS]

    # perform test for both priors
    for type_col, par_col in zip(prior_type_cols, prior_par_cols):
        # iterate over rows
        for _, row in parameter_df.iterrows():
            # get type
            if type_col not in row or core.is_empty(row[type_col]):
                type_ = PARAMETER_SCALE_UNIFORM
            else:
                type_ = row[type_col]
            # get parameters
            pars_str = row.get(par_col, '')
            with_default_parameters = [PARAMETER_SCALE_UNIFORM]
            # check if parameters are empty
            if core.is_empty(pars_str):
                if type_ not in with_default_parameters:
                    raise AssertionError(
                        f"An empty {par_col} is only permitted with "
                        f"{type_col} in {with_default_parameters}.")
                # empty parameters fine
                continue
            # parse parameters
            try:
                pars = tuple([float(val) for val in pars_str.split(';')])
            except ValueError:
                raise AssertionError(
                    f"Could not parse prior parameters '{pars_str}'.")
            # all distributions take 2 parameters
            if len(pars) != 2:
                raise AssertionError(
                    f"The prior parameters '{pars}' do not contain the "
                    "expected number of entries (currently 'par1;par2' "
                    "for all prior types).")


def assert_parameter_estimate_is_boolean(parameter_df: pd.DataFrame) -> None:
    """
    Check if all entries in the estimate column of the parameter table are
    0 or 1.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Raises:
        AssertionError: in case of problems
    """
    for estimate in parameter_df[ESTIMATE]:
        if int(estimate) not in [True, False]:
            raise AssertionError(
                f"Expected 0 or 1 but got {estimate} in {ESTIMATE} column.")


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

    if NOISE_PARAMETERS not in measurement_df:
        measurement_df[NOISE_PARAMETERS] = np.nan

    measurement_df.loc[
        measurement_df.noiseParameters.apply(isinstance, args=(
            numbers.Number,)), NOISE_PARAMETERS] = np.nan

    grouping_cols = core.get_notnull_columns(
        measurement_df,
        [OBSERVABLE_ID,
         SIMULATION_CONDITION_ID,
         PREEQUILIBRATION_CONDITION_ID,
         OBSERVABLE_PARAMETERS,
         NOISE_PARAMETERS,
         ])
    grouped_df = measurement_df.fillna('').groupby(grouping_cols).size()\
        .reset_index()

    grouping_cols = core.get_notnull_columns(
        grouped_df,
        [OBSERVABLE_ID,
         SIMULATION_CONDITION_ID,
         PREEQUILIBRATION_CONDITION_ID])
    grouped_df2 = grouped_df.groupby(grouping_cols).size().reset_index()

    if len(grouped_df.index) != len(grouped_df2.index):
        logger.warning("Measurement table has timepoint-specific "
                       f"mappings:\n{grouped_df}")
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
    if OBSERVABLE_PARAMETERS not in measurement_df:
        return False

    for _, row in measurement_df.iterrows():
        for override in measurements.split_parameter_replacement_list(
                row.get(OBSERVABLE_PARAMETERS, None)):
            if isinstance(override, numbers.Number):
                return True

    return False


def assert_noise_distributions_valid(observable_df: pd.DataFrame) -> None:
    """
    Ensure that noise distributions and transformations for observables are
    valid.

    Arguments:
        observable_df: PEtab observable table

    Raises:
        AssertionError: in case of problems
    """
    if OBSERVABLE_TRANSFORMATION in observable_df:
        # check for valid values
        for trafo in observable_df[OBSERVABLE_TRANSFORMATION]:
            if trafo not in ['', *OBSERVABLE_TRANSFORMATIONS] \
                    and not (isinstance(trafo, numbers.Number)
                             and np.isnan(trafo)):
                raise ValueError(
                    f"Unrecognized observable transformation in observable "
                    f"table: {trafo}.")

    if NOISE_DISTRIBUTION in observable_df:
        for distr in observable_df[NOISE_DISTRIBUTION]:
            if distr not in ['', *NOISE_MODELS] \
                    and not (isinstance(distr, numbers.Number)
                             and np.isnan(distr)):
                raise ValueError(
                    f"Unrecognized noise distribution in observable "
                    f"table: {distr}.")


def assert_unique_observable_ids(observable_df: pd.DataFrame) -> None:
    """
    Check if the observableId column of the observable table is unique.

    Arguments:
        observable_df: PEtab observable DataFrame

    Raises:
        AssertionError: in case of problems
    """
    non_unique_ids = get_non_unique(observable_df.index)
    if len(non_unique_ids) > 0:
        raise AssertionError(
            f"Non-unique values found in the {OBSERVABLE_ID} column"
            " of the observable table: " + str(non_unique_ids))


def get_non_unique(values):
    counter = Counter(values)
    return [value for (value, count) in counter.items() if count > 1]


def lint_problem(problem: 'petab.Problem') -> bool:
    """Run PEtab validation on problem

    Arguments:
        problem: PEtab problem to check

    Returns:
        True is errors occurred, False otherwise
    """
    # pylint: disable=too-many-statements
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
            check_measurement_df(problem.measurement_df, problem.observable_df)

            if problem.condition_df is not None:
                assert_measurement_conditions_present_in_condition_table(
                    problem.measurement_df, problem.condition_df
                )
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

    if problem.observable_df is not None:
        logger.info("Checking observable table...")
        try:
            check_observable_df(problem.observable_df)
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True
        if problem.sbml_model is not None:
            for obs_id in problem.observable_df.index:
                if problem.sbml_model.getElementBySId(obs_id):
                    logger.error(f"Observable ID {obs_id} shadows model "
                                 "entity.")
                    errors_occurred = True
    else:
        logger.warning("Observable table not available. Skipping.")

    if problem.parameter_df is not None:
        logger.info("Checking parameter table...")
        try:
            check_parameter_df(problem.parameter_df, problem.sbml_model,
                               problem.observable_df,
                               problem.measurement_df, problem.condition_df)
        except AssertionError as e:
            logger.error(e)
            errors_occurred = True
    else:
        logger.warning("Parameter table not available. Skipping.")

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
            or problem.sbml_model is None or problem.parameter_df is None \
            or problem.observable_df is None:
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


def assert_measurement_conditions_present_in_condition_table(
        measurement_df: pd.DataFrame, condition_df: pd.DataFrame) -> None:
    """Ensure that all entries from measurement_df.simulationConditionId and
    measurement_df.preequilibrationConditionId are present in
    condition_df.index.

    Arguments:
        measurement_df: PEtab measurement table
        condition_df: PEtab condition table

    Raises:
        AssertionError: in case of problems
    """

    used_conditions = set(measurement_df[SIMULATION_CONDITION_ID].values)
    if PREEQUILIBRATION_CONDITION_ID in measurement_df:
        used_conditions |= \
            set(measurement_df[PREEQUILIBRATION_CONDITION_ID].dropna().values)
    available_conditions = set(condition_df.index.values)
    missing_conditions = used_conditions - available_conditions

    if missing_conditions:
        raise AssertionError("Measurement table references conditions that "
                             "are not specified in the condition table: "
                             + str(missing_conditions))


def is_valid_identifier(x: str) -> bool:
    """Check whether `x` is a valid identifier

    Check whether `x` is a valid identifier for conditions, parameters,
    observables... . Identifiers may contain upper and lower case letters,
    digits and underscores, but must not start with a digit.

    Arguments:
        x: string to check

    Returns:
        ``True`` if valid, ``False`` otherwise
    """
    if pd.isna(x):
        return False

    return re.match(r'^[a-zA-Z_]\w*$', x) is not None


def check_ids(ids: Iterable[str], kind: str = '') -> None:
    """Check IDs are valid

    Arguments:
        ids: Iterable of IDs to check
        kind: Kind of IDs, for more informative error message

    Raises:
        ValueError - in case of invalid IDs
    """
    invalids = [(index, _id)
                for index, _id in enumerate(ids)
                if not is_valid_identifier(_id)]

    if invalids:
        # The first row is the header row, and Python lists are zero-indexed,
        # hence need to add 2 for the correct line number.
        offset = 2
        error_output = '\n'.join([
            f'Line {index+offset}: ' +
            ('Missing ID' if pd.isna(_id) else _id)
            for index, _id in invalids])
        raise ValueError(f"Invalid {kind} ID(s):\n{error_output}")
