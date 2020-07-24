# -*- coding: utf-8 -*-
"""Supports the Langmuir Probe (LANG) instrument on Dynamics Explorer 2 (DE2).

From CDAWeb:

The Langmuir Probe Instrument (LANG) was a cylindrical electrostatic probe that
obtained measurements of electron temperature, Te, and electron or ion
concentration, Ne or Ni, respectively, and spacecraft potential.  Data from
this investigation were used to provide temperature and density measurements
along magnetic field lines related to thermal energy and particle flows within
the magnetosphere-ionosphere system, to provide thermal plasma conditions for
wave-particle interactions, and to measure large-scale and fine-structure
ionospheric effects of energy deposition in the ionosphere.  The Langmuir Probe
instrument was identical to that used on the AE satellites and the Pioneer
Venus Orbiter. Two independent sensors were connected to individual adaptive
sweep voltage circuits which continuously tracked the changing electron
temperature and spacecraft potential, while autoranging electrometers adjusted
their gain in response to the changing plasma density. The control signals used
to achieve this automatic tracking provided a continuous monitor of the
ionospheric parameters without telemetering each volt-ampere (V-I) curve.
Furthermore, internal data storage circuits permitted high resolution, high
data rate sampling of selected V-I curves for transmission to ground to verify
or correct the inflight processed data. Time resolution was 0.5 seconds.


References
----------
J. P. Krehbiel, L. H. Brace, R. F. Theis, W. H. Pinkus, and R. B. Kaplan,
The Dynamics Explorer 2 Langmuir Probe (LANG), Space Sci. Instrum., v. 5, n. 4,
p. 493, 1981.

Properties
----------
platform
    'de2'
name
    'lang'
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
name = 'lang'

tags = {'': '500 ms cadence Langmuir Probe data'}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(1983, 1, 1)}}

fname = 'de2_plasma500ms_lang_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# use the default CDAWeb method
load = cdw.load

# support download routine
basic_tag = {'dir': '/pub/data/de/de2/plasma_lang/plasma500ms_lang_cdaweb',
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
