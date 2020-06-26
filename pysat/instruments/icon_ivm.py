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
from pysat.instruments.icon_euv import icon_ssl_download

import logging
logger = logging.getLogger(__name__)


platform = 'icon'
name = 'ivm'
tags = {'': 'Level 2 public geophysical data'}
# dictionary of sat_ids ad tags supported by each
sat_ids = {'a': [''],
           'b': ['']}
# Note for developers: IVM-A and IVM-B face in opposite directions, and only
# one is expected to have geophysical data at a given time depedning on ram
# direction.  IVM-B data is not available as of Jun 26 2020, as this mode has
# not yet been engaged.  Bypassing tests and warning checks via the password_req
# flag
_test_dates = {'a': {'': dt.datetime(2020, 1, 1)},
               'b': {'': dt.datetime(2020, 1, 1)}}  # IVM-B not yet engaged
_test_download_travis = {'a': {kk: False for kk in tags.keys()}}
_password_req = {'b': {kk: True for kk in tags.keys()}}

aname = 'ICON_L2-7_IVM-A_{year:04d}-{month:02d}-{day:02d}_v02r002.NC'
bname = 'ICON_L2-7_IVM-B_{year:04d}-{month:02d}-{day:02d}_v02r002.NC'
supported_tags = {'a': {'': aname},
                  'b': {'': bname}}

# use the general methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# support download routine
basic_tag_a = {'dir': '/pub/LEVEL.2/IVM-A',
               'remote_fname': '{year:4d}/{doy:03d}/Data/' + aname,
               'local_fname': aname}
basic_tag_b = {'dir': '/pub/LEVEL.2/IVM-B',
               'remote_fname': '{year:4d}/{doy:03d}/Data/' + aname,
               'local_fname': aname}

download_tags = {'a': {'': basic_tag_a},
                 'b': {'': basic_tag_b}}
download = functools.partial(icon_ssl_download, supported_tags=download_tags)


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
