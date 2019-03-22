import pandas as pd

data = {'observableParameters': ['obs1', 'obs1', 'obs2', 'obs3'],
        'noiseParameters': ['noise1', 'noise1', 'noise2', 'noise3'],
        'observableTransformation': ['log10', 'log10', 'log10', 'log10']}
measurement_data = pd.DataFrame(data)