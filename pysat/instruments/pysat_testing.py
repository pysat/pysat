# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
import functools
import numpy as np

import pandas as pds

import pysat
from pysat.instruments.methods import testing as mm_test

# pysat required parameters
platform = 'pysat'
name = 'testing'

# dictionary of data 'tags' and corresponding description
# tags are used to choose the behaviour of dummy1
tags = {'': 'Regular testing data set',
        'ascend': 'Ascending Integers from 0 testing data set',
        'descend': 'Descending Integers from 0 testing data set',
        'plus10': 'Ascending Integers from 10 testing data set',
        'fives': 'All 5s testing data set',
        'mlt_offset': 'dummy1 is offset by five from regular testing set'}

# dictionary of satellite IDs, list of corresponding tags
# a numeric string can be used in sat_id to change the number of points per day
sat_ids = {'': ['', 'ascend', 'descend', 'plus10', 'fives', 'mlt_offset']}
_test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}


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

    # work on file index if keyword present
    if self.kwargs['file_date_range'] is not None:
        # set list files routine to desired date range
        # attach to the instrument object
        fdr = self.kwargs['file_date_range']
        self._list_rtn = functools.partial(list_files, file_date_range=fdr)
        self.files.refresh()

    # mess with file dates if kwarg option present
    if self.kwargs['mangle_file_dates']:
        self.files.files.index = \
            self.files.files.index + pds.DateOffset(minutes=5)


def default(self):
    """Default customization function.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue).

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    pass


def load(fnames, tag=None, sat_id=None, sim_multi_file_right=False,
         sim_multi_file_left=False, root_date=None, file_date_range=None,
         malformed_index=False, mangle_file_dates=False):
    """ Loads the test files

    Parameters
    ----------
    fnames : list
        List of filenames
    tag : str or NoneType
        Instrument tag (accepts '')
    sat_id : str or NoneType
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
        used. Shift actually performed by the init function.
        (default=None)
    malformed_index : boolean
        If True, time index will be non-unique and non-monotonic.
    mangle_file_dates : bool
        If True, the loaded file list time index is shifted by 5-minutes.
        This shift is actually performed by the init function.

    Returns
    -------
    data : (pds.DataFrame)
        Testing data
    meta : (pysat.Meta)
        Metadataxs

    """

    # create an artifical satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()
    uts, index, date = mm_test.generate_times(fnames, sat_id, freq='1S')

    # Specify the date tag locally and determine the desired date range
    pds_offset = pds.DateOffset(hours=12)
    if sim_multi_file_right:
        root_date = root_date or _test_dates[''][''] + pds_offset
    elif sim_multi_file_left:
        root_date = root_date or _test_dates[''][''] - pds_offset
    else:
        root_date = root_date or _test_dates['']['']

    data = pysat.DataFrame(uts, columns=['uts'])

    # need to create simple orbits here. Have start of first orbit default
    # to 1 Jan 2009, 00:00 UT. 14.84 orbits per day
    time_delta = date - root_date
    data['mlt'] = mm_test.generate_fake_data(time_delta.total_seconds(),
                                             uts, period=iperiod['lt'],
                                             data_range=drange['lt'])

    # do slt, 20 second offset from mlt
    data['slt'] = mm_test.generate_fake_data(time_delta.total_seconds()+20,
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

    # fake orbit number
    fake_delta = date - (_test_dates[''][''] - pds.DateOffset(years=1))
    data['orbit_num'] = mm_test.generate_fake_data(fake_delta.total_seconds(),
                                                   uts, period=iperiod['lt'],
                                                   cyclic=False)

    # create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude'] / 15.0).astype(int)
    if tag == 'ascend':
        data['dummy1'] = [i for i in range(len(data['mlt']))]
    elif tag == 'descend':
        data['dummy1'] = [-i for i in range(len(data['mlt']))]
    elif tag == 'plus10':
        data['dummy1'] = [i + 10 for i in range(len(data['mlt']))]
    elif tag == 'fives':
        data['dummy1'] = [5 for i in range(len(data['mlt']))]
    elif tag == 'mlt_offset':
        data['dummy1'] = mlt_int + 5
    else:
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

    if malformed_index:
        index = index.tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]]*3

    data.index = index
    data.index.name = 'Epoch'
    return data, meta.copy()


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
download = functools.partial(mm_test.download)


meta = pysat.Meta()
meta['uts'] = {'units': 's',
               'long_name': 'Universal Time',
               'custom': False}
meta['Epoch'] = {'units': 'Milliseconds since 1970-1-1',
                 'Bin_Location': 0.5,
                 'notes': 'UTC time at middle of geophysical measurement.',
                 'desc': 'UTC seconds', }
meta['mlt'] = {'units': 'hours',
               'long_name': 'Magnetic Local Time',
               'label': 'MLT',
               'axis': 'MLT',
               'desc': 'Magnetic Local Time',
               'value_min': 0.0,
               'value_max': 24.0,
               'notes': ('Magnetic Local Time is the solar local time of the '
                         'field line at the location where the field crosses '
                         'the magnetic equator. In this case we just simulate '
                         '0-24 with a consistent orbital period and an offste '
                         'with SLT.'),
               'fill': np.nan,
               'scale': 'linear'}
meta['slt'] = {'units': 'hours',
               'long_name': 'Solar Local Time',
               'label': 'SLT',
               'axis': 'SLT',
               'desc': 'Solar Local Time',
               'value_min': 0.0,
               'value_max': 24.0,
               'notes': ('Solar Local Time is the local time (zenith angle of '
                         'sun) of the given location. Overhead noon, +/- 90 '
                         'is 6, 18 SLT .'),
               'fill': np.nan,
               'scale': 'linear'}
meta['orbit_num'] = {'units': '',
                     'long_name': 'Orbit Number',
                     'label': 'Orbit Number',
                     'axis': 'Orbit Number',
                     'desc': 'Orbit Number',
                     'value_min': 0.0,
                     'value_max': 25000.0,
                     'notes': ('Number of orbits since the start of the '
                               'mission. For this simulation we use the '
                               'number of 5820 second periods since the '
                               'start, 2008-01-01.'),
                     'fill': np.nan,
                     'scale': 'linear'}

meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
meta['dummy1'] = {'units': '', 'long_name': 'dummy1'}
meta['dummy2'] = {'units': '', 'long_name': 'dummy2'}
meta['dummy3'] = {'units': '', 'long_name': 'dummy3'}
meta['dummy4'] = {'units': '', 'long_name': 'dummy4'}
meta['string_dummy'] = {'units': '', 'long_name': 'string_dummy'}
meta['unicode_dummy'] = {'units': '', 'long_name': 'unicode_dummy'}
meta['int8_dummy'] = {'units': '', 'long_name': 'int8_dummy'}
meta['int16_dummy'] = {'units': '', 'long_name': 'int16_dummy'}
meta['int32_dummy'] = {'units': '', 'long_name': 'int32_dummy'}
meta['int64_dummy'] = {'units': '', 'long_name': 'int64_dummy'}
