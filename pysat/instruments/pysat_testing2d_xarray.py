# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
import functools
import numpy as np

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

platform = 'pysat'
name = 'testing2D_xarray'

tags = {'': 'Regular testing data set'}
sat_ids = {'': ['']}
pandas_format = False
_test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}


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


def load(fnames, tag=None, sat_id=None, malformed_index=False):
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
    malformed_index : bool False
        If True, the time index will be non-unique and non-monotonic.

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Metadataxs

    """

    # create an artifical satellite data set
    iperiod = mm_test.define_period()
    drange = mm_test.define_range()
    # Using 100s frequency for compatibility with seasonal analysis unit tests
    uts, index, date = mm_test.generate_times(fnames, sat_id, freq='100S')

    if malformed_index:
        index = index.tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]]*3
    data = xr.Dataset({'uts': (('time'), index)}, coords={'time': index})

    # need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day
    # figure out how far in time from the root start
    # use that info to create a signal that is continuous from that start
    # going to presume there are 5820 seconds per orbit (97 minute period)
    time_delta = date - pysat.datetime(2009, 1, 1)

    # mlt runs 0-24 each orbit.
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

    # create latitude signal for testing polar orbits
    angle = mm_test.generate_fake_data(time_delta.total_seconds(), uts,
                                       period=iperiod['angle'],
                                       data_range=drange['angle'])
    latitude = 90.0 * np.cos(angle)
    data['latitude'] = (('time'), latitude)

    # create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude'] / 15.).astype(int)
    data['dummy1'] = (('time'), mlt_int)
    data['dummy2'] = (('time'), long_int)
    data['dummy3'] = (('time'), mlt_int + long_int * 1000.)
    data['dummy4'] = (('time'), uts)

    # create altitude 'profile' at each location
    num = len(data['uts'])
    data['profiles'] = \
        (('time', 'altitude'),
         data['dummy3'].values[:, np.newaxis] * np.ones((num, 15)))
    data.coords['altitude'] = ('altitude', np.arange(15))

    # profiles that could have different altitude values
    data['variable_profiles'] = \
        (('time', 'z'),
         data['dummy3'].values[:, np.newaxis] * np.ones((num, 15)))
    data.coords['altitude2'] = \
        (('time', 'z'),
         np.arange(15)[np.newaxis, :]*np.ones((num, 15)))

    # basic image simulation
    data['images'] = \
        (('time', 'x', 'y'),
         data['dummy3'].values[:,
                               np.newaxis,
                               np.newaxis] * np.ones((num, 17, 17)))
    data.coords['latitude'] = \
        (('time', 'x', 'y'),
         np.arange(17)[np.newaxis,
                       np.newaxis,
                       :]*np.ones((num, 17, 17)))
    data.coords['longitude'] = \
        (('time', 'x', 'y'),
         np.arange(17)[np.newaxis,
                       np.newaxis,
                       :] * np.ones((num, 17, 17)))

    return data, meta.copy()


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
download = functools.partial(mm_test.download)


# create very limited metadata
meta = pysat.Meta()
meta['uts'] = {'units': 's', 'long_name': 'Universal Time'}
meta['mlt'] = {'units': 'hours', 'long_name': 'Magnetic Local Time'}
meta['slt'] = {'units': 'hours', 'long_name': 'Solar Local Time'}
meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
meta['altitude'] = {'units': 'km', 'long_name': 'Altitude'}
variable_profile_meta = pysat.Meta()
variable_profile_meta['variable_profiles'] = {'units': '',
                                              'long_name': 'series'}
meta['variable_profiles'] = {'meta': variable_profile_meta, 'units': '',
                             'long_name': 'series'}
profile_meta = pysat.Meta()
profile_meta['density'] = {'units': '', 'long_name': 'profiles'}
profile_meta['dummy_str'] = {'units': '', 'long_name': 'profiles'}
profile_meta['dummy_ustr'] = {'units': '', 'long_name': 'profiles'}
meta['profiles'] = {'meta': profile_meta, 'units': '', 'long_name': 'profiles'}
image_meta = pysat.Meta()
image_meta['density'] = {'units': '', 'long_name': 'profiles'}
image_meta['fraction'] = {'units': '', 'long_name': 'profiles'}
meta['images'] = {'meta': image_meta, 'units': '',
                  'long_name': 'profiles'}
