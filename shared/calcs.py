import numpy as np

def spherical_centroid(lats, lons):
    lat = np.radians(lats)
    lon = np.radians(lons)

    x1 = np.cos(lat) * np.cos(lon)
    y1 = np.cos(lat) * np.sin(lon)
    z1 = np.sin(lat)

    xbar = x1.mean()
    ybar = y1.mean()
    zbar = z1.mean()

    lon_rad = np.arctan2(ybar, xbar)
    r = np.sqrt(xbar ** 2 + ybar ** 2)
    lat_rad = np.arctan2(zbar, r)

    return np.degrees(lat_rad), np.degrees(lon_rad)