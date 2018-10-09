
# -*- coding: utf-8 -*-
"""Supports the Magnetic Electron Ion Spectrometer (MagEIS) 
onboard the Radiation Belt Storm Probe (RBSP, Van Allen Probe) satellites,
under the Van Allen Probes Mission.
Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb) in CDF format.

Parameters
----------
platform : string
    'rbsp'
name : string
    'mageis'
tag : string
    None supported

Warnings
- No cleaning routines
- Module not written by RBSP team.
--------

Authors
-------
Armando Maldonado, The University of Texas at Dallas, Tue  9 Oct 2018 17:37:14 CDT
Russel Stoneback, The University of Texas at Dallas
       
"""

from __future__ import print_function
from __future__ import absolute_import

import functools

import pandas as pds
import numpy as np

import pysat

from . import nasa_cdaweb_methods as cdw

platform = 'rbsp'
name = 'mageis'
tags = {'':''}
sat_ids = {'':['']}

# support list files routine
# use the default CDAWeb method
mageis_fname = 'rbspa_rel03_ect-mageis-l3_{year:4d}{month:02d}{day:02d}_v?????.cdf'
supported_tags = {'':{'':mageis_fname}}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir':'/pub/data/rbsp/rbspa/l3/ect/mageis/sectors/rel03',
            'remote_fname':'{year:4d}/'+mageis_fname,
            'local_fname':mageis_fname}
supported_tags = {'':basic_tag}
download = functools.partial(cdw.download, supported_tags) 

