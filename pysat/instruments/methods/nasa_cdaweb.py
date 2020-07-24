# -*- coding: utf-8 -*-
"""Provides default routines for integrating NASA CDAWeb instruments into
pysat. Adding new CDAWeb datasets should only require mininal user
intervention.

"""

from __future__ import absolute_import, division, print_function
import logging
import sys
import warnings

import pandas as pds

import pysat
from pysat.instruments.methods import general as mm_gen

logger = logging.getLogger(__name__)


def list_files(tag=None, sat_id=None, data_path=None, format_str=None,
               supported_tags=None, fake_daily_files_from_monthly=False,
               two_digit_year_break=None):
    """Return a Pandas Series of every file for chosen satellite data.

    .. deprecated:: 2.2.0
      `list_files` will be removed in pysat 3.0.0, it will be replaced by the
      copy in instruments.methods.general

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
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : (string or NoneType)
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)
    supported_tags : (dict or NoneType)
        keys are sat_id, each containing a dict keyed by tag
        where the values file format template strings. (default=None)
    fake_daily_files_from_monthly : (bool)
        Some CDAWeb instrument data files are stored by month, interfering
        with pysat's functionality of loading by day. This flag, when true,
        appends daily dates to monthly files internally. These dates are
        used by load routine in this module to provide data by day.
    two_digit_year_break : (int)
        If filenames only store two digits for the year, then
        '1900' will be added for years >= two_digit_year_break
        and '2000' will be added for years < two_digit_year_break.

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    Examples
    --------
    ::

        fname = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
        supported_tags = {'dc_b': fname}
        list_files = functools.partial(nasa_cdaweb.list_files,
                                       supported_tags=supported_tags)

        fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
        supported_tags = {'': fname}
        list_files = functools.partial(cdw.list_files,
                                       supported_tags=supported_tags)

    """

    warnings.warn(' '.join(["methods.nasa_cdaweb.list_files has been",
                            "deprecated and will be removed in pysat 3.0.0.",
                            "Please use methods.general.list_files instead"]),
                  DeprecationWarning, stacklevel=2)

    out = mm_gen.list_files(tag=tag, sat_id=sat_id, data_path=data_path,
                            format_str=format_str,
                            supported_tags=supported_tags,
                            fake_daily_files_from_monthly=fake_daily_files_from_monthly,
                            two_digit_year_break=two_digit_year_break)
    return out


def load(fnames, tag=None, sat_id=None,
         fake_daily_files_from_monthly=False,
         flatten_twod=True):
    """Load NASA CDAWeb CDF files.

    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

    Parameters
    ------------
    fnames : (pandas.Series)
        Series of filenames
    tag : (str or NoneType)
        tag or None (default=None)
    sat_id : (str or NoneType)
        satellite id or None (default=None)
    fake_daily_files_from_monthly : bool
        Some CDAWeb instrument data files are stored by month, interfering
        with pysat's functionality of loading by day. This flag, when true,
        parses of daily dates to monthly files that were added internally
        by the list_files routine, when flagged. These dates are
        used here to provide data by day.
    flatted_twod : bool
        Flattens 2D data into different columns of root DataFrame rather
        than produce a Series of DataFrames

    Returns
    ---------
    data : (pandas.DataFrame)
        Object containing satellite data
    meta : (pysat.Meta)
        Object containing metadata such as column names and units

    Examples
    --------
    ::

        # within the new instrument module, at the top level define
        # a new variable named load, and set it equal to this load method
        # code below taken from cnofs_ivm.py.

        # support load routine
        # use the default CDAWeb method
        load = cdw.load


    """

    import pysatCDF

    if len(fnames) <= 0:
        return pysat.DataFrame(None), None
    else:
        # going to use pysatCDF to load the CDF and format
        # data and metadata for pysat using some assumptions.
        # Depending upon your needs the resulting pandas DataFrame may
        # need modification
        # currently only loads one file, which handles more situations via
        # pysat than you may initially think

        if fake_daily_files_from_monthly:
            # parse out date from filename
            fname = fnames[0][0:-11]
            date = pysat.datetime.strptime(fnames[0][-10:], '%Y-%m-%d')
            with pysatCDF.CDF(fname) as cdf:
                # convert data to pysat format
                data, meta = cdf.to_pysat(flatten_twod=flatten_twod)
                # select data from monthly
                data = data.loc[date:date+pds.DateOffset(days=1)
                                - pds.DateOffset(microseconds=1), :]
                return data, meta
        else:
            # basic data return
            with pysatCDF.CDF(fnames[0]) as cdf:
                return cdf.to_pysat(flatten_twod=flatten_twod)


def download(supported_tags, date_array, tag, sat_id,
             remote_site='https://cdaweb.gsfc.nasa.gov',
             data_path=None, user=None, password=None,
             fake_daily_files_from_monthly=False,
             multi_file_day=False):
    """Routine to download NASA CDAWeb CDF data.

    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

    Parameters
    -----------
    supported_tags : dict
        dict of dicts. Keys are supported tag names for download. Value is
        a dict with 'dir', 'remote_fname', 'local_fname'. Inteded to be
        pre-set with functools.partial then assigned to new instrument code.
    date_array : array_like
        Array of datetimes to download data for. Provided by pysat.
    tag : str or NoneType (None)
        tag or None
    sat_id : (str or NoneType)
        satellite id or None (default=None)
    remote_site : (string or NoneType)
        Remote site to download data from
        (default='https://cdaweb.gsfc.nasa.gov')
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    user : (string or NoneType)
        Username to be passed along to resource with relevant data.
        (default=None)
    password : (string or NoneType)
        User password to be passed along to resource with relevant data.
        (default=None)
    fake_daily_files_from_monthly : bool
        Some CDAWeb instrument data files are stored by month. This flag,
        when true, accomodates this reality with user feedback on a monthly
        time frame.

    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.

    Examples
    --------
    ::

        # download support added to cnofs_vefi.py using code below
        rn = '{year:4d}/cnofs_vefi_bfield_1sec_{year:4d}{month:02d}{day:02d}'+
            '_v05.cdf'
        ln = 'cnofs_vefi_bfield_1sec_{year:4d}{month:02d}{day:02d}_v05.cdf'
        dc_b_tag = {'dir':'/pub/data/cnofs/vefi/bfield_1sec',
                    'remote_fname': rn,
                    'local_fname': ln}
        supported_tags = {'dc_b': dc_b_tag}

        download = functools.partial(nasa_cdaweb.download,
                                     supported_tags=supported_tags)

    """

    import os
    import requests

    try:
        inst_dict = supported_tags[sat_id][tag]
    except KeyError:
        raise ValueError('Tag name unknown.')

    # path to relevant file on CDAWeb
    remote_url = remote_site + inst_dict['dir']

    # naming scheme for files on the CDAWeb server
    remote_fname = inst_dict['remote_fname']

    # naming scheme for local files, should be closely related
    # to CDAWeb scheme, though directory structures may be reduced
    # if desired
    local_fname = inst_dict['local_fname']

    if not multi_file_day:
        # Get list of files from server
        remote_files = list_remote_files(tag=tag, sat_id=sat_id,
                                         remote_site=remote_site,
                                         supported_tags=supported_tags)
        # Find only requested files that exist remotely
        date_array = pds.DatetimeIndex(list(set(remote_files.index)
                                            & set(date_array))).sort_values()

    for date in date_array:
        # format files for specific dates and download location
        formatted_remote_fname = remote_fname.format(year=date.year,
                                                     month=date.month,
                                                     day=date.day,
                                                     hour=date.hour,
                                                     min=date.minute,
                                                     sec=date.second)
        formatted_local_fname = local_fname.format(year=date.year,
                                                   month=date.month,
                                                   day=date.day,
                                                   hour=date.hour,
                                                   min=date.minute,
                                                   sec=date.second)
        saved_local_fname = os.path.join(data_path, formatted_local_fname)

        # perform download
        if not multi_file_day:
            # standard download
            try:
                logger.info(' '.join(('Attempting to download file for',
                                      date.strftime('%d %B %Y'))))
                sys.stdout.flush()
                remote_path = '/'.join((remote_url.strip('/'),
                                        formatted_remote_fname))
                req = requests.get(remote_path)
                if req.status_code != 404:
                    open(saved_local_fname, 'wb').write(req.content)
                    logger.info('Finished.')
                else:
                    logger.info(' '.join(('File not available for',
                                          date.strftime('%d %B %Y'))))
            except requests.exceptions.RequestException as exception:
                logger.info(' '.join((exception, '- File not available for',
                                      date.strftime('%d %B %Y'))))
        else:
            try:
                logger.info(' '.join(('Attempting to download files for',
                                      date.strftime('%d %B %Y'))))
                sys.stdout.flush()
                remote_files = list_remote_files(tag=tag, sat_id=sat_id,
                                                 remote_site=remote_site,
                                                 supported_tags=supported_tags,
                                                 year=date.year,
                                                 month=date.month,
                                                 day=date.day)

                # Get the files
                i = 0
                n = len(remote_files.values)
                for remote_file in remote_files.values:
                    remote_dir = os.path.split(formatted_remote_fname)[0]
                    remote_file_path = '/'.join((remote_url.strip('/'),
                                                 remote_dir.strip('/'),
                                                 remote_file))
                    saved_local_fname = os.path.join(data_path, remote_file)
                    req = requests.get(remote_file_path)
                    if req.status_code != 404:
                        open(saved_local_fname, 'wb').write(req.content)
                        i += 1
                    else:
                        logger.info(' '.join(('File not available for',
                                              date.strftime('%d %B %Y'))))
                logger.info('Downloaded {i:} of {n:} files.'.format(i=i, n=n))
            except requests.exceptions.RequestException as exception:
                logger.info(' '.join((exception, '- Files not available for',
                                      date.strftime('%d %B %Y'))))


def list_remote_files(tag, sat_id,
                      remote_site='https://cdaweb.gsfc.nasa.gov',
                      supported_tags=None,
                      user=None, password=None,
                      fake_daily_files_from_monthly=False,
                      two_digit_year_break=None, delimiter=None,
                      year=None, month=None, day=None):
    """Return a Pandas Series of every file for chosen remote data.

    .. deprecated:: 2.2.0
      `year/month/day` keywords will be removed in pysat 3.0.0, they will be
      replaced with a start/stop syntax consistent with the download routine

    This routine is intended to be used by pysat instrument modules supporting
    a particular NASA CDAWeb dataset.

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.
        (default=None)
    remote_site : (string or NoneType)
        Remote site to download data from
        (default='https://cdaweb.gsfc.nasa.gov')
    supported_tags : dict
        dict of dicts. Keys are supported tag names for download. Value is
        a dict with 'dir', 'remote_fname', 'local_fname'. Inteded to be
        pre-set with functools.partial then assigned to new instrument code.
    user : (string or NoneType)
        Username to be passed along to resource with relevant data.
        (default=None)
    password : (string or NoneType)
        User password to be passed along to resource with relevant data.
        (default=None)
    fake_daily_files_from_monthly : bool
        Some CDAWeb instrument data files are stored by month. This flag,
        when true, accomodates this reality with user feedback on a monthly
        time frame.
        (default=False)
    two_digit_year_break : (int or NoneType)
        If filenames only store two digits for the year, then
        '1900' will be added for years >= two_digit_year_break
        and '2000' will be added for years < two_digit_year_break.
        (default=None)
    delimiter : (string or NoneType)
        If filename is delimited, then provide delimiter alone e.g. '_'
        (default=None)
    year : (int or NoneType)
        Selects a given year to return remote files for.  None returns all
        years.
        (default=None)
    month : (int or NoneType)
        Selects a given month to return remote files for.  None returns all
        months.  Requires year to be defined.
        (default=None)
    day : (int or NoneType)
        Selects a given day to return remote files for.  None returns all
        days.  Requires year and month to be defined.
        (default=None)

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    Examples
    --------
    ::

        fname = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
        supported_tags = {'dc_b': fname}
        list_remote_files = \
            functools.partial(nasa_cdaweb.list_remote_files,
                              supported_tags=supported_tags)

        fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
        supported_tags = {'': fname}
        list_remote_files = \
            functools.partial(cdw.list_remote_files,
                              supported_tags=supported_tags)

    """

    import os
    import requests
    import warnings
    from bs4 import BeautifulSoup

    if tag is None:
        tag = ''
    if sat_id is None:
        sat_id = ''
    try:
        inst_dict = supported_tags[sat_id][tag]
    except KeyError:
        raise ValueError('Tag name unknown.')

    # path to relevant file on CDAWeb
    remote_url = remote_site + inst_dict['dir']

    # naming scheme for files on the CDAWeb server
    format_str = inst_dict['remote_fname']

    # Check for appropriate combination of kwargs.  Warn and continue if not.
    if (year is None) and (month is not None):
        warnings.warn("Month keyword requires year.  Ignoring month.")
        month = None
    if ((year is None) or (month is None)) and (day is not None):
        warnings.warn("Day keyword requires year and month.  Ignoring day.")
        day = None

    # Deprecations warnings for changing syntax
    if any([year, month, day]):
        warnings.warn(' '.join(["The year/month/day keywords have been deprecated",
                                "and will be removed in pysat 3.0.0.  Instead,",
                                "use datetime values consistent with the",
                                "start/stop syntax in the download methods."]),
                      DeprecationWarning, stacklevel=2)

    # get a listing of all files
    # determine if we need to walk directories

    # Find Subdirectories and modify remote_url if user input is specified
    dir_split = os.path.split(format_str)
    if len(dir_split[0]) != 0:
        # Get all subdirectories
        subdirs = dir_split[0].split('/')
        # only keep file portion of format
        format_str = dir_split[-1]
        n_layers = len(subdirs)
        # Check for formatted subdirectories if user input is specified
        for subdir in subdirs:
            if (year is not None) and (subdir.find('year') != -1):
                remote_url = '/'.join((remote_url.strip('/'),
                                       subdir.format(year=year)))
                n_layers -= 1
            if (month is not None) and (subdir.find('month') != -1):
                remote_url = '/'.join((remote_url.strip('/'),
                                       subdir.format(month=month)))
                n_layers -= 1
            if (day is not None) and (subdir.find('day') != -1):
                remote_url = '/'.join((remote_url.strip('/'),
                                       subdir.format(day=day)))
                n_layers -= 1

    # Start with file extention as prime target
    targets = ['.' + format_str.split('.')[-1]]

    # Extract file preamble as target - those characters left of variables
    # or wildcards
    fmt_idx = [format_str.find('{')]
    fmt_idx.append(format_str.find('?'))
    fmt_idx.append(format_str.find('*'))

    # Not all characters may exist in a filename.  Remove those that don't.
    fmt_idx = [elem for elem in fmt_idx if elem != -1]

    # If preamble exists, add to targets
    if fmt_idx:
        targets.append(format_str[0:min(fmt_idx)])

    remote_dirs = []
    for level in range(n_layers + 1):
        remote_dirs.append([])
    remote_dirs[0] = ['']

    # Build a list of files using each filename target as a goal
    if n_layers > 1:
        n_loops = 2
        warnings.warn(' '.join(('Current implementation only goes down one',
                                'level of subdirectories.  Try specifying',
                                'a year for more accurate results.')))
    else:
        n_loops = n_layers + 1
    full_files = []

    try:
        for level in range(n_loops):
            for directory in remote_dirs[level]:
                temp_url = '/'.join((remote_url.strip('/'), directory))
                soup = BeautifulSoup(requests.get(temp_url).content, "lxml")
                links = soup.find_all('a', href=True)
                for link in links:
                    # If there is room to go down, look for directories
                    if link['href'].count('/') == 1:
                        remote_dirs[level+1].append(link['href'])
                    else:
                        # If at the endpoint, add matching files to list
                        add_file = True
                        for target in targets:
                            if link['href'].count(target) == 0:
                                add_file = False
                        if add_file:
                            full_files.append(link['href'])
    except requests.exceptions.ConnectionError as merr:
        raise type(merr)(' '.join((str(merr), 'pysat -> Request potentially',
                                   'exceeded the server limit. Please try again',
                                   'using a smaller data range.')))

    # parse remote filenames to get date information
    if delimiter is None:
        stored = pysat._files.parse_fixed_width_filenames(full_files,
                                                          format_str)
    else:
        stored = pysat._files.parse_delimited_filenames(full_files,
                                                        format_str, delimiter)

    # process the parsed filenames and return a properly formatted Series
    stored_list = pysat._files.process_parsed_filenames(stored,
                                                        two_digit_year_break)
    # Downselect to user-specified dates, if needed
    if year is not None:
        mask = (stored_list.index.year == year)
        if month is not None:
            mask = mask & (stored_list.index.month == month)
            if day is not None:
                mask = mask & (stored_list.index.day == day)
        stored_list = stored_list[mask]

    return stored_list
