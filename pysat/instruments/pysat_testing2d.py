# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing.

.. deprecated:: 3.0.2
    Support for 2D pandas objects will be removed in 3.2.0+.  This instrument
    module simulates an object that will no longer be supported.

"""

import datetime as dt
import functools
import numpy as np
import warnings

import pandas as pds

import pysat
from pysat.instruments.methods import testing as mm_test

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
    test_init_kwarg : any
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
    # Seed the DataFrame with a UT array
    data = pds.DataFrame(np.mod(uts, 86400.), columns=['uts'])

    # Need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day. Figure out how far in time from
    # the root start a measurement is and use that info to create a signal
    # that is continuous from that start. Going to presume there are 5820
    # seconds per orbit (97 minute period).
    time_delta = dates[0] - dt.datetime(2009, 1, 1)

    # MLT runs 0-24 each orbit
    data['mlt'] = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                             period=iperiod['lt'],
                                             data_range=drange['lt'])

    # SLT, 20 second offset from `mlt`.
    data['slt'] = mm_test.generate_fake_data(time_delta.total_seconds() + 20,
                                             uts, period=iperiod['lt'],
                                             data_range=drange['lt'])

    # Create a fake longitude, resets every 6240 seconds. Sat moves at
    # 360/5820 deg/s, Earth rotates at 360/86400, takes extra time to go
    # around full longitude.
    data['longitude'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                                   uts, period=iperiod['lon'],
                                                   data_range=drange['lon'])

    # Create latitude signal for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(),
                                       uts, period=iperiod['angle'],
                                       data_range=drange['angle'])
    data['latitude'] = max_latitude * np.cos(angle)

    # Create constant altitude at 400 km
    alt0 = 400.0
    data['altitude'] = alt0 * np.ones(data['latitude'].shape)

    # Dummy variable data for different types
    data['string_dummy'] = ['test'] * len(data)
    data['unicode_dummy'] = [u'test'] * len(data)
    data['int8_dummy'] = np.ones(len(data), dtype=np.int8)
    data['int16_dummy'] = np.ones(len(data), dtype=np.int16)
    data['int32_dummy'] = np.ones(len(data), dtype=np.int32)
    data['int64_dummy'] = np.ones(len(data), dtype=np.int64)

    if malformed_index:
        index = index.tolist()

        # Create a non-monotonic index
        index[0:3], index[3:6] = index[3:6], index[0:3]

        # Create a non-unique index
        index[6:9] = [index[6]] * 3

    data.index = index
    data.index.name = 'Epoch'

    # Higher rate time signal (for scalar >= 2). This time signal is used
    # for 2D profiles associated with each time in main DataFrame.
    num_profiles = 50 if num_samples >= 50 else num_samples
    end_date = dates[0] + dt.timedelta(seconds=2 * num_profiles - 1)
    high_rate_template = pds.date_range(dates[0], end_date, freq='2S')

    # Create a few simulated profiles.  This results in a pds.DataFrame at
    # each time with mixed variables.
    profiles = []

    # DataFrame at each time with numeric variables only
    alt_profiles = []

    # Series at each time, numeric data only
    series_profiles = []

    # Frame indexed by date times
    frame = pds.DataFrame({'density': data.loc[data.index[0:num_profiles],
                                               'mlt'].values.copy(),
                           'dummy_str': ['test'] * num_profiles,
                           'dummy_ustr': [u'test'] * num_profiles},
                          index=data.index[0:num_profiles],
                          columns=['density', 'dummy_str', 'dummy_ustr'])

    # Frame indexed by float
    dd = np.arange(num_profiles) * 1.2
    ff = np.arange(num_profiles) / num_profiles
    ii = np.arange(num_profiles) * 0.5
    frame_alt = pds.DataFrame({'density': dd, 'fraction': ff},
                              index=ii,
                              columns=['density', 'fraction'])

    # Series version of storage
    series_alt = pds.Series(dd, index=ii, name='series_profiles')

    for time in data.index:
        frame.index = high_rate_template + (time - data.index[0])
        profiles.append(frame)
        alt_profiles.append(frame_alt)
        series_profiles.append(series_alt)

    # Store multiple data types into main frame
    data['profiles'] = pds.Series(profiles, index=data.index)
    data['alt_profiles'] = pds.Series(alt_profiles, index=data.index)
    data['series_profiles'] = pds.Series(series_profiles, index=data.index)

    # Set the meta data
    meta = mm_test.initialize_test_meta('epoch', data.keys())

    # Reset profiles as children meta
    profile_meta = pysat.Meta()
    profile_meta['density'] = {'long_name': 'density', 'units': 'N/cc',
                               'desc': 'Fake "density" signal for testing.',
                               'value_min': 0., 'value_max': 25.,
                               'fill': np.nan}
    profile_meta['dummy_str'] = {'long_name': 'dummy_str',
                                 'desc': 'String data for testing.'}
    profile_meta['dummy_ustr'] = {'long_name': 'dummy_ustr',
                                  'desc': 'Unicode string data for testing.'}

    # Update profiles metadata with sub-variable information
    meta['profiles'] = {'meta': profile_meta}

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
