import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from petab import generate_experiment_id  # noqa: E402
from visualization import plot_data_and_simulation


def test_visualization_routine():
    data_file_path = "https://raw.githubusercontent.com/LoosC/" \
                     "Benchmark-Models/" \
        "hackathon/hackathon_contributions_new_data_format/" \
        "Isensee_JCB2018/measurementData_Isensee_JCB2018.tsv"

    condition_file_path = "https://raw.githubusercontent.com/LoosC/" \
        "Benchmark-Models/hackathon/hackathon_contributions_" \
        "new_data_format/Isensee_JCB2018/" \
        "experimentalCondition_Isensee_JCB2018.tsv"

    visualization_file_path = "https://raw.githubusercontent.com/LoosC/"\
        "Benchmark-Models/visualization/hackathon_contributions"\
        "_new_data_format/Isensee_JCB2018/visualizationSpecific"\
        "ation_Isensee_JCB2018_2.tsv"
    simulation_file_path = "https://raw.githubusercontent.com/LoosC/"\
        "Benchmark-Models/visualization/hackathon_contributions"\
        "_new_data_format/Isensee_JCB2018/simulationData"\
        "_Isensee_JCB2018.tsv"
    ax = \
        plot_data_and_simulation.plot_data_and_simulation(data_file_path,
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
