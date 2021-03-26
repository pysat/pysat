# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""

import datetime as dt
import functools
import numpy as np

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

logger = pysat.logger

# pysat required parameters
platform = 'pysat'
name = 'testing_xarray'
# dictionary of data 'tags' and corresponding description
tags = {'': 'Regular testing data set'}
# dictionary of satellite IDs, list of corresponding tags
inst_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}
pandas_format = False

epoch_name = u'time'


# Init method
init = mm_test.init


# Clean method
clean = mm_test.clean


# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag=None, inst_id=None, sim_multi_file_right=False,
         sim_multi_file_left=False, malformed_index=False,
         num_samples=None, test_load_kwarg=None):
    """ Loads the test files

    Parameters
    ----------
    fnames : list
        List of filenames
    tag : str or NoneType
        Instrument tag (accepts '')
    inst_id : str or NoneType
        Instrument satellite ID (accepts '')
    sim_multi_file_right : boolean
        Adjusts date range to be 12 hours in the future or twelve hours beyond
        root_date (default=False)
    sim_multi_file_left : boolean
        Adjusts date range to be 12 hours in the past or twelve hours before
        root_date (default=False)
    malformed_index : boolean
        If True, time index will be non-unique and non-monotonic.
    num_samples : int
        Number of samples
    test_load_kwarg : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Metadata

    """

    # Support keyword testing
    logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # create an artifical satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()

    if num_samples is None:
        # Default to 1 day at a frequency of 1S
        num_samples = 86400
    uts, index, dates = mm_test.generate_times(fnames, num_samples,
                                               freq='1S')

    if sim_multi_file_right:
        root_date = dt.datetime(2009, 1, 1, 12)
    elif sim_multi_file_left:
        root_date = dt.datetime(2008, 12, 31, 12)
    else:
        root_date = dt.datetime(2009, 1, 1)

    if malformed_index:
        index = index.tolist()

        # Create a nonmonotonic index
        index[0:3], index[3:6] = index[3:6], index[0:3]

        # Create a non-unique index
        index[6:9] = [index[6]] * 3

    data = xr.Dataset({'uts': ((epoch_name), index)},
                      coords={epoch_name: index})
    # need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day
    time_delta = dates[0] - root_date
    mlt = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['mlt'] = ((epoch_name), mlt)

    # do slt, 20 second offset from mlt
    slt = mm_test.generate_fake_data(time_delta.total_seconds() + 20, uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['slt'] = ((epoch_name), slt)

    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    longitude = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                           period=iperiod['lon'],
                                           data_range=drange['lon'])
    data['longitude'] = ((epoch_name), longitude)

    # create latitude area for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                       period=iperiod['angle'],
                                       data_range=drange['angle'])
    latitude = 90.0 * np.cos(angle)
    data['latitude'] = ((epoch_name), latitude)

    # create constant altitude at 400 km
    alt0 = 400.0
    altitude = alt0 * np.ones(data['latitude'].shape)
    data['altitude'] = ((epoch_name), altitude)

    # fake orbit number
    fake_delta = dates[0] - dt.datetime(2008, 1, 1)
    orbit_num = mm_test.generate_fake_data(fake_delta.total_seconds(),
                                           uts, period=iperiod['lt'],
                                           cyclic=False)

    data['orbit_num'] = ((epoch_name), orbit_num)

    # create some fake data to support testing of averaging routines
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
                          np.array([1] * len(data.indexes[epoch_name]),
                          dtype=np.int8))
    data['int16_dummy'] = ((epoch_name),
                           np.array([1] * len(data.indexes[epoch_name]),
                           dtype=np.int16))
    data['int32_dummy'] = ((epoch_name),
                           np.array([1] * len(data.indexes[epoch_name]),
                           dtype=np.int32))
    data['int64_dummy'] = ((epoch_name),
                           np.array([1] * len(data.indexes[epoch_name]),
                           dtype=np.int64))

    meta = pysat.Meta()
    meta['uts'] = {'units': 's', 'long_name': 'Universal Time',
                   'custom': False}
    meta[epoch_name] = {'units': 'Milliseconds since 1970-1-1',
                        'Bin_Location': 0.5,
                        'notes':
                        'UTC time at middle of geophysical measurement.',
                        'desc': 'UTC seconds', }
    meta['mlt'] = {'units': 'hours',
                   'long_name': 'Magnetic Local Time',
                   'desc': 'Magnetic Local Time',
                   'value_min': 0.,
                   'value_max': 24.,
                   'notes': ''.join(['Magnetic Local Time is the solar local ',
                                     'time of the field line at the location ',
                                     'where the field crosses the magnetic ',
                                     'equator. In this case we just simulate ',
                                     '0-24 with a consistent orbital period ',
                                     'and an offset with SLT.'])}
    meta['slt'] = {'units': 'hours', 'long_name': 'Solar Local Time',
                   'desc': 'Solar Local Time', 'value_min': 0.,
                   'value_max': 24.,
                   'notes': ''.join(['Solar Local Time is the local time ',
                                     '(zenith angle of thee sun) of the given',
                                     ' locaiton. Overhead noon, +/- 90 is 6,',
                                     ' 18 SLT .'])}
    meta['orbit_num'] = {'long_name': 'Orbit Number', 'desc': 'Orbit Number',
                         'value_min': 0., 'value_max': 25000.,
                         'notes': ''.join(['Number of orbits since the start ',
                                           'of the mission. For this ',
                                           'simulation we use the ',
                                           'number of 5820 second periods ',
                                           'since the start, 2008-01-01.'])}

    meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
    meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
    meta['altitude'] = {'units': 'km', 'long_name': 'Altitude'}
    for var in data.keys():
        if var.find('dummy') >= 0:
            meta[var] = {'units': 'none', 'notes': 'Dummy variable'}

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
