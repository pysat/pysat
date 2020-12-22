"""
tests the pysat coords area
"""
import datetime as dt
import numpy as np

import pytest

import pysat
from pysat.utils import coords


class TestCyclicData():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.ref_angles = np.array([340.0, 348.0, 358.9, 0.5, 5.0, 9.87])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.ref_angles

    def test_adjust_cyclic_data_default(self):
        """ Test adjust_cyclic_data with default range """

        ref_rad = np.radians(self.ref_angles) - np.pi
        ref_angles = coords.adjust_cyclic_data(ref_rad)

        assert ref_angles.max() < 2.0 * np.pi
        assert ref_angles.min() >= 0.0

    def test_adjust_cyclic_data_custom(self):
        """ Test adjust_cyclic_data with a custom range """

        ref_angles = coords.adjust_cyclic_data(self.ref_angles,
                                               high=180.0, low=-180.0)

        assert ref_angles.max() < 180.0
        assert ref_angles.min() >= -180.0


class TestLonSLT():
    def setup(self):
        """Runs after every method to clean up previous testing."""
        self.py_inst = None
        self.inst_time = dt.datetime(2009, 1, 1)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.py_inst, self.inst_time

    #####################################
    # Update Longitude
    @pytest.mark.parametrize("name", ["testing", "testing_xarray"])
    def test_update_longitude(self, name):
        """Test update_longitude """

        self.py_inst = pysat.Instrument(platform='pysat', name=name)
        self.py_inst.load(date=self.inst_time)

        # Test instruments initially define longitude between 0-360 deg
        assert np.all(self.py_inst.data['longitude'] < 360.0)
        assert np.all(self.py_inst.data['longitude'] >= 0.0)

        # Longitude defaults to updating range from -180 to 180 deg
        coords.update_longitude(self.py_inst, lon_name="longitude")

        assert np.all(self.py_inst.data['longitude'] < 180.0)
        assert np.all(self.py_inst.data['longitude'] >= -180.0)

    def test_bad_lon_name_update_longitude(self):
        """Test update_longitude with a bad longitude name"""

        self.py_inst = pysat.Instrument(platform='pysat', name="testing")
        self.py_inst.load(date=self.inst_time)

        with pytest.raises(ValueError):
            coords.update_longitude(self.py_inst, lon_name="not longitude")

    #########################
    # calc_solar_local_time
    @pytest.mark.parametrize("name", ["testing", "testing_xarray"])
    def test_calc_solar_local_time(self, name):
        """Test calc_solar_local_time with longitudes from 0-360 deg for 0 UTH
        """

        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        num_samples=1)
        self.py_inst.load(date=self.inst_time)

        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt')

        # This works because test instrument longitude ranges from 0-360 deg
        assert (abs(self.py_inst['slt'].values
                    - self.py_inst['longitude'].values / 15.0)).max() < 1.0e-6

    def test_calc_solar_local_time_w_neg_longitude(self):
        """Test calc_solar_local_time with longitudes from -180 to 180 deg"""

        self.py_inst = pysat.Instrument(platform='pysat', name="testing")
        self.py_inst.load(date=self.inst_time)

        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt')
        coords.update_longitude(self.py_inst, lon_name="longitude")
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt2')

        assert (abs(self.py_inst['slt'] - self.py_inst['slt2'])).max() < 1.0e-6

    def test_bad_lon_name_calc_solar_local_time(self):
        """Test calc_solar_local_time with a bad longitude name"""

        self.py_inst = pysat.Instrument(platform='pysat', name="testing")
        self.py_inst.load(date=self.inst_time)

        with pytest.raises(ValueError):
            coords.calc_solar_local_time(self.py_inst,
                                         lon_name="not longitude",
                                         slt_name='slt')
