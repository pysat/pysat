import datetime as dt
import numpy as np

import pandas as pds

import pysat
from pysat.instruments import omni_hro



class TestOMNICustom():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing', sat_id='12',
                                         tag='1min', clean_level='clean')
        self.testInst.load(2009, 1)

        # Recast time in minutes rather than seconds
        self.testInst.data.index = \
            pds.Series([t + dt.timedelta(seconds=60-i) +
                        dt.timedelta(minutes=i)
                        for i, t in enumerate(self.testInst.data.index)])

        # Add IMF data
        self.testInst['BX_GSM'] = pds.Series([3.17384966, 5.98685138,
                                              1.78749668, 0.38628409,
                                              2.73080263, 1.58814078,
                                              5.24880448, 3.92347300,
                                              5.59494670, 0.93246592,
                                              5.23676319, 1.14214992],
                                             index=self.testInst.data.index)
        self.testInst['BY_GSM'] = pds.Series([3.93531272, 2.50331246,
                                              0.99765539, 1.07203600,
                                              5.43752734, 5.10629137,
                                              0.59588891, 2.19412638,
                                              0.15550858, 3.75433603,
                                              4.82323932, 3.61784563],
                                             index=self.testInst.data.index)
        self.testInst['BZ_GSM'] = pds.Series([3.94396168, 5.61163579,
                                              4.02930788, 5.47347958,
                                              5.69823962, 0.47219819,
                                              1.47760461, 3.47187188,
                                              4.12581021, 4.40641671,
                                              2.87780562, 0.58539121],
                                             index=self.testInst.data.index)
        self.testInst['flow_speed'] = \
            pds.Series([394.396168, 561.163579,
                        402.930788, 547.347958,
                        569.823962, 47.219819,
                        147.760461, 347.187188,
                        412.581021, 440.641671,
                        287.780562, 58.539121],
                       index=self.testInst.data.index)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    # def test_time_shift_to_magnetic_poles(self):
    #     """Test time shift of OMNI data"""
    #     pysat.instruments.omni_hro.time_shift_to_magnetic_poles(self.testInst)
    #
    #     assert True

    def test_clock_angle(self):
        """ Test clock angle."""

        # Run the clock angle routine
        omni_hro.calculate_clock_angle(self.testInst)

        # Set test clock angle
        test_angle = np.array([44.93710732, 24.04132437, 13.90673288,
                               11.08167359, 43.65882745, 84.71666707,
                               21.96325222, 32.29174675,  2.15855047,
                               40.43151704, 59.17741091, 80.80882619])

        # Test the difference.  There may be a 2 pi integer ambiguity
        test_diff = abs(test_angle - self.testInst['clock_angle'])
        assert np.all(test_diff < 1.0e-8)

    def test_yz_plane_mag(self):
        """ Test the Byz plane magnitude calculation."""

        # Run the clock angle routine
        omni_hro.calculate_clock_angle(self.testInst)

        # Calculate plane magnitude
        test_mag = np.array([5.57149172, 6.14467489, 4.15098040, 5.57747612,
                             7.87633407, 5.12807787, 1.59323538, 4.10707742,
                             4.12873986, 5.78891590, 5.61652942, 3.66489971])

        # Test the difference
        test_diff = abs(test_mag - self.testInst['BYZ_GSM'])
        assert np.all(test_diff < 1.0e-8)

    def test_yz_plane_cv(self):
        """ Test the IMF steadiness CV calculation."""

        # Run the clock angle and steadiness routines
        omni_hro.calculate_clock_angle(self.testInst)
        omni_hro.calculate_imf_steadiness(self.testInst, steady_window=5,
                                          min_window_frac=0.8)

        # Ensure the BYZ coefficient of variation is calculated correctly
        byz_cv = np.array([np.nan, 0.158620, 0.229267, 0.239404, 0.469371,
                           0.470944, 0.495892, 0.384522, 0.396275, 0.208209,
                           0.221267, np.nan])

        # Test the difference
        test_diff = abs(byz_cv - self.testInst['BYZ_CV'])

        assert test_diff[np.isnan(test_diff)].shape[0] == 2
        assert np.all(test_diff[~np.isnan(test_diff)] < 1.0e-6)
        assert np.all(np.isnan(self.testInst['BYZ_CV']) == np.isnan(byz_cv))

    def test_clock_angle_std(self):
        """ Test the IMF steadiness standard deviation calculation."""

        # Run the clock angle and steadiness routines
        omni_hro.calculate_clock_angle(self.testInst)
        omni_hro.calculate_imf_steadiness(self.testInst, steady_window=5,
                                          min_window_frac=0.8)

        # Ensure the BYZ coefficient of variation is calculated correctly
        ca_std = np.array([np.nan, 13.317200, 14.429278, 27.278579,
                           27.468469, 25.500730, 27.673033, 27.512069,
                           19.043833, 26.616713, 29.250390, np.nan])

        # Test the difference
        test_diff = abs(ca_std - self.testInst['clock_angle_std'])

        assert test_diff[np.isnan(test_diff)].shape[0] == 2
        assert np.all(test_diff[~np.isnan(test_diff)] < 1.0e-6)
        assert np.all(np.isnan(self.testInst['clock_angle_std']) ==
                      np.isnan(ca_std))

    def test_dayside_recon(self):
        """ Test the IMF steadiness standard deviation calculation."""

        # Run the clock angle and steadiness routines
        omni_hro.calculate_clock_angle(self.testInst)
        omni_hro.calculate_dayside_reconnection(self.testInst)

        # Ensure the BYZ coefficient of variation is calculated correctly
        rcon = np.array([698.297487, 80.233896, 3.033586, 2.216075,
                         1425.310083, 486.460306, 2.350339, 103.843722,
                         0.000720, 534.586320, 1464.596772, 388.974792])

        # Test the difference
        test_diff = abs(rcon - self.testInst['recon_day'])

        assert test_diff.shape[0] == 12
        assert np.all(test_diff < 1.0e-6)
