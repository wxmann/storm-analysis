from datetime import datetime
from functools import partial

import pandas as pd

from shared.workdir import bulksave

ALL_SEG_FILE = 'https://www.spc.noaa.gov/wcm/data/1950-{}_all_tornadoes.csv'
ALL_TOR_TRACK_FILE = 'https://www.spc.noaa.gov/wcm/data/1950-{}_actual_tornadoes.csv'


def load_tor_segments(force_save=False, to_tz=None):
    return _common_load(ALL_SEG_FILE, force_save, to_tz)


def load_full_tors(force_save=False, to_tz=None):
    return _common_load(ALL_TOR_TRACK_FILE, force_save, to_tz)


def _common_load(file_template, force_save, to_tz):
    this_year = datetime.now().year
    attempt_years = range(this_year - 3, this_year + 1)
    urls = [file_template.format(yr) for yr in attempt_years]

    results = bulksave(urls, 'spc', override_existing=force_save, postsave=partial(load_spc_file, to_tz=to_tz))
    successes = [result for result in results if result.success]

    if not successes:
        raise LoadSpcException

    ret = successes[-1].output
    ret.temporal.datetime_col = 'date_time'
    ret.geospatial.latlon_cols = ['slat', 'slon']
    return ret


def load_spc_file(file, to_tz=None):
    df = pd.read_csv(file, parse_dates=[['date', 'time']], index_col='om')
    if to_tz is not None:
        df = convert_spc_data_tz(df, to_tz)
    return df


def convert_spc_data_tz(df, to_tz, copy=True):
    if not isinstance(to_tz, int):
        raise ValueError("TZ conversion argument must be an integer")
    if copy:
        df = df.copy()

    tz_diffs = df.tz - to_tz
    df['date_time'] = df.date_time - pd.to_timedelta(tz_diffs, 'H')
    df['yr'] = df.date_time.dt.year
    df['mo'] = df.date_time.dt.month
    df['dy'] = df.date_time.dt.day
    df['tz'] = to_tz

    return df


class LoadSpcException(Exception):
    pass


class tzs:
    CST = 3
    GMT = 9
    EST = 4
    PST = 1
    MST = 2