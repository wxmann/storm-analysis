from shapely.geometry import Point


def _is_in_region(event, region_poly, cols):
    assert len(cols) == 2
    lat_col, lon_col = cols
    pt = Point(event[lat_col], event[lon_col])
    return region_poly.contains(pt)


def filter_region_generic(df, region_poly, cols):
    return df[df.apply(lambda r: _is_in_region(r, region_poly, cols), axis=1)]