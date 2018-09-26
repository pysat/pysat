# -*- coding: utf-8 -*-
"""Supports the Planar Langmuir Probe (PLP) 
onboard the Communication and Navigation Outage Forecasting
System (C/NOFS) satellite. Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb).

Parameters
----------
platform : string
    'cnofs'
name : string
    'plp'

Warnings
--------
- Currently no cleaning routine.
- Module not written by PLP team.
        
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
name = 'plp'
tags = {'':''}
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}


# support list files routine
# use the default CDAWeb method
fname = 'cnofs_plp_plasma_1sec_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'':{'':fname}}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir':'/pub/data/cnofs/plp/plasma_1sec',
            'remote_fname':'{year:4d}/'+fname,
            'local_fname':fname}
supported_tags = {'':basic_tag}
download = functools.partial(cdw.download, supported_tags)


def clean(inst):
    for key in inst.data.columns:
        if key != 'Epoch':
          idx, = np.where(inst[key] == inst.meta[key, inst.fill_label])
          inst[idx, key] = np.nan


