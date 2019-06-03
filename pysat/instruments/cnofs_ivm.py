# -*- coding: utf-8 -*-
"""Supports the Ion Velocity Meter (IVM) onboard the Communication
and Navigation Outage Forecasting System (C/NOFS) satellite, part
of the Coupled Ion Netural Dynamics Investigation (CINDI). Downloads
data from the NASA Coordinated Data Analysis Web (CDAWeb) in CDF
format.

The IVM is composed of the Retarding Potential Analyzer (RPA) and
Drift Meter (DM). The RPA measures the energy of plasma along the
direction of satellite motion. By fitting these measurements
to a theoretical description of plasma the number density, plasma
composition, plasma temperature, and plasma motion may be determined.
The DM directly measures the arrival angle of plasma. Using the reported
motion of the satellite the angle is converted into ion motion along
two orthogonal directions, perpendicular to the satellite track.

A brief discussion of the C/NOFS mission and instruments can be found at
de La Beaujardière, O., et al. (2004), C/NOFS: A mission to forecast
scintillations, J. Atmos. Sol. Terr. Phys., 66, 1573–1591,
doi:10.1016/j.jastp.2004.07.030.

Parameters
----------
platform : string
    'cnofs'
name : string
    'ivm'
tag : string
    None supported
sat_id : string
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

import numpy as np

import pysat

from .methods import nasa_cdaweb as cdw

platform = 'cnofs'
name = 'ivm'
tags = {'': ''}
sat_ids = {'': ['']}
test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}


# support list files routine
# use the default CDAWeb method
fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}
list_files = functools.partial(cdw.list_files,
                               supported_tags=supported_tags)

# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/cnofs/cindi/ivm_500ms_cdf',
             'remote_fname': '{year:4d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)
# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


def default(ivm):
    ivm.sample_rate = 1.0 if ivm.date >= pysat.datetime(2010, 7, 29) else 2.0


def clean(inst):
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
    if inst.clean_level == 'clean':
        # choose areas below 550km
        # inst.data = inst.data[inst.data.alt <= 550]
        idx, = np.where(inst.data.altitude <= 550)
        inst.data = inst[idx, :]

    # make sure all -999999 values are NaN
    inst.data.replace(-999999., np.nan, inplace=True)

    if (inst.clean_level == 'clean') | (inst.clean_level == 'dusty'):
        try:
            idx, = np.where(np.abs(inst.data.ionVelmeridional) < 10000.)
            inst.data = inst[idx, :]
        except AttributeError:
            pass

        if inst.clean_level == 'dusty':
            # take out all values where RPA data quality is > 1
            idx, = np.where(inst.data.RPAflag <= 1)
            inst.data = inst[idx, :]
            # IDM quality flags
            inst.data = inst.data[(inst.data.driftMeterflag <= 3)]
        else:
            # take out all values where RPA data quality is > 0
            idx, = np.where(inst.data.RPAflag <= 0)
            inst.data = inst[idx, :]
            # IDM quality flags
            inst.data = inst.data[(inst.data.driftMeterflag <= 0)]
    if inst.clean_level == 'dirty':
        # take out all values where RPA data quality is > 4
        idx, = np.where(inst.data.RPAflag <= 4)
        inst.data = inst[idx, :]
        # IDM quality flags
        inst.data = inst.data[(inst.data.driftMeterflag <= 6)]

    # basic quality check on drifts and don't let UTS go above 86400.
    idx, = np.where(inst.data.time <= 86400.)
    inst.data = inst[idx, :]

    # make sure MLT is between 0 and 24
    idx, = np.where((inst.data.mlt >= 0) & (inst.data.mlt <= 24.))
    inst.data = inst[idx, :]
    return
