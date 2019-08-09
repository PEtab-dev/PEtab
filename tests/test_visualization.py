import pandas as pd

from petab import generate_experiment_id  # noqa: E402
from petab.visualize import plot_data_and_simulation


def test_visualization_routine():
    data_file_path = "doc/example/example_Isensee/example_measurementData" \
                     ".tsv"
    condition_file_path = \
        "doc/example/example_Isensee/example_experimentalCondition.tsv"
    visualization_file_path = \
        "doc/example/example_Isensee/example_visualizationSpecification.tsv"
    simulation_file_path = \
        "doc/example/example_Isensee/example_simulationData.tsv"

    plot_data_and_simulation(data_file_path,
                             condition_file_path,
                             visualization_file_path,
                             simulation_file_path)


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
