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


class TestGetYearDay():
    """Unit tests for `getyrdoy`."""

    @pytest.mark.parametrize("date,tst_yr,tst_doy",
                             [(dt.datetime(2009, 1, 1), 2009, 1),
                              (dt.datetime(2008, 12, 31), 2008, 366)])
    def test_getyrdoy(self, date, tst_yr, tst_doy):
        """Test the date to year, day of year code function."""
        out_yr, out_doy = pytime.getyrdoy(date)

        assert tst_yr == out_yr, "wrong output year"
        assert tst_doy == out_doy, "wrong output day of year"
        return

    def test_getdyrdoy_bad_input(self):
        """Test getdyrdoy raises AttributeError for bad input object."""

        with pytest.raises(AttributeError) as aerr:
            pytime.getyrdoy(2009.1)

        assert str(aerr).find("Must supply a datetime object") >= 0
        return


class TestParseDate():
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
        """Test raises ValueError for unrealistic date input."""

        with pytest.raises(ValueError) as verr:
            pytime.parse_date(*in_args)

        assert str(verr).find(vmsg) >= 0
        return


class TestCalcFreqRes():
    """Unit tests for `calc_res`, `freq_to_res`, and `calc_freq`."""

    def setup(self):
        """Set up the unit test environment before each method."""
        self.year = np.full(shape=4, dtype=int, fill_value=2001)
        self.month = np.ones(shape=4, dtype=int)
        return

    def teardown(self):
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
    def test_calc_input_len_fail(self, func_name):
        """Test calc freq/res raises ValueError with an empty list."""
        test_func = getattr(pytime, func_name)

        with pytest.raises(ValueError) as verr:
            test_func(list())

        assert str(verr).find("insufficient data to calculate resolution") >= 0
        return

    @pytest.mark.parametrize('func_name', ['calc_freq', 'calc_res'])
    def test_calc_input_type_fail(self, func_name):
        """Test calc freq/res raises ValueError with non-datetime list."""
        test_func = getattr(pytime, func_name)

        with pytest.raises(AttributeError) as aerr:
            test_func([1, 2, 3, 4])

        assert str(aerr).find("Input should be times") >= 0
        return


class TestCreateDateRange():
    """Unit tests for `create_date_range`."""

    @pytest.mark.parametrize("start,stop,tst_len", [
        (dt.datetime(2012, 2, 28), dt.datetime(2012, 3, 1), 3),
        ([dt.datetime(2012, 2, 28), dt.datetime(2013, 2, 28)],
         [dt.datetime(2012, 3, 1), dt.datetime(2013, 3, 1)], 5)])
    def test_create_date_range(self, start, stop, tst_len):
        """Test ability to generate season list."""
        # Get the seasonal output
        season = pytime.create_date_range(start, stop, freq='D')

        # Get the testing start and stop times from the input
        tst_start = start[0] if hasattr(start, "__iter__") else start
        tst_stop = stop[-1] if hasattr(stop, "__iter__") else stop

        # Test the seasonal return values
        testing.assert_lists_equal([season[0], season[-1]],
                                   [tst_start, tst_stop])
        return


class TestCreateDatetimeIndex():
    """Unit test `create_datetime_index`."""

    def setup(self):
        """Set up the unit test environment before each method."""
        self.year = 2012 * np.ones(4)
        self.month = 2 * np.ones(4)
        self.day = 28 * np.ones(4)
        self.uts = np.arange(0, 4)
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        del self.year, self.month, self.day, self.uts
        return

    def test_create_datetime_index(self):
        """Test creation of an array of datetime objects from arrays of inputs.
        """

        dates = pytime.create_datetime_index(year=self.year, month=self.month,
                                             day=self.day, uts=self.uts)

        testing.assert_lists_equal([dates[0], dates[-1]],
                                   [dt.datetime(2012, 2, 28),
                                    dt.datetime(2012, 2, 28, 0, 0, 3)])
        return

    def test_create_datetime_index_wo_month_day_uts(self):
        """Test ability to generate missing parameters."""

        dates = pytime.create_datetime_index(year=self.year)

        testing.assert_lists_equal([dates[0], dates[-1]],
                                   [dt.datetime(2012, 1, 1),
                                    dt.datetime(2012, 1, 1)])
        return

    @pytest.mark.parametrize("in_args,err_msg", [
        ([[]], "Length of array must be larger than 0."),
        ([2009], "Must provide an iterable for all inputs.")])
    def test_create_datetime_index_bad_input(self, in_args, err_msg):
        """Test raises ValueError with inappropriate input parameters."""

        with pytest.raises(ValueError) as verr:
            pytime.create_datetime_index(*in_args)

        assert str(verr).find(err_msg) >= 0
        return


class TestFilterDatetimeInput():
    """Unit tests for `filter_datetime_input`."""

    def test_filter_datetime_input_none(self):
        """Test a successful `filter_datetime_input` with NoneType input."""

        self.in_date = None
        out_date = pytime.filter_datetime_input(None)
        assert out_date is None
        return

    def test_filter_datetime_input_datetime(self):
        """Test a successful `filter_datetime_input` with datetime input."""

        in_date = dt.datetime(2009, 1, 1, 1, 1)
        out_date = pytime.filter_datetime_input(in_date)
        assert out_date == dt.datetime(2009, 1, 1)
        return

    def test_filter_datetime_input_list(self):
        """Test a successful `filter_datetime_input` with list input."""

        in_date = [dt.datetime(2009, 1, 1, 1, 1)]
        out_date = pytime.filter_datetime_input(in_date)
        assert len(out_date) == len(in_date)
        assert out_date[0] == dt.datetime(2009, 1, 1)
        return

    def test_filter_datetime_input_array(self):
        """Test a successful `filter_datetime_input` with array input."""

        in_date = np.array([dt.datetime(2009, 1, 1, 1, 1)])
        out_date = pytime.filter_datetime_input(in_date)
        assert len(out_date) == len(in_date)
        assert out_date[0] == dt.datetime(2009, 1, 1)
        return
