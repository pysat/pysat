# -*- coding: utf-8 -*-
"""Supports the Planar Langmuir Probe (PLP) onboard the Communication
and Navigation Outage Forecasting System (C/NOFS) satellite. Downloads
data from the NASA Coordinated Data Analysis Web (CDAWeb).

Description from CDAWeb:

The Planar Langmuir Probe on C/NOFS is a suite of 2 current measuring sensors
mounted on the ram facing surface of the spacecraft.  The primary sensor is an
Ion Trap (conceptually similar to RPAs flown on many other spacecraft) capable
of measuring ion densities as low as 1 cm-3 with a 12 bit log electrometer.
The secondary senor is a swept bias planar Langmuir probe (Surface Probe)
capable of measuring Ne, Te, and spacecraft potential.

The ion number density is the one second average of the ion density sampled at
either 32, 256, 512, or 1024 Hz (depending on the mode).

The ion density standard deviation is the standard deviation of the samples
used to produce the one second average number density.

DeltaN/N is the detrened ion number density 1 second standard deviation divided
by the mean 1 sec density.

The electron density, electron temperature, and spacecraft potential are all
derived from a least squares fit to the current-bias curve from the Surface
Probe.

The data is PRELIMINARY, and as such, is intended for BROWSE PURPOSES ONLY.

References
----------
A brief discussion of the C/NOFS mission and instruments can be found at
de La Beaujardière, O., et al. (2004), C/NOFS: A mission to forecast
scintillations, J. Atmos. Sol. Terr. Phys., 66, 1573–1591,
doi:10.1016/j.jastp.2004.07.030.

Properties
----------
platform
    'cnofs'
name
    'plp'
tag
    None supported
sat_id
    None supported

Warnings
--------
- The data are PRELIMINARY, and as such, are intended for BROWSE PURPOSES ONLY.
- Currently no cleaning routine.
- Module not written by PLP team.

"""

from __future__ import print_function
from __future__ import absolute_import
import functools
import numpy as np

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw
from pysat.instruments.methods import general as mm_gen

platform = 'cnofs'
name = 'plp'
tags = {'': ''}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}


# support list files routine
# use the default CDAWeb method
fname = 'cnofs_plp_plasma_1sec_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/cnofs/plp/plasma_1sec',
             'remote_fname': '{year:4d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)
# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


def clean(inst):
    """Routine to return C/NOFS PLP data cleaned to the specified level

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Notes
    --------
    Basic cleaning to find valid Epoch values

    """

    for key in inst.data.columns:
        if key != 'Epoch':
            idx, = np.where(inst[key] == inst.meta[key, inst.fill_label])
            inst[idx, key] = np.nan
