# -*- coding: utf-8 -*-
"""
Generic module for loading netCDF4 files into the pandas format within pysat.
"""

import pandas as pds
import numpy as np
import pysat

# pysat required parameters
platform = 'netcdf'
name = 'pandas'
# dictionary of data 'tags' and corresponding description
tags = {'':'netCDF4'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}


        
def init(self):
    pass
                
def load(fnames, tag=None, sat_id=None, sim_multi_file_right=False,
        sim_multi_file_left=False, root_date = None, **kwargs):
    """Loads data using pysat.utils.load_netcdf4 .
    
    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine and through
    to the load_netcdf4 call.
    
    Example
    -------
    inst = pysat.Instrument('netcdf', 'pandas', custom_kwarg='test')
    
    """
    return pysat.utils.load_netcdf4(fnames, **kwargs)


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    pass
