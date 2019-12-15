"""Code regarding the PEtab YAML config files"""

import os

from typing import Dict, Union, Optional

import jsonschema
import yaml


SCHEMA = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      "petab_schema.yaml")


def validate(yaml_config: Union[Dict, str], wd: Optional[str] = None):
    """Validate syntax and semantics of PEtab config YAML

    Arguments:
        yaml_config:
            PEtab YAML config as filename or dict.
        wd:
            Working directory for relative paths. Defaults to location of YAML
            file if a filename was provided for ``yaml_config`` or the current
            working directory.
    """

    validate_yaml_syntax(yaml_config)
    validate_yaml_semantics(yaml_config, wd)


def validate_yaml_syntax(
        yaml_config: Union[Dict, str],
        schema: Union[None, Dict, str] = None):
    """Validate PEtab YAML file syntax

    Arguments:
        yaml_config:
            PEtab YAML file to validate, as file name or dictionary
        schema:
            Custom schema for validation

    Raises:
        see jsonschema.validate
    """

    if schema is None:
        schema = SCHEMA

    if isinstance(schema, str):
        with open(schema) as f:
            schema = yaml.load(f)

    if isinstance(yaml_config, str):
        with open(yaml_config) as f:
            yaml_config = yaml.load(f)

    jsonschema.validate(instance=yaml_config, schema=schema)


def validate_yaml_semantics(
        yaml_config: Union[Dict, str], wd: Optional[str] = None):
    """Validate PEtab YAML file semantics

    Check for existence of files. Assumes valid syntax.

    Version number and contents of referenced files are not yet checked.

    Arguments:
        yaml_config:
            PEtab YAML config as filename or dict.
        wd:
            Working directory for relative paths. Defaults to location of YAML
            file if a filename was provided for ``yaml_config`` or the current
            working directory.

    Raises:
        AssertionError: in case of problems
    """
    if isinstance(yaml_config, str):
        if not wd:
            wd = os.path.dirname(yaml_config)
        with open(yaml_config) as f:
            yaml_config = yaml.load(f)

    if wd:
        old_wd = os.getcwd()
        os.chdir(wd)

    def _check_file(_filename: str, _field: str):
        if not os.path.isfile(_filename):
            raise AssertionError(f"File '{_filename}' provided as '{_field}' "
                                 "does not exist.")

    try:
        for problem_config in yaml_config['problems']:
            for field in ['sbml_file', 'condition_file']:
                _check_file(problem_config[field], field)
            for filename in problem_config['measurement_files']:
                _check_file(filename, 'measurement_files')

    finally:
        if wd:
            os.chdir(old_wd)
