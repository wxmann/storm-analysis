from functools import lru_cache

import xarray as xr
import pandas as pd
import numpy as np

from ops import update_accessors


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

    def _construct_year_map(self, datetimes):
        year_map = {}
        for time_ in datetimes:
            year = time_.year
            if year not in year_map:
                year_map[year] = []
            year_map[year].append(time_)
        return year_map

    @update_accessors(latlon=['lat', 'lon'])
    def hgt(self, when, level=None):
        if isinstance(when, int):
            return _dataset_for('ncep.reanalysis/pressure', f'hgt.{when}')

        year_map = self._construct_year_map(self._get_times(when))
        concat_datasets = []

        for year in year_map:
            ds = _dataset_for('ncep.reanalysis/pressure', f'hgt.{year}')
            datetimes = year_map[year]
            filtered = _filter_dataset_for(ds, level, when=datetimes)
            concat_datasets.append(filtered)

        return xr.concat(concat_datasets, dim='time')

    @update_accessors(latlon=['lat', 'lon'])
    def hgt_ltm(self, when=None, level=None):
        ds = _dataset_for('ncep.reanalysis.derived/pressure', 'hgt.4Xday.1981-2010.ltm')
        ds_lev_filtered = _filter_dataset_for(ds, level=level, when=None)

        if when is None:
            return ds_lev_filtered

        year_map = self._construct_year_map(self._get_times(when))
        concat_datasets = []

        # this is required because the ltm files are loaded with year=0, and hence loaded as cftimes
        # rather than typical np times.
        orig_times = ds_lev_filtered.time.values

        for year in year_map:
            newtimes = np.array([pd.Timestamp(year=year,
                                              month=t.month,
                                              day=t.day,
                                              hour=t.hour,
                                              minute=t.minute) for t in orig_times])
            ds_lev_filtered['time'] = newtimes
            concat_datasets.append(ds_lev_filtered.sel(time=year_map[year]))

        return xr.concat(concat_datasets, dim='time')

    @update_accessors(latlon=['lat', 'lon'])
    def hgt_anom(self, when, level=None):
        return self.hgt(when, level) - self.hgt_ltm(when, level)


daily4x = Daily4X()
