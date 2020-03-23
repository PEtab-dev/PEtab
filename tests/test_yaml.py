"""Test for petab.yaml"""
import tempfile

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
    with tempfile.TemporaryDirectory() as folder:
        # create target files
        sbml_file = tempfile.mkstemp(dir=folder)[1]
        condition_file = tempfile.mkstemp(dir=folder)[1]
        measurement_file = tempfile.mkstemp(dir=folder)[1]
        parameter_file = tempfile.mkstemp(dir=folder)[1]
        observable_file = tempfile.mkstemp(dir=folder)[1]
        yaml_file = tempfile.mkstemp(dir=folder)[1]
        visualization_file = tempfile.mkstemp(dir=folder)[1]
        create_default_yaml(sbml_file, condition_file, measurement_file,
                            parameter_file, observable_file, yaml_file,
                            visualization_file)
        validate(yaml_file)
