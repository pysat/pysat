# -*- coding: utf-8 -*-
"""Supports the Michelson Interferometer for Global High-resolution
Thermospheric Imaging (MIGHTI) instrument onboard the Ionospheric
CONnection Explorer (ICON) satellite.  Accesses local data in
netCDF format.

Parameters
----------
platform : string
    'icon'
name : string
    'mighti'
tag : string
    Supports 'los_wind_green', 'los_wind_red', 'vector_wind_green',
    'vector_wind_red', 'temperature'.  Note that not every data product
    available for every sat_id
sat_id : string
    '', 'a', or 'b'

Warnings
--------
- The cleaning parameters for the instrument are still under development.
- Only supports level-2 data.

Example
-------
    import pysat
    mighti = pysat.Instrument('icon', 'mighti', 'vector_wind_green',
                              clean_level='clean')
    mighti.download(dt.datetime(2020, 1, 30), dt.datetime(2020, 12, 31))
    mighti.load(2017,363)

Authors
---------
Originated from EUV support.
Jeff Klenzing, Mar 17, 2018, Goddard Space Flight Center
Russell Stoneback, Mar 23, 2018, University of Texas at Dallas
Conversion to MIGHTI, Oct 8th, 2028, University of Texas at Dallas

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
name = 'mighti'
tags = {'los_wind_green': 'Line of sight wind data -- Green Line',
        'los_wind_red': 'Line of sight wind data -- Red Line',
        'vector_wind_green': 'Vector wind data -- Green Line',
        'vector_wind_red': 'Vector wind data -- Red Line',
        'temperature': 'Neutral temperature data'}
sat_ids = {'': ['vector_wind_green', 'vector_wind_red'],
           'a': ['los_wind_green', 'los_wind_red', 'temperature'],
           'b': ['los_wind_green', 'los_wind_red', 'temperature']}
_test_dates = {jj: {kk: dt.datetime(2020, 1, 1) for kk in sat_ids[jj]}
               for jj in sat_ids.keys()}
_test_download = {jj: {kk: False for kk in sat_ids[jj]}
                  for jj in sat_ids.keys()}
pandas_format = False

datestr = '{year:04d}-{month:02d}-{day:02d}'
fname1 = 'ICON_L2-1_MIGHTI-{id:s}_LOS-Wind-{color:s}_{date:s}_v03r001.NC'
fname2 = 'ICON_L2-2_MIGHTI_Vector-Wind-{color:s}_{date:s}_v03r001.NC'
fname3 = 'ICON_L2-3_MIGHTI-{id:s}_Temperature_{date:s}_v03r001.NC'
supported_tags = {'': {'vector_wind_green': fname2.format(color='Green',
                                                          date=datestr),
                       'vector_wind_red': fname2.format(color='Red',
                                                        date=datestr)},
                  'a': {'los_wind_green': fname1.format(id='A', color='Green',
                                                        date=datestr),
                        'los_wind_red': fname1.format(id='A', color='Red',
                                                      date=datestr),
                        'temperature': fname3.format(id='A', date=datestr)},
                  'b': {'los_wind_green': fname1.format(id='B', color='Green',
                                                        date=datestr),
                        'los_wind_red': fname1.format(id='B', color='Red',
                                                      date=datestr),
                        'temperature': fname3.format(id='B', date=datestr)}}

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

    Note
    ----
        Removes ICON preamble on variable names.

    """

    target = {'los_wind_green': 'ICON_L21_',
              'los_wind_red': 'ICON_L21_',
              'vector_wind_green': 'ICON_L22_',
              'vector_wind_red': 'ICON_L22_',
              'temperature': 'ICON_L23_'}
    mm_gen.remove_leading_text(inst, target=target[inst.tag])


def load(fnames, tag=None, sat_id=None):
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


def download(date_array, tag, sat_id, data_path=None, user=None,
             password=None):
    """Will download data for ICON MIGHTI, after successful launch and
    operations.

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
        logger.info("Cleaning actions for ICON MIGHTI aren't yet defined.")

    return
