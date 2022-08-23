# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing."""

import datetime as dt
import functools
import numpy as np

import pandas as pds

import pysat
from pysat.instruments.methods import testing as mm_test

# pysat required parameters
platform = 'pysat'
name = 'testing'

# Dictionary of data 'tags' and corresponding description
# tags are used to choose the behaviour of `dummy1`.
tags = {'': 'Regular testing data set',
        'no_download': 'simulate an instrument without download support',
        'non_strict': 'simulate an instrument without strict_time_flag',
        'user_password': 'simulates an instrument that requires a password',
        'default_meta': 'simulates an instrument using the default metadata'}

# Dictionary of satellite IDs, list of corresponding tags.
inst_ids = {'': [tag for tag in tags.keys()]}
_test_dates = {'': {tag: dt.datetime(2009, 1, 1) for tag in tags.keys()}}
_test_download = {'': {'no_download': False}}
_test_load_opt = {'': {'': {'num_samples': 13}}}

# Init method
init = mm_test.init

# Clean method
clean = mm_test.clean

# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag='', inst_id='', sim_multi_file_right=False,
         sim_multi_file_left=False, root_date=None, malformed_index=False,
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
    root_date : NoneType
        Optional central date, uses _test_dates if not specified.
        (default=None)
    malformed_index : bool
        If True, time index will be non-unique and non-monotonic (default=False)
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
        theta is a linear periodic signal bounded by [0, 2 * pi) (default=90.).

    Returns
    -------
    data : pds.DataFrame
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

    # Specify the date tag locally and determine the desired date range
    pds_offset = dt.timedelta(hours=12)
    if sim_multi_file_right:
        root_date = root_date or _test_dates[''][''] + pds_offset
    elif sim_multi_file_left:
        root_date = root_date or _test_dates[''][''] - pds_offset
    else:
        root_date = root_date or _test_dates['']['']

    # Store UTS, mod 86400.
    data = pds.DataFrame(np.mod(uts, 86400.), columns=['uts'])

    # Need to create simple orbits here. Have start of first orbit default
    # to 1 Jan 2009, 00:00 UT. 14.84 orbits per day.
    time_delta = dates[0] - root_date
    data['mlt'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                             uts, period=iperiod['lt'],
                                             data_range=drange['lt'])

    # SLT, 20 second offset from `mlt`.
    data['slt'] = mm_test.generate_fake_data(time_delta.total_seconds() + 20,
                                             uts, period=iperiod['lt'],
                                             data_range=drange['lt'])

    # Create a fake longitude, resets every 6240 seconds.
    # Sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude.
    data['longitude'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                                   uts, period=iperiod['lon'],
                                                   data_range=drange['lon'])

    # Create latitude area for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(),
                                       uts, period=iperiod['angle'],
                                       data_range=drange['angle'])
    data['latitude'] = max_latitude * np.cos(angle)

    # Create constant altitude at 400 km
    alt0 = 400.0
    data['altitude'] = alt0 * np.ones(data['latitude'].shape)

    # Fake orbit number
    fake_delta = dates[0] - (_test_dates[''][''] - pds.DateOffset(years=1))
    data['orbit_num'] = mm_test.generate_fake_data(fake_delta.total_seconds(),
                                                   uts, period=iperiod['lt'],
                                                   cyclic=False)

    # Create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude'] / 15.0).astype(int)
    data['dummy1'] = mlt_int
    data['dummy2'] = long_int
    data['dummy3'] = mlt_int + long_int * 1000.0
    data['dummy4'] = uts
    data['string_dummy'] = ['test'] * len(data)
    data['unicode_dummy'] = [u'test'] * len(data)
    data['int8_dummy'] = np.ones(len(data), dtype=np.int8)
    data['int16_dummy'] = np.ones(len(data), dtype=np.int16)
    data['int32_dummy'] = np.ones(len(data), dtype=np.int32)
    data['int64_dummy'] = np.ones(len(data), dtype=np.int64)

    # Activate for testing malformed_index, and for instrument_test_class.
    if malformed_index or tag == 'non_strict':
        index = index.tolist()

        # Create a non-monotonic index
        index[0:3], index[3:6] = index[3:6], index[0:3]

        # Create a non-unique index
        index[6:9] = [index[6]] * 3

    data.index = index
    data.index.name = 'Epoch'

    # Set the meta data
    meta = mm_test.initialize_test_meta('Epoch', data.keys())

    if tag == 'default_meta':
        return data, pysat.Meta()
    else:
        return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
