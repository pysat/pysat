# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
Adapted from existing pysat testing instrument, but changes the data in 
dummy1 to negative integers descending from 0 and deletes dummy2-4
"""

import pandas as pds
import numpy as np
import pysat

# pysat required parameters
platform = 'pysat'
name = 'testing'
# dictionary of data 'tags' and corresponding description
tags = {'':'Regular testing data set'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}

meta = pysat.Meta()
meta['uts'] = {'units':'s', 'long_name':'Universal Time', 'custom':False}
meta['mlt'] = {'units':'hours', 'long_name':'Magnetic Local Time'}
meta['slt'] = {'units':'hours', 'long_name':'Solar Local Time'}

        
def init(self):
    self.new_thing=True        
                
def load(fnames, tag=None, sat_id=None, sim_multi_file_right=False,
        sim_multi_file_left=False, root_date = None):
    # create an artifical satellite data set
    parts = fnames[0].split('/')
    yr = int('20'+parts[-1][0:2])
    month = int(parts[-3])
    day = int(parts[-2])

    date = pysat.datetime(yr, month, day)
    if sim_multi_file_right:
        root_date = root_date or pysat.datetime(2009,1,1,12)
        data_date = date+pds.DateOffset(hours=12)
    elif sim_multi_file_left:
        root_date = root_date or pysat.datetime(2008,12,31,12)
        data_date = date-pds.DateOffset(hours=12)
    else:
        root_date = root_date or pysat.datetime(2009,1,1)
        data_date = date
    num = 86400 if tag is '' else int(tag)
    num_array = np.arange(num)
    uts = num_array
    data = pysat.DataFrame(uts, columns=['uts'])

    # need to create simple orbits here. Have start of first orbit 
    # at 2009,1, 0 UT. 14.84 orbits per day	
    time_delta = date  - root_date
    uts_root = np.mod(time_delta.total_seconds(), 5820)
    mlt = np.mod(uts_root+num_array, 5820)*(24./5820.)
    data['mlt'] = mlt
    
    # fake orbit number
    fake_delta = date  - pysat.datetime(2008,1,1) 
    fake_uts_root = fake_delta.total_seconds()

    data['orbit_num'] = ((fake_uts_root+num_array)/5820.).astype(int)
    
    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time 
    # to go around full longitude
    long_uts_root = np.mod(time_delta.total_seconds(), 6240)
    longitude = np.mod(long_uts_root+num_array, 6240)*(360./6240.)
    data['longitude'] = longitude

    # create latitude area for testing polar orbits
    latitude = 90.*np.cos(np.mod(uts_root+num_array, 5820)*(2.*np.pi/5820.)) 
    data['latitude'] = latitude
    
    # do slt, 20 second offset from mlt
    uts_root = np.mod(time_delta.total_seconds()+20, 5820)
    data['slt'] = np.mod(uts_root+num_array, 5820)*(24./5820.)
    
    # create some fake data to support testing of averaging routines
    dummy1 = []
    for i in range(len(data['mlt'])):
        dummy1.append(-i)
    long_int = (data['longitude']/15.).astype(int)
    data['dummy1'] = dummy1
    data['string_dummy'] = ['test']*len(data)
    data['unicode_dummy'] = [u'test'] * len(data)
    data['int8_dummy'] = np.ones(len(data), dtype=np.int8)
    data['int16_dummy'] = np.ones(len(data), dtype=np.int16)
    data['int32_dummy'] = np.ones(len(data), dtype=np.int32)
    data['int64_dummy'] = np.ones(len(data), dtype=np.int64)
    # print (data['string_dummy'])
    
    index = pds.date_range(data_date, data_date+pds.DateOffset(seconds=num-1), freq='S')
    data.index=index[0:num]
    data.index.name = 'time'
    return data, meta.copy()

def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2008,1,1), pysat.datetime(2010,12,31)) 
    names = [ data_path+date.strftime('%D')+'.nofile' for date in index]
    return pysat.Series(names, index=index)
    
def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    pass
