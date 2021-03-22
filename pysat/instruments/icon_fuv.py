# -*- coding: utf-8 -*-
"""Supports the Far Ultraviolet (FUV) imager onboard the Ionospheric
CONnection Explorer (ICON) satellite.  Accesses local data in
netCDF format.

.. deprecated:: 2.3.0
  This Instrument module has been removed from pysat in the 3.0.0 release and
  can now be found in pysatNASA (https://github.com/pysat/pysatNASA).  Note that
  the ICON files are retrieved from different servers here and in pysatNASA,
  resulting in a difference in local file names. Please see the migration guide
  there for more details.

Properties
----------
platform
    'icon'
name
    'fuv'
tag
    None supported


Warnings
--------
- The cleaning parameters for the instrument are still under development.
- Only supports level-2 data.


Example
-------
::

    import pysat
    fuv = pysat.Instrument(platform='icon', name='fuv', tag='day')
    fuv.download(dt.datetime(2020, 1, 1), dt.datetime(2020, 1, 31))
    fuv.load(2020, 1)

By default, pysat removes the ICON level tags from variable names, ie,
ICON_L27_Ion_Density becomes Ion_Density.  To retain the original names, use
::

    fuv = pysat.Instrument(platform='icon', name='fuv', tag=day',
                           keep_original_names=True)


Authors
---------
Originated from EUV support.
Jeff Klenzing, Mar 17, 2018, Goddard Space Flight Center
Russell Stoneback, Mar 23, 2018, University of Texas at Dallas
Conversion to FUV, Oct 8th, 2028, University of Texas at Dallas

"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import functools
import logging
import warnings

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw
from pysat.instruments.methods import general as mm_gen
from pysat.instruments.methods import icon as mm_icon


logger = logging.getLogger(__name__)

platform = 'icon'
name = 'fuv'
tags = {'day': 'Level 2 daytime O/N2',
        'night': 'Level 2 nighttime O profile'}
sat_ids = {'': ['day', 'night']}
_test_dates = {'': {kk: dt.datetime(2020, 1, 1) for kk in tags.keys()}}
pandas_format = False

# Set the list_files routine
fname24 = ''.join(('icon_l2-4_fuv_day_{year:04d}{month:02d}{day:02d}_',
                   'v04r000.nc'))
fname25 = ''.join(('icon_l2-5_fuv_night_{year:04d}{month:02d}{day:02d}_',
                   'v04r000.nc'))
supported_tags = {'': {'day': fname24, 'night': fname25}}

list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# Set the download routine
basic_tag24 = {'dir': '/pub/data/icon/l2/l2-4_fuv_day',
               'remote_fname': '{year:04d}/' + fname24,
               'local_fname': fname24}
basic_tag25 = {'dir': '/pub/data/icon/l2/l2-5_fuv_night',
               'remote_fname': '{year:04d}/' + fname25,
               'local_fname': fname25}
download_tags = {'': {'day': basic_tag24, 'night': basic_tag25}}

download = functools.partial(cdw.download, download_tags)

# Set the list_remote_files routine
list_remote_files = functools.partial(cdw.list_remote_files,
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
                                    mm_icon.refs['fuv']))

    warnings.warn(" ".join(["_".join([self.platform, self.name]),
                            "has been removed from the pysat-managed",
                            "Instruments in pysat 3.0.0, and now resides in",
                            "pysatNASA:",
                            "https://github.com/pysat/pysatNASA",
                            "Note that the ICON files are retrieved from",
                            "different servers here and in pysatNASA, resulting",
                            "in a difference in local file names. Please see",
                            "the migration guide there for more details."]),
                  DeprecationWarning, stacklevel=2)
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
        remove_preamble(inst)


def remove_preamble(inst):
    """Removes preambles in variable names"""

    target = {'day': 'ICON_L24_',
              'night': 'ICON_L25_'}
    mm_gen.remove_leading_text(inst, target=target[inst.tag])


def load(fnames, tag=None, sat_id=None, keep_original_names=False):
    """Loads ICON FUV data using pysat into pandas.

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
        inst = pysat.Instrument('icon', 'fuv')
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
                                    fill_label='FillVal',
                                    pandas_format=pandas_format)


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

    warnings.warn("Cleaning actions for ICON FUV are not yet defined.")
    return
