# -*- coding: utf-8 -*-
"""Supports the Ion Velocity Meter (IVM) 
onboard the Communication and Navigation Outage Forecasting
System (C/NOFS) satellite, part of the Coupled Ion Netural Dynamics 
Investigation (CINDI). Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb) in CDF format.

Parameters
----------
platform : string
    'cnofs'
name : string
    'ivm'
tag : string
    None supported

Warnings
--------
- The sampling rate of the instrument changes on July 29th, 2010.
  The rate is attached to the instrument object as .sample_rate.

- The cleaning parameters for the instrument are still under development.
       
"""
from __future__ import print_function
from __future__ import absolute_import

import functools

import pandas as pds
import numpy as np

import pysat

from . import nasa_cdaweb_methods as cdw

platform = 'cnofs'
name = 'ivm'
tags = {'':''}
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}


# support list files routine
# use the default CDAWeb method
ivm_fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'':ivm_fname}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir':'/pub/data/cnofs/cindi/ivm_500ms_cdf',
            'remote_fname':'{year:4d}/'+ivm_fname,
            'local_fname':ivm_fname}
supported_tags = {'':basic_tag}
download = functools.partial(cdw.download, supported_tags)


def default(ivm):
    ivm.sample_rate = 1.0 if ivm.date >= pysat.datetime(2010, 7, 29) else 2.0
   
        
def clean(self):
    """Routine to return C/NOFS IVM data cleaned to the specified level

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
    Supports 'clean', 'dusty', 'dirty'
    
    """

    # cleans cindi data
    if self.clean_level == 'clean':
        # choose areas below 550km
        # self.data = self.data[self.data.alt <= 550]
        idx, = np.where(self.data.altitude <= 550)
        self.data = self.data.iloc[idx,:]
    
    # make sure all -999999 values are NaN
    self.data.replace(-999999., np.nan, inplace=True)
    # idx, idy, = np.where(self.data == -999999.)
    # self.data.iloc[idx,idy] = np.nan

    if (self.clean_level == 'clean') | (self.clean_level == 'dusty'):
        try:
            # self.data = self.data[(abs(self.data.iv_mer) < 10000.)]
            idx, = np.where(np.abs(self.data.ionVelmeridional) < 10000.)
            self.data = self.data.iloc[idx,:]
        except AttributeError:
            pass
        # take out all values where RPA data quality is > 3
        # self.data = self.data[self.data.rpa_flag <= 3]
        idx, = np.where(self.data.RPAflag <= 3)
        self.data = self.data.iloc[idx,:]

        # enforce minimum RPA density if RPA flag eqal to 3
        o_dens = self.data.ionDensity*self.data.ion1fraction
        # self.data = self.data[-((o_dens < 3.E4) & (self.data.rpa_flag==3))]
        idx, = np.where(-((o_dens < 3.E4) & (self.data.RPAflag==3)))
        self.data = self.data.iloc[idx,:]
        
        # IDM quality flags
        self.data = self.data[ (self.data.driftMeterflag>= 90) & (self.data.driftMeterflag % 10 < 1) ]
        idx, = np.where((self.data.driftMeterflag>= 90) & (self.data.driftMeterflag % 10 < 1))
        self.data = self.data.iloc[idx,:]

    # basic quality check on drifts and don't let UTS go above 86400.
    # self.data = self.data[ (self.data.uts <= 86400.)]
    idx, = np.where(self.data.time <= 86400.)
    self.data = self.data.iloc[idx,:]
    
    # make sure MLT is between 0 and 24
    # self.data = self.data[(self['mlt'] >= 0.) & (self['mlt'] <= 24.)]
    idx, = np.where((self.data.mlt >= 0) & (self.data.mlt <= 24.))
    self.data = self.data.iloc[idx,:]
    return

