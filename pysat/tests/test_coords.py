"""
tests the pysat coords area
"""
import os
import numpy as np
import nose.tools
from nose.tools import assert_raises, raises
import pysat
import pysat.instruments.pysat_testing


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        from pysat.utils import coords

    def teardown(self):
        """Runs after every method to clean up previous testing."""

    def test_geodetic_to_geocentric_single(self):
        """Test conversion from geodetic to geocentric coordinates"""

        lat0 = 45.0
        lon0 = 9.0

        latx, lonx, radx = coords.geodetic_to_geocentric(lat0,
                                                         lon_in=lon0)

        assert (abs(latx - 44.807576784018046) < 1.0e-6)
        assert (abs(lonx - lon0) < 1.0e-6)
        assert (abs(radx - 6367.489543863465) < 1.0e-6)

    def test_geocentric_to_geodetic_single(self):
        """Test conversion from geocentric to geodetic coordinates"""

        lat0 = 45.0
        lon0 = 9.0

        latx, lonx, radx = pysat.coords.geodetic_to_geocentric(lat0,
                                                               lon_in=lon0,
                                                               inverse=True)

        assert (abs(latx - 45.192423215981954) < 1.0e-6)
        assert (abs(lonx - lon0) < 1.0e-6)
        assert (abs(radx - 6367.345908499981) < 1.0e-6)

    def test_geodetic_to_geocentric_mult(self):
        """Test array conversion from geodetic to geocentric coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        latx, lonx, radx = pysat.coords.geodetic_to_geocentric(45.0*arr,
                                                               lon_in=9.0*arr)

        assert latx.shape == arr.shape
        assert lonx.shape == arr.shape
        assert radx.shape == arr.shape
        assert (abs(latx - 44.807576784018046).max() < 1.0e-6)
        assert (abs(lonx - 9.0).max() < 1.0e-6)
        assert (abs(radx - 6367.489543863465).max() < 1.0e-6)

    def test_geocentric_to_geodetic_mult(self):
        """Test array conversion from geocentric to geodetic coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        latx, lonx, radx = pysat.coords.geodetic_to_geocentric(45.0*arr,
                                                               lon_in=9.0*arr,
                                                               inverse=True)

        assert latx.shape == arr.shape
        assert lonx.shape == arr.shape
        assert radx.shape == arr.shape
        assert (abs(latx - 45.192423215981954).max() < 1.0e-6)
        assert (abs(lonx - 9.0).max() < 1.0e-6)
        assert (abs(radx - 6367.345908499981).max() < 1.0e-6)

    def test_spherical_to_cartesian_single(self):
        """Test conversion from spherical to cartesian coordinates"""

        x, y, z = pysat.coords.spherical_to_cartesian(45.0, 30.0, 1.0)

        assert abs(x - y) < 1.0e-6
        assert abs(z - 0.5) < 1.0e-6

    def test_cartesian_to_spherical_single(self):
        """Test conversion from cartesian to spherical coordinates"""

        x = 0.6123724356957946
        az, el, r = pysat.coords.spherical_to_cartesian(x, x, 0.5,
                                                        inverse=True)

        assert abs(az - 45.0) < 1.0e-6
        assert abs(el - 30.0) < 1.0e-6
        assert abs(r - 1.0) < 1.0e-6

    def test_spherical_to_cartesian_mult(self):
        """Test array conversion from spherical to cartesian coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        x, y, z = pysat.coords.spherical_to_cartesian(45.0*arr, 30.0*arr, arr)

        assert x.shape == arr.shape
        assert y.shape == arr.shape
        assert z.shape == arr.shape
        assert abs(x - y).max() < 1.0e-6
        assert abs(z - 0.5).max() < 1.0e-6

    def test_cartesian_to_spherical_mult(self):
        """Test array conversion from cartesian to spherical coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        x = 0.6123724356957946
        az, el, r = pysat.coords.spherical_to_cartesian(x*arr, x*arr, 0.5*arr,
                                                        inverse=True)

        assert az.shape == arr.shape
        assert el.shape == arr.shape
        assert r.shape == arr.shape
        assert abs(az - 45.0).max() < 1.0e-6
        assert abs(el - 30.0).max() < 1.0e-6
        assert abs(r - 1.0).max() < 1.0e-6

    def test_geodetic_to_geocentric_inverse(self):
        """Tests the reversibility of geodetic to geocentric conversions"""

        lat1 = 37.5
        lon1 = 117.3
        lat2, lon2, rad_e = pysat.coords.geodetic_to_geocentric(lat1,
                                                                lon_in=lon1,
                                                                inverse=False)
        lat3, lon3, rad_e = pysat.coords.geodetic_to_geocentric(lat2,
                                                                lon_in=lon2,
                                                                inverse=True)
        assert (abs(lon1-lon3) < 1.0e-6)
        assert (abs(lat1-lat3) < 1.0e-6)

    def test_geodetic_to_geocentric_horizontal_inverse(self):
        """Tests the reversibility of geodetic to geocentric horiz conversions

        Note:  inverse of az and el angles currently non-functional"""

        lat1 = -17.5
        lon1 = 187.3
        az1 = 52.0
        el1 = 63.0
        lat2, lon2, rad_e, az2, el2 = \
            pysat.coords.geodetic_to_geocentric_horizontal(lat1, lon1,
                                                           az1, el1,
                                                           inverse=False)
        lat3, lon3, rad_e, az3, el3 = \
            pysat.coords.geodetic_to_geocentric_horizontal(lat2, lon2,
                                                           az2, el2,
                                                           inverse=True)

        assert (abs(lon1-lon3) < 1.0e-6)
        assert (abs(lat1-lat3) < 1.0e-6)
        assert (abs(az1-az3) < 1.0e-6)
        assert (abs(el1-el3) < 1.0e-6)

    def test_spherical_to_cartesian_inverse(self):
        """Tests the reversibility of spherical to cartesian conversions"""

        x1 = 3000.0
        y1 = 2000.0
        z1 = 2500.0
        az, el, r = pysat.coords.spherical_to_cartesian(x1, y1, z1,
                                                        inverse=True)
        x2, y2, z2 = pysat.coords.spherical_to_cartesian(az, el, r,
                                                         inverse=False)

        assert (abs(x1-x2) < 1.0e-6)
        assert (abs(y1-y2) < 1.0e-6)
        assert (abs(z1-z2) < 1.0e-6)

    def test_global_to_local_cartesian_inverse(self):
        """Tests the reversibility of the global to loc cartesian transform"""

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
        assert (abs(x1-x3) < 1.0e-6)
        assert (abs(y1-y3) < 1.0e-6)
        assert (abs(z1-z3) < 1.0e-6)

    def test_local_horizontal_to_global_geo(self):
        """Tests the conversion of the local horizontal to global geo"""

        az = 30.0
        el = 45.0
        dist = 1000.0
        lat0 = 45.0
        lon0 = 0.0
        alt0 = 400.0

        latx, lonx, radx = \
            pysat.coords.local_horizontal_to_global_geo(az, el, dist,
                                                        lat0, lon0, alt0)

        assert (abs(latx - 50.419037572472625) < 1.0e-6)
        assert (abs(lonx + 7.694008395350697) < 1.0e-6)
        assert (abs(radx - 7172.15486518744) < 1.0e-6)
