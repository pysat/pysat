# -*- coding: utf-8 -*-
"""
Supports loading data from files generated using TIEGCM
(Thermosphere Ionosphere Electrodynamics General Circulation Model) model.
TIEGCM file is a netCDF file with multiple dimensions for some variables.

Properties
----------
platform
    'ucar'
name
    'tiegcm'
tag
    None supported
sat_id
    None supported

"""

# python 2/3 comptability
from __future__ import print_function
from __future__ import absolute_import
import logging
import warnings

import xarray as xr
import pysat

logger = logging.getLogger(__name__)

# the platform and name strings associated with this instrument
# need to be defined at the top level
# these attributes will be copied over to the Instrument object by pysat
# the strings used here should also be used to name this file
# platform_name.py
platform = 'ucar'
name = 'tiegcm'

# dictionary of data 'tags' and corresponding description
tags = {'': 'UCAR TIE-GCM file'}
# dictionary of satellite IDs, list of corresponding tags for each sat_ids
# example
# sat_ids = {'a':['L1', 'L0'], 'b':['L1', 'L2'], 'c':['L1', 'L3']}
sat_ids = {'': ['']}
# good day to download test data for. Downloads aren't currently supported!
# format is outer dictionary has sat_id as the key
# each sat_id has a dictionary of test dates keyed by tag string
_test_dates = {'': {'': pysat.datetime(2019, 1, 1)}}

# specify using xarray (not using pandas)
pandas_format = False


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    logger.info("Mission acknowledgements and data restrictions will be printed " +
          "here when available.")
    return


def load(fnames, tag=None, sat_id=None, **kwargs):
    """Loads TIEGCM data using xarray.

    This routine is called as needed by pysat. It is not intended
    for direct user interaction.

    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : string
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    sat_id : string
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    **kwargs : extra keywords
        Passthrough for additional keyword arguments specified when
        instantiating an Instrument object. These additional keywords
        are passed through to this routine by pysat.

    Returns
    -------
    data, metadata
        Data and Metadata are formatted for pysat. Data is an xarray
        DataSet while metadata is a pysat.Meta instance.

    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine.

    Examples
    --------
    ::

        inst = pysat.Instrument('ucar', 'tiegcm')
        inst.load(2019,1)

    """

    # load data
    data = xr.open_dataset(fnames[0])
    # move attributes to the Meta object
    # these attributes will be trasnferred to the Instrument object
    # automatically by pysat
    meta = pysat.Meta()
    for attr in data.attrs:
        setattr(meta, attr[0], attr[1])
    data.attrs = []

    # fill Meta object with variable information
    for key in data.variables.keys():
        attrs = data.variables[key].attrs
        meta[key] = attrs

    # move misc parameters from xarray to the Instrument object via Meta
    # doing this after the meta ensures all metadata is still kept
    # even for moved variables
    meta.p0 = data['p0']
    meta.p0_model = data['p0_model']
    meta.grav = data['grav']
    meta.mag = data['mag']
    meta.timestep = data['timestep']
    # remove these variables from xarray
    data = data.drop(['p0', 'p0_model', 'grav', 'mag', 'timestep'])

    return data, meta


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a list of files corresponding to UCAR TIEGCM.

    This routine is invoked by pysat and is not intended for direct
    use by the end user. Arguments are provided by pysat.

    Multiple data levels may be supported via the 'tag' input string.

    Parameters
    ----------
    tag : string
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    sat_id : string
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    data_path : string
        Full path to directory containing files to be loaded. This
        is provided by pysat. The user may specify their own data path
        at Instrument instantiation and it will appear here. (default=None)
    format_str : string
        String template used to parse the datasets filenames. If a user
        supplies a template string at Instrument instantiation
        then it will appear here, otherwise defaults to None. (default=None)

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

    if format_str is None:
        # default file naming
        format_str = 'tiegcm_icon_merg2.0_totTgcm.s_{day:03d}_{year:4d}.nc'

    return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None,
             **kwargs):
    """Placeholder for UCAR TIEGCM downloads. Doesn't do anything.

    This routine is invoked by pysat and is not intended for direct use by
    the end user.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : string
        Tag identifier used for particular dataset. This input is provided by
        pysat.
    sat_id : string
        Satellite ID string identifier used for particular dataset. This input
        is provided by pysat.
    data_path : string
        Path to directory to download data to. (default=None)
    user : string
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied. (default=None)
    password : string
        Password for data download. (default=None)
    **kwargs : dict
        Additional keywords supplied by user when invoking the download
        routine attached to a pysat.Instrument object are passed to this
        routine via kwargs.

    """

    warnings.warn('Not implemented in this version.')
    return
