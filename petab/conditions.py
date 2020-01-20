"""Functions operating on the PEtab condition table"""

from typing import Iterable, Optional, List

import numpy as np
import pandas as pd

from . import lint, parameters, core


def get_condition_df(condition_file_name: str) -> pd.DataFrame:
    """Read the provided condition file into a ``pandas.Dataframe``

    Conditions are rows, parameters are columns, conditionId is index.

    Arguments:
        condition_file_name: File name of PEtab condition file
    """

    condition_df = pd.read_csv(condition_file_name, sep='\t')
    lint.assert_no_leading_trailing_whitespace(
        condition_df.columns.values, "condition")

    try:
        condition_df.set_index(['conditionId'], inplace=True)
    except KeyError:
        raise KeyError(
            'Condition table missing mandatory field `conditionId`.')

    return condition_df


def create_condition_df(parameter_ids: Iterable[str],
                        condition_ids: Optional[Iterable[str]] = None
                        ) -> pd.DataFrame:
    """Create empty condition DataFrame

    Arguments:
        parameter_ids: the columns
        condition_ids: the rows
    Returns:
        A ``pandas.DataFrame`` with empty given rows and columns and all nan
        values
    """

    data = {'conditionId': []}
    for p in parameter_ids:
        if not parameters.parameter_id_is_valid(p):
            raise ValueError("Invalid parameter name: " + p)
        data[p] = []

    df = pd.DataFrame(data)
    df.set_index(['conditionId'], inplace=True)

    if not condition_ids:
        return df

    for c in condition_ids:
        df[c] = np.nan

    return df


def get_parametric_overrides(condition_df: pd.DataFrame) -> List[str]:
    """Get parametric overrides from condition table

    Arguments:
        condition_df: PEtab condition table

    Returns:
        List of parameter IDs that are mapped in a condition-specific way
    """
    constant_parameters = list(
        set(condition_df.columns.values.tolist()) - {'conditionId',
                                                     'conditionName'})
    result = []

    for column in constant_parameters:
        if np.issubdtype(condition_df[column].dtype, np.number):
            continue

        floatified = condition_df.loc[:, column].apply(core.to_float_if_float)

        for x in floatified:
            if not isinstance(x, float):
                result.append(x)
    return result
