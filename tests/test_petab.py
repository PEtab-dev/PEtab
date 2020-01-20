import os
import pickle
import sys
import tempfile
from math import nan

import libsbml
import numpy as np
import pandas as pd
import pytest

sys.path.append(os.getcwd())
import petab  # noqa: E402


@pytest.fixture
def condition_df_2_conditions():
    condition_df = pd.DataFrame(data={
        'conditionId': ['condition1', 'condition2'],
        'conditionName': ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })
    condition_df.set_index('conditionId', inplace=True)
    return condition_df


@pytest.fixture
def minimal_sbml_model():
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    model.setTimeUnits("second")
    model.setExtentUnits("mole")
    model.setSubstanceUnits('mole')
    return document, model


@pytest.fixture
def petab_problem():
    # create test model
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    model.setTimeUnits("second")
    model.setExtentUnits("mole")
    model.setSubstanceUnits('mole')

    p = model.createParameter()
    p.setId('fixedParameter1')
    p.setName('FixedParameter1')

    p = model.createParameter()
    p.setId('observable_1')
    p.setName('Observable 1')

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        sbml_file_name = fh.name
        fh.write(libsbml.writeSBMLToString(document))

    measurement_df = pd.DataFrame(data={
        'observableId': ['obs1', 'obs2'],
        'observableParameters': ['', 'p1;p2'],
        'noiseParameters': ['p3;p4', 'p5']
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        measurement_file_name = fh.name
        measurement_df.to_csv(fh, sep='\t', index=False)

    condition_df = pd.DataFrame(data={
        'conditionId': ['condition1', 'condition2'],
        'conditionName': ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })
    condition_df.set_index('conditionId', inplace=True)

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        condition_file_name = fh.name
        condition_df.to_csv(fh, sep='\t', index=True)

    parameter_df = pd.DataFrame(data={
        'parameterId': ['dynamicParameter1', 'dynamicParameter2'],
        'parameterName': ['', '...'],  # ...
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        parameter_file_name = fh.name
        parameter_df.to_csv(fh, sep='\t', index=False)

    problem = petab.Problem.from_files(
        sbml_file=sbml_file_name,
        measurement_file=measurement_file_name,
        condition_file=condition_file_name,
        parameter_file=parameter_file_name)

    return problem


@pytest.fixture
def fujita_model_scaling():
    path = 'doc/example/example_Fujita/'

    sbml_file = path + 'Fujita_model.xml'
    condition_file = path + 'Fujita_experimentalCondition.tsv'
    measurement_file = path + 'Fujita_measurementData.tsv'
    parameter_file = path + 'Fujita_parameters_scaling.tsv'

    return petab.Problem.from_files(sbml_file=sbml_file,
                                    condition_file=condition_file,
                                    measurement_file=measurement_file,
                                    parameter_file=parameter_file)


def test_split_parameter_replacement_list():
    assert petab.split_parameter_replacement_list('') == []
    assert petab.split_parameter_replacement_list('param1') == ['param1']
    assert petab.split_parameter_replacement_list('param1;param2') \
        == ['param1', 'param2']
    assert petab.split_parameter_replacement_list('1.0') == [1.0]
    assert petab.split_parameter_replacement_list('1.0;2.0') == [1.0, 2.0]
    assert petab.split_parameter_replacement_list('param1;2.2') \
        == ['param1', 2.2]
    assert petab.split_parameter_replacement_list(np.nan) == []
    assert petab.split_parameter_replacement_list(1.5) == [1.5]
    assert petab.split_parameter_replacement_list(None) == []


def test_get_measurement_parameter_ids():
    measurement_df = pd.DataFrame(
        data={
            'observableParameters': ['', 'p1;p2'],
            'noiseParameters': ['p3;p4', 'p5']})
    expected = ['p1', 'p2', 'p3', 'p4', 'p5']
    actual = petab.get_measurement_parameter_ids(measurement_df)
    # ordering is arbitrary
    assert set(actual) == set(expected)


def test_parameter_is_offset_parameter():
    assert petab.parameter_is_offset_parameter('a', 'a + b') is True
    assert petab.parameter_is_offset_parameter('b', 'a + b') is True
    assert petab.parameter_is_offset_parameter('b', 'a - b') is False
    assert petab.parameter_is_offset_parameter('b', 'sqrt(b)') is False
    assert petab.parameter_is_offset_parameter('b', 'a * b') is False


def test_parameter_is_scaling_parameter():
    assert petab.parameter_is_scaling_parameter('a', 'a + b') is False
    assert petab.parameter_is_scaling_parameter('a', 'a * b') is True
    assert petab.parameter_is_scaling_parameter('a', 'a * b + 1') is False
    assert petab.parameter_is_scaling_parameter('a', 'a * a') is False


def test_serialization(petab_problem):
    # serialize and back
    problem_recreated = pickle.loads(pickle.dumps(petab_problem))

    assert problem_recreated.measurement_df.equals(
        petab_problem.measurement_df)

    assert problem_recreated.parameter_df.equals(
        petab_problem.parameter_df)

    assert problem_recreated.condition_df.equals(
        petab_problem.condition_df)

    # Can't test for equality directly, testing for number of parameters
    #  should do the job here
    assert len(problem_recreated.sbml_model.getListOfParameters()) \
        == len(petab_problem.sbml_model.getListOfParameters())


def test_get_observable_id():
    assert petab.get_observable_id('observable_obs1') == 'obs1'
    assert petab.get_observable_id('sigma_obs1') == 'obs1'


def test_get_placeholders():
    assert petab.get_placeholders('1.0', 'any', 'observable') == set()

    assert petab.get_placeholders(
        'observableParameter1_twoParams * '
        'observableParameter2_twoParams + otherParam',
        'twoParams', 'observable') \
        == {'observableParameter1_twoParams',
            'observableParameter2_twoParams'}

    assert petab.get_placeholders('3.0 * noiseParameter1_oneParam',
                                  'oneParam', 'noise') \
        == {'noiseParameter1_oneParam'}


def test_startpoint_sampling(fujita_model_scaling):
    startpoints = fujita_model_scaling.sample_parameter_startpoints(100)
    assert (np.isfinite(startpoints)).all
    assert startpoints.shape == (100, 19)
    for sp in startpoints:
        assert sp[0] >= np.log10(31.62) and sp[0] <= np.log10(316.23)
        assert sp[1] >= -3 and sp[1] <= 3


def test_create_parameter_df(condition_df_2_conditions):
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    model.setTimeUnits("second")
    model.setExtentUnits("mole")
    model.setSubstanceUnits('mole')

    s = model.createSpecies()
    s.setId('x1')

    petab.sbml.add_global_parameter(
        model,
        parameter_id='fixedParameter1',
        parameter_name='FixedParameter1',
        value=2.0)

    petab.sbml.add_global_parameter(
        model,
        parameter_id='p0',
        parameter_name='Parameter 0',
        value=3.0)

    petab.sbml.add_model_output_with_sigma(
        sbml_model=model,
        observable_id='obs1',
        observable_name='Observable 1',
        observable_formula='x1')

    petab.add_model_output_with_sigma(
        sbml_model=model,
        observable_id='obs2',
        observable_name='Observable 2',
        observable_formula='2*x1')

    # Add assignment rule target which should be ignored
    petab.add_global_parameter(sbml_model=model,
                               parameter_id='assignment_target')
    petab.create_assigment_rule(sbml_model=model,
                                assignee_id='assignment_target', formula='1.0')

    measurement_df = pd.DataFrame(data={
        'observableId': ['obs1', 'obs2'],
        'observableParameters': ['', 'p1;p2'],
        'noiseParameters': ['p3;p4', 'p5']
    })

    parameter_df = petab.create_parameter_df(
        model,
        condition_df_2_conditions,
        measurement_df)

    # first model parameters, then row by row noise and sigma overrides
    expected = ['p3', 'p4', 'p1', 'p2', 'p5']
    actual = parameter_df.index.values.tolist()
    assert actual == expected

    # test with condition parameter override:
    condition_df_2_conditions.loc['condition2', 'fixedParameter1'] \
        = 'overrider'
    expected = ['p3', 'p4', 'p1', 'p2', 'p5', 'overrider']

    parameter_df = petab.create_parameter_df(
        model,
        condition_df_2_conditions,
        measurement_df)
    actual = parameter_df.index.values.tolist()
    assert actual == expected

    # test with optional parameters
    expected = ['p0', 'p3', 'p4', 'p1', 'p2', 'p5', 'overrider']

    parameter_df = petab.create_parameter_df(
        model,
        condition_df_2_conditions,
        measurement_df,
        include_optional=True)
    actual = parameter_df.index.values.tolist()
    assert actual == expected
    assert parameter_df.loc['p0', 'nominalValue'] == 3.0


def test_flatten_timepoint_specific_output_overrides(minimal_sbml_model):
    document, model = minimal_sbml_model
    petab.sbml.add_global_parameter(
        sbml_model=model, parameter_id='observableParameter1_obs1')
    petab.sbml.add_model_output_with_sigma(
        sbml_model=model, observable_id='obs1',
        observable_formula='observableParameter1_obs1')

    # Measurement table with timepoint-specific overrides
    measurement_df = pd.DataFrame(data={
        'observableId':
            ['obs1', 'obs1', 'obs1', 'obs1'],
        'simulationConditionId':
            ['condition1', 'condition1', 'condition1', 'condition1'],
        'preequilibrationConditionId':
            ['', '', '', ''],
        'time':
            [1.0, 1.0, 2.0, 2.0],
        'measurement':
            [np.nan] * 4,
        'observableParameters':
            ['obsParOverride1', 'obsParOverride2',
             'obsParOverride2', 'obsParOverride2'],
        'noiseParameters':
            ['noiseParOverride1', 'noiseParOverride1',
             'noiseParOverride2', 'noiseParOverride2']
    })

    measurement_df_expected = pd.DataFrame(data={
        'observableId':
            ['obs1_1', 'obs1_2', 'obs1_3', 'obs1_3'],
        'simulationConditionId':
            ['condition1', 'condition1', 'condition1', 'condition1'],
        'preequilibrationConditionId':
            ['', '', '', ''],
        'time':
            [1.0, 1.0, 2.0, 2.0],
        'measurement':
            [np.nan] * 4,
        'observableParameters':
            ['obsParOverride1', 'obsParOverride2',
             'obsParOverride2', 'obsParOverride2'],
        'noiseParameters':
            ['noiseParOverride1', 'noiseParOverride1',
             'noiseParOverride2', 'noiseParOverride2']
    })

    problem = petab.Problem(sbml_model=model,
                            measurement_df=measurement_df)

    assert petab.lint_problem(problem) is False

    # Ensure having timepoint-specific overrides
    assert petab.lint.measurement_table_has_timepoint_specific_mappings(
        measurement_df) is True

    petab.flatten_timepoint_specific_output_overrides(problem)

    # Timepoint-specific overrides should be gone now
    assert petab.lint.measurement_table_has_timepoint_specific_mappings(
        problem.measurement_df) is False

    assert problem.measurement_df.equals(measurement_df_expected) is True

    assert petab.lint_problem(problem) is False


def test_concat_measurements():
    a = pd.DataFrame({'measurement': [1.0]})
    b = pd.DataFrame({'time': [1.0]})

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        filename_a = fh.name
        a.to_csv(fh, sep='\t', index=False)

    expected = pd.DataFrame({
        'measurement': [1.0, nan],
        'time': [nan, 1.0]
    })

    assert expected.equals(
        petab.concat_tables([a, b],
                            petab.measurements.get_measurement_df))

    assert expected.equals(
        petab.concat_tables([filename_a, b],
                            petab.measurements.get_measurement_df))


def test_to_float_if_float():
    to_float_if_float = petab.core.to_float_if_float

    assert to_float_if_float(1) == 1.0
    assert to_float_if_float("1") == 1.0
    assert to_float_if_float("-1.0") == -1.0
    assert to_float_if_float("1e1") == 10.0
    assert to_float_if_float("abc") == "abc"
    assert to_float_if_float([]) == []
