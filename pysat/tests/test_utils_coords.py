"""
tests the pysat coords area
"""
import datetime as dt
import numpy as np

import pytest

import pysat
from pysat.utils import ucoords

class TestCyclicData():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.test_angles = np.array([340.0, 348.0, 358.9, 0.5, 5.0, 9.87])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.test_angles

    def test_adjust_cyclic_data_default(self):
        """ Test adjust_cyclic_data with default range """

        test_in = np.radians(self.test_angles) - np.pi
        test_angles = ucoords.adjust_cyclic_data(test_in)

        assert test_angles.max() < 2.0 * np.pi
        assert test_angles.min() >= 0.0

    def test_adjust_cyclic_data_custom(self):
        """ Test adjust_cyclic_data with a custom range """

        test_angles = ucoords.adjust_cyclic_data(self.test_angles,
                                                high=180.0, low=-180.0)

        assert test_angles.max() < 180.0
        assert test_angles.min() >= -180.0


class TestLonSLT():
    def setup(self):
        """Runs after every method to clean up previous testing."""
        self.test_inst = None
        self.test_time = dt.datetime(2009, 1, 1)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.test_inst, self.test_time

    #####################################
    # Update Longitude
    @pytest.mark.parametrize("name", ["testing", "testing_xarray"])
    def test_update_longitude(self, name):
        """Test update_longitude """

        self.test_inst = pysat.Instrument(platform='pysat', name=name)
        self.test_inst.load(date=self.test_time)

        # Test instruments initially define longitude between 0-360 deg
        assert np.all(self.testInst.data['longitude'] < 360.0)
        assert np.all(self.testInst.data['longitude'] >= 0.0)

        # Longitude defaults to updating range from -180 to 180 deg
        ucoords.update_longitude(self.testInst, lon_name="longitude")

        assert np.all(self.test_inst.data['longitude'] < 180.0)
        assert np.all(self.test_inst.data['longitude'] >= -180.0)

    def test_bad_lon_name_update_longitude(self):
        """Test update_longitude with a bad longitude name"""

        self.test_inst = pysat.Instrument(platform='pysat', name="testing")
        self.test_inst.load(date=self.test_time)

        with pytest.raises(ValueError):
            ucoords.update_longitude(self.testInst, lon_name="not longitude")

    #########################
    # calc_solar_local_time
    @pytest.mark.parametrize("name", ["testing", "testing_xarray"])
    def test_calc_solar_local_time(self):
        """Test calc_solar_local_time with longitudes from 0-360 deg"""

        self.test_inst = pysat.Instrument(platform='pysat', name=name)
        self.test_inst.load(date=self.test_time)

        ucoords.calc_solar_local_time(self.test_inst, lon_name="longitude",
                                     slt_name='slt')

        # This works because test instrument longitude ranges from 0-360 deg
        assert (abs(self.test_inst['slt']
                    - self.test_inst['longitude'] / 15.0)).max() < 1.0e-6

    def test_calc_solar_local_time_w_neg_longitude(self):
        """Test calc_solar_local_time with longitudes from -180 to 180 deg"""

        self.test_inst = pysat.Instrument(platform='pysat', name="testing")
        self.test_inst.load(date=self.test_time)

        ucoords.calc_solar_local_time(self.test_inst, lon_name="longitude",
                                     slt_name='slt')
        ucoords.update_longitude(self.testInst, lon_name="longitude")
        ucoords.calc_solar_local_time(self.testInst, lon_name="longitude",
                                     slt_name='slt2')

        assert (abs(self.testInst['slt']
                    - self.testInst['slt2'])).max() < 1.0e-6

    def test_bad_lon_name_calc_solar_local_time(self):
        """Test calc_solar_local_time with a bad longitude name"""

        self.test_inst = pysat.Instrument(platform='pysat', name="testing")
        self.test_inst.load(date=self.test_time)

        with pytest.raises(ValueError):
            ucoords.calc_solar_local_time(self.testInst,
                                         lon_name="not longitude",
                                         slt_name='slt')
