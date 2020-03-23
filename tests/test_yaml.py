"""Test for petab.yaml"""
import tempfile

import pytest
from petab.yaml import validate, create_problem_yaml

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


def test_create_problem_yaml():
    with tempfile.TemporaryDirectory() as folder:
        # test with single problem files
        # create target files
        sbml_file = tempfile.mkstemp(dir=folder)[1]
        condition_file = tempfile.mkstemp(dir=folder)[1]
        measurement_file = tempfile.mkstemp(dir=folder)[1]
        parameter_file = tempfile.mkstemp(dir=folder)[1]
        observable_file = tempfile.mkstemp(dir=folder)[1]
        yaml_file = tempfile.mkstemp(dir=folder)[1]
        visualization_file = tempfile.mkstemp(dir=folder)[1]
        create_problem_yaml(sbml_file, condition_file, measurement_file,
                            parameter_file, observable_file, yaml_file,
                            visualization_file)
        validate(yaml_file)

        # test for list of files
        # create additional target files
        sbml_file2 = tempfile.mkstemp(dir=folder)[1]
        condition_file2 = tempfile.mkstemp(dir=folder)[1]
        measurement_file2 = tempfile.mkstemp(dir=folder)[1]
        observable_file2 = tempfile.mkstemp(dir=folder)[1]
        yaml_file2 = tempfile.mkstemp(dir=folder)[1]

        sbml_files = [sbml_file, sbml_file2]
        condition_files = [condition_file, condition_file2]
        measurement_files = [measurement_file, measurement_file2]
        observable_files = [observable_file, observable_file2]
        create_problem_yaml(sbml_files, condition_files, measurement_files,
                            parameter_file, observable_files, yaml_file2)
        validate(yaml_file2)

