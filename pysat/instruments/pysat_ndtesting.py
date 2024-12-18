#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing."""

import datetime as dt
import functools
import numpy as np

import pandas as pds
import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

platform = 'pysat'
name = 'ndtesting'

pandas_format = False
tags = {'': 'Regular testing data set'}
inst_ids = {'': [tag for tag in tags.keys()]}
_test_dates = {'': {tag: dt.datetime(2009, 1, 1) for tag in tags.keys()}}
_test_load_opt = {'': {'': [{'num_extra_time_coords': 0},
                            {'num_extra_time_coords': 1}]}}

epoch_name = u'time'

# Init method
init = mm_test.init

# Clean method
clean = mm_test.clean

# Optional methods
concat_data = mm_test.concat_data
preprocess = mm_test.preprocess


def load(fnames, tag='', inst_id='', sim_multi_file_right=False,
         sim_multi_file_left=False, root_date=None, non_monotonic_index=False,
         non_unique_index=False, start_time=None, num_samples=864,
         sample_rate='100s', test_load_kwarg=None, max_latitude=90.0,
         num_extra_time_coords=0):
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
    root_date : NoneType
        Optional central date, uses _test_dates if not specified.
        (default=None)
    non_monotonic_index : bool
        If True, time index will be non-monotonic (default=False)
    non_unique_index : bool
        If True, time index will be non-unique (default=False)
    start_time : dt.timedelta or NoneType
        Offset time of start time since midnight UT. If None, instrument data
        will begin at midnight. (default=None)
    num_samples : int
        Maximum number of times to generate.  Data points will not go beyond the
        current day. (default=864)
    sample_rate : str
        Frequency of data points, using pandas conventions. (default='100s')
    test_load_kwarg : any
        Keyword used for pysat unit testing to ensure that functionality for
        custom keywords defined in instrument support functions is working
        correctly. (default=None)
    max_latitude : float
        Latitude simulated as `max_latitude` * cos(theta(t))`, where
        theta is a linear periodic signal bounded by [0, 2 * pi) (default=90.0)
    num_extra_time_coords : int
        Number of extra time coordinates to include. (default=0)

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
    uts, index, dates = mm_test.generate_times(fnames, num_samples,
                                               freq=sample_rate,
                                               start_time=start_time)

    # Specify the date tag locally and determine the desired date range
    pds_offset = dt.timedelta(hours=12)
    if sim_multi_file_right:
        root_date = root_date or _test_dates[''][''] + pds_offset
    elif sim_multi_file_left:
        root_date = root_date or _test_dates[''][''] - pds_offset
    else:
        root_date = root_date or _test_dates['']['']

    if non_monotonic_index:
        index = mm_test.non_monotonic_index(index)
    if non_unique_index:
        index = mm_test.non_unique_index(index)

    data = xr.Dataset({'uts': ((epoch_name), uts)},
                      coords={epoch_name: index})

    # Need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day. Figure out how far in time from
    # the root start a measurement is and use that info to create a signal
    # that is continuous from that start. Going to presume there are 5820
    # seconds per orbit (97 minute period).
    time_delta = dates[0] - root_date

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

    # Fake orbit number
    fake_delta = dates[0] - (_test_dates[''][''] - pds.DateOffset(years=1))
    data['orbit_num'] = ((epoch_name),
                         mm_test.generate_fake_data(fake_delta.total_seconds(),
                                                    uts, period=iperiod['lt'],
                                                    cyclic=False))

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
    data.coords['x'] = (('x'), np.arange(7))
    data.coords['y'] = (('y'), np.arange(7))
    data.coords['z'] = (('z'), np.arange(5))

    # Add extra time coords
    for i in range(num_extra_time_coords):
        ckey = 'time{:d}'.format(i)
        tindex = data.indexes[epoch_name][:-1 * (i + 1)]
        data.coords[ckey] = (
            (ckey), [itime + dt.timedelta(microseconds=1 + i)
                     for i, itime in enumerate(tindex)])

    # Create altitude 'profile' at each location to simulate remote data
    num = len(data['uts'])
    data['profiles'] = (
        (epoch_name, 'profile_height'),
        data['dummy3'].values[:, np.newaxis] * np.ones(
            (num, data.coords['z'].shape[0])))
    data.coords['profile_height'] = ('profile_height',
                                     np.arange(len(data.coords['z'])))

    # Profiles that could have different altitude values
    data['variable_profiles'] = (
        (epoch_name, 'z'), data['dummy3'].values[:, np.newaxis]
        * np.ones((num, data.coords['z'].shape[0])))
    data.coords['variable_profile_height'] = (
        (epoch_name, 'z'), np.arange(data.coords['z'].shape[0])[np.newaxis, :]
        * np.ones((num, data.coords['z'].shape[0])))

    # Create fake image type data, projected to lat / lon at some location
    # from satellite.
    data['images'] = ((epoch_name, 'x', 'y'),
                      data['dummy3'].values[
                          :, np.newaxis, np.newaxis]
                      * np.ones((num, data.coords['x'].shape[0],
                                 data.coords['y'].shape[0])))
    data.coords['image_lat'] = ((epoch_name, 'x', 'y'),
                                np.arange(data.coords['x'].shape[0])[
                                    np.newaxis, np.newaxis, :]
                                * np.ones((num, data.coords['x'].shape[0],
                                           data.coords['y'].shape[0])))
    data.coords['image_lon'] = ((epoch_name, 'x', 'y'),
                                np.arange(data.coords['x'].shape[0])[
                                    np.newaxis, np.newaxis, :]
                                * np.ones((num, data.coords['x'].shape[0],
                                           data.coords['y'].shape[0])))

    # There may be data that depends on alternate time indices
    for i in range(num_extra_time_coords):
        alt_epoch = 'time{:d}'.format(i)
        data['variable_profiles{:d}'.format(i)] = (
            (alt_epoch, 'z'), np.full(shape=(data.coords[alt_epoch].shape[0],
                                             data.coords['z'].shape[0]),
                                      fill_value=100.0 + i))

    meta = mm_test.initialize_test_meta(epoch_name, data.keys())
    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
