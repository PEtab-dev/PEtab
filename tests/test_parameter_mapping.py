import numpy as np
import os
import pandas as pd
import petab
from petab.sbml import add_global_parameter
from petab.parameter_mapping import _apply_parameter_table
from petab.C import *

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
            OBSERVABLE_ID: ['obs1', 'obs2'],
            SIMULATION_CONDITION_ID: ['condition1', 'condition2'],
            PREEQUILIBRATION_CONDITION_ID: ['', ''],
            OBSERVABLE_PARAMETERS: ['', ''],
            NOISE_PARAMETERS: ['', '']
        })

        _, sbml_model = minimal_sbml_model
        add_global_parameter(sbml_model, 'dynamicParameter1').setValue(1.0)
        add_global_parameter(sbml_model, 'dynamicParameter2').setValue(2.0)
        add_global_parameter(sbml_model, 'dynamicParameter3').setValue(3.0)

        # Test without parameter table
        expected = [({},
                     {'dynamicParameter1': 1.0,
                      'dynamicParameter2': 2.0,
                      'dynamicParameter3': 3.0,
                      'fixedParameter1': 1.0}),
                    ({},
                     {'dynamicParameter1': 1.0,
                      'dynamicParameter2': 2.0,
                      'dynamicParameter3': 3.0,
                      'fixedParameter1': 2.0})]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            sbml_model=sbml_model,
            measurement_df=measurement_df,
            condition_df=condition_df,
        )

        assert actual == expected

        # Test with parameter table
        parameter_df = pd.DataFrame(data={
            petab.PARAMETER_ID: ['dynamicParameter1', 'dynamicParameter2',
                                 'dynamicParameter3'],
            petab.ESTIMATE: [0, 1, 1],
            petab.NOMINAL_VALUE: [11.0, 12.0, None]
        })
        parameter_df.set_index(PARAMETER_ID, inplace=True)

        expected = [({},
                     {'dynamicParameter1': 11.0,
                      'dynamicParameter2': 'dynamicParameter2',
                      'dynamicParameter3': 'dynamicParameter3',
                      'fixedParameter1': 1.0}),
                    ({},
                     {'dynamicParameter1': 11.0,
                      'dynamicParameter2': 'dynamicParameter2',
                      'dynamicParameter3': 'dynamicParameter3',
                      'fixedParameter1': 2.0})]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            sbml_model=sbml_model,
            measurement_df=measurement_df,
            condition_df=condition_df,
            parameter_df=parameter_df
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

        measurement_df = pd.DataFrame(data={
            OBSERVABLE_ID: ['obs1', 'obs2', 'obs1', 'obs2'],
            SIMULATION_CONDITION_ID: ['condition1', 'condition1',
                                      'condition2', 'condition2'],
            PREEQUILIBRATION_CONDITION_ID: ['', '', '', ''],
            OBSERVABLE_PARAMETERS: ['obs1par1override;obs1par2cond1override',
                                    'obs2par1cond1override',
                                    'obs1par1override;obs1par2cond2override',
                                    'obs2par1cond2override'],
            NOISE_PARAMETERS: ['', '', '', '']
        })

        parameter_df = pd.DataFrame(data={
            PARAMETER_ID: [
                'dynamicParameter1', 'dynamicParameter2', 'obs1par1override',
                'obs1par2cond1override', 'obs1par2cond2override',
                'obs2par1cond1override', 'obs2par1cond2override'
            ],
            ESTIMATE: [1] * 7
        })
        parameter_df.set_index(PARAMETER_ID, inplace=True)

        expected = [({},
                     {'fixedParameter1': 1.0,
                      'dynamicParameter1': 'dynamicParameter1',
                      'dynamicParameter2': 'dynamicParameter2',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond1override',
                      'observableParameter1_obs2': 'obs2par1cond1override',
                      }),
                    ({},
                     {'fixedParameter1': 2.0,
                      'dynamicParameter1': 'dynamicParameter1',
                      'dynamicParameter2': 'dynamicParameter2',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond2override',
                      'observableParameter1_obs2': 'obs2par1cond2override'
                      })]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            sbml_model=sbml_model, parameter_df=parameter_df)

        assert actual == expected

        # For one case we test parallel execution, which must yield the same
        # result
        os.environ[petab.ENV_NUM_THREADS] = "4"
        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            sbml_model=sbml_model, parameter_df=parameter_df)
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
            OBSERVABLE_ID: ['obs1', 'obs2', 'obs1', 'obs2'],
            SIMULATION_CONDITION_ID: ['condition1', 'condition1',
                                      'condition2', 'condition2'],
            PREEQUILIBRATION_CONDITION_ID: ['', '', '', ''],
            OBSERVABLE_PARAMETERS: ['obs1par1override;obs1par2cond1override',
                                    '',
                                    'obs1par1override;obs1par2cond2override',
                                    'obs2par1cond2override'],
            NOISE_PARAMETERS: ['', '', '', '']
        })

        parameter_df = pd.DataFrame(data={
            PARAMETER_ID: [
                'dynamicParameter1', 'obs1par1override',
                'obs1par2cond1override', 'obs1par2cond2override',
                'obs2par1cond2override'],
            ESTIMATE: [1, 1, 1, 1, 1],
        })
        parameter_df.set_index(PARAMETER_ID, inplace=True)

        expected = [({},
                     {'fixedParameter1': 1.0,
                      'dynamicParameter1': 'dynamicParameter1',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond1override',
                      'observableParameter1_obs2': np.nan,
                      }),
                    ({},
                     {'fixedParameter1': 2.0,
                      'dynamicParameter1': 'dynamicParameter1',
                      'observableParameter1_obs1': 'obs1par1override',
                      'observableParameter2_obs1': 'obs1par2cond2override',
                      'observableParameter1_obs2': 'obs2par1cond2override'
                      })]

        actual = petab.get_optimization_to_simulation_parameter_mapping(
            measurement_df=measurement_df,
            condition_df=condition_df,
            sbml_model=sbml_model, parameter_df=parameter_df
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
            CONDITION_ID: ['condition1', 'condition2', 'condition3'],
            CONDITION_NAME: ['', 'Condition 2', ''],
            'dynamicParameter1': ['dynamicOverride1_1',
                                  'dynamicOverride1_2', 0]
        })
        condition_df.set_index(CONDITION_ID, inplace=True)

        measurement_df = pd.DataFrame(data={
            SIMULATION_CONDITION_ID: ['condition1', 'condition2',
                                      'condition3'],
            OBSERVABLE_ID: ['obs1', 'obs2', 'obs1'],
            OBSERVABLE_PARAMETERS: '',
            NOISE_PARAMETERS: '',
        })

        parameter_df = pd.DataFrame(data={
            PARAMETER_ID: ['dynamicOverride1_1', 'dynamicOverride1_2'],
            PARAMETER_NAME: ['', '...'],
            ESTIMATE: [1, 1]
        })
        parameter_df.set_index(PARAMETER_ID, inplace=True)

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
        p = model.createParameter()
        p.setId('overridee')
        p.setValue(2.0)
        assert petab.get_model_parameters(model) == ['overridee']
        assert petab.get_model_parameters(model, with_values=True) \
            == {'overridee': 2.0}

        condition_df = pd.DataFrame(data={
            CONDITION_ID:
                ['condition1', 'condition2', 'condition3', 'condition4'],
            CONDITION_NAME: '',
            'overridee':
                ['dynamicOverrideLog10', 'fixedOverrideLin',
                 'fixedOverrideLog10', 10.0]
        })
        condition_df.set_index('conditionId', inplace=True)

        measurement_df = pd.DataFrame(data={
            SIMULATION_CONDITION_ID:
                ['condition1', 'condition2', 'condition3', 'condition4'],
            OBSERVABLE_ID:
                ['obs1', 'obs2', 'obs1', 'obs2'],
            OBSERVABLE_PARAMETERS: '',
            NOISE_PARAMETERS: '',
        })

        parameter_df = pd.DataFrame(data={
            PARAMETER_ID: ['dynamicOverrideLog10',
                           'fixedOverrideLin',
                           'fixedOverrideLog10'],
            PARAMETER_NAME: '',
            ESTIMATE: [1, 0, 0],
            NOMINAL_VALUE: [np.nan, 2, -2],
            PARAMETER_SCALE: [LOG10, LIN, LOG10]
        })
        parameter_df.set_index(PARAMETER_ID, inplace=True)

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
                            # not scaled:
                            ({}, {'overridee': -2.0}),
                            ({}, {'overridee': 10.0})]

        expected_scale_map = [({}, {'overridee': LOG10}),
                              ({}, {'overridee': LIN}),
                              ({}, {'overridee': LIN}),
                              ({}, {'overridee': LIN})]

        assert actual_par_map == expected_par_map
        assert actual_scale_map == expected_scale_map

        # Add preeq condition
        measurement_df[PREEQUILIBRATION_CONDITION_ID] = \
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
                            # not rescaled:
                            ({'overridee': -2.0}, {'overridee': -2.0}),
                            ({'overridee': -2.0}, {'overridee': 10.0})]
        expected_scale_map = [({'overridee': LOG10}, {'overridee': LOG10}),
                              ({'overridee': LOG10}, {'overridee': LIN}),
                              ({'overridee': LIN}, {'overridee': LIN}),
                              ({'overridee': LIN}, {'overridee': LIN})]
        assert actual_par_map == expected_par_map
        assert actual_scale_map == expected_scale_map


def test_fill_in_nominal_values():
    parameter_df = pd.DataFrame(data={
        PARAMETER_ID: ['estimated', 'not_estimated'],
        PARAMETER_NAME: ['', '...'],  # ...
        NOMINAL_VALUE: [0.0, 2.0],
        ESTIMATE: [1, 0]
    })
    parameter_df.set_index([PARAMETER_ID], inplace=True)

    mapping = {'estimated': 'estimated', 'not_estimated': 'not_estimated'}
    actual = mapping.copy()
    _apply_parameter_table(actual, parameter_df)
    expected = {'estimated': 'estimated', 'not_estimated': 2.0}
    assert expected == actual
