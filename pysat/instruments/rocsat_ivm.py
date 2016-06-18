# -*- coding: utf-8 -*-
"""Supports the Ion Velocity Meter (IVM) 
onboard the Republic of China Satellite (ROCSAT-1). Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb).

Parameters
----------
platform : string
    'rocsat'
name : string
    'ivm'
tag : string
    

Warnings
--------
- Currently no cleaning routine.
        
"""

from __future__ import print_function
from __future__ import absolute_import
import pandas as pds
import numpy as np
import pysat
import sys

def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data"""
    if format_str is None:
        format_str = 'rs_k0_ipei_{year:04d}{month:02d}{day:02d}_v01.cdf'
    if data_path is not None:
        return pysat.Files.from_os(data_path=data_path, 
                                   format_str=format_str)
    else:
        raise ValueError ('A directory must be passed to the loading routine for IVM')
            

def load(fnames, tag=None, sat_id=None):
    import pysatCDF
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), None
    else:        
        with pysatCDF.CDF(fnames[0]) as cdf:
            return cdf.to_pysat()

def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    """
    download ROCSAT-1 IVM data, layout consistent with pysat

    start and stop should be datetimes
    """
    import os
    import ftplib

    ftp = ftplib.FTP('cdaweb.gsfc.nasa.gov')   # connect to host, default port
    ftp.login()               # user anonymous, passwd anonymous@
    
    ftp.cwd('/pub/data/rocsat/ipei')

    for date in date_array:
        fname = '{year1:4d}/rs_k0_ipei_{year1:04d}{month:02d}{day:02d}_v01.cdf'
        fname = fname.format(year1=date.year, month=date.month, day=date.day)
        local_fname = 'rs_k0_ipei_{year:04d}{month:02d}{day:02d}_v01.cdf'.format(
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
