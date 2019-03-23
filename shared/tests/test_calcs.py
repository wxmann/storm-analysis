import numpy as np
import pytest

from shared.calcs import spherical_centroid


def test_spherical_centroid():
    arr1 = np.array([0, -120, 89, -120]).reshape(2, 2)
    arr2 = np.array([20, -175, 20, 175]).reshape(2, 2)
    latctr1, lonctr1 = spherical_centroid(arr1[:, 0], arr1[:, 1])
    latctr2, lonctr2 = spherical_centroid(arr2[:, 0], arr2[:, 1])

    assert (latctr1, lonctr1) == (pytest.approx(44.5), pytest.approx(-120))
    assert (latctr2, lonctr2) == (pytest.approx(20, 1e-2), pytest.approx(180, 1e-2))
