"""Functions for working with the PEtab observables table"""

from _collections import OrderedDict
from typing import Union, List

import libsbml
import pandas as pd
import re
import sympy as sp

from . import lint, core
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
        observable_file = pd.read_csv(observable_file, sep='\t',
                                      float_precision='round_trip')

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
                          sbml_model: libsbml.Model) -> List[str]:
    """Get output parameters

    Returns IDs of parameters used in observable and noise formulas that are
    not defined in the SBML model.

    Arguments:
        observable_df: PEtab observable table
        sbml_model: SBML model

    Returns:
        List of output parameter IDs
    """
    formulas = list(observable_df[OBSERVABLE_FORMULA])
    if NOISE_FORMULA in observable_df:
        formulas.extend(observable_df[NOISE_FORMULA])
    output_parameters = OrderedDict()

    for formula in formulas:
        free_syms = sorted(sp.sympify(formula).free_symbols,
                           key=lambda symbol: symbol.name)
        for free_sym in free_syms:
            sym = str(free_sym)
            if sbml_model.getElementBySId(sym) is None and sym != 'time':
                output_parameters[sym] = None

    return list(output_parameters.keys())


def get_formula_placeholders(formula_string: str, observable_id: str,
                             override_type: str) -> List[str]:
    """
    Get placeholder variables in noise or observable definition for the
    given observable ID.

    Arguments:
        formula_string: observable formula
        observable_id: ID of current observable
        override_type: 'observable' or 'noise', depending on whether `formula`
            is for observable or for noise model

    Returns:
        List of placeholder parameter IDs in the order expected in the
        observableParameter column of the measurement table.
    """
    if not formula_string:
        return []

    if not isinstance(formula_string, str):
        return []

    pattern = re.compile(r'(?:^|\W)(' + re.escape(override_type)
                         + r'Parameter\d+_' + re.escape(observable_id)
                         + r')(?=\W|$)')
    placeholder_set = set(pattern.findall(formula_string))

    # need to sort and check that there are no gaps in numbering
    placeholders = [f"{override_type}Parameter{i}_{observable_id}"
                    for i in range(1, len(placeholder_set) + 1)]

    if placeholder_set != set(placeholders):
        raise AssertionError("Non-consecutive numbering of placeholder "
                             f"parameter for {placeholder_set}")

    return placeholders


def get_placeholders(observable_df: pd.DataFrame) -> List[str]:
    """Get all placeholder parameters from observable table observableFormulas
    and noiseFormulas

    Arguments:
        observable_df: PEtab observable table

    Returns:
        List of placeholder parameters from observable table observableFormulas
        and noiseFormulas.
    """

    # collect placeholder parameters overwritten by
    # {observable,noise}Parameters
    placeholders = []
    for _, row in observable_df.iterrows():
        for placeholder_type, formula_column \
                in zip(['observable', 'noise'],
                       [OBSERVABLE_FORMULA, NOISE_FORMULA]):
            if formula_column not in row:
                continue

            cur_placeholders = get_formula_placeholders(
                row[formula_column], row.name, placeholder_type)
            placeholders.extend(cur_placeholders)
    return core.unique_preserve_order(placeholders)


def create_observable_df() -> pd.DataFrame:
    """Create empty observable dataframe

    Returns:
        Created DataFrame
    """

    df = pd.DataFrame(data={col: [] for col in OBSERVABLE_DF_COLS})

    return df
