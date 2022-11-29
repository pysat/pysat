# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing.

.. deprecated:: 3.0.2
    All data present in this instrument is duplicated in pysat_ndtesting.
    This instrument will be removed in 3.2.0+ to reduce redundancy.

"""

import datetime as dt
import functools
import numpy as np
import warnings

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

# pysat required parameters
platform = 'pysat'
name = 'testing_xarray'

# Dictionary of data 'tags' and corresponding description
tags = {'': 'Regular testing data set'}

# Dictionary of satellite IDs, list of corresponding tags
inst_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}
pandas_format = False

epoch_name = u'time'


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

    warnings.warn(" ".join(["The instrument module `pysat_testing_xarray` has",
                            "been deprecated and will be removed in 3.2.0+."]),
                  DeprecationWarning, stacklevel=2)

    mm_test.init(self, test_init_kwarg=test_init_kwarg)
    return


# Clean method
clean = mm_test.clean

# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag='', inst_id='', sim_multi_file_right=False,
         sim_multi_file_left=False, malformed_index=False,
         start_time=None, num_samples=86400, test_load_kwarg=None,
         max_latitude=90.):
    """Load the test files.

    Parameters
    ----------
    fnames : list
        List of filenames.
    tag : str
        Tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    inst_id : str
        Instrument ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    sim_multi_file_right : bool
        Adjusts date range to be 12 hours in the future or twelve hours beyond
        `root_date`. (default=False)
    sim_multi_file_left : bool
        Adjusts date range to be 12 hours in the past or twelve hours before
        `root_date`. (default=False)
    malformed_index : bool
        If True, time index will be non-unique and non-monotonic.
    start_time : dt.timedelta or NoneType
        Offset time of start time since midnight UT. If None, instrument data
        will begin at midnight. (default=None)
    num_samples : int
        Maximum number of times to generate.  Data points will not go beyond the
        current day. (default=86400)
    test_load_kwarg : any
        Keyword used for pysat unit testing to ensure that functionality for
        custom keywords defined in instrument support functions is working
        correctly. (default=None)
    max_latitude : float
        Latitude simulated as `max_latitude` * cos(theta(t))`, where
        theta is a linear periodic signal bounded by [0, 2 * pi). (default=90.)

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Metadata

    """

    # Support keyword testing
    pysat.logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # Create an artificial satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()

    uts, index, dates = mm_test.generate_times(fnames, num_samples, freq='1S',
                                               start_time=start_time)

    if sim_multi_file_right:
        root_date = dt.datetime(2009, 1, 1, 12)
    elif sim_multi_file_left:
        root_date = dt.datetime(2008, 12, 31, 12)
    else:
        root_date = dt.datetime(2009, 1, 1)

    if malformed_index:
        index = index.tolist()

        # Create a non-monotonic index
        index[0:3], index[3:6] = index[3:6], index[0:3]

        # Create a non-unique index
        index[6:9] = [index[6]] * 3

    data = xr.Dataset({'uts': ((epoch_name), uts)},
                      coords={epoch_name: index})

    # Need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day. Figure out how far in time from
    # the root start a measurement is and use that info to create a signal
    # that is continuous from that start. Going to presume there are 5820
    # seconds per orbit (97 minute period).
    time_delta = dates[0] - root_date
    mlt = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['mlt'] = ((epoch_name), mlt)

    # SLT, 20 second offset from `mlt`.
    slt = mm_test.generate_fake_data(time_delta.total_seconds() + 20, uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['slt'] = ((epoch_name), slt)

    # Create a fake longitude, resets every 6240 seconds. Sat moves at
    # 360/5820 deg/s, Earth rotates at 360/86400, takes extra time to go
    # around full longitude.
    longitude = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                           period=iperiod['lon'],
                                           data_range=drange['lon'])
    data['longitude'] = ((epoch_name), longitude)

    # Create latitude area for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                       period=iperiod['angle'],
                                       data_range=drange['angle'])
    latitude = max_latitude * np.cos(angle)
    data['latitude'] = ((epoch_name), latitude)

    # Create constant altitude at 400 km
    alt0 = 400.0
    altitude = alt0 * np.ones(data['latitude'].shape)
    data['altitude'] = ((epoch_name), altitude)

    # Fake orbit number
    fake_delta = dates[0] - dt.datetime(2008, 1, 1)
    orbit_num = mm_test.generate_fake_data(fake_delta.total_seconds(),
                                           uts, period=iperiod['lt'],
                                           cyclic=False)

    data['orbit_num'] = ((epoch_name), orbit_num)

    # Create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int).data
    long_int = (data['longitude'] / 15.).astype(int).data
    data['dummy1'] = ((epoch_name), mlt_int)
    data['dummy2'] = ((epoch_name), long_int)
    data['dummy3'] = ((epoch_name), mlt_int + long_int * 1000.)
    data['dummy4'] = ((epoch_name), uts)
    data['string_dummy'] = ((epoch_name),
                            ['test'] * len(data.indexes[epoch_name]))
    data['unicode_dummy'] = ((epoch_name),
                             [u'test'] * len(data.indexes[epoch_name]))
    data['int8_dummy'] = ((epoch_name),
                          np.ones(len(data.indexes[epoch_name]), dtype=np.int8))
    data['int16_dummy'] = ((epoch_name),
                           np.ones(len(data.indexes[epoch_name]),
                                   dtype=np.int16))
    data['int32_dummy'] = ((epoch_name),
                           np.ones(len(data.indexes[epoch_name]),
                                   dtype=np.int32))
    data['int64_dummy'] = ((epoch_name),
                           np.ones(len(data.indexes[epoch_name]),
                                   dtype=np.int64))

    # Set the meta data
    meta = mm_test.initialize_test_meta(epoch_name, data.keys())
    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
