# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing."""

import datetime as dt
import functools
import numpy as np

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

logger = pysat.logger

platform = 'pysat'
name = 'testmodel'
tags = {'': 'Regular testing data set'}
inst_ids = {'': ['']}
pandas_format = False
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}


# Init method
init = mm_test.init


# Clean method
clean = mm_test.clean


# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag=None, inst_id=None, start_time=None, num_samples=96,
         test_load_kwarg=None):
    """Load the test files.

    Parameters
    ----------
    fnames : list
        List of filenames
    tag : str or NoneType
        Instrument tag (accepts '')
    inst_id : str or NoneType
        Instrument satellite ID (accepts '')
    start_time : dt.timedelta or NoneType
        Offset time of start time since midnight UT. If None, instrument data
        will begin at midnight.
        (default=None)
    num_samples : int
        Maximum number of times to generate.  Data points will not go beyond the
        current day. (default=96)
    test_load_kwarg : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Metadata

    """

    # Support keyword testing
    logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # create an artifical model data set
    uts, index, dates = mm_test.generate_times(fnames, num_samples, freq='900S',
                                               start_time=start_time)

    # Define range of simulated 3D model
    latitude = np.linspace(-50, 50, 21)
    longitude = np.linspace(0, 360, 73)
    altitude = np.linspace(300, 500, 41)
    data = xr.Dataset({'uts': (('time'), np.mod(uts, 86400.))},
                      coords={'time': index, 'latitude': latitude,
                              'longitude': longitude, 'altitude': altitude})

    slt = np.zeros([len(uts), len(longitude)])
    for i, ut in enumerate(uts):
        for j, long in enumerate(longitude):
            slt[i, j] = np.mod(ut / 3600.0 + long / 15.0, 24.0)
    data['slt'] = (('time', 'longitude'), slt)
    data['mlt'] = (('time', 'longitude'), np.mod(slt + 0.2, 24.0))

    # Fake 3D data consisting of non-physical values between 0 and 21 everywhere
    # Used for interpolation routines in pysatModels
    dummy1 = np.mod(data['uts'] * data['latitude'] * data['longitude'], 21.0)
    data['dummy1'] = (('time', 'latitude', 'longitude'), dummy1.data)

    # Fake 4D data consisting of non-physical values between 0 and 21 everywhere
    # Used for interpolation routines in pysatModels
    dummy2 = np.mod(data['dummy1'] * data['altitude'], 21.0)
    data['dummy2'] = (('time', 'latitude', 'longitude', 'altitude'),
                      dummy2.data)

    # Set the meta data.
    meta = mm_test.initialize_test_meta('time', data.keys())
    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
