"""Functions performing various calculations."""

import pandas as pd
from functools import reduce
from typing import List, Union

from .C import *
import petab


def calculate_residuals(
    measurement_dfs: Union[List[pd.DataFrame], pd.DataFrame],
    simulation_dfs: Union[List[pd.DataFrame], pd.DataFrame],
    observable_dfs: Union[List[pd.DataFrame], pd.DataFrame],
    normalize: bool = True,
    scale: bool = True
) -> List[pd.DataFrame]:
    """Calculate residuals.

    Arguments:
        measurement_dfs:
            The problem measurement tables.
        simulation_dfs:
            Simulation tables corresponding to the measurement tables.
        observable_dfs:
            The problem observable tables.
        normalize:
            Whether to normalize residuals by the noise standard deviation
            terms.
        scale:
            Whether to calculate residuals of scaled values.

    Returns:
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
    for (measurement_df, simulation_df, observable_df) in zip(
            measurement_dfs, simulation_dfs, observable_dfs):
        residual_df = calculate_residuals_for_table(
            measurement_df, simulation_df, observable_df, normalize, scale)
        residual_dfs.append(residual_df)
    return residual_dfs


def calculate_residuals_for_table(
    measurement_df: pd.DataFrame,
    simulation_df: pd.DataFrame,
    observable_df: pd.DataFrame,
    normalize: bool = True,
    scale: bool = True
) -> pd.DataFrame:
    """
    Calculate residuals for a single measurement table.
    For the arrgumenets, see `calculate_residuals`.
    """
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

        if scale:
            # apply scaling
            observable = observable_df.loc[row[OBSERVABLE_ID]]
            trafo = observable.get(OBSERVABLE_TRANSFORMATION, LIN)
            simulation = petab.scale(simulation, trafo)
            measurement = petab.scale(measurement, trafo)

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
    return residual_df
