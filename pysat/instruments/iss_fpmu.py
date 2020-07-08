# -*- coding: utf-8 -*-
"""Supports the Floating Potential Measurement Unit
(FPMU) instrument onboard the International Space
Station (ISS). Downloads data from the NASA
Coordinated Data Analysis Web (CDAWeb).

Parameters
----------
platform : string
    'iss'
name : string
    'fpmu'
tag : string
    None Supported
sat_id : string
    None supported

Warnings
--------
- Currently clean only replaces fill values with Nans.
- Module not written by FPMU team.

"""
from __future__ import print_function
from __future__ import absolute_import
import datetime as dt
import functools
import numpy as np

from pysat.instruments.methods import general as mm_gen
from pysat.instruments.methods import nasa_cdaweb as cdw

platform = 'iss'
name = 'fpmu'
tags = {'': ''}
sat_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2017, 10, 1)}}

# support list files routine
# use the default CDAWeb method
fname = 'iss_sp_fpmu_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/international_space_station_iss/sp_fpmu',
             'remote_fname': '{year:4d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)

# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


def clean(inst):
    """Return FPMU data cleaned to the specified level.

    Parameters
    ----------
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Returns
    -------
    Void : (NoneType)
        data in inst is modified in-place.

    """

    inst.data.replace(-999., np.nan, inplace=True)  # Te
    inst.data.replace(-9.9999998e+30, np.nan, inplace=True)  # Ni

    return None
