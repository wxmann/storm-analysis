import numpy as np
import pandas as pd

from shared.tzs import query_tz


def discretize(df, spacing_min=1):
    foreachtor = [discretize_event(tor, spacing_min) for _, tor in df.iterrows()]
    return pd.concat(foreachtor, ignore_index=True)


def discretize_event(event, spacing_min=1, endpoint=False):
    elapsed_min = (event.end_date_time - event.begin_date_time) / pd.Timedelta('1 min')
    tzstr = event.cz_timezone
    slat, slon, elat, elon = event.begin_lat, event.begin_lon, event.end_lat, event.end_lon
    numpoints = elapsed_min // spacing_min

    if numpoints == 0:
        numpoints = 1

    lat_space = np.linspace(slat, elat, numpoints, endpoint=endpoint)
    lon_space = np.linspace(slon, elon, numpoints, endpoint=endpoint)
    latlons = np.vstack([lat_space, lon_space]).T

    t0 = event.begin_date_time
    t1 = event.end_date_time

    t0 = localize_timestamp_tz(t0, tzstr)
    t1 = localize_timestamp_tz(t1, tzstr)

    time_space = np.linspace(t0.value, t1.value, numpoints, endpoint=endpoint)
    times = pd.to_datetime(time_space)

    ret = pd.DataFrame(latlons, columns=['lat', 'lon'])
    ret['event_id'] = event.event_id
    ret['timestamp'] = times.tz_localize('GMT').tz_convert(query_tz(tzstr).to_pytz())

    return ret


def localize_timestamp_tz(timestamp, tz):
    tzobj = query_tz(tz).to_pytz()
    return pd.Timestamp(timestamp, tz=tzobj)