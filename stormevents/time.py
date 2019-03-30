import pandas as pd

from shared import tzs

__all__ = ['convert_df_tz', 'sync_datetime_fields']


def convert_df_tz(df, to_tz='CST', copy=True):
    assert all([
        'state' in df.columns,
        'cz_timezone' in df.columns,
        'begin_date_time' in df.columns
    ])
    if copy:
        df = df.copy()

    if to_tz is None:
        raise ValueError("Must specify a non-null timezone")

    to_tz = tzs.query_tz(abbrev=to_tz)

    for col in ('begin_date_time', 'end_date_time'):
        if col in df.columns:
            df[col] = df.apply(lambda row: convert_row(row, col, to_tz), axis=1)

    return sync_datetime_fields(df, to_tz.abbrev)


def convert_row(row, col, to_tz):
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
    return row[col] + pd.Timedelta(hours=delta_offset)


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