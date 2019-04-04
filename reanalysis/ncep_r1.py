from functools import lru_cache

import xarray as xr
import pandas as pd


@lru_cache()
def _dataset_for(folder, file):
    url = f'https://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets/{folder}/{file}.nc'
    return xr.open_dataset(url)


def _filter_dataset_for(ds, level, when):
    kw = {}
    if level:
        kw['level'] = level
    if when:
        kw['time'] = when
    return ds.sel(**kw)


class Daily4X(object):
    def __init__(self):
        pass

    def hgt(self, year=None, level=None, when=None):
        if when is not None:
            when = pd.Timestamp(when)
            year = when.year
        elif year is None:
            raise ValueError("Must supply year or datetime argument")

        ds = _dataset_for('ncep.reanalysis/pressure', f'hgt.{year}')
        return _filter_dataset_for(ds, level, when)

    def hgt_ltm(self, level=None, when=None):
        ds = _dataset_for('ncep.reanalysis.derived/pressure', 'hgt.4Xday.1981-2010.ltm')
        ds_lev_filtered = _filter_dataset_for(ds, level=level, when=None)

        when = pd.Timestamp(when)
        month, day, hour = when.month, when.day, when.hour
        dt = ds.time.dt
        dt_query = (dt.month == month) & (dt.day == day) & (dt.hour == hour)
        return ds_lev_filtered.sel(time=dt_query)


daily4x = Daily4X()
