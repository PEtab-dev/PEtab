import pandas as pd
from functools import reduce
from typing import List

from .C import *


def calculate_residuals(
    measurement_dfs: List[pd.DataFrame],
    simulation_dfs: List[pd.DataFrame],
    observable_dfs: List[pd.DataFrame],
    normalize: bool = True
) -> List[pd.DataFrame]:
    """Calculate residuals.

    Returns
    -------
    residual_dfs:
        Data frames in the same structure as `measurement_dfs`
        with a field `residual` instead of measurement.
    """
    # convenience
    if isinstance(measurement_dfs, pd.DataFrame):
        measurement_dfs = [measurement_dfs]
    if isinstance(simulation_dfs, pd.DataFrame):
        simulation_dfs = [simulation_dfs]
    if isinstance(observable_dfs, pd.DataFrame):
        observable_dfs = [observable_dfs]

    # iterate over data frames
    residual_dfs = []
    for (observable_df, measurement_df, simulation_df) in zip(
            observable_dfs, measurement_dfs, simulation_dfs):
        # create residual df as copy of measurement df, change column
        residual_df = measurement_df.copy(deep=True).rename(
            columns={MEASUREMENT: RESIDUAL})

        # matching columns
        compared_cols = set(MEASUREMENT_DF_COLS)
        compared_cols -= {MEASUREMENT}
        compared_cols &= set(measurement_df.columns)

        # iterate over measurements, find corresponding simulations
        for irow, row in measurement_df.iterrows():
            measurement = row[MEASUREMENT]

            # look up in simulation df
            masks = [simulation_df[col] == row[col] for col in compared_cols]
            mask = reduce(lambda x, y: x & y, masks)

            simulation = simulation_df.loc[mask][SIMULATION].iloc[0]

            # non-normalized residual is just the difference
            residual = simulation - measurement

            if normalize:
                # look up noise standard deviation
                observable = observable_df.loc[row[OBSERVABLE_ID]]
                std = observable[NOISE_FORMULA]
                try:
                    std = float(std)
                except ValueError:
                    raise ValueError(
                        "Normalized residuals currently only supported for "
                        "numeric noise formulas.")
                residual /= std

            # fill in value
            residual_df.loc[irow, RESIDUAL] = residual

        # append dataframe to list
        residual_dfs.append(residual_df)
    return residual_dfs
