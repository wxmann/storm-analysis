class LatLonAccessors(object):

    def __init__(self):
        self._latlon_accessors = []

    def _latlon_accessor_check(self, accessors):
        if not accessors:
            raise ValueError("Missing or null lat lon argument")
        if len(accessors) != 2:
            raise ValueError("Must provide exactly two accessors corresponding to lat and lon")

    @property
    def latlon_accessors(self):
        return list(self._latlon_accessors)

    @latlon_accessors.setter
    def latlon_accessors(self, cols):
        self._latlon_accessor_check(cols)
        self._latlon_accessors = cols

    def _get_latlon_accessors(self, latlon_accessors):
        latlon_accessors = latlon_accessors or self._latlon_accessors
        self._latlon_accessor_check(latlon_accessors)
        return latlon_accessors