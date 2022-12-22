"""Unit tests for the `pysat.Instrument.index` attribute."""

import datetime as dt
from importlib import reload

import pytest

import pysat
from pysat.utils import testing


class TestMalformedIndex(object):
    """Unit tests for pandas `pysat.Instrument` with malformed index."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True,
                                         use_header=True)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy
        return

    def test_ensure_unique_index(self):
        """Ensure that if Instrument index not-unique error is raised."""

        testing.eval_bad_input(self.testInst.load, ValueError,
                               'Loaded data is not unique.',
                               input_args=[self.ref_time.year, self.ref_doy])
        return


class TestMalformedIndexXArray(TestMalformedIndex):
    """Basic tests for xarray `pysat.Instrument` with shifted file dates."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True,
                                         use_header=True)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy
        return
