from unittest import mock
import pandas as pd
import numpy as np
import pytest

from shared import workdir
from testing.helpers import resource_path, assert_frame_eq_ignoring_dtypes, open_resource
from ..stormevents import load_events, load_file, urls_for, export, convert_df_tz


@mock.patch('shared.req.requests')
def test_urls_for(req):
    response = mock.MagicMock()
    req.get.return_value = response

    response.status_code = 200
    with open_resource('mock_ncdc_listing.html', 'r') as f:
        text = f.read()
        response.text = text

    results = urls_for([1952, 1954, 2005])
    expected_urls = ['https://www1.ncdc.noaa.gov/pub/data/swdi/stormevents/csvfiles/{}'.format(file) for file in (
        'StormEvents_details-ftp_v1.0_d1952_c20170619.csv.gz',
        'StormEvents_details-ftp_v1.0_d1954_c20160223.csv.gz'
    )]
    assert results == expected_urls


def test_filter_df_stormtype():
    df = load_file(resource_path('stormevents_mixed_tzs.csv'), eventtypes=['Tornado', 'Hail'])
    eventtypes = df[['event_type']]

    assert len(eventtypes) == 13
    assert len(eventtypes[eventtypes.event_type == 'Tornado']) == 12
    assert len(eventtypes[eventtypes.event_type == 'Hail']) == 1


def test_filter_df_state():
    df = load_file(resource_path('stormevents_mixed_tzs.csv'), states=['Hawaii', 'Colorado'])
    states = df[['state']]

    assert len(states) == 4
    assert len(states[states.state == 'HAWAII']) == 3
    assert len(states[states.state == 'COLORADO']) == 1


def test_convert_df_timezone():
    src_df = load_file(resource_path('stormevents_mixed_tzs.csv'))
    src_df = src_df[['begin_yearmonth', 'begin_day', 'begin_time', 'end_yearmonth',
                     'end_day', 'end_time', 'state', 'year', 'month_name', 'event_type',
                     'cz_name', 'cz_timezone', 'begin_date_time', 'end_date_time',
                     'begin_lat', 'begin_lon', 'episode_narrative', 'event_narrative']]

    expected_df = load_file(resource_path('stormevents_mixed_tzs_togmt.csv'))
    converted_src_df = convert_df_tz(src_df, 'GMT')
    assert_frame_eq_ignoring_dtypes(converted_src_df, expected_df)


def test_error_if_convert_to_null_tz():
    src_df = load_file(resource_path('stormevents_mixed_tzs.csv'))
    with pytest.raises(ValueError):
        convert_df_tz(src_df, None)


@mock.patch('datasrcs.stormevents.get_links', return_value=(
        'StormEvents_details-ftp_v1.0_d1990_c20170717.csv',
        'StormEvents_details-ftp_v1.0_d1991_c20170717.csv',
        'StormEvents_details-ftp_v1.0_d1992_c20170717.csv'
))
def test_load_multiple_years_storm_data_no_tz_conversion(reqpatch):
    workdir.setto(resource_path(''))
    states = list(map(str.upper, ['Texas', 'Oklahoma', 'Kansas', 'Louisiana', 'Colorado']))
    lower_bound = pd.Timestamp('1990-01-01')
    upper_bound = pd.Timestamp('1992-10-31')
    df = load_events(lower_bound, upper_bound, eventtypes=['Tornado'],
                     states=states)

    assert len(df) == 48
    assert len(df[df.year == 1990]) == 37
    assert len(df[df.year == 1991]) == 10
    assert len(df[df.year == 1992]) == 1
    
    for _, row in df.iterrows():
        assert lower_bound <= row.begin_date_time < upper_bound
        assert row.state in states
        assert row.event_type == 'Tornado'

@mock.patch('datasrcs.stormevents.get_links', return_value=(
        'StormEvents_details-ftp_v1.0_d1990_c20170717.csv',
        'StormEvents_details-ftp_v1.0_d1991_c20170717.csv',
        'StormEvents_details-ftp_v1.0_d1992_c20170717.csv'
))
def test_load_multiple_years_storm_data_localize_to_tz(getlinks):
    workdir.setto(resource_path(''))
    lower_bound = pd.Timestamp('1990-01-01')
    upper_bound = pd.Timestamp('1992-10-31')
    states = list(map(str.upper, ['Texas', 'Oklahoma', 'Kansas', 'Louisiana', 'Colorado']))

    df = load_events(lower_bound, upper_bound, eventtypes=['Tornado'],
                     states=states, tz='EST')

    df_original = load_events(lower_bound, upper_bound, eventtypes=['Tornado'],
                     states=states)

    assert len(df) == 48
    assert len(df[df.year == 1990]) == 37
    assert len(df[df.year == 1991]) == 10
    assert len(df[df.year == 1992]) == 1
    
    for _, row in df.iterrows():
        assert lower_bound <= row.begin_date_time < upper_bound
        assert row.state in states
        assert row.event_type == 'Tornado'
        assert row.cz_timezone == 'EST'

    for tz, delta in zip(('CST', 'MST'), (1, 2)):
        tz_rows = df_original.cz_timezone == tz
        converted_times = df[tz_rows].begin_date_time
        original_times = df_original[tz_rows].begin_date_time
        tds = (converted_times - original_times).unique()

        assert len(tds) == 1
        td = pd.Timedelta(tds[0])
        hours = td.total_seconds() / 3600
        assert hours == delta


@mock.patch('datasrcs.stormevents.get_links', return_value=(
        'StormEvents_details-ftp_v1.0_d1991_c20170717.csv.gz',
))
def test_load_two_days_storm_data_localize_to_tz(reqpatch):
    workdir.setto(resource_path(''))
    df = load_events('1991-04-26 12:00', '1991-04-28 12:00', eventtypes=['Tornado'], tz='UTC')

    df_expected = load_file(resource_path('two_day_stormevents_UTC_expected.csv'))
    assert_frame_eq_ignoring_dtypes(df, df_expected)