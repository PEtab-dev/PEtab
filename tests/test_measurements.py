"""Tests related to petab.measurements"""

import tempfile
import pandas as pd
from math import nan
import petab


def test_concat_measurements():
    a = pd.DataFrame({'measurement': [1.0]})
    b = pd.DataFrame({'time': [1.0]})

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fh:
        filename_a = fh.name
        a.to_csv(fh, sep='\t', index=False)

    expected = pd.DataFrame({
        'measurement': [1.0, nan],
        'time': [nan, 1.0]
    })

    assert expected.equals(petab.concat_measurements([a, b]))

    assert expected.equals(petab.concat_measurements([filename_a, b]))
