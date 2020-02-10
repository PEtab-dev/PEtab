import pickle
import tempfile
from math import nan
import copy

import libsbml
import numpy as np
import pandas as pd
import petab
import pytest
from petab.C import *


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
def petab_problem(minimal_sbml_model):
    # create test model
    document, model = minimal_sbml_model

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
        OBSERVABLE_ID: ['obs1', 'obs2'],
        OBSERVABLE_PARAMETERS: ['', 'p1;p2'],
        NOISE_PARAMETERS: ['p3;p4', 'p5']
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        measurement_file_name = fh.name
        measurement_df.to_csv(fh, sep='\t', index=False)

    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        CONDITION_NAME: ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })
    condition_df.set_index(CONDITION_ID, inplace=True)

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        condition_file_name = fh.name
        condition_df.to_csv(fh, sep='\t', index=True)

    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['dynamicParameter1', 'dynamicParameter2'],
        PARAMETER_NAME: ['', '...'],
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        parameter_file_name = fh.name
        parameter_df.to_csv(fh, sep='\t', index=False)

    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['observable_1'],
        OBSERVABLE_NAME: ['julius'],
        OBSERVABLE_FORMULA: ['observable_1'],
        NOISE_FORMULA: [1],
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        observable_file_name = fh.name
        observable_df.to_csv(fh, sep='\t', index=False)

    problem = petab.Problem.from_files(
        sbml_file=sbml_file_name,
        measurement_file=measurement_file_name,
        condition_file=condition_file_name,
        parameter_file=parameter_file_name,
        observable_files=observable_file_name)

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
            OBSERVABLE_PARAMETERS: ['', 'p1;p2'],
            NOISE_PARAMETERS: ['p3;p4', 'p5']})
    expected = ['p1', 'p2', 'p3', 'p4', 'p5']
    actual = petab.get_measurement_parameter_ids(measurement_df)
    # ordering is arbitrary
    assert set(actual) == set(expected)


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


def test_startpoint_sampling(fujita_model_scaling):
    startpoints = fujita_model_scaling.sample_parameter_startpoints(100)
    assert (np.isfinite(startpoints)).all
    assert startpoints.shape == (100, 19)
    for sp in startpoints:
        assert np.log10(31.62) <= sp[0] <= np.log10(316.23)
        assert -3 <= sp[1] <= 3


def test_create_parameter_df(minimal_sbml_model, condition_df_2_conditions):
    _, model = minimal_sbml_model
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
        OBSERVABLE_ID: ['obs1', 'obs2'],
        OBSERVABLE_PARAMETERS: ['', 'p1;p2'],
        NOISE_PARAMETERS: ['p3;p4', 'p5']
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
    assert parameter_df.loc['p0', NOMINAL_VALUE] == 3.0


def test_flatten_timepoint_specific_output_overrides():
    """Test flatten_timepoint_specific_output_overrides"""
    observable_df = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1'],
        OBSERVABLE_FORMULA: [
            'observableParameter1_obs1 + observableParameter2_obs1'],
        NOISE_FORMULA: ['noiseParameter1_obs1']
    })
    observable_df.set_index(OBSERVABLE_ID, inplace=True)

    observable_df_expected = pd.DataFrame(data={
        OBSERVABLE_ID: ['obs1_1', 'obs1_2', 'obs1_3'],
        OBSERVABLE_FORMULA: [
            'observableParameter1_obs1_1 + observableParameter2_obs1_1',
            'observableParameter1_obs1_2 + observableParameter2_obs1_2',
            'observableParameter1_obs1_3 + observableParameter2_obs1_3'],
        NOISE_FORMULA: ['noiseParameter1_obs1_1',
                        'noiseParameter1_obs1_2',
                        'noiseParameter1_obs1_3']
    })
    observable_df_expected.set_index(OBSERVABLE_ID, inplace=True)

    # Measurement table with timepoint-specific overrides
    measurement_df = pd.DataFrame(data={
        OBSERVABLE_ID:
            ['obs1', 'obs1', 'obs1', 'obs1'],
        SIMULATION_CONDITION_ID:
            ['condition1', 'condition1', 'condition1', 'condition1'],
        PREEQUILIBRATION_CONDITION_ID:
            ['', '', '', ''],
        TIME:
            [1.0, 1.0, 2.0, 2.0],
        MEASUREMENT:
            [np.nan] * 4,
        OBSERVABLE_PARAMETERS:
            ['obsParOverride1;1.0', 'obsParOverride2;1.0',
             'obsParOverride2;1.0', 'obsParOverride2;1.0'],
        NOISE_PARAMETERS:
            ['noiseParOverride1', 'noiseParOverride1',
             'noiseParOverride2', 'noiseParOverride2']
    })

    measurement_df_expected = pd.DataFrame(data={
        OBSERVABLE_ID:
            ['obs1_1', 'obs1_2', 'obs1_3', 'obs1_3'],
        SIMULATION_CONDITION_ID:
            ['condition1', 'condition1', 'condition1', 'condition1'],
        PREEQUILIBRATION_CONDITION_ID:
            ['', '', '', ''],
        TIME:
            [1.0, 1.0, 2.0, 2.0],
        MEASUREMENT:
            [np.nan] * 4,
        OBSERVABLE_PARAMETERS:
            ['obsParOverride1;1.0', 'obsParOverride2;1.0',
             'obsParOverride2;1.0', 'obsParOverride2;1.0'],
        NOISE_PARAMETERS:
            ['noiseParOverride1', 'noiseParOverride1',
             'noiseParOverride2', 'noiseParOverride2']
    })

    problem = petab.Problem(measurement_df=measurement_df,
                            observable_df=observable_df)

    assert petab.lint_problem(problem) is False

    # Ensure having timepoint-specific overrides
    assert petab.lint.measurement_table_has_timepoint_specific_mappings(
        measurement_df) is True

    petab.flatten_timepoint_specific_output_overrides(problem)

    # Timepoint-specific overrides should be gone now
    assert petab.lint.measurement_table_has_timepoint_specific_mappings(
        problem.measurement_df) is False

    assert problem.observable_df.equals(observable_df_expected) is True
    assert problem.measurement_df.equals(measurement_df_expected) is True

    assert petab.lint_problem(problem) is False


def test_concat_measurements():
    a = pd.DataFrame({MEASUREMENT: [1.0]})
    b = pd.DataFrame({TIME: [1.0]})

    with tempfile.NamedTemporaryFile(mode='w', delete=True) as fh:
        filename_a = fh.name
        a.to_csv(fh, sep='\t', index=False)

        # finish writing
        fh.flush()

        expected = pd.DataFrame({
            MEASUREMENT: [1.0, nan],
            TIME: [nan, 1.0]
        })

        assert expected.equals(
            petab.concat_tables([a, b],
                                petab.measurements.get_measurement_df))

        assert expected.equals(
            petab.concat_tables([filename_a, b],
                                petab.measurements.get_measurement_df))


def test_get_obervable_ids(petab_problem):  # pylint: disable=W0621
    """Test if observable ids functions returns correct value."""
    assert set(petab_problem.get_observable_ids()) == set(['observable_1'])


def test_parameter_properties(petab_problem):  # pylint: disable=W0621
    """
    Test the petab.Problem functions to get parameter values.
    """
    petab_problem = copy.deepcopy(petab_problem)
    petab_problem.parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['par1', 'par2', 'par3'],
        LOWER_BOUND: [0, 0.1, 0.1],
        UPPER_BOUND: [100, 100, 200],
        PARAMETER_SCALE: ['lin', 'log', 'log10'],
        NOMINAL_VALUE: [7, 8, 9],
        ESTIMATE: [1, 1, 0],
    }).set_index(PARAMETER_ID)
    assert petab_problem.x_ids == ['par1', 'par2', 'par3']
    assert petab_problem.x_free_ids == ['par1', 'par2']
    assert petab_problem.x_fixed_ids == ['par3']
    assert petab_problem.lb == [0, 0.1, 0.1]
    assert petab_problem.lb_scaled == [0, np.log(0.1), np.log10(0.1)]
    assert petab_problem.get_lb(fixed=False, scaled=True) == [0, np.log(0.1)]
    assert petab_problem.ub == [100, 100, 200]
    assert petab_problem.ub_scaled == [100, np.log(100), np.log10(200)]
    assert petab_problem.get_ub(fixed=False, scaled=True) == [100, np.log(100)]
    assert petab_problem.x_nominal == [7, 8, 9]
    assert petab_problem.x_nominal_scaled == [7, np.log(8), np.log10(9)]
    assert petab_problem.x_nominal_free == [7, 8]
    assert petab_problem.x_nominal_fixed == [9]
    assert petab_problem.x_nominal_free_scaled == [7, np.log(8)]
    assert petab_problem.x_nominal_fixed_scaled == [np.log10(9)]


def test_to_float_if_float():
    to_float_if_float = petab.core.to_float_if_float

    assert to_float_if_float(1) == 1.0
    assert to_float_if_float("1") == 1.0
    assert to_float_if_float("-1.0") == -1.0
    assert to_float_if_float("1e1") == 10.0
    assert to_float_if_float("abc") == "abc"
    assert to_float_if_float([]) == []


def test_to_files(petab_problem):  # pylint: disable=W0621
    """Test problem.to_files."""
    with tempfile.TemporaryDirectory() as folder:
        # create target files
        sbml_file = tempfile.mkstemp(dir=folder)[1]
        condition_file = tempfile.mkstemp(dir=folder)[1]
        measurement_file = tempfile.mkstemp(dir=folder)[1]
        parameter_file = tempfile.mkstemp(dir=folder)[1]
        observable_file = tempfile.mkstemp(dir=folder)[1]

        # write contents to files
        petab_problem.to_files(
            sbml_file=sbml_file,
            condition_file=condition_file,
            measurement_file=measurement_file,
            parameter_file=parameter_file,
            visualization_file=None,
            observable_file=observable_file)

        # exemplarily load some
        parameter_df = petab.get_parameter_df(parameter_file)
        same_nans = parameter_df.isna() == petab_problem.parameter_df.isna()
        assert ((parameter_df == petab_problem.parameter_df) | same_nans) \
            .all().all()
