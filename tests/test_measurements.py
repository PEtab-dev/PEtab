"""Tests related to petab.measurements"""
import petab
import pytest


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
