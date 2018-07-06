# -*- coding: utf-8 -*-
"""Supports the SEE instrument on TIMED.

Downloads data from the NASA Coordinated Data 
Analysis Web (CDAWeb).

Supports two options for loading that may be
specified at instantiation.

Parameters
----------
platform : string
    'timed'
name : string
    'see'
tag : string
    None
flatten_twod : bool (True)
    If True, then two dimensional data is flattened across 
    columns. Name mangling is used to group data, first column
    is 'name', last column is 'name_end'. In between numbers are 
    appended 'name_1', 'name_2', etc. All data for a given 2D array
    may be accessed via, data.ix[:,'item':'item_end']
    If False, then 2D data is stored as a series of DataFrames, 
    indexed by Epoch. data.ix[0, 'item']

Note
----
- no tag required

Warnings
--------
- Currently no cleaning routine.
        
"""

from __future__ import print_function
from __future__ import absolute_import
import functools

import pysat
from . import nasa_cdaweb_methods as cdw

# include basic instrument info
platform = 'timed'
name = 'see'
tags = {'':''}
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}


# support list files routine
# use the default CDAWeb method
fname = 'timed_l3a_see_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'':{'':fname}}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags,
                               fake_daily_files_from_monthly=True)

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/timed/see/data/level3a_cdf',
             'remote_fname': '{year:4d}/{month:02d}/'+fname,
             'local_fname': fname}
supported_tags = {'': basic_tag}
download = functools.partial(cdw.download, supported_tags)

# support load routine
# use the default CDAWeb method
load = functools.partial(cdw.load, fake_daily_files_from_monthly=True)

                    
def clean(inst):
    """Routine to return TIMED SEE data cleaned to the specified level

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
    No cleaning currently available.
    """

    return None
                    
                    
                    
                    
                    


