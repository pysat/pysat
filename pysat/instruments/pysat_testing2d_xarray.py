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

platform = 'pysat'
name = 'testing2d_xarray'

tags = {'': 'Regular testing data set'}
sat_ids = {'': ['']}
pandas_format = False
tags = {'': 'Regular testing data set'}
inst_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}

epoch_name = u'time'


# Init method
init = mm_test.init


# Clean method
clean = mm_test.clean


# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag=None, inst_id=None, malformed_index=False,
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
    malformed_index : bool False
        If True, the time index will be non-unique and non-monotonic.
    num_samples : int
        Number of samples
    test_load_kwarg : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Testing metadata

    """

    # Support keyword testing
    logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # create an artifical satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()

    if num_samples is None:
        # Default to 1 day at a frequency of 100S
        num_samples = 864
    # Using 100s frequency for compatibility with seasonal analysis unit tests
    uts, index, dates = mm_test.generate_times(fnames, num_samples,
                                               freq='100S')

    if malformed_index:
        index = index.tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]] * 3
    data = xr.Dataset({'uts': ((epoch_name), index)},
                      coords={epoch_name: index})

    # need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day
    # figure out how far in time from the root start
    # use that info to create a signal that is continuous from that start
    # going to presume there are 5820 seconds per orbit (97 minute period)
    time_delta = dates[0] - dt.datetime(2009, 1, 1)

    # mlt runs 0-24 each orbit.
    mlt = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['mlt'] = ((epoch_name), mlt)

    # do slt, 20 second offset from mlt
    slt = mm_test.generate_fake_data(time_delta.total_seconds() + 20, uts,
                                     period=iperiod['lt'],
                                     data_range=drange['lt'])
    data['slt'] = ((epoch_name), slt)

    # create a fake satellite longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    longitude = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                           period=iperiod['lon'],
                                           data_range=drange['lon'])
    data['longitude'] = ((epoch_name), longitude)

    # create fake satellite latitude for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                       period=iperiod['angle'],
                                       data_range=drange['angle'])
    latitude = 90.0 * np.cos(angle)
    data['latitude'] = ((epoch_name), latitude)

    # create constant altitude at 400 km for a satellite that has yet
    # to experience orbital decay
    alt0 = 400.0
    altitude = alt0 * np.ones(data['latitude'].shape)
    data['altitude'] = ((epoch_name), altitude)

    # create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int).data
    long_int = (data['longitude'] / 15.).astype(int).data
    data['dummy1'] = ((epoch_name), mlt_int)
    data['dummy2'] = ((epoch_name), long_int)
    data['dummy3'] = ((epoch_name), mlt_int + long_int * 1000.)
    data['dummy4'] = ((epoch_name), uts)

    # Add dummy coords
    data.coords['x'] = (('x'), np.arange(17))
    data.coords['y'] = (('y'), np.arange(17))
    data.coords['z'] = (('z'), np.arange(15))

    # create altitude 'profile' at each location to simulate remote data
    num = len(data['uts'])
    data['profiles'] = (
        (epoch_name, 'profile_height'),
        data['dummy3'].values[:, np.newaxis] * np.ones((num, 15)))
    data.coords['profile_height'] = ('profile_height', np.arange(15))

    # profiles that could have different altitude values
    data['variable_profiles'] = (
        (epoch_name, 'z'), data['dummy3'].values[:, np.newaxis]
        * np.ones((num, 15)))
    data.coords['variable_profile_height'] = (
        (epoch_name, 'z'), np.arange(15)[np.newaxis, :] * np.ones((num, 15)))

    # Create fake image type data, projected to lat / lon at some location
    # from satellite
    data['images'] = ((epoch_name, 'x', 'y'),
                      data['dummy3'].values[
                          :, np.newaxis, np.newaxis] * np.ones((num, 17, 17)))
    data.coords['image_lat'] = \
        ((epoch_name, 'x', 'y'),
         np.arange(17)[np.newaxis,
                       np.newaxis,
                       :] * np.ones((num, 17, 17)))
    data.coords['image_lon'] = ((epoch_name, 'x', 'y'),
                                np.arange(17)[np.newaxis, np.newaxis,
                                              :] * np.ones((num, 17, 17)))

    # create very limited metadata
    meta = pysat.Meta()
    meta[epoch_name] = {'long_name': 'Datetime Index'}
    meta['uts'] = {'units': 's', 'long_name': 'Universal Time'}
    meta['mlt'] = {'units': 'hours', 'long_name': 'Magnetic Local Time'}
    meta['slt'] = {'units': 'hours', 'long_name': 'Solar Local Time'}
    meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
    meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
    meta['altitude'] = {'units': 'km', 'long_name': 'Altitude'}
    variable_profile_meta = pysat.Meta()
    variable_profile_meta['variable_profiles'] = {'long_name': 'series'}
    meta['variable_profiles'] = {'meta': variable_profile_meta,
                                 'long_name': 'series'}
    profile_meta = pysat.Meta()
    profile_meta['density'] = {'long_name': 'profiles'}
    profile_meta['dummy_str'] = {'long_name': 'profiles'}
    profile_meta['dummy_ustr'] = {'long_name': 'profiles'}
    meta['profiles'] = {'meta': profile_meta, 'long_name': 'profiles'}
    image_meta = pysat.Meta()
    image_meta['density'] = {'long_name': 'profiles'}
    image_meta['fraction'] = {'long_name': 'profiles'}
    meta['images'] = {'meta': image_meta, 'long_name': 'profiles'}
    for var in data.keys():
        if var.find('dummy') >= 0:
            meta[var] = {'units': 'none', 'long_name': var,
                         'notes': 'Dummy variable'}
    meta['x'] = {'long_name': 'x-value of image pixel',
                 'notes': 'Dummy Variable'}
    meta['y'] = {'long_name': 'y-value of image pixel',
                 'notes': 'Dummy Variable'}
    meta['z'] = {'long_name': 'z-value of profile height',
                 'notes': 'Dummy Variable'}
    meta['image_lat'] = {'long_name': 'Latitude of image pixel',
                         'notes': 'Dummy Variable'}
    meta['image_lon'] = {'long_name': 'Longitude of image pixel',
                         'notes': 'Dummy Variable'}
    meta['profile_height'] = {'long_name': 'profile height'}
    meta['variable_profile_height'] = {'long_name': 'Variable Profile Height'}

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
