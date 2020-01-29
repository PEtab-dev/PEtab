"""Functions for working with the PEtab observables table"""

from typing import Union

import pandas as pd

from . import lint
from .C import *  # noqa: F403


def get_observable_df(
        observable_file_name: Union[str, pd.DataFrame, None]
) -> pd.DataFrame:
    """
    Read the provided observable file into a ``pandas.Dataframe``.

    Arguments:
        observable_file_name: Name of the file to read from.

    Returns:
        Observable DataFrame
    """
    if observable_file_name is None:
        return observable_file_name

    if isinstance(observable_file_name, pd.DataFrame):
        return observable_file_name

    observable_df = pd.read_csv(observable_file_name, sep='\t')
    lint.assert_no_leading_trailing_whitespace(
        observable_df.columns.values, "observable")
    try:
        observable_df.set_index([OBSERVABLE_ID], inplace=True)
    except KeyError:
        raise KeyError(
            f"Observable table missing mandatory field {OBSERVABLE_ID}.")

    return observable_df


def write_observable_df(df: pd.DataFrame, filename: str) -> None:
    """Write PEtab observable table

    Arguments:
        df: PEtab observable table
        filename: Destination file name
    """
    with open(filename, 'w') as fh:
        df.to_csv(fh, sep='\t', index=True)
