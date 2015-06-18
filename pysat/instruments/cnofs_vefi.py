# -*- coding: utf-8 -*-
"""Supports the Vector Electric Field Instrument (VEFI) 
onboard the Communication and Navigation Outage Forecasting
System (C/NOFS) satellite. Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb).

Parameters
----------
tag : {'dc_b'}

Notes
-----
- tag = 'dc_b': 1 second DC magnetometer data

Warnings
--------
- Currently no cleaning routine.
- Module not written by VEFI team.
        
"""

import pandas as pds
import numpy as np
import pysat
import sys

import spacepy
from spacepy import pycdf
import pysat


def list_files(tag=None, data_path=None):
    """Return a Pandas Series of every file for chosen satellite data"""
    if data_path is not None:
        if tag == 'dc_b':
            return pysat.Files.from_os(data_path=data_path, 
            format_str='cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf')
        else:
            raise ValueError('Unknown tag')
    else:
        raise ValueError ('A directory must be passed to the loading routine for VEFI')
            

def load(fnames, tag=None):
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), None
    else:
        try:
            cdf = pycdf.CDF(fnames[0])
        except pycdf.CDFError:
            return pysat.DataFrame(), pysat.Meta()
            
        data = {}
        meta = pysat.Meta()
        for key in cdf.iterkeys():
            data[key] = cdf[key][...]
            try:             
                meta[key] = {'units':cdf[key].attrs['UNITS'],
                            'long_name':cdf[key].attrs['LABLAXIS'], 
                            'description':cdf[key].attrs['CATDESC']} 
                #meta[key] = {'description':cdf[key].attrs['VAR_NOTES']}          
            except KeyError:
                pass
        epoch = data.pop('Epoch')
	data = pysat.DataFrame(data, index=pds.to_datetime(epoch, unit='s'))
	return data, meta.copy()

def download(date_array, tag, data_path=None, user=None, password=None):
    """
    download vefi 1_second magnetic field data, layout consistent with pysat

    start and stop should be datetimes
    """
    import os
    import ftplib

    ftp = ftplib.FTP('cdaweb.gsfc.nasa.gov')   # connect to host, default port
    ftp.login()               # user anonymous, passwd anonymous@
    
    if tag == 'dc_b':
        ftp.cwd('/pub/data/cnofs/vefi/bfield_1sec')
    
        for date in date_array:
            fname = '{year1:4d}/cnofs_vefi_bfield_1sec_{year2:4d}{month:02d}{day:02d}_v05.cdf'
            fname = fname.format(year1=date.year, year2=date.year, month=date.month, day=date.day)
            local_fname = 'cnofs_vefi_bfield_1sec_{year:4d}{month:02d}{day:02d}_v05.cdf'.format(
                    year=date.year, month=date.month, day=date.day)
            saved_fname = os.path.join(data_path,local_fname) 
            try:
                print 'Downloading file for '+date.strftime('%D')
                sys.stdout.flush()
                ftp.retrbinary('RETR '+fname, open(saved_fname,'w').write)
            except ftplib.error_perm as exception:
                if exception[0][0:3] != '550':
                    raise
                else:
                    os.remove(saved_fname)
                    print 'File not available for '+ date.strftime('%D')
