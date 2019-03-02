# -*- coding: utf-8 -*-
"""Supports the Ion Drift Meter (IDM) instrument on
Dynamics Explorer 2 (DE2).

From CDAWeb:

The Ion Drift Meter (IDM) measured the bulk motions of the ionospheric plasma
perpendicular to the satellite velocity vector. The measured parameters,
horizontal and vertical ion-drift velocities, had an expected range of plus or
minus 4 km/s. The accuracy of the measurement was expected to be plus or minus
50 m/s for the anticipated 0.5 deg accuracy in vehicle attitude determination.
The nominal time resolution of the measurement was 1/32 s. This investigation
yielded information on (1) the ion convection (electric field) pattern in the
auroral and polar ionosphere; (2) the flow of plasma along magnetic field lines
within the plasmasphere, which determines whether this motion was simply a
breathing of the protonosphere, a refilling of this region after a storm, or an
interhemispheric transport of plasma; (3) the thermal ion contribution to
field-aligned electric currents; (4) velocity fields associated with small-
scale phenomena that are important at both low and high latitudes; and (5) the
magnitude and variation of the total concentration along the flight path. The
ion drift meter measured the plasma motion parallel to the sensor face by using
a gridded collimator and multiple collectors to determine the direction of
arrival of the plasma. The instrument geometry was very similar to that used on
the Atmosphere Explorer satellites. Each sensor consisted of a square entrance
aperture that served as collimator, some electrically isolating grids, and a
segmented planar collector. The angle of arrival of the ions with respect to
the sensor was determined by measuring the ratio of the currents to the
different collector segments, and this was done by taking the difference in the
logarithms of the current. Two techniques were used to determine this ratio. In
the standard drift sensor (SDS), the collector segments were connected in pairs
to two logarithmic amplifiers. The second technique, called the univeral drift
sensor (UDS), allowed simultaneous measurement of both components. Here, each
collector segment was permanently connected to a logarithmic amplifier and two
difference amplifiers were used to determine the horizontal and vertical
arrival angles simultaneously. The IDM consisted of two sensors, one providing
the SDS output and the other providing the UDS output. During the period
from 81317 to 82057 the instrument memory suffered a critical upset and ion
temperatures and drifts are not available during this period.
This data set is available from NSSDC's anonymous ftp archive at
ftp://nssdcftp.gsfc.nasa.gov/spacecraft_data/de/de2/plasma_idm/ It includes the
high-resolution data from the Dynamics Explorer 2 (DE-2) Ion Drift Meter (IDM)
for the whole DE-2 mission time period in ASCII format. This data set was
generated at NSSDC by converting the PI-provided data set (SPIO-00232) from
binary to ASCII format. The IDM data files provide absolute measurements of the
cross track ion drift velocity 4 times per second. The complete drift vector
can be obtained by combining IDM and RPA ion drift measurements.


References
----------
R. A. Heelis, W. B. Hanson, C. R. Lippincott, D. R. Zuccaro, L. H. Harmon,
B. J. Holt, J. E. Doherty, R. A. Power,
The Ion Drift Meter for Dynamics Explorer-B,
Space Sci. Instrum., v. 5, n. 4, p. 511, 1981.

Parameters
----------
platform : string
    Supports 'de2'
name : string
    Supports 'idm'
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
name = 'idm'

# dictionary of data 'tags' and corresponding description
tags = {'': '250 ms cadence Ion Drift Meter data'}

# Let pysat know if there are multiple satellite platforms supported
# by these routines
# define a dictionary keyed by satellite ID, each with a list of
# corresponding tags
# sat_ids = {'a':['L1', 'L0'], 'b':['L1', 'L2'], 'c':['L1', 'L3']}
sat_ids = {'': ['']}

test_dates = {'': {'': pysat.datetime(1983, 1, 1)}}

fname = 'de2_vion250ms_idm_{year:04d}{month:02d}{day:02d}_v01.cdf'
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
basic_tag = {'dir': '/pub/data/de/de2/plasma_idm/vion250ms_cdaweb',
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
