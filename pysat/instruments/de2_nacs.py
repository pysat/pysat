# -*- coding: utf-8 -*-
"""Supports the Neutral Atmosphere Composition Spectrometer (NACS) instrument
on Dynamics Explorer 2 (DE2).

From CDAWeb:

The Neutral Atmosphere Composition Spectrometer (NACS) was designed to obtain
in situ measurements of the neutral atmospheric composition and to study the
variations of the neutral atmosphere in response to energy coupled into it from
the magnetosphere.  Because temperature enhancements, large-scale circulation
cells, and wave propagation are produced by energy input (each of which
posseses a specific signature in composition variation), the measurements
permitted the study of the partition, flow, and deposition of energy from the
magnetosphere. Specifically, the investigation objective was to characterize
the composition of the neutral atmosphere with particular emphasis on
variability in constituent densities driven by interactions in the atmosphere,
ionosphere, and magnetosphere system. The quadrupole mass spectrometer used was
nearly identical to those flown on the AE-C, -D, and -E missions. The electron-
impact ion source was used in a closed mode. Atmospheric particles entered an
antechamber through a knife-edged orifice, where they were thermalized to the
instrument temperature. The ions with the selected charge-to-mass ratios had
stable trajectories through the hyperbolic electric field, exited the analyzer,
and entered the detection system. An off-axis beryllium-copper dynode
multiplier operating at a gain of 2.E6 provided an output pulse of electrons
for each ion arrival. The detector output had a pulse rate proportional to the
neutral density in the ion source of the selected mass. The instrument also
included two baffles that scanned across the input orifice for optional
measurement of the zonal and vertical components of the neutral wind. The mass
select system provided for 256 mass values between 0 and 51 atomic mass units
(u) or each 0.2 u. It was possible to call any one of these mass numbers into
each of eight 0.016-s intervals. This sequence was repeated each 0.128 s.

This data set includes daily files of the PI-provided DE-2 NACS 1-second data
and corresponding orbit parameters.  The data set was generated at NSSDC from
the original PI-provided data and software (SPTH-00010) and from the
orbit/attitude database and software that is part of the DE-2 UA data set
(SPIO-00174). The original NACS data were provided by the PI team in a highly
compressed VAX/VMS binary format on magnetic tapes. The data set covers the
whole DE-2 mission time period. Each data point is an average over the normally
8 measurements per second. Densities and relative errors are provided for
atomic oxygen (O), molecular nitrogen (N2), helium (He), atomic nitrogen (N),
and argon (Ar).  The data quality is generally quite good below 500 km, but
deteriorates towards higher altitudes as oxygen and molecular nitrogen approach
their background values (which could only be determined from infrequent
spinning orbits) and the count rate for Ar becomes very low. The difference
between minimum (background) and maximum count rate for atomic nitrogen
(estimated from mass 30) was so small that results are generally poor.  Data
were lost between 12 March 1982 and 31 March 1982 when the counter overflowed.


References
----------
G. R. Carrignan, B. P. Block, J. C. Maurer,  A. E. Hedin, C. A. Reber,
N. W. Spencer
The neutral mass spectrometer on Dynamics Explorer B
Space Sci. Instrum., v. 5, n. 4, p. 429, 1981.

Properties
----------
platform
    'de2'
name
    'nacs'
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
name = 'nacs'

tags = {'': '1 s cadence Neutral Atmosphere Composition Spectrometer data'}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(1983, 1, 1)}}

fname = 'de2_neutral1s_nacs_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# use the default CDAWeb method
load = cdw.load

# support download routine
basic_tag = {'dir': '/pub/data/de/de2/neutral_gas_nacs/neutral1s_nacs_cdaweb',
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
