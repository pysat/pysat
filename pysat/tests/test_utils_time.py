#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests for the pysat.utils.time functions."""

import datetime as dt
import numpy as np

import pytest

from pysat.utils import testing
from pysat.utils import time as pytime


class TestGetTimes(object):
    """Unit tests for datetime conversion functions."""

    @pytest.mark.parametrize("in_date,tst_yr,tst_doy",
                             [(dt.datetime(2009, 1, 1), 2009, 1),
                              (dt.datetime(2008, 12, 31), 2008, 366)])
    def test_getyrdoy(self, in_date, tst_yr, tst_doy):
        """Test the date to year, day of year code function.

        Parameters
        ----------
        in_date : dt.datetime
            Datetime object
        tst_year : int
            Decimal year
        tst_doy : int
            Decimal day of year

        """
        out_yr, out_doy = pytime.getyrdoy(in_date)

        assert tst_yr == out_yr, "wrong output year"
        assert tst_doy == out_doy, "wrong output day of year"
        return

    def test_getdyrdoy_bad_input(self):
        """Test getdyrdoy raises AttributeError for bad input object."""

        testing.eval_bad_input(pytime.getyrdoy, AttributeError,
                               "Must supply a datetime object", [2009.1])
        return

    @pytest.mark.parametrize("in_dtime,out_year",
                             [(dt.datetime(2009, 1, 1), 2009.0),
                              (dt.datetime(2008, 12, 31, 23, 59, 59),
                               2008.9999999683768469)])
    def test_datetime_to_dec_year(self, in_dtime, out_year):
        """Test the datetime to decimal year function.

        Parameters
        ----------
        in_dtime : dt.datetime
            Datetime object
        out_year : float
            Decimal year

        """

        test_year = pytime.datetime_to_dec_year(in_dtime)

        assert test_year == out_year
        return


class TestParseDate(object):
    """Unit tests for parse_date."""

    @pytest.mark.parametrize("in_args,in_kwargs,tst_date", [
        (['14', '10', '31'], {}, dt.datetime(2014, 10, 31)),
        (['94', '10', '31'], {'century': 1900}, dt.datetime(1994, 10, 31)),
        (['1894', '10', '31'], {}, dt.datetime(1894, 10, 31))])
    def test_parse_date_2_digit_year(self, in_args, in_kwargs, tst_date):
        """Test the ability to parse a str to produce a datetime object."""

        out_date = pytime.parse_date(*in_args, **in_kwargs)

        assert out_date == tst_date
        return

    @pytest.mark.parametrize("in_args,vmsg", [
        (["0", "12", "15"], "year 0 is out of range"),
        (["10", "15", "15"], "month must be in 1..12"),
        (['10', '12', '55'], "day is out of range for month"),
        (['10', '12', '15', '33'], "hour must be in 0..23"),
        (['10', '12', '15', '3', '70'], "minute must be in 0..59"),
        (['10', '12', '15', '3', '1', '68'], "second must be in 0..59"),
        (['10', '12', '15', '3', '1', '55', -30], "year -20 is out of range")])
    def test_parse_date_bad_input(self, in_args, vmsg):
        """Test raises ValueError for unrealistic date input.

        Parameters
        ----------
        in_args : list
            List of input arguments
        vmsg : str
            Expected output error message

        """

        testing.eval_bad_input(pytime.parse_date, ValueError, vmsg, in_args)
        return


class TestCalcFreqRes(object):
    """Unit tests for `calc_res`, `freq_to_res`, and `calc_freq`."""

    def setup_method(self):
        """Set up the unit test environment before each method."""
        self.year = np.full(shape=4, dtype=int, fill_value=2001)
        self.month = np.ones(shape=4, dtype=int)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        del self.year, self.month
        return

    @pytest.mark.parametrize('trange,freq_out',
                             [(np.arange(0.0, 4.0, 1.0), '1S'),
                              (np.arange(0.0, 0.04, .01), '10000000N')])
    def test_calc_freq(self, trange, freq_out):
        """Test index frequency calculation."""

        tind = pytime.create_datetime_index(year=self.year, month=self.month,
                                            uts=trange)
        freq = pytime.calc_freq(tind)

        assert freq.find(freq_out) == 0
        return

    @pytest.mark.parametrize('freq_in,res_out',
                             [('S', 1.0), ('2D', 172800.0),
                              ('10000000N', 0.01)])
    def test_freq_to_res(self, freq_in, res_out):
        """Test index frequency to resolution calculation."""
        res = pytime.freq_to_res(freq_in)

        assert res == res_out
        return

    @pytest.mark.parametrize('use_mean', [True, False])
    def test_calc_res_mean_flag(self, use_mean):
        """Test index frequency calculation."""
        # Set the input and output comparison
        tind = [dt.datetime(self.year[0], self.month[0], 1,
                            i if i < 3 else i + 1)
                for i in range(len(self.year))]
        out_res = 4800.0 if use_mean else 3600.0

        # Get and test the output resolution
        res = pytime.calc_res(tind, use_mean=use_mean)
        assert res == out_res
        return

    @pytest.mark.parametrize('func_name', ['calc_freq', 'calc_res'])
    @pytest.mark.parametrize('in_args, error, err_msg', [
        ([[]], ValueError, "insufficient data to calculate resolution"),
        ([[1, 2, 3, 4]], AttributeError, "Input should be times")])
    def test_calc_input_failure(self, func_name, in_args, error, err_msg):
        """Test calc freq/res raises apppropriate errors with bad inputs.

        Parameters
        ----------
        func_name : str
            Function name
        in_args : list
            Input arguments as a list
        error : exception
            Expected error type
        err_msg : str
            Expected error message

        """
        func = getattr(pytime, func_name)
        testing.eval_bad_input(func, error, err_msg, input_args=in_args)
        return


class TestCreateDateRange(object):
    """Unit tests for `create_date_range`."""

    @pytest.mark.parametrize("start,stop,tst_len", [
        (dt.datetime(2012, 2, 28), dt.datetime(2012, 3, 1), 3),
        ([dt.datetime(2012, 2, 28), dt.datetime(2013, 2, 28)],
         [dt.datetime(2012, 3, 1), dt.datetime(2013, 3, 1)], 5)])
    def test_create_date_range(self, start, stop, tst_len):
        """Test ability to generate season list.

        Parameters
        ----------
        start : dt.datetime
            Start time
        stop : dt.datetime
            End time
        tst_len : int
            Expected number of times in output

        """
        # Get the seasonal output
        season = pytime.create_date_range(start, stop, freq='D')

        # Get the testing start and stop times from the input
        tst_start = start[0] if hasattr(start, "__iter__") else start
        tst_stop = stop[-1] if hasattr(stop, "__iter__") else stop

        # Test the seasonal return values
        testing.assert_lists_equal([season[0], season[-1]],
                                   [tst_start, tst_stop])
        return


class TestCreateDatetimeIndex(object):
    """Unit test `create_datetime_index`."""

    def setup_method(self):
        """Set up the unit test environment before each method."""
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        return

    @pytest.mark.parametrize("kwargs, target",
                             [({'year': 2012 * np.ones(4),
                                'month': 2 * np.ones(4),
                                'day': 28 * np.ones(4),
                                'uts': np.arange(0, 4)},
                              [dt.datetime(2012, 2, 28),
                               dt.datetime(2012, 2, 28, 0, 0, 3)]),
                              ({'year': 2012 * np.ones(4),
                                'day': 366 * np.ones(4),
                                'uts': np.arange(0, 4)},
                               [dt.datetime(2012, 12, 31),
                                dt.datetime(2012, 12, 31, 0, 0, 3)]),
                              ({'year': [2012, 2012, 2012, 2008],
                                'day': 366 * np.ones(4),
                                'uts': np.arange(0, 4)},
                               [dt.datetime(2012, 12, 31),
                                dt.datetime(2008, 12, 31, 0, 0, 3)]),
                              ({'year': 2012 * np.ones(4)},
                               [dt.datetime(2012, 1, 1),
                                dt.datetime(2012, 1, 1)])])
    def test_create_datetime_index(self, kwargs, target):
        """Test create an array of datetime objects from arrays of inputs.

        Parameters
        ----------
        kwargs : dict
            Input kwargs
        target : list
            Expected output

        """

        dates = pytime.create_datetime_index(**kwargs)

        testing.assert_lists_equal([dates[0], dates[-1]], target)
        return

    @pytest.mark.parametrize("in_args,err_msg", [
        ([[]], "Length of array must be larger than 0."),
        ([2009], "Must provide an iterable for all inputs.")])
    def test_create_datetime_index_bad_input(self, in_args, err_msg):
        """Test raises ValueError with inappropriate input parameters.

        Parameters
        ----------
        in_args : list
            List of input arguments
        err_msg : str
            Expected error message

        """

        testing.eval_bad_input(pytime.create_datetime_index, ValueError,
                               err_msg, in_args)
        return


class TestFilterDatetimeInput(object):
    """Unit tests for `filter_datetime_input`."""

    def test_filter_datetime_input_none(self):
        """Test a successful `filter_datetime_input` with NoneType input."""

        self.in_date = None
        out_date = pytime.filter_datetime_input(None)
        assert out_date is None
        return

    @pytest.mark.parametrize("in_time, islist",
                             [(dt.datetime.utcnow(), False),
                              (dt.datetime(2010, 1, 1, 12, tzinfo=dt.timezone(
                                  dt.timedelta(seconds=14400))), False),
                              ([dt.datetime(2010, 1, 1, 12, i,
                                            tzinfo=dt.timezone(
                                                dt.timedelta(seconds=14400)))
                                for i in range(3)], True)])
    def test_filter_datetime(self, in_time, islist):
        """Test range of allowed inputs for the Instrument datetime filter.

        Parameters
        ----------
        in_time : dt.datetime or list-like
            Input time
        islist : bool
            Boolean flag to indicate if `in_time` a list.

        """

        # Because the input datetime is the middle of the day and the offset
        # is four hours, the reference date and input date are the same
        if islist:
            self.ref_time = [dt.datetime(tt.year, tt.month, tt.day)
                             for tt in in_time]
            self.out = pytime.filter_datetime_input(in_time)
        else:
            self.ref_time = [dt.datetime(in_time.year, in_time.month,
                                         in_time.day)]
            self.out = [pytime.filter_datetime_input(in_time)]

        # Test for the date values and timezone awareness status
        for i, tt in enumerate(self.out):
            assert tt == self.ref_time[i], \
                "Filtered time has changed dates."
            assert tt.tzinfo is None, \
                "Filtered timezone was not removed at value {:d}.".format(i)
        return
