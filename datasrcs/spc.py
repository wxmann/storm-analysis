from datetime import datetime

import pandas as pd

from .ops import filter_region_generic
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

    results = bulksave(urls, 'spc', override_existing=force_save, postsave=_pd_read_csv)
    successes = [result for result in results if result.success]

    if not successes:
        raise LoadSpcException
    return successes[-1].output


def _pd_read_csv(file):
    return pd.read_csv(file, parse_dates=[['date', 'time']], index_col='om')


class LoadSpcException(Exception):
    pass


@pd.api.extensions.register_dataframe_accessor('spc')
class SpcDataFrameExtension(object):
    def __init__(self, df):
        self._df = df

    def filter_region(self, region_poly, cols=('slat', 'slon')):
        return filter_region_generic(self._df, region_poly, cols)