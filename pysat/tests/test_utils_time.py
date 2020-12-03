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

    @pytest.mark.parametrize("yr, mo, dy, cen, ref_dtime",
                             [("14", "10", "31", 2000,
                               dt.datetime(2014, 10, 31,
                                           tzinfo=dt.timezone.utc)),
                              ("94", "10", "31", 1800,
                               dt.datetime(1894, 10, 31,
                                           tzinfo=dt.timezone.utc)),
                              ("94", "10", "31", 1900,
                               dt.datetime(1994, 10, 31,
                                           tzinfo=dt.timezone.utc)),
                              ("1994", "10", "31", 2000,
                               dt.datetime(1994, 10, 31,
                                           tzinfo=dt.timezone.utc))])
    def test_parse_date_success(self, yr, mo, dy, cen, ref_dtime):
        """Test the ability to parse a str to get a valid datetime
        """

        date = pytime.parse_date(yr, mo, dy, century=cen)

        assert date == ref_dtime

    def test_parse_date_bad_input(self):
        """Test raises ValueError when identifying a date before the space age
        """

        with pytest.raises(ValueError):
            pytime.parse_date('194', '15', '31')


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

        assert dates[0] == dt.datetime(2012, 2, 28, tzinfo=dt.timezone.utc)
        assert dates[-1] == dt.datetime(2012, 2, 28, 0, 0, 3,
                                        tzinfo=dt.timezone.utc)
        assert len(dates) == 4

    def test_create_datetime_index_wo_year(self):
        """Must include a year"""

        with pytest.raises(ValueError):
            _ = pytime.create_datetime_index()

    def test_create_datetime_index_wo_month_day_uts(self):
        """Tests ability to generate missing parameters"""

        dates = pytime.create_datetime_index(year=self.year)

        assert dates[0] == dt.datetime(2012, 1, 1, tzinfo=dt.timezone.utc)
        assert dates[-1] == dt.datetime(2012, 1, 1, tzinfo=dt.timezone.utc)
        assert len(dates) == 4


class TestSetTimezone():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.ttime = dt.datetime(2010, 1, 1)
        self.timezone = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.ttime, self.timezone

    def update_test_time(self):
        """ Update the test time using the timezone attribute
        """
        if self.timezone is not None:
            self.timezone = self.timezone.upper()

            if self.timezone == "UTC":
                self.ttime = self.ttime.astimezone(tz=dt.timezone.utc)
            else:
                tzone = dt.timezone(dt.timedelta(hours=int(self.timezone)))
                self.ttime = self.ttime.astimezone(tz=tzone)

        return

    @pytest.mark.parametrize("in_tz, naive_is_utc",
                             [(None, True), ("UTC", True), ("UTC", False),
                              ("2", True), ("2", False)])
    def test_set_timezone_to_utc_success(self, in_tz, naive_is_utc):
        """Test successful setting of UTC datetime data
        """

        # Set the input time and get the utc_time
        self.timezone = in_tz
        self.update_test_time()
        utc_time = pytime.set_timezone_to_utc(self.ttime, naive_is_utc)

        # Assert that the output is a datetime object
        assert isinstance(utc_time, dt.datetime)

        # Assert that the output is aware
        assert utc_time.tzinfo is not None
        assert utc_time.tzinfo.utcoffset is not None

        # Assert that the output timezone is UTC
        assert utc_time.tzinfo.utcoffset(utc_time).total_seconds() == 0.0

    def test_set_timezone_to_utc_failure(self):
        """Test raises TypeError if input type is naive and needs to be aware
        """

        with pytest.raises(TypeError) as terr:
            pytime.set_timezone_to_utc(self.ttime, naive_is_utc=False)

        assert "datetime input is naive" in str(terr.value)
