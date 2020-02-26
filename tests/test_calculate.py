from petab import calculate_residuals
from petab.C import *
import pandas as pd


def test_calculate_residuals():
    """Test calculate.calculate_residuals."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a', 'obs_a'],
        SIMULATION_CONDITION_ID: ['c0', 'c1'],
        TIME: [0, 10],
        MEASUREMENT: [0, 1]
    })

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs_a'],
        OBSERVABLE_FORMULA: ['A'],
        NOISE_FORMULA: [2]
    }).set_index([OBSERVABLE_ID])

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 2]

    residual_dfs = calculate_residuals(
        measurement_df, simulation_df, observable_df)

    assert set(residual_dfs[0][RESIDUAL]) == {(2-0)/2, (2-1)/2}

    # don't apply normalization
    residual_dfs = calculate_residuals(
        measurement_df, simulation_df, observable_df, normalize=False)

    assert set(residual_dfs[0][RESIDUAL]) == {(2-0), (2-1)}


def test_calculate_residuals_replicates():
    """Test calculate.calculate_residuals with replicates."""
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

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 2]

    residual_dfs = calculate_residuals(
        measurement_df, simulation_df, observable_df)

    assert set(residual_dfs[0][RESIDUAL]) == {(2-0)/2, (2-1)/2}
