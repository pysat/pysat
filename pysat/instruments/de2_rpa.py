# -*- coding: utf-8 -*-
"""Supports the Retarding Potential Analyzer (RPA) instrument on
Dynamics Explorer 2 (DE2).

From CDAWeb:

The Retarding Potential Analyzer (RPA) measured the bulk ion velocity in the
direction of the spacecraft motion, the constituent ion concentrations, and the
ion temperature along the satellite path. These parameters were derived from a
least squares fit to the ion number flux vs energy curve obtained by sweeping
or stepping the voltage applied to the internal retarding grids of the RPA. In
addition, a separate wide aperture sensor, a duct sensor, was flown to measure
the spectral characteristics of iregularities in the total ion concentration.
The measured parameters obtained from this investigation were important to the
understanding of mechanisms that influence the plasma; i.e., to understand the
coupling between the solar wind and the earth's atmosphere. The measurements
were made with a multigridded planar retarding potential analyzer very similar
in concept and geometry to the instruments carried on the AE satellites. The
retarding potential was variable in the range from approximately +32 to 0 V.
The details of this voltage trace, and whether it was continuous or stepped,
depended on the operating mode of the instrument. Specific parameters deduced
from these measurements were ion temperature; vehicle potential; ram component
of the ion drift velocity; the ion and electron concentration irregularity
spectrum; and the concentration of H+, He+, O+, and Fe+, and of molecular ions
near perigee.

It includes the DUCT portion of the high resolutiondata from the Dynamics
Explorer 2 (DE-2) Retarding Potential Analyzer (RPA) for the whole DE-2 mission
time period in ASCII format. This version was generated at NSSDC from the
PI-provided binary data (SPIO-00232). The DUCT files include RPA measurements
ofthe total ion concentration every 64 times per second. Due to a failure in
the instrument memory system RPA data are not available from 81317 06:26:40 UT
to 82057 13:16:00 UT. This data set is based on the revised version of the RPA
files that was submitted by the PI team in June of 1995. The revised RPA data
include a correction to the spacecraft potential.

References
----------
W. B. Hanson, R. A. Heelis, R. A. Power, C. R. Lippincott, D. R. Zuccaro,
B. J. Holt, L. H. Harmon, and S. Sanatani, “The retarding potential analyzer
for dynamics explorer-B,” Space Sci. Instrum. 5, 503–510 (1981).

Properties
----------
platform
    'de2'
name
    'rpa'
sat_id
    ''
tag
    None Supported

Authors
-------
J. Klenzing

"""

from __future__ import print_function
from __future__ import absolute_import

import functools

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw
from pysat.instruments.methods import general as mm_gen

platform = 'de2'
name = 'rpa'

tags = {'': '2 sec cadence RPA data'}  # this is the default
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(1983, 1, 1)}}

fname = 'de2_ion2s_rpa_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# use the default CDAWeb method
load = cdw.load

# support download routine
basic_tag = {'dir': '/pub/data/de/de2/plasma_rpa/ion2s_cdaweb',
             'remote_fname': '{year:4d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)

# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


def clean(inst):
    """Routine to return PLATFORM/NAME data cleaned to the specified level

    Cleaning level is specified in inst.clean_level and pysat
    will accept user input for several strings. The clean_level is
    specified at instantiation of the Instrument object.

    'clean' All parameters should be good, suitable for statistical and
            case studies
    'dusty' All paramers should generally be good though same may
            not be great
    'dirty' There are data areas that have issues, data should be used
            with caution
    'none'  No cleaning applied, routine not called in this case.


    Parameters
    -----------
    inst : pysat.Instrument
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    """

    return
