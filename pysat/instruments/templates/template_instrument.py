# -*- coding: utf-8 -*-
"""
This is a template for a pysat.Instrument support file.
Modify this file as needed when adding a new Instrument to pysat.

This is a good area to introduce the instrument, provide background
on the mission, operations, instrumentation, and measurements.

Also a good place to provide contact information. This text will
be included in the pysat API documentation.

Properties
----------
platform
    *List platform string here*
name
    *List name string here*
inst_id
    *List supported inst_ids here*
tag
    *List supported tag strings here*

Note
----
- Optional section, remove if no notes

Warnings
--------
- Optional section, remove if no warnings
- Two blank lines needed afterward for proper formatting


Examples
--------
::

    Example code can go here


Authors
-------
Author name and institution

"""

import datetime as dt

import pysat

# Assign the pysat logger to the local log commands, as these functions will
# all be executed within pysat.  If this is the only instance pysat is used,
# consider omitting the pysat import and logger assignment and replacing it
# with:
# from pysat import logger
logger = pysat.logger

# ----------------------------------------------------------------------------
# Instrument attributes:

# The platform and name strings associated with this instrument need to be
# defined at the top level.  These attributes will be copied over to the
# Instrument object by pysat.  The strings used here should also be used to
# name this file platform_name.py
platform = ''
name = ''

# Dictionary of data 'tags' and corresponding description
tags = {'': 'description 1',  # this is the default
        'tag_string': 'description 2'}

# Let pysat know if there are multiple satellite platforms supported
# by these routines.  Define a dictionary keyed by instrument ID, each with a
# list of corresponding tags.  For example:
# inst_ids = {'a': ['tag1', 'tag2'], 'b': ['tag2', 'tag3']}
inst_ids = {'': ['', 'tag_string']}

# Set to False to specify using xarray (not using pandas)
# Set to True if data will be returned via a pandas DataFrame
pandas_format = False

# The following attributes will be set to these default values upon
# instantiation if not otherwise specified
directory_format = None
file_format = None
multi_file_day = False  # Set to True if files span less than a day
orbit_info = None

# ----------------------------------------------------------------------------
# Instrument testing attributes:

# Define good days to download data for when pysat undergoes testing.
# format is outer dictionary has inst_id as the key
# each inst_id has a dictionary of test dates keyed by tag string
# _test_dates = {'a':{'tag1': dt.datetime(2019,1,1),
#                     'tag2': dt.datetime(2019,1,1)},
#                'b':{'tag2': dt.datetime(2019,1,1),
#                     'tag3': dt.datetime(2019,1,1),}}
_test_dates = {'': {'': dt.datetime(2019, 1, 1),
                    'tag_string': dt.datetime(2019, 1, 2)}}

# Set Testing flags
# Dict structure should mirror _test_dates above

# For instruments without download support, set _test_download to False
# If not set, defaults to True
_test_download = {'': {'': False, 'tag_string': True}}

# For instruments using FTP for download, set _test_download_travis to False
# These tests will still download locally but be skipped on Travis CI
# If not set, defaults to True
_test_download_travis = {'': {'': False, 'tag_string': False}}

# For instruments requiring a user passwrod, set _password_req to True
# These instruments will not be downloaded as part of tests to preserve password
# security
# If not set, defaults to False
_password_req = {'': {'': True, 'tag_string': False}}

# ----------------------------------------------------------------------------
# Instrument methods: routines that are attached to the pysat.Instrument
# as class methods


# Required method
def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation. Object modified in place.  Use this to set
    the acknowledgements and references.

    """

    # Required attribute: acknowledgements
    self.acknowledgements = 'This would go in the Acknowledgements section'

    # Required attribute: references
    self.references = 'These are the instrument references'

    # Direct feedback to logging info
    logger.info(self.acknowledgements)
    return


# Required method
def clean(self):
    """Method to return PLATFORM/NAME data cleaned to the specified level

    Cleaning level is specified in inst.clean_level and pysat
    will accept user input for several strings. The clean_level is
    specified at instantiation of the Instrument object, though it may be
    updated to a more stringent level and re-applied after instantiation.
    The clean method is applied after default every time data is loaded.

    Note
    ----
    - 'clean' All parameters are good, suitable for scientific studies
    - 'dusty' Most parameters are good, requires instrument familiarity
    - 'dirty' There are data areas that have issues, use with caution
    - 'none' No cleaning applied, routine not called in this case.

    """

    return


# Optional method
def preprocess(self):
    """Customization method that performs standard preprocessing.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue). Object
    modified in place.

    """

    return

# ----------------------------------------------------------------------------
# Instrument functions: routines that are attached to the pysat.Instrument
# as function attributes


# Required function
def list_files(tag=None, inst_id=None, data_path=None, format_str=None):
    """Produce a list of files corresponding to PLATFORM/NAME.

    This routine is invoked by pysat and is not intended for direct
    use by the end user. Arguments are provided by pysat.

    Parameters
    ----------
    tag : string
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    inst_id : string
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

    Multiple data levels may be supported via the 'tag' input string.
    Multiple instruments via the inst_id string.

    """

    if format_str is None:
        # user did not supply an alternative format template string
        format_str = 'example_name_{year:04d}_{month:02d}_{day:02d}.nc'
    # we use a pysat provided function to grab list of files from the
    # local file system that match the format defined above
    file_list = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    return file_list


# Required function
def download(date_array, tag, inst_id, data_path=None, user=None, password=None,
             **kwargs):
    """Placeholder for PLATFORM/NAME downloads.

    This routine is called as needed by pysat. It is not intended
    for direct user interaction.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : string
        Tag identifier used for particular dataset. This input is provided by
        pysat. (default='')
    inst_id : string
        Satellite ID string identifier used for particular dataset. This input
        is provided by pysat. (default='')
    data_path : string
        Path to directory to download data to. (default=None)
    user : string (OPTIONAL)
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied. (default=None)
    password : string (OPTIONAL)
        Password for data download. (default=None)
    custom_keywords : placeholder
        Additional keywords supplied by user when invoking the download
        routine attached to a pysat.Instrument object are passed to this
        routine. Use of custom keywords here is discouraged.

    """

    return


# Required function
def load(fnames, tag=None, inst_id=None, custom_keyword=None):
    """Loads PLATFORM data into (PANDAS/XARRAY).

    This routine is called as needed by pysat. It is not intended
    for direct user interaction.

    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : string
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. While
        tag defaults to None here, pysat provides '' as the default
        tag unless specified by user at Instrument instantiation. (default='')
    inst_id : string
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    custom_keyword : type to be set
        Developers may include any custom keywords, with default values
        defined in the method signature. This is included here as a
        place holder and should be removed.

    Returns
    -------
    data, metadata
        Data and Metadata are formatted for pysat. Data is a
        pandas DataFrame or xarray DataSet while metadata is a pysat.Meta
        instance.

    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine.

    Examples
    --------
    ::

        inst = pysat.Instrument('ucar', 'tiegcm')
        inst.load(2019, 1)

    """

    # netCDF4 files, particularly those produced by pysat can be loaded using a
    # pysat provided function, load_netcdf4.

    # Metadata across different files can employ different labels for the
    # same category of information. In our notional example, the file is
    # from NASA's CDAWeb and uses their standard for metadata. The dictionary
    # passed into the labels keyword is keyed by the category type that pysat
    # tracks, while the value contains a tuple for the string label used
    # within the file as well as the type of metadata to be tracked.
    # `load_netcdf4` uses this information to correctly parse metadata within
    # the file and attach it as appropriate. Once both the data and
    # metadata are returned by this function, pysat will adapt the metadata
    # labels to match the standard chosen by the user, not the
    # labels chosen by CDAWeb.
    data, mdata = pysat.utils.load_netcdf4(fnames, epoch_name='Epoch',
                                           labels={'units': ('Units', str),
                                                   'name': ('Long_Name', str),
                                                   'notes': ('Var_Notes', str),
                                                   'desc': ('CatDesc', str),
                                                   'plot': ('FieldNam', str),
                                                   'axis': ('LablAxis', str),
                                                   'scale': ('ScaleTyp', str),
                                                   'min_val': (
                                                       'ValidMin', float),
                                                   'max_val': (
                                                       'ValidMax', float),
                                                   'fill_val': (
                                                       'FillVal', float)},
                                           pandas_format=pandas_format)
    return data, mdata


# Recommended function
def list_remote_files(tag, inst_id, user=None, password=None):
    """Return a Pandas Series of every file for chosen remote data.

    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

    Parameters
    -----------
    tag : string or NoneType
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    inst_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    user : string or NoneType
        Username to be passed along to resource with relevant data.
        (default=None)
    password : string or NoneType
        User password to be passed along to resource with relevant data.
        (default=None)

    Note
    ----
    If defined, the expected return variable is a pandas.Series formatted for
    the Files class (pysat._files.Files) containing filenames and indexed by
    date and time

    """

    return
