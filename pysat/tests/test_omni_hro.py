import pysat
import pandas as pds
import numpy as np
from nose.tools import assert_raises, raises
import nose.tools

class TestOMNICustom:
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.test_angles = [340.0, 348.0, 358.9, 0.5, 5.0, 9.87]
        self.test_nan = [340.0, 348.0, 358.9, 0.5, 5.0, 9.87, np.nan]
        self.circ_kwargs = {"high":360.0, "low":0.0}
        self.testInst = pysat.Instrument('pysat', 'testing', tag='10',
                                         clean_level='clean')
        self.testInst.data['BX_GSM'] = pds.Series([3.17384966, 5.98685138,
                                                   1.78749668, 0.38628409,
                                                   2.73080263, 1.58814078,
                                                   5.24880448, 3.92347300,
                                                   5.59494670, 0.93246592,
                                                   5.23676319, 1.14214992])
        self.testInst.data['BY_GSM'] = pds.Series([3.93531272, 2.50331246,
                                                   0.99765539, 1.07203600,
                                                   5.43752734, 5.10629137,
                                                   0.59588891, 2.19412638,
                                                   0.15550858, 3.75433603,
                                                   4.82323932, 3.61784563])
        self.testInst.data['BZ_GSM'] = pds.Series([3.94396168, 5.61163579,
                                                   4.02930788, 5.47347958,
                                                   5.69823962, 0.47219819,
                                                   1.47760461, 3.47187188,
                                                   4.12581021, 4.40641671,
                                                   2.87780562, 0.58539121])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.test_angles, self.test_nan, self.circ_kwargs, self.testInst

    def test_circmean(self):
        """ Test custom circular mean."""
        from scipy import stats

        ref_mean = stats.circmean(self.test_angles, **self.circ_kwargs)
        test_mean = pysat.instruments.omni_hro.nan_circmean(self.test_angles,
                                                            **self.circ_kwargs)
        ans1 = ref_mean == test_mean

        assert ans1

    def test_circstd_nan(self):
        """ Test custom circular mean with NaN."""
        from scipy import stats

        ref_mean = stats.circmean(self.test_angles, **self.circ_kwargs)
        ref_nan = stats.circmean(self.test_nan, **self.circ_kwargs)
        test_nan = pysat.instruments.omni_hro.nan_circmean(self.test_nan,
                                                           **self.circ_kwargs)

        ans1 = np.isnan(ref_nan)
        ans2 = ref_mean == test_nan

        assert ans1 & ans2

    def test_circstd(self):
        """ Test custom circular std."""
        from scipy import stats

        ref_std = stats.circstd(self.test_angles, **self.circ_kwargs)
        test_std = pysat.instruments.omni_hro.nan_circstd(self.test_angles,
                                                          **self.circ_kwargs)
        ans1 = ref_std == test_std

        assert ans1

    def test_circstd_nan(self):
        """ Test custom circular std with NaN."""
        from scipy import stats

        ref_std = stats.circstd(self.test_angles, **self.circ_kwargs)
        ref_nan = stats.circstd(self.test_nan, **self.circ_kwargs)
        test_nan = pysat.instruments.omni_hro.nan_circstd(self.test_nan,
                                                          **self.circ_kwargs)

        ans1 = np.isnan(ref_nan)
        ans2 = ref_std == test_nan

        assert ans1 & ans2

    def test_clock_angle(self):
        """ Test clock angle."""

        # Run the clock angle routine
        pysat.instruments.omni_hro.calculate_clock_angle(self.testInst)

        # Set test clock angle
        test_angle = pds.Series([44.93710732, 24.04132437, 13.90673288,
                                 11.08167359, 43.65882745, 84.71666707,
                                 21.96325222, 32.29174675,  2.15855047,
                                 40.43151704, 59.17741091, 80.80882619])

        # Test the difference.  There may be a 2 pi integer ambiguity
        test_diff = test_angle - self.testInst['clock_angle']
        ans1 = np.all(test_diff == 0.0)

        assert ans1

    def test_yz_plane_mag(self):
        """ Test the Byz plane magnitude calculation."""

        # Run the clock angle routine
        pysat.instruments.omni_hro.calculate_clock_angle(self.testInst)

        # Calculate plane magnitude
        test_mag = pds.Series([5.57149172, 6.14467489, 4.15098040, 5.57747612,
                               7.87633407, 5.12807787, 1.59323538, 4.10707742,
                               4.12873986, 5.78891590, 5.61652942, 3.66489971])

        # Test the difference
        test_diff = test_mag - self.testInst['BYZ_GSM']
        ans1 = np.all(test_diff == 0.0)

        assert ans1

    def test_yz_plane_cv(self):
        """ Test the IMF steadiness calculation."""

        # Run the clock angle and steadiness routines
        pysat.instruments.omni_hro.calculate_clock_angle(self.testInst)
        pysat.instruments.omni_hro.calculate_imf_steadiness(self.testInst,
                                                            min_periods=4,
                                                            window=5)

        # Ensure the BYZ coefficient of variation is calculated correctly
        byz_cv = pds.Series([np.nan, 0.158620, 0.229267, 0.239404, 0.469371,
                             0.470944, 0.495892, 0.384522, 0.396275, 0.208209,
                             0.221267, np.nan])

        # Test the difference
        test_diff = byz_cv - self.testInst['BYZ_CV']

        ans1 = test_diff[np.isnan(test_diff)].shape[0] == 2
        ans2 = np.all(test_diff[~np.isnan(test_diff)] == 0.0)
        ans3 = np.all(np.isnan(self.testInst['BYZ_CV']) == np.isnan(byz_cv))

        assert ans1 & ans2 & ans3

    def test_clock_angle_std(self):
        """ Test the IMF steadiness calculation."""

        # Run the clock angle and steadiness routines
        pysat.instruments.omni_hro.calculate_clock_angle(self.testInst)
        pysat.instruments.omni_hro.calculate_imf_steadiness(self.testInst,
                                                            min_periods=4,
                                                            window=5)

        # Ensure the BYZ coefficient of variation is calculated correctly
        ca_std = pds.Series([np.nan, 13.317200, 14.429278, 27.278579,
                             27.468469, 25.500730, 27.673033, 27.512069,
                             19.043833, 26.616713, 29.250390, np.nan])

        # Test the difference
        test_diff = ca_std - self.testInst['clock_angle_std']

        ans1 = test_diff[np.isnan(test_diff)].shape[0] == 2
        ans2 = np.all(test_diff[~np.isnan(test_diff)] == 0.0)
        ans3 = np.all(np.isnan(self.testInst['clock_angle_std']) ==
                      np.isnan(ca_std))

        assert ans1 & ans2 & ans3
