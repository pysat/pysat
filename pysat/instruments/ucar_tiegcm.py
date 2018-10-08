# -*- coding: utf-8 -*-
"""
Supports loading data from files generated using TIEGCM 
(Thermosphere Ionosphere Electrodynamics General Circulation Model) model.
TIEGCM file is a netCDF file with multiple dimensions for some variables.

Parameters
----------
platform : string
    'ucar'
name : string
    'tiegcm'
tag : string
    None supported
   
Note
----

    Loads into xarray format.
    
"""

from __future__ import print_function
from __future__ import absolute_import

import os

import pandas as pds
import xarray as xr
import numpy as np
import pysat

platform = 'ucar'
name = 'tiegcm'

# specify using xarray (not using pandas)
pandas_format = False

def init(self):
    """Initializes the Instrument object with instrument specific values.
    
    Runs once upon instantiation.
    
    """
    
    print ("Mission acknowledgements and data restrictions will be printed here when available.")
    
    pass


def load(fnames, tag=None, sat_id=None):
    """Loads TIEGCM data using xarray.
    
    This routine is called as needed by pysat. It is not intended
    for direct user interaction.
    
    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : string
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    sat_id : string
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    **kwargs : extra keywords
        Passthrough for additional keyword arguments specified when 
        instantiating an Instrument object. These additional keywords
        are passed through to this routine by pysat.
    
    Returns
    -------
    data, metadata
        Data and Metadata are formatted for pysat. Data is an xarray 
        DataSet while metadata is a pysat.Meta instance.
        
    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine.
    
    Examples
    --------
    ::
        inst = pysat.Instrument('ucar', 'tiegcm')
        inst.load(2019,1)
    
    """

    data = xr.open_dataset(fnames[0])
    meta = pysat.Meta()
    # move attributes to the Meta object
    # these attributes will be trasnferred to the Instrument object
    # automatically by pysat
    for attr in data.attrs:
        setattr(meta, attr[0], attr[1])
    data.attrs = []
        
    # fill Meta object with variable information
    for key in data.variables.keys():
        attrs = data.variables[key].attrs
        meta[key] = attrs

    # move misc parameters
    # doing this after the meta ensures all metadata is still kept
    # even for moved variables
    meta.p0 = data['p0']
    meta.p0_model = data['p0_model']
    meta.grav = data['grav']
    meta.mag = data['mag']
    meta.timestep = data['timestep']
    # remove from xarray
    data = data.drop(['p0', 'p0_model', 'grav', 'mag', 'timestep'])
            
    return data, meta


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of files corresponding to UCAR TIEGCM.

    This routine is invoked by pysat and is not intended for direct use by the end user.
    
    Multiple data levels may be supported via the 'tag' input string.
    Currently defaults to level-2 data, or L2 in the filename.

    Parameters
    ----------
    tag : string ('')
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    sat_id : string ('')
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    data_path : string
        Full path to directory containing files to be loaded. This
        is provided by pysat. The user may specify their own data path
        at Instrument instantiation and it will appear here.
    format_str : string (None)
        String template used to parse the datasets filenames. If a user
        supplies a template string at Instrument instantiation
        then it will appear here, otherwise defaults to None.
    
    Returns
    -------
    pandas.Series
        Series of filename strings, including the path, indexed by datetime.
    
    Examples
    --------
    ::
        If a filename is SPORT_L2_IVM_2019-01-01_v01r0000.NC then the template
        is 'SPORT_L2_IVM_{year:04d}-{month:02d}-{day:02d}_v{version:02d}r{revision:04d}.NC'
    
    Note
    ----
    The returned Series should not have any duplicate datetimes. If there are
    multiple versions of a file the most recent version should be kept and the rest
    discarded. This routine uses the pysat.Files.from_os constructor, thus
    the returned files are up to pysat specifications.
    
    """
    
    return pysat.Files.from_os(data_path=data_path, 
                                format_str='tiegcm_icon_merg2.0_totTgcm.s_{day:03d}_{year:4d}.nc')

def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    print ('Not implemented.')
    pass

