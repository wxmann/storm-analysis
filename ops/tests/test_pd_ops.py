from collections import namedtuple

from datetime import date
from shapely.geometry import Polygon
import pandas as pd
import numpy as np
import pytest

import ops
from testing.helpers import resource_path

expected_results = namedtuple('expected_results', ['start', 'end', 'numrecords'])

@pytest.fixture(scope='module')
def set_accessors():
    ops.set_latlon_accessor(['slat', 'slon'])
    ops.set_time_accessor('date_time')
    yield
    ops.unset_latlon_accessor()
    ops.unset_time_accessor()

def test_get_tors_in_day(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    df_day = df.temporal.getday('1999-05-03')
    assert len(df_day) == 71

    unique_days = df_day.date_time.dt.date.unique()
    assert len(unique_days) == 1
    assert unique_days[0] == date(1999, 5, 3)

def test_iterate_through_days(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    expected_data = [
        expected_results(start='1999-05-02', end='1999-05-03', numrecords=10),
        expected_results(start='1999-05-03', end='1999-05-04', numrecords=71),
        expected_results(start='1999-05-04', end='1999-05-05', numrecords=43),
        expected_results(start='1999-05-05', end='1999-05-06', numrecords=16)
    ]

    actuals = df.temporal.iter_days()
    _assert_iterated_dfs(actuals, expected_data)

def test_iterate_through_days_nonzero_hour(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    expected_data = [
        expected_results(start='1999-05-01 15:00', end='1999-05-02 15:00', numrecords=2),
        expected_results(start='1999-05-02 15:00', end='1999-05-03 15:00', numrecords=8),
        expected_results(start='1999-05-03 15:00', end='1999-05-04 15:00', numrecords=96),
        expected_results(start='1999-05-04 15:00', end='1999-05-05 15:00', numrecords=18),
        expected_results(start='1999-05-05 15:00', end='1999-05-06 15:00', numrecords=16)
    ]

    actuals = df.temporal.iter_days(hour=15)
    _assert_iterated_dfs(actuals, expected_data)

def test_iterate_through_days_start_and_end(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    expected_data = [
        expected_results(start='1999-05-03', end='1999-05-04', numrecords=71),
        expected_results(start='1999-05-04', end='1999-05-05', numrecords=43)
    ]

    actuals = df.temporal.iter_days(start='1999-05-03', end='1999-05-05')
    _assert_iterated_dfs(actuals, expected_data)

def test_iterate_through_days_start_and_end_nonzero_hour(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    expected_data = [
        expected_results(start='1999-05-03 15:00', end='1999-05-04 15:00', numrecords=96),
        expected_results(start='1999-05-04 15:00', end='1999-05-05 15:00', numrecords=18)
    ]

    actuals = df.temporal.iter_days(start='1999-05-03', end='1999-05-05', hour=15)
    _assert_iterated_dfs(actuals, expected_data)

def test_raise_if_set_invalid_column():
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    with pytest.raises(ValueError, match='Invalid column not in dataframe: invalid_col'):
        df.temporal.iter_days(datetime_col='invalid_col')

def test_skip_empty_days_if_skip_empty_true(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    expected_data = [
        expected_results(start='1999-05-05', end='1999-05-06', numrecords=16)
    ]

    actuals = df.temporal.iter_days(start='1999-05-05', end='1999-05-10')
    _assert_iterated_dfs(actuals, expected_data)

def test_not_skip_empty_days_if_skip_empty_false(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    expected_data = [
        expected_results(start='1999-05-05', end='1999-05-06', numrecords=16),
        expected_results(start='1999-05-06', end='1999-05-07', numrecords=0)
    ]

    actuals = df.temporal.iter_days(start='1999-05-05', end='1999-05-07', skip_empty_days=False)
    _assert_iterated_dfs(actuals, expected_data)

def test_iterate_days_with_custom_datetime_col(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])
    df['datep1'] = df.date_time + pd.Timedelta('1 day')

    expected_data = [
        expected_results(start='1999-05-03', end='1999-05-04', numrecords=10),
        expected_results(start='1999-05-04', end='1999-05-05', numrecords=71),
        expected_results(start='1999-05-05', end='1999-05-06', numrecords=43),
        expected_results(start='1999-05-06', end='1999-05-07', numrecords=16)
    ]

    actuals = df.temporal.iter_days(datetime_col='datep1')
    _assert_iterated_dfs(actuals, expected_data, col='datep1')

def test_find_centroid(set_accessors):
    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    ctrlat, ctrlon = df.geospatial.centroid()
    assert (ctrlat, ctrlon) == (pytest.approx(36.498, 1e-3), pytest.approx(-96.2876, 1e-3))

def test_filter_region(set_accessors):
    northern_plains_latlons = np.array([[40, -105], [40, -93], [49, -93], [49, -105]])
    northern_plains = Polygon(northern_plains_latlons)

    df = pd.read_csv(resource_path('spc_may99.csv'), parse_dates=['date_time'])

    tors_northern_plains = df.geospatial.filter_region(northern_plains)
    states = tors_northern_plains.st.unique()
    days = tors_northern_plains.dy.unique()
    assert len(states) == 2
    assert 'SD' in states and 'NE' in states
    assert len(tors_northern_plains) == 19
    assert len(days) == 2
    assert 2 in days and 3 in days


def _assert_iterated_dfs(df_iters, expected_data, col='date_time'):
    df_iters = list(df_iters)
    assert len(df_iters) == len(expected_data)

    for (interv, df), expectation in zip(df_iters, expected_data):
        start = pd.Timestamp(expectation.start)
        end = pd.Timestamp(expectation.end)

        assert (interv.left, interv.right, interv.closed) == (start, end, 'left')
        assert len(df) == expectation.numrecords

        if expectation.numrecords == 0:
            assert df.empty
        else:
            in_range = df.apply(lambda r: (r[col] >= start) & (r[col] < end), axis=1)
            assert in_range.all()