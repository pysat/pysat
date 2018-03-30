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
tags = {'':''}
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2017,5,27)}}

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
    
    import xarray as xr
    
    a = xr.open_dataset(fnames[0])
    
    df = pysat.DataFrame()
    meta = pysat.Meta()
    
    for key in a.keys():
        temp = a[key]
        if len(temp.dims) == 1:
            if key != 'Epoch':
                df[key] = temp.data
                meta[key] = temp.attrs
    
    # handle S/C position
    temp = a['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF'].data
    df['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF_X'] = temp[:,0]
    df['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF_Y'] = temp[:,1]
    df['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF_Z'] = temp[:,2]
    meta['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF_X'] = a['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF'].attrs
    meta['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF_Y'] = a['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF'].attrs
    meta['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF_Z'] = a['ICON_L2_EUV_Daytime_OP_SC_Position_ECEF'].attrs
    
    # O+ vs altitude
    df2 = pysat.DataFrame()
    meta2 = pysat.Meta()
    df2['Oplus'] = a['ICON_L2_EUV_Daytime_OP_Retrieval_Oplus'].data.flatten(order='C')
    meta2['Oplus'] = a['ICON_L2_EUV_Daytime_OP_Retrieval_Oplus'].attrs
    new_index = a['ICON_L2_EUV_Daytime_OP_Retrieval_Altitude'].data.flatten(order='C')
    meta2['altitude'] = a['ICON_L2_EUV_Daytime_OP_Retrieval_Altitude'].attrs
    df2['Sigma_Oplus'] = a['ICON_L2_EUV_Daytime_OP_Retrieval_Sigma_Oplus'].data.flatten(order='C')
    meta2['Sigma_Oplus'] = a['ICON_L2_EUV_Daytime_OP_Retrieval_Sigma_Oplus'].attrs
    num = len(a['Epoch'].data)
    step_size = len(df2)//num
    loop_list = []
    for i in np.arange(num):
        loop_list.append(df2.iloc[step_size*i:step_size*(i+1), :])
        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
        loop_list[-1].index.name = 'altitude'
    df['retrieval'] = loop_list
    meta['retrieval'] = meta2
        
    # Model Data
    df2 = pysat.DataFrame()
    # new_index = a['ICON_L2_EUV_Daytime_OP_Input_Data_Altitude'].data.flatten(order='C')
    meta2 = pysat.Meta()
    df2['base'] = a['ICON_L2_EUV_Daytime_OP_Model_Base'].data.flatten(order='C')
    meta2['base'] = a['ICON_L2_EUV_Daytime_OP_Model_Base'].attrs
    df2['change'] = a['ICON_L2_EUV_Daytime_OP_Model_Change'].data.flatten(order='C')
    meta2['change'] = a['ICON_L2_EUV_Daytime_OP_Model_Change'].attrs
    df2['covest'] = a['ICON_L2_EUV_Daytime_OP_Model_Covest'].data.flatten(order='C')
    meta2['covest'] = a['ICON_L2_EUV_Daytime_OP_Model_Covest'].attrs
    df2['ineq_flag'] = a['ICON_L2_EUV_Daytime_OP_Model_Ineq_Flag'].data.flatten(order='C')
    meta2['ineq_flag'] = a['ICON_L2_EUV_Daytime_OP_Model_Ineq_Flag'].attrs
    df2['lower_limit'] = a['ICON_L2_EUV_Daytime_OP_Model_Lower_Limit'].data.flatten(order='C')
    meta2['lower_limit'] = a['ICON_L2_EUV_Daytime_OP_Model_Lower_Limit'].attrs
    df2['m'] = a['ICON_L2_EUV_Daytime_OP_Model_m'].data.flatten(order='C')
    meta2['m'] = a['ICON_L2_EUV_Daytime_OP_Model_m'].attrs
    df2['m_init'] = a['ICON_L2_EUV_Daytime_OP_Model_m_Init'].data.flatten(order='C')
    meta2['m_init'] = a['ICON_L2_EUV_Daytime_OP_Model_m_Init'].attrs
    df2['m_true'] = a['ICON_L2_EUV_Daytime_OP_Model_m_True'].data.flatten(order='C')
    meta2['m_true'] = a['ICON_L2_EUV_Daytime_OP_Model_m_True'].attrs
    df2['name'] = a['ICON_L2_EUV_Daytime_OP_Model_Name'].data.flatten(order='C')
    meta2['name'] = a['ICON_L2_EUV_Daytime_OP_Model_Name'].attrs
    df2['upper_limit'] = a['ICON_L2_EUV_Daytime_OP_Model_Upper_Limit'].data.flatten(order='C')
    meta2['upper_limit'] = a['ICON_L2_EUV_Daytime_OP_Model_Upper_Limit'].attrs
    num = len(a['Epoch'].data)
    step_size = len(df2)//num
    loop_list = []
    new_index = np.arange(step_size)
    for i in np.arange(num):
        loop_list.append(df2.iloc[step_size*i:step_size*(i+1), :])
        loop_list[-1].index = new_index
        loop_list[-1].index.name = 'index'
    df['model'] = loop_list
    meta['model'] = meta2
    
    # model covariance
    df2 = pysat.DataFrame()
    temp = a['ICON_L2_EUV_Daytime_OP_Model_Covfit'].data
    loop_list = []
    for i in np.arange(num):
        loop_list.append(pysat.DataFrame(temp[i, :, :]))
        # loop_list[-1].index = new_index
        loop_list[-1].index.name = 'index'
    df['model_covfit'] = loop_list
    meta['model_covfit'] = a['ICON_L2_EUV_Daytime_OP_Model_Covfit'].attrs

    # Input Data vs altitude
    df2 = pysat.DataFrame()
    meta2 = pysat.Meta()
    new_index = a['ICON_L2_EUV_Daytime_OP_Input_Data_Altitude'].data.flatten(order='C')
    df2['Covariance_834'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Covariance_834'].data.flatten(order='C')
    meta2['Covariance_834'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Covariance_834'].attrs
    df2['Brightness_834'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Brightness_834'].data.flatten(order='C')
    meta2['Brightness_834'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Brightness_834'].attrs
    df2['Din_834'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Din_834'].data.flatten(order='C')
    meta2['Din_834'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Din_834'].attrs
    df2['Covariance_617'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Covariance_617'].data.flatten(order='C')
    meta2['Covariance_617'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Covariance_617'].attrs
    df2['Brightness_617'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Brightness_617'].data.flatten(order='C')
    df2['Brightness_617'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Brightness_617'].data.flatten(order='C')
    df2['Din_617'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Din_617'].data.flatten(order='C')
    meta2['Din_617'] = a['ICON_L2_EUV_Daytime_OP_Input_Data_Din_617'].attrs
    num = len(a['Epoch'].data)
    step_size = len(df2)//num
    loop_list = []
    for i in np.arange(num):
        loop_list.append(df2.iloc[step_size*i:step_size*(i+1), :])
        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
        loop_list[-1].index.name = 'altitude'
    df['input_data'] = loop_list
    meta['input_data'] = meta2

    df.index = pds.to_datetime(a['Epoch'].data)
    return df, meta


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of ICON EUV files.

    Notes
    -----
    Currently fixed to level-2

    """

    desc = None
    level = 'level_2'
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
