"""Tests the `pysat.instruments.methods.testing` methods."""

import datetime as dt
from os import path
import pandas as pds
import pytest

import pysat
from pysat.instruments.methods import testing as mm_test


class TestBasics(object):
    """Unit tests for testing methods."""

    def setup(self):
        """Set up the unit test environment for each method."""

        self.test_inst = pysat.Instrument('pysat', 'testing')
        # get list of filenames.
        self.fnames = [self.test_inst.files.files.values[0]]
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.test_inst, self.fnames
        return

    @pytest.mark.parametrize("kwarg", [0.0, 7, 'badval', {'hours': 'bad'},
                                       dt.datetime(2009, 1, 1)])
    def test_inst_start_time_badval(self, kwarg):
        """Test operation of cadence keyword, including default behavior."""

        with pytest.raises(ValueError) as verr:
            mm_test.generate_times(self.fnames, 10, start_time=kwarg)
        assert str(verr).find("start_time must be a dt.timedelta object") >= 0
        return

    @pytest.mark.parametrize("num,kwargs,output",
                             [(10, None, [0.0, 9.0]),
                              (10, {'start_time': dt.timedelta(hours=1)},
                               [3600.0, 3609.0]),
                              (10, {'start_time': dt.timedelta(hours=1),
                                    'freq': '10s'},
                               [3600.0, 3690.0]),
                              (87000, {}, [0.0, 86399.0])])
    def test_generate_times_kwargs(self, num, kwargs, output):
        """Test use of kwargs in generate_times, including default behavior."""

        if kwargs:
            uts, index, dates = mm_test.generate_times(self.fnames, num,
                                                       **kwargs)
        else:
            uts, index, dates = mm_test.generate_times(self.fnames, num)

        assert uts[0] == output[0]
        assert uts[-1] == output[1]
        assert len(uts) == len(index)
        assert len(dates) == 1
        # Check that calculations are done correctly.
        delta_time = [dt.timedelta(seconds=sec) for sec in uts]
        assert (index.to_pydatetime() - delta_time == dates).all
        return
