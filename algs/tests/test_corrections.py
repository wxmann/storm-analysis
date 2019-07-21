from datasrcs import stormevents
from testing.helpers import resource_path, assert_frame_eq_ignoring_dtypes
from algs.corrections import correct_tornado_times

def test_correct_tornado_times():
    df = stormevents.load_file(resource_path('stormevents_bad_times.csv'))
    df = correct_tornado_times(df)

    df_expected = stormevents.load_file(resource_path('stormevents_bad_times_corrected.csv'))
    assert_frame_eq_ignoring_dtypes(df, df_expected)


def test_after_tz_conversion_correct_tornado_times():
    df = stormevents.load_file(resource_path('stormevents_bad_times.csv'), tz='GMT')
    df = correct_tornado_times(df)

    df_expected = stormevents.load_file(resource_path('stormevents_bad_times_GMT_corrected.csv'))
    assert_frame_eq_ignoring_dtypes(df, df_expected)