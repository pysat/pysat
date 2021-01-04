# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""

import datetime as dt
import functools
import logging
import numpy as np
import warnings

import pandas as pds

import pysat
from pysat.instruments.methods import testing as mm_test

logger = logging.getLogger(__name__)

# pysat required parameters
platform = 'pysat'
name = 'testing'

# dictionary of data 'tags' and corresponding description
# tags are used to choose the behaviour of dummy1
tags = {'': 'Regular testing data set',
        'no_download': 'simulate an instrument without download support',
        'non_strict': 'simulate an instrument without strict_time_flag',
        'user_password': 'simulates an instrument that requires a password'}

# dictionary of satellite IDs, list of corresponding tags
# a numeric string can be used in inst_id to change the number of points per day
inst_ids = {'': ['', 'no_download', 'non_strict', 'user_password']}
_test_dates = {'': {'': dt.datetime(2009, 1, 1),
                    'no_download': dt.datetime(2009, 1, 1),
                    'non_strict': dt.datetime(2009, 1, 1),
                    'user_password': dt.datetime(2009, 1, 1)}}
_test_download = {'': {'no_download': False}}


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Shifts time index of files by 5-minutes if mangle_file_dates
    set to True at pysat.Instrument instantiation.

    Creates a file list for a given range if the file_date_range
    keyword is set at instantiation.

    Parameters
    ----------
    inst : pysat.Instrument
        This object
    file_date_range : pds.date_range
        Optional keyword argument that specifies the range of dates for which
        test files will be created
    mangle_file_dates : bool
        If True, the loaded file list time index is shifted by 5-minutes.

    """

    self.new_thing = True
    logger.info(mm_test.ackn_str)
    self.acknowledgements = mm_test.ackn_str
    self.references = mm_test.refs

    # work on file index if keyword present
    if self.kwargs['load']['file_date_range'] is not None:
        # set list files routine to desired date range
        # attach to the instrument object
        fdr = self.kwargs['load']['file_date_range']
        self._list_files_rtn = functools.partial(list_files,
                                                 file_date_range=fdr)
        self.files.refresh()

    # mess with file dates if kwarg option present
    if self.kwargs['load']['mangle_file_dates']:
        self.files.files.index = \
            self.files.files.index + dt.timedelta(minutes=5)
    return


def clean(self):
    """Cleaning function
    """

    return


# Optional method
def preprocess(self):
    """Customization method that performs standard preprocessing.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue). Object
    modified in place.

    """

    return


def load(fnames, tag=None, inst_id=None, sim_multi_file_right=False,
         sim_multi_file_left=False, root_date=None, file_date_range=None,
         malformed_index=False, mangle_file_dates=False, num_samples=None,
         multi_file_day=False):
    """ Loads the test files

    Parameters
    ----------
    fnames : list
        List of filenames
    tag : str or NoneType
        Instrument tag (accepts '' or a string to change the behaviour of
        dummy1 for constellation testing)
    inst_id : str or NoneType
        Instrument satellite ID (accepts '' or a number (i.e., '10'), which
        specifies the number of data points to include in the test instrument)
    sim_multi_file_right : boolean
        Adjusts date range to be 12 hours in the future or twelve hours beyond
        root_date (default=False)
    sim_multi_file_left : boolean
        Adjusts date range to be 12 hours in the past or twelve hours before
        root_date (default=False)
    root_date : NoneType
        Optional central date, uses _test_dates if not specified.
        (default=None)
    file_date_range : pds.date_range or NoneType
        Range of dates for files or None, if this optional arguement is not
    file_date_range : pds.date_range or NoneType
        Range of dates for files or None, if this optional argument is not
        used. Shift actually performed by the init function.
        (default=None)
    malformed_index : boolean
        If True, time index will be non-unique and non-monotonic (default=False)
    mangle_file_dates : bool
        If True, the loaded file list time index is shifted by 5-minutes.
        This shift is actually performed by the init function.
    num_samples : int
        Number of samples per day

    Returns
    -------
    data : pds.DataFrame
        Testing data
    meta : pysat.Meta
        Metadata

    """

    # create an artificial satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()

    if num_samples is None:
        if inst_id != '':
            estr = ' '.join(('inst_id will no longer be supported',
                             'for setting the number of samples per day.'))
            warnings.warn(estr, DeprecationWarning)
            num_samples = int(inst_id)
        else:
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

    # store UTS, mod 86400
    data = pds.DataFrame(np.mod(uts, 86400.), columns=['uts'])

    # need to create simple orbits here. Have start of first orbit default
    # to 1 Jan 2009, 00:00 UT. 14.84 orbits per day
    time_delta = dates[0] - root_date
    data['mlt'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                             uts, period=iperiod['lt'],
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

    # create latitude area for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(),
                                       uts, period=iperiod['angle'],
                                       data_range=drange['angle'])
    data['latitude'] = 90.0 * np.cos(angle)

    # create constant altitude at 400 km
    alt0 = 400.0
    data['altitude'] = alt0 * np.ones(data['latitude'].shape)

    # fake orbit number
    fake_delta = dates[0] - (_test_dates[''][''] - pds.DateOffset(years=1))
    data['orbit_num'] = mm_test.generate_fake_data(fake_delta.total_seconds(),
                                                   uts, period=iperiod['lt'],
                                                   cyclic=False)

    # create some fake data to support testing of averaging routines
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

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
