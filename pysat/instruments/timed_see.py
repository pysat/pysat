# -*- coding: utf-8 -*-
"""Supports the SEE instrument on TIMED.

Downloads data from the NASA Coordinated Data
Analysis Web (CDAWeb).

Supports two options for loading that may be
specified at instantiation.

Parameters
----------
platform : string
    'timed'
name : string
    'see'
tag : string
    None
sat_id : string
    None supported
flatten_twod : bool (True)
    If True, then two dimensional data is flattened across
    columns. Name mangling is used to group data, first column
    is 'name', last column is 'name_end'. In between numbers are
    appended 'name_1', 'name_2', etc. All data for a given 2D array
    may be accessed via, data.loc[:, 'item':'item_end']
    If False, then 2D data is stored as a series of DataFrames,
    indexed by Epoch. data.loc[0, 'item']

Note
----
- no tag required

Warnings
--------
- Currently no cleaning routine.

"""

from __future__ import print_function
from __future__ import absolute_import
import datetime as dt
import functools
import logging

from pysat.instruments.methods import general as mm_gen
from pysat.instruments.methods import nasa_cdaweb as cdw

logger = logging.getLogger(__name__)

# include basic instrument info
platform = 'timed'
name = 'see'
tags = {'': ''}
sat_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}


# support list files routine
# use the default CDAWeb method
fname = 'timed_l3a_see_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags,
                               fake_daily_files_from_monthly=True)

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/timed/see/data/level3a_cdf',
             'remote_fname': '{year:4d}/{month:02d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)
# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)

# support load routine
# use the default CDAWeb method
load = functools.partial(cdw.load, fake_daily_files_from_monthly=True)


# code should be defined below as needed
def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.


    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    rules_url = 'http://www.timed.jhuapl.edu/WWW/scripts/mdc_rules.pl'
    ackn_str = ' '.join(('Please see the Rules of the Road at',
                         rules_url))
    logger.info(ackn_str)
    self.acknowledgements = ackn_str
    self.references = ' '.join(('Woods, T. N., Eparvier, F. G., Bailey,',
                                     'S. M., Chamberlin, P. C., Lean, J.,',
                                     'Rottman, G. J., Solomon, S. C., Tobiska,',
                                     'W. K., and Woodraska, D. L. (2005),',
                                     'Solar EUV Experiment (SEE): Mission',
                                     'overview and first results, J. Geophys.',
                                     'Res., 110, A01312,',
                                     'doi:10.1029/2004JA010765.'))

    return


def clean(inst):
    """Routine to return TIMED SEE data cleaned to the specified level

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
    --------
    No cleaning currently available.
    """

    return None
