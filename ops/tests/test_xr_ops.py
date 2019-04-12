import pytest
import xarray as xr
import numpy as np

import ops
from testing.helpers import resource_path

@pytest.fixture(scope='module')
def set_accessors():
    ops.set_latlon_accessor(['lat', 'lon'])
    yield
    ops.unset_latlon_accessor()


def test_shiftgrid_dataset(set_accessors):
    ds = xr.open_dataset(resource_path('h5_910427.nc'))
    shifted = ds.geospatial.shiftgrid()

    assert shifted.lon.values.max() == 180.0
    assert shifted.lon.values.min() == -177.5
    assert ds.lon.values.min() == 0.0

    assert shifted.lon.shape == ds.lon.shape
    assert (np.diff(shifted.lon) >= 0).all()


def test_get_domain(set_accessors):
    lon0, lon1 = 100, 200
    lat0, lat1 = 0, 90
    ds = xr.open_dataset(resource_path('h5_910427.nc'))
    shifted = ds.geospatial.domain(lon0, lon1, lat0, lat1)

    lats = shifted.lat.values
    lons = shifted.lon.values

    assert ((lats >= lat0) & (lats <= lat1)).all()
    assert ((lons >= lon0) & (lons <= lon1)).all()
    assert lats.shape[0] == 37
    assert lons.shape[0] == 41



