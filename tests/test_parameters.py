"""Tests for petab/parameters.py"""
import tempfile
import pytest
import numpy as np
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

    # Test parameter subset files
    with tempfile.TemporaryDirectory() as directory:
        parameter_dfs, parameter_files = ({}, {})
        parameter_dfs['complete'] = pd.DataFrame(data={
            PARAMETER_ID: ['id1', 'id2', 'id3'],
            PARAMETER_NAME: ['name1', 'name2', 'name3']
        })
        parameter_dfs['subset1'] = pd.DataFrame(data={
            PARAMETER_ID: ['id1', 'id2'],
            PARAMETER_NAME: ['name1', 'name2']
        })
        parameter_dfs['subset2_strict'] = pd.DataFrame(data={
            PARAMETER_ID: ['id3'],
            PARAMETER_NAME: ['name3']
        })
        parameter_dfs['subset2_overlap'] = pd.DataFrame(data={
            PARAMETER_ID: ['id2', 'id3'],
            PARAMETER_NAME: ['name2', 'name3']
        })
        parameter_dfs['subset2_error'] = pd.DataFrame(data={
            PARAMETER_ID: ['id2', 'id3'],
            PARAMETER_NAME: ['different_name2', 'name3']
        })
        for name, df in parameter_dfs.items():
            with tempfile.NamedTemporaryFile(
                    mode='w', delete=False, dir=directory) as fh:
                parameter_files[name] = fh.name
                parameter_dfs[name].to_csv(fh, sep='\t', index=False)
        # Check that subset files are correctly combined
        assert(petab.get_parameter_df(parameter_files['complete']).equals(
            petab.get_parameter_df([parameter_files['subset1'],
                                    parameter_files['subset2_strict']])))
        # Check that identical parameter definitions are correctly combined
        assert(petab.get_parameter_df(parameter_files['complete']).equals(
            petab.get_parameter_df([parameter_files['subset1'],
                                    parameter_files['subset2_overlap']])))
        # Ensure an error is raised if there exist parameterId duplicates
        # with non-identical parameter definitions
        with pytest.raises(ValueError):
            petab.get_parameter_df([parameter_files['subset1'],
                                    parameter_files['subset2_error']])


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
    expected[INITIALIZATION_PRIOR_TYPE] = [PARAMETER_SCALE_UNIFORM] * 3
    expected[INITIALIZATION_PRIOR_PARAMETERS] = ["-5;5", "-6;6", "1e-7;1e7"]
    expected[OBJECTIVE_PRIOR_TYPE] = [PARAMETER_SCALE_UNIFORM] * 3
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


def test_scale_unscale():
    """Test the parameter scaling functions."""
    par = 2.5
    # scale
    assert petab.scale(par, LIN) == par
    assert petab.scale(par, LOG) == np.log(par)
    assert petab.scale(par, LOG10) == np.log10(par)
    # unscale
    assert petab.unscale(par, LIN) == par
    assert petab.unscale(par, LOG) == np.exp(par)
    assert petab.unscale(par, LOG10) == 10**par

    # map scale
    assert list(petab.map_scale([par]*3, [LIN, LOG, LOG10])) == \
        [par, np.log(par), np.log10(par)]
    # map unscale
    assert list(petab.map_unscale([par]*3, [LIN, LOG, LOG10])) == \
        [par, np.exp(par), 10**par]

    # map broadcast
    assert list(petab.map_scale([par, 2*par], LOG)) == \
        list(np.log([par, 2*par]))
    assert list(petab.map_unscale([par, 2*par], LOG)) == \
        list(np.exp([par, 2*par]))
