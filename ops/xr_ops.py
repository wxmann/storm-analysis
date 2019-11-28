import xarray as xr
import numpy as np
from scipy import fftpack

from .op_shared import LatLonAware

@xr.register_dataset_accessor('geospatial')
class GeospatialDataset(LatLonAware):
    def __init__(self, ds):
        super().__init__()
        self._ds = ds

    def _latlon_accessor_check(self, accessors, check_dims=True):
        super()._latlon_accessor_check(accessors)

        if check_dims:
            for accessor in accessors:
                if not accessor in self._ds.dims:
                    raise ValueError(f"Cannot find dimension in dataset: {accessor}")

    def shiftgrid(self, latlon_dims=None):
        _, londim = self._get_latlon_accessors(latlon_dims)
        shifted = self._ds.copy()
        londata = shifted[londim].values
        londata_shifted = np.where((londata >= -180) & (londata <= 180), londata, -360 + londata)
        shifted[londim] = londata_shifted
        shifted = shifted.sortby(londim)
        return shifted

    def domain(self, lon0, lon1, lat0, lat1, latlon_dims=None, descending_lats=True):
        latdim, londim = self._get_latlon_accessors(latlon_dims)
        lonslice = slice(lon0, lon1)
        latslice = slice(lat1, lat0) if descending_lats else slice(lat0, lat1)
        return self._ds.sel({latdim: latslice, londim: lonslice})


@xr.register_dataset_accessor('fft')
class FftDataset():
    def __init__(self, ds):
        super().__init__()
        self._ds = ds

    def power_spectrum(self, var, sample_spacing):
        fft_in = self._ds[var]
        sig_fft = fftpack.fft(fft_in)
        power = np.abs(sig_fft) ** 2
        sample_freq = fftpack.fftfreq(fft_in.size, sample_spacing)
        positive_freq = sample_freq > 0
        return sample_freq[positive_freq], power[positive_freq]