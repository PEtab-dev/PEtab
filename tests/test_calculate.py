"""Tests related to petab.calculate."""

from petab import (calculate_residuals, calculate_chi2, calculate_llh,
                   calculate_single_llh)
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
    expected_llh = 0.5*(np.array(list(expected_residuals))**2).sum() + \
        0.5*np.log(2*np.pi*np.array([2, 2, 3, 3])**2).sum()

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm,
            expected_llh)


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
    expected_llh = 0.5*(np.array(list(expected_residuals))**2).sum() + \
        0.5*np.log(2*np.pi*np.array([2, 2])**2).sum()

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm,
            expected_llh)


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
    expected_llh = 0.5*(np.array(list(expected_residuals))**2).sum() + \
        0.5*np.log(2*np.pi*np.array([2, 2])**2*np.array([0.5, 1])**2).sum()

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm,
            expected_llh)


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
    expected_llh = 0.5*(np.array(list(expected_residuals))**2).sum() + \
        0.5*np.log(2*np.pi*np.array([2*7+8+4, 2*2+3+4])**2
                   * np.array([0.5, 1])**2).sum()

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm,
            expected_llh)


def model_custom_likelihood():
    """Model with customized likelihoods."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_b'],
        SIMULATION_CONDITION_ID: ['c0', 'c0'],
        TIME: [5, 10],
        MEASUREMENT: [0.5, 2]
    })

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_b'],
        OBSERVABLE_FORMULA: ['A', 'B'],
        OBSERVABLE_TRANSFORMATION: [LOG, LIN],
        NOISE_FORMULA: [2, 1.5],
        NOISE_DISTRIBUTION: [LAPLACE, LAPLACE]
    }).set_index([OBSERVABLE_ID])

    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2'],
        NOMINAL_VALUE: [3, 4]
    }).set_index([PARAMETER_ID])

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 3]

    expected_residuals = {(np.log(2)-np.log(0.5))/2, (3-2)/1.5}
    expected_residuals_nonorm = {np.log(2)-np.log(0.5), 3-2}
    expected_llh = np.abs(list(expected_residuals)).sum() + \
        np.log(2*np.array([2, 1.5])*np.array([0.5, 1])).sum()

    return (measurement_df, observable_df, parameter_df,
            simulation_df, expected_residuals, expected_residuals_nonorm,
            expected_llh)


@pytest.fixture
def models():
    """Test model collection covering different features."""
    return [model_simple(), model_replicates(),
            model_scalings(), model_non_numeric_overrides(),
            model_custom_likelihood()]


def test_calculate_residuals(models):  # pylint: disable=W0621
    """Test calculate.calculate_residuals."""
    for i_model, model in enumerate(models):
        print(f"Model {i_model}")
        (measurement_df, observable_df, parameter_df, simulation_df,
         expected_residuals, _, _) = model
        residual_dfs = calculate_residuals(
            measurement_df, simulation_df, observable_df, parameter_df)
        assert set(residual_dfs[0][RESIDUAL]) == pytest.approx(
            expected_residuals)


def test_calculate_non_normalized_residuals(models):  # pylint: disable=W0621
    """Test calculate.calculate_residuals without normalization."""
    for i_model, model in enumerate(models):
        print(f"Model {i_model}")
        (measurement_df, observable_df, parameter_df, simulation_df,
         _, expected_residuals_nonorm, _) = model
        residual_dfs = calculate_residuals(
            measurement_df, simulation_df, observable_df, parameter_df,
            normalize=False)
        assert set(residual_dfs[0][RESIDUAL]) == pytest.approx(
            expected_residuals_nonorm)


def test_calculate_chi2(models):  # pylint: disable=W0621
    """Test calculate.calculate_chi2."""
    for i_model, model in enumerate(models):
        print(f"Model {i_model}")
        (measurement_df, observable_df, parameter_df, simulation_df,
         expected_residuals, _, _) = model
        chi2 = calculate_chi2(
            measurement_df, simulation_df, observable_df, parameter_df)

        expected = sum(np.array(list(expected_residuals))**2)
        assert chi2 == pytest.approx(expected)


def test_calculate_llh(models):  # pylint: disable=W0621
    """Test calculate.calculate_llh."""
    for i_model, model in enumerate(models):
        print(f"Model {i_model}")
        (measurement_df, observable_df, parameter_df, simulation_df,
         _, _, expected_llh) = model
        llh = calculate_llh(
            measurement_df, simulation_df, observable_df, parameter_df)
        assert llh == pytest.approx(expected_llh) or expected_llh is None


def test_calculate_single_llh():
    """Test calculate.calculate_single_llh."""
    m, s, sigma = 5.3, 4.5, 1.6
    pi, log, log10 = np.pi, np.log, np.log10

    llh = calculate_single_llh(measurement=m, simulation=s, noise_value=sigma,
                               noise_distribution=NORMAL, scale=LIN)
    expected_llh = 0.5 * (((s-m)/sigma)**2 + log(2*pi*sigma**2))
    assert llh == pytest.approx(expected_llh)

    llh = calculate_single_llh(measurement=m, simulation=s, noise_value=sigma,
                               noise_distribution=NORMAL, scale=LOG)
    expected_llh = 0.5 * (((log(s)-log(m))/sigma)**2 +
                          log(2*pi*sigma**2*m**2))
    assert llh == pytest.approx(expected_llh)

    llh = calculate_single_llh(measurement=m, simulation=s, noise_value=sigma,
                               noise_distribution=NORMAL, scale=LOG10)
    expected_llh = 0.5 * (((log10(s)-log10(m))/sigma)**2 +
                          log(2*pi*sigma**2*m**2))
    assert llh == pytest.approx(expected_llh)

    llh = calculate_single_llh(measurement=m, simulation=s, noise_value=sigma,
                               noise_distribution=LAPLACE, scale=LIN)
    expected_llh = abs((s-m)/sigma) + log(2*sigma)
    assert llh == pytest.approx(expected_llh)

    llh = calculate_single_llh(measurement=m, simulation=s, noise_value=sigma,
                               noise_distribution=LAPLACE, scale=LOG)
    expected_llh = abs((log(s)-log(m))/sigma) + log(2*sigma*m)
    assert llh == pytest.approx(expected_llh)

    llh = calculate_single_llh(measurement=m, simulation=s, noise_value=sigma,
                               noise_distribution=LAPLACE, scale=LOG10)
    expected_llh = abs((log10(s)-log10(m))/sigma) + log(2*sigma*m)
    assert llh == pytest.approx(expected_llh)
