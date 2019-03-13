from unittest import mock

from shared import workdir
from testing.helpers import resource_path, assert_frame_eq_ignoring_dtypes, open_resource
from stormevents.io import load_events, load_file, urls_for


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
    assert len(eventtypes[eventtypes.event_type == 'Invalid']) == 0


def test_filter_df_state():
    df = load_file(resource_path('stormevents_mixed_tzs.csv'), states=['Hawaii', 'Colorado'])
    states = df[['state']]

    assert len(states) == 4
    assert len(states[states.state == 'HAWAII']) == 3
    assert len(states[states.state == 'COLORADO']) == 1
    assert len(states[states.state == 'NO']) == 0


@mock.patch('shared.req.get_links', return_value=(
        'StormEvents_details-ftp_v1.0_d1990_c20170717.csv.gz',
        'StormEvents_details-ftp_v1.0_d1991_c20170717.csv.gz',
        'StormEvents_details-ftp_v1.0_d1992_c20170717.csv.gz',
))
def test_load_multiple_years_storm_data(reqpatch):
    workdir.setto(resource_path(''))
    df = load_events('1990-01-01', '1992-10-31', eventtypes=['Tornado'],
                                 states=['Texas', 'Oklahoma', 'Kansas'])

    df_expected = load_file(resource_path('multiyear_storm_events_expected.csv'))
    assert_frame_eq_ignoring_dtypes(df, df_expected)


@mock.patch('wxdata.http.get_links', return_value=(
        'StormEvents_details-ftp_v1.0_d1990_c20170717.csv.gz',
        'StormEvents_details-ftp_v1.0_d1991_c20170717.csv.gz',
        'StormEvents_details-ftp_v1.0_d1992_c20170717.csv.gz',
))
def test_load_multiple_years_storm_data_localize_to_tz(reqpatch):
    workdir.setto(resource_path(''))
    df = stormevents.load_events('1990-01-01', '1992-10-31', eventtypes=['Tornado'],
                                 states=['Texas', 'Oklahoma', 'Kansas'], tz='EST')

    df_expected = stormevents.load_file(resource_path('multiyear_storm_events_EST_expected.csv'),
                                        tz_localize=True)
    assert_frame_eq_ignoring_dtypes(df, df_expected)