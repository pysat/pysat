"""
tests the pysat coords area
"""
import datetime as dt
import logging
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
        self.inst_time_2 = dt.datetime(2009, 1, 3)

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
        # Testing the difference in periodic space to guard against changes
        # in numerical precision across platforms.
        diff = abs(self.py_inst['slt'].values
                   - self.py_inst['longitude'].values / 15.0)
        diff_radians = diff * np.pi / 12.0
        sin_diff = np.sin(diff_radians)
        cos_diff = np.cos(diff_radians)
        assert np.max(np.abs(sin_diff)) < 1.0e-6
        assert np.min(np.abs(cos_diff)) > 1.0 - 1.0e-6

    @pytest.mark.parametrize("name", ["testing", "testing_xarray"])
    def test_calc_solar_local_time_inconsistent_keywords(self, name, caplog):
        """Test that ref_date only works when apply_modulus=False"""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        num_samples=1)
        self.py_inst.load(date=self.inst_time)
        with caplog.at_level(logging.INFO, logger='pysat'):
            # Apply solar local time method
            coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                         slt_name='slt',
                                         ref_date=self.py_inst.date,
                                         apply_modulus=True)
        captured = caplog.text

        # Confirm we have the correct informational message
        assert captured.find('Keyword `ref_date` only supported if') >= 0
        return

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
        """Test calc_solar_local_time with a bad longitude name."""

        self.py_inst = pysat.Instrument(platform='pysat', name="testing")
        self.py_inst.load(date=self.inst_time)

        with pytest.raises(ValueError):
            coords.calc_solar_local_time(self.py_inst,
                                         lon_name="not longitude",
                                         slt_name='slt')

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "testing2d_xarray"])
    def test_lon_broadcasting_calc_solar_local_time(self, name):
        """Test calc_solar_local_time with longitude coordinates."""

        self.py_inst = pysat.Instrument(platform='pysat', name=name)
        self.py_inst.load(date=self.inst_time)
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt')

        assert self.py_inst['slt'].max() < 24.0
        assert self.py_inst['slt'].min() >= 0.0

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "testing2d_xarray"])
    def test_lon_broadcasting_calc_solar_local_time_no_mod_multiday(self, name):
        """Test calc_solar_local_time with longitude coordinates, no mod, 2 days
        """

        self.py_inst = pysat.Instrument(platform='pysat', name=name)
        self.py_inst.load(date=self.inst_time, end_date=self.inst_time_2)
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt', apply_modulus=False)

        assert self.py_inst['slt'].max() > 48.0
        assert self.py_inst['slt'].max() < 72.0
        assert self.py_inst['slt'].min() >= 0.0

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "testing2d_xarray"])
    def test_lon_broadcasting_calc_solar_local_time_no_mod_ref_date(self, name):
        """Test calc_solar_local_time with longitude coordinates, no mod, 2 days
        """

        self.py_inst = pysat.Instrument(platform='pysat', name=name)
        self.py_inst.load(date=self.inst_time, end_date=self.inst_time_2)
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt', apply_modulus=False,
                                     ref_date=self.inst_time
                                              - dt.timedelta(days=1))

        assert self.py_inst['slt'].max() > 72.0
        assert self.py_inst['slt'].max() < 96.0
        assert self.py_inst['slt'].min() >= 24.0

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "testing2d_xarray"])
    def test_lon_broadcasting_calc_solar_local_time_no_mod(self, name):
        """Test calc_solar_local_time with longitude coordinates, no modulus
        """

        self.py_inst = pysat.Instrument(platform='pysat', name=name)
        self.py_inst.load(date=self.inst_time)
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt', apply_modulus=False)

        assert self.py_inst['slt'].max() > 24.0
        assert self.py_inst['slt'].max() < 48.0
        assert self.py_inst['slt'].min() >= 0.0

    def test_single_lon_calc_solar_local_time(self):
        """Test calc_solar_local_time with a single longitude value."""

        self.py_inst = pysat.Instrument(platform='pysat', name="testing_xarray")
        self.py_inst.load(date=self.inst_time)
        lon_name = 'lon2'

        # Create a second longitude with a single value
        self.py_inst.data = self.py_inst.data.update({lon_name: (lon_name,
                                                                 [10.0])})
        self.py_inst.data = self.py_inst.data.squeeze(dim=lon_name)

        # Calculate and test the SLT
        coords.calc_solar_local_time(self.py_inst, lon_name=lon_name,
                                     slt_name='slt')

        assert self.py_inst['slt'].max() < 24.0
        assert self.py_inst['slt'].min() >= 0.0
        assert self.py_inst['slt'].shape == self.py_inst.index.shape
