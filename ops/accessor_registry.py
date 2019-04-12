__all__ = ['get_latlon_accessor', 'set_latlon_accessor' ,'unset_latlon_accessor']

_ACCESSORS = {}

def set_latlon_accessor(latlon_accessors):
    if len(latlon_accessors) != 2:
        raise ValueError("Must provide exactly two accessors corresponding to lat and lon")
    _ACCESSORS['latlon'] = latlon_accessors


def get_latlon_accessor():
    return _ACCESSORS.get('latlon', None)


def unset_latlon_accessor():
    if 'latlon' in _ACCESSORS:
        del _ACCESSORS['latlon']