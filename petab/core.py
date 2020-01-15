"""PEtab core functions (or functions that don't fit anywhere else)"""

import logging
from typing import Iterable

import numpy as np
import pandas as pd
import sympy as sp

from . import sbml
from . import problem

logger = logging.getLogger(__name__)


def parameter_is_scaling_parameter(parameter: str, formula: str) -> bool:
    """
    Check if is scaling parameter.

    Arguments:
        parameter: Some identifier.
        formula: Some sympy-compatible formula.

    Returns:
        ``True`` if parameter ``parameter`` is a scaling parameter in formula
         ``formula``.
    """

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula / sym_parameter).free_symbols


def parameter_is_offset_parameter(parameter: str, formula: str) -> bool:
    """
    Check if is offset parameter.

    Arguments:
        parameter: Some identifier.
        formula: Some sympy-compatible formula.

    Returns:
         ``True`` if parameter ``parameter`` is an offset parameter with
         positive sign in formula ``formula``.
    """

    sym_parameter = sp.sympify(parameter)
    sym_formula = sp.sympify(formula)

    return sym_parameter not in (sym_formula - sym_parameter).free_symbols


def get_notnull_columns(df: pd.DataFrame, candidates: Iterable):
    """
    Return list of ``df``-columns in ``candidates`` which are not all null/nan.

    The output can e.g. be used as input for ``pandas.DataFrame.groupby``.

    Arguments:
        df:
            Dataframe
        candidates:
            Columns of ``df`` to consider
    """
    return [col for col in candidates
            if col in df and not np.all(df[col].isnull())]


def get_observable_id(parameter_id: str) -> str:
    """Get PEtab observable ID from PEtab-style sigma or observable
    `AssignmentRule`-target ``parameter_id``.

    e.g. for 'observable_obs1' -> 'obs1', for 'sigma_obs1' -> 'obs1'

    Arguments:
        parameter_id: Some parameter ID

    Returns:
        Observable ID
    """

    if parameter_id.startswith(r'observable_'):
        return parameter_id[len('observable_'):]

    if parameter_id.startswith(r'sigma_'):
        return parameter_id[len('sigma_'):]

    raise ValueError('Cannot extract observable id from: ' + parameter_id)


def flatten_timepoint_specific_output_overrides(
        petab_problem: 'problem.Problem') -> None:
    """Flatten timepoint-specific output parameter overrides.

    If the PEtab problem definition has timepoint-specific
    `observableParameters` or `noiseParameters` for the same observable,
    replace those by replicating the respective observable.

    This is a helper function for some tools which may not support such
    timepoint-specific mappings. The measurement table is modified in place.

    Arguments:
        petab_problem:
            PEtab problem to work on
    """

    # Create empty df -> to be filled with replicate-specific observables
    df_new = pd.DataFrame()

    # Get observableId, preequilibrationConditionId
    # and simulationConditionId columns in measurement df
    df = petab_problem.measurement_df[
        ["observableId",
         "preequilibrationConditionId",
         "simulationConditionId"]
    ]
    # Get unique combinations of observableId, preequilibrationConditionId
    # and simulationConditionId
    df_unique_values = df.drop_duplicates()

    # Loop over each unique combination
    for nrow in range(len(df_unique_values.index)):
        df = petab_problem.measurement_df.loc[
            (petab_problem.measurement_df['observableId'] ==
             df_unique_values.loc[nrow, "observableId"])
            & (petab_problem.measurement_df['preequilibrationConditionId'] <=
               df_unique_values.loc[nrow, "preequilibrationConditionId"])
            & (petab_problem.measurement_df['simulationConditionId'] <=
               df_unique_values.loc[nrow, "simulationConditionId"])
        ]

        # Get list of unique observable parameters
        unique_sc = df["observableParameters"].unique()
        # Get list of unique noise parameters
        unique_noise = df["noiseParameters"].unique()

        # Loop
        for i_noise, cur_noise in enumerate(unique_noise):
            for i_sc, cur_sc in enumerate(unique_sc):
                # Find the position of all instances of cur_noise
                # and unique_sc[j] in their corresponding column
                # (full-string matches are denoted by zero)
                idxs = (
                        df["noiseParameters"].str.find(cur_noise) +
                        df["observableParameters"].str.find(cur_sc)
                )
                tmp_ = df.loc[idxs == 0, "observableId"]
                # Create replicate-specific observable name
                tmp = tmp_ + "_" + str(i_noise + i_sc + 1)
                # Check if replicate-specific observable name already exists
                # in df. If true, rename replicate-specific observable
                counter = 2
                while (df["observableId"].str.find(
                        tmp.to_string()
                ) == 0).any():
                    tmp = tmp_ + counter*"_" + str(i_noise + i_sc + 1)
                    counter += 1
                df.loc[idxs == 0, "observableId"] = tmp
                # Append the result in a new df
                df_new = df_new.append(df.loc[idxs == 0])
                # Restore the observable name in the original df
                # (for continuation of the loop)
                df.loc[idxs == 0, "observableId"] = tmp

    # Update/Redefine measurement df with replicate-specific observables
    petab_problem.measurement_df = df_new

    # Get list of already existing unique observable names
    unique_observables = df["observableId"].unique()

    # Remove already existing observables from the sbml model
    for obs in unique_observables:
        petab_problem.sbml_model.removeRuleByVariable("observable_" + obs)
        petab_problem.sbml_model.removeSpecies(obs)
        petab_problem.sbml_model.removeParameter(
            'observable_' + obs)

    # Redefine with replicate-specific observables in the sbml model
    for replicate_id in petab_problem.measurement_df["observableId"].unique():
        sbml.add_global_parameter(
            sbml_model=petab_problem.sbml_model,
            parameter_id='observableParameter1_' + replicate_id)
        sbml.add_global_parameter(
            sbml_model=petab_problem.sbml_model,
            parameter_id='noiseParameter1_' + replicate_id)
        sbml.add_model_output(
            sbml_model=petab_problem.sbml_model,
            observable_id=replicate_id,
            formula='observableParameter1_' + replicate_id)
        sbml.add_model_output_sigma(
            sbml_model=petab_problem.sbml_model,
            observable_id=replicate_id,
            formula='noiseParameter1_' + replicate_id)
