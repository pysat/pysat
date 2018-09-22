# -*- coding: utf-8 -*-
"""
Ion Velocity Meter (IVM) support for the NASA/INPE SPORT CubeSat.

This mission is still in development. This routine is here to help
with the development of code associated with SPORT and the IVM.

"""

# import pandas as pds
# import numpy as np
import pysat

# pysat required parameters
platform = 'sport'
name = 'ivm'
# dictionary of data 'tags' and corresponding description
tags = {'':'Level-2 IVM Files',
        'L1': 'Level-1 IVM Files',
        'L0': 'Level-0 IVM Files'}
# dictionary of satellite IDs, list of corresponding tags
# only one satellite in this case
sat_ids = {'':['']}
# good day to download test data for. Downloads aren't currently supported
test_dates = {'':{'':pysat.datetime(2019,1,1)}}


        
def init(self):
    pass
                
def load(fnames, tag=None, sat_id=None, sim_multi_file_right=False,
        sim_multi_file_left=False, root_date = None, **kwargs):
    """Loads SPORT IVM data using pysat.utils.load_netcdf4 .
    
    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine and through
    to the load_netcdf4 call.
    
    Example
    -------
    inst = pysat.Instrument('sport', 'ivm')
    inst.load(2019,1)
    
    """
    
    return pysat.utils.load_netcdf4(fnames, **kwargs)


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of files corresponding to SPORT IVM
    
    Multiple data levels may be supported via the 'tag' input string.
    Currently defaults to level-2 data, or L2 in the filename.
    
    """
        
    if format_str is None:
        if tag is '':
            tag = 'L2'
        format_str = 'SPORT_'+tag+'_IVM_{year:04d}-{month:02d}-{day:02d}_v{version:02d}r{revision:04d}.NC'
    return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    print ('Downloads are not currently supported')
    pass