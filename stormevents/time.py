import pandas as pd

from shared import tzhelp as _tzhelp

__all__ = ['convert_df_tz', 'sync_datetime_fields',
           'convert_timestamp_tz', 'localize_timestamp_tz',
           'df_tz']


def convert_df_tz(df, to_tz='CST', copy=True, localized=False):
    assert all([
        'state' in df.columns,
        'cz_timezone' in df.columns,
        'begin_date_time' in df.columns
    ])
    if copy:
        df = df.copy()

    for col in ('begin_date_time', 'end_date_time'):
        if col in df.columns:
            df[col] = df.apply(lambda row: convert_row_tz(row, col, to_tz, localized), axis=1)

    return sync_datetime_fields(df, to_tz)


def convert_row_tz(row, col, to_tz, localized=False):
    try:
        state = row['state']
        # In older versions of storm events, `AST` and `AKST` are both logged as `AST`.
        # We can't let our tz-conversion logic believe naively it's Atlantic Standard Time
        if row['cz_timezone'] == 'AST':
            if state == 'ALASKA':
                return convert_timestamp_tz(row[col], 'AKST-9', to_tz, localized)
            else:
                # both Puerto Rico and Virgin Islands in AST
                return convert_timestamp_tz(row[col], 'AST-4', to_tz, localized)

        # moving on now...
        return convert_timestamp_tz(row[col], row['cz_timezone'], to_tz)
    except CannotParseStormEventsTimezoneStr:
        try:
            state_tz = _tzhelp.tz_for_state(row.state)
            return convert_timestamp_tz(row[col], state_tz, to_tz, localized)

        except _tzhelp.MultipleStatesInTimeZoneException:
            lat, lon = row['begin_lat'], row['begin_lon']
            latlon_tz = _tzhelp.tz_for_latlon(lat, lon)
            return convert_timestamp_tz(row[col], str(latlon_tz), to_tz, localized)

    except KeyError:
        raise ValueError("Row must have `state` and `cz_timezone` column")


def convert_timestamp_tz(timestamp, from_tz, to_tz, localized=False):
    original_tz_pd = _pytz_from_str(from_tz) if isinstance(from_tz, str) else from_tz
    new_tz_pd = _pytz_from_str(to_tz) if isinstance(to_tz, str) else to_tz
    converted = pd.Timestamp(timestamp, tz=original_tz_pd).tz_convert(new_tz_pd)

    if not localized:
        return converted.tz_localize(None)
    return converted


def localize_timestamp_tz(timestamp, tz):
    return convert_timestamp_tz(timestamp, tz, tz)


def _pytz_from_str(tz_str):
    if not tz_str or tz_str in ('UTC', 'GMT'):
        import pytz
        return pytz.timezone('GMT')

    tz_str_up = tz_str.upper()
    # handle the weird cases
    if tz_str_up in ('SCT', 'CSC'):
        # found these egregious typos
        raise CannotParseStormEventsTimezoneStr("{} is probably CST but cannot determine for sure".format(tz_str))
    elif tz_str_up == 'UNK':
        raise CannotParseStormEventsTimezoneStr("UNK timezone")

    # we're safe; fallback to our usual timezone parsing logic
    return _tzhelp.to_pytz(tz_str)


class CannotParseStormEventsTimezoneStr(Exception):
    pass


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


def df_tz(df):
    all_tzs = df.cz_timezone.unique()
    if len(all_tzs) != 1:
        raise MixedTimezoneException("DataFrame has mixed timezones: {}".format(all_tzs))
    return all_tzs[0]


class MixedTimezoneException(Exception):
    pass
