# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""

import datetime as dt
import functools
import numpy as np

import pandas as pds

import pysat
from pysat.instruments.methods import testing as mm_test

logger = pysat.logger

# pysat required parameters
platform = 'pysat'
name = 'testing'

# dictionary of data 'tags' and corresponding description
# tags are used to choose the behaviour of dummy1
tags = {'': 'Regular testing data set',
        'no_download': 'simulate an instrument without download support',
        'non_strict': 'simulate an instrument without strict_time_flag',
        'user_password': 'simulates an instrument that requires a password',
        'default_meta': 'simulates an instrument using the defualt meta'}

# dictionary of satellite IDs, list of corresponding tags
# a numeric string can be used in inst_id to change the number of points per day
inst_ids = {'': [tag for tag in tags.keys()]}
_test_dates = {'': {tag: dt.datetime(2009, 1, 1) for tag in tags.keys()}}
_test_download = {'': {'no_download': False}}


# Init method
init = mm_test.init


# Clean method
clean = mm_test.clean


# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag=None, inst_id=None, sim_multi_file_right=False,
         sim_multi_file_left=False, root_date=None, malformed_index=False,
         num_samples=None, test_load_kwarg=None):
    """ Loads the test files

    Parameters
    ----------
    fnames : list
        List of filenames
    tag : str or NoneType
        Instrument tag (accepts '' or a string to change the behaviour of
        certain instrument aspects for testing)
    inst_id : str or NoneType
        Instrument satellite ID (accepts '')
    sim_multi_file_right : boolean
        Adjusts date range to be 12 hours in the future or twelve hours beyond
        root_date (default=False)
    sim_multi_file_left : boolean
        Adjusts date range to be 12 hours in the past or twelve hours before
        root_date (default=False)
    root_date : NoneType
        Optional central date, uses _test_dates if not specified.
        (default=None)
    malformed_index : boolean
        If True, time index will be non-unique and non-monotonic (default=False)
    num_samples : int
        Number of samples per day
    test_load_kwarg : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    data : pds.DataFrame
        Testing data
    meta : pysat.Meta
        Metadata

    """

    # Support keyword testing
    logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # Create an artificial satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()

    if num_samples is None:
        # Default to 1 day at a frequency of 1S
        num_samples = 86400
    uts, index, dates = mm_test.generate_times(fnames, num_samples,
                                               freq='1S')

    # Specify the date tag locally and determine the desired date range
    pds_offset = dt.timedelta(hours=12)
    if sim_multi_file_right:
        root_date = root_date or _test_dates[''][''] + pds_offset
    elif sim_multi_file_left:
        root_date = root_date or _test_dates[''][''] - pds_offset
    else:
        root_date = root_date or _test_dates['']['']

    # Store UTS, mod 86400
    data = pds.DataFrame(np.mod(uts, 86400.), columns=['uts'])

    # Need to create simple orbits here. Have start of first orbit default
    # to 1 Jan 2009, 00:00 UT. 14.84 orbits per day
    time_delta = dates[0] - root_date
    data['mlt'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                             uts, period=iperiod['lt'],
                                             data_range=drange['lt'])

    # Do slt, 20 second offset from mlt
    data['slt'] = mm_test.generate_fake_data(time_delta.total_seconds() + 20,
                                             uts, period=iperiod['lt'],
                                             data_range=drange['lt'])

    # Create a fake longitude, resets every 6240 seconds
    # Sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude.
    data['longitude'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                                   uts, period=iperiod['lon'],
                                                   data_range=drange['lon'])

    # Create latitude area for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(),
                                       uts, period=iperiod['angle'],
                                       data_range=drange['angle'])
    data['latitude'] = 90.0 * np.cos(angle)

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

    # Activate for testing malformed_index, and for instrument_test_class
    if malformed_index or tag == 'non_strict':
        index = index.tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]] * 3

    data.index = index
    data.index.name = 'Epoch'

    # Set the meta data
    meta = pysat.Meta()
    meta['uts'] = {'units': 's', 'long_name': 'Universal Time', 'custom': False}
    meta['Epoch'] = {'units': 'Milliseconds since 1970-1-1',
                     'Bin_Location': 0.5,
                     'notes': 'UTC time at middle of geophysical measurement.',
                     'desc': 'UTC seconds'}
    meta['mlt'] = {'units': 'hours', 'long_name': 'Magnetic Local Time',
                   'desc': 'Magnetic Local Time',
                   'value_min': 0.0, 'value_max': 24.0,
                   'notes': ''.join(['Magnetic Local Time is the solar local ',
                                     'time of thefield line at the location ',
                                     'where the field crosses the magnetic ',
                                     'equator. In this case we just simulate ',
                                     '0-24 with a consistent orbital period ',
                                     'and an offset with SLT.']),
                   'scale': 'linear'}
    meta['slt'] = {'units': 'hours', 'long_name': 'Solar Local Time',
                   'desc': 'Solar Local Time', 'value_min': 0.0,
                   'value_max': 24.0,
                   'notes': ''.join(['Solar Local Time is the local time ',
                                     '(zenith angle of sun) of the given ',
                                     'location. Overhead noon, +/- 90 is 6, ',
                                     '18 SLT .'])}
    meta['orbit_num'] = {'units': '', 'long_name': 'Orbit Number',
                         'desc': 'Orbit Number', 'value_min': 0.0,
                         'value_max': 25000.0,
                         'notes': ''.join(['Number of orbits since the start ',
                                           'of the mission. For this ',
                                           'simulation we use the number of ',
                                           '5820 second periods since the ',
                                           'start, 2008-01-01.'])}
    meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
    meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
    meta['altitude'] = {'units': 'km', 'long_name': 'Altitude'}
    if tag != 'default_meta':
        for var in data.keys():
            if var.find('dummy') >= 0:
                meta[var] = {'units': 'none',
                             'notes': 'Dummy variable for testing'}

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
