from .accessor_registry import get_latlon_accessor

class LatLonAware(object):

    def __init__(self):
        pass

    def _latlon_accessor_check(self, accessors):
        if not accessors:
            raise ValueError("Missing or null lat lon argument")
        if len(accessors) != 2:
            raise ValueError("Must provide exactly two accessors corresponding to lat and lon")

    def _get_latlon_accessors(self, latlon_accessors):
        latlon_accessors = latlon_accessors or get_latlon_accessor()
        self._latlon_accessor_check(latlon_accessors)
        return latlon_accessors