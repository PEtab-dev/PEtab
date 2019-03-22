import pandas as pd
import sys
import os
sys.path.append(os.getcwd())
import visualization

def test_generate_experimentId_no_empty():
        data_actual = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3'],
                'noiseParameters': ['noise1', 'noise1', 'noise2', 'noise3'],
                'observableTransformation': ['log10', 'log10', 'log10', 'log10']}
        measurement_data = pd.DataFrame(data_actual)
        measurement_data_actual = visualization.generate_experimentId(
                measurement_data)
        data_expect = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3'],
                'noiseParameters': ['noise1', 'noise1', 'noise2', 'noise3'],
                'observableTransformation': ['log10', 'log10', 'log10', 'log10'],
                       'experimentId': ['experiment_1', 'experiment_1',
                                        'experiment_2', 'experiment_3']}
        measurement_data_expect = pd.DataFrame(data_expect)
        assert measurement_data_actual == measurement_data_expect

def test_generate_experimentId_empty():
        data_actual = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3',
                                         float('nan'), 1, 1, 2, 2],
                'noiseParameters': ['noise1', 'noise1', 'noise2', 'noise3',
                                    'noise3', 'noise4', 'noise4', 'noise4',
                                    'noise5'],
                'observableTransformation': ['log10', 'log10', 'log10',
                                             'log10', 'log10', 'log10',
                                             'log10', 'log10', 'log10']}
        measurement_data = pd.DataFrame(data_actual)
        measurement_data_actual = visualization.generate_experimentId(
                measurement_data)
        data_expect = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3',
                                         float('nan'), 1, 1, 2, 2],
                'noiseParameters': ['noise1', 'noise1', 'noise2', 'noise3',
                                    'noise3', 'noise4', 'noise4', 'noise4',
                                    'noise5'],
                'observableTransformation': ['log10', 'log10', 'log10',
                                             'log10', 'log10', 'log10',
                                             'log10', 'log10', 'log10'],
                'experimentId': ['experiment_1', 'experiment_1',
                                 'experiment_2', 'experiment_3',
                                 'experiment_4', 'experiment_5',
                                 'experiment_5', 'experiment_6',
                                 'experiment_7']}
        measurement_data_expect = pd.DataFrame(data_expect)
        assert measurement_data_actual == measurement_data_expect