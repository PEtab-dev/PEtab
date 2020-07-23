"""Functions operating on the PEtab measurement table"""
# noqa: F405


import itertools
import numbers
from typing import List, Union, Dict
from warnings import warn

import numpy as np
import pandas as pd

from . import (lint, core, observables)
from .C import *  # noqa: F403


def get_measurement_df(
        measurement_file: Union[None, str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Read the provided measurement file into a ``pandas.Dataframe``.

    Arguments:
        measurement_file: Name of file to read from or pandas.Dataframe

    Returns:
        Measurement DataFrame
    """
    if measurement_file is None:
        return measurement_file

    if isinstance(measurement_file, str):
        measurement_file = pd.read_csv(measurement_file, sep='\t',
                                       float_precision='round_trip')

    lint.assert_no_leading_trailing_whitespace(
        measurement_file.columns.values, MEASUREMENT)

    return measurement_file


def write_measurement_df(df: pd.DataFrame, filename: str) -> None:
    """Write PEtab measurement table

    Arguments:
        df: PEtab measurement table
        filename: Destination file name
    """
    with open(filename, 'w') as fh:
        df.to_csv(fh, sep='\t', index=False)


def get_noise_distributions(measurement_df: pd.DataFrame) -> dict:
    """
    Returns dictionary of cost definitions per observable, if specified.

    Looks through all parameters satisfying `sbml_parameter_is_cost` and
    return as dictionary.

    Parameters:
        measurement_df: PEtab measurement table

    Returns:
        Dictionary with `observableId` => `cost definition`
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    lint.assert_noise_distributions_valid(measurement_df)

    # read noise distributions from measurement file
    grouping_cols = core.get_notnull_columns(
        measurement_df, [OBSERVABLE_ID, OBSERVABLE_TRANSFORMATION,
                         NOISE_DISTRIBUTION])

    observables = measurement_df.fillna('').groupby(grouping_cols).size()\
        .reset_index()
    noise_distrs = {}
    for _, row in observables.iterrows():
        # prefix id to get observable id
        id_ = 'observable_' + row.observableId

        # extract observable transformation and noise distribution,
        # use lin+normal as default if none provided
        obs_trafo = row.observableTransformation \
            if OBSERVABLE_TRANSFORMATION in row \
            and row.observableTransformation \
            else LIN
        noise_distr = row.noiseDistribution \
            if NOISE_DISTRIBUTION in row \
            and row.noiseDistribution \
            else NORMAL
        # add to noise distributions
        noise_distrs[id_] = {
            OBSERVABLE_TRANSFORMATION: obs_trafo,
            NOISE_DISTRIBUTION: noise_distr}

    return noise_distrs


def get_simulation_conditions(measurement_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a table of separate simulation conditions. A simulation condition
    is a specific combination of simulationConditionId and
    preequilibrationConditionId.

    Arguments:
        measurement_df: PEtab measurement table

    Returns:
        Dataframe with columns 'simulationConditionId' and
        'preequilibrationConditionId'. All-null columns will be omitted.
        Missing 'preequilibrationConditionId's will be set to '' (empty
        string).
    """
    # find columns to group by (i.e. if not all nans).
    # can be improved by checking for identical condition vectors
    grouping_cols = core.get_notnull_columns(
        measurement_df,
        [SIMULATION_CONDITION_ID, PREEQUILIBRATION_CONDITION_ID])

    # group by cols and return dataframe containing each combination
    #  of those rows only once (and an additional counting row)
    # We require NaN-containing rows, but they are ignored by `groupby`,
    # therefore replace them before
    simulation_conditions = measurement_df.fillna('').groupby(
        grouping_cols).size().reset_index()[grouping_cols]
    # sort to be really sure that we always get the same order
    return simulation_conditions.sort_values(grouping_cols, ignore_index=True)


def get_rows_for_condition(measurement_df: pd.DataFrame,
                           condition: Union[pd.Series, pd.DataFrame, Dict]
                           ) -> pd.DataFrame:
    """
    Extract rows in `measurement_df` for `condition` according
    to 'preequilibrationConditionId' and 'simulationConditionId' in
    `condition`.

    Arguments:
        measurement_df:
            PEtab measurement DataFrame
        condition:
            DataFrame with single row (or Series) and columns
            'preequilibrationConditionId' and 'simulationConditionId'.
            Or dictionary with those keys.

    Returns:
        The subselection of rows in ``measurement_df`` for the condition
    ``condition``.
    """
    # filter rows for condition
    row_filter = 1
    # check for equality in all grouping cols
    if PREEQUILIBRATION_CONDITION_ID in condition:
        row_filter = (measurement_df[PREEQUILIBRATION_CONDITION_ID]
                      .fillna('') ==
                      condition[PREEQUILIBRATION_CONDITION_ID]) & row_filter
    if SIMULATION_CONDITION_ID in condition:
        row_filter = (measurement_df[SIMULATION_CONDITION_ID] ==
                      condition[SIMULATION_CONDITION_ID]) & row_filter
    # apply filter
    cur_measurement_df = measurement_df.loc[row_filter, :]

    return cur_measurement_df


def get_measurement_parameter_ids(measurement_df: pd.DataFrame) -> List[str]:
    """
    Return list of ID of parameters which occur in measurement table as
    observable or noise parameter overrides.

    Arguments:
        measurement_df:
            PEtab measurement DataFrame

    Returns:
        List of parameter IDs
    """

    def get_unique_parameters(series):
        return core.unique_preserve_order(
            itertools.chain.from_iterable(
                series.apply(split_parameter_replacement_list)))

    return core.unique_preserve_order(
        get_unique_parameters(measurement_df[OBSERVABLE_PARAMETERS])
        + get_unique_parameters(measurement_df[NOISE_PARAMETERS]))


def split_parameter_replacement_list(
        list_string: Union[str, numbers.Number],
        delim: str = ';') -> List[Union[str, float]]:
    """
    Split values in observableParameters and noiseParameters in measurement
    table.

    Arguments:
        list_string: delim-separated stringified list
        delim: delimiter

    Returns:
         List of split values. Numeric values converted to float.
    """
    if list_string is None:
        return []

    if isinstance(list_string, numbers.Number):
        # Empty cells in pandas might be turned into nan
        # We might want to allow nan as replacement...
        if np.isnan(list_string):
            return []
        return [list_string]

    result = [x.strip() for x in list_string.split(delim) if len(x.strip())]
    return [core.to_float_if_float(x) for x in result]


def create_measurement_df() -> pd.DataFrame:
    """Create empty measurement dataframe

    Returns:
        Created DataFrame
    """

    df = pd.DataFrame(data={
        OBSERVABLE_ID: [],
        PREEQUILIBRATION_CONDITION_ID: [],
        SIMULATION_CONDITION_ID: [],
        MEASUREMENT: [],
        TIME: [],
        OBSERVABLE_PARAMETERS: [],
        NOISE_PARAMETERS: [],
        DATASET_ID: [],
        REPLICATE_ID: []
    })

    return df


def measurements_have_replicates(measurement_df: pd.DataFrame) -> bool:
    """Tests whether the measurements come with replicates

    Arguments:
        measurement_df: Measurement table

    Returns:
        ``True`` if there are replicates, ``False`` otherwise
    """
    grouping_cols = core.get_notnull_columns(
        measurement_df,
        [OBSERVABLE_ID, SIMULATION_CONDITION_ID,
         PREEQUILIBRATION_CONDITION_ID, TIME])
    return np.any(
        measurement_df.fillna('').groupby(grouping_cols).size().values - 1)


def assert_overrides_match_parameter_count(
        measurement_df: pd.DataFrame,
        observable_df: pd.DataFrame) -> None:
    """Ensure that number of parameters in the observable definition matches
    the number of overrides in ``measurement_df``

    Arguments:
        measurement_df: PEtab measurement table
        observable_df: PEtab observable table
    """

    # sympify only once and save number of parameters
    observable_parameters_count = {
        obs_id: len(observables.get_formula_placeholders(
            formula, obs_id, 'observable'))
        for obs_id, formula in zip(observable_df.index.values,
                                   observable_df[OBSERVABLE_FORMULA])}
    noise_parameters_count = {
        obs_id:
            len(observables.get_formula_placeholders(formula, obs_id, 'noise'))
        for obs_id, formula in zip(observable_df.index.values,
                                   observable_df[NOISE_FORMULA])}

    for _, row in measurement_df.iterrows():
        # check observable parameters
        try:
            expected = observable_parameters_count[row[OBSERVABLE_ID]]
        except KeyError:
            raise ValueError(
                f"Observable {row[OBSERVABLE_ID]} used in measurement table "
                f"is not defined.")
        actual = len(split_parameter_replacement_list(
            row.get(OBSERVABLE_PARAMETERS, None)))
        # No overrides are also allowed
        if actual not in [0, expected]:
            formula = observable_df.loc[row[OBSERVABLE_ID], OBSERVABLE_FORMULA]
            raise AssertionError(
                f'Mismatch of observable parameter overrides for '
                f'{row[OBSERVABLE_ID]} ({formula})'
                f'in:\n{row}\n'
                f'Expected 0 or {expected} but got {actual}')

        # check noise parameters
        replacements = split_parameter_replacement_list(
            row.get(NOISE_PARAMETERS, None))
        try:
            expected = noise_parameters_count[row[OBSERVABLE_ID]]

            # No overrides are also allowed
            if not (len(replacements) == 0 or len(replacements) == expected):
                raise AssertionError(
                    f'Mismatch of noise parameter overrides in:\n{row}\n'
                    f'Expected 0 or {expected} but got {actual}')
        except KeyError:
            # no overrides defined, but a numerical sigma can be provided
            # anyways
            if not len(replacements) == 1 \
                    or not isinstance(replacements[0], numbers.Number):
                raise AssertionError(
                    f'No placeholders have been specified in the noise model '
                    f'for observable {row[OBSERVABLE_ID]}, but parameter ID '
                    'or multiple overrides were specified in the '
                    'noiseParameters column.')
