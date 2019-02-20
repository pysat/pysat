"""
tests the pysat utils.stats area
"""
import os
import numpy as np
import pandas as pds
import nose.tools
from nose.tools import assert_raises, raises
import tempfile
import pysat
import pysat.instruments.pysat_testing
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
        from scipy import stats as scistats

        ref_mean = scistats.circmean(self.test_angles, **self.circ_kwargs)
        test_mean = pystats.nan_circmean(self.test_angles, **self.circ_kwargs)
        ans1 = ref_mean == test_mean

        assert ans1

    def test_circstd_nan(self):
        """ Test custom circular mean with NaN."""
        from scipy import stats as scistats

        ref_mean = scistats.circmean(self.test_angles, **self.circ_kwargs)
        ref_nan = scistats.circmean(self.test_nan, **self.circ_kwargs)
        test_nan = pystats.nan_circmean(self.test_nan, **self.circ_kwargs)

        assert np.isnan(ref_nan)
        assert ref_mean == test_nan

    def test_circstd(self):
        """ Test custom circular std."""
        from scipy import stats as scistats

        ref_std = scistats.circstd(self.test_angles, **self.circ_kwargs)
        test_std = pystats.nan_circstd(self.test_angles, **self.circ_kwargs)
        ans1 = ref_std == test_std

        assert ans1

    def test_circstd_nan(self):
        """ Test custom circular std with NaN."""
        from scipy import stats as scistats

        ref_std = scistats.circstd(self.test_angles, **self.circ_kwargs)
        ref_nan = scistats.circstd(self.test_nan, **self.circ_kwargs)
        test_nan = pystats.nan_circstd(self.test_nan, **self.circ_kwargs)

        assert np.isnan(ref_nan)
        assert ref_std == test_nan
