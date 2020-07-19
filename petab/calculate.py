"""Functions performing various calculations."""

import numpy as np
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
    compared_cols &= set(simulation_df.columns)

    # compute noise formulas for observables
    noise_formulas = get_symbolic_noise_formulas(observable_df)

    # iterate over measurements, find corresponding simulations
    for irow, row in measurement_df.iterrows():
        measurement = row[MEASUREMENT]
        # look up in simulation df
        masks = [(simulation_df[col] == row[col]) | petab.is_empty(row[col])
                 for col in compared_cols]
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

        noise_value = 1
        if normalize:
            # look up noise standard deviation
            noise_value = evaluate_noise_formula(
                row, noise_formulas, parameter_df, simulation)
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
        noise_formulas: dict,
        parameter_df: pd.DataFrame,
        simulation: float) -> float:
    """Fill in parameters for `measurement` and evaluate noise_formula.

    Arguments:
        measurement: A measurement table row.
        noise_formulas: The noise formulas as computed by
            `get_symbolic_noise_formulas`.
        parameter_df: The parameter table.
        simulation: The simulation corresponding to the measurement, scaled.

    Returns:
        noise_value: The noise value.
    """
    # the observable id
    observable_id = measurement[OBSERVABLE_ID]

    # extract measurement specific overrides
    observable_parameter_overrides = petab.split_parameter_replacement_list(
        measurement.get(NOISE_PARAMETERS, None))
    overrides = {}
    # fill in measurement specific parameters
    for i_obs_par, obs_par in enumerate(observable_parameter_overrides):
        overrides[f"noiseParameter{i_obs_par+1}_{observable_id}"] = obs_par

    # fill in observables
    overrides[observable_id] = simulation

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


def calculate_chi2(
        measurement_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        simulation_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        observable_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        parameter_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        normalize: bool = True,
        scale: bool = True
) -> float:
    """Calculate the chi2 value.

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
        chi2: The aggregated chi2 value.
    """
    residual_dfs = calculate_residuals(
        measurement_dfs, simulation_dfs, observable_dfs, parameter_dfs,
        normalize, scale)
    chi2s = [calculate_chi2_for_table_from_residuals(df)
             for df in residual_dfs]
    chi2 = sum(chi2s)
    return chi2


def calculate_chi2_for_table_from_residuals(
        residual_df: pd.DataFrame) -> float:
    """Compute chi2 value for a single residual table."""
    return (np.array(residual_df[RESIDUAL])**2).sum()


def calculate_llh(
        measurement_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        simulation_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        observable_dfs: Union[List[pd.DataFrame], pd.DataFrame],
        parameter_dfs: Union[List[pd.DataFrame], pd.DataFrame],
) -> float:
    """Calculate total log likelihood.

    Arguments:
        measurement_dfs:
            The problem measurement tables.
        simulation_dfs:
            Simulation tables corresponding to the measurement tables.
        observable_dfs:
            The problem observable tables.
        parameter_dfs:
            The problem parameter tables.

    Returns:
        llh: The log-likelihood.
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
    llhs = []
    for (measurement_df, simulation_df, observable_df, parameter_df) in zip(
            measurement_dfs, simulation_dfs, observable_dfs, parameter_dfs):
        _llh = calculate_llh_for_table(
            measurement_df, simulation_df, observable_df, parameter_df)
        llhs.append(_llh)
    llh = sum(llhs)
    return llh


def calculate_llh_for_table(
        measurement_df: pd.DataFrame,
        simulation_df: pd.DataFrame,
        observable_df: pd.DataFrame,
        parameter_df: pd.DataFrame) -> float:
    """Calculate log-likelihood for one set of tables. For the arguments, see
    `calculate_llh`."""
    llhs = []

    # matching columns
    compared_cols = set(MEASUREMENT_DF_COLS)
    compared_cols -= {MEASUREMENT}
    compared_cols &= set(measurement_df.columns)
    compared_cols &= set(simulation_df.columns)

    # compute noise formulas for observables
    noise_formulas = get_symbolic_noise_formulas(observable_df)

    # iterate over measurements, find corresponding simulations
    for irow, row in measurement_df.iterrows():
        measurement = row[MEASUREMENT]

        # look up in simulation df
        masks = [(simulation_df[col] == row[col]) | petab.is_empty(row[col])
                 for col in compared_cols]
        mask = reduce(lambda x, y: x & y, masks)

        simulation = simulation_df.loc[mask][SIMULATION].iloc[0]

        observable = observable_df.loc[row[OBSERVABLE_ID]]

        # get scale
        scale = observable.get(OBSERVABLE_TRANSFORMATION, LIN)

        # get noise standard deviation
        noise_value = evaluate_noise_formula(
            row, noise_formulas, parameter_df, petab.scale(simulation, scale))

        # get noise distribution
        noise_distribution = observable.get(NOISE_DISTRIBUTION, NORMAL)

        llh = calculate_single_llh(
            measurement, simulation, scale, noise_distribution, noise_value)
        llhs.append(llh)
    llh = sum(llhs)
    return llh


def calculate_single_llh(
        measurement: float,
        simulation: float,
        scale: str,
        noise_distribution: str,
        noise_value: float) -> float:
    """Calculate a single log likelihood.

    Arguments:
        measurement: The measurement value.
        simulation: The simulated value.
        scale: The scale on which the noise model is to be applied.
        noise_distribution: The noise distribution.
        noise_value: The considered noise models possess a single noise
            parameter, e.g. the normal standard deviation.

    Returns:
        llh: The computed likelihood for the given values.
    """
    # short-hand
    m, s, sigma = measurement, simulation, noise_value
    pi, log, log10 = np.pi, np.log, np.log10

    # go over the possible cases
    if noise_distribution == NORMAL and scale == LIN:
        nllh = 0.5*log(2*pi*sigma**2) + 0.5*((s-m)/sigma)**2
    elif noise_distribution == NORMAL and scale == LOG:
        nllh = 0.5*log(2*pi*sigma**2*m**2) + 0.5*((log(s)-log(m))/sigma)**2
    elif noise_distribution == NORMAL and scale == LOG10:
        nllh = 0.5*log(2*pi*sigma**2*m**2*log(10)**2) + \
            0.5*((log10(s)-log10(m))/sigma)**2
    elif noise_distribution == LAPLACE and scale == LIN:
        nllh = log(2*sigma) + abs((s-m)/sigma)
    elif noise_distribution == LAPLACE and scale == LOG:
        nllh = log(2*sigma*m) + abs((log(s)-log(m))/sigma)
    elif noise_distribution == LAPLACE and scale == LOG10:
        nllh = log(2*sigma*m*log(10)) + abs((log10(s)-log10(m))/sigma)
    llh = - nllh
    return llh
