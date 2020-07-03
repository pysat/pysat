"""
tests the pysat coords area
"""
import numpy as np

import pandas as pds
import pytest

import pysat
from pysat.utils import coords, time


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.test_angles = np.array([340.0, 348.0, 358.9, 0.5, 5.0, 9.87])

        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing',
                                         clean_level='clean')
        # Add longitude to the test instrument
        ones = np.ones(shape=len(self.test_angles))
        tind = time.create_datetime_index(year=ones*2001,
                                          month=ones,
                                          uts=np.arange(0.0, len(ones), 1.0))

        self.testInst.data = \
            pds.DataFrame(np.array([tind, self.test_angles]).transpose(),
                          index=tind, columns=["time", "longitude"])

        self.deg_units = ["deg", "degree", "degrees", "rad", "radian",
                          "radians", "h", "hr", "hrs", "hours"]
        self.dist_units = ["m", "km", "cm"]
        self.vel_units = ["m/s", "cm/s", "km/s", 'm s$^{-1}$', 'cm s$^{-1}$',
                          'km s$^{-1}$', 'm s-1', 'cm s-1', 'km s-1']

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.test_angles, self.testInst
        del self.deg_units, self.dist_units, self.vel_units

    #####################################
    # Cyclic data conversions

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

    #####################################
    # Update Longitude

    def test_update_longitude(self):
        """Test update_longitude """

        coords.update_longitude(self.testInst, lon_name="longitude")

        assert np.all(self.testInst.data['longitude'] < 180.0)
        assert np.all(self.testInst.data['longitude'] >= -180.0)

    def test_bad_lon_name_update_longitude(self):
        """Test update_longitude with a bad longitude name"""

        with pytest.raises(ValueError):
            coords.update_longitude(self.testInst, lon_name="not longitude")

    #########################
    # calc_solar_local_time

    def test_calc_solar_local_time(self):
        """Test calc_solar_local_time"""

        coords.calc_solar_local_time(self.testInst, lon_name="longitude",
                                     slt_name='slt')
        target = np.array([22.66666667, 23.20027778, 23.92722222,
                           0.03416667, 0.33444444, 0.65938889])

        assert (abs(self.testInst['slt'] - target)).max() < 1.0e-6

    def test_calc_solar_local_time_w_update_longitude(self):
        """Test calc_solar_local_time with update_longitude"""

        coords.calc_solar_local_time(self.testInst, lon_name="longitude",
                                     slt_name='slt')
        coords.update_longitude(self.testInst, lon_name="longitude")
        coords.calc_solar_local_time(self.testInst, lon_name="longitude",
                                     slt_name='slt2')

        assert (abs(self.testInst['slt']
                    - self.testInst['slt2'])).max() < 1.0e-6

    def test_bad_lon_name_calc_solar_local_time(self):
        """Test calc_solar_local_time with a bad longitude name"""

        with pytest.raises(ValueError):
            coords.calc_solar_local_time(self.testInst,
                                         lon_name="not longitude",
                                         slt_name='slt')
