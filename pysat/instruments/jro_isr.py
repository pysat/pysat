# -*- coding: utf-8 -*-.
"""Supports the Incoherent Scatter Radar at the Jicamarca Radio Observatory

The Incoherent Scatter Radar (ISR) at the Jicamarca Radio Observatory (JRO)
observes ion drifts, line-of-sight neutral winds, electron density and
temperature, ion temperature, and ion composition through three overarching
experiments.

Downloads data from the JRO Madrigal Database.

Parameters
----------
platform : string
    'jro'
name : string
    'isr'
tag : string
    'drifts', 'drifts_ave', 'oblique_stan', 'oblique_rand', 'oblique_long'

Example
-------
    import pysat
    dmsp = pysat.Instrument('jro', 'isr', 'drifts', clean_level='clean')
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

platform = 'jro'
name = 'isr'
tags = {'drifts':'Drifts and wind', 'drifts_ave':'Averaged drifts',
        'oblique_stan':'Standard Faraday rotation double-pulse',
        'oblique_rand':'Randomized Faraday rotation double-pulse',
        'oblique_long':'Long pulse Faraday rotation'}
sat_ids = {'':list(tags.keys())}
test_dates = {'':{'drifts':pysat.datetime(2010,1,19),
                  'drifts_ave':pysat.datetime(2010,1,19),
                  'oblique_stan':pysat.datetime(2010,4,19),
                  'oblique_rand':pysat.datetime(2000,11,9),
                  'oblique_long':pysat.datetime(2010,4,12)}}

# support list files routine
# use the default CDAWeb method
jro_fname1 = 'jro{year:4d}{month:02d}{day:02d}'
jro_fname2 = '.{version:03d}.hdf5'
supported_tags = {ss:{'drifts':jro_fname1 + "drifts" + jro_fname2,
                      'drifts_ave':jro_fname1 + "drifts_ave" + jro_fname2,
                      'oblique_stan':jro_fname1 + jro_fname2,
                      'oblique_rand':jro_fname1 + "?" + jro_fname2,
                      'oblique_rand':jro_fname1 + "?" + jro_fname2}
                  for ss in sat_ids.keys()}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)

# madrigal tags
madrigal_inst_code = 10
madrigal_tag = {'':{'drifts':1910, 'drifts_ave':1911, 'oblique_stan':1800,
                    'oblique_rand':1801, 'oblique_long':1802},}
                
# let pysat know that data is spread across more than one file
# multi_file_day=True

# Set to False to specify using xarray (not using pandas)
# Set to True if data will be returned via a pandas DataFrame
pandas_format = True

# support load routine
load = mad_meth.load

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

    print ("The Jicamarca Radio Observatory is operated by the Instituto " +
           "Geofisico del Peru, Ministry of Education, with support from the" +
           " National Science Foundation as contracted through Cornell" +
           " University.  " + mad_meth.cedar_rules())
    return

def download(date_array, tag='', sat_id='', data_path=None, user=None,
             password=None):
    """Downloads data from Madrigal.
    
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
    mad_meth.download(date_array, inst_code=str(madrigal_inst_code),
                      kindat=str(madrigal_tag[sat_id][tag]),
                      data_path=data_path, user=user, password=password)


def default(self):
    pass
   
        
def clean(self):
    """Routine to return JRO ISR data cleaned to the specified level

    Returns
    --------
    Void : (NoneType)
        data in inst is modified in-place.

    Notes
    --------
    Supports 'clean', 'dusty', 'dirty'
    'Clean' is unknown
    'Dusty' is unknown
    'Dirty' is unknown
    'None' None

    Routine is called by pysat, and not by the end user directly.
    
    """

    if self.clean_level in ['clean', 'dusty', 'dirty']:
        print('WARNING: this level 1 data has no quality flags')
    idx = []

    # downselect data based upon cleaning conditions above
    self.data = self[idx]
        
    return
