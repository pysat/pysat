# -*- coding: utf-8 -*-
"""Supports the Extreme Ultraviolet (EUV) imager onboard the Ionospheric
CONnection Explorer (ICON) satellite.  Accesses local data in
netCDF format.

Properties
----------
platform
    'icon'
name
    'euv'
tag
    None supported


Warnings
--------
- The cleaning parameters for the instrument are still under development.
- Only supports level-2 data.


Examples
--------
::

    import pysat
    euv = pysat.Instrument(platform='icon', name='euv')
    euv.download(dt.datetime(2020, 1, 1), dt.datetime(2020, 1, 31))
    euv.load(2020, 1)

By default, pysat removes the ICON level tags from variable names, ie,
ICON_L27_Ion_Density becomes Ion_Density.  To retain the original names, use
::

    euv = pysat.Instrument(platform='icon', name='euv',
                           keep_original_names=True)


Authors
---------
Jeff Klenzing, Mar 17, 2018, Goddard Space Flight Center
Russell Stoneback, Mar 23, 2018, University of Texas at Dallas

"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import functools
import logging

import pysat
from pysat.instruments.methods import general as mm_gen
from pysat.instruments.methods import icon as mm_icon


logger = logging.getLogger(__name__)

platform = 'icon'
name = 'euv'
tags = {'': 'Level 2 public geophysical data'}
sat_ids = {'': ['']}
_test_dates = {'': {'': dt.datetime(2020, 1, 1)}}
_test_download_travis = {'': {kk: False for kk in tags.keys()}}
pandas_format = False

fname = ''.join(('ICON_L2-6_EUV_{year:04d}-{month:02d}-{day:02d}_',
                 'v{version:02d}r{revision:03d}.NC'))
supported_tags = {'': {'': fname}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# support download routine
basic_tag = {'dir': '/pub/LEVEL.2/EUV',
             'remote_fname': 'Data/' + fname}
download_tags = {'': {'': basic_tag}}
download = functools.partial(mm_icon.ssl_download, supported_tags=download_tags)

# support listing files on SSL
list_remote_files = functools.partial(mm_icon.list_remote_files,
                                      supported_tags=download_tags)


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    """
    logger.info(mm_icon.ackn_str)
    self.meta.acknowledgements = mm_icon.ackn_str
    self.meta.references = ''.join((mm_icon.refs['mission'],
                                    mm_icon.refs['euv']))

    pass


def default(inst):
    """Default routine to be applied when loading data. Adjusts epoch timestamps
    to datetimes and removes variable preambles.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    """

    mm_gen.convert_timestamp_to_datetime(inst, sec_mult=1.0e-3)
    if not inst.kwargs['keep_original_names']:
        mm_gen.remove_leading_text(inst, target='ICON_L26_')


def load(fnames, tag=None, sat_id=None, keep_original_names=False):
    """Loads ICON EUV data using pysat into pandas.

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
    keep_original_names : boolean
        if True then the names as given in the netCDF ICON file
        will be used as is. If False, a preamble is removed.

    Returns
    -------
    data, metadata
        Data and Metadata are formatted for pysat. Data is a pandas
        DataFrame while metadata is a pysat.Meta instance.

    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine.

    The 'Altitude' dimension is renamed as 'Alt' to avoid confusion with the
    'Altitude' variable when performing xarray operations

    Examples
    --------
    ::
        inst = pysat.Instrument('icon', 'euv', sat_id='a', tag='')
        inst.load(2020, 1)

    """

    data, mdata = pysat.utils.load_netcdf4(fnames, epoch_name='Epoch',
                                           units_label='Units',
                                           name_label='Long_Name',
                                           notes_label='Var_Notes',
                                           desc_label='CatDesc',
                                           plot_label='FieldNam',
                                           axis_label='LablAxis',
                                           scale_label='ScaleTyp',
                                           min_label='ValidMin',
                                           max_label='ValidMax',
                                           fill_label='FillVal',
                                           pandas_format=pandas_format)
    # xarray can't merge if variable and dim names are the same
    if 'Altitude' in data.dims:
        data = data.rename({'Altitude': 'Alt'})
    return data, mdata


def clean(inst):
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

    Note
    ----
        Supports 'clean', 'dusty', 'dirty', 'none'. Method is
        not called by pysat if clean_level is None or 'none'.

    """

    vars = ['HmF2', 'NmF2', 'Oplus']
    if 'Flags' in inst.variables:
        icon_flag = 'Flags'
    else:
        icon_flag = 'ICON_L26_Flags'
        vars = ['ICON_L26_' + x for x in vars]

    min_val = {'clean': 1.0,
               'dusty': 2.0}
    if inst.clean_level in ['clean', 'dusty']:
        for var in vars:
            inst[var] = inst[var].where(inst[icon_flag]
                                        <= min_val[inst.clean_level])
    else:
        # dirty and worse lets everything through
        pass
    return
