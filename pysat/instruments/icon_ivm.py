# -*- coding: utf-8 -*-

"""Supports the Ion Velocity Meter (IVM)
onboard the Ionospheric Connections (ICON) Explorer.

Properties
----------
platform
    'icon'
name
    'ivm'
tag
    None supported
sat_id
    'a' or 'b'


Warnings
--------
- No download routine as ICON has not yet been launched
- Data not yet publicly available


Example
-------
::

    import pysat
    ivm = pysat.Instrument(platform='icon', name='ivm', sat_id='a')
    ivm.download(dt.datetime(2020, 1, 1), dt.datetime(2020, 1, 31))
    ivm.load(2020, 1)

By default, pysat removes the ICON level tags from variable names, ie,
ICON_L27_Ion_Density becomes Ion_Density.  To retain the original names, use
::

    ivm = pysat.Instrument(platform='icon', name='ivm', sat_id='a',
                           keep_original_names=True)


Author
------
R. A. Stoneback

"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import functools
import logging
import numpy as np

import pysat
from pysat.instruments.methods import general as mm_gen
from pysat.instruments.methods import icon as mm_icon


logger = logging.getLogger(__name__)

platform = 'icon'
name = 'ivm'
tags = {'': 'Level 2 public geophysical data'}
# Note for developers: IVM-A and IVM-B face in opposite directions, and only
# one is expected to have geophysical data at a given time depending on ram
# direction. In general, IVM-A is operational when the remote instruments face
# northward, and IVM-B when the remote instruments face southward. IVM-B data
# is not available as of Jun 26 2020, as this mode has not yet been engaged.
# Bypassing tests and warning checks via the password_req flag
sat_ids = {'a': [''],
           'b': ['']}
_test_dates = {'a': {'': dt.datetime(2020, 1, 1)},
               'b': {'': dt.datetime(2020, 1, 1)}}  # IVM-B not yet engaged
_test_download_travis = {'a': {kk: False for kk in tags.keys()}}
_test_download = {'b': {kk: False for kk in tags.keys()}}
_password_req = {'b': {kk: True for kk in tags.keys()}}

aname = ''.join(('ICON_L2-7_IVM-A_{year:04d}-{month:02d}-{day:02d}_',
                 'v{version:02d}r{revision:03d}.NC'))
bname = ''.join(('ICON_L2-7_IVM-B_{year:04d}-{month:02d}-{day:02d}_',
                 'v{version:02d}r{revision:03d}.NC'))
supported_tags = {'a': {'': aname},
                  'b': {'': bname}}

# use the general methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# support download routine
basic_tag_a = {'dir': '/pub/LEVEL.2/IVM-A',
               'remote_fname': 'Data/' + aname}
basic_tag_b = {'dir': '/pub/LEVEL.2/IVM-B',
               'remote_fname': 'Data/' + bname}

download_tags = {'a': {'': basic_tag_a},
                 'b': {'': basic_tag_b}}
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
                                    mm_icon.refs['ivm']))

    pass


def default(inst):
    """Default routine to be applied when loading data. Removes variable
    preambles.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    """

    if not inst.kwargs['keep_original_names']:
        mm_gen.remove_leading_text(inst, target='ICON_L27_')


def load(fnames, tag=None, sat_id=None, keep_original_names=False):
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

    Examples
    --------
    ::
        inst = pysat.Instrument('icon', 'ivm', sat_id='a', tag='')
        inst.load(2020, 1)

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
        Supports 'clean', 'dusty', 'dirty', 'none'

    """

    # IVM variable groupings
    drift_variables = ['Ion_Velocity_X', 'Ion_Velocity_Zonal',
                       'Ion_Velocity_Meridional',
                       'Ion_Velocity_Field_Aligned']
    cross_drift_variables = ['Ion_Velocity_Z', 'Ion_Velocity_Y']
    rpa_variables = ['Ion_Temperature', 'Ion_Density',
                     'Fractional_Ion_Density_H',
                     'Fractional_Ion_Density_O']
    if 'RPA_Flag' in inst.variables:
        rpa_flag = 'RPA_Flag'
        dm_flag = 'DM_Flag'
    else:
        rpa_flag = 'ICON_L27_RPA_Flag'
        dm_flag = 'ICON_L27_DM_Flag'
        drift_variables = ['ICON_L27_' + x for x in drift_variables]
        cross_drift_variables = ['ICON_L27_' + x for x in cross_drift_variables]
        rpa_variables = ['ICON_L27_' + x for x in rpa_variables]

    if inst.clean_level in ['clean', 'dusty']:
        # remove drift values impacted by RPA
        idx, = np.where(inst[rpa_flag] >= 1)
        for var in drift_variables:
            inst[idx, var] = np.nan
        # DM values
        idx, = np.where(inst[dm_flag] >= 1)
        for var in cross_drift_variables:
            inst[idx, var] = np.nan

    if inst.clean_level == 'clean':
        # other RPA parameters
        idx, = np.where(inst[rpa_flag] >= 2)
        for var in rpa_variables:
            inst[idx, var] = np.nan

    return
