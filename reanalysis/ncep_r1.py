from functools import partial

import numpy as np
import pandas as pd
import xarray as xr

BASE_URI = 'http://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets'


def dailyavg(product, query, with_shiftgrid=False):
    all_dailyavg_years = range(1948, pd.Timestamp.now().year)
    years = _coerce_to_list(query.get('year', all_dailyavg_years))

    load_func = partial(_load_ncep, folder='ncep.reanalysis.dailyavgs',
                        product=product, query=query,
                        with_shiftgrid=with_shiftgrid)
    results = []
    for yr in years:
        results.append(load_func(yr))

    print(f'Combining data from years for {product}')
    return xr.concat(results, dim='time')


def dailyavg_ltm(product, query, with_shiftgrid=False):
    product += '.day'
    year = '1981-2010.ltm'
    folder = 'ncep.reanalysis.derived'
    result = _load_ncep(year, folder, product, query, with_shiftgrid)

    years = _coerce_to_list(query.get('year', []))
    if years:
        orig_times = result.time.values
        concat_datasets = []
        for year in years:
            ds_for_year = result.copy()
            newtimes = np.array([pd.Timestamp(year=year,
                                              month=t.month,
                                              day=t.day,
                                              hour=t.hour,
                                              minute=t.minute) for t in orig_times])
            ds_for_year['time'] = newtimes
            concat_datasets.append(ds_for_year)

        print(f'Creating long-term mean timeseries of {product}')
        return xr.concat(concat_datasets, dim='time')

    return result


def _load_ncep(year, folder, product, query, with_shiftgrid):
    url = f'{BASE_URI}/{folder}/{product}.{year}.nc'
    ds = xr.open_dataset(url)
    ds = select(ds, query, with_shiftgrid=with_shiftgrid)
    # print(f'loaded for year {year}')
    return ds


def select(data, query, with_shiftgrid=False):
    kw = {}

    level_param = query.get('pressure_level', [])
    if level_param:
        kw['level'] = level_param

    months = _coerce_to_list(query.get('month', []))
    days = _coerce_to_list(query.get('day', []))
    hours = _coerce_to_list(query.get('hour', []))

    if all([not months, not days, not hours]):
        pass
    else:
        time_query = np.in1d([1], [1])
        if months:
            time_query &= np.in1d(data['time.month'], months)
        if days:
            time_query &= np.in1d(data['time.day'], days)
        if hours:
            time_query &= np.in1d(data['time.hour'], hours)

        kw['time'] = time_query

    result = data.sel(**kw)

    if with_shiftgrid:
        result = shiftgrid(result)

    area_param = query.get('area', None)
    if area_param:
        area_kw = {}
        north, west, south, east = map(float, area_param.split('/'))
        lat_query = slice(north, south)
        lon_query = slice(west, east)
        area_kw['lat'] = lat_query
        area_kw['lon'] = lon_query
        return result.sel(**area_kw)

    return result


def shiftgrid(ds, londim='lon', copy=False):
    shifted = ds.copy() if copy else ds
    londata = shifted[londim].values
    londata_shifted = np.where((londata >= -180) & (londata <= 180), londata, -360 + londata)
    shifted[londim] = londata_shifted
    shifted = shifted.sortby(londim)
    return shifted


def _coerce_to_list(val):
    if isinstance(val, (float, int, str)):
        return [val]
    return val