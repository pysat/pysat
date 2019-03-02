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

References
----------
W. B. Hanson, R. A. Heelis, R. A. Power, C. R. Lippincott, D. R. Zuccaro,
B. J. Holt, L. H. Harmon, and S. Sanatani, “The retarding potential analyzer
for dynamics explorer-B,” Space Sci. Instrum. 5, 503–510 (1981).

Parameters
----------
platform : string
    Supports 'de2'
name : string
    Supports 'rpa'
sat_id : string
    None Supported
tag : string
    None Supported

Note
----
::

    Notes

Warnings
--------


Authors
-------

"""

from __future__ import print_function
from __future__ import absolute_import

import functools
import sys

import numpy as np
import pandas as pds

import pysat
from . import nasa_cdaweb_methods as cdw

# the platform and name strings associated with this instrument
# need to be defined at the top level
# these attributes will be copied over to the Instrument object by pysat
# the strings used here should also be used to name this file
# platform_name.py
platform = 'de2'
name = 'rpa'

# dictionary of data 'tags' and corresponding description
tags = {'': 'description 1',  # this is the default
        'tag_string': 'description 2'}

# Let pysat know if there are multiple satellite platforms supported
# by these routines
# define a dictionary keyed by satellite ID, each with a list of
# corresponding tags
# sat_ids = {'a':['L1', 'L0'], 'b':['L1', 'L2'], 'c':['L1', 'L3']}
sat_ids = {'': ['']}

test_dates = {'': {'': pysat.datetime(1983, 1, 1)}}

fname = 'de2_ion2s_rpa_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}

# use the CDAWeb methods list files routine
list_files = functools.partial(cdw.list_files,
                               supported_tags=supported_tags)

#
# support load routine
#
# use the default CDAWeb method
load = cdw.load

#
# support download routine
basic_tag = {'dir': '/pub/data/de/de2/plasma_rpa/ion2s_cdaweb',
             'remote_fname': '{year:4d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)

# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


# code should be defined below as needed
def default(self):
    """Default customization function.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue).

    Parameters
    ----------
    self : pysat.Instrument
        This object

    Returns
    --------
    Void : (NoneType)
        Object modified in place.


    """

    return


# code should be defined below as needed
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
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Returns
    --------
    Void : (NoneType)
        data in inst is modified in-place.

    Notes
    -----

    """

    return
