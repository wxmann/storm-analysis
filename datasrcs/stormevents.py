import re
import warnings
from datetime import datetime
from functools import partial
from itertools import product

import pandas as pd
import six

from shared.req import get_links, DataRetrievalException
from shared.workdir import bulksave
from shared import tzs

__all__ = ['load_file', 'load_events', 'load_events_year', 'export',
           'load_tor_events', 'load_svr_events', 'urls_for', 'convert_df_tz', 'sync_datetime_fields']


def urls_for(years):
    return get_links('https://www1.ncdc.noaa.gov/pub/data/swdi/stormevents/csvfiles/',
                     file_filter=_year_filter(years))


def _year_filter(years):
    years = (str(yr) for yr in years)
    regex = r'StormEvents_details-ftp_v\d{1}\.\d{1}_d({YEARS})_c\d{8}'.replace(r'{YEARS}', '|'.join(years))

    def ret(link):
        return bool(re.search(regex, link))

    return ret


def _year_from_link(link):
    regex = r'StormEvents_details-ftp_v\d{1}\.\d{1}_d(\d{4})_c\d{8}'
    matches = re.search(regex, link)
    if matches:
        year = matches.group(1)
        return int(year)
    else:
        raise DataRetrievalException("Could not get year from assumed storm event "
                                     "CSV link: {}".format(link))


def load_file(file, months=None, hours=None, eventtypes=None, states=None, 
              tz=None):
    df = pd.read_csv(file,
                     parse_dates=['BEGIN_DATE_TIME', 'END_DATE_TIME'],
                     infer_datetime_format=True,
                     index_col=False,
                     converters={
                         'BEGIN_TIME': lambda t: t.zfill(4),
                         'END_TIME': lambda t: t.zfill(4)
                     },
                     dtype={'{}_{}'.format(flag, temporal_accessor): object
                            for flag, temporal_accessor
                            in product(('BEGIN', 'END'), ('YEARMONTH',))},
                     compression='infer')

    df.columns = map(str.lower, df.columns)

    if eventtypes is not None:
        df = df[df.event_type.isin(eventtypes)]
    if states is not None:
        df = df[df.state.isin([state.upper() for state in states])]
    if months is not None:
        df = df[df.month_name.isin(months)]
    if hours is not None:
        df = df[pd.to_numeric(df.begin_time.str[:2]).isin(hours)]

    if tz is not None:
        df = convert_df_tz(df, tz, False)
    return df


def load_events(start, end, eventtypes=None, states=None, months=None,
                hours=None, tz=None, debug=False):

    if isinstance(start, six.string_types):
        start = pd.Timestamp(start)
    if isinstance(end, six.string_types):
        end = pd.Timestamp(end)

    #FIXME: there is a corner case of start and end being near the turn of the year that fails.
    # We need to resolve the start and end variables to able to load both years'
    # dataframes if needed.

    if end < start:
        raise ValueError("End date must be on or after start date")
    year1 = start.year
    year2 = end.year

    links = urls_for(range(year1, year2 + 1))
    load_df_with_filter = partial(load_file, eventtypes=eventtypes, states=states, months=months,
                                  hours=hours, tz=tz)

    results = bulksave(links, postsave=load_df_with_filter)
    dfs = [result.output for result in results if result.success and result.output is not None]
    errors = [result for result in results if not result.success]

    if errors:
        err_yrs = []
        for err in errors:
            err_yrs.append(str(_year_from_link(err.url)))

            if debug:
                print(err.exceptions)
        warnings.warn('There were errors trying to load dataframes for years: {}'.format(','.join(err_yrs)))

    if dfs:
        ret = pd.concat(dfs, ignore_index=True)
        ret = ret[(ret.begin_date_time >= start) & (ret.begin_date_time < end)]
        ret.reset_index(drop=True, inplace=True)
    else:
        ret = pd.DataFrame()

    if debug:
        return results, ret
    else:
        return ret


def load_events_year(year, **kwargs):
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31, 23, 59, 59)
    return load_events(start, end, **kwargs)


def export(df, saveloc, lowercase_cols=True, **kwargs):
    if lowercase_cols:
        df.to_csv(saveloc, header=[col.upper() for col in df.columns], index=False, **kwargs)
    else:
        df.to_csv(saveloc, index=False, **kwargs)


load_tor_events = partial(load_events, eventtypes=['Tornado'])
load_svr_events = partial(load_events, eventtypes=['Tornado', 'Hail', 'Thunderstorm Wind'])


def convert_df_tz(df, to_tz='CST', copy=True):
    assert all([
        col in df.columns for col in ('state', 'cz_timezone', 'begin_date_time', 'begin_lat', 'begin_lon')
    ])
    if copy:
        df = df.copy()

    if to_tz is None:
        raise ValueError("Must specify a non-null timezone")

    to_tz = tzs.query_tz(abbrev=to_tz)
    offsets = df.apply(lambda row: _find_tz_offset(row, to_tz), axis=1)

    for col in ('begin_date_time', 'end_date_time'):
        if col in df.columns:
            df[col] = df[col] + offsets

    return sync_datetime_fields(df, to_tz.abbrev)


def _find_tz_offset(row, to_tz):
    state = row['state']
    latlon = (row['begin_lat'], row['begin_lon'])
    # In older versions of storm events, `AST` and `AKST` are both logged as `AST`.
    # We can't let our tz-conversion logic believe naively it's Atlantic Standard Time
    if row['cz_timezone'] == 'AST':
        if state == 'ALASKA':
            from_tz = tzs.query_tz(abbrev='AKST-9')
        else:
            # both Puerto Rico and Virgin Islands in AST
            from_tz = tzs.query_tz(abbrev='AST-4')
    else:
        from_tz = tzs.query_tz(abbrev=row['cz_timezone'], state=state, latlon=latlon)

    delta_offset = to_tz.utc_offset - from_tz.utc_offset
    return pd.Timedelta(hours=delta_offset)


def sync_datetime_fields(df, tz=None):
    for prefix in ('begin', 'end'):
        dt_col = '{}_date_time'.format(prefix)
        if dt_col in df.columns:
            dts = df[dt_col].dt

            yearmonth_col = '{}_yearmonth'.format(prefix)
            time_col = '{}_time'.format(prefix)
            day_col = '{}_day'.format(prefix)

            if yearmonth_col in df.columns:
                df[yearmonth_col] = dts.strftime('%Y%m')
            if time_col in df.columns:
                df[time_col] = dts.strftime('%H%M')
            if day_col in df.columns:
                df[day_col] = dts.day

            if prefix == 'begin' and 'year' in df.columns:
                df['year'] = dts.year

            if prefix == 'begin' and 'month_name' in df.columns:
                df['month_name'] = dts.strftime('%B')

    if tz is not None:
        df['cz_timezone'] = tz

    return df