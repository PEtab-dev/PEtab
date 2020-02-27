"""Tests related to petab.calculate."""

from petab import calculate_residuals, calculate_chi2
from petab.C import *
import pandas as pd
import numpy as np
import pytest


def model_simple():
    "Simple model."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_a', 'obs_b', 'obs_b'],
        SIMULATION_CONDITION_ID: ['c0', 'c1', 'c0', 'c1'],
        TIME: [0, 10, 0, 10],
        MEASUREMENT: [0, 1, 20, 22]
    })

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_b'],
        OBSERVABLE_FORMULA: ['A', 'B'],
        NOISE_FORMULA: [2, 3]
    }).set_index([OBSERVABLE_ID])

    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2'],
        NOMINAL_VALUE: [3, 4]
    })

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 2, 19, 20]

    expected_residuals = {(2-0)/2, (2-1)/2, (19-20)/3, (20-22)/3}
    expected_residuals_nonorm = {2-0, 2-1, 19-20, 20-22}

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm)


def model_replicates():
    """Model with replicates."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_a'],
        SIMULATION_CONDITION_ID: ['c0', 'c0'],
        TIME: [10, 10],
        MEASUREMENT: [0, 1]
    })

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a'],
        OBSERVABLE_FORMULA: ['A'],
        NOISE_FORMULA: [2]
    }).set_index([OBSERVABLE_ID])

    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2'],
        NOMINAL_VALUE: [3, 4]
    }).set_index([PARAMETER_ID])

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 2]

    expected_residuals = {(2-0)/2, (2-1)/2}
    expected_residuals_nonorm = {2-0, 2-1}

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm)


def model_scalings():
    """Model with scalings."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_a'],
        SIMULATION_CONDITION_ID: ['c0', 'c0'],
        TIME: [5, 10],
        MEASUREMENT: [0.5, 1]
    })

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a'],
        OBSERVABLE_FORMULA: ['A'],
        OBSERVABLE_TRANSFORMATION: [LOG],
        NOISE_FORMULA: [2]
    }).set_index([OBSERVABLE_ID])

    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2'],
        NOMINAL_VALUE: [3, 4]
    }).set_index([PARAMETER_ID])

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 3]

    expected_residuals = {(np.log(2)-np.log(0.5))/2, (np.log(3)-np.log(1))/2}
    expected_residuals_nonorm = {np.log(2)-np.log(0.5), np.log(3)-np.log(1)}

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm)


def model_non_numeric_overrides():
    """Model with non-numeric overrides."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_a'],
        SIMULATION_CONDITION_ID: ['c0', 'c0'],
        TIME: [5, 10],
        MEASUREMENT: [0.5, 1],
        NOISE_PARAMETERS: ['7;8', '2;par1']
    })

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a'],
        OBSERVABLE_FORMULA: ['A'],
        OBSERVABLE_TRANSFORMATION: [LOG],
        NOISE_FORMULA: ['2*noiseParameter1_obs_a + '
                        'noiseParameter2_obs_a + par2']
    }).set_index([OBSERVABLE_ID])

    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2'],
        NOMINAL_VALUE: [3, 4]
    }).set_index([PARAMETER_ID])

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 3]

    expected_residuals = {(np.log(2)-np.log(0.5))/(2*7+8+4),
                          (np.log(3)-np.log(1))/(2*2+3+4)}
    expected_residuals_nonorm = {np.log(2)-np.log(0.5), np.log(3)-np.log(1)}

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm)


@pytest.fixture
def models():
    return [model_simple(), model_replicates(),
            model_scalings(), model_non_numeric_overrides()]


def test_calculate_residuals(models):  # pylint: disable=W0621
    """Test calculate.calculate_residuals."""
    for model in models:
        (measurement_df, observable_df, parameter_df, simulation_df,
            expected_residuals, _) = model
        residual_dfs = calculate_residuals(
            measurement_df, simulation_df, observable_df, parameter_df)
        assert set(residual_dfs[0][RESIDUAL]) == pytest.approx(
            expected_residuals)


def test_calculate_non_normalized_residuals(models):  # pylint: disable=W0621
    """Test calculate.calculate_residuals without normalization."""
    for model in models:
        (measurement_df, observable_df, parameter_df, simulation_df,
            _, expected_residuals_nonorm) = model
        residual_dfs = calculate_residuals(
            measurement_df, simulation_df, observable_df, parameter_df,
            normalize=False)
        assert set(residual_dfs[0][RESIDUAL]) == pytest.approx(
            expected_residuals_nonorm)


def test_calculate_chi2(models):  # pylint: disable=W0621
    """Test calculate.calculate_chi2."""
    for model in models:
        (measurement_df, observable_df, parameter_df, simulation_df,
            expected_residuals, _) = model
        chi2 = calculate_chi2(
            measurement_df, simulation_df, observable_df, parameter_df)

        expected = sum(np.array(list(expected_residuals))**2)
        assert chi2 == pytest.approx(expected)
