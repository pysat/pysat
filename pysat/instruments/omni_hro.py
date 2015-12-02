# -*- coding: utf-8 -*-
"""Supports OMNI Combined, Definitive, IMF and Plasma Data, and Energetic Proton Fluxes,
Time-Shifted to the Nose of the Earth's Bow Shock, plus Solar and Magnetic Indices. Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb). Supports both 5 and 1 minute files.

Parameters
----------
platform : string
    'omni'
name : string
    'hro'
tag : string
    Select time between samples, one of {'1min', '5min'}

Note
----
Files are stored by the first day of each month. When downloading use
omni.download(start, stop, freq='MS') to only download days that could possibly have data.
'MS' gives a monthly start frequency.

Warnings
--------
- Currently no cleaning routine. Though the CDAWEB description indicates that these level-2 products
  are expected to be ok.
- Module not written by OMNI team.
        
"""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys

import pandas as pds
import numpy as np

import spacepy
from spacepy import pycdf
import pysat


def list_files(tag=None, data_path=None):
    """Return a Pandas Series of every file for chosen satellite data"""
    if data_path is not None:
        if (tag == '1min') | (tag == '5min'):
            files = pysat.Files.from_os(data_path=data_path,
                    format_str=''.join(['omni_hro_',tag,'{year:4d}{month:02d}{day:02d}_v01.cdf']))
            # files are by month, just repeat filename in a given month for each day of the month
            # load routine will select out appropriate data
            if not files.empty:
                files.ix[files.index[-1]+pds.DateOffset(months=1)-pds.DateOffset(days=1)] = files.iloc[-1]
                files = files.asfreq('D', 'pad')
            return files
        else:
            raise ValueError('Unknown tag')
    else:
        raise ValueError ('A directory must be passed to the loading routine for VEFI')
            

def load(fnames, tag=None):

    
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), None
    else:

        try:
            with spacepy.pycdf.CDF(fnames[0]) as temporary:
                omni_cdf = temporary.copy()
                #print ('Clean Read')
        except pycdf.CDFError:
            return pysat.DataFrame(), pysat.Meta()
            
        data = {}
        meta = pysat.Meta()
        for key in omni_cdf.iterkeys():
            key_low = key.lower()
            data[key_low] = omni_cdf[key][...]
            try:             
                meta[key_low] = {'units':omni_cdf[key].attrs['UNITS'],
                            'long_name':omni_cdf[key].attrs['LABLAXIS'], 
                            'description':omni_cdf[key].attrs['CATDESC'],
                            'fill_value':omni_cdf[key].attrs['FILLVAL']}
            except KeyError:
                attrs = omni_cdf[key].attrs.keys()
    
                if 'UNITS' in attrs:
                    meta[key_low] = {'units':omni_cdf[key].attrs['UNITS']}
                if 'LABLAXIS' in attrs:
                    meta[key_low] = {'long_name':omni_cdf[key].attrs['LABLAXIS']}
                if 'CATDESC' in attrs:
                    meta[key_low] = {'description':omni_cdf[key].attrs['CATDESC']}
                if 'FILLVAL' in attrs:
                    meta[key_low] = {'fill_value':omni_cdf[key].attrs['FILLVAL']}

        epoch = data.pop('epoch')
    data = pysat.DataFrame(data, index=pds.to_datetime(epoch, unit='s'))
    return data, meta

def clean(omni):
    for key in omni.data.columns:
        idx, = np.where(omni[key] == omni.meta[key].fill_value)
        omni.data.ix[idx, key] = np.nan

def default(omni):
    """ OMNI data stored monthly. Select out desired day."""
    start = omni.date
    stop = omni.date + pds.DateOffset(days=1) - pds.DateOffset(microseconds=1)
    omni.data = omni.data.ix[start:stop]
    return omni

def download(date_array, tag, data_path=None, user=None, password=None):
    """
    download OMNI data, layout consistent with pysat
    """
    import os
    import ftplib

    ftp = ftplib.FTP('cdaweb.gsfc.nasa.gov')   # connect to host, default port
    ftp.login()               # user anonymous, passwd anonymous@
    
    if (tag == '1min') | (tag == '5min'):
        ftp.cwd('/pub/data/omni/omni_cdaweb/hro_'+tag)
    
        for date in date_array:
            fname = '{year1:4d}/omni_hro_'+tag+'_{year2:4d}{month:02d}{day:02d}_v01.cdf'
            fname = fname.format(year1=date.year, year2=date.year, month=date.month, day=date.day)
            local_fname = ''.join(['omni_hro_',tag,'_{year:4d}{month:02d}{day:02d}_v01.cdf']).format(
                    year=date.year, month=date.month, day=date.day)
            saved_fname = os.path.join(data_path,local_fname) 
            try:
                print('Downloading file for '+date.strftime('%D'))
                sys.stdout.flush()
                ftp.retrbinary('RETR '+fname, open(saved_fname,'w').write)
            except ftplib.error_perm as exception:
                if exception[0][0:3] != '550':
                    raise
                else:
                    os.remove(saved_fname)
                    print('File not available for '+ date.strftime('%D'))
    ftp.quit()
    return