import numpy as np
import pandas as pd
import cartopy.crs as ccrs
from geopy import Point
from geopy.distance import distance
from shapely.geometry import Polygon

import config


class Geobbox(object):
    def __init__(self, west, east, south, north, crs=None):
        self._west = west
        self._east = east
        self._south = south
        self._north = north
        self._as_tuple = (west, east, south, north)
        self._crs = crs or ccrs.PlateCarree()

    @property
    def west(self):
        return self._west

    @property
    def east(self):
        return self._east

    @property
    def south(self):
        return self._south

    @property
    def north(self):
        return self._north

    @property
    def crs(self):
        return self._crs

    def as_tuple(self):
        return self._as_tuple

    def __eq__(self, other):
        if self is other:
            return True
        elif not isinstance(other, Geobbox):
            return False
        return self.as_tuple() == other.as_tuple() and self._crs == other.crs

    def __hash__(self):
        coords = list(self.as_tuple())
        coords.append(self._crs)
        return hash(tuple(coords))

    def __getitem__(self, item):
        return self.as_tuple()[item]

    def __str__(self):
        return 'geobbox(west={}, east={}, south={}, north={})'.format(self.west, self.east,
                                                                      self.south, self.north)

    def top_border(self, numpts=40):
        x = np.linspace(self.west, self.east, numpts)
        y = np.full(x.shape, self.north, dtype=np.float32)
        return np.vstack([x, y]).T

    def bottom_border(self, numpts=40):
        x = np.linspace(self.west, self.east, numpts)
        y = np.full(x.shape, self.south, dtype=np.float32)
        return np.vstack([x, y]).T

    def left_border(self, numpts=40):
        y = np.linspace(self.south, self.north, numpts)
        x = np.full(y.shape, self.west, dtype=np.float32)
        return np.vstack([x, y]).T

    def right_border(self, numpts=40):
        y = np.linspace(self.south, self.north, numpts)
        x = np.full(y.shape, self.east, dtype=np.float32)
        return np.vstack([x, y]).T

    def _transform_line(self, line, to_crs):
        linex = line[:, 0]
        liney = line[:, 1]
        return to_crs.transform_points(self.crs, linex, liney)[:, 0:2]

    def bounds_transform(self, to_crs):
        if to_crs == self.crs:
            return self

        transformed_top = self._transform_line(self.top_border(), to_crs)
        transformed_bottom = self._transform_line(self.bottom_border(), to_crs)
        transformed_left = self._transform_line(self.left_border(), to_crs)
        transformed_right = self._transform_line(self.right_border(), to_crs)

        west = transformed_left[:, 0].min()
        east = transformed_right[:, 0].max()
        south = transformed_bottom[:, 1].min()
        north = transformed_top[:, 1].max()

        return Geobbox(west, east, south, north, to_crs)

    def is_outside(self, otherbbox):
        if otherbbox.crs != self.crs:
            otherbbox = otherbbox.bounds_transform(self.crs)

        return all([
            self.west <= otherbbox.west,
            self.east >= otherbbox.east,
            self.south <= otherbbox.south,
            self.north >= otherbbox.north
        ])


conus = Geobbox(-127.5, -65.5, 20.5, 51)

us_southeast = Geobbox(-98, -74, 23, 40)

us_southctrl = Geobbox(-110, -88, 24.5, 41)

us_southwest = Geobbox(-128, -103, 28.5, 42.5)

us_northwest = Geobbox(-130, -105, 39, 52)

us_northctrl = Geobbox(-110, -85.5, 38, 52)

us_northeast = Geobbox(-90, -65, 36, 52)

southern_plains = Geobbox(-107.5, -91, 27.5, 39.5)

central_plains = Geobbox(-107.5, -91, 33.5, 44)

northern_plains = Geobbox(-108.5, -90, 41, 51.5)

dixie = Geobbox(-97, -79, 28, 37.5)

midwest = Geobbox(-98, -79, 36, 50)

gulf_of_mexico = Geobbox(-100, -79, 17.5, 33)

florida = Geobbox(-90, -77.5, 23, 32.5)

carolinas = Geobbox(-86, -73, 31, 38)

northeast_megalopolis = Geobbox(-80.5, -68, 37, 44.5)

california = Geobbox(-127.5, -112, 30, 43)


def zoom(latlon, westeast, northsouth=None):
    if northsouth is None:
        northsouth = westeast
    return Geobbox(*calculate_bbox(latlon, westeast, northsouth))


def calculate_bbox(ctr, west_east, north_south):
    if len(ctr) != 2:
        raise ValueError("Center point must be a (lat, lon) pair")

    start = Point(*ctr)
    dist_westeast = distance(kilometers=west_east)
    dist_northsouth = distance(kilometers=north_south)

    lon0 = dist_westeast.destination(start, 270).longitude
    lon1 = dist_westeast.destination(start, 90).longitude
    lat0 = dist_northsouth.destination(start, 180).latitude
    lat1 = dist_northsouth.destination(start, 0).latitude

    return lon0, lon1, lat0, lat1


def chase_alley():
    bdys_df = pd.read_csv(config.get_resource('chasealley.csv'))
    # depending on the version of shapely, we might have to manually close the polygon
    bdys_df = bdys_df.append(bdys_df.loc[0])
    latlon_mat = bdys_df[['lat', 'lon']].values
    return bdys_df, Polygon(latlon_mat)