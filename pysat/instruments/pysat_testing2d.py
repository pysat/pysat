# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
import os

import numpy as np
import pandas as pds

import pysat
from pysat.instruments.methods import testing as test

platform = 'pysat'
name = 'testing'

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
    malformed_index : bool (False)
        If True, the time index will be non-unique and non-monotonic. 

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
    date = pysat.datetime(yr, month, day)
    # scalar divisor below used to reduce the number of time samples
    # covered by the simulation per day. The higher the number the lower
    # the number of samples (86400/scalar)
    scalar = 100
    num = 86400/scalar
    # basic time signal in UTS
    uts = np.arange(num) * scalar
    num_array = np.arange(num) * scalar
    # seed DataFrame with UT array
    data = pysat.DataFrame(uts, columns=['uts'])

    # need to create simple orbits here. Have start of first orbit
    # at 2009,1, 0 UT. 14.84 orbits per day
    # figure out how far in time from the root start
    # use that info to create a signal that is continuous from that start
    # going to presume there are 5820 seconds per orbit (97 minute period)
    time_delta = date - pysat.datetime(2009, 1, 1)
    # mlt runs 0-24 each orbit.
    data['mlt'] = test.generate_fake_data(time_delta.total_seconds(),
                                          np.arange(num)*scalar,
                                          period=5820, data_range=[0.0, 24.0])
    # do slt, 20 second offset from mlt
    data['slt'] = test.generate_fake_data(time_delta.total_seconds()+20,
                                          np.arange(num)*scalar,
                                          period=5820, data_range=[0.0, 24.0])
    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    data['longitude'] = test.generate_fake_data(time_delta.total_seconds(),
                                                num_array, period=6240,
                                                data_range=[0.0, 360.0])
    # create latitude signal for testing polar orbits
    angle = test.generate_fake_data(time_delta.total_seconds(),
                                    num_array, period=5820,
                                    data_range=[0.0, 2.0*np.pi])
    data['latitude'] = 90.0 * np.cos(angle)

    # create real UTC time signal
    index = pds.date_range(date,
                           date + pds.DateOffset(hours=23,
                                                 minutes=59,
                                                 seconds=59),
                           freq=str(scalar)+'S')
    if malformed_index:
        index = index[0:num].tolist()
        # nonmonotonic
        index[0:3], index[3:6] = index[3:6], index[0:3]
        # non unique
        index[6:9] = [index[6]]*3

    data.index = index
    data.index.name = 'epoch'
    # higher rate time signal (for scalar >= 2)
    # this time signal used for 2D profiles associated with each time in main
    # DataFrame
    high_rate_template = pds.date_range(date,
                                        date + pds.DateOffset(hours=0,
                                                              minutes=1,
                                                              seconds=39),
                                        freq='2S')

    # create a few simulated profiles
    # DataFrame at each time with mixed variables
    profiles = []
    # DataFrame at each time with numeric variables only
    alt_profiles = []
    # Serie at each time, numeric data only
    series_profiles = []
    # frame indexed by date times
    frame = pds.DataFrame({'density': data.loc[data.index[0:50],
                                               'mlt'].values.copy(),
                           'dummy_str': ['test'] * 50,
                           'dummy_ustr': [u'test'] * 50},
                          index=data.index[0:50],
                          columns=['density', 'dummy_str', 'dummy_ustr'])
    # frame indexed by float
    dd = np.arange(50) * 1.2
    ff = np.arange(50) / 50.
    ii = np.arange(50) * 0.5
    frame_alt = pds.DataFrame({'density': dd, 'fraction': ff},
                              index=ii,
                              columns=['density', 'fraction'])
    # series version of storage
    series_alt = pds.Series(dd, index=ii, name='series_profiles')

    for time in data.index:
        frame.index = high_rate_template + (time - data.index[0])
        profiles.append(frame)
        alt_profiles.append(frame_alt)
        series_profiles.append(series_alt)
    # store multiple data types into main frame
    data['profiles'] = pds.Series(profiles, index=data.index)
    data['alt_profiles'] = pds.Series(alt_profiles, index=data.index)
    data['series_profiles'] = pds.Series(series_profiles, index=data.index)
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
