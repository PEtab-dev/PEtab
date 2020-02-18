"""Functions for working with the PEtab observables table"""

from typing import Union, Set

import libsbml
import pandas as pd
import sympy as sp

from . import lint
from .C import *  # noqa: F403


def get_observable_df(
        observable_file: Union[str, pd.DataFrame, None]
) -> pd.DataFrame:
    """
    Read the provided observable file into a ``pandas.Dataframe``.

    Arguments:
        observable_file: Name of the file to read from or pandas.Dataframe.

    Returns:
        Observable DataFrame
    """
    if observable_file is None:
        return observable_file

    if isinstance(observable_file, str):
        observable_file = pd.read_csv(observable_file, sep='\t')

    lint.assert_no_leading_trailing_whitespace(
        observable_file.columns.values, "observable")

    if not isinstance(observable_file.index, pd.RangeIndex):
        observable_file.reset_index(inplace=True)

    try:
        observable_file.set_index([OBSERVABLE_ID], inplace=True)
    except KeyError:
        raise KeyError(
            f"Observable table missing mandatory field {OBSERVABLE_ID}.")

    return observable_file


def write_observable_df(df: pd.DataFrame, filename: str) -> None:
    """Write PEtab observable table

    Arguments:
        df: PEtab observable table
        filename: Destination file name
    """
    with open(filename, 'w') as fh:
        df.to_csv(fh, sep='\t', index=True)


def get_output_parameters(observable_df: pd.DataFrame,
                          sbml_model: libsbml.Model) -> Set[str]:
    """Get output parameters

    Returns IDs of parameters used in observable and noise formulas that are
    not defined in the SBML model.

    Arguments:
        observable_df: PEtab observable table
        sbml_model: SBML model

    Returns:
        List of output parameter IDs
    """
    formulas = set(observable_df[OBSERVABLE_FORMULA])
    formulas |= set(observable_df[NOISE_FORMULA])
    output_parameters = set()

    for formula in formulas:
        for free_sym in sp.sympify(formula).free_symbols:
            sym = str(free_sym)
            if sbml_model.getElementBySId(sym) is None:
                output_parameters.add(sym)

    return output_parameters
