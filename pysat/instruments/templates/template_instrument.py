# -*- coding: utf-8 -*-
"""
This is a template for a pysat.Instrument support file.
Modify this file as needed when adding a new Instrument to pysat.

This is a good area to introduce the instrument, provide background
on the mission, operations, instrumenation, and measurements.

Also a good place to provide contact information. This text will
be included in the pysat API documentation.

Parameters
----------
platform : string
    *List platform string here*
name : string
    *List name string here*
sat_id : string
    *List supported sat_ids here*
tag : string
    *List supported tag strings here*

Note
----
::

    Notes

Warnings
--------


Authors
-------

"""

# python 2/3 comptability
from __future__ import print_function
from __future__ import absolute_import

# pandas support
import pandas as pds
# xarray support
import xarray as xr
import pysat

import logging
logger = logging.getLogger(__name__)

# the platform and name strings associated with this instrument
# need to be defined at the top level
# these attributes will be copied over to the Instrument object by pysat
# the strings used here should also be used to name this file
# platform_name.py
platform = ''
name = ''

# dictionary of data 'tags' and corresponding description
tags = {'': 'description 1',  # this is the default
        'tag_string': 'description 2'}

# Let pysat know if there are multiple satellite platforms supported
# by these routines
# define a dictionary keyed by satellite ID, each with a list of
# corresponding tags
# sat_ids = {'a':['L1', 'L0'], 'b':['L1', 'L2'], 'c':['L1', 'L3']}
sat_ids = {'': ['']}

# Define good days to download data for when pysat undergoes testing.
# format is outer dictionary has sat_id as the key
# each sat_id has a dictionary of test dates keyed by tag string
# test_dates = {'a':{'L0':pysat.datetime(2019,1,1),
#                    'L1':pysat.datetime(2019,1,1)},
#               'b':{'L1':pysat.datetime(2019,1,1),
#                    'L2':pysat.datetime(2019,1,1),}}
test_dates = {'': {'': pysat.datetime(2019, 1, 1)}}

# Set to False to specify using xarray (not using pandas)
# Set to True if data will be returned via a pandas DataFrame
pandas_format = False


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    Returns
    --------
    Void : (NoneType)
        Object modified in place.


    """

    logger.info("Mission acknowledgements and data restrictions will be printed " +
          "here when available.")
    return


def default(self):
    """Default customization function.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue).

    Parameters
    ----------
    self : pysat.Instrument
        This object

    Returns
    --------
    Void : (NoneType)
        Object modified in place.


    """

    return


def load(fnames, tag=None, sat_id=None, **kwargs):
    """Loads PLATFORM data into (PANDAS/XARRAY).

    This routine is called as needed by pysat. It is not intended
    for direct user interaction.

    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : string ('')
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. While
        tag defaults to None here, pysat provides '' as the default
        tag unless specified by user at Instrument instantiation.
    sat_id : string ('')
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
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

    # netCDF4 files, particularly those produced
    # by pysat can be loaded using a pysat provided
    # function
    # Metadata in our notional example file is
    # labeled by strings determined by a standard
    # we can adapt pysat to the standard by specifying
    # the string labels used in the file
    # function below returns both data and metadata
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

    # This code below demonstrates the use of xarray
    # functions to load TIEGCM data
    # Metadata is transferred from xarray to the Instrument object
    # Data is transferred as well
    # data not indexed by time are transferred to the Instrument object as an
    # attribute

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
    """Produce a list of files corresponding to PLATFORM/NAME.

    This routine is invoked by pysat and is not intended for direct
    use by the end user. Arguments are provided by pysat.

    Parameters
    ----------
    tag : string ('')
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    sat_id : string ('')
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    data_path : string (None)
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

    Multiple data levels may be supported via the 'tag' input string.
    Multiple instruments via the sat_id string.


    """

    format_str = 'example_name_{year:04d}_{month:02d}_{day:02d}.nc'
    # we use a pysat provided function to grab list of files from the
    # local file system that match the format defined above
    return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def list_remote_files(tag, sat_id, user=None, password=None):
    """Return a Pandas Series of every file for chosen remote data.

    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    user : (string or NoneType)
        Username to be passed along to resource with relevant data.
        (default=None)
    password : (string or NoneType)
        User password to be passed along to resource with relevant data.
        (default=None)

    Returns
    --------
    pandas.Series
        A Series formatted for the Files class (pysat._files.Files)
        containing filenames and indexed by date and time

    """

    pass


def download(date_array, tag, sat_id, data_path=None, user=None, password=None,
             **kwargs):
    """Placeholder for PLATFORM/NAME downloads.

    This routine is invoked by pysat and is not intended for direct use by the
    end user.

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
        pysat. If an account
        is required for dowloads this routine here must error if user not
        supplied.
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

    return


# code should be defined below as needed
def clean(inst):
    """Routine to return PLATFORM/NAME data cleaned to the specified level

    Cleaning level is specified in inst.clean_level and pysat
    will accept user input for several strings. The clean_level is
    specified at instantiation of the Instrument object.

    'clean' All parameters should be good, suitable for statistical and
            case studies
    'dusty' All paramers should generally be good though same may
            not be great
    'dirty' There are data areas that have issues, data should be used
            with caution
    'none'  No cleaning applied, routine not called in this case.


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
    -----

    """

    return
