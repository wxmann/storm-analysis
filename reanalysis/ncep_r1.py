from functools import lru_cache

import xarray as xr
import pandas as pd
import numpy as np


@lru_cache()
def _dataset_for(folder, file):
    url = f'https://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets/{folder}/{file}.nc'
    return xr.open_dataset(url)


def _filter_dataset_for(ds, level, when):
    kw = {}
    if level is not None:
        kw['level'] = level
    if when is not None:
        kw['time'] = when
    return ds.sel(**kw)


class Daily4X(object):
    def __init__(self):
        pass

    def _get_times(self, when):
        if isinstance(when, str):
            return [pd.Timestamp(when)]

        try:
            iter(when)
        except TypeError:
            times = [pd.Timestamp(when)]
        else:
            times = [pd.Timestamp(ts) for ts in when]

        return times

    def hgt(self, when, level=None):
        if isinstance(when, int):
            return _dataset_for('ncep.reanalysis/pressure', f'hgt.{when}')

        year_map = {}
        for time_ in self._get_times(when):
            year = time_.year
            if year not in year_map:
                year_map[year] = []
            year_map[year].append(time_)

        concat_datasets = []

        for year in year_map:
            ds = _dataset_for('ncep.reanalysis/pressure', f'hgt.{year}')
            datetimes = year_map[year]
            filtered = _filter_dataset_for(ds, level, when=datetimes)
            concat_datasets.append(filtered)

        return xr.concat(concat_datasets, dim='time')

    def hgt_ltm(self, when=None, level=None):
        ds = _dataset_for('ncep.reanalysis.derived/pressure', 'hgt.4Xday.1981-2010.ltm')
        ds_lev_filtered = _filter_dataset_for(ds, level=level, when=None)

        if when is None:
            return ds_lev_filtered

        concat_datasets = []

        # this is required because the ltm files are loaded with year=0, and hence loaded as cftimes
        # rather than typical np times.
        orig_times = ds_lev_filtered.time.values

        for time_ in self._get_times(when):
            # hack: reconstruct the time series for each year
            # TODO: optimize this to do it for only unique years
            newtimes = np.array([pd.Timestamp(year=time_.year,
                                              month=t.month,
                                              day=t.day,
                                              hour=t.hour,
                                              minute=t.minute) for t in orig_times])
            ds_lev_filtered['time'] = newtimes
            concat_datasets.append(ds_lev_filtered.sel(time=time_))

        return xr.concat(concat_datasets, dim='time')

        # when = pd.Timestamp(when)
        # month, day, hour = when.month, when.day, when.hour
        # dt = ds.time.dt
        # dt_query = (dt.month == month) & (dt.day == day) & (dt.hour == hour)
        # return ds_lev_filtered.sel(time=dt_query)


daily4x = Daily4X()
