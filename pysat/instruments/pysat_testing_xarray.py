# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
import functools
import numpy as np

import xarray

import pysat
from pysat.instruments.methods import testing as mm_test

# pysat required parameters
platform = 'pysat'
name = 'testing_xarray'
# dictionary of data 'tags' and corresponding description
tags = {'': 'Regular testing data set'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}
pandas_format = False


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    self.new_thing = True


def default(inst):
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
         sim_multi_file_left=False, malformed_index=False,
         **kwargs):
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
    malformed_index : boolean
        If True, time index will be non-unique and non-monotonic.
    kwargs : dict
        Additional unspecified keywords supplied to pysat.Instrument upon
        instantiation are passed here.

    Returns
    -------
    data : (xr.Dataset)
        Testing data
    meta : (pysat.Meta)
        Metadata

    """

    # create an artifical satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()
    uts, index, date = mm_test.generate_times(fnames, sat_id=sat_id, freq='1S')

    if sim_multi_file_right:
        root_date = pysat.datetime(2009, 1, 1, 12)
    elif sim_multi_file_left:
        root_date = pysat.datetime(2008, 12, 31, 12)
    else:
        root_date = pysat.datetime(2009, 1, 1)

    if malformed_index:
        index = index.tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]]*3

    data = xarray.Dataset({'uts': (('time'), index)}, coords={'time': index})
    # need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day
    time_delta = date - root_date
    mlt = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['mlt'] = (('time'), mlt)

    # do slt, 20 second offset from mlt
    slt = mm_test.generate_fake_data(time_delta.total_seconds()+20, uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['slt'] = (('time'), slt)

    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    longitude = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                           period=iperiod['lon'],
                                           data_range=drange['lon'])
    data['longitude'] = (('time'), longitude)

    # create latitude area for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                       period=iperiod['angle'],
                                       data_range=drange['angle'])
    latitude = 90.0 * np.cos(angle)
    data['latitude'] = (('time'), latitude)

    # fake orbit number
    fake_delta = date - pysat.datetime(2008, 1, 1)
    orbit_num = mm_test.generate_fake_data(fake_delta.total_seconds(),
                                           uts, period=iperiod['lt'],
                                           cyclic=False)

    data['orbit_num'] = (('time'), orbit_num)

    # create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude'] / 15.).astype(int)
    data['dummy1'] = (('time'), mlt_int)
    data['dummy2'] = (('time'), long_int)
    data['dummy3'] = (('time'), mlt_int + long_int * 1000.)
    data['dummy4'] = (('time'), uts)
    data['string_dummy'] = (('time'), ['test'] * len(data.indexes['time']))
    data['unicode_dummy'] = (('time'), [u'test'] * len(data.indexes['time']))
    data['int8_dummy'] = (('time'), np.array([1] * len(data.indexes['time']),
                          dtype=np.int8))
    data['int16_dummy'] = (('time'), np.array([1] * len(data.indexes['time']),
                           dtype=np.int16))
    data['int32_dummy'] = (('time'), np.array([1] * len(data.indexes['time']),
                           dtype=np.int32))
    data['int64_dummy'] = (('time'), np.array([1] * len(data.indexes['time']),
                           dtype=np.int64))

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
               'value_min': 0.,
               'value_max': 24.,
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
               'value_min': 0.,
               'value_max': 24.,
               'notes': ('Solar Local Time is the local time (zenith angle of '
                         'sun) of the given locaiton. Overhead noon, +/- 90 is'
                         ' 6, 18 SLT .'),
               'fill': np.nan,
               'scale': 'linear'}
meta['orbit_num'] = {'units': '',
                     'long_name': 'Orbit Number',
                     'label': 'Orbit Number',
                     'axis': 'Orbit Number',
                     'desc': 'Orbit Number',
                     'value_min': 0.,
                     'value_max': 25000.,
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
