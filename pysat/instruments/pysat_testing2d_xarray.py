# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing.

.. deprecated:: 3.1.0
    This module has been renamed pysat_ndtesting.  A copy inheriting the
    routines from the new location is maintained here for backwards-
    compatibility. This instrument will be removed in 3.2.0+ to reduce
    redundancy.

"""

import datetime as dt
import functools
import numpy as np
import warnings

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test
from pysat.instruments import pysat_ndtesting

platform = 'pysat'
name = 'testing2d_xarray'

tags = pysat_ndtesting.tags
inst_ids = pysat_ndtesting.inst_ids
pandas_format = pysat_ndtesting.pandas_format
_test_dates = pysat_ndtesting._test_dates


# Init method
def init(self, test_init_kwarg=None):
    """Initialize the test instrument.

    Parameters
    ----------
    self : pysat.Instrument
        This object
    test_init_kwarg : any
        Testing keyword (default=None)

    """

    warnings.warn(" ".join(["The instrument module `pysat_testing2d_xarray`",
                            "has been deprecated and will be removed in",
                            "3.2.0+. Please use `pysat_ndtesting` instead."]),
                  DeprecationWarning, stacklevel=2)

    mm_test.init(self, test_init_kwarg=test_init_kwarg)
    return


# Clean method
clean = pysat_ndtesting.clean

# Optional method, preprocess
preprocess = pysat_ndtesting.preprocess

load = pysat_ndtesting.load

list_files = functools.partial(pysat_ndtesting.list_files,
                               test_dates=_test_dates)
list_remote_files = functools.partial(pysat_ndtesting.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(pysat_ndtesting.download)
