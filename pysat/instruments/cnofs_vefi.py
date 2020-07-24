# -*- coding: utf-8 -*-
"""Supports the Vector Electric Field Instrument (VEFI)
onboard the Communication and Navigation Outage Forecasting
System (C/NOFS) satellite. Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb).

Description from CDAWeb:

The DC vector magnetometer on the CNOFS spacecraft is a three axis, fluxgate
sensor with active thermal control situated on a 0.6m boom.  This magnetometer
measures the Earth's magnetic field using 16 bit A/D converters at 1 sample per
sec with a range of .. 45,000 nT.  Its primary objective on the CNOFS
spacecraft is to enable an accurate V x B measurement along the spacecraft
trajectory.  In order to provide an in-flight calibration of the magnetic field
data, we compare the most recent POMME model (the POtsdam Magnetic Model of the
Earth, http://geomag.org/models/pomme5.html) with the actual magnetometer
measurements to help determine a set of calibration parameters for the gains,
offsets, and non-orthogonality matrix of the sensor axes.  The calibrated
magnetic field measurements are provided in the data file here. The VEFI
magnetic field data file currently contains the following variables:
B_north   Magnetic field in the north direction
B_up      Magnetic field in the up direction
B_west    Magnetic field in the west direction

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
    'vefi'
tag
    Select measurement type, one of {'dc_b'}
sat_id
    None supported

Note
----
- tag = 'dc_b': 1 second DC magnetometer data

Warnings
--------
- The data is PRELIMINARY, and as such, is intended for BROWSE PURPOSES ONLY.
- Limited cleaning routine.
- Module not written by VEFI team.

"""

from __future__ import print_function
from __future__ import absolute_import
import functools
import numpy as np

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw
from pysat.instruments.methods import general as mm_gen

platform = 'cnofs'
name = 'vefi'
tags = {'dc_b': 'DC Magnetometer data - 1 second'}
sat_ids = {'': ['dc_b']}
_test_dates = {'': {'dc_b': pysat.datetime(2009, 1, 1)}}

# support list files routine
# use the default CDAWeb method
fname = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
supported_tags = {'': {'dc_b': fname}}
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/cnofs/vefi/bfield_1sec',
             'remote_fname': '{year:4d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'dc_b': basic_tag}}
download = functools.partial(cdw.download, supported_tags)
# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


def clean(inst):
    """Routine to return VEFI data cleaned to the specified level

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Notes
    --------
    'dusty' or 'clean' removes data when interpolation flag is set to 1

    """

    if (inst.clean_level == 'dusty') | (inst.clean_level == 'clean'):
        idx, = np.where(inst['B_flag'] == 0)
        inst.data = inst[idx, :]

    return None
