from datetime import datetime

import pandas as pd

from shared.workdir import bulksave

ALL_SEG_FILE = 'https://www.spc.noaa.gov/wcm/data/1950-{}_all_tornadoes.csv'
ALL_TOR_TRACK_FILE = 'https://www.spc.noaa.gov/wcm/data/1950-{}_actual_tornadoes.csv'


def load_tor_segments(force_save=False):
    return _common_load(ALL_SEG_FILE, force_save)


def load_full_tors(force_save=False):
    return _common_load(ALL_TOR_TRACK_FILE, force_save)


def _common_load(file_template, force_save):
    this_year = datetime.now().year
    attempt_years = range(this_year - 3, this_year + 1)
    urls = [file_template.format(yr) for yr in attempt_years]

    results = bulksave(urls, 'spc', override_existing=force_save, postsave=load_spc_file)
    successes = [result for result in results if result.success]

    if not successes:
        raise LoadSpcException

    ret = successes[-1].output
    ret.temporal.datetime_col = 'date_time'
    ret.geospatial.latlon_cols = ['slat', 'slon']
    return ret


def load_spc_file(file):
    return pd.read_csv(file, parse_dates=[['date', 'time']], index_col='om')


class LoadSpcException(Exception):
    pass