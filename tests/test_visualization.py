import pandas as pd
import pytest

from petab import generate_experiment_id  # noqa: E402
from petab.visualize import (plot_data_and_simulation,
                             plot_measurements_by_observable)


@pytest.fixture
def data_file_Fujita():
    return "doc/example/example_Fujita/Fujita_measurementData.tsv"


@pytest.fixture
def condition_file_Fujita():
    return "doc/example/example_Fujita/Fujita_experimentalCondition.tsv"


@pytest.fixture
def data_file_Isensee():
    return "doc/example/example_Isensee/Isensee_measurementData.tsv"


@pytest.fixture
def condition_file_Isensee():
    return "doc/example/example_Isensee/Isensee_experimentalCondition.tsv"


@pytest.fixture
def vis_spec_file_Isensee():
    return "doc/example/example_Isensee/Isensee_visualizationSpecification.tsv"


@pytest.fixture
def simulation_file_Isensee():
    return "doc/example/example_Isensee/Isensee_simulationData.tsv"


def test_visualization_with_vis_and_sim(data_file_Isensee,
                                        condition_file_Isensee,
                                        vis_spec_file_Isensee,
                                        simulation_file_Isensee):
    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             vis_spec_file_Isensee,
                             simulation_file_Isensee)


def test_visualization_with_vis(data_file_Isensee,
                                condition_file_Isensee,
                                vis_spec_file_Isensee):
    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             vis_spec_file_Isensee)


def test_visualization_with_dataset_list(data_file_Isensee,
                                         condition_file_Isensee):
    datasets = [['JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_ctrl',
                 'JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_Fsk'],
                ['JI09_160201_Drg453-452_CycNuc__ctrl',
                 'JI09_160201_Drg453-452_CycNuc__Fsk',
                 'JI09_160201_Drg453-452_CycNuc__Sp8_Br_cAMPS_AM']]
    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             dataset_id_list=datasets)


def test_visualization_without_datasets(data_file_Fujita,
                                        condition_file_Fujita):

    sim_cond_num_list = [[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]]
    sim_cond_id_list = [['model1_data1'], ['model1_data2', 'model1_data3'],
                        ['model1_data4', 'model1_data5'], ['model1_data6']]
    observable_num_list = [[0], [1], [2], [0, 2], [1, 2]]
    observable_id_list = [['pS6_tot'], ['pEGFR_tot'], ['pAkt_tot']]

    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_cond_num_list=sim_cond_num_list)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_cond_id_list=sim_cond_id_list)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             observable_num_list=observable_num_list)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             observable_id_list=observable_id_list)


def test_simple_visualization(data_file_Fujita,
                              condition_file_Fujita):
    plot_measurements_by_observable(data_file_Fujita, condition_file_Fujita)


def test_generate_experimentId_no_empty():
    data_actual = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3'],
                   'noiseParameters': ['noise1', 'noise1', 'noise2',
                                       'noise3'],
                   'observableTransformation': ['log10', 'log10', 'log10',
                                                'log10']}
    measurement_data = pd.DataFrame(data_actual)
    measurement_data_actual = generate_experiment_id(measurement_data)
    data_expect = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3'],
                   'noiseParameters': ['noise1', 'noise1', 'noise2',
                                       'noise3'],
                   'observableTransformation': ['log10', 'log10', 'log10',
                                                'log10'],
                   'experimentId': ['experiment_1', 'experiment_1',
                                    'experiment_2', 'experiment_3']}
    measurement_data_expect = pd.DataFrame(data_expect)
    assert all(measurement_data_actual == measurement_data_expect)


def test_generate_experiment_id_empty():
    data_actual = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3',
                                            float('nan'), 1, 1, 2, 2],
                   'noiseParameters': ['noise1', 'noise1', 'noise2',
                                       'noise3', 'noise3', 'noise4',
                                       'noise4', 'noise4', 'noise5'],
                   'observableTransformation': ['log10', 'log10', 'log10',
                                                'log10', 'log10', 'log10',
                                                'log10', 'log10', 'log10']}
    measurement_data = pd.DataFrame(data_actual)
    measurement_data_actual = generate_experiment_id(measurement_data)
    data_expect = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3',
                                            float('nan'), 1, 1, 2, 2],
                   'noiseParameters': ['noise1', 'noise1', 'noise2',
                                       'noise3', 'noise3', 'noise4',
                                       'noise4', 'noise4', 'noise5'],
                   'observableTransformation': ['log10', 'log10', 'log10',
                                                'log10', 'log10', 'log10',
                                                'log10', 'log10', 'log10'],
                   'experimentId': ['experiment_1', 'experiment_1',
                                    'experiment_2', 'experiment_3',
                                    'experiment_4', 'experiment_5',
                                    'experiment_5', 'experiment_6',
                                    'experiment_7']}
    measurement_data_expect = pd.DataFrame(data_expect)
    assert all(measurement_data_actual == measurement_data_expect)
