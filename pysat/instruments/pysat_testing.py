# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
import functools
import os

import numpy as np
import pandas as pds

import pysat

# pysat required parameters
platform = 'pysat'
name = 'testing'

# dictionary of data 'tags' and corresponding description
tags = {'': 'Regular testing data set'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'': ['']}
test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}

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
                         'sun) of the given locaiton. Overhead noon, +/- 90 '
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


def init(self):
    """ Initialization function

    Parameters
    ----------
    file_date_range : (pds.date_range)
        Optional keyword argument that specifies the range of dates for which
        test files will be created

    """
    self.new_thing = True

    if 'file_date_range' in self.kwargs:
        # set list files routine to desired date range
        # attach to the instrument object
        self._list_rtn = functools.partial(list_files, \
                                file_date_range=self.kwargs['file_date_range'])
        self.files.refresh()


def load(fnames, tag=None, sat_id=None, sim_multi_file_right=False,
         sim_multi_file_left=False, root_date=None, file_date_range=None):
    """ Loads the test files

    Parameters
    ----------
    fnames : (list)
        List of filenames
    tag : (str or NoneType)
        Instrument tag (accepts '' or a number (i.e., '10'), which specifies
        the number of times to include in the test instrument)
    sat_id : (str or NoneType)
        Instrument satellite ID (accepts '')
    sim_multi_file_right : (boolean)
        Adjusts date range to be 12 hours in the future or twelve hours beyond
        root_date (default=False)
    sim_multi_file_left : (boolean)
        Adjusts date range to be 12 hours in the past or twelve hours before
        root_date (default=False)
    root_date : (NoneType)
        Optional central date, uses test_dates if not specified.
        (default=None)
    file_date_range : (pds.date_range or NoneType)
        Range of dates for files or None, if this optional arguement is not
        used
        (default=None)

    Returns
    -------
    data : (pds.DataFrame)
        Testing data
    meta : (pysat.Meta)
        Metadataxs

    """
    # create an artifical satellite data set
    parts = os.path.split(fnames[0])[-1].split('-')
    yr = int(parts[0])
    month = int(parts[1])
    day = int(parts[2][0:2])

    # Specify the date tag locally and determine the desired date range
    date = pysat.datetime(yr, month, day)
    pds_offset = pds.DateOffset(hours=12)
    if sim_multi_file_right:
        root_date = root_date or test_dates[''][''] + pds_offset
        data_date = date + pds_offset
    elif sim_multi_file_left:
        root_date = root_date or test_dates[''][''] - pds_offset
        data_date = date - pds_offset
    else:
        root_date = root_date or test_dates['']['']
        data_date = date

    # The tag can be used to specify the number of indexes to load, if
    # using the default testing object
    num = 86400 if tag in tags.keys() else int(tag)
    num_array = np.arange(num)
    uts = num_array
    data = pysat.DataFrame(uts, columns=['uts'])

    # need to create simple orbits here. Have start of first orbit default
    # to 1 Jan 2009, 00:00 UT. 14.84 orbits per day
    time_delta = date - root_date
    uts_root = np.mod(time_delta.total_seconds(), 5820)
    mlt = np.mod(uts_root + num_array, 5820) * (24.0 / 5820.0)
    data['mlt'] = mlt

    # fake orbit number
    fake_delta = date - (test_dates[''][''] - pds.DateOffset(years=1))
    fake_uts_root = fake_delta.total_seconds()

    data['orbit_num'] = ((fake_uts_root + num_array) / 5820.0).astype(int)

    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    long_uts_root = np.mod(time_delta.total_seconds(), 6240)
    longitude = np.mod(long_uts_root + num_array, 6240) * (360.0 / 6240.0)
    data['longitude'] = longitude

    # create latitude area for testing polar orbits
    latitude = 90.0 * np.cos(np.mod(uts_root + num_array, 5820) *
                             (2.0 * np.pi / 5820.0))
    data['latitude'] = latitude

    # do slt, 20 second offset from mlt
    uts_root = np.mod(time_delta.total_seconds() + 20, 5820)
    data['slt'] = np.mod(uts_root + num_array, 5820) * (24.0 / 5820.0)

    # create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude'] / 15.0).astype(int)
    data['dummy1'] = mlt_int
    data['dummy2'] = long_int
    data['dummy3'] = mlt_int + long_int * 1000.0
    data['dummy4'] = num_array
    data['string_dummy'] = ['test'] * len(data)
    data['unicode_dummy'] = [u'test'] * len(data)
    data['int8_dummy'] = np.ones(len(data), dtype=np.int8)
    data['int16_dummy'] = np.ones(len(data), dtype=np.int16)
    data['int32_dummy'] = np.ones(len(data), dtype=np.int32)
    data['int64_dummy'] = np.ones(len(data), dtype=np.int64)
    # print (data['string_dummy'])

    index = pds.date_range(data_date,
                           data_date + pds.DateOffset(seconds=num-1),
                           freq='S')
    data.index = index[0:num]
    data.index.name = 'Epoch'
    return data, meta.copy()


def list_files(tag=None, sat_id=None, data_path=None, format_str=None,
               file_date_range=None):
    """Produce a fake list of files spanning a year

    Parameters
    ----------
    tag : (str)
        pysat instrument tag (default=None)
    sat_id : (str)
        pysat satellite ID tag (default=None)
    data_path : (str)
        pysat data path (default=None)
    format_str : (str)
        file format string (default=None)
    file_date_range : (pds.date_range)
        File date range (default=None)

    Returns
    -------
    Series of filenames indexed by file time

    """

    # Determine the appropriate date range for the fake files
    if file_date_range is None:
        start = test_dates[''][''] - pds.DateOffset(years=1)
        stop = test_dates[''][''] + pds.DateOffset(years=2) \
            - pds.DateOffset(days=1)
        file_date_range = pds.date_range(start, stop)

    index = file_date_range

    # Create the list of fake filenames
    names = [data_path + date.strftime('%Y-%m-%d') + '.nofile'
             for date in index]

    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None,
             user=None, password=None):
    """ Download routine, not used since files are created locally"""
    pass
