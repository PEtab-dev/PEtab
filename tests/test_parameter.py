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
