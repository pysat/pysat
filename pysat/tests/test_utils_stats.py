"""
tests the pysat utils.stats area
"""
import numpy as np

from scipy import stats as scistats

from pysat.utils import stats as pystats


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""

        # Add testing data for circular statistics
        self.test_angles = np.array([340.0, 348.0, 358.9, 0.5, 5.0, 9.87])
        self.test_nan = [340.0, 348.0, 358.9, 0.5, 5.0, 9.87, np.nan]
        self.circ_kwargs = {"high": 360.0, "low": 0.0}

    def teardown(self):
        """Runs after every method to clean up previous testing."""

        del self.test_angles, self.test_nan, self.circ_kwargs

    def test_circmean(self):
        """ Test custom circular mean."""

        ref_mean = scistats.circmean(self.test_angles, **self.circ_kwargs)
        test_mean = pystats.nan_circmean(self.test_angles, **self.circ_kwargs)

        assert ref_mean == test_mean

    def test_circmean_nan(self):
        """ Test custom circular mean with NaN."""

        ref_mean = scistats.circmean(self.test_angles, **self.circ_kwargs)
        ref_nan = scistats.circmean(self.test_nan, **self.circ_kwargs)
        test_nan = pystats.nan_circmean(self.test_nan, **self.circ_kwargs)

        assert np.isnan(ref_nan)
        assert ref_mean == test_nan

    def test_circstd(self):
        """ Test custom circular std."""

        ref_std = scistats.circstd(self.test_angles, **self.circ_kwargs)
        test_std = pystats.nan_circstd(self.test_angles, **self.circ_kwargs)

        assert ref_std == test_std

    def test_circstd_nan(self):
        """ Test custom circular std with NaN."""

        ref_std = scistats.circstd(self.test_angles, **self.circ_kwargs)
        ref_nan = scistats.circstd(self.test_nan, **self.circ_kwargs)
        test_nan = pystats.nan_circstd(self.test_nan, **self.circ_kwargs)

        assert np.isnan(ref_nan)
        assert ref_std == test_nan

    def test_deprecation_warning_median1d(self):
        """Test if median1D in stats is deprecated"""

        import warnings
        import pysat

        testInst = pysat.Instrument('pysat', 'testing')
        testInst.load(date=pysat.datetime(2009, 1, 1))

        warnings.simplefilter("always")
        with warnings.catch_warnings(record=True) as w:
            pystats.median1D(testInst, [0, 24, 2], 'slt', 'slt')

        assert len(w) == 1
        assert w[0].category == DeprecationWarning

    def test_deprecation_warning_circmean(self):
        """Test if circmean in stats is deprecated"""

        import warnings

        warnings.simplefilter("always")
        with warnings.catch_warnings(record=True) as w:
            pystats.nan_circmean(self.test_angles, **self.circ_kwargs)

        assert len(w) == 1
        assert w[0].category == DeprecationWarning

    def test_deprecation_warning_circstd(self):
        """Test if circstd in stats is deprecated"""

        import warnings

        warnings.simplefilter("always")
        with warnings.catch_warnings(record=True) as w:
            pystats.nan_circstd(self.test_angles, **self.circ_kwargs)

        assert len(w) == 1
        assert w[0].category == DeprecationWarning
