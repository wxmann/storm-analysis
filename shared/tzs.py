import pytz


class TimeZone(object):
    @classmethod
    def todst(cls, inst):
        new_abbrev = inst.abbrev.replace('S', 'D')
        new_offset = inst.utc_offset + 1
        new_states = set(inst.full_states)
        if 'ARIZONA' in inst.full_states:
            new_states.remove('ARIZONA')
        new_inst = cls(new_abbrev, new_offset, new_states, True)
        return new_inst

    @classmethod
    def gmt(cls):
        return cls('GMT', 0, [])

    def __init__(self, abbrev, utc_offset, full_states, isdst=False):
        self.abbrev = abbrev
        self.utc_offset = utc_offset
        self.full_states = set(full_states)
        self.isdst = isdst

    def to_pytz(self):
        if self.utc_offset == 0:
            tzstr = 'GMT'
        else:
            connector = '+' if self.utc_offset < 0 else '-'
            tzstr = 'Etc/GMT{}{}'.format(connector, abs(self.utc_offset))
        return pytz.timezone(tzstr)

    def __repr__(self):
        return f'<tz {self.abbrev} {self.utc_offset} from GMT>'


PST = TimeZone('PST', -8, ('WASHINGTON', 'CALIFORNIA', 'NEVADA'))
PDT = TimeZone.todst(PST)

MST = TimeZone('MST', -7, ('MONTANA', 'WYOMING', 'UTAH', 'COLORADO', 'ARIZONA', 'NEW MEXICO'))
MDT = TimeZone.todst(MST)

CST = TimeZone('CST', -6, ('OKLAHOMA', 'MINNESOTA', 'IOWA', 'WISCONSIN', 'MISSOURI', 'ARKANSAS',
                           'LOUISIANA', 'ILLINOIS', 'MISSISSIPPI', 'ALABAMA'))
CDT = TimeZone.todst(CST)

EST = TimeZone('EST', -5, ('OHIO', 'WEST VIRGINIA', 'PENNSYLVANIA', 'NEW YORK', 'VERMONT', 'NEW HAMPSHIRE',
                           'MAINE', 'MASSACHUSETTS', 'RHODE ISLAND', 'CONNECTICUT', 'NEW JERSEY', 'DELAWARE',
                           'MARYLAND', 'DISTRICT OF COLUMBIA', 'VIRGINIA', 'NORTH CAROLINA', 'SOUTH CAROLINA',
                           'GEORGIA'))
EDT = TimeZone.todst(EST)

# American Samoa, Guam, and PR/USVI do not observe DST
SST = TimeZone('SST', -11, ('AMERICAN SAMOA',))
AST = TimeZone('AST', -4, ('PUERTO RICO', 'VIRGIN ISLANDS'))
GST = TimeZone('GST', 10, ('GUAM',))

# Note: the lack of full states is because a part of the Aleutian Islands is in HST instead of AKST
AKST = TimeZone('AKST', -9, [])
AKDT = TimeZone.todst(AKST)

# Hawaii does not observe DST, but the Aleutian Islands do, so unfortunately, HDT exists.
HST = TimeZone('HST', -10, ('HAWAII',))
HDT = TimeZone.todst(HST)

GMT = TimeZone.gmt()

SUPPORTED_TIMEZONES = (
    PST, MST, CST, EST, HST, SST, AKST, AST,
    PDT, MDT, CDT, EDT, AKDT, GST, GMT
)

_state_tz_lookup = {}
_abbrev_tz_lookup = {}
_offset_tz_lookup = {}

for tz in SUPPORTED_TIMEZONES:
    if not tz.isdst:
        for st in tz.full_states:
            _state_tz_lookup[st] = tz

    _abbrev_tz_lookup[tz.abbrev] = tz

    if not tz.isdst:
        if tz.utc_offset <= 0:
            connector = '+'
            offset = -tz.utc_offset
        else:
            connector = '-'
            offset = tz.utc_offset
        _abbrev_tz_lookup['{}{}{}'.format('GMT', connector, offset)] = tz
        _abbrev_tz_lookup['{}{}{}'.format('UTC', connector, offset)] = tz

    # support for both +0 and -0
    _abbrev_tz_lookup['GMT-0'] = GMT
    _abbrev_tz_lookup['UTC'] = GMT

    if not tz.isdst:
        _offset_tz_lookup[tz.utc_offset] = tz


class CannotFindTimeZoneException(Exception):
    pass


__all__ = ['tz_for_state', 'to_pytz', 'tz_for_latlon']


def query_tz(abbrev=None, state=None, latlon=None):
    if abbrev is None and state is None and latlon is None:
        raise CannotFindTimeZoneException(
            'Require at least one of `abbrev`, `state`, or `latlon` parameters to find timezone')
    
    if abbrev is not None:
        abbrev = abbrev.upper().strip()
        # print(_abbrev_tz_lookup)
        if abbrev in _abbrev_tz_lookup:
            return _abbrev_tz_lookup[abbrev]
    
    if state is not None:
        state = state.upper().strip()
        if state in _state_tz_lookup:
            return _state_tz_lookup[state]

    if latlon is not None:
        lat, lon = latlon
        offset = _offset_for_latlon(lat, lon)
        if offset in _offset_tz_lookup:
            return _offset_tz_lookup[offset]
        
    raise CannotFindTimeZoneException(
        'Cannot find timezone based on query: {}'.format(
            str(dict(abbrev=abbrev, state=state, latlon=latlon))))


def _offset_for_latlon(lat, lon):
    from tzwhere import tzwhere
    tzname = tzwhere.tzwhere().tzNameAt(lat, lon)
    # tzname is DST-dependent, we want to freeze it at a constant GMT-offset
    return pytz_tostd_offset(tzname)


# def _find_tz(abbrev):
#     if abbrev is None:
#         raise UnsupportedTimeZoneException('Cannot get TZ info for `None`')
#     tz_str = abbrev.upper().strip()
#     try:
#         return _timezone_map[tz_str]
#     except KeyError:
#         raise UnsupportedTimeZoneException("Invalid tz: {} (or offset does not match tz abbrevation)".format(tz_str))


# def tz_for_state(state):
#     state = state.upper().strip()
#     try:
#         return _state_std_tz_map[state].to_pytz()
#     except KeyError:
#         raise MultipleStatesInTimeZoneException


# # try to use this sparingly, it has perf issues
# def tz_for_latlon(lat, lon):
#     from tzwhere import tzwhere
#     tzname = tzwhere.tzwhere().tzNameAt(lat, lon)

#     # tzname is DST-dependent, we want to freeze it at a constant GMT-offset
#     offset = utc_offset_no_dst(tzname)
#     if offset < 0:
#         tzname = 'Etc/GMT+{}'.format(-offset)
#     else:
#         tzname = 'Etc/GMT-{}'.format(offset)
#     return to_pytz(tzname)


# def to_pytz(tz_str):
#     if tz_str is None:
#         return _find_tz(tz_str).to_pytz()
#     try:
#         # we're good here
#         return pytz.timezone(tz_str)
#     except pytz.UnknownTimeZoneError:
#         # get it from our hard-coded list
#         return _find_tz(tz_str).to_pytz()


def pytz_tostd_offset(pytz_, as_of=None):
    from datetime import datetime, timedelta
    if isinstance(pytz_, str):
        tz_to_act = pytz.timezone(pytz_)
    else:
        tz_to_act = pytz_

    if as_of is None:
        as_of = datetime(datetime.now().year, 1, 1)
    dt = tz_to_act.utcoffset(as_of) - tz_to_act.dst(as_of)

    if dt < timedelta(0):
        return -24 + dt.seconds // 3600
    return dt.seconds // 3600