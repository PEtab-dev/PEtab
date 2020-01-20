import os
import subprocess
from unittest.mock import patch

import libsbml
import pandas as pd
import petab
import pytest
from petab import (lint, sbml)  # noqa: E402


def test_assert_measured_observables_present_in_model():
    # create test model
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()

    measurement_df = pd.DataFrame(data={
        'observableId': ['non-existing1'],
    })

    with pytest.raises(AssertionError):
        lint.assert_measured_observables_present_in_model(
            measurement_df, model
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
        'observableId': ['obs1', 'obs1'],
        'simulationConditionId': ['condition1', 'condition1'],
        'preequilibrationConditionId': ['', ''],
        'time': [1.0, 2.0],
        'observableParameters': ['obsParOverride', ''],
        'noiseParameters': ['', '']
    })

    assert lint.measurement_table_has_timepoint_specific_mappings(
        measurement_df) is True

    measurement_df.loc[1, 'observableId'] = 'obs2'

    assert lint.measurement_table_has_timepoint_specific_mappings(
        measurement_df) is False


def test_assert_overrides_match_parameter_count():
    # Ensure we recognize and fail if we have wrong number of overrides
    observables = {
        'observable_0obsPar1noisePar': {
            'formula': '1.0'
        },
        'observable_2obsPar0noisePar': {
            'formula': 'observableParameter1_2obsPar0noisePar + '
                       'observableParameter2_2obsPar0noisePar'
        }
    }
    noise = {
        'observable_0obsPar1noisePar': 'noiseParameter1_0obsPar1noisePar',
        'observable_2obsPar0noisePar': '1.0'
    }
    measurement_df_orig = pd.DataFrame(data={
        'observableId': ['0obsPar1noisePar',
                         '2obsPar0noisePar'],
        'simulationConditionId': ['condition1', 'condition1'],
        'preequilibrationConditionId': ['', ''],
        'time': [1.0, 2.0],
        'observableParameters': ['', ''],
        'noiseParameters': ['', '']
    })

    # No overrides
    petab.assert_overrides_match_parameter_count(
        measurement_df_orig, observables, noise)

    # Sigma override
    measurement_df = measurement_df_orig.copy()
    measurement_df.loc[0, 'noiseParameters'] = 'noiseParOverride'
    petab.assert_overrides_match_parameter_count(
        measurement_df, observables, noise)

    measurement_df.loc[0, 'noiseParameters'] = 'noiseParOverride;oneTooMuch'
    with pytest.raises(AssertionError):
        petab.assert_overrides_match_parameter_count(
            measurement_df, observables, noise)

    measurement_df.loc[0, 'noiseParameters'] = 'noiseParOverride'
    measurement_df.loc[1, 'noiseParameters'] = 'oneTooMuch'
    with pytest.raises(AssertionError):
        petab.assert_overrides_match_parameter_count(
            measurement_df, observables, noise)

    # Observable override
    measurement_df = measurement_df_orig.copy()
    measurement_df.loc[1, 'observableParameters'] = 'override1;override2'
    petab.assert_overrides_match_parameter_count(
        measurement_df, observables, noise)

    measurement_df.loc[1, 'observableParameters'] = 'oneMissing'
    with pytest.raises(AssertionError):
        petab.assert_overrides_match_parameter_count(
            measurement_df, observables, noise)


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
    measurement_df = pd.DataFrame(data={
        'observableId': ['0obsPar1noisePar',
                         '2obsPar0noisePar'],
        'simulationConditionId': ['condition1', 'condition1'],
        'preequilibrationConditionId': ['', ''],
        'time': [1.0, 2.0],
        'measurement': [1.0, 2.0],
        'observableParameters': ['', ''],
        'noiseParameters': ['', ''],
        'noiseDistribution': ['', ''],
    })
    lint.assert_noise_distributions_valid(measurement_df)

    measurement_df['observableTransformation'] = ['lin', 'log']
    measurement_df['noiseDistribution'] = ['normal', '']
    lint.assert_noise_distributions_valid(measurement_df)

    measurement_df['noiseDistribution'] = ['Normal', '']
    with pytest.raises(ValueError):
        lint.assert_noise_distributions_valid(measurement_df)

    measurement_df['noiseDistribution'] = ['', '']
    measurement_df['observableTransformation'] = ['log', '']
    measurement_df['measurement'] = [-1.0, 0.0]
    with pytest.raises(ValueError):
        lint.assert_noise_distributions_valid(measurement_df)


def test_check_parameter_bounds():
    lint.check_parameter_bounds(pd.DataFrame(
        {'lowerBound': [1], 'upperBound': [2], 'estimate': [1]}))

    with pytest.raises(AssertionError):
        lint.check_parameter_bounds(pd.DataFrame(
            {'lowerBound': [3], 'upperBound': [2], 'estimate': [1]}))

    with pytest.raises(AssertionError):
        lint.check_parameter_bounds(pd.DataFrame(
            {'lowerBound': [-1], 'upperBound': [2],
             'estimate': [1], 'parameterScale': ['log10']}))

    with pytest.raises(AssertionError):
        lint.check_parameter_bounds(pd.DataFrame(
            {'lowerBound': [-1], 'upperBound': [2],
             'estimate': [1], 'parameterScale': ['log']}))


def test_assert_parameter_prior_type_is_valid():
    lint.assert_parameter_prior_type_is_valid(pd.DataFrame(
        {'initializationPriorType': ['uniform', 'laplace'],
         'objectivePriorType': ['normal', 'logNormal']}))
    lint.assert_parameter_prior_type_is_valid(pd.DataFrame())

    with pytest.raises(AssertionError):
        lint.assert_parameter_prior_type_is_valid(pd.DataFrame(
            {'initializationPriorType': ['normal', '']}))


def test_petablint_succeeds():
    """Run petablint and ensure we exit successfully for a file that should
    contain no errors"""

    script_path = os.path.abspath(os.path.dirname(__file__))
    test_mes_file = os.path.join(
        script_path, '..',
        'doc/example/example_Isensee/Isensee_measurementData.tsv')

    result = subprocess.run(['petablint', '-m', test_mes_file])
    assert result.returncode == 0


def test_assert_measurement_conditions_present_in_condition_table():
    condition_df = pd.DataFrame(data={
        'conditionId': ['condition1', 'condition2'],
        'conditionName': ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })
    condition_df.set_index('conditionId', inplace=True)

    measurement_df = pd.DataFrame(data={
        'observableId': ['', ''],
        'simulationConditionId': ['condition1', 'condition1'],
        'time': [1.0, 2.0],
        'measurement': [1.0, 2.0],
        'observableParameters': ['', ''],
        'noiseParameters': ['', ''],
        'noiseDistribution': ['', ''],
    })

    # check we can handle missing preeq condition
    lint.assert_measurement_conditions_present_in_condition_table(
        measurement_df=measurement_df, condition_df=condition_df)

    # check we can handle preeq condition
    measurement_df['preequilibrationConditionId'] = ['condition1',
                                                     'condition2']

    lint.assert_measurement_conditions_present_in_condition_table(
        measurement_df=measurement_df, condition_df=condition_df)

    # check we detect missing condition
    measurement_df['preequilibrationConditionId'] = ['missing_condition1',
                                                     'missing_condition2']
    with pytest.raises(AssertionError):
        lint.assert_measurement_conditions_present_in_condition_table(
            measurement_df=measurement_df, condition_df=condition_df)
