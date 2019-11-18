"""
tests the pysat utils.time area
"""
import numpy as np

from nose.tools import raises
import pandas as pds

from pysat.utils import time as pytime


###########
# getyrdoy

def test_getyrdoy_1():
    """Test the date to year, day of year code functionality"""

    date = pds.datetime(2009, 1, 1)
    yr, doy = pytime.getyrdoy(date)

    assert ((yr == 2009) & (doy == 1))


def test_getyrdoy_leap_year():
    """Test the date to year, day of year code functionality (leap_year)"""

    date = pds.datetime(2008, 12, 31)
    yr, doy = pytime.getyrdoy(date)

    assert ((yr == 2008) & (doy == 366))


#############
# parse_date

def test_parse_date_2_digit_year():
    """Test the ability to parse a str to produce a pandas datetime"""

    date = pytime.parse_date('14', '10', '31')

    assert date == pds.datetime(2014, 10, 31)


def test_parse_date_2_digit_year_last_century():
    """Test the ability to parse a str to produce a pandas datetime
    pre-2000"""

    date = pytime.parse_date('94', '10', '31', century=1900)

    assert date == pds.datetime(1994, 10, 31)


def test_parse_date_4_digit_year():
    """Test the ability to parse a str to produce a pandas datetime"""

    date = pytime.parse_date('1994', '10', '31')

    assert date == pds.datetime(1994, 10, 31)


@raises(ValueError)
def test_parse_date_bad_input():
    """Test the ability to idenitfy a non-physical date"""

    _ = pytime.parse_date('194', '15', '31')


############
# calc_freq

def test_calc_freq():
    """Test index frequency calculation"""

    tind = pytime.create_datetime_index(year=np.ones(shape=(4,))*2001,
                                        month=np.ones(shape=(4,)),
                                        uts=np.arange(0.0, 4.0, 1.0))
    freq = pytime.calc_freq(tind)

    assert freq.find("1S") == 0


def test_calc_freq_ns():
    """Test index frequency calculation with nanosecond output"""

    tind = pytime.create_datetime_index(year=np.ones(shape=(4,))*2001,
                                        month=np.ones(shape=(4,)),
                                        uts=np.arange(0.0, 0.04, .01))
    freq = pytime.calc_freq(tind)

    assert freq.find("10000000N") == 0


@raises(ValueError)
def test_calc_freq_len_fail():
    """Test index frequency calculation with empty list"""

    pytime.calc_freq(list())


@raises(AttributeError)
def test_calc_freq_type_fail():
    """Test index frequency calculation with non-datetime list"""

    pytime.calc_freq([1, 2, 3, 4])


####################
# create_date_range

def test_create_date_range():
    """Test ability to generate season list"""

    start = pds.datetime(2012, 2, 28)
    stop = pds.datetime(2012, 3, 1)
    season = pytime.create_date_range(start, stop, freq='D')

    assert season[0] == start
    assert season[-1] == stop
    assert len(season) == 3


def test_create_date_range_w_gaps():
    """Test ability to generate season list"""

    start = [pds.datetime(2012, 2, 28), pds.datetime(2013, 2, 28)]
    stop = [pds.datetime(2012, 3, 1), pds.datetime(2013, 3, 1)]
    season = pytime.create_date_range(start, stop, freq='D')

    assert season[0] == start[0]
    assert season[-1] == stop[-1]
    assert len(season) == 5


#########################
# create_datetime_index

def test_create_datetime_index():
    """Tests ability to create an array of datetime objects from distinct
    arrays of input paramters"""

    arr = np.ones(4)

    dates = pytime.create_datetime_index(year=2012*arr, month=2*arr,
                                         day=28*arr, uts=np.arange(0, 4))

    assert dates[0] == pds.datetime(2012, 2, 28)
    assert dates[-1] == pds.datetime(2012, 2, 28, 0, 0, 3)
    assert len(dates) == 4


@raises(ValueError)
def test_create_datetime_index_wo_year():
    """Must include a year"""

    _ = pytime.create_datetime_index()


def test_create_datetime_index_wo_month_day_uts():
    """Tests ability to generate missing paramters"""

    arr = np.ones(4)

    dates = pytime.create_datetime_index(year=2012*arr)

    assert dates[0] == pds.datetime(2012, 1, 1)
    assert dates[-1] == pds.datetime(2012, 1, 1)
    assert len(dates) == 4


def test_deprecated_season_date_range():
    """Tests that deprecation of season_date_range is working"""

    import warnings

    start = pds.datetime(2012, 2, 28)
    stop = pds.datetime(2012, 3, 1)
    warnings.simplefilter("always")
    with warnings.catch_warnings(record=True) as war1:
        season1 = pytime.create_date_range(start, stop, freq='D')
    with warnings.catch_warnings(record=True) as war2:
        season2 = pytime.season_date_range(start, stop, freq='D')

    assert len(season1) == len(season2)
    assert (season1 == season2).all()
    assert len(war1) == 0
    assert len(war2) == 1
    assert war2[0].category == DeprecationWarning
