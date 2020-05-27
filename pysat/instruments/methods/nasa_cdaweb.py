# -*- coding: utf-8 -*-
"""Provides default routines for integrating NASA CDAWeb instruments into
pysat. Adding new CDAWeb datasets should only require mininal user
intervention.

"""

from __future__ import absolute_import, division, print_function
import datetime as dt
import numpy as np
import sys

import pandas as pds

import pysat

import logging
logger = logging.getLogger(__name__)


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
        return pds.DataFrame(None), None
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
            date = dt.datetime.strptime(fnames[0][-10:], '%Y-%m-%d')
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
    tag : (str or NoneType)
        tag or None (default=None)
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
                      start=None, stop=None):
    """Return a Pandas Series of every file for chosen remote data.

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
    start : (dt.datetime or NoneType)
        Starting time for file list. A None value will start with the first
        file found.
        (default=None)
    stop : (dt.datetime or NoneType)
        Ending time for the file list.  A None value will stop with the last
        file found.
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

    # Check for acustom start stop dates.  Set to defaults if NoneType
    # if start is None:
    #     start = dt.datetime(1958, 1, 1)
    # if stop is None:
    #     stop = dt.datetime.now()
    # if start == stop:
    #     stop += dt.timedelta(days=1)

    # Break string format into path and filename
    dir_split = os.path.split(format_str)

    # Parse the path to find the number of levels to search
    format_dir = dir_split[0]
    search_dir = pysat._files.construct_searchstring_from_format(format_dir)
    n_layers = len(search_dir['keys'])
    print(search_dir['keys'])

    # only keep file portion of format
    format_str = dir_split[-1]
    # Generate list of targets to identify files
    search_dict = pysat._files.construct_searchstring_from_format(format_str)
    targets = [x for x in search_dict['string_blocks'] if len(x) > 0]

    remote_dirs = []
    for level in range(n_layers + 1):
        remote_dirs.append([])
    remote_dirs[0] = ['']

    # Build a list of files using each filename target as a goal
    full_files = []

    if start is None and stop is None:
        url_list = [remote_url]
    elif start is not None:
        stop = dt.datetime.now() if stop is None else stop

        if 'year' in search_dir['keys']:
            search_years = np.arange(start.year, stop.year + 0.1).astype(int)

    try:
        for top_url in url_list:
            for level in range(n_layers+1):
                for directory in remote_dirs[level]:
                    temp_url = '/'.join((top_url.strip('/'), directory))
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
    except Exception as merr:
        raise type(merr)(' '.join((str(merr), 'Request exceeds the server',
                                   'limit. Please try again using a smaller',
                                   'data range.')))

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
    if start is not None:
        mask = (stored_list.index >= start)
        if stop is not None:
            mask = mask & (stored_list.index <= stop)
        stored_list = stored_list[mask]

    return stored_list
