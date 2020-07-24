# -*- coding: utf-8 -*-.
"""Supports generalized access to Madrigal Data.

To use this routine, you need to know both the Madrigal Instrument code
as well as the data tag numbers that Madrigal uses to uniquely identify
data sets. Using these codes, the methods.madrigal.py routines will
be used to support downloading and loading of data.

Downloads data from the Madrigal Database.

Warnings
--------
    All data downloaded under this general support is placed in the same
    directory, pysat_data_dir/madrigal/pandas/. For technical reasons,
    the file search algorithm for pysat's Madrigal support is set to permissive
    defaults. Thus, all instrument files downloaded via this interface will be
    picked up by the madrigal pandas pysat Instrument object unless the
    file_format keyword is used at instantiation.

    Files can be safely downloaded without knowing the file_format keyword,
    or equivalently, how Madrigal names the files. See `Examples` for more.

Parameters
----------
platform : string
    'madrigal'
name : string
    'pandas'
tag : string
    ''

Examples
--------
::
    # for isolated use of a madrigal data set
    import pysat
    # download DMSP data from Madrigal
    dmsp = pysat.Instrument('madrigal', 'pandas',
                            madrigal_code=8100,
                            madrigal_tag=10241)
    dmsp.download(pysat.datetime(2017, 12, 30), pysat.datetime(2017, 12, 31),
                  user='Firstname+Lastname', password='email@address.com')
    dmsp.load(2017,363)

    # for users that plan on using multiple Madrigal datasets
    # using this general interface then an additional parameter
    # should be supplied upon instrument instantiation (file_format)

    # pysat needs information on how to parse filenames from Madrigal
    # for the particular instrument under study.
    # When starting from scratch (no files), this is a two step process.
    # First, get atleast one file from Madrigal, using the steps above
    # using the file downloaded. Using the filename, convert it to a template
    # string
    # and pass that to pysat when instantiating future Instruments.

    # For example, one of the files downloaded above is
    # dms_ut_19980101_11.002.hdf5
    # pysat needs a template for how to pull out the year, month, day, and,
    # if available, hour, minute, second, etc.
    # the format/template string for this instrument is
    # 'dms_ut_{year:4d}{month:02d}{day:02d}_12.002.hdf5', following
    # python standards for string templates/Formatters
    # https://docs.python.org/2/library/string.html

    # the complete instantiation for this instrument is
    dmsp = pysat.Instrument('madrigal', 'pandas',
                            madrigal_code=8100,
                            madrigal_tag=10241,
                            file_format='dms_ut_{year:4d}{month:02d}{day:02d}_11.002.hdf5')

Note
----
    Please provide name and email when downloading data with this routine.

"""

from __future__ import print_function
from __future__ import absolute_import

import functools
import pysat
from pysat.instruments.methods import madrigal as mad_meth
from pysat.instruments.methods import nasa_cdaweb as cdw

import logging
logger = logging.getLogger(__name__)

platform = 'madrigal'
name = 'pandas'
tags = {'': 'General Madrigal data access loaded into pysat via pandas.'}
sat_ids = {'': list(tags.keys())}
# need to sort out test day setting for unit testing
_test_dates = {'': {'': pysat.datetime(2010, 1, 19)}}

# support list files routine
# use the default CDAWeb method
#########
# need a way to get the filename strings for a particular instrument
# I've put in wildcards for now....
#########
jro_fname1 = '*{year:4d}{month:02d}{day:02d}'
jro_fname2 = '.{version:03d}.hdf5'
supported_tags = {ss: {'': jro_fname1 + "*" + jro_fname2}
                  for ss in sat_ids.keys()}
list_files = functools.partial(cdw.list_files,
                               supported_tags=supported_tags)

# let pysat know that data is spread across more than one file
# multi_file_day=True

# Set to False to specify using xarray (not using pandas)
# Set to True if data will be returned via a pandas DataFrame
pandas_format = True

# support load routine
load = mad_meth.load

# support download routine
# real download attached during init
# however, pysat requires a method before we get there
download = mad_meth.download


def init(self):
    """Initializes the Instrument object in support of Madrigal access

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    logger.info(mad_meth.cedar_rules())

    code = self.kwargs['madrigal_code']
    tag = self.kwargs['madrigal_tag']
    self._download_rtn = functools.partial(_general_download,
                                           inst_code=str(code),
                                           kindat=str(tag))
    return


def _general_download(date_array, tag='', sat_id='', data_path=None, user=None,
                      password=None, inst_code=None, kindat=None):
    """Downloads data from Madrigal.

    Method will be partially set using functools.partial. Intended to
    have the same call structure as normal instrument download routine.
    Upon Instrument instantiation this routine will be set to
    parameters specific to a Madrigal data set. It will then work like
    a standard download call.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : string
        Tag identifier used for particular dataset. This input is provided by
        pysat. (default='')
    sat_id : string
        Satellite ID string identifier used for particular dataset. This input
        is provided by pysat. (default='')
    data_path : string
        Path to directory to download data to. (default=None)
    user : string
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied. (default=None)
    password : string
        Password for data download. (default=None)
    inst_code : int
        Madrigal integer code used to identify platform (default=None)
    kindat : int
        Madrigal integer code used to identify data set (default=None)

    Note
    ----
    The user's names should be provided in field user. Ruby Payne-Scott should
    be entered as Ruby+Payne-Scott

    The password field should be the user's email address. These parameters
    are passed to Madrigal when downloading.

    The affiliation field is set to pysat to enable tracking of pysat
    downloads.

    """
    mad_meth.download(date_array, inst_code=inst_code, kindat=kindat,
                      data_path=data_path, user=user, password=password)


def clean(self):
    """Placeholder routine that would normally return cleaned data

    Notes
    --------
    Supports 'clean', 'dusty', 'dirty' in the sense that it prints
    a message noting there is no cleaning.
    'None' is also supported as it signifies no cleaning.

    Routine is called by pysat, and not by the end user directly.

    """

    if self.clean_level in ['clean', 'dusty', 'dirty']:
        logger.warning('Generalized Madrigal data support has no cleaning.')

    return
