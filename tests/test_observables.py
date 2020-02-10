"""Tests for petab.observables"""
import pandas as pd
import pytest
import tempfile

import petab
from petab.C import *


def test_get_observable_df():
    """Test measurements.get_measurement_df."""
    # without id
    observable_df = pd.DataFrame(data={
        OBSERVABLE_NAME: ['observable name 1'],
        OBSERVABLE_FORMULA: ['observable_1'],
        NOISE_FORMULA: [1],
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        file_name = fh.name
        observable_df.to_csv(fh, sep='\t', index=False)

    with pytest.raises(KeyError):
        petab.get_observable_df(file_name)

    # with id
    observable_df[OBSERVABLE_ID] = ['observable_1']

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        file_name = fh.name
        observable_df.to_csv(fh, sep='\t', index=False)

    df = petab.get_observable_df(file_name)
    assert (df == observable_df.set_index(OBSERVABLE_ID)).all().all()

    # test other arguments
    assert (petab.get_observable_df(observable_df) == observable_df) \
        .all().all()
    assert petab.get_observable_df(None) is None


def test_write_observable_df():
    """Test measurements.get_measurement_df."""
    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['observable_1'],
        OBSERVABLE_NAME: ['observable name 1'],
        OBSERVABLE_FORMULA: ['observable_1'],
        NOISE_FORMULA: [1],
    }).set_index(OBSERVABLE_ID)

    with tempfile.NamedTemporaryFile(mode='w', delete=True) as fh:
        file_name = fh.name
        petab.write_observable_df(observable_df, file_name)
        re_df = petab.get_observable_df(file_name)
        assert (observable_df == re_df).all().all()


def test_get_output_parameters(minimal_sbml_model):
    """Test measurements.get_output_parameters."""
    # sbml model
    _, model = minimal_sbml_model

    p = model.createParameter()
    p.setId('fixedParameter1')
    p.setName('FixedParameter1')

    p = model.createParameter()
    p.setId('observable_1')
    p.setName('Observable 1')

    # observable file
    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['observable_1'],
        OBSERVABLE_NAME: ['observable name 1'],
        OBSERVABLE_FORMULA: ['observable_1 * scaling + offset'],
        NOISE_FORMULA: [1],
    }).set_index(OBSERVABLE_ID)

    output_parameters = petab.get_output_parameters(observable_df, model)

    assert output_parameters == {'scaling', 'offset'}
