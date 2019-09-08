import numpy as np
import pandas as pd
from geopy.distance import great_circle


def forward_motion(df, periods=1, cols=None, synoptic_times=True):
    if cols is None:
        cols = dict(
            storm_id='sid',
            timestamp='iso_time',
            lat='lat',
            lon='lon'
        )
    df = df[cols.values()]

    if synoptic_times:
        df = df[df[cols['timestamp']].dt.hour.isin([0, 6, 12, 18])]

    shifted = df.groupby(cols['storm_id']).shift(-periods)
    deltas = df.join(shifted, lsuffix='_0', rsuffix='_1')

    lat0 = np.radians(deltas.lat_0)
    lat1 = np.radians(deltas.lat_1)
    delta_lon = np.radians(deltas.lon_1 - deltas.lon_0)
    y = np.sin(delta_lon) * np.cos(lat1)
    x = np.cos(lat0) * np.sin(lat1) - (np.sin(lat0) * np.cos(lat1) * np.cos(delta_lon))
    angles = np.arctan2(y, x)
    angles = np.pi / 2 - angles  # convert bearing to angles

    def dist_nm(row):
        r_lat0, r_lon0, r_lat1, r_lon1 = row.lat_0, row.lon_0, row.lat_1, row.lon_1
        if np.any(np.isnan([r_lat0, r_lat1, r_lon0, r_lon1])):
            return np.nan

        pt0 = (r_lat0, r_lon0)
        pt1 = (r_lat1, r_lon1)
        return great_circle(pt0, pt1).nm

    dists = deltas.apply(dist_nm, axis=1)
    speeds = np.abs(dists / (periods * 6))

    return dists, speeds, angles


def stalls(df, threshold_nm, time_periods, cols=None):
    if cols is None:
        cols = dict(
            storm_id='sid',
            timestamp='iso_time',
            lat='lat',
            lon='lon'
        )
    df = df[df[cols['timestamp']].dt.hour.isin([0, 6, 12, 18])]

    queries = []
    for i in range(1, time_periods + 1):
        dists, _, _ = forward_motion(df, i, cols=cols)
        queries.append(dists <= threshold_nm)

    stall_query = pd.concat(queries, axis=1).all(axis=1)
    return df[stall_query]