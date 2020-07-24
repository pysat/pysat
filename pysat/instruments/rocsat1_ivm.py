# -*- coding: utf-8 -*-
"""Supports the Ion Velocity Meter (IVM)
onboard the Republic of China Satellite (ROCSAT-1). Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb).

Properties
----------
platform
    'rocsat1'
name
    'ivm'
tag
    None
sat_id
    None supported

Note
----
- no tag or sat_id required

Warnings
--------
- Currently no cleaning routine.

"""

from __future__ import print_function
from __future__ import absolute_import
import functools
import warnings

import pysat

from pysat.instruments.methods import nasa_cdaweb as cdw
from pysat.instruments.methods import general as mm_gen

platform = 'rocsat1'
name = 'ivm'
tags = {'': ''}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(2002, 1, 1)}}


# support list files routine
# use the default CDAWeb method
fname = 'rs_k0_ipei_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)
# support load routine
# use the default CDAWeb method
load = cdw.load

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/rocsat/ipei',
             'remote_fname': '{year:4d}/'+fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)
# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


def clean(inst):
    """Routine to return ROCSAT-1 IVM data cleaned to the specified level

    Parameters
    -----------
    inst : pysat.Instrument
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Notes
    --------
    No cleaning currently available for ROCSAT-1 IVM.
    """

    warnings.warn("No cleaning currently available for ROCSAT")

    return None
