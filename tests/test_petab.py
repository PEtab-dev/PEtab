import pytest
import tempfile
import pandas as pd
import sys
import os
import libsbml
import numpy as np

sys.path.append(os.getcwd())
import petab


@pytest.fixture
def condition_df_2_conditions():
    condition_df = pd.DataFrame(data={
        'conditionId': ['condition1', 'condition2'],
        'conditionName': ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })
    return condition_df


def test_split_parameter_replacement_list():
    assert petab.split_parameter_replacement_list('') == []
    assert petab.split_parameter_replacement_list('param1') == ['param1']
    assert petab.split_parameter_replacement_list('param1;param2') == ['param1', 'param2']
    assert petab.split_parameter_replacement_list('1.0') == [1.0]
    assert petab.split_parameter_replacement_list('1.0;2.0') == [1.0, 2.0]
    assert petab.split_parameter_replacement_list('param1;2.2') == ['param1', 2.2]
    assert petab.split_parameter_replacement_list(np.nan) == []
    assert petab.split_parameter_replacement_list(1.5) == [1.5]


def test_get_measurement_parameter_ids():
    measurement_df = pd.DataFrame(data={'observableParameters': ['', 'p1;p2'], 'noiseParameters': ['p3;p4', 'p5']})
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


def test_assignment_rules_to_dict():
    # Create Sbml model with one parameter and one assignment rule
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    p = model.createParameter()
    p.setId('observable_1')
    p.setName('Observable 1')
    rule = model.createAssignmentRule()
    rule.setId('assignmentRuleIdDoesntMatter')
    rule.setVariable('observable_1')
    rule.setFormula('a+b')

    expected = {
        'observable_1': {
            'name': 'Observable 1',
            'formula': 'a+b'
        }
    }

    actual = petab.assignment_rules_to_dict(model, remove=False)
    assert actual == expected
    assert model.getAssignmentRuleByVariable('observable_1') is not None
    assert len(model.getListOfParameters()) == 1

    actual = petab.assignment_rules_to_dict(model, remove=True)
    assert actual == expected
    assert model.getAssignmentRuleByVariable('observable_1') is None
    assert len(model.getListOfParameters()) == 0


def test_optimization_problem(condition_df_2_conditions):
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

    condition_df = condition_df_2_conditions

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        condition_file_name = fh.name
        condition_df.to_csv(fh, sep='\t', index=False)

    parameter_df = pd.DataFrame(data={
        'parameterId': ['dynamicParameter1', 'dynamicParameter2'],
        'parameterName': ['', '...'],  # ...
    })

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        parameter_file_name = fh.name
        parameter_df.to_csv(fh, sep='\t', index=False)

    problem = petab.Problem(sbml_file=sbml_file_name,
                            measurement_file=measurement_file_name,
                            condition_file=condition_file_name,
                            parameter_file=parameter_file_name)

    assert problem.get_constant_parameters() == ['fixedParameter1']


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
            'simulationConditionId': ['condition1', 'condition1', 'condition2', 'condition2'],
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
            'simulationConditionId': ['condition1', 'condition1', 'condition2', 'condition2'],
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
                     'observableParameter1_obs2',
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


def test_get_num_placeholders():
    assert petab.get_num_placeholders('1.0', 'any', 'observable') == 0

    assert petab.get_num_placeholders(
        'observableParameter1_twoParams * observableParameter2_twoParams + otherParam',
        'twoParams', 'observable') == 2

    assert petab.get_num_placeholders('3.0 * noiseParameter1_oneParam', 'oneParam', 'noise') == 1


def test_get_dynamic_parameters_from_sbml():
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    p = model.createParameter()
    p.setId('dynamicParameter1')
    p.setConstant(False)
    p = model.createParameter()
    p.setId('fixedParameter1')
    p.setConstant(True)

    assert petab.get_dynamic_parameters_from_sbml(model) == ['dynamicParameter1']
