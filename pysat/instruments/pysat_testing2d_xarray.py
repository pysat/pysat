# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
import os

import numpy as np
import pandas as pds
import xarray as xr

import pysat
from pysat.instruments.methods import testing as test

platform = 'pysat'
name = 'testing2D_xarray'

pandas_format = False


def init(self):
    self.new_thing = True


def load(fnames, tag=None, sat_id=None, malformed_index=False):
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

    Returns
    -------
    data : (xr.Dataset)
        Testing data
    meta : (pysat.Meta)
        Metadataxs

    """

    # create an artifical satellite data set
    parts = os.path.split(fnames[0])[-1].split('-')
    yr = int(parts[0])
    month = int(parts[1])
    day = int(parts[2][0:2])
    date = pysat.datetime(yr, month, day)
    # scalar divisor below used to reduce the number of time samples
    # covered by the simulation per day. The higher the number the lower
    # the number of samples (86400/scalar)
    scalar = 1
    num = 86400//scalar
    num_array = np.arange(num) * scalar
    # seed DataFrame with UT array
    index = pds.date_range(date, 
                           date+pds.DateOffset(seconds=num-1), 
                           freq='S')
    if malformed_index:
        index = index[0:num].tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]]*3
    data = xr.Dataset({'uts': (('time'), index)}, coords={'time':index})

    # need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day
    # figure out how far in time from the root start
    # use that info to create a signal that is continuous from that start
    # going to presume there are 5820 seconds per orbit (97 minute period)
    time_delta = date - pysat.datetime(2009, 1, 1)

    # mlt runs 0-24 each orbit.
    mlt = test.generate_fake_data(time_delta.total_seconds(),
                                  np.arange(num)*scalar,
                                  period=5820, data_range=[0.0, 24.0])
    data['mlt'] = (('time'), mlt)

    # do slt, 20 second offset from mlt
    slt = test.generate_fake_data(time_delta.total_seconds()+20,
                                  np.arange(num)*scalar,
                                  period=5820, data_range=[0.0, 24.0])
    data['slt'] = (('time'), slt)

    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    longitude = test.generate_fake_data(time_delta.total_seconds(), num_array,
                                        period=6240, data_range=[0.0, 360.0])
    data['longitude'] = (('time'), longitude)

    # create latitude signal for testing polar orbits
    angle = test.generate_fake_data(time_delta.total_seconds(),
                                    num_array, period=5820,
                                    data_range=[0.0, 2.0*np.pi])
    latitude = 90.0 * np.cos(angle)
    data['latitude'] = (('time'), latitude)

    # create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude'] / 15.).astype(int)
    data['dummy1'] = (('time'), mlt_int)
    data['dummy2'] = (('time'), long_int)
    data['dummy3'] = (('time'), mlt_int + long_int * 1000.)
    data['dummy4'] = (('time'), num_array)

    # create altitude 'profile' at each location
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


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""

    index = pds.date_range(pysat.datetime(2008, 1, 1),
                           pysat.datetime(2010, 12, 31))
    names = [data_path + date.strftime('%Y-%m-%d') + '.nofile'
             for date in index]
    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None, user=None,
             password=None):
    pass


# create very limited metadata
meta = pysat.Meta()
meta['uts'] = {'units': 's', 'long_name': 'Universal Time'}
meta['mlt'] = {'units': 'hours', 'long_name': 'Magnetic Local Time'}
meta['slt'] = {'units': 'hours', 'long_name': 'Solar Local Time'}
meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
series_profile_meta = pysat.Meta()
series_profile_meta['series_profiles'] = {'units': '', 'long_name': 'series'}
meta['series_profiles'] = {'meta': series_profile_meta, 'units': '',
                           'long_name': 'series'}
profile_meta = pysat.Meta()
profile_meta['density'] = {'units': '', 'long_name': 'profiles'}
profile_meta['dummy_str'] = {'units': '', 'long_name': 'profiles'}
profile_meta['dummy_ustr'] = {'units': '', 'long_name': 'profiles'}
meta['profiles'] = {'meta': profile_meta, 'units': '', 'long_name': 'profiles'}
alt_profile_meta = pysat.Meta()
alt_profile_meta['density'] = {'units': '', 'long_name': 'profiles'}
alt_profile_meta['fraction'] = {'units': '', 'long_name': 'profiles'}
meta['alt_profiles'] = {'meta': alt_profile_meta, 'units': '',
                        'long_name': 'profiles'}
