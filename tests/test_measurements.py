"""Tests related to petab.measurements"""
import numpy as np
import pandas as pd
import pytest
import tempfile

import petab
from petab.C import *


def test_get_placeholders():
    """Test get_placeholders"""

    # no placeholder
    assert petab.get_placeholders('1.0', 'any', 'observable') == []

    # multiple placeholders
    assert petab.get_placeholders(
        'observableParameter1_twoParams * '
        'observableParameter2_twoParams + otherParam',
        'twoParams', 'observable') \
        == ['observableParameter1_twoParams',
            'observableParameter2_twoParams']

    # noise placeholder
    assert petab.get_placeholders('3.0 * noiseParameter1_oneParam',
                                  'oneParam', 'noise') \
        == ['noiseParameter1_oneParam']

    # multiple instances and in 'wrong' order
    assert petab.get_placeholders(
        'observableParameter2_twoParams * '
        'observableParameter1_twoParams + '
        'otherParam / observableParameter2_twoParams',
        'twoParams', 'observable') \
        == ['observableParameter1_twoParams',
            'observableParameter2_twoParams']

    # non-consecutive numbering
    with pytest.raises(AssertionError):
        petab.get_placeholders(
            'observableParameter2_twoParams + observableParameter2_twoParams',
            'twoParams', 'observable')

    # empty
    assert petab.get_placeholders('', 'any', 'observable') == []

    # non-string
    assert petab.get_placeholders(1, 'any', 'observable') == []


def test_get_measurement_df():
    """Test measurements.get_measurement_df."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1', 'obs2'],
        OBSERVABLE_PARAMETERS: ['', 'p1;p2'],
        NOISE_PARAMETERS: ['p3;p4', 'p5']
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        file_name = fh.name
        measurement_df.to_csv(fh, sep='\t', index=False)

    df = petab.get_measurement_df(file_name).replace(np.nan, '')
    assert (df == measurement_df).all().all()

    # test other arguments
    assert (petab.get_measurement_df(measurement_df) == measurement_df) \
        .all().all()
    assert petab.get_measurement_df(None) is None


def test_write_measurement_df():
    """Test measurements.get_measurement_df."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1', 'obs2'],
        OBSERVABLE_PARAMETERS: ['', 'p1;p2'],
        NOISE_PARAMETERS: ['p3;p4', 'p5']
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=True) as fh:
        file_name = fh.name
        petab.write_measurement_df(measurement_df, file_name)
        re_df = petab.get_measurement_df(file_name).replace(np.nan, '')
        assert (measurement_df == re_df).all().all()


def test_create_measurement_df():
    """Test measurements.create_measurement_df."""
    df = petab.create_measurement_df()
    assert set(df.columns.values) == set(MEASUREMENT_DF_COLS)


def test_measurements_have_replicates():
    """Test measurements.measurements_have_replicates."""
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1', 'obs1'],
        OBSERVABLE_PARAMETERS: ['', 'p1;p2'],
        NOISE_PARAMETERS: ['p3;p4', 'p5'],
        TIME: [0, 1],
        MEASUREMENT: [42, 137.01]
    })
    assert not petab.measurements_have_replicates(measurement_df)

    measurement_df[TIME] = [1, 1]
    assert petab.measurements_have_replicates(measurement_df)
