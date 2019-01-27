"""
tests the pysat utils area
"""
import os
import numpy as np
import nose.tools
from nose.tools import assert_raises, raises
import pysat
import pysat.instruments.pysat_testing


def test_geodetic_to_geocentric_inverse():
    """Tests the reversability of geodetic to geocentric conversions"""

    lat1 = 37.5
    lon1 = 117.3
    lat2, lon2, rad_e = pysat.coords.geodetic_to_geocentric(lat1,
                                                            lon_in=lon1,
                                                            inverse=False)
    lat3, lon3, rad_e = pysat.coords.geodetic_to_geocentric(lat2,
                                                            lon_in=lon2,
                                                            inverse=True)
    tol = 1e-9
    
    assert ((np.abs(lon1-lon3) < np.abs(lon1*tol)) &
            (np.abs(lat1-lat3) < np.abs(lat1*tol)))


def test_geodetic_to_geocentric_horizontal_inverse():
    """Tests the reversability of geodetic to geocentric horizontal conversions

    Note:  inverse of az and el angles currently non-functional"""

    lat1 = -17.5
    lon1 = 187.3
    az1 = 52.0
    el1 = 63.0
    lat2, lon2, rad_e, az2, el2 = \
        pysat.coords.geodetic_to_geocentric_horizontal(lat1, lon1, az1, el1,
                                                       inverse=False)
    lat3, lon3, rad_e, az3, el3 = \
        pysat.coords.geodetic_to_geocentric_horizontal(lat2, lon2, az2, el2,
                                                       inverse=True)

    tol = 1e-9

    assert ((np.abs(lon1-lon3) < np.abs(lon1*tol)) &
            (np.abs(lat1-lat3) < np.abs(lat1*tol)) &
            (np.abs(az1-az3) < np.abs(az1*tol)) &
            (np.abs(el1-el3) < np.abs(el1*tol)))


def test_spherical_to_cartesian_inverse():
    """Tests the reversability of spherical to cartesian conversions"""

    x1 = 3000.0
    y1 = 2000.0
    z1 = 2500.0
    az, el, r = pysat.coords.spherical_to_cartesian(x1, y1, z1, inverse=True)
    x2, y2, z2 = pysat.coords.spherical_to_cartesian(az, el, r, inverse=False)

    tol = 1e-9

    assert ((np.abs(x1-x2) < np.abs(x1*tol)) &
            (np.abs(y1-y2) < np.abs(y1*tol)) &
            (np.abs(z1-z2) < np.abs(z1*tol)))


def test_global_to_local_cartesian_inverse():
    """Tests the reversability of the global to local cartesian transform"""

    x1 = 7000.0
    y1 = 8000.0
    z1 = 9500.0
    lat = 37.5
    lon = 289.0
    rad = 6380.0
    x2, y2, z2 = pysat.coords.global_to_local_cartesian(x1, y1, z1,
                                                        lat, lon, rad,
                                                        inverse=False)
    x3, y3, z3 = pysat.coords.global_to_local_cartesian(x2, y2, z2,
                                                        lat, lon, rad,
                                                        inverse=True)
    tol = 1e-9

    assert ((np.abs(x1-x3) < np.abs(x1*tol)) &
            (np.abs(y1-y3) < np.abs(y1*tol)) &
            (np.abs(z1-z3) < np.abs(z1*tol)))
