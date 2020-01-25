import pandas as pd

from petab import conditions
from petab.C import *


def test_get_parametric_overrides():

    condition_df = pd.DataFrame(data={
        CONDITION_ID: ['condition1', 'condition2'],
        CONDITION_NAME: ['', 'Condition 2'],
        'fixedParameter1': [1.0, 2.0]
    })

    assert conditions.get_parametric_overrides(condition_df) == []

    condition_df.fixedParameter1 = \
        condition_df.fixedParameter1.values.astype(int)

    assert conditions.get_parametric_overrides(condition_df) == []

    condition_df.loc[0, 'fixedParameter1'] = 'parameterId'

    assert conditions.get_parametric_overrides(condition_df) == ['parameterId']
