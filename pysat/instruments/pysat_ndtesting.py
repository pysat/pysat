# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing."""

import datetime as dt
import functools
import numpy as np

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

platform = 'pysat'
name = 'ndtesting'

pandas_format = False
tags = {'': 'Regular testing data set'}
inst_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}

epoch_name = u'time'

# Init method
init = mm_test.init

# Clean method
clean = mm_test.clean

# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag='', inst_id='', malformed_index=False,
         start_time=None, num_samples=864, test_load_kwarg=None,
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
    malformed_index : bool
        If True, the time index will be non-unique and non-monotonic.
        (default=False)
    start_time : dt.timedelta or NoneType
        Offset time of start time since midnight UT. If None, instrument data
        will begin at midnight. (default=None)
    num_samples : int
        Maximum number of times to generate.  Data points will not go beyond the
        current day. (default=864)
    test_load_kwarg : any
        Keyword used for pysat unit testing to ensure that functionality for
        custom keywords defined in instrument support functions is working
        correctly. (default=None)
    max_latitude : float
        Latitude simulated as `max_latitude` * cos(theta(t))`, where
        theta is a linear periodic signal bounded by [0, 2 * pi) (default=90.).

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Testing metadata

    """

    # Support keyword testing
    pysat.logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # Create an artificial satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()

    # Using 100s frequency for compatibility with seasonal analysis unit tests
    uts, index, dates = mm_test.generate_times(fnames, num_samples, freq='100S',
                                               start_time=start_time)

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
    time_delta = dates[0] - dt.datetime(2009, 1, 1)

    # MLT runs 0-24 each orbit
    mlt = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['mlt'] = ((epoch_name), mlt)

    # SLT, 20 second offset from `mlt`.
    slt = mm_test.generate_fake_data(time_delta.total_seconds() + 20, uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['slt'] = ((epoch_name), slt)

    # Create a fake satellite longitude, resets every 6240 seconds.
    # Satellite moves at 360/5820 deg/s, Earth rotates at 360/86400, takes
    # extra time to go around full longitude.
    longitude = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                           period=iperiod['lon'],
                                           data_range=drange['lon'])
    data['longitude'] = ((epoch_name), longitude)

    # Create fake satellite latitude for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                       period=iperiod['angle'],
                                       data_range=drange['angle'])
    latitude = max_latitude * np.cos(angle)
    data['latitude'] = ((epoch_name), latitude)

    # Create constant altitude at 400 km for a satellite that has yet
    # to experience orbital decay
    alt0 = 400.0
    altitude = alt0 * np.ones(data['latitude'].shape)
    data['altitude'] = ((epoch_name), altitude)

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

    # Add dummy coords
    data.coords['x'] = (('x'), np.arange(17))
    data.coords['y'] = (('y'), np.arange(17))
    data.coords['z'] = (('z'), np.arange(15))

    # Create altitude 'profile' at each location to simulate remote data
    num = len(data['uts'])
    data['profiles'] = (
        (epoch_name, 'profile_height'),
        data['dummy3'].values[:, np.newaxis] * np.ones((num, 15)))
    data.coords['profile_height'] = ('profile_height', np.arange(15))

    # Profiles that could have different altitude values
    data['variable_profiles'] = (
        (epoch_name, 'z'), data['dummy3'].values[:, np.newaxis]
        * np.ones((num, 15)))
    data.coords['variable_profile_height'] = (
        (epoch_name, 'z'), np.arange(15)[np.newaxis, :] * np.ones((num, 15)))

    # Create fake image type data, projected to lat / lon at some location
    # from satellite.
    data['images'] = ((epoch_name, 'x', 'y'),
                      data['dummy3'].values[
                          :, np.newaxis, np.newaxis] * np.ones((num, 17, 17)))
    data.coords['image_lat'] = \
        ((epoch_name, 'x', 'y'),
         np.arange(17)[np.newaxis,
                       np.newaxis,
                       :] * np.ones((num, 17, 17)))
    data.coords['image_lon'] = ((epoch_name, 'x', 'y'),
                                np.arange(17)[np.newaxis, np.newaxis,
                                              :] * np.ones((num, 17, 17)))

    meta = mm_test.initialize_test_meta(epoch_name, data.keys())
    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
