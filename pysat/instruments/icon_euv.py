# -*- coding: utf-8 -*-
"""Supports the Extreme Ultraviolet (EUV) imager onboard the Ionospheric
CONnection Explorer (ICON) satellite.  Accesses local data in
netCDF format.

Parameters
----------
platform : string
    'icon'
name : string
    'euv'
tag : string
    None supported

Warnings
--------
- The cleaning parameters for the instrument are still under development.
- Only supports level-2 data.

Authors
---------
Jeff Klenzing, Mar 17, 2018, Goddard Space Flight Center
Russell Stoneback, Mar 23, 2018, University of Texas at Dallas

"""

from __future__ import print_function
from __future__ import absolute_import

import functools

import pandas as pds
import numpy as np

import pysat
from . import nasa_cdaweb_methods as cdw


platform = 'icon'
name = 'euv'
tags = {'level_2':'Level 2 public geophysical data'}
sat_ids = {'':['level_2']}
test_dates = {'':{'level_2':pysat.datetime(2017,5,27)}}

def init(self):
    """
    """
    pass

    return


def default(inst):
    """Default routine to be applied when loading data. Removes redundant naming

    """
    import pysat.instruments.icon_ivm as icivm
    inst.tag = 'level_2'
    icivm.remove_icon_names(inst, target='ICON_L2_EUV_Daytime_OP_')


def load(fnames, tag=None, sat_id=None):
    """

    """
    
    return pysat.utils.load_netcdf4(fnames, epoch_name='Epoch', 
                                    units_label='Units', name_label='Long_Name', 
                                    notes_label='Var_Notes', desc_label='CatDesc',
                                    plot_label='FieldNam', axis_label='LablAxis', 
                                    scale_label='ScaleTyp',
                                    min_label='ValidMin', max_label='ValidMax',
                                    fill_label='FillVal')


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of ICON EUV files.

    Notes
    -----
    Currently fixed to level-2

    """

    desc = None
    level = tag
    if level == 'level_1':
        code = 'L1'
        desc = None
    elif level == 'level_2':
        code = 'L2'
        desc = None
    else:
        raise ValueError('Unsupported level supplied: ' + level)

    if format_str is None:
        format_str = 'ICON_'+code+'_EUV_Daytime'
        if desc is not None:
            format_str += '_' + desc +'_'
        format_str += '_{year:4d}-{month:02d}-{day:02d}_v{version:02d}r{revision:03d}.NC'

    return pysat.Files.from_os(data_path=data_path,
                                format_str=format_str)


def download(inst, start, stop, user=None, password=None):
    """ICON has not yet been launched."""

    return
