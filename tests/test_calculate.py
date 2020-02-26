from petab import calculate_residuals
from petab.C import *
import pandas as pd
import numpy as np


def test_calculate_residuals():
    """Test calculate.calculate_residuals."""
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

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 2, 19, 20]

    residual_dfs = calculate_residuals(
        measurement_df, simulation_df, observable_df)

    assert set(residual_dfs[0][RESIDUAL]) == \
        {(2-0)/2, (2-1)/2, (19-20)/3, (20-22)/3}

    # don't apply normalization
    residual_dfs = calculate_residuals(
        measurement_df, simulation_df, observable_df, normalize=False)

    assert set(residual_dfs[0][RESIDUAL]) == \
        {(2-0), (2-1), (19-20), (20-22)}


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


def test_calculate_residuals_scaling():
    """Test calculate.calculate_residuals with scaling."""
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

    simulation_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: SIMULATION})
    simulation_df[SIMULATION] = [2, 3]

    residual_dfs = calculate_residuals(
        measurement_df, simulation_df, observable_df)

    assert set(residual_dfs[0][RESIDUAL]) == \
        {(np.log(2)-np.log(0.5))/2, (np.log(3)-np.log(1))/2}
