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
- Limited cleaning routine.
- Module not written by VEFI team.
        
"""

from __future__ import print_function
from __future__ import absolute_import
import pandas as pds
import numpy as np
import pysat
import sys
import functools


from . import nasa_cdaweb_methods as cdw

platform = 'cnofs'
name = 'vefi'
tags = {'dc_b':'DC Magnetometer data - 1 second'}
sat_ids = {'':['dc_b']}
test_dates = {'':{'dc_b':pysat.datetime(2009,1,1)}}

# support list files routine
# use the default CDAWeb method
fname = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
supported_tags = {'':{'dc_b':fname}}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir':'/pub/data/cnofs/vefi/bfield_1sec',
            'remote_fname':'{year:4d}/'+fname,
            'local_fname':fname}
supported_tags = {'dc_b':basic_tag}
download = functools.partial(cdw.download, supported_tags)

                    
def clean(inst):
    """Routine to return VEFI data cleaned to the specified level

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
    'dusty' or 'clean' removes data when interpolation flag is set to 1
    """
    
    if (inst.clean_level == 'dusty') | (inst.clean_level == 'clean'):
        idx, = np.where(inst['B_flag'] == 0)
        inst.data = inst[idx, :]

    return None
                    
                    
                    
                    
                    


