# -*- coding: utf-8 -*-

"""Supports the Ion Velocity Meter (IVM) 
onboard the Ionospheric Connections (ICON) Explorer. 

Parameters
----------
platform : string
    'icon'
name : string
    'ivm'
tag : string
    None supported
sat_id : string
    'a' or 'b'

Warnings
--------
- No download routine as ICON has not yet been launched
- Data not yet publicly available

R. A. Stoneback

"""

from __future__ import print_function
from __future__ import absolute_import

import functools

import pandas as pds
import numpy as np

import pysat
from . import nasa_cdaweb_methods as cdw


platform = 'icon'
name = 'ivm'
tags = {'':''}
sat_ids = {'a':[''], 
           'b':['']}
test_dates = {'a':{'':pysat.datetime(2018,1,1)},
              'b':{'':pysat.datetime(2018,1,1)}}


def init(self):
    """
    """
    pass

    return


def default(inst):
    """Default routine to be applied when loading data. Removes redundant naming
    
    """
    
    remove_icon_names(inst)


def load(fnames, tag=None, sat_id=None):
    """
    
    """
    return pysat.utils.load_netcdf4(fnames, units_label='Units', name_label='Long_Name',  epoch_name='Epoch')
  

def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of ICON IVM files for both 'a' and 'b' instruments.
    
    Notes
    -----
    Currently fixed to level-2
    
    """
    
    desc = None
    tag = 'level_2'
    if tag == 'level_1':
        code = 'L1'
        desc = None
    elif tag == 'level_2':
        code = 'L2'
        desc = None
    else:
        raise ValueError('Unsupported tag supplied: ' + tag)
        
    if format_str is None:
        format_str = 'ICON_'+code+'_IVM-'+sat_id.upper()
        if desc is not None:
            format_str += '_' + desc +'_'
        format_str += '_{year:4d}-{month:02d}-{day:02d}_v{version:02d}r{revision:03d}.NC'

    return pysat.Files.from_os(data_path=data_path,
                                format_str=format_str)



def download(inst, start, stop, user=None, password=None):
    """ICON has not yet been launched."""
    
    return
        

def remove_icon_names(inst, target=None):
    """Removes leading text on ICON project variable names

    Parameters
    ----------
    inst : pysat.Instrument
        ICON associated pysat.Instrument object
    target : str
        Leading string to remove. If none supplied,
        ICON project standards are used to identify and remove
        leading text

    Returns
    -------
    None
        Modifies Instrument object in place


    """
  
    if target is None:
        lev = inst.tag
        if lev == 'level_2':
            lev = 'L2'
        elif lev == 'level_0':
            lev = 'L0'
        elif lev == 'level_0p':
            lev = 'L0P'
        elif lev == 'level_1.5':
            lev = 'L1-5'
        elif lev == 'level_1':
            lev = 'L1'
        else:
            raise ValueError('Uknown ICON data level')
        
        # get instrument code
        sid = inst.sat_id.lower()
        if sid == 'a':
            sid = 'IVM_A'
        elif sid == 'b':
            sid = 'IVM_B'
        else:
            raise ValueError('Unknown ICON satellite ID')
        prepend_str = '_'.join(('ICON', lev, sid)) + '_'
    else:
        prepend_str = target

    inst.data.rename(columns=lambda x: x.split(prepend_str)[-1].lower(), inplace=True)
    inst.meta.data.rename(index=lambda x: x.split(prepend_str)[-1].lower(), inplace=True)
    orig_keys = inst.meta.keys_nD()  
    for key in orig_keys:
        new_key = key.split(prepend_str)[-1].lower()
        inst.meta[new_key] = inst.meta.pop(key)
        
    return    

