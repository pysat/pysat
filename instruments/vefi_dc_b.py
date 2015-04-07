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


def listFiles(tag=None, data_dir=None):
    """Return a Pandas Series of every file for chosen satellite data"""

    if data_dir is not None:
        return pysat.Files.from_os(dir_path='vefi_dc_b', 
            format_str='cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v06.cdf')
    else:
        raise ValueError ('A directory must be passed to the loading routine for VEFI DC B')
            
# define metadata for VEFI instrument                                
meta = pysat.Meta()
meta['Epoch'] = {'long_name':'Epoch', 'units':'s'}
meta['year'] = {'long_name':'Epoch', 'units':'years'}
meta['dayofyear'] = {'long_name':'Epoch', 'units':'days'}
meta['B_north'] = {'long_name':'Epoch', 'units':'nT'}
meta['B_up'] = {'long_name':'Epoch', 'units':'nT'}
meta['B_west'] = {'long_name':'Epoch', 'units':'nT'}
meta['B_flag'] = {'long_name':'Epoch', 'units':''}
meta['B_IGRF_north'] = {'long_name':'Epoch', 'units':'nT'}
meta['B_IGRF_up'] = {'long_name':'Epoch', 'units':'nT'}
meta['B_IGRF_west'] = {'long_name':'Epoch', 'units':'nT'}
meta['latitude'] = {'long_name':'Epoch', 'units':'degrees'}
meta['longitude'] = {'long_name':'Epoch', 'units':'degrees'}
meta['altitude'] = {'long_name':'Epoch', 'units':'km'}
meta['dB_zon'] = {'long_name':'Epoch', 'units':'nT'}
meta['dB_mer'] = {'long_name':'Epoch', 'units':'nT'}
meta['dB_par'] = {'long_name':'Epoch', 'units':'nT'}
                                
def load(fnames, tag=None):
    if len(fnames) <= 0 :
        return pds.DataFrame(None), None
    else:
         cdf = pycdf.CDF(fnames[0])
         data = {}
         #data.index=cdf['Epoch'][...]
         for key in cdf.iterkeys():
             data[key] = cdf[key][...]
	 data = pds.DataFrame(data, index=pds.to_datetime(data['Epoch'], unit='s'))
	 return data, meta

#def default(ivm):
#    pass
#def clean(self):
#    pass 
    
    
#old list files code

     #   search_str = os.path.join(data_dir,'vefi_dc_b','cnofs_vefi_bfield_1sec_*.cdf')
     #   files = glob.glob(search_str)
     #   yr = np.ones(len(files)).astype(int)
     #   doy = np.ones(len(files)).astype(int)
     #   index = [None]*len(files)
     #   #need to parse out dates for datetime index
     #   for i,temp in enumerate(files):
     #       yr[i] = int(temp[-16:-12])
	    #month = int(temp[-12:-10])
	    #day = int(temp[-10:-8])
	    #print yr[i], month, day
     #       index[i] = pds.datetime(yr[i], month, day) 
     #       doy[i] = (index[i] - pds.datetime(yr[i],1,1)).days + 1
     #   file_list = pds.Series(files, index=index)

               
        #return file_list