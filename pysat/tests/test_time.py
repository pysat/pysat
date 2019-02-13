"""
tests the pysat utils.time area
"""
import os
import numpy as np
import pandas as pds
import nose.tools
from nose.tools import assert_raises, raises
import tempfile
import pysat
import pysat.instruments.pysat_testing


#-------------------
# basic yrdoy tests
def test_getyrdoy_1():
    """Test the date to year, day of year code functionality"""
    date = pds.datetime(2009, 1, 1)
    yr, doy = pysat.utils.time.getyrdoy(date)
    assert ((yr == 2009) & (doy == 1))

def test_getyrdoy_leap_year():
    """Test the date to year, day of year code functionality (leap_year)"""
    date = pds.datetime(2008,12,31)
    yr, doy = pysat.utils.time.getyrdoy(date)
    assert ((yr == 2008) & (doy == 366))
