# -*- coding: utf-8 -*-
"""Supports the Vector Electric Field Instrument (VEFI) 
onboard the Communication and Navigation Outage Forecasting
System (C/NOFS) satellite. Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb).

Parameters
----------
platform : string
    'cnofs'
name : string
    'vefi'
tag : string
    Select measurement type, one of {'dc_b'}

Note
----
- tag = 'dc_b': 1 second DC magnetometer data

Warnings
--------
- Currently no cleaning routine.
- Module not written by VEFI team.
        
"""

from __future__ import print_function
from __future__ import absolute_import
import pandas as pds
import numpy as np
import pysat
import sys


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are 'dc_b'. (default=None)
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

    if data_path is not None:
        if tag == 'dc_b':
            dc_fmt = \
                'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
            return pysat.Files.from_os(data_path=data_path, format_str=dc_fmt)
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
        
        with pysatCDF.CDF(fnames[0]) as cdf:
            return cdf.to_pysat()

def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
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
                print('Downloading file for '+date.strftime('%D'))
                sys.stdout.flush()
                ftp.retrbinary('RETR '+fname, open(saved_fname,'w').write)
            except ftplib.error_perm as exception:
                if exception[0][0:3] != '550':
                    raise
                else:
                    os.remove(saved_fname)
                    print('File not available for '+ date.strftime('%D'))
                    
                    
                    
                    
                    
                    
                    



        #try:
        #    cdf = pysatCDF.CDF(fnames[0])
        #except pysatCDF.CDFError:
        #    return pysat.DataFrame(), pysat.Meta()
        #    
        #data = {}
        #meta = pysat.Meta()
        #for key in cdf.iterkeys():
        #    data[key] = cdf[key][...]
        #    try:             
        #        meta[key] = {'units':cdf[key].attrs['UNITS'],
        #                    'long_name':cdf[key].attrs['LABLAXIS'], 
        #                    'description':cdf[key].attrs['CATDESC']} 
        #        #meta[key] = {'description':cdf[key].attrs['VAR_NOTES']}          
        #    except KeyError:
        #        pass
        #epoch = data.pop('Epoch')
        #data = pysat.DataFrame(data, index=pds.to_datetime(epoch, unit='s'))
        #return data, meta

