"""Test COMBINE archive"""
import os
import tempfile

import pandas as pd

import petab
from petab.C import *

# import fixtures
pytest_plugins = [
    "tests.test_petab",
]


def test_combine_archive(minimal_sbml_model):
    """Test `create_combine_archive` and `Problem.from_combine`"""

    # Create test files
    document, sbml_model = minimal_sbml_model

    # Create tables with arbitrary content
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1', 'obs2'],
        OBSERVABLE_PARAMETERS: ['', 'p1;p2'],
        NOISE_PARAMETERS: ['p3;p4', 'p5']
    })

    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        CONDITION_NAME: ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })
    condition_df.set_index(CONDITION_ID, inplace=True)

    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['dynamicParameter1', 'dynamicParameter2'],
        PARAMETER_NAME: ['', '...'],
    })
    parameter_df.set_index(PARAMETER_ID, inplace=True)

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['observable_1'],
        OBSERVABLE_FORMULA: ['observable_1'],
        NOISE_FORMULA: [1],
    })
    observable_df.set_index(OBSERVABLE_ID, inplace=True)

    sbml_file_name = 'model.xml'
    measurement_file_name = 'measurements.tsv'
    condition_file_name = 'conditions.tsv'
    parameter_file_name = 'parameters.tsv'
    observable_file_name = 'observables.tsv'
    yaml_file_name = 'test.yaml'

    yaml_config = {
        FORMAT_VERSION: petab.__format_version__,
        PARAMETER_FILE: parameter_file_name,
        PROBLEMS: [
            {
                SBML_FILES: [sbml_file_name],
                MEASUREMENT_FILES: [measurement_file_name],
                CONDITION_FILES: [condition_file_name],
                OBSERVABLE_FILES: [observable_file_name]
            }
        ]
    }

    with tempfile.TemporaryDirectory(prefix='petab_test_combine_archive') \
            as tempdir:
        # Write test data
        petab.write_sbml(document, os.path.join(tempdir, sbml_file_name))
        petab.write_measurement_df(
            measurement_df, os.path.join(tempdir, measurement_file_name))
        petab.write_parameter_df(
            parameter_df, os.path.join(tempdir, parameter_file_name))
        petab.write_observable_df(
            observable_df, os.path.join(tempdir, observable_file_name))
        petab.write_condition_df(
            condition_df, os.path.join(tempdir, condition_file_name))
        petab.write_yaml(yaml_config, os.path.join(tempdir, yaml_file_name))

        archive_file_name = os.path.join(tempdir, 'test.omex')

        # Create COMBINE archive
        petab.create_combine_archive(os.path.join(tempdir, yaml_file_name),
                                     archive_file_name, family_name="Tester")

        # Read COMBINE archive
        problem = petab.Problem.from_combine(archive_file_name)

        assert problem.parameter_df is not None
        assert problem.condition_df is not None
        assert problem.measurement_df is not None
        assert problem.observable_df is not None
