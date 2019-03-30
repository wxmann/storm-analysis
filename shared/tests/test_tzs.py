import pytest
import pytz

from shared import tzs


def test_get_tz_from_state():
    with pytest.raises(tzs.CannotFindTimeZoneException):
        tzs.query_tz(state='Oregon')
    assert tzs.query_tz(state='California') == tzs.PST
    assert tzs.query_tz(state='New York') == tzs.EST

def test_get_tz_from_latlon():
    latlon = (37.7, -122.4)
    assert tzs.query_tz(latlon=latlon) == tzs.PST

def test_convert_tz_to_dst():
    pst = tzs.PST
    assert pst.todst().utc_offset == tzs.PST.utc_offset + 1
    assert pst.todst().abbrev == 'PDT'

def test_get_tz_from_abbrev():
    assert tzs.query_tz(abbrev='CST') == tzs.CST
    assert tzs.query_tz(abbrev='GMT') == tzs.GMT
    assert tzs.query_tz(abbrev='UTC') == tzs.GMT
    assert tzs.query_tz(abbrev='GMT+8') == tzs.PST
    assert tzs.query_tz(abbrev='GMT-0') == tzs.GMT
    assert tzs.query_tz(abbrev='GMT+0') == tzs.GMT
    assert tzs.query_tz(abbrev='PDT') == tzs.PDT

def test_convert_to_pytz():
    assert tzs.CST.to_pytz() == pytz.timezone('Etc/GMT+6')
    assert tzs.GMT.to_pytz() == pytz.timezone('GMT')