# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import

import os

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
meta['uts'] = {'units':'s', 
               'long_name':'Universal Time', 
               'custom':False}
meta['Epoch'] = {'units':'Milliseconds since 1970-1-1',
                 'Bin_Location': 0.5,
                 'notes': 'UTC time at middle of geophysical measurement.',
                 'desc': 'UTC seconds',
                }
meta['mlt'] = {'units':'hours', 
               'long_name':'Magnetic Local Time',
               'label': 'MLT',
               'axis': 'MLT',
               'desc': 'Magnetic Local Time',
               'value_min': 0.,
               'value_max': 24.,
               'notes': ('Magnetic Local Time is the solar local time of the field line '
                        'at the location where the field crosses the magnetic equator. '
                        'In this case we just simulate 0-24 with a '
                        'consistent orbital period and an offste with SLT.'),
               'fill': np.nan,
               'scale': 'linear'}
meta['slt'] = {'units':'hours', 
               'long_name':'Solar Local Time',
               'label': 'SLT',
               'axis': 'SLT',
               'desc': 'Solar Local Time',
               'value_min': 0.,
               'value_max': 24.,
               'notes': ('Solar Local Time is the local time (zenith angle of sun) '
                         'of the given locaiton. Overhead noon, +/- 90 is 6, 18 SLT .'),
               'fill': np.nan,
               'scale': 'linear'}
meta['orbit_num'] = {'units':'', 
                     'long_name':'Orbit Number',
                     'label': 'Orbit Number',
                     'axis': 'Orbit Number',
                     'desc': 'Orbit Number',
                     'value_min': 0.,
                     'value_max': 25000.,
                     'notes': ('Number of orbits since the start of the mission. '
                               'For this simulation we use the number of 5820 second periods '
                               'since the start, 2008-01-01.'),
                     'fill': np.nan,
                     'scale': 'linear'}

meta['longitude'] = {'units':'degrees', 'long_name':'Longitude'} 
meta['latitude'] = {'units':'degrees', 'long_name':'Latitude'} 
meta['dummy1'] = {'units':'', 'long_name':'dummy1'}
meta['dummy2'] = {'units':'', 'long_name':'dummy2'}
meta['dummy3'] = {'units':'', 'long_name':'dummy3'}
meta['dummy4'] = {'units':'', 'long_name':'dummy4'}
meta['string_dummy'] = {'units':'', 'long_name':'string_dummy'}
meta['unicode_dummy'] = {'units':'', 'long_name':'unicode_dummy'}
meta['int8_dummy'] = {'units':'', 'long_name':'int8_dummy'}
meta['int16_dummy'] = {'units':'', 'long_name':'int16_dummy'}
meta['int32_dummy'] = {'units':'', 'long_name':'int32_dummy'}
meta['int64_dummy'] = {'units':'', 'long_name':'int64_dummy'}


        
def init(self):
    self.new_thing=True        
                
def load(fnames, tag=None, sat_id=None, sim_multi_file_right=False,
        sim_multi_file_left=False, root_date = None):
    # create an artifical satellite data set
    parts = os.path.split(fnames[0])[-1].split('-')
    yr = int(parts[0])
    month = int(parts[1])
    day = int(parts[2][0:2])

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
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude']/15.).astype(int)
    data['dummy1'] = mlt_int
    data['dummy2'] = long_int
    data['dummy3'] = mlt_int + long_int*1000.
    data['dummy4'] = num_array
    data['string_dummy'] = ['test']*len(data)
    data['unicode_dummy'] = [u'test'] * len(data)
    data['int8_dummy'] = np.ones(len(data), dtype=np.int8)
    data['int16_dummy'] = np.ones(len(data), dtype=np.int16)
    data['int32_dummy'] = np.ones(len(data), dtype=np.int32)
    data['int64_dummy'] = np.ones(len(data), dtype=np.int64)
    # print (data['string_dummy'])
    
    index = pds.date_range(data_date, data_date+pds.DateOffset(seconds=num-1), freq='S')
    data.index=index[0:num]
    data.index.name = 'Epoch'
    return data, meta.copy()


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2008,1,1), pysat.datetime(2010,12,31)) 
    names = [ data_path+date.strftime('%Y-%m-%d')+'.nofile' for date in index]
    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    pass
