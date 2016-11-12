# -*- coding: utf-8 -*-
"""Supports the SEE instrument onboard TIMED. 

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
    columns. If False, then 2D data is stored as a series
    of DataFrames, indexed by Epoch.

Note
----
- no tag required

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

import functools


from . import nasa_cdaweb_methods as cdw

# support list files routine
# use the default CDAWeb method
fname = 'timed_l3a_see_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'':fname}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags,
                               fake_daily_files_from_monthly=True)

# support download routine
# use the default CDAWeb method
basic_tag = {'dir':'/pub/data/timed/cdf/see/l3a',
            'remote_fname':'{year:4d}/{month:02d}/'+fname,
            'local_fname':fname}
supported_tags = {'':basic_tag}
download = functools.partial(cdw.download, supported_tags)

# support load routine
# use the default CDAWeb method
#load = functools.partial(cdw.load, fake_daily_files_from_monthly=True,
#                         flatten_twod=True)
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
                    
                    
                    
                    
                    


