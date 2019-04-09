import pytest
import tempfile
import pandas as pd
import sys
import os
import libsbml
import numpy as np
import pickle

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


def test_split_parameter_replacement_list():
    assert petab.split_parameter_replacement_list('') == []
    assert petab.split_parameter_replacement_list('param1') == ['param1']
    assert petab.split_parameter_replacement_list('param1;param2') \
        == ['param1', 'param2']
    assert petab.split_parameter_replacement_list('1.0') == [1.0]
    assert petab.split_parameter_replacement_list('1.0;2.0') == [1.0, 2.0]
    assert petab.split_parameter_replacement_list('param1;2.2') == \
        ['param1', 2.2]
    assert petab.split_parameter_replacement_list(np.nan) == []
    assert petab.split_parameter_replacement_list(1.5) == [1.5]


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


def test_petab_problem(petab_problem):
    """
    Basic tests on petab problem.
    """
    assert petab_problem.get_constant_parameters() == ['fixedParameter1']


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
    assert len(problem_recreated.sbml_model.getListOfParameters()) == \
        len(petab_problem.sbml_model.getListOfParameters())


class TestGetSimulationToOptimizationParameterMapping(object):

    def test_no_condition_specific(self, condition_df_2_conditions):
        # Trivial case - no condition-specific parameters

        condition_df = condition_df_2_conditions

        measurement_df = pd.DataFrame(data={
            'observableId': ['obs1', 'obs2'],
            'simulationConditionId': ['condition1', 'condition2'],
            'preequilibrationConditionId': ['', ''],
            'observableParameters': ['', ''],
            'noiseParameters': ['', '']
        })

        expected = [['dynamicParameter1',
                     'dynamicParameter2',
                     'dynamicParameter3'],
                    ['dynamicParameter1',
                     'dynamicParameter2',
                     'dynamicParameter3']]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            par_sim_ids=['dynamicParameter1',
                         'dynamicParameter2',
                         'dynamicParameter3']
        )

        assert actual == expected

    def test_all_override(self, condition_df_2_conditions):
        # Condition-specific parameters overriding original parameters
        condition_df = condition_df_2_conditions

        measurement_df = pd.DataFrame(data={
            'observableId': ['obs1', 'obs2', 'obs1', 'obs2'],
            'simulationConditionId': ['condition1', 'condition1',
                                      'condition2', 'condition2'],
            'preequilibrationConditionId': ['', '', '', ''],
            'observableParameters': ['obs1par1override;obs1par2cond1override',
                                     'obs2par1cond1override',
                                     'obs1par1override;obs1par2cond2override',
                                     'obs2par1cond2override'],
            'noiseParameters': ['', '', '', '']
        })

        expected = [['dynamicParameter1',
                     'dynamicParameter2',
                     'obs1par1override',
                     'obs1par2cond1override',
                     'obs2par1cond1override',
                     ],
                    ['dynamicParameter1',
                     'dynamicParameter2',
                     'obs1par1override',
                     'obs1par2cond2override',
                     'obs2par1cond2override'
                     ]]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            par_sim_ids=['dynamicParameter1',
                         'dynamicParameter2',
                         'observableParameter1_obs1',
                         'observableParameter2_obs1',
                         'observableParameter1_obs2']
        )

        assert actual == expected

    def test_partial_override(self, condition_df_2_conditions):
        # Condition-specific parameters, keeping original parameters
        condition_df = condition_df_2_conditions

        measurement_df = pd.DataFrame(data={
            'observableId': ['obs1', 'obs2', 'obs1', 'obs2'],
            'simulationConditionId': ['condition1', 'condition1',
                                      'condition2', 'condition2'],
            'preequilibrationConditionId': ['', '', '', ''],
            'observableParameters': ['obs1par1override;obs1par2cond1override',
                                     '',
                                     'obs1par1override;obs1par2cond2override',
                                     'obs2par1cond2override'],
            'noiseParameters': ['', '', '', '']
        })

        expected = [['dynamicParameter1',
                     'dynamicParameter2',
                     'obs1par1override',
                     'obs1par2cond1override',
                     np.nan,
                     ],
                    ['dynamicParameter1',
                     'dynamicParameter2',
                     'obs1par1override',
                     'obs1par2cond2override',
                     'obs2par1cond2override'
                     ]]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            par_sim_ids=['dynamicParameter1',
                         'dynamicParameter2',
                         'observableParameter1_obs1',
                         'observableParameter2_obs1',
                         'observableParameter1_obs2']
        )

        assert actual == expected

    def test_parameterized_condition_table(self, minimal_sbml_model):
        condition_df = pd.DataFrame(data={
            'conditionId': ['condition1', 'condition2', 'condition3'],
            'conditionName': ['', 'Condition 2', ''],
            'dynamicParameter1': ['dynamicOverride1_1',
                                  'dynamicOverride1_2', 0]
        })
        condition_df.set_index('conditionId', inplace=True)

        measurement_df = pd.DataFrame(data={
            'simulationConditionId': ['condition1', 'condition2',
                                      'condition3'],
            'observableId': ['obs1', 'obs2', 'obs1'],
            'observableParameters': '',
            'noiseParameters': '',
        })

        parameter_df = pd.DataFrame(data={
            'parameterId': ['dynamicOverride1_1', 'dynamicOverride1_2'],
            'parameterName': ['', '...'],  # ...
        })
        parameter_df.set_index('parameterId', inplace=True)

        document, model = minimal_sbml_model
        model.createParameter().setId('dynamicParameter1')

        assert petab.get_model_parameters(model) == ['dynamicParameter1']

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            parameter_df=parameter_df,
            sbml_model=model
        )

        expected = [['dynamicOverride1_1'],
                    ['dynamicOverride1_2'],
                    [0]]

        assert actual == expected

    def test_parameterized_condition_table_changed_scale(
            self, minimal_sbml_model):
        """Test overriding a dynamic parameter `overridee` with
        - a log10 parameter to be estimated (condition 1)
        - lin parameter not estimated (condition2)
        - log10 parameter not estimated (condition 3)
        - constant override (condition 4)"""

        document, model = minimal_sbml_model
        model.createParameter().setId('overridee')
        assert petab.get_model_parameters(model) == ['overridee']

        condition_df = pd.DataFrame(data={
            'conditionId':
                ['condition1', 'condition2', 'condition3', 'condition4'],
            'conditionName': '',
            'overridee':
                ['dynamicOverrideLog10', 'fixedOverrideLin',
                 'fixedOverrideLog10', 10.0]
        })
        condition_df.set_index('conditionId', inplace=True)

        measurement_df = pd.DataFrame(data={
            'simulationConditionId':
                ['condition1', 'condition2', 'condition3', 'condition4'],
            'observableId':
                ['obs1', 'obs2', 'obs1', 'obs2'],
            'observableParameters': '',
            'noiseParameters': '',
        })

        parameter_df = pd.DataFrame(data={
            'parameterId': ['dynamicOverrideLog10',
                            'fixedOverrideLin',
                            'fixedOverrideLog10'],
            'parameterName': '',
            'estimate': [1, 0, 0],
            'nominalValue': [np.nan, 2, -2],
            'parameterScale': ['log10', 'lin', 'log10']
        })
        parameter_df.set_index('parameterId', inplace=True)

        actual_par_map = \
            petab.get_optimization_to_simulation_parameter_mapping(
                measurement_df=measurement_df,
                condition_df=condition_df,
                parameter_df=parameter_df,
                sbml_model=model
            )

        actual_scale_map = petab.get_optimization_to_simulation_scale_mapping(
            parameter_df=parameter_df,
            mapping_par_opt_to_par_sim=actual_par_map
        )

        expected_par_map = [['dynamicOverrideLog10'],
                            [2.0],
                            # rescaled:
                            [0.01],
                            [10.0]]

        expected_scale_map = [['log10'],
                              ['lin'],
                              ['lin'],
                              ['lin']]

        assert actual_par_map == expected_par_map
        assert actual_scale_map == expected_scale_map


def test_get_observable_id():
    assert petab.get_observable_id('observable_obs1') == 'obs1'
    assert petab.get_observable_id('sigma_obs1') == 'obs1'


def test_get_placeholders():
    assert petab.get_placeholders('1.0', 'any', 'observable') == set()

    assert petab.get_placeholders(
        'observableParameter1_twoParams * '
        'observableParameter2_twoParams + otherParam',
        'twoParams', 'observable') \
        == {'observableParameter1_twoParams', 'observableParameter2_twoParams'}

    assert petab.get_placeholders(
        '3.0 * noiseParameter1_oneParam', 'oneParam', 'noise') \
        == {'noiseParameter1_oneParam'}


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
    expected = ['p0', 'p3', 'p4', 'p1', 'p2', 'p5']
    actual = parameter_df.index.values.tolist()
    assert actual == expected
    assert parameter_df.loc['p0', 'nominalValue'] == 3.0

    # test with condition parameter override:
    condition_df_2_conditions.loc['condition2', 'fixedParameter1'] \
        = 'overrider'
    expected = ['p0', 'p3', 'p4', 'p1', 'p2', 'p5', 'overrider']

    parameter_df = petab.create_parameter_df(
        model,
        condition_df_2_conditions,
        measurement_df)
    actual = parameter_df.index.values.tolist()
    assert actual == expected
    assert parameter_df.loc['p0', 'nominalValue'] == 3.0


def test_fill_in_nominal_values():
    parameter_df = pd.DataFrame(data={
        'parameterId': ['estimated', 'not_estimated'],
        'parameterName': ['', '...'],  # ...
        'nominalValue': [0.0, 2.0],
        'estimate': [1, 0]
    })
    parameter_df.set_index(['parameterId'], inplace=True)
    mapping = [[1.0, 1.0], ['estimated', 'not_estimated']]

    actual = mapping.copy()
    petab.fill_in_nominal_values(actual, parameter_df)
    expected = [[1.0, 1.0], ['estimated', 2.0]]
    assert expected == actual

    del parameter_df['estimate']
    # should not replace
    actual = mapping.copy()
    petab.fill_in_nominal_values(actual, parameter_df)
    expected = mapping.copy()
    assert expected == actual
