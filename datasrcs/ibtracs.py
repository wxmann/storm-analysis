import pandas as pd
from functools import partial

from shared.workdir import savefile

_DATA_DIR = 'ftp://eclipse.ncdc.noaa.gov/pub/ibtracs/v04r00/provisional/csv'


def ibtracsv4(basin):
    url = f'{_DATA_DIR}/ibtracs.{basin}.list.v04r00.csv'
    save_to_local = savefile(url, in_subdir='ibtracs')

    df = pd.read_csv(save_to_local.dest,
                     skiprows=[1],
                     parse_dates=['ISO_TIME'],
                     na_values=' ')
    df.columns = map(str.lower, df.columns)
    return df


atlantic_tcs = partial(ibtracsv4, 'NA')

epac_tcs = partial(ibtracsv4, 'EP')

wpac_tcs = partial(ibtracsv4, 'WP')