import pytest
import pytz

from shared import tzhelp
from shared.tzhelp import MultipleStatesInTimeZoneException


def test_get_tz_from_state():
    with pytest.raises(MultipleStatesInTimeZoneException):
        tzhelp.tz_for_state('Oregon')
    assert tzhelp.tz_for_state('California') == pytz.timezone('Etc/GMT+8')
    assert tzhelp.tz_for_state('New York') == pytz.timezone('Etc/GMT+5')


def test_get_tz_from_latlon():
    lat, lon = 37.7, -122.4
    assert tzhelp.tz_for_latlon(lat, lon) == pytz.timezone('Etc/GMT+8')


def test_convert_to_pytz():
    abbrev = 'CST'
    assert tzhelp.to_pytz(abbrev) == pytz.timezone('Etc/GMT+6')

    abbrev = 'GMT'
    assert tzhelp.to_pytz(abbrev) == pytz.timezone('GMT')