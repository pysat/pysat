# -*- coding: utf-8 -*-
"""Provides default routines for integrating NASA CDAWeb instruments into pysat.
Adding new CDAWeb datasets should only require mininal user intervention.
 
"""

from __future__ import absolute_import, division, print_function

import pandas as pds
import numpy as np
import pysat
import sys


def list_files(tag=None, sat_id=None, data_path=None, format_str=None,
               supported_tags=None, fake_daily_files_from_monthly=False,
               two_digit_year_break=None):
    """Return a Pandas Series of every file for chosen satellite data.
    
    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

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
    supported_tags : (dict or NoneType)
        keys are tags supported by list_files routine. Values are the
        default format_str values for key. (default=None)
    fake_daily_files_from_monthly : bool
        Some CDAWeb instrument data files are stored by month, interfering
        with pysat's functionality of loading by day. This flag, when true,
        appends daily dates to monthly files internally. These dates are
        used by load routine in this module to provide data by day. 

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    Examples
    --------
    :: 

        fname = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
        supported_tags = {'dc_b':fname}
        list_files = functools.partial(nasa_cdaweb_methods.list_files, 
                                       supported_tags=supported_tags)

        ivm_fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
        supported_tags = {'':ivm_fname}
        list_files = functools.partial(cdw.list_files, 
                                       supported_tags=supported_tags)
    
    """

    if data_path is not None:
        if format_str is None:
                try:
                    format_str = supported_tags[sat_id][tag]
                except KeyError:
                    raise ValueError('Unknown tag')
        out = pysat.Files.from_os(data_path=data_path, 
                                  format_str=format_str)

        if (not out.empty) and fake_daily_files_from_monthly:
            out.ix[out.index[-1] + pds.DateOffset(months=1) -
                                   pds.DateOffset(days=1)] = out.iloc[-1]  
            out = out.asfreq('D', 'pad')
            out = out + '_' + out.index.strftime('%Y-%m-%d')  
            return out

        return out
    else:
        estr = 'A directory must be passed to the loading routine for <Instrument Code>'
        raise ValueError (estr)            

def load(fnames, tag=None, sat_id=None, 
         fake_daily_files_from_monthly=False,
         flatten_twod=True):
    """Load NASA CDAWeb CDF files.
    
    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

    Parameters
    ------------
    fnames : (pandas.Series)
        Series of filenames
    tag : (str or NoneType)
        tag or None (default=None)
    sat_id : (str or NoneType)
        satellite id or None (default=None)
    fake_daily_files_from_monthly : bool
        Some CDAWeb instrument data files are stored by month, interfering
        with pysat's functionality of loading by day. This flag, when true,
        parses of daily dates to monthly files that were added internally
        by the list_files routine, when flagged. These dates are
        used here to provide data by day. 

    Returns
    ---------
    data : (pandas.DataFrame)
        Object containing satellite data
    meta : (pysat.Meta)
        Object containing metadata such as column names and units
        
    Examples
    --------
    ::
    
        # within the new instrument module, at the top level define
        # a new variable named load, and set it equal to this load method
        # code below taken from cnofs_ivm.py.
        
        # support load routine
        # use the default CDAWeb method
        load = cdw.load

        
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
        
        if fake_daily_files_from_monthly:
            # parse out date from filename
            fname = fnames[0][0:-11]
            date = pysat.datetime.strptime(fnames[0][-10:], '%Y-%m-%d')
            with pysatCDF.CDF(fname) as cdf:
                # convert data to pysat format
                data, meta = cdf.to_pysat(flatten_twod=flatten_twod)
                # select data from monthly
                data = data.ix[date:date+pds.DateOffset(days=1) - pds.DateOffset(microseconds=1),:]
                return data, meta     
        else:
            # basic data return 
            with pysatCDF.CDF(fnames[0]) as cdf:     
                return cdf.to_pysat(flatten_twod=flatten_twod)

def download(supported_tags, date_array, tag, sat_id, 
             ftp_site='cdaweb.gsfc.nasa.gov', 
             data_path=None, user=None, password=None,
             fake_daily_files_from_monthly=False):
    """Routine to download NASA CDAWeb CDF data.
    
    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

    Parameters
    -----------
    supported_tags : dict
        dict of dicts. Keys are supported tag names for download. Value is 
        a dict with 'dir', 'remote_fname', 'local_fname'. Inteded to be
        pre-set with functools.partial then assigned to new instrument code.
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
    fake_daily_files_from_monthly : bool
        Some CDAWeb instrument data files are stored by month.This flag, 
        when true, accomodates this reality with user feedback on a monthly
        time frame. 

    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.

    Examples
    --------
    :: 
    
        # download support added to cnofs_vefi.py using code below
        rn = '{year:4d}/cnofs_vefi_bfield_1sec_{year:4d}{month:02d}{day:02d}_v05.cdf'
        ln = 'cnofs_vefi_bfield_1sec_{year:4d}{month:02d}{day:02d}_v05.cdf'
        dc_b_tag = {'dir':'/pub/data/cnofs/vefi/bfield_1sec',
                    'remote_fname':rn,
                    'local_fname':ln}
        supported_tags = {'dc_b':dc_b_tag}
    
        download = functools.partial(nasa_cdaweb_methods.download, 
                                     supported_tags=supported_tags)
    
    """

    import os
    import ftplib

    # connect to CDAWeb default port
    ftp = ftplib.FTP(ftp_site) 
    # user anonymous, passwd anonymous@
    ftp.login()               
    
    try:
        ftp_dict = supported_tags[tag]
    except KeyError:
        raise ValueError('Tag name unknown.')
        
    # path to relevant file on CDAWeb
    ftp.cwd(ftp_dict['dir'])
    
    # naming scheme for files on the CDAWeb server
    remote_fname = ftp_dict['remote_fname']
    
    # naming scheme for local files, should be closely related
    # to CDAWeb scheme, though directory structures may be reduced
    # if desired
    local_fname = ftp_dict['local_fname']
    
    for date in date_array:            
        # format files for specific dates and download location
        formatted_remote_fname = remote_fname.format(year=date.year, 
                        month=date.month, day=date.day)
        formatted_local_fname = local_fname.format(year=date.year, 
                        month=date.month, day=date.day)
        saved_local_fname = os.path.join(data_path,formatted_local_fname) 

        # perform download                  
        try:
            print('Attempting to download file for '+date.strftime('%x'))
            sys.stdout.flush()
            ftp.retrbinary('RETR '+formatted_remote_fname, open(saved_local_fname,'wb').write)
            print('Finished.')
        except ftplib.error_perm as exception:
            # if exception[0][0:3] != '550':
            if str(exception.args[0]).split(" ", 1)[0] != '550':
                raise
            else:
                os.remove(saved_local_fname)
                print('File not available for '+ date.strftime('%x'))
    ftp.close()
               
                    
                    
                    
                    
                    


