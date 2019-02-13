"""
tests the pysat utils.coords area
"""
import os
import numpy as np
import pandas as pds
import tempfile
import nose.tools
from nose.tools import assert_raises, raises
import pysat
import pysat.instruments.pysat_testing
from pysat.utils import coords


def prep_dir(inst=None):
    import os
    import shutil

    if inst is None:
        inst = pysat.Instrument(platform='pysat', name='testing')
    # create data directories
    try:
        os.makedirs(inst.files.data_path)
        #print ('Made Directory')
    except OSError:
        pass

def remove_files(inst):
    # remove any files
    dir = inst.files.data_path
    for the_file in os.listdir(dir):
        if (the_file[0:13] == 'pysat_testing') & (the_file[-19:] ==
                                                  '.pysat_testing_file'):
            file_path = os.path.join(dir, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""

        self.test_angles = np.array([340.0, 348.0, 358.9, 0.5, 5.0, 9.87])
        self.deg_units = ["deg", "degree", "degrees", "rad", "radian",
                          "radians", "h", "hr", "hrs", "hours"]
        self.dist_units = ["m", "km", "cm"]
        self.vel_units = ["m/s", "cm/s", "km/s"]

        # store current pysat directory
        self.data_path = pysat.data_dir

        # create temporary directory
        dir_name = tempfile.mkdtemp()
        pysat.utils.set_data_dir(dir_name, store=False)

        self.testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                                         clean_level='clean')
        # create testing directory
        prep_dir(self.testInst)
        # Add longitude to the test instrument
        ones = np.ones(shape=len(self.test_angles))
        time = pysat.utils.time.create_datetime_index(year=ones*2001,
                                                      month=ones,
                                                      uts=np.arange(0.0,
                                                                    len(ones),
                                                                    1.0))


        test_dat = np.array([time, self.test_angles]).transpose()
        self.testInst.data = pds.DataFrame(test_dat,
                                           index=time,
                                           columns=["time", "longitude"])


    def teardown(self):
        """Runs after every method to clean up previous testing."""

        del self.test_angles, self.deg_units, self.dist_units, self.vel_units
        del self.testInst

    def test_adjust_cyclic_data_default(self):
        """ Test adjust_cyclic_data with default range """

        test_in = np.radians(self.test_angles) - np.pi
        test_angles = coords.adjust_cyclic_data(test_in)

        assert test_angles.max() < 2.0 * np.pi
        assert test_angles.min() >= 0.0

    def test_adjust_cyclic_data_custom(self):
        """ Test adjust_cyclic_data with a custom range """

        test_angles = coords.adjust_cyclic_data(self.test_angles,
                                                high=180.0, low=-180.0)

        assert test_angles.max() < 180.0
        assert test_angles.min() >= -180.0

    def test_update_longitude(self):
        """Test update_longitude """

        coords.update_longitude(self.testInst, lon_name="longitude")

        assert np.all(self.testInst.data['longitude'] < 180.0)
        assert np.all(self.testInst.data['longitude'] >= -180.0)

    def test_bad_lon_name_update_longitude(self):
        """Test update_longitude with a bad longitude name"""

        assert_raises(ValueError, coords.update_longitude,
                      self.testInst)

    def test_scale_units_same(self):
        """ Test scale_units when both units are the same """

        scale = coords.scale_units("happy", "happy")

        assert scale == 1.0

    def test_scale_units_angles(self):
        """Test scale_units for angles """

        for out_unit in self.deg_units:
            scale = coords.scale_units(out_unit, "deg")

            if out_unit.find("deg") == 0:
                assert scale == 1.0
            elif out_unit.find("rad") == 0:
                assert scale == np.pi / 180.0
            else:
                assert scale == 1.0 / 15.0

    def test_scale_units_dist(self):
        """Test scale_units for distances """

        for out_unit in self.dist_units:
            scale = coords.scale_units(out_unit, "m")

            if out_unit == "m":
                assert scale == 1.0
            elif out_unit.find("km") == 0:
                assert scale == 0.001
            else:
                assert scale == 100.0

    def test_scale_units_vel(self):
        """Test scale_units for velocities """

        for out_unit in self.vel_units:
            scale = coords.scale_units(out_unit, "m/s")

            if out_unit == "m/s":
                assert scale == 1.0
            elif out_unit.find("km/s") == 0:
                assert scale == 0.001
            else:
                assert scale == 100.0

    def test_scale_units_bad(self):
        """Test scale_units for mismatched input"""

        assert_raises(ValueError, coords.scale_units, "happy", "m")
        assert_raises(ValueError, coords.scale_units, "m", "happy")
        assert_raises(ValueError, coords.scale_units, "m", "m/s")
        assert_raises(ValueError, coords.scale_units, "m", "deg")
        assert_raises(ValueError, coords.scale_units, "h", "km/s")

    def test_geodetic_to_geocentric_single(self):
        """Test conversion from geodetic to geocentric coordinates"""

        lat, lon, rad = coords.geodetic_to_geocentric(45.0, lon_in=8.0)

        assert (abs(lat - 44.807576784018046) < 1.0e-6)
        assert (abs(lon - 8.0) < 1.0e-6)
        assert (abs(rad - 6367.489543863465) < 1.0e-6)

    def test_geocentric_to_geodetic_single(self):
        """Test conversion from geocentric to geodetic coordinates"""

        lat, lon, rad = coords.geodetic_to_geocentric(45.0, lon_in=8.0,
                                                      inverse=True)

        assert (abs(lat - 45.192423215981954) < 1.0e-6)
        assert (abs(lon - 8.0) < 1.0e-6)
        assert (abs(rad - 6367.345908499981) < 1.0e-6)

    def test_geodetic_to_geocentric_mult(self):
        """Test array conversion from geodetic to geocentric coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        lat, lon, rad = coords.geodetic_to_geocentric(45.0*arr,
                                                      lon_in=8.0*arr)

        assert lat.shape == arr.shape
        assert lon.shape == arr.shape
        assert rad.shape == arr.shape
        assert (abs(lat - 44.807576784018046).max() < 1.0e-6)
        assert (abs(lon - 8.0).max() < 1.0e-6)
        assert (abs(rad - 6367.489543863465).max() < 1.0e-6)

    def test_geocentric_to_geodetic_mult(self):
        """Test array conversion from geocentric to geodetic coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        lat, lon, rad = coords.geodetic_to_geocentric(45.0*arr, lon_in=8.0*arr,
                                                      inverse=True)

        assert lat.shape == arr.shape
        assert lon.shape == arr.shape
        assert rad.shape == arr.shape
        assert (abs(lat - 45.192423215981954).max() < 1.0e-6)
        assert (abs(lon - 8.0).max() < 1.0e-6)
        assert (abs(rad - 6367.345908499981).max() < 1.0e-6)

    def test_spherical_to_cartesian_single(self):
        """Test conversion from spherical to cartesian coordinates"""

        x, y, z = coords.spherical_to_cartesian(45.0, 30.0, 1.0)

        assert abs(x - y) < 1.0e-6
        assert abs(z - 0.5) < 1.0e-6

    def test_cartesian_to_spherical_single(self):
        """Test conversion from cartesian to spherical coordinates"""

        x = 0.6123724356957946
        az, el, r = coords.spherical_to_cartesian(x, x, 0.5,
                                                  inverse=True)

        assert abs(az - 45.0) < 1.0e-6
        assert abs(el - 30.0) < 1.0e-6
        assert abs(r - 1.0) < 1.0e-6

    def test_spherical_to_cartesian_mult(self):
        """Test array conversion from spherical to cartesian coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        x, y, z = coords.spherical_to_cartesian(45.0*arr, 30.0*arr, arr)

        assert x.shape == arr.shape
        assert y.shape == arr.shape
        assert z.shape == arr.shape
        assert abs(x - y).max() < 1.0e-6
        assert abs(z - 0.5).max() < 1.0e-6

    def test_cartesian_to_spherical_mult(self):
        """Test array conversion from cartesian to spherical coordinates"""

        arr = np.ones(shape=(10,), dtype=float)
        x = 0.6123724356957946
        az, el, r = coords.spherical_to_cartesian(x*arr, x*arr, 0.5*arr,
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
        lat2, lon2, rad_e = coords.geodetic_to_geocentric(lat1, lon_in=lon1,
                                                          inverse=False)
        lat3, lon3, rad_e = coords.geodetic_to_geocentric(lat2, lon_in=lon2,
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
            coords.geodetic_to_geocentric_horizontal(lat1, lon1,
                                                     az1, el1,
                                                     inverse=False)
        lat3, lon3, rad_e, az3, el3 = \
            coords.geodetic_to_geocentric_horizontal(lat2, lon2,
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
        az, el, r = coords.spherical_to_cartesian(x1, y1, z1, inverse=True)
        x2, y2, z2 = coords.spherical_to_cartesian(az, el, r, inverse=False)

        assert (abs(x1-x2) < 1.0e-6)
        assert (abs(y1-y2) < 1.0e-6)
        assert (abs(z1-z2) < 1.0e-6)

    def test_global_to_local_cartesian_inverse(self):
        """Tests the reversibility of the global to loc cartesian transform"""

        x1 = 7000.0
        y1 = 8000.0
        z1 = 9500.0
        lat = 37.5
        lon = 288.0
        rad = 6380.0
        x2, y2, z2 = coords.global_to_local_cartesian(x1, y1, z1,
                                                      lat, lon, rad,
                                                      inverse=False)
        x3, y3, z3 = coords.global_to_local_cartesian(x2, y2, z2,
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
            coords.local_horizontal_to_global_geo(az, el, dist,
                                                  lat0, lon0, alt0)

        assert (abs(latx - 50.419037572472625) < 1.0e-6)
        assert (abs(lonx + 7.694008395350697) < 1.0e-6)
        assert (abs(radx - 7172.15486518744) < 1.0e-6)
