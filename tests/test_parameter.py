"""Tests for petab/parameters.py"""
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
