"""Unit tests for the `pysat.Instrument.index` attribute."""

import datetime as dt
from importlib import reload

import pytest

import pysat


class TestMalformedIndex(object):
    """Unit tests for pandas `pysat.Instrument` with malformed index."""

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy
        return

    def test_ensure_unique_index(self):
        """Ensure that if Instrument index not-unique error is raised."""

        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, self.ref_doy)
        estr = 'Loaded data is not unique.'
        assert str(err).find(estr) > 0
        return


class TestMalformedIndexXarray(TestMalformedIndex):
    """Basic tests for xarray `pysat.Instrument` with shifted file dates."""

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy
        return
