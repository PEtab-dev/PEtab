"""Code regarding the PEtab YAML config files"""

import os

from typing import Dict, Union

import jsonschema
import yaml


SCHEMA = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      "petab_schema.yaml")


def validate(data: Union[Dict, str],
             schema: Union[None, Dict, str] = None):
    """Validiate PEtab YAML file

    Arguments:
        data:
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

    if isinstance(data, str):
        with open(data) as f:
            data = yaml.load(f)

    jsonschema.validate(instance=data, schema=schema)
