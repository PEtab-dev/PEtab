"""Test for petab.yaml"""

import pytest
from petab.yaml import validate

from jsonschema.exceptions import ValidationError


def test_validate():
    data = {
        'petab_version': '1.1.1'
    }

    # should fail because we miss some information
    with pytest.raises(ValidationError):
        validate(data)
