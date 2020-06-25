# -*- coding: utf-8 -*-

"""Supports the Ion Velocity Meter (IVM)
onboard the Ionospheric Connections (ICON) Explorer.

Parameters
----------
platform : string
    'icon'
name : string
    'ivm'
tag : string
    None supported
sat_id : string
    'a' or 'b'

Warnings
--------
- No download routine as ICON has not yet been launched
- Data not yet publicly available

Example
-------
    import pysat
    ivm = pysat.Instrument('icon', 'ivm', sat_id='a', clean_level='clean')
    ivm.download(dt.datetime(2020, 1, 1), dt.datetime(2020, 1, 31))
    ivm.load(2020, 1)

Author
------
R. A. Stoneback

"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import functools
import warnings

import pysat
from pysat.instruments.methods import general as mm_gen

import logging
logger = logging.getLogger(__name__)


platform = 'icon'
name = 'ivm'
tags = {'': 'Level 2 public geophysical data'}
# dictionary of sat_ids ad tags supported by each
sat_ids = {'a': [''],
           'b': ['']}
_test_dates = {'a': {'': dt.datetime(2020, 1, 1)},
               'b': {'': dt.datetime(2020, 1, 1)}}
_test_download = {'a': {kk: False for kk in tags.keys()},
                  'b': {kk: False for kk in tags.keys()}}

aname = 'ICON_L2-7_IVM-A_{year:04d}-{month:02d}-{day:02d}_v02r002.NC'
bname = 'ICON_L2-7_IVM-B_{year:04d}-{month:02d}-{day:02d}_v02r002.NC'
supported_tags = {'a': {'': aname},
                  'b': {'': bname}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    Returns
    --------
    Void : (NoneType)
        modified in-place, as desired.

    """

    logger.info(' '.join(("Mission acknowledgements and data restrictions",
                          "will be printed here when available.")))

    pass


def default(inst):
    """Default routine to be applied when loading data.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    Note
    ----
        Removes ICON preamble on variable names.

    """

    mm_gen.remove_leading_text(inst, target='ICON_L27_')


def load(fnames, tag=None, sat_id=None):
    """Loads ICON IVM data using pysat into pandas.

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
    upon instantiation are passed along to this routine.

    Examples
    --------
    ::
        inst = pysat.Instrument('icon', 'ivm', sat_id='a', tag='')
        inst.load(2019,1)

    """

    return pysat.utils.load_netcdf4(fnames, epoch_name='Epoch',
                                    units_label='Units',
                                    name_label='Long_Name',
                                    notes_label='Var_Notes',
                                    desc_label='CatDesc',
                                    plot_label='FieldNam',
                                    axis_label='LablAxis',
                                    scale_label='ScaleTyp',
                                    min_label='ValidMin',
                                    max_label='ValidMax',
                                    fill_label='FillVal')


def download(date_array, tag, sat_id, data_path=None, user=None,
             password=None):
    """Will download data for ICON IVM, after successful launch and operations.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
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
    **kwargs : dict
        Additional keywords supplied by user when invoking the download
        routine attached to a pysat.Instrument object are passed to this
        routine via kwargs.

    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.


    """

    warnings.warn(''.join(("Downloads in pysat not yet supported.  Please ",
                           "download data from ",
                           "ftp://icon-science.ssl.berkeley.edu/pub/LEVEL.2/")))

    return


def clean(inst, clean_level=None):
    """Provides data cleaning based upon clean_level.

    clean_level is set upon Instrument instantiation to
    one of the following:

    'Clean'
    'Dusty'
    'Dirty'
    'None'

    Routine is called by pysat, and not by the end user directly.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Returns
    --------
    Void : (NoneType)
        data in inst is modified in-place.

    Note
    ----
        Supports 'clean', 'dusty', 'dirty', 'none'

    """

    if clean_level != 'none':
        warnings.warn("Cleaning actions for ICON IVM are not yet defined.")
    return
