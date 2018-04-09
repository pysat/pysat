# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""

import pandas as pds
import numpy as np
import pysat

platform = 'pysat'
name = 'testing'

meta = pysat.Meta()
meta['uts'] = {'units':'s', 'long_name':'Universal Time'}
meta['mlt'] = {'units':'hours', 'long_name':'Magnetic Local Time'}
meta['slt'] = {'units':'hours', 'long_name':'Solar Local Time'}
profile_meta = pysat.Meta()
profile_meta['density'] = {'units':'', 'long_name':'profiles'}
meta['profiles'] = profile_meta


def init(self):
    self.new_thing=True        


def load(fnames, tag=None, sat_id=None):
    # create an artifical satellite data set
    parts = fnames[0].split('/')
    yr = int('20'+parts[-1][0:2])
    month = int(parts[-3])
    day = int(parts[-2])
    date = pysat.datetime(yr,month,day)
    scalar = 50
    num = 86400/scalar #int(tag)
    uts = np.arange(num)*scalar
    num_array = np.arange(num)*scalar
    data = pysat.DataFrame(uts, columns=['uts'])

    # need to create simple orbits here. Have start of first orbit 
    # at 2009,1, 0 UT. 14.84 orbits per day	
    time_delta = date  - pysat.datetime(2009,1,1) 
    uts_root = np.mod(time_delta.total_seconds(), 5820)
    mlt = np.mod(uts_root+np.arange(num)*scalar, 5820)*(24./5820.)
    data['mlt'] = mlt
    
    # do slt, 20 second offset from mlt
    uts_root = np.mod(time_delta.total_seconds()+20, 5820)
    data['slt'] = np.mod(uts_root+np.arange(num)*scalar, 5820)*(24./5820.)

    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time
    # to go around full longitude
    long_uts_root = np.mod(time_delta.total_seconds(), 6240)
    longitude = np.mod(long_uts_root+num_array, 6240)*(360./6240.)
    data['longitude'] = longitude

    # create latitude area for testing polar orbits
    latitude = 90.*np.cos(np.mod(uts_root+num_array, 5820)*(2.*np.pi/5820.))
    data['latitude'] = latitude

    index = pds.date_range(date,date+pds.DateOffset(hours=23,minutes=59,seconds=59),freq=str(scalar)+'S')
    data.index=index
    data.index.name = 'epoch'
    high_rate_template = pds.date_range(date,date+pds.DateOffset(hours=0, minutes=1, seconds=39),freq='2S')
    
    profiles = []
    alt_profiles = []
    series_profiles = []
    # frame indexed by date times
    frame = pds.DataFrame({'density': data.ix[0:50, 'mlt'].values.copy(), 'dummy_str': ['test'] * 50,
                           'dummy_ustr': [u'test'] * 50},
                          index=data.index[0:50],
                          columns=['density', 'dummy_str', 'dummy_ustr'])
    # frame indexed by float
    dd = np.arange(50)*1.2
    ff = np.arange(50)/50.
    ii = np.arange(50) * 0.5
    frame_alt = pds.DataFrame({'density': dd, 'fraction': ff},
                              index=ii,
                              columns=['density', 'fraction'])

    series_alt = pds.Series(dd, index=ii, name='series_profiles')

    for time in data.index:
        frame.index = high_rate_template + (time - data.index[0])
        profiles.append(frame)
        alt_profiles.append(frame_alt)
        series_profiles.append(series_alt)
    data['profiles'] = pds.Series(profiles, index=data.index)
    data['alt_profiles'] = pds.Series(alt_profiles, index=data.index)
    data['series_profiles'] = pds.Series(series_profiles, index=data.index)
    return data, meta.copy()


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2008,1,1), pysat.datetime(2010,12,31)) 
    names = [ data_path+'/'+date.strftime('%D')+'.nofile' for date in index]
    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    pass
