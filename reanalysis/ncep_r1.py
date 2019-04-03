from functools import lru_cache

import xarray as xr
import pandas as pd


@lru_cache()
def _dataset_for(folder, file):
    url = f'https://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets/{folder}/{file}.nc'
    return xr.open_dataset(url)


def _filter_dataset_for(ds, level, datetime_):
    kw = {}
    if level:
        kw['level'] = level
    if datetime_:
        kw['time'] = datetime_
    if kw:
        return ds.sel(**kw)
    return ds


class Daily4X(object):
    def __init__(self):
        pass

    def hgt(self, year=None, level=500, datetime_=None):
        if datetime_ is not None:
            datetime_ = pd.Timestamp(datetime_)
            year = datetime_.year
        elif year is None:
            raise ValueError("Must supply year or datetime argument")

        ds = _dataset_for('ncep.reanalysis/pressure', f'hgt.{year}')
        return _filter_dataset_for(ds, level, datetime_)

    def hgt_ltm(self):
        return _dataset_for('ncep.reanalysis.derived/pressure', 'hgt.mon.1981-2010.ltm')


daily4x = Daily4X()
