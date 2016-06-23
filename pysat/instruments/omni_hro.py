# -*- coding: utf-8 -*-
"""Supports OMNI Combined, Definitive, IMF and Plasma Data, and Energetic
Proton Fluxes, Time-Shifted to the Nose of the Earth's Bow Shock, plus Solar
and Magnetic Indices. Downloads data from the NASA Coordinated Data Analysis
Web (CDAWeb). Supports both 5 and 1 minute files.

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
omni.download(start, stop, freq='MS') to only download days that could possibly
have data.  'MS' gives a monthly start frequency.

This material is based upon work supported by the 
National Science Foundation under Grant Number 1259508. 

Any opinions, findings, and conclusions or recommendations expressed in this 
material are those of the author(s) and do not necessarily reflect the views 
of the National Science Foundation.


Warnings
--------
- Currently no cleaning routine. Though the CDAWEB description indicates that
  these level-2 products are expected to be ok.
- Module not written by OMNI team.

"""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import functools

import pandas as pds
import numpy as np

import pysat


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are '1min' and '5min'.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : (string or NoneType)
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files
    """
    if format_str is None and data_path is not None:
        if (tag == '1min') | (tag == '5min'):
            min_fmt = ''.join(['omni_hro_', tag,
                               '{year:4d}{month:02d}{day:02d}_v01.cdf'])
            files = pysat.Files.from_os(data_path=data_path, format_str=min_fmt)
            # files are by month, just add date to monthly filename for
            # each day of the month. load routine will use date to select out appropriate
            # data
            if not files.empty:
                files.ix[files.index[-1] + pds.DateOffset(months=1) -
                         pds.DateOffset(days=1)] = files.iloc[-1]
                files = files.asfreq('D', 'pad')
                # add the date to the filename
                files = files + '_' + files.index.strftime('%Y-%m-%d')
            return files
        else:
            raise ValueError('Unknown tag')
    elif format_str is None:
        estr = 'A directory must be passed to the loading routine for VEFI'
        raise ValueError (estr)
    else:
        return pysat.Files.from_os(data_path=data_path, format_str=format_str)
            

def load(fnames, tag=None, sat_id=None):
    import pysatCDF
    
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), None
    else:
        # pull out date appended to filename
        fname = fnames[0][0:-11]
        date = pysat.datetime.strptime(fnames[0][-10:], '%Y-%m-%d')
        with pysatCDF.CDF(fname) as cdf:
            data, meta = cdf.to_pysat()
            # pick out data for date
            data = data.ix[date:date+pds.DateOffset(days=1) - pds.DateOffset(microseconds=1)] 
            return data, meta
            #return cdf.to_pysat()

def clean(omni):
    for key in omni.data.columns:
        if key != 'Epoch':
          idx, = np.where(omni[key] == omni.meta[key].fillval)
          omni.data.ix[idx, key] = np.nan


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
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

