"""
tests the pysat utils.time area
"""
import datetime as dt
import numpy as np

import pytest

from pysat.utils import time as pytime


class TestGetYearDay():

    def test_getyrdoy_1(self):
        """Test the date to year, day of year code functionality"""

        date = dt.datetime(2009, 1, 1)
        yr, doy = pytime.getyrdoy(date)

        assert ((yr == 2009) & (doy == 1))

    def test_getyrdoy_leap_year(self):
        """Test the date to year, day of year code functionality (leap_year)"""

        date = dt.datetime(2008, 12, 31)
        yr, doy = pytime.getyrdoy(date)

        assert ((yr == 2008) & (doy == 366))


class TestParseDate():

    def test_parse_date_2_digit_year(self):
        """Test the ability to parse a str to produce a pandas datetime"""

        date = pytime.parse_date('14', '10', '31')

        assert date == dt.datetime(2014, 10, 31)

    def test_parse_date_2_digit_year_last_century(self):
        """Test the ability to parse a str to produce a pandas datetime
        pre-2000"""

        date = pytime.parse_date('94', '10', '31', century=1900)

        assert date == dt.datetime(1994, 10, 31)

    def test_parse_date_4_digit_year(self):
        """Test the ability to parse a str to produce a pandas datetime"""

        date = pytime.parse_date('1994', '10', '31')

        assert date == dt.datetime(1994, 10, 31)

    def test_parse_date_bad_input(self):
        """Test the ability to identify a non-physical date"""

        with pytest.raises(ValueError):
            _ = pytime.parse_date('194', '15', '31')


class TestCalcFreq():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.year = np.ones(4) * 2001
        self.month = np.ones(4) * 1

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.year, self.month

    def test_calc_freq(self):
        """Test index frequency calculation"""

        tind = pytime.create_datetime_index(year=self.year,
                                            month=self.month,
                                            uts=np.arange(0.0, 4.0, 1.0))
        freq = pytime.calc_freq(tind)

        assert freq.find("1S") == 0

    def test_calc_freq_ns(self):
        """Test index frequency calculation with nanosecond output"""

        tind = pytime.create_datetime_index(year=self.year,
                                            month=self.month,
                                            uts=np.arange(0.0, 0.04, .01))
        freq = pytime.calc_freq(tind)

        assert freq.find("10000000N") == 0

    def test_calc_freq_len_fail(self):
        """Test index frequency calculation with empty list"""

        with pytest.raises(ValueError):
            pytime.calc_freq(list())

    def test_calc_freq_type_fail(self):
        """Test index frequency calculation with non-datetime list"""

        with pytest.raises(AttributeError):
            pytime.calc_freq([1, 2, 3, 4])


class TestCreateDateRange():

    def test_create_date_range(self):
        """Test ability to generate season list"""

        start = dt.datetime(2012, 2, 28)
        stop = dt.datetime(2012, 3, 1)
        season = pytime.create_date_range(start, stop, freq='D')

        assert season[0] == start
        assert season[-1] == stop
        assert len(season) == 3

    def test_create_date_range_w_gaps(self):
        """Test ability to generate season list"""

        start = [dt.datetime(2012, 2, 28), dt.datetime(2013, 2, 28)]
        stop = [dt.datetime(2012, 3, 1), dt.datetime(2013, 3, 1)]
        season = pytime.create_date_range(start, stop, freq='D')

        assert season[0] == start[0]
        assert season[-1] == stop[-1]
        assert len(season) == 5


class TestCreateDatetimeIndex():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.year = 2012 * np.ones(4)
        self.month = 2 * np.ones(4)
        self.day = 28 * np.ones(4)
        self.uts = np.arange(0, 4)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.year, self.month, self.day, self.uts

    def test_create_datetime_index(self):
        """Tests ability to create an array of datetime objects from distinct
        arrays of input parameters"""

        dates = pytime.create_datetime_index(year=self.year, month=self.month,
                                             day=self.day, uts=self.uts)

        assert dates[0] == dt.datetime(2012, 2, 28)
        assert dates[-1] == dt.datetime(2012, 2, 28, 0, 0, 3)
        assert len(dates) == 4

    def test_create_datetime_index_wo_year(self):
        """Must include a year"""

        with pytest.raises(ValueError):
            _ = pytime.create_datetime_index()

    def test_create_datetime_index_wo_month_day_uts(self):
        """Tests ability to generate missing parameters"""

        dates = pytime.create_datetime_index(year=self.year)

        assert dates[0] == dt.datetime(2012, 1, 1)
        assert dates[-1] == dt.datetime(2012, 1, 1)
        assert len(dates) == 4
