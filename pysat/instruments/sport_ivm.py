# -*- coding: utf-8 -*-
"""
Ion Velocity Meter (IVM) support for the NASA/INPE SPORT CubeSat.

This mission is still in development. This routine is here to help
with the development of code associated with SPORT and the IVM.

"""

import functools
import logging
import warnings

import pysat
from pysat.instruments.methods import general as mm_gen

logger = logging.getLogger(__name__)


# pysat required parameters
platform = 'sport'
name = 'ivm'
# dictionary of data 'tags' and corresponding description
tags = {'': 'Level-2 IVM Files',
        'L1': 'Level-1 IVM Files',
        'L0': 'Level-0 IVM Files'}
# dictionary of satellite IDs, list of corresponding tags
# only one satellite in this case
sat_ids = {'': ['']}
# good day to download test data for. Downloads aren't currently supported
_test_dates = {'': {'': pysat.datetime(2019, 1, 1)}}

prefix = 'SPORT_{tag}_IVM_'
format_str = ''.join(('{year:04d}-{month:02d}-{day:02d}',
                      '_v{version:02d}r{revision:04d}.NC'))
supported_tags = {'': {'': ''.join((prefix.format(tag='L2'), format_str)),
                       'L1': ''.join((prefix.format(tag='L1'), format_str)),
                       'L0': ''.join((prefix.format(tag='L0'), format_str))}}
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    """

    logger.info(' '.join(("Mission acknowledgements and data restrictions will",
                          "be printed here when available.")))

    pass


def load(fnames, tag=None, sat_id=None, **kwargs):
    """Loads SPORT IVM data using pysat.utils.load_netcdf4.

    This routine is called as needed by pysat. It is not intended
    for direct user interaction.

    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : string
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    sat_id : string
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    **kwargs : extra keywords
        Passthrough for additional keyword arguments specified when
        instantiating an Instrument object. These additional keywords
        are passed through to this routine by pysat.

    Returns
    -------
    data, metadata
        Data and Metadata are formatted for pysat. Data is a pandas
        DataFrame while metadata is a pysat.Meta instance.

    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine and through
    to the load_netcdf4 call.

    Examples
    --------
    ::

        inst = pysat.Instrument('sport', 'ivm')
        inst.load(2019, 1)

    """

    return pysat.utils.load_netcdf4(fnames, **kwargs)


def download(date_array, tag, sat_id, data_path=None, user=None,
             password=None):
    """Downloads data for SPORT IVM, once SPORT is operational and in orbit.

    This routine is invoked by pysat and is not intended for direct use by
    the end user.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need
        not be contiguous.
    tag : string ('')
        Tag identifier used for particular dataset. This input is provided by
        pysat.
    sat_id : string  ('')
        Satellite ID string identifier used for particular dataset. This input
        is provided by pysat.
    data_path : string (None)
        Path to directory to download data to.
    user : string (None)
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied.
    password : string (None)
        Password for data download.

    """

    warnings.warn('Downloads are not currently supported - not launched yet!')

    pass
