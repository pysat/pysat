# -*- coding: utf-8 -*-
"""Supports the <Instrument Name> 
onboard the <Mission Platform>. Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb).

Parameters
----------
platform : string
    <Platform Identifier>
name : string
    <Instrument Identifier>
tag : string
    Select measurement type, one of {<Sub-Type Identifiers>}

Note
----
- tag = <sub-type strings> : <Brief Info on sub-types>

Warnings
--------
- Currently no cleaning routine.
- Module not written by <Instrument Name> team.
        
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
        Denotes type of file to load.  Accepted types are <tag strings>. (default=None)
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
        # values from VEFI are used here, replace with equivalent for your
        # instrument
        if tag == 'dc_b':
            if format_str is None:
                # default naming scheme for VEFI DC_B files from NASA CDAWeb
                format_str = \
                'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
            return pysat.Files.from_os(data_path=data_path, 
                                       format_str=format_str)
        else:
            raise ValueError('Unknown tag')
    else:
        estr = 'A directory must be passed to the loading routine for <Instrument Code>'
        raise ValueError (estr)            

def load(fnames, tag=None, sat_id=None):
    """Load <Instrument> files

    Parameters
    ------------
    fnames : (pandas.Series)
        Series of filenames
    tag : (str or NoneType)
        tag or None (default=None)
    sat_id : (str or NoneType)
        satellite id or None (default=None)

    Returns
    ---------
    data : (pandas.DataFrame)
        Object containing satellite data
    meta : (pysat.Meta)
        Object containing metadata such as column names and units
    """
    import pysatCDF

    if len(fnames) <= 0 :
        return pysat.DataFrame(None), None
    else:
        # going to use pysatCDF to load the CDF and format
        # data and metadata for pysat using some assumptions.
        # Depending upon your needs the resulting pandas DataFrame may
        # need modification 
        # currently only loads one file, which handles more situations via pysat
        # than you may initially think
        with pysatCDF.CDF(fnames[0]) as cdf:
            return cdf.to_pysat()

def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    """
    Download <Instrument> data, layout consistent with pysat

    start and stop should be datetimes
    """
    """Routine to download <Instrument> data

    Parameters
    -----------
    date_array : array_like
        Array of datetimes to download data for. Provided by pysat.
    tag : (str or NoneType)
        tag or None (default=None)
    sat_id : (str or NoneType)
        satellite id or None (default=None)
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    user : (string or NoneType)
        Username to be passed along to resource with relevant data.  
        (default=None)
    password : (string or NoneType)
        User password to be passed along to resource with relevant data.  
        (default=None)

    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.

    """

    import os
    import ftplib

    # connect to CDAWeb default port
    ftp = ftplib.FTP('cdaweb.gsfc.nasa.gov')   
    # user anonymous, passwd anonymous@
    ftp.login()               
    
    if tag == 'dc_b':
        # path to relevant file on CDAWeb
        # using VEFI DC_B as an example
        ftp.cwd('/pub/data/cnofs/vefi/bfield_1sec')
        
        # naming scheme for files on the CDAWeb server
        remote_fname = '{year1:4d}/cnofs_vefi_bfield_1sec_{year2:4d}{month:02d}{day:02d}_v05.cdf'
        
        # naming scheme for local files, should be closely related
        # to CDAWeb scheme, though directory structures may be reduced
        # if desired
        local_fname = 'cnofs_vefi_bfield_1sec_{year:4d}{month:02d}{day:02d}_v05.cdf'
    else:
        raise ValueError('Tag name unknown.')
        
    for date in date_array:
        # format files for specific dates and download location
        formatted_remote_fname = remote_fname.format(year1=date.year, 
                        year2=date.year, month=date.month, day=date.day)
        formatted_local_fname = local_fname.format(year=date.year, 
                        month=date.month, day=date.day)
        saved_local_fname = os.path.join(data_path,formatted_local_fname) 

        # perform download                  
        try:
            print('Downloading file for '+date.strftime('%D'))
            sys.stdout.flush()
            ftp.retrbinary('RETR '+formatted_remote_fname, open(saved_local_fname,'w').write)
        except ftplib.error_perm as exception:
            if exception[0][0:3] != '550':
                raise
            else:
                os.remove(saved_local_fname)
                print('File not available for '+ date.strftime('%D'))
                
                    
def clean(inst):
    """Routine to return <Instrument> data cleaned to the specified level

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Returns
    --------
    Void : (NoneType)
        data in inst is modified in-place.

    Notes
    --------
    No cleaning currently available for <Instrument>
    """

    return None
                    
                    
                    
                    
                    


