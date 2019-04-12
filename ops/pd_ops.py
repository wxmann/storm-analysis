from datetime import time

import pandas as pd
from shapely.geometry import Point

import ops
from shared import calcs
from .op_shared import LatLonAware


@pd.api.extensions.register_dataframe_accessor('temporal')
class TemporalDataframe(object):
    def __init__(self, df):
        self._df = df

    def _datetime_col_check(self, col, check_column_valid=True):
        if not col:
            raise ValueError("Missing or null date argument")
        if check_column_valid:
            if col not in self._df.columns:
                raise ValueError("Invalid column not in dataframe: {}".format(col))

    def _get_datetime_col(self, datetime_col):
        datetime_col = datetime_col or ops.get_time_accessor()
        self._datetime_col_check(datetime_col)
        return datetime_col

    def getday(self, date_, datetime_col=None):
        datetime_col = self._get_datetime_col(datetime_col)
        min_time = pd.Timestamp(date_)
        max_time = min_time + pd.Timedelta('1 day')
        return self._df[(self._df[datetime_col] >= min_time) & (self._df[datetime_col] < max_time)]

    def iter_days(self, hour=0, start=None, end=None, skip_empty_days=True, datetime_col=None):
        datetime_col = self._get_datetime_col(datetime_col)
        min_time = self._df[datetime_col].min()
        max_time = self._df[datetime_col].max()
        one_day = pd.Timedelta('1 day')

        if start is None:
            if min_time.hour >= hour:
                start_time = pd.Timestamp.combine(min_time.date(), time(hour=hour))
            else:
                start_time = pd.Timestamp.combine(min_time.date() - pd.Timedelta('1 day'), time(hour=hour))
        else:
            start_time = pd.Timestamp.combine(pd.Timestamp(start), time(hour=hour))

        if end is None:
            end_time = max_time + one_day
        else:
            end_time = pd.Timestamp.combine(pd.Timestamp(end), time(hour=hour))

        intervals = pd.interval_range(start_time, end_time, freq='D', closed='left')
        return iter_intervals(self._df, datetime_col, intervals, skip_empty_buckets=skip_empty_days)


def iter_intervals(df, col, interval_index, skip_empty_buckets=True):
    for interval in interval_index:
        if interval.closed == 'left':
            entries = (df[col] >= interval.left) & (df[col] < interval.right)
        elif interval.closed == 'right':
            entries = (df[col] > interval.left) & (df[col] <= interval.right)
        elif interval.closed == 'both':
            entries = (df[col] >= interval.left) & (df[col] <= interval.right)
        else:
            entries = (df[col] > interval.left) & (df[col] < interval.right)

        df_in_interval = df[entries]
        if df_in_interval.empty and skip_empty_buckets:
            continue
        yield interval, df[entries]


@pd.api.extensions.register_dataframe_accessor('geospatial')
class GeospatialDataframe(LatLonAware):
    def __init__(self, df):
        super().__init__()
        self._df = df

    def _latlon_accessor_check(self, accessors, check_columns_valid=True):
        super(GeospatialDataframe, self)._latlon_accessor_check(accessors)

        if check_columns_valid:
            for col in accessors:
                if col not in self._df.columns:
                    raise ValueError("Invalid column not in dataframe: {}".format(col))

    def centroid(self, latlon_cols=None):
        latcol, loncol = self._get_latlon_accessors(latlon_cols)
        ctrlat, ctrlon = calcs.spherical_centroid(self._df[latcol], self._df[loncol])
        return ctrlat, ctrlon

    def filter_region(self, region_poly, latlon_cols=None):
        return self._df[
            self._df.apply(lambda r: _is_in_region(r, region_poly, self._get_latlon_accessors(latlon_cols)), axis=1)
        ]


def _is_in_region(event, region_poly, cols):
    assert len(cols) == 2
    lat_col, lon_col = cols
    pt = Point(event[lat_col], event[lon_col])
    return region_poly.contains(pt)
