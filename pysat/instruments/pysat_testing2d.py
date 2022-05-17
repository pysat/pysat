# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing.

.. deprecated:: 3.0.2
    Support for 2d pandas objects will be removed in 3.2.0+.  This instrument
    module simulates an object that will no longer be supported.

"""

import datetime as dt
import functools
import numpy as np
import warnings

import pandas as pds

import pysat
from pysat.instruments.methods import testing as mm_test

logger = pysat.logger

platform = 'pysat'
name = 'testing2d'
tags = {'': 'Regular testing data set'}
inst_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}


# Init method
def init(self, test_init_kwarg=None):
    """Initialize the test instrument.

    Parameters
    ----------
    self : pysat.Instrument
        This object
    test_init_kwarg : any or NoneType
        Testing keyword (default=None)

    """

    warnings.warn(" ".join(["The instrument module `pysat_testing2d` has been",
                            "deprecated and will be removed in 3.2.0+. This",
                            "module simulates an object that will no longer be",
                            "supported."]),
                  DeprecationWarning, stacklevel=2)

    mm_test.init(self, test_init_kwarg=test_init_kwarg)
    return


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
        List of filenames
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
        will begin at midnight.
        (default=None)
    num_samples : int
        Maximum number of times to generate.  Data points will not go beyond the
        current day. (default=864)
    test_load_kwarg : any or NoneType
        Testing keyword (default=None)
    max_latitude : float
        Latitude simulated as `max_latitude` * cos(theta(t))`, where
        theta is a linear periodic signal bounded by [0, 2 * pi) (default=90.).

    Returns
    -------
    data : pds.DataFrame
        Testing data
    meta : pysat.Meta
        Testing metadata

    """

    # Support keyword testing
    logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # create an artifical satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()

    # Using 100s frequency for compatibility with seasonal analysis unit tests
    uts, index, dates = mm_test.generate_times(fnames, num_samples, freq='100S',
                                               start_time=start_time)
    # Seed the DataFrame with a UT array
    data = pds.DataFrame(np.mod(uts, 86400.), columns=['uts'])

    # need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day
    # figure out how far in time from the root start
    # use that info to create a signal that is continuous from that start
    # going to presume there are 5820 seconds per orbit (97 minute period)
    time_delta = dates[0] - dt.datetime(2009, 1, 1)
    # mlt runs 0-24 each orbit.
    data['mlt'] = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                             period=iperiod['lt'],
                                             data_range=drange['lt'])
    # do slt, 20 second offset from mlt
    data['slt'] = mm_test.generate_fake_data(time_delta.total_seconds() + 20,
                                             uts, period=iperiod['lt'],
                                             data_range=drange['lt'])
    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    data['longitude'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                                   uts, period=iperiod['lon'],
                                                   data_range=drange['lon'])
    # create latitude signal for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(),
                                       uts, period=iperiod['angle'],
                                       data_range=drange['angle'])
    data['latitude'] = max_latitude * np.cos(angle)

    # create constant altitude at 400 km
    alt0 = 400.0
    data['altitude'] = alt0 * np.ones(data['latitude'].shape)

    if malformed_index:
        index = index.tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]] * 3

    data.index = index
    data.index.name = 'Epoch'
    # higher rate time signal (for scalar >= 2)
    # this time signal used for 2D profiles associated with each time in main
    # DataFrame
    num_profiles = 50 if num_samples >= 50 else num_samples
    end_date = dates[0] + dt.timedelta(seconds=2 * num_profiles - 1)
    high_rate_template = pds.date_range(dates[0], end_date, freq='2S')

    # create a few simulated profiles
    # DataFrame at each time with mixed variables
    profiles = []
    # DataFrame at each time with numeric variables only
    alt_profiles = []
    # Serie at each time, numeric data only
    series_profiles = []
    # frame indexed by date times
    frame = pds.DataFrame({'density': data.loc[data.index[0:num_profiles],
                                               'mlt'].values.copy(),
                           'dummy_str': ['test'] * num_profiles,
                           'dummy_ustr': [u'test'] * num_profiles},
                          index=data.index[0:num_profiles],
                          columns=['density', 'dummy_str', 'dummy_ustr'])
    # frame indexed by float
    dd = np.arange(num_profiles) * 1.2
    ff = np.arange(num_profiles) / num_profiles
    ii = np.arange(num_profiles) * 0.5
    frame_alt = pds.DataFrame({'density': dd, 'fraction': ff},
                              index=ii,
                              columns=['density', 'fraction'])
    # series version of storage
    series_alt = pds.Series(dd, index=ii, name='series_profiles')

    for time in data.index:
        frame.index = high_rate_template + (time - data.index[0])
        profiles.append(frame)
        alt_profiles.append(frame_alt)
        series_profiles.append(series_alt)
    # store multiple data types into main frame
    data['profiles'] = pds.Series(profiles, index=data.index)
    data['alt_profiles'] = pds.Series(alt_profiles, index=data.index)
    data['series_profiles'] = pds.Series(series_profiles, index=data.index)

    # Set the meta data.
    meta = mm_test.initialize_test_meta('epoch', data.keys())

    # Reset profiles as children meta
    profile_meta = pysat.Meta()
    profile_meta['density'] = {'long_name': 'profiles'}
    profile_meta['dummy_str'] = {'long_name': 'profiles'}
    profile_meta['dummy_ustr'] = {'long_name': 'profiles'}
    meta['profiles'] = {'meta': profile_meta, 'long_name': 'profiles'}

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
