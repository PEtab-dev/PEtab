"""Functions performing various calculations."""

import pandas as pd
from functools import reduce
from typing import List, Union
import sympy
import numbers

from .C import *
import petab


def calculate_residuals(
        measurement_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        simulation_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        observable_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        parameter_dfs: Union[List[pd.DataFrame], pd.DataFrame],
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
        parameter_dfs:
            The problem parameter tables.
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
    if isinstance(parameter_dfs, pd.DataFrame):
        parameter_dfs = [parameter_dfs]

    # iterate over data frames
    residual_dfs = []
    for (measurement_df, simulation_df, observable_df, parameter_df) in zip(
            measurement_dfs, simulation_dfs, observable_dfs, parameter_dfs):
        residual_df = calculate_residuals_for_table(
            measurement_df, simulation_df, observable_df, parameter_df,
            normalize, scale)
        residual_dfs.append(residual_df)
    return residual_dfs


def calculate_residuals_for_table(
        measurement_df: pd.DataFrame,
        simulation_df: pd.DataFrame,
        observable_df: pd.DataFrame,
        parameter_df: pd.DataFrame,
        normalize: bool = True,
        scale: bool = True
) -> pd.DataFrame:
    """
    Calculate residuals for a single measurement table.
    For the argumenets, see `calculate_residuals`.
    """
    # create residual df as copy of measurement df, change column
    residual_df = measurement_df.copy(deep=True).rename(
        columns={MEASUREMENT: RESIDUAL})

    # matching columns
    compared_cols = set(MEASUREMENT_DF_COLS)
    compared_cols -= {MEASUREMENT}
    compared_cols &= set(measurement_df.columns)

    # compute noise formulas for observables
    noise_formulas = get_symbolic_noise_formulas(observable_df)

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
            noise_value = evaluate_noise_formula(
                row, parameter_df, noise_formulas)
            residual /= noise_value

        # fill in value
        residual_df.loc[irow, RESIDUAL] = residual
    return residual_df


def get_symbolic_noise_formulas(observable_df) -> dict:
    """Sympify noise formulas.

    Arguments:
        obervable_df: The observable table.

    Returns:
        noise_formulas: Dictionary of {observable_id}: {noise_formula}.
    """
    noise_formulas = {}
    # iterate over observables
    for row in observable_df.itertuples():
        observable_id = row.Index
        if NOISE_FORMULA not in observable_df.columns:
            noise_formula = None
        else:
            noise_formula = sympy.sympify(row.noiseFormula)
        noise_formulas[observable_id] = noise_formula
    return noise_formulas


def evaluate_noise_formula(
        measurement: pd.Series,
        parameter_df: pd.DataFrame,
        noise_formulas: dict) -> float:
    """Fill in parameters for `measurement` and evaluate noise_formula.

    Arguments:
        measurement: A measurement table row.
        parameter_df: The parameter table.
        noise_formulas: The noise formulas as computed by
            `get_symbolic_noise_formulas`.

    Returns:
        noise_value: The noise value.
    """
    # the observable id
    observable_id = measurement[OBSERVABLE_ID]

    # extract measurement specific overrides
    observable_parameter_overrides = petab.split_parameter_replacement_list(
        measurement.get(NOISE_PARAMETERS))
    overrides = {}
    # fill in measurement specific parameters
    for i_obs_par, obs_par in enumerate(observable_parameter_overrides):
        overrides[f"noiseParameter{i_obs_par+1}_{observable_id}"] = obs_par

    # fill in general parameters
    for row in parameter_df.itertuples():
        overrides[row.Index] = row.nominalValue

    # replace parametric measurement specific parameters
    for key, value in overrides.items():
        if not isinstance(value, numbers.Number):
            # is parameter
            overrides[key] = parameter_df.loc[value, NOMINAL_VALUE]

    # replace parameters by values in formula
    noise_formula = noise_formulas[observable_id]
    noise_value = noise_formula.subs(overrides)

    # conversion is possible if all parameters are replaced
    try:
        noise_value = float(noise_value)
    except TypeError:
        raise TypeError(
            f"Cannot replace all parameters in noise formula {noise_value} "
            f"for observable {observable_id}.")
    return noise_value
