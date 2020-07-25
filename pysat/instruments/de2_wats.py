# -*- coding: utf-8 -*-
"""Supports the Wind and Temperature Spectrometer (WATS) instrument on
Dynamics Explorer 2 (DE2).

From CDAWeb:

The Wind and Temperature Spectrometer (WATS) measured the in situ neutral
winds, the neutral particle temperatures, and the concentrations of selected
gases. The objective of this investigation was to study the interrelationships
among the winds, temperatures, plasma drift, electric fields, and other
properties of the thermosphere that were measured by this and other instruments
on the spacecraft. Knowledge of how these properties are interrelated
contributed to an understanding of the consequences of the acceleration of
neutral particles by the ions in the ionosphere, the acceleration of ions by
neutrals creating electric fields, and the related energy transfer between the
ionosphere and the magnetosphere. Three components of the wind, one normal to
the satellite velocity vector in the horizontal plane, one vertical, and one in
the satellite direction were measured. A retarding potential quadrupole mass
spectrometer, coupled to the atmosphere through a precisely orificed
antechamber, was used. It was operated in either of two modes: one employed the
retarding capability and the other used the ion source as a conventional
nonretarding source. Two scanning baffles were used in front of the mass
spectrometer: one moved vertically and the other moved horizontally. The
magnitudes of the horizontal and vertical components of the wind normal to the
spacecraft velocity vector were computed from measurements of the angular
relationship between the neutral particle stream and the sensor. The component
of the total stream velocity in the satellite direction was measured directly
by the spectrometer system through determination of the required retarding
potential.  At altitudes too high for neutral species measurements, the planned
operation required the instrument to measure the thermal ion species only.  A
series of four sequentially occurring slots --each a 2-s long measurement
interval-- was adapted for the basic measurement format of the instrument.
Different functions were commanded into these slots in any combination, one per
measurement interval. Thus the time resolution can be 2, 4, 6, or 8 seconds.
Further details are found in This data set consists of the high-resolution data
of the Dynamics Explorer 2 Wind and Temperature Spectrometer (WATS) experiment.
The files contain the neutral density, temperature and horizontal (zonal) wind
velocity, and orbital parameters in ASCII format. The time resolution is
typically 2 seconds. Data are given as daily files (typically a few 100 Kbytes
each). PI-provided software (WATSCOR) was used to correct the binary data set.
NSSDC-developed software was used to add the orbit parameters, to convert the
binary into ASCII format and to combine the (PI-provided) orbital files into
daily files. For more on DE-2, WATS, and the binary data, see the
WATS_VOLDESC_SFDU_DE.DOC and WATS_FORMAT_SFDU_DE.DOC files. More information
about the processing done at NSSDC is given in WATS_NSSDC_PRO_DE.DOC.


References
----------
N. W. Spencer, L. E. Wharton, H. B. Niemann, A. E. Hedin, G. R. Carrignan,
J. C. Maurer
The Dynamics Explorer Wind and Temperature Spectrometer
Space Sci. Instrum., v. 5, n. 4, p. 417, 1981.

Properties
----------
platform
    'de2'
name
    'wats'
sat_id
    None Supported
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
name = 'wats'

tags = {'': '2 s cadence Wind and Temperature Spectrometer data'}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(1983, 1, 1)}}

fname = 'de2_wind2s_wats_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# use the default CDAWeb method
load = cdw.load

# support download routine
basic_tag = {'dir': '/pub/data/de/de2/neutral_gas_wats/wind2s_wats_cdaweb',
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
