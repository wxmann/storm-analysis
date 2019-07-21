import math

import cartopy
import numpy as np
import shapely.geometry as sgeom
from cartopy import crs as ccrs
from cartopy import feature as cfeat
from geopy.distance import distance
import matplotlib.pyplot as plt

import config
from .mapplots import CartopyMapPlotter
from .mapareas import Geobbox


class CartopyMap(object):
    @classmethod
    def from_axes(cls, ax, **kwargs):
        if 'ax' in kwargs:
            raise ValueError("Ax is duplicated in args and kwargs")
        if 'proj' in kwargs:
            raise ValueError("Please use the normal constructor to supply `proj` argument")
        if 'bbox' not in kwargs:
            kwargs['bbox'] = Geobbox(*ax.get_extent(), ax.projection)
        return cls(proj=ax.projection, ax=ax, **kwargs)

    def __init__(self, proj=None, scale='i', bbox=None, ax=None,
                 bg=None, borderstyle=None, countystyle=None, hwystyle=None):
        self.proj = proj or ccrs.Mercator()
        self.bbox = bbox
        if bbox is not None and not isinstance(self.bbox, Geobbox):
            west, east, south, north = self.bbox
            self.bbox = Geobbox(west, east, south, north, self.proj)
        self.bg = bg
        self.scale = scale
        self.borderstyle = borderstyle or MapStyle(1.0, 'gray', 'none', 1.0)
        self.countystyle = countystyle or MapStyle(0.2, 'gray', 'none', 1.0)
        self.hwystyle = hwystyle or MapStyle(0.4, 'brown', 'none', 1.0)
        self._ax = ax

    @property
    def ax(self):
        if self._ax is None:
            self._init_ax()
        return self._ax

    def _init_ax(self):
        if self._ax is None:
            self._ax = plt.axes(projection=self.proj)

        if self.bg is not None:
            self._ax.background_patch.set_facecolor(self.bg)

        if self.bbox is not None:
            self._ax.set_extent(self.bbox)

    def draw(self, layers='default', lake_threshold=None):
        if not layers or layers == 'default':
            layers = ['coastlines', 'borders', 'states', 'lakes']
        elif 'default' in layers:
            layers += ['coastlines', 'borders', 'states', 'lakes']

        if lake_threshold is None:
            lake_threshold = 80 if 'counties' in layers else 300

        self._init_ax()

        if 'coastlines' in layers:
            self.draw_coastlines()
        if 'borders' in layers:
            self.draw_borders()
        if 'states' in layers:
            self.draw_states()
        if 'lakes' in layers:
            self.draw_lakes(lake_threshold)
        if 'counties' in layers:
            self.draw_counties()
        if 'highways' in layers:
            self.draw_highways()

    def draw_us_detailed(self):
        self.draw(layers=['default', 'counties', 'highways'])

    @property
    def plot(self):
        return CartopyMapPlotter(self)

    def draw_coastlines(self):
        coastlines = cfeat.GSHHSFeature(self.scale, levels=[1])
        self.ax.add_feature(coastlines, **self.borderstyle.to_mpl_kw())

    def draw_lakes(self, threshold=300):
        lakes = (rec.geometry for rec in self._ghssh_shp(self.scale, level=2).records()
                 if _size_km(rec) > threshold)
        self.ax.add_geometries(lakes, ccrs.PlateCarree(), **self.borderstyle.to_mpl_kw())

    def draw_borders(self):
        borders = (read_line_geometries(rec) for rec in self._wdbii_shp(self.scale, level=1).records())
        self.ax.add_geometries(borders, ccrs.PlateCarree(), **self.borderstyle.to_mpl_kw())

    def draw_states(self):
        states = (read_line_geometries(rec) for rec in self._wdbii_shp(self.scale, level=2).records())
        self.ax.add_geometries(states, ccrs.PlateCarree(), **self.borderstyle.to_mpl_kw())

    def draw_counties(self):
        counties = self._generic_shp('UScounties').geometries()
        self.ax.add_geometries(counties, ccrs.PlateCarree(), **self.countystyle.to_mpl_kw())

    def draw_highways(self):
        hwys = self._generic_shp('hways').geometries()
        self.ax.add_geometries(hwys, ccrs.PlateCarree(), **self.hwystyle.to_mpl_kw())

    def plotlatlons(self, lats, lons, **kwargs):
        transf = kwargs.pop('transform', ccrs.PlateCarree())
        return self.ax.plot(lons, lats, transform=transf, **kwargs)

    def _generic_shp(self, name):
        file = config.get_shp(name, name + '.shp')
        return cartopy.io.shapereader.Reader(file)

    def _ghssh_shp(self, scale, level):
        file = config.get_shp('gshhs', 'GSHHS_{}_L{}.shp'.format(scale, level))
        return cartopy.io.shapereader.Reader(file)

    def _wdbii_shp(self, scale, level, type='border'):
        file = config.get_shp('gshhs', 'WDBII_{}_{}_L{}.prj'.format(type, scale, level))
        return cartopy.io.shapereader.Reader(file)


class MapStyle(object):
    def __init__(self, width=1.0, color='gray', fill='none', alpha=1.0):
        self.width = width
        self.color = color
        self.fill = fill
        self.alpha = alpha

    def to_mpl_kw(self):
        return {
            'edgecolor': self.color,
            'linewidth': self.width,
            'facecolor': self.fill,
            'alpha': self.alpha
        }


def read_line_geometries(shprec, threshold_km=100):
    size = _size_km(shprec)
    geom = shprec.geometry

    if size < threshold_km:
        return geom

    if len(geom) != 1:
        # the GSHHS shapefile only has one geometry per record,
        # so we punt here when in the case it's not
        return geom

    only_geom_in_group = geom[0]
    geom_coords = only_geom_in_group.coords
    result_geometry = []
    for i, current_coord in enumerate(geom_coords):
        if i == len(geom_coords) - 1:
            result_geometry.append(current_coord)
        else:
            next_coord = geom_coords[i + 1]
            lon0, lat0 = current_coord
            lon1, lat1 = next_coord
            dist = distance((lat0, lon0), (lat1, lon1)).km

            if dist < threshold_km:
                result_geometry.append(current_coord)
            else:
                n = int(math.ceil(dist / threshold_km)) + 1
                inset_xs = np.linspace(lon0, lon1, n)
                inset_ys = np.linspace(lat0, lat1, n)

                for inset_x, inset_y in zip(inset_xs, inset_ys):
                    result_geometry.append((inset_x, inset_y))

    line = sgeom.LineString(result_geometry)
    return sgeom.MultiLineString([line])


def _size_km(shprec):
    lon0, lat0, lon1, lat1 = shprec.bounds
    return distance((lat0, lon0), (lat1, lon1)).km
