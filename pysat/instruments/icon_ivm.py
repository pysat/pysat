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
    ivm = pysat.Instrument('icon', 'ivm', sat_id='a', tag='level_2',
                           clean_level='clean')
    ivm.download(pysat.datetime(2019, 1, 30), pysat.datetime(2019, 12, 31))
    ivm.load(2017,363)

Author
------
R. A. Stoneback

"""

from __future__ import print_function
from __future__ import absolute_import

import functools
import numpy as np
import pandas as pds
import warnings

import pysat
from .methods import nasa_cdaweb as cdw


platform = 'icon'
name = 'ivm'
tags = {'level_2': 'Level 2 public geophysical data'}
# dictionary of sat_ids ad tags supported by each
sat_ids = {'a': ['level_2'],
           'b': ['level_2']}
test_dates = {'a': {'level_2': pysat.datetime(2018, 1, 1)},
              'b': {'level_2': pysat.datetime(2018, 1, 1)}}


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

    print("Mission acknowledgements and data restrictions will be printed " +
          "here when available.")

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

    remove_icon_names(inst)


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
        inst = pysat.Instrument('icon', 'ivm', sat_id='a', tag='level_2')
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


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of files corresponding to ICON IVM.

    This routine is invoked by pysat and is not intended for direct use by
    the end user.

    Multiple data levels may be supported via the 'tag' input string.
    Currently defaults to level-2 data, or L2 in the filename.

    Parameters
    ----------
    tag : string ('')
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    sat_id : string ('')
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    data_path : string
        Full path to directory containing files to be loaded. This
        is provided by pysat. The user may specify their own data path
        at Instrument instantiation and it will appear here.
    format_str : string (None)
        String template used to parse the datasets filenames. If a user
        supplies a template string at Instrument instantiation
        then it will appear here, otherwise defaults to None.

    Returns
    -------
    pandas.Series
        Series of filename strings, including the path, indexed by datetime.

    Examples
    --------
    ::
        If a filename is SPORT_L2_IVM_2019-01-01_v01r0000.NC then the template
        is 'SPORT_L2_IVM_{year:04d}-{month:02d}-{day:02d}_' +
        'v{version:02d}r{revision:04d}.NC'

    Note
    ----
    The returned Series should not have any duplicate datetimes. If there are
    multiple versions of a file the most recent version should be kept and the
    rest discarded. This routine uses the pysat.Files.from_os constructor, thus
    the returned files are up to pysat specifications.

    """

    desc = None
    tag = 'level_2'
    if tag == 'level_1':
        code = 'L1'
        desc = None
    elif tag == 'level_2':
        code = 'L2'
        desc = None
    else:
        raise ValueError('Unsupported tag supplied: ' + tag)

    if format_str is None:
        format_str = 'ICON_'+code+'_IVM-'+sat_id.upper()
        if desc is not None:
            format_str += '_' + desc + '_'
        format_str += '_{year:4d}-{month:02d}-{day:02d}'
        format_str += '_v{version:02d}r{revision:03d}.NC'

    return pysat.Files.from_os(data_path=data_path,
                               format_str=format_str)


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

    warnings.warn("Downloads aren't yet available.")

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


def remove_icon_names(inst, target=None):
    """Removes leading text on ICON project variable names

    Parameters
    ----------
    inst : pysat.Instrument
        ICON associated pysat.Instrument object
    target : str
        Leading string to remove. If none supplied,
        ICON project standards are used to identify and remove
        leading text

    Returns
    -------
    None
        Modifies Instrument object in place


    """

    if target is None:
        lev = inst.tag
        if lev == 'level_2':
            lev = 'L2'
        elif lev == 'level_0':
            lev = 'L0'
        elif lev == 'level_0p':
            lev = 'L0P'
        elif lev == 'level_1.5':
            lev = 'L1-5'
        elif lev == 'level_1':
            lev = 'L1'
        else:
            raise ValueError('Uknown ICON data level')

        # get instrument code
        sid = inst.sat_id.lower()
        if sid == 'a':
            sid = 'IVM_A'
        elif sid == 'b':
            sid = 'IVM_B'
        else:
            raise ValueError('Unknown ICON satellite ID')
        prepend_str = '_'.join(('ICON', lev, sid)) + '_'
    else:
        prepend_str = target

    inst.data.rename(columns=lambda x: x.split(prepend_str)[-1], inplace=True)
    inst.meta.data.rename(index=lambda x: x.split(prepend_str)[-1],
                          inplace=True)
    orig_keys = inst.meta.keys_nD()
    for keynd in orig_keys:
        new_key = keynd.split(prepend_str)[-1]
        new_meta = inst.meta.pop(keynd)
        new_meta.data.rename(index=lambda x: x.split(prepend_str)[-1],
                             inplace=True)
        inst.meta[new_key] = new_meta

    return
