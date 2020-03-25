"""Tests for petab/parameters.py"""
import tempfile
import pytest

import pandas as pd
import petab
from petab.C import *


def test_get_optimization_parameter_scaling():
    """Test get_optimization_parameter_scaling"""
    df = pd.DataFrame(data={
        PARAMETER_ID: ['p1', 'p2', 'p3'],
        ESTIMATE: [1, 0, 1],
        PARAMETER_SCALE: [LIN, LOG, LOG10]
    })
    df.set_index(PARAMETER_ID, inplace=True)

    # parameter and scale
    expected = dict(p1=LIN, p3=LOG10)

    actual = petab.get_optimization_parameter_scaling(df)

    assert actual == expected


def test_get_optimization_parameters():
    """Test get_optimization_parameters"""
    df = pd.DataFrame(data={
        PARAMETER_ID: ['p1', 'p2', 'p3'],
        ESTIMATE: [1, 0, 1],
    })
    df.set_index(PARAMETER_ID, inplace=True)

    expected = ['p1', 'p3']

    actual = petab.get_optimization_parameters(df)

    assert actual == expected


def test_get_parameter_df():
    """Test parameters.get_parameter_df."""
    # parameter df missing ids
    parameter_df = pd.DataFrame(data={
        PARAMETER_NAME: ['parname1', 'parname2'],
    })
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        file_name = fh.name
        parameter_df.to_csv(fh, sep='\t', index=False)

    with pytest.raises(KeyError):
        petab.get_parameter_df(file_name)

    # with ids
    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2'],
        PARAMETER_NAME: ['parname1', 'parname2'],
    })
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        file_name = fh.name
        parameter_df.to_csv(fh, sep='\t', index=False)

    df = petab.get_parameter_df(file_name)
    assert (df == parameter_df.set_index(PARAMETER_ID)).all().all()


def test_write_parameter_df():
    """Test parameters.write_parameter_df."""
    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2'],
        PARAMETER_NAME: ['parname1', 'parname2'],
    }).set_index(PARAMETER_ID)

    with tempfile.NamedTemporaryFile(mode='w', delete=True) as fh:
        file_name = fh.name
        petab.write_parameter_df(parameter_df, file_name)
        re_df = petab.get_parameter_df(file_name)
        assert (parameter_df == re_df).all().all()


def test_normalize_parameter_df():
    """Check parameters.normalize_parameter_df."""
    parameter_df = pd.DataFrame({
        PARAMETER_ID: ['par0', 'par1', 'par2'],
        PARAMETER_SCALE: [LOG10, LOG10, LIN],
        NOMINAL_VALUE: [1e-2, 1e-3, 1e-4],
        ESTIMATE: [1, 1, 0],
        LOWER_BOUND: [1e-5, 1e-6, 1e-7],
        UPPER_BOUND: [1e5, 1e6, 1e7]
    }).set_index(PARAMETER_ID)

    actual = petab.normalize_parameter_df(parameter_df)

    expected = parameter_df.copy(deep=True)
    expected[PARAMETER_NAME] = parameter_df.reset_index()[PARAMETER_ID]
    expected[INITIALIZATION_PRIOR_TYPE] = [UNINFORMATIVE] * 3
    expected[INITIALIZATION_PRIOR_PARAMETERS] = ["-5;5", "-6;6", "1e-7;1e7"]
    expected[OBJECTIVE_PRIOR_TYPE] = [UNINFORMATIVE] * 3
    expected[OBJECTIVE_PRIOR_PARAMETERS] = ["-5;5", "-6;6", "1e-7;1e7"]

    # check ids
    assert list(actual.index.values) == list(expected.index.values)

    # check if basic columns match
    for col in PARAMETER_DF_COLS[1:]:
        if col in [INITIALIZATION_PRIOR_PARAMETERS,
                   OBJECTIVE_PRIOR_PARAMETERS]:
            continue
        assert ((actual[col] == expected[col]) |
                (actual[col].isnull() == expected[col].isnull())).all()

    # check if prior parameters match
    for col in [INITIALIZATION_PRIOR_PARAMETERS, OBJECTIVE_PRIOR_PARAMETERS]:
        for (_, actual_row), (_, expected_row) in \
                zip(actual.iterrows(), expected.iterrows()):
            actual_pars = tuple([float(val) for val in
                                 actual_row[col].split(';')])
            expected_pars = tuple([float(val) for val in
                                   expected_row[col].split(';')])

            assert actual_pars == expected_pars

    # check is a projection
    actual2 = petab.normalize_parameter_df(actual)
    assert ((actual == actual2) | (actual.isnull() == actual2.isnull())) \
        .all().all()

    # check is valid petab
    petab.check_parameter_df(actual)
