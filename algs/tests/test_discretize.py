import pandas as pd
from algs.discretize import discretize

def test_discretize_tor():
    # input event has tz-localized timestamp
    numpts_1 = 10
    t0_1 = pd.Timestamp('2017-01-01 00:00-06:00')
    tor1 = {
        'begin_date_time': t0_1,
        'end_date_time': t0_1 + pd.Timedelta(minutes=numpts_1),
        'begin_lat': 10.00,
        'begin_lon': -100.00,
        'end_lat': 15.00,
        'end_lon': -90.00,
        'cz_timezone': 'CST',
        'event_id': 1
    }

    # input event has non tz-localized timestamp
    numpts_2 = 5
    t0_2 = pd.Timestamp('2017-01-08 00:00')
    tor2 = {
        'begin_date_time': t0_2,
        'end_date_time': t0_2 + pd.Timedelta(minutes=numpts_2),
        'begin_lat': 50.00,
        'begin_lon': -100.00,
        'end_lat': 51.00,
        'end_lon': -110.00,
        'cz_timezone': 'CST',
        'event_id': 2
    }

    # input event has only one point
    t0_3 = pd.Timestamp('2017-01-09 00:00')
    tor3 = {
        'begin_date_time': t0_3,
        'end_date_time': t0_3,
        'begin_lat': 49.00,
        'begin_lon': -105.00,
        'end_lat': 49.00,
        'end_lon': -106.00,
        'cz_timezone': 'CST',
        'event_id': 3
    }

    df = pd.DataFrame({0: tor1, 1: tor2, 2: tor3}).T

    points = discretize(df)

    assert points.shape[0] == numpts_1 + numpts_2 + 1

    assert points[points.event_id == 1].shape[0] == numpts_1
    for i in range(0, numpts_1):
        pt = points.loc[i]
        assert pt['timestamp'] == tor1['begin_date_time'] + pd.Timedelta(minutes=i)
        assert pt['lat'] == tor1['begin_lat'] + 0.5 * i
        assert pt['lon'] == tor1['begin_lon'] + 1 * i

    assert points[points.event_id == 2].shape[0] == numpts_2
    for i in range(0, numpts_2):
        pt = points.loc[numpts_1 + i]
        assert pt['timestamp'] == (tor2['begin_date_time'] + pd.Timedelta(minutes=i)).tz_localize('Etc/GMT+6')
        assert pt['lat'] == tor2['begin_lat'] + 0.2 * i
        assert pt['lon'] == tor2['begin_lon'] - 2 * i

    assert points[points.event_id == 3].shape[0] == 1
    extrapt = points.loc[numpts_1 + numpts_2]
    assert extrapt['timestamp'] == tor3['begin_date_time'].tz_localize('Etc/GMT+6')
    assert extrapt['lat'] == tor3['begin_lat']
    assert extrapt['lon'] == tor3['begin_lon']
