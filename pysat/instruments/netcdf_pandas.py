# -*- coding: utf-8 -*-
"""
Generic module for loading netCDF4 files into the pandas format within pysat.

This file may be used as a template for adding pysat support for a new dataset
based upon netCDF4 files, or other file types (with modification).

This routine may also be used to add quick local support for a netCDF4 based
dataset without having to define an instrument module for pysat. Relevant
parameters may be specified when instantiating this Instrument object to
support the relevant file location and naming schemes. This presumes the pysat
developed utils.load_netCDF4 routine is able to load the file. See the load 
routine docstring in this module for more.

The routines defined within may also be used when adding a new instrument to pysat
by importing this module and using the functools.partial methods to attach these
functions to the new instrument model. See pysat/instruments/cnofs_ivm.py for more.
NASA CDAWeb datasets, such as C/NOFS IVM, use the methods within 
pysat/instruments/nasa_cdaweb_methods.py to make adding new CDAWeb instruments easy.

"""

import pandas as pds
import numpy as np
import pysat

# pysat required parameters
platform = 'netcdf'
name = 'pandas'
# dictionary of data 'tags' and corresponding description
tags = {'':'netCDF4'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}


        
def init(self):
    """Initializes the Instrument object with instrument specific values.
    
    Runs once upon instantiation. This routine provides a convenient
    location to print Acknowledgements or restrictions from the mission. 
    
    """
    
    pass

                
def load(fnames, tag=None, sat_id=None, **kwargs):
    """Loads data using pysat.utils.load_netcdf4 .

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
        Data and Metadata are formatted for pysat. Data is a pandas 
        DataFrame while metadata is a pysat.Meta instance.
        
    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine and through
    to the load_netcdf4 call.
    
    Examples
    --------
    ::
    
        inst = pysat.Instrument('sport', 'ivm')
        inst.load(2019,1)
    
        # create quick Instrument object for a new, random netCDF4 file
        # define filename template string to identify files
        # this is normally done by instrument code, but in this case
        # there is no built in pysat instrument support
        # presumes files are named default_2019-01-01.NC
        format_str = 'default_{year:04d}-{month:02d}-{day:02d}.NC'
        inst = pysat.Instrument('netcdf', 'pandas', 
                                custom_kwarg='test'
                                data_path='./',
                                format_str=format_str)
        inst.load(2019,1)
    
    """
    
    return pysat.utils.load_netcdf4(fnames, **kwargs)


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of files corresponding to format_str located at data_path.

    This routine is invoked by pysat and is not intended for direct use by the end user.
    
    Multiple data levels may be supported via the 'tag' and 'sat_id' input strings.

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
    
    Normally the format_str for each supported tag and sat_id is defined within this routine.
    However, as this is a generic routine, those definitions can't be made here. This method
    could be used in an instrument specific module where the list_files routine in the
    new package defines the format_str based upon inputs, then calls this routine passing
    both data_path and format_str.
    
    Alternately, the list_files routine in nasa_cdaweb_methods may also be used and has
    more built in functionality. Supported tages and format strings may be defined
    within the new instrument module and passed as arguments to nasa_cdaweb_methods.list_files .
    For an example on using this routine, see pysat/instrument/cnofs_ivm.py or cnofs_vefi, cnofs_plp,
    omni_hro, timed_see, etc.
    
    """
    
    return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    """Downloads data for supported instruments, however this is a template call.
    
    This routine is invoked by pysat and is not intended for direct use by the end user.
    
    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not be contiguous.
    tag : string ('')
        Tag identifier used for particular dataset. This input is provided by pysat.
    sat_id : string  ('')
        Satellite ID string identifier used for particular dataset. This input is provided by pysat.
    data_path : string (None)
        Path to directory to download data to.
    user : string (None)
        User string input used for download. Provided by user and passed via pysat. If an account
        is required for dowloads this routine here must error if user not supplied.
    password : string (None)
        Password for data download.
        
    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.
    
    
    """

    print ('This is a generic Instrument routine and does not support downloading data.')
    pass
