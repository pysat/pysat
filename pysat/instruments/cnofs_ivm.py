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

References
----------
A brief discussion of the C/NOFS mission and instruments can be found at
de La Beaujardière, O., et al. (2004), C/NOFS: A mission to forecast
scintillations, J. Atmos. Sol. Terr. Phys., 66, 1573–1591,
doi:10.1016/j.jastp.2004.07.030.

Discussion of cleaning parameters for ion drifts can be found in:
Burrell, Angeline G., Equatorial topside magnetic field-aligned ion drifts
at solar minimum, The University of Texas at Dallas, ProQuest
Dissertations Publishing, 2012. 3507604.

Discussion of cleaning parameters for ion temperature can be found in:
Hairston, M. R., W. R. Coley, and R. A. Heelis (2010), Mapping the
duskside topside ionosphere with CINDI and DMSP, J. Geophys. Res.,115,
A08324, doi:10.1029/2009JA015051.


Properties
----------
platform
    'cnofs'
name
    'ivm'
tag
    None supported
sat_id
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

from pysat.instruments.methods import nasa_cdaweb as cdw
from pysat.instruments.methods import general as mm_gen

platform = 'cnofs'
name = 'ivm'
tags = {'': ''}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}


# support list files routine
# use the default CDAWeb method
fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}
list_files = functools.partial(mm_gen.list_files,
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
    inst : pysat.Instrument
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Notes
    --------
    Supports 'clean', 'dusty', 'dirty'

    """

    # make sure all -999999 values are NaN
    inst.data.replace(-999999., np.nan, inplace=True)

    # Set maximum flags
    if inst.clean_level == 'clean':
        max_rpa_flag = 1
        max_dm_flag = 0
    elif inst.clean_level == 'dusty':
        max_rpa_flag = 3
        max_dm_flag = 3
    else:
        max_rpa_flag = 4
        max_dm_flag = 6

    # First pass, keep good RPA fits
    idx, = np.where(inst.data.RPAflag <= max_rpa_flag)
    inst.data = inst[idx, :]

    # Second pass, find bad drifts, replace with NaNs
    idx = (inst.data.driftMeterflag > max_dm_flag)

    # Also exclude very large drifts and drifts where 100% O+
    if (inst.clean_level == 'clean') | (inst.clean_level == 'dusty'):
        if 'ionVelmeridional' in inst.data.columns:
            # unrealistic velocities
            # This check should be performed at the RPA or IDM velocity level
            idx2 = (np.abs(inst.data.ionVelmeridional) >= 10000.0)
            idx = (idx | idx2)

    if len(idx) > 0:
        drift_labels = ['ionVelmeridional', 'ionVelparallel', 'ionVelzonal',
                        'ionVelocityX', 'ionVelocityY', 'ionVelocityZ']
        for label in drift_labels:
            inst[idx, label] = np.NaN

    # Check for bad RPA fits in dusty regime.
    # O+ concentration criteria from Burrell, 2012
    if inst.clean_level == 'dusty' or inst.clean_level == 'clean':
        # Low O+ concentrations for RPA Flag of 3 are suspect and high O+
        # fractions create a shallow fit region for the ram velocity
        nO = inst.data.ion1fraction * inst.data.Ni
        idx = (((inst.data.RPAflag == 3) & (nO <= 3.0e4)) |
               (inst.data.ion1fraction >= 1.0))

        # Only remove data if RPA component of drift is greater than 1%
        unit_vecs = {'ionVelmeridional': 'meridionalunitvectorX',
                     'ionVelparallel': 'parallelunitvectorX',
                     'ionVelzonal': 'zonalunitvectorX'}
        for label in unit_vecs:
            idx0 = idx & (np.abs(inst[unit_vecs[label]]) >= 0.01)
            inst[idx0, label] = np.NaN

        # The RPA component of the ram velocity is always 100%
        inst[idx, 'ionVelocityX'] = np.NaN

        # Check for bad temperature fits (O+ < 15%), replace with NaNs
        # Criteria from Hairston et al, 2010
        idx = inst.data.ion1fraction < 0.15
        inst[idx, 'ionTemperature'] = np.NaN

        # The ion fractions should always sum to one and never drop below zero
        ifracs = ['ion{:d}fraction'.format(i) for i in np.arange(1, 6)]
        ion_sum = np.sum([inst[label] for label in ifracs], axis=0)
        ion_min = np.min([inst[label] for label in ifracs], axis=0)
        idx = ((ion_sum != 1.0) | (ion_min < 0.0))
        for label in ifracs:
            inst[idx, label] = np.NaN

    # basic quality check on drifts and don't let UTS go above 86400.
    idx, = np.where(inst.data.time <= 86400.)
    inst.data = inst[idx, :]

    # make sure MLT is between 0 and 24
    idx, = np.where((inst.data.mlt >= 0) & (inst.data.mlt <= 24.))
    inst.data = inst[idx, :]
    return
