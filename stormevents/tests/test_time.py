from unittest import mock

import pytz

from stormevents.io import load_file
from stormevents.time import convert_df_tz
from testing.helpers import resource_path, assert_frame_eq_ignoring_dtypes


@mock.patch('shared._timezones.tz_for_latlon')
def test_convert_df_timezone(latlontz):
    def handle_latlon_tz(lat, lon):
        if lat is None or lon is None:
            return None
        return pytz.timezone('Etc/GMT+5')

    latlontz.side_effect = handle_latlon_tz
    src_df = load_file(resource_path('stormevents_mixed_tzs.csv'))
    src_df = src_df[['begin_yearmonth', 'begin_day', 'begin_time', 'end_yearmonth',
                     'end_day', 'end_time', 'state', 'year', 'month_name', 'event_type',
                     'cz_name', 'cz_timezone', 'begin_date_time', 'end_date_time',
                     'begin_lat', 'begin_lon', 'episode_narrative', 'event_narrative']]

    expected_df = load_file(resource_path('stormevents_mixed_tzs_togmt.csv'), tz_localize=True)
    converted_src_df = convert_df_tz(src_df, 'GMT')
    assert_frame_eq_ignoring_dtypes(converted_src_df, expected_df)


@mock.patch('shared._timezones.tz_for_latlon')
def test_convert_df_timezone_multiple_times(latlontz):
    def handle_latlon_tz(lat, lon):
        if lat is None or lon is None:
            return None
        return pytz.timezone('Etc/GMT+5')

    latlontz.side_effect = handle_latlon_tz
    src_df = load_file(resource_path('stormevents_mixed_tzs.csv'))
    src_df = src_df[['begin_yearmonth', 'begin_day', 'begin_time', 'end_yearmonth',
                     'end_day', 'end_time', 'state', 'year', 'month_name', 'event_type',
                     'cz_name', 'cz_timezone', 'begin_date_time', 'end_date_time',
                     'begin_lat', 'begin_lon', 'episode_narrative', 'event_narrative']]

    expected_df = load_file(resource_path('stormevents_mixed_tzs_togmt.csv'), tz_localize=True)
    intermed = convert_df_tz(src_df, 'CST')
    converted_src_df = convert_df_tz(intermed, 'GMT')
    assert_frame_eq_ignoring_dtypes(converted_src_df, expected_df)