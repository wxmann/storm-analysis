from functools import wraps

__all__ = ['get_latlon_accessor', 'set_latlon_accessor' ,'unset_latlon_accessor',
           'get_time_accessor', 'set_time_accessor', 'unset_time_accessor',
           'update_accessors']

_ACCESSORS = {}

def set_latlon_accessor(latlon_accessors):
    if len(latlon_accessors) != 2:
        raise ValueError("Must provide exactly two accessors corresponding to lat and lon")
    _ACCESSORS['latlon'] = latlon_accessors

def set_time_accessor(time_accessor):
    _ACCESSORS['datetime'] = time_accessor


def get_latlon_accessor():
    return _ACCESSORS.get('latlon', None)


def get_time_accessor():
    return _ACCESSORS.get('datetime', None)


def unset_latlon_accessor():
    if 'latlon' in _ACCESSORS:
        del _ACCESSORS['latlon']


def unset_time_accessor():
    if 'datetime' in _ACCESSORS:
        del _ACCESSORS['datetime']


def update_accessors(**updates):
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            ret = func(*args, **kwargs)
            _ACCESSORS.update(updates)
            return ret
        return wrapped_func
    return decorator