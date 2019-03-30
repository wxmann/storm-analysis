import pytest

from stormevents.io import load_file
from stormevents.time import convert_df_tz
from testing.helpers import resource_path, assert_frame_eq_ignoring_dtypes


def test_convert_df_timezone():
    src_df = load_file(resource_path('stormevents_mixed_tzs.csv'))
    src_df = src_df[['begin_yearmonth', 'begin_day', 'begin_time', 'end_yearmonth',
                     'end_day', 'end_time', 'state', 'year', 'month_name', 'event_type',
                     'cz_name', 'cz_timezone', 'begin_date_time', 'end_date_time',
                     'begin_lat', 'begin_lon', 'episode_narrative', 'event_narrative']]

    expected_df = load_file(resource_path('stormevents_mixed_tzs_togmt.csv'))
    converted_src_df = convert_df_tz(src_df, 'GMT')
    assert_frame_eq_ignoring_dtypes(converted_src_df, expected_df)


def test_error_if_tz_is_null():
    src_df = load_file(resource_path('stormevents_mixed_tzs.csv'))
    with pytest.raises(ValueError):
        convert_df_tz(src_df, None)