import numpy as np
import os
import pandas as pd
import petab
from petab.sbml import add_global_parameter

# import fixtures
pytest_plugins = [
   "tests.test_petab",
]


class TestGetSimulationToOptimizationParameterMapping(object):

    @staticmethod
    def test_no_condition_specific(condition_df_2_conditions,
                                   minimal_sbml_model):
        # Trivial case - no condition-specific parameters

        condition_df = condition_df_2_conditions

        measurement_df = pd.DataFrame(data={
            'observableId': ['obs1', 'obs2'],
            'simulationConditionId': ['condition1', 'condition2'],
            'preequilibrationConditionId': ['', ''],
            'observableParameters': ['', ''],
            'noiseParameters': ['', '']
        })

        _, sbml_model = minimal_sbml_model
        add_global_parameter(sbml_model, 'dynamicParameter1')
        add_global_parameter(sbml_model, 'dynamicParameter2')
        add_global_parameter(sbml_model, 'dynamicParameter3')

        expected = [({},
                     {'dynamicParameter1': 'dynamicParameter1',
                      'dynamicParameter2': 'dynamicParameter2',
                      'dynamicParameter3': 'dynamicParameter3'}),
                    ({},
                     {'dynamicParameter1': 'dynamicParameter1',
                      'dynamicParameter2': 'dynamicParameter2',
                      'dynamicParameter3': 'dynamicParameter3'})]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            sbml_model=sbml_model,
            measurement_df=measurement_df,
            condition_df=condition_df,
        )

        assert actual == expected

    @staticmethod
    def test_all_override(condition_df_2_conditions,
                          minimal_sbml_model):
        # Condition-specific parameters overriding original parameters
        condition_df = condition_df_2_conditions

        _, sbml_model = minimal_sbml_model
        add_global_parameter(sbml_model, 'dynamicParameter1')
        add_global_parameter(sbml_model, 'dynamicParameter2')
        add_global_parameter(sbml_model, 'observableParameter1_obs1')
        add_global_parameter(sbml_model, 'observableParameter2_obs1')
        add_global_parameter(sbml_model, 'observableParameter1_obs2')

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

        expected = [({},
                     {'dynamicParameter1': 'dynamicParameter1',
                      'dynamicParameter2': 'dynamicParameter2',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond1override',
                      'observableParameter1_obs2': 'obs2par1cond1override',
                      }),
                    ({},
                     {'dynamicParameter1': 'dynamicParameter1',
                      'dynamicParameter2': 'dynamicParameter2',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond2override',
                      'observableParameter1_obs2': 'obs2par1cond2override'
                      })]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            sbml_model=sbml_model)

        assert actual == expected

        # For one case we test parallel execution, which must yield the same
        # result
        os.environ[petab.ENV_NUM_THREADS] = "4"
        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            sbml_model=sbml_model)
        assert actual == expected

    @staticmethod
    def test_partial_override(condition_df_2_conditions,
                              minimal_sbml_model):
        # Condition-specific parameters, keeping original parameters
        condition_df = condition_df_2_conditions

        _, sbml_model = minimal_sbml_model
        add_global_parameter(sbml_model, 'dynamicParameter1')
        add_global_parameter(sbml_model, 'observableParameter1_obs1')
        add_global_parameter(sbml_model, 'observableParameter2_obs1')
        add_global_parameter(sbml_model, 'observableParameter1_obs2')

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

        expected = [({},
                     {'dynamicParameter1': 'dynamicParameter1',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond1override',
                      'observableParameter1_obs2': np.nan,
                      }),
                    ({},
                     {'dynamicParameter1': 'dynamicParameter1',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond2override',
                      'observableParameter1_obs2': 'obs2par1cond2override'
                      })]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            sbml_model=sbml_model
        )

        # Comparison with NaN containing expected results fails after pickling!
        # Need to test first for correct NaNs, then for the rest.
        assert np.isnan(expected[0][1]['observableParameter1_obs2'])
        assert np.isnan(actual[0][1]['observableParameter1_obs2'])
        expected[0][1]['observableParameter1_obs2'] = 0.0
        actual[0][1]['observableParameter1_obs2'] = 0.0

        assert actual == expected

    @staticmethod
    def test_parameterized_condition_table(minimal_sbml_model):
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

        expected = [({}, {'dynamicParameter1': 'dynamicOverride1_1'}),
                    ({}, {'dynamicParameter1': 'dynamicOverride1_2'}),
                    ({}, {'dynamicParameter1': 0})]

        assert actual == expected

    @staticmethod
    def test_parameterized_condition_table_changed_scale(
            minimal_sbml_model):
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
            measurement_df=measurement_df,
            mapping_par_opt_to_par_sim=actual_par_map
        )

        expected_par_map = [({}, {'overridee': 'dynamicOverrideLog10'}),
                            ({}, {'overridee': 2.0}),
                            # rescaled:
                            ({}, {'overridee': 0.01}),
                            ({}, {'overridee': 10.0})]

        expected_scale_map = [({}, {'overridee': 'log10'}),
                              ({}, {'overridee': 'lin'}),
                              ({}, {'overridee': 'lin'}),
                              ({}, {'overridee': 'lin'})]

        assert actual_par_map == expected_par_map
        assert actual_scale_map == expected_scale_map

        # Add preeq condition
        measurement_df['preequilibrationConditionId'] = \
            ['condition1', 'condition1', 'condition3', 'condition3']
        actual_par_map = \
            petab.get_optimization_to_simulation_parameter_mapping(
                measurement_df=measurement_df,
                condition_df=condition_df,
                parameter_df=parameter_df,
                sbml_model=model
            )

        actual_scale_map = petab.get_optimization_to_simulation_scale_mapping(
            parameter_df=parameter_df,
            measurement_df=measurement_df,
            mapping_par_opt_to_par_sim=actual_par_map
        )

        expected_par_map = [({'overridee': 'dynamicOverrideLog10'},
                             {'overridee': 'dynamicOverrideLog10'}),
                            ({'overridee': 'dynamicOverrideLog10'},
                             {'overridee': 2.0}),
                            # rescaled:
                            ({'overridee': 0.01}, {'overridee': 0.01}),
                            ({'overridee': 0.01}, {'overridee': 10.0})]
        expected_scale_map = [({'overridee': 'log10'}, {'overridee': 'log10'}),
                              ({'overridee': 'log10'}, {'overridee': 'lin'}),
                              ({'overridee': 'lin'}, {'overridee': 'lin'}),
                              ({'overridee': 'lin'}, {'overridee': 'lin'})]
        assert actual_par_map == expected_par_map
        assert actual_scale_map == expected_scale_map


def test_fill_in_nominal_values():
    parameter_df = pd.DataFrame(data={
        'parameterId': ['estimated', 'not_estimated'],
        'parameterName': ['', '...'],  # ...
        'nominalValue': [0.0, 2.0],
        'estimate': [1, 0]
    })
    parameter_df.set_index(['parameterId'], inplace=True)

    mapping = {'estimated': 'estimated', 'not_estimated': 'not_estimated'}
    actual = mapping.copy()
    petab.fill_in_nominal_values(actual, parameter_df)
    expected = {'estimated': 'estimated', 'not_estimated': 2.0}
    assert expected == actual

    del parameter_df['estimate']
    # should not replace
    mapping = {'estimated': 1.0, 'not_estimated': 1.0}
    actual = mapping.copy()
    petab.fill_in_nominal_values(actual, parameter_df)
    expected = mapping.copy()
    assert expected == actual

    mapping = {'estimated': 'estimated', 'not_estimated': 'not_estimated'}
    actual = mapping.copy()
    petab.fill_in_nominal_values(actual, parameter_df)
    expected = mapping.copy()
    assert expected == actual
