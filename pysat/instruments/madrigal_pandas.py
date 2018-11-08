# -*- coding: utf-8 -*-.
"""Supports generalized access to Madrigal Data.

To use this routine, you need to know both the Madrigal Instrument code
as well as the data tag numbers that Madrigal uses to uniquely identify
data sets. Using these codes, the madrigal_methods.py routines will
be used to support downloading and loading of data.


Downloads data from the JRO Madrigal Database.

Parameters
----------
platform : string
    'madrigal'
name : string
    'pandas'
tag : string
    ''

Example
-------
    import pysat
    # download DMSP data from Madrigal
    dmsp = pysat.Instrument('madrigal', 'pandas',
                            madrigal_inst_code=8100,
                            madrigal_tag=10241)
    dmsp.download(pysat.datetime(2017, 12, 30), pysat.datetime(2017, 12, 31), 
                  user='Firstname+Lastname', password='email@address.com')
    dmsp.load(2017,363)

Note
----
    Please provide name and email when downloading data with this routine.

"""

from __future__ import print_function
from __future__ import absolute_import

import functools
import pysat
from . import madrigal_methods as mad_meth
from . import nasa_cdaweb_methods as cdw

platform = 'madrigal'
name = 'pandas'
tags = {'':'General Madrigal data access loaded into pysat via pandas.'}
sat_ids = {'':list(tags.keys())}
# need to sort out test day setting for unit testing
test_dates = {'':{'':pysat.datetime(2010,1,19)}}

# support list files routine
# use the default CDAWeb method
#########
# need a way to get the filename strings for a particular instrument
# I've put in wildcards for now....
#########
jro_fname1 = '*{year:4d}{month:02d}{day:02d}'
jro_fname2 = '.{version:03d}.hdf5'
supported_tags = {ss:{'':jro_fname1 + "*" + jro_fname2}
                  for ss in sat_ids.keys()}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)
                
# let pysat know that data is spread across more than one file
# multi_file_day=True

# Set to False to specify using xarray (not using pandas)
# Set to True if data will be returned via a pandas DataFrame
pandas_format = True

# support load routine
load = mad_meth.load

# support download routine
# real download attached during init
# however, pysat requires a method before we get there
download = mad_meth.download

def init(self):
    """Initializes the Instrument object with values specific to JRO ISR
    
    Runs once upon instantiation.
    
    Parameters
    ----------
    self : pysat.Instrument
        This object

    Returns
    --------
    Void : (NoneType)
        Object modified in place.
    
    
    """

    print (mad_meth.cedar_rules())
    
    code = self.kwargs['madrigal_code']
    tag = self.kwargs['madrigal_tag']
    self._download_rtn = functools.partial(_general_download, 
                                      inst_code=str(code),
                                      kindat=str(tag))
    return

def _general_download(date_array, tag='', sat_id='', data_path=None, user=None,
             password=None, inst_code=None, kindat=None):
    """Downloads data from Madrigal.
    
    Method will be partially set using functools.partial. Intended to
    have the same call structure as normal instrument download routine.
    Upon Instrument instantiation this routine will be set to
    parameters specific to a Madrigal data set. It will then work like
    a standard download call.
    
    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : string ('')
        Tag identifier used for particular dataset. This input is provided by
        pysat.
    sat_id : string  ('')
        Satellite ID string identifier used for particular dataset. This input
        is provided by pysat.
    data_path : string (None)
        Path to directory to download data to.
    user : string (None)
        User string input used for download. Provided by user and passed via
        pysat. If an account
        is required for dowloads this routine here must error if user not
        supplied.
    password : string (None)
        Password for data download.
    inst_code : int
        Madrigal integer code used to identify platform
    kindat : int
        Madrigal integer code used to identify data set
        
    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.
    
    Notes
    -----
    The user's names should be provided in field user. Ruby Payne-Scott should
    be entered as Ruby+Payne-Scott

    The password field should be the user's email address. These parameters
    are passed to Madrigal when downloading.

    The affiliation field is set to pysat to enable tracking of pysat downloads.

    """
    mad_meth.download(date_array, inst_code=inst_code,
                      kindat=kindat,
                      data_path=data_path, user=user, password=password)

   
        
def clean(self):
    """Routine to return JRO ISR data cleaned to the specified level

    Returns
    --------
    Void : (NoneType)
        data in inst is modified in-place.

    Notes
    --------
    Supports 'clean', 'dusty', 'dirty'
    'Clean' is unknown for oblique modes, over 200 km for drifts
    'Dusty' is unknown for oblique modes, over 200 km for drifts
    'Dirty' is unknown for oblique modes, over 200 km for drifts
    'None' None

    Routine is called by pysat, and not by the end user directly.
    
    """
    if self.clean_level in ['clean', 'dusty']:
        print('WARNING: Generalized Madrigal data support has no cleaning.')
    
    return
