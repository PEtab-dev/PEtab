import os
import subprocess
from math import nan
from unittest.mock import patch

import libsbml
import pandas as pd
import pytest

import petab
from petab import (lint, sbml)  # noqa: E402
from petab.C import *

# import fixtures
pytest_plugins = [
    "tests.test_petab",
]


def test_assert_measured_observables_present_in_model():
    # create test model

    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['non-existing1'],
    })

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1'],
    })
    observable_df.set_index(OBSERVABLE_ID, inplace=True)

    with pytest.raises(AssertionError):
        lint.assert_measured_observables_defined(
            measurement_df, observable_df
        )


def test_condition_table_is_parameter_free():
    with patch('petab.get_parametric_overrides') \
            as mock_get_parametric_overrides:
        mock_get_parametric_overrides.return_value = []
        assert lint.condition_table_is_parameter_free(pd.DataFrame()) is True
        mock_get_parametric_overrides.assert_called_once()

        mock_get_parametric_overrides.reset_mock()
        mock_get_parametric_overrides.return_value = ['p1']
        assert lint.condition_table_is_parameter_free(pd.DataFrame()) is False
        mock_get_parametric_overrides.assert_called_once()


def test_measurement_table_has_timepoint_specific_mappings():
    # Ensure we fail if we have time-point specific assignments

    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1', 'obs1'],
        SIMULATION_CONDITION_ID: ['condition1', 'condition1'],
        PREEQUILIBRATION_CONDITION_ID: ['', ''],
        TIME: [1.0, 2.0],
        OBSERVABLE_PARAMETERS: ['obsParOverride', ''],
        NOISE_PARAMETERS: ['', '']
    })

    assert lint.measurement_table_has_timepoint_specific_mappings(
        measurement_df) is True

    measurement_df.loc[1, OBSERVABLE_ID] = 'obs2'

    assert lint.measurement_table_has_timepoint_specific_mappings(
        measurement_df) is False


def test_assert_overrides_match_parameter_count():
    # Ensure we recognize and fail if we have wrong number of overrides
    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['0obsPar1noisePar', '2obsPar0noisePar'],
        OBSERVABLE_FORMULA: ['1.0',
                             'observableParameter1_2obsPar0noisePar + '
                             'observableParameter2_2obsPar0noisePar'],
        NOISE_FORMULA: ['noiseParameter1_0obsPar1noisePar', '1.0']
    })
    observable_df.set_index(OBSERVABLE_ID, inplace=True)

    measurement_df_orig = pd.DataFrame(data={
        OBSERVABLE_ID: ['0obsPar1noisePar',
                        '2obsPar0noisePar'],
        SIMULATION_CONDITION_ID: ['condition1', 'condition1'],
        PREEQUILIBRATION_CONDITION_ID: ['', ''],
        TIME: [1.0, 2.0],
        OBSERVABLE_PARAMETERS: ['', ''],
        NOISE_PARAMETERS: ['', '']
    })

    # No overrides
    petab.assert_overrides_match_parameter_count(
        measurement_df_orig, observable_df)

    # Sigma override
    measurement_df = measurement_df_orig.copy()
    measurement_df.loc[0, NOISE_PARAMETERS] = 'noiseParOverride'
    petab.assert_overrides_match_parameter_count(
        measurement_df, observable_df)

    measurement_df.loc[0, NOISE_PARAMETERS] = 'noiseParOverride;oneTooMuch'
    with pytest.raises(AssertionError):
        petab.assert_overrides_match_parameter_count(
            measurement_df, observable_df)

    measurement_df.loc[0, NOISE_PARAMETERS] = 'noiseParOverride'
    measurement_df.loc[1, NOISE_PARAMETERS] = 'oneTooMuch'
    with pytest.raises(AssertionError):
        petab.assert_overrides_match_parameter_count(
            measurement_df, observable_df)

    # Observable override
    measurement_df = measurement_df_orig.copy()
    measurement_df.loc[1, OBSERVABLE_PARAMETERS] = 'override1;override2'
    petab.assert_overrides_match_parameter_count(
        measurement_df, observable_df)

    measurement_df.loc[1, OBSERVABLE_PARAMETERS] = 'oneMissing'
    with pytest.raises(AssertionError):
        petab.assert_overrides_match_parameter_count(
            measurement_df, observable_df)


def test_assert_no_leading_trailing_whitespace():

    test_df = pd.DataFrame(data={
        'testId': ['name1 ', 'name2'],
        'testText ': [' name1', 'name2'],
        'testNumeric': [1.0, 2.0],
        'testNone': None
    })

    with pytest.raises(AssertionError):
        lint.assert_no_leading_trailing_whitespace(
            test_df.columns.values, "test")

    with pytest.raises(AssertionError):
        lint.assert_no_leading_trailing_whitespace(
            test_df['testId'].values, "testId")

    with pytest.raises(AssertionError):
        lint.assert_no_leading_trailing_whitespace(
            test_df['testText '].values, "testText")

    lint.assert_no_leading_trailing_whitespace(
        test_df['testNumeric'].values, "testNumeric")

    lint.assert_no_leading_trailing_whitespace(
        test_df['testNone'].values, "testNone")


def test_assert_model_parameters_in_condition_or_parameter_table():
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    model.setTimeUnits("second")
    model.setExtentUnits("mole")
    model.setSubstanceUnits('mole')
    sbml.add_global_parameter(model, 'parameter1')
    sbml.add_global_parameter(model, 'noiseParameter1_')
    sbml.add_global_parameter(model, 'observableParameter1_')

    lint.assert_model_parameters_in_condition_or_parameter_table(
            model, pd.DataFrame(columns=['parameter1']), pd.DataFrame()
    )

    lint.assert_model_parameters_in_condition_or_parameter_table(
            model, pd.DataFrame(), pd.DataFrame(index=['parameter1']))

    with pytest.raises(AssertionError):
        lint.assert_model_parameters_in_condition_or_parameter_table(
            model,
            pd.DataFrame(columns=['parameter1']),
            pd.DataFrame(index=['parameter1']))

    lint.assert_model_parameters_in_condition_or_parameter_table(
            model, pd.DataFrame(), pd.DataFrame())

    sbml.create_assigment_rule(model, assignee_id='parameter1',
                               formula='parameter2')
    lint.assert_model_parameters_in_condition_or_parameter_table(
        model, pd.DataFrame(), pd.DataFrame())


def test_assert_noise_distributions_valid():
    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['0obsPar1noisePar',
                        '2obsPar0noisePar'],
        NOISE_PARAMETERS: ['', ''],
        NOISE_DISTRIBUTION: ['', ''],
    })
    observable_df.set_index([OBSERVABLE_ID], inplace=True)

    lint.assert_noise_distributions_valid(observable_df)

    observable_df[OBSERVABLE_TRANSFORMATION] = [LIN, LOG]
    observable_df[NOISE_DISTRIBUTION] = [NORMAL, '']
    lint.assert_noise_distributions_valid(observable_df)

    observable_df[NOISE_DISTRIBUTION] = ['Normal', '']
    with pytest.raises(ValueError):
        lint.assert_noise_distributions_valid(observable_df)

    observable_df.drop(columns=NOISE_DISTRIBUTION, inplace=True)
    lint.assert_noise_distributions_valid(observable_df)


def test_check_measurement_df():
    """Check measurement (and observable) tables"""
    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['0obsPar1noisePar',
                        '2obsPar0noisePar'],
        OBSERVABLE_FORMULA: ['', ''],
        NOISE_FORMULA: ['', ''],
        NOISE_DISTRIBUTION: ['', ''],
    })
    observable_df.set_index([OBSERVABLE_ID], inplace=True)

    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['0obsPar1noisePar',
                        '2obsPar0noisePar'],
        SIMULATION_CONDITION_ID: ['condition1', 'condition1'],
        PREEQUILIBRATION_CONDITION_ID: ['', ''],
        TIME: [1.0, 2.0],
        MEASUREMENT: [1.0, 2.0],
        OBSERVABLE_PARAMETERS: ['', ''],
        NOISE_PARAMETERS: ['', ''],
    })

    lint.check_measurement_df(measurement_df, observable_df)

    # Incompatible measurement and transformation
    observable_df[OBSERVABLE_TRANSFORMATION] = [LOG, '']
    measurement_df[MEASUREMENT] = [-1.0, 0.0]
    with pytest.raises(ValueError):
        lint.check_measurement_df(measurement_df, observable_df)


def test_check_parameter_bounds():
    lint.check_parameter_bounds(pd.DataFrame(
        {LOWER_BOUND: [1], UPPER_BOUND: [2], ESTIMATE: [1]}))

    with pytest.raises(AssertionError):
        lint.check_parameter_bounds(pd.DataFrame(
            {LOWER_BOUND: [3], UPPER_BOUND: [2], ESTIMATE: [1]}))

    with pytest.raises(AssertionError):
        lint.check_parameter_bounds(pd.DataFrame(
            {LOWER_BOUND: [-1], UPPER_BOUND: [2],
             ESTIMATE: [1], PARAMETER_SCALE: [LOG10]}))

    with pytest.raises(AssertionError):
        lint.check_parameter_bounds(pd.DataFrame(
            {LOWER_BOUND: [-1], UPPER_BOUND: [2],
             ESTIMATE: [1], PARAMETER_SCALE: [LOG]}))


def test_assert_parameter_prior_type_is_valid():
    lint.assert_parameter_prior_type_is_valid(pd.DataFrame(
        {INITIALIZATION_PRIOR_TYPE: [UNIFORM, LAPLACE],
         OBJECTIVE_PRIOR_TYPE: [NORMAL, LOG_NORMAL]}))
    lint.assert_parameter_prior_type_is_valid(pd.DataFrame())

    with pytest.raises(AssertionError):
        lint.assert_parameter_prior_type_is_valid(pd.DataFrame(
            {INITIALIZATION_PRIOR_TYPE: ['normal', '']}))


def test_petablint_succeeds():
    """Run petablint and ensure we exit successfully for a file that should
    contain no errors"""
    dir_isensee = '../doc/example/example_Isensee/'
    dir_fujita = '../doc/example/example_Fujita/'

    # run with measurement file
    script_path = os.path.abspath(os.path.dirname(__file__))
    measurement_file = os.path.join(
        script_path, dir_isensee, 'Isensee_measurementData.tsv')
    result = subprocess.run(['petablint', '-m', measurement_file])
    assert result.returncode == 0

    # run with yaml
    yaml_file = os.path.join(script_path, dir_fujita, 'Fujita.yaml')
    result = subprocess.run(['petablint', '-v', '-y', yaml_file])
    assert result.returncode == 0

    parameter_file = os.path.join(
        script_path, dir_fujita, 'Fujita_parameters.tsv')
    result = subprocess.run(['petablint', '-v', '-p', parameter_file])
    assert result.returncode == 0


def test_assert_measurement_conditions_present_in_condition_table():
    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        CONDITION_NAME: ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })
    condition_df.set_index(CONDITION_ID, inplace=True)

    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['', ''],
        SIMULATION_CONDITION_ID: ['condition1', 'condition1'],
        TIME: [1.0, 2.0],
        MEASUREMENT: [1.0, 2.0],
        OBSERVABLE_PARAMETERS: ['', ''],
        NOISE_PARAMETERS: ['', ''],
    })

    # check we can handle missing preeq condition
    lint.assert_measurement_conditions_present_in_condition_table(
        measurement_df=measurement_df, condition_df=condition_df)

    # check we can handle preeq condition
    measurement_df[PREEQUILIBRATION_CONDITION_ID] = ['condition1',
                                                     'condition2']

    lint.assert_measurement_conditions_present_in_condition_table(
        measurement_df=measurement_df, condition_df=condition_df)

    # check we detect missing condition
    measurement_df[PREEQUILIBRATION_CONDITION_ID] = ['missing_condition1',
                                                     'missing_condition2']
    with pytest.raises(AssertionError):
        lint.assert_measurement_conditions_present_in_condition_table(
            measurement_df=measurement_df, condition_df=condition_df)


def test_check_condition_df(minimal_sbml_model):
    """Check that we correctly detect errors in condition table"""

    _, sbml_model = minimal_sbml_model

    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1'],
        'p1': [nan],
    })
    condition_df.set_index(CONDITION_ID, inplace=True)

    # parameter missing in model
    with pytest.raises(AssertionError):
        lint.check_condition_df(condition_df, sbml_model)

    # fix:
    sbml_model.createParameter().setId('p1')
    lint.check_condition_df(condition_df, sbml_model)

    # species missing in model
    condition_df['s1'] = [3.0]
    with pytest.raises(AssertionError):
        lint.check_condition_df(condition_df, sbml_model)

    # fix:
    sbml_model.createSpecies().setId('s1')
    lint.check_condition_df(condition_df, sbml_model)

    # compartment missing in model
    condition_df['c1'] = [4.0]
    with pytest.raises(AssertionError):
        lint.check_condition_df(condition_df, sbml_model)

    # fix:
    sbml_model.createCompartment().setId('c1')
    lint.check_condition_df(condition_df, sbml_model)
