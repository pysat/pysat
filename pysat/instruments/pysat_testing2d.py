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
    num = 864 #int(tag)
    uts = np.arange(num)
    data = pysat.DataFrame(uts, columns=['uts'])


    # need to create simple orbits here. Have start of first orbit 
    # at 2009,1, 0 UT. 14.84 orbits per day	
    time_delta = date  - pysat.datetime(2009,1,1) 
    uts_root = np.mod(time_delta.total_seconds(), 5820)
    mlt = np.mod(uts_root+np.arange(num), 5820)*(24./5820.)
    data['mlt'] = mlt
    
    # do slt, 20 second offset from mlt
    uts_root = np.mod(time_delta.total_seconds()+20, 5820)
    data['slt'] = np.mod(uts_root+np.arange(num), 5820)*(24./5820.)

    index = pds.date_range(date,date+pds.DateOffset(hours=23,minutes=59,seconds=59),freq='100S')
    data.index=index
    data.index.name = 'epoch'
    
    profiles = []
    frame = pds.DataFrame({'density':data.ix[0:50,'mlt'].values.copy(), 'dummy_str':['test']*50,
                                        'dummy_ustr':[u'test']*50},
                                      index=data.index[0:50],
                                      columns=['density', 'dummy_str', 'dummy_ustr'])
    for time in data.index:
        profiles.append(frame)
    data['profiles'] = pds.Series(profiles, index=data.index)
    
    return data, meta.copy()

def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2008,1,1), pysat.datetime(2010,12,31)) 
    names = [ data_path+'/'+date.strftime('%D')+'.nofile' for date in index]
    return pysat.Series(names, index=index)
    
def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    pass
