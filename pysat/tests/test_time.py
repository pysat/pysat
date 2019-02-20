"""
tests the pysat utils.time area
"""
import numpy as np
import pandas as pds
import nose.tools
from nose.tools import assert_raises, raises
import pysat
from pysat.utils import time as pytime


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


def test_calc_freq(self):
    """Test index frequency calculation"""

    self.testInst.load(2009, 1)
    self.testInst.index.freq = pytime.calc_freq(self.testInst.index)

    assert self.testInst.index.freq.freqstr.find("S") == 0


def test_calc_freq_ns(self):
    """Test index frequency calculation with nanosecond output"""

    tind = pytime.create_datetime_index(year=np.ones(shape=(4,))*2001,
                                        month=np.ones(shape=(4,)),
                                        uts=np.arange(0.0, 0.04, .01))
    freq = pytime.calc_freq(tind)

    assert freq.find("10000000N") == 0


def test_calc_freq_len_fail(self):
    """Test index frequency calculation with empty list"""

    assert_raises(ValueError, pytime.calc_freq, list())


def test_calc_freq_type_fail(self):
    """Test index frequency calculation with non-datetime list"""

    assert_raises(AttributeError, pytime.calc_freq, [1, 2, 3, 4])
