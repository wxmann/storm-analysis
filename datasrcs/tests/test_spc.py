from datasrcs.spc import load_spc_file
from shared.tzs import CST
from testing.helpers import resource_path, assert_frame_eq_ignoring_dtypes

import pandas as pd

def test_load_spc_file():
    file = resource_path('spc_mixedtzs.csv')
    df = load_spc_file(file)

    assert len(df) == 12
    for om in [245, 89, 216, 158, 17, 264, 804, 458, 271, 200, 501, 656]:
        assert om in df.index


def test_load_spc_file_and_convert_tz():
    file = resource_path('spc_mixedtzs.csv')
    df = load_spc_file(file, to_tz=CST)
    df2 = load_spc_file(file, to_tz=3)

    print(df[['date_time', 'tz']])
    print(df2[['date_time', 'tz']])

    df_expected = pd.read_csv(resource_path('spc_mixedtzs_converted.csv'), index_col='om', parse_dates=['date_time'])
    assert_frame_eq_ignoring_dtypes(df, df_expected, dt_columns=['date_time'])
    assert_frame_eq_ignoring_dtypes(df2, df_expected, dt_columns=['date_time'])