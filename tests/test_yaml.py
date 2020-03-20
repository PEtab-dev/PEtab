"""Test for petab.yaml"""

import pytest
from petab.yaml import validate, create_default_yaml

from jsonschema.exceptions import ValidationError


def test_validate():
    data = {
        'format_version': '1'
    }

    # should fail because we miss some information
    with pytest.raises(ValidationError):
        validate(data)

    # should be well-formed
    file_ = "doc/example/example_Fujita/Fujita.yaml"
    validate(file_)


def test_create_default_yaml():
    create_default_yaml('test')
