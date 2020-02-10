"""Tests related to petab.conditions"""
import numpy as np
import pandas as pd
import tempfile
import pytest

import petab
from petab import conditions
from petab.C import *


def test_get_parametric_overrides():

    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        CONDITION_NAME: ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })

    assert conditions.get_parametric_overrides(condition_df) == []

    condition_df.fixedParameter1 = \
        condition_df.fixedParameter1.values.astype(int)

    assert conditions.get_parametric_overrides(condition_df) == []

    condition_df.loc[0, 'fixedParameter1'] = 'parameterId'

    assert conditions.get_parametric_overrides(condition_df) == ['parameterId']


def test_get_condition_df():
    """Test conditions.get_condition_df."""
    # condition df missing ids
    condition_df = pd.DataFrame(data={
        CONDITION_NAME: ['Condition 1', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        file_name = fh.name
        condition_df.to_csv(fh, sep='\t', index=False)

    with pytest.raises(KeyError):
        petab.get_condition_df(file_name)

    # with ids
    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        CONDITION_NAME: ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        file_name = fh.name
        condition_df.to_csv(fh, sep='\t', index=False)

    df = petab.get_condition_df(file_name).replace(np.nan, '')
    assert (df == condition_df.set_index(CONDITION_ID)).all().all()

    # test other arguments
    assert (petab.get_condition_df(condition_df) == condition_df).all().all()
    assert petab.get_condition_df(None) is None


def test_write_condition_df():
    """Test conditions.write_condition_df."""
    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        CONDITION_NAME: ['Condition 1', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    }).set_index(CONDITION_ID)

    with tempfile.NamedTemporaryFile(mode='w', delete=True) as fh:
        file_name = fh.name
        petab.write_condition_df(condition_df, file_name)
        re_df = petab.get_condition_df(file_name)
        assert (condition_df == re_df).all().all()


def test_create_condition_df():
    """Test conditions.create_condition_df."""
    parameter_ids = ['par1', 'par2', 'par3']
    condition_ids = ['condition1', 'condition2']

    df = petab.create_condition_df(parameter_ids, condition_ids)

    expected = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        'par1': [np.nan, np.nan],
        'par2': [np.nan, np.nan],
        'par3': [np.nan, np.nan]
    }).set_index(CONDITION_ID)

    assert ((df == expected) | df.isna() == expected.isna()).all().all()
