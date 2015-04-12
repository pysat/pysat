# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 17:03:47 2012

@author: musicalphysics
"""

import pandas as pds
import numpy as np
import pysat

import spacepy
from spacepy import pycdf


def list_files(tag=None, data_dir=None):
    """Return a Pandas Series of every file for chosen satellite data"""

    if data_dir is not None:
        return pysat.Files.from_os(dir_path='vefi_dc_b', 
            format_str='cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v06.cdf')
    else:
        raise ValueError ('A directory must be passed to the loading routine for VEFI DC B')
            
# define metadata for VEFI instrument                              
meta = pysat.Meta()
meta['Epoch'] = {'long_name':'Epoch', 'units':'s'}
meta['year'] = {'long_name':'Year', 'units':'years'}
meta['dayofyear'] = {'long_name':'Day of Year', 'units':'days'}
meta['B_north'] = {'long_name':'Magnetic Field (North)', 'units':'nT'}
meta['B_up'] = {'long_name':'Magnetic Field (Up)', 'units':'nT'}
meta['B_west'] = {'long_name':'Magnetic Field (West)', 'units':'nT'}
meta['B_flag'] = {'long_name':'Flag', 'units':''}
meta['B_IGRF_north'] = {'long_name':'IGRF Magnetic Field (North)', 'units':'nT'}
meta['B_IGRF_up'] = {'long_name':'IGRF Magnetic Field (Up)', 'units':'nT'}
meta['B_IGRF_west'] = {'long_name':'IGRF Magnetic Field (West)', 'units':'nT'}
meta['latitude'] = {'long_name':'Geographic Latituge', 'units':'degrees'}
meta['longitude'] = {'long_name':'Geographic Longitude', 'units':'degrees'}
meta['altitude'] = {'long_name':'Altitude', 'units':'km'}
meta['dB_zon'] = {'long_name':'Delta Magnetic Field - Zonal', 'units':'nT'}
meta['dB_mer'] = {'long_name':'Delta Magnetic Field - Meridional ', 'units':'nT'}
meta['dB_par'] = {'long_name':'Delta Magnetic Field - Parallel ', 'units':'nT'}
                                
def load(fnames, tag=None):
    if len(fnames) <= 0 :
        return pds.DataFrame(None), None
    else:
         cdf = pycdf.CDF(fnames[0])
         data = {}
         for key in cdf.iterkeys():
             data[key] = cdf[key][...]
	 data = pds.DataFrame(data, index=pds.to_datetime(data['Epoch'], unit='s'))
	 return data, meta.copy()
