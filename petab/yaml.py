"""Code regarding the PEtab YAML config files"""

import os

from typing import Dict, Union, Optional

import jsonschema
import yaml


SCHEMA = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      "petab_schema.yaml")


def validate(yaml_config: Union[Dict, str], path_prefix: Optional[str] = None):
    """Validate syntax and semantics of PEtab config YAML

    Arguments:
        yaml_config:
            PEtab YAML config as filename or dict.
        path_prefix:
            Base location for relative paths. Defaults to location of YAML
            file if a filename was provided for ``yaml_config`` or the current
            working directory.
    """

    validate_yaml_syntax(yaml_config)
    validate_yaml_semantics(yaml_config=yaml_config,
                            path_prefix=path_prefix)


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

    schema = load_yaml(schema)
    yaml_config = load_yaml(yaml_config)

    jsonschema.validate(instance=yaml_config, schema=schema)


def validate_yaml_semantics(
        yaml_config: Union[Dict, str], path_prefix: Optional[str] = None):
    """Validate PEtab YAML file semantics

    Check for existence of files. Assumes valid syntax.

    Version number and contents of referenced files are not yet checked.

    Arguments:
        yaml_config:
            PEtab YAML config as filename or dict.
        path_prefix:
            Base location for relative paths. Defaults to location of YAML
            file if a filename was provided for ``yaml_config`` or the current
            working directory.

    Raises:
        AssertionError: in case of problems
    """
    if not path_prefix:
        if isinstance(yaml_config, str):
            path_prefix = os.path.dirname(yaml_config)
        else:
            path_prefix = ""

    yaml_config = load_yaml(yaml_config)

    def _check_file(_filename: str, _field: str):
        if not os.path.isfile(_filename):
            raise AssertionError(f"File '{_filename}' provided as '{_field}' "
                                 "does not exist.")

    _check_file(os.path.join(path_prefix, yaml_config['parameter_file']),
                'parameter_file')
    for problem_config in yaml_config['problems']:
        for field in ['sbml_files', 'condition_files',
                      'measurement_files']:
            for filename in problem_config[field]:
                _check_file(os.path.join(path_prefix, filename), field)


def load_yaml(yaml_config: Union[Dict, str]) -> Dict:
    """Load YAML

    Convenience function to allow for providing YAML inputs either as filename
    or as dictionary.

    Arguments:
        yaml_config:
            PEtab YAML config as filename or dict.

    Returns:
        The unmodified dictionary if ``yaml_config`` was dictionary.
        Otherwise the parsed the YAML file.
    """

    if isinstance(yaml_config, str):
        with open(yaml_config) as f:
            return yaml.full_load(f)

    return yaml_config


def is_composite_problem(yaml_config: Union[Dict, str]) -> bool:
    """Does this YAML file comprise multiple models?

    Arguments:
        yaml_config: PEtab configuration as dictionary or YAML file name
    """

    yaml_config = load_yaml(yaml_config)
    return len(yaml_config['problems']) > 1


def assert_single_condition_and_sbml_file(problem_config: Dict) -> None:
    """Check that there is only a single condition file and a single SBML
    file specified.

    Arguments:
        problem_config:
            Dictionary as defined in the YAML schema inside the `problems`
            list.
    Raises:
        NotImplementedError:
            If multiple condition or SBML files specified.
    """
    if (len(problem_config['sbml_files']) > 1
            or len(problem_config['condition_files']) > 1):
        # TODO https://github.com/ICB-DCM/PEtab/issues/188
        # TODO https://github.com/ICB-DCM/PEtab/issues/189
        raise NotImplementedError(
            'Support for multiple models or condition files is not yet '
            ' implemented.')
