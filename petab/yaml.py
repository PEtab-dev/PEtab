"""Code regarding the PEtab YAML config files"""

import os
from typing import Any, Dict, Union, Optional, List

import jsonschema
import numpy as np
import yaml
from pandas.io.common import get_handle

from .C import *  # noqa: F403

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

    # Handles both a single parameter file, and a parameter file that has been
    # split into multiple subset files.
    for parameter_subset_file in (
            list(np.array(yaml_config[PARAMETER_FILE]).flat)):
        _check_file(
            os.path.join(path_prefix, parameter_subset_file),
            parameter_subset_file
        )

    for problem_config in yaml_config[PROBLEMS]:
        for field in [SBML_FILES, CONDITION_FILES, MEASUREMENT_FILES,
                      VISUALIZATION_FILES, OBSERVABLE_FILES]:
            if field in problem_config:
                for filename in problem_config[field]:
                    _check_file(os.path.join(path_prefix, filename), field)


def load_yaml(yaml_config: Union[Dict, str]) -> Dict:
    """Load YAML

    Convenience function to allow for providing YAML inputs as filename, URL
    or as dictionary.

    Arguments:
        yaml_config:
            PEtab YAML config as filename or dict or URL.

    Returns:
        The unmodified dictionary if ``yaml_config`` was dictionary.
        Otherwise the parsed the YAML file.
    """

    # already parsed? all PEtab problem yaml files are dictionaries
    if isinstance(yaml_config, dict):
        return yaml_config

    handle = get_handle(yaml_config, mode='r').handle
    return yaml.safe_load(handle)


def is_composite_problem(yaml_config: Union[Dict, str]) -> bool:
    """Does this YAML file comprise multiple models?

    Arguments:
        yaml_config: PEtab configuration as dictionary or YAML file name
    """

    yaml_config = load_yaml(yaml_config)
    return len(yaml_config[PROBLEMS]) > 1


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
    if (len(problem_config[SBML_FILES]) > 1
            or len(problem_config[CONDITION_FILES]) > 1):
        # TODO https://github.com/ICB-DCM/PEtab/issues/188
        # TODO https://github.com/ICB-DCM/PEtab/issues/189
        raise NotImplementedError(
            'Support for multiple models or condition files is not yet '
            'implemented.')


def write_yaml(yaml_config: Dict[str, Any], filename: str) -> None:
    """Write PEtab YAML file

    Arguments:
        yaml_config: Data to write
        filename: File to create
    """

    with open(filename, 'w') as outfile:
        yaml.dump(yaml_config, outfile, default_flow_style=False,
                  sort_keys=False)


def create_problem_yaml(sbml_files: Union[str, List[str]],
                        condition_files: Union[str, List[str]],
                        measurement_files: Union[str, List[str]],
                        parameter_file: str,
                        observable_files: Union[str, List[str]],
                        yaml_file: str,
                        visualization_files: Optional[Union[str, List[str]]]
                        = None) -> None:
    """
    Create and write default YAML file for a single PEtab problem

    Arguments:
        sbml_files: Path of SBML model file or list of such
        condition_files: Path of condition file or list of such
        measurement_files: Path of measurement file or list of such
        parameter_file: Path of parameter file
        observable_files: Path of observable file or lsit of such
        yaml_file: Path to which YAML file should be written
        visualization_files: Optional Path to visualization file or list of
        such
    """
    if isinstance(sbml_files, str):
        sbml_files = [sbml_files]
    if isinstance(condition_files, str):
        condition_files = [condition_files]
    if isinstance(measurement_files, str):
        measurement_files = [measurement_files]
    if isinstance(observable_files, str):
        observable_files = [observable_files]
    if isinstance(visualization_files, str):
        visualization_files = [visualization_files]

    problem_dic = {CONDITION_FILES: condition_files,
                   MEASUREMENT_FILES: measurement_files,
                   SBML_FILES: sbml_files,
                   OBSERVABLE_FILES: observable_files}
    if visualization_files is not None:
        problem_dic.update({'visualization_files': visualization_files})
    yaml_dic = {PARAMETER_FILE: parameter_file,
                FORMAT_VERSION: 1,
                PROBLEMS: [problem_dic]}
    write_yaml(yaml_dic, yaml_file)
