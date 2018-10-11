
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
from collections import defaultdict
import pandas as pds
import numpy as np

import pysat

from . import nasa_cdaweb_methods as cdw

platform = 'rbsp'
name = 'mageis'
sat_ids=['a','b']
tags=['l2','l3','l4']

# support list files routine
# use the default CDAWeb method
supported_tags_fname=defaultdict(dict)
for sat_id in sat_ids:
    for tag in tags:
        fname='rbsp'+sat_id+'_rel03_ect-mageis-'+tag +'{year:4d}{month:02d{day:02d}_v?????.cdf' 
        supported_tags_fname[sat_id][tag]=fname

list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags_fname)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
supported_tags_download=defaultdict(dict)
for sat_id in sat_ids:
    for tag in tags:
        download_dict = {'dir':'/pub/data/rbsp/rbsp'+sat_id+'/'+tag
                        +'/ect/mageis/sectors/rel03',
                        'remote_fname':'{year:4d}/'
                         +supported_tags_fname[sat_id][tag],
                        'local_fname':supported_tags_fname[sat_id][tag]}
        
        supported_tags_download[sat_id][tag]=download_dict

download = functools.partial(cdw.download, 
                             supported_tags=supported_tags_download) 

