# -*- coding: utf-8 -*-.
"""Provides default routines for integrating CEDAR Madrigal instruments into
pysat, reducing the amount of user intervention.

 """

from __future__ import absolute_import
from __future__ import print_function

import datetime as dt
import logging
import numpy as np
import os
import pandas as pds
import subprocess
import sys

import h5py
from madrigalWeb import madrigalWeb

import pysat

logger = logging.getLogger(__name__)

def cedar_rules():
    """ General acknowledgement statement for Madrigal data.

    Returns
    -------
    ackn : string
        String with general acknowledgement for all CEDAR Madrigal data

    """
    ackn = "Contact the PI when using this data, in accordance with the CEDAR"
    ackn += " 'Rules of the Road'"
    return ackn


# support load routine
def load(fnames, tag=None, sat_id=None, xarray_coords=[]):
    """Loads data from Madrigal into Pandas.

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
    xarray_coords : list
        List of keywords to use as coordinates if xarray output is desired
        instead of a Pandas DataFrame (default=[])

    Returns
    -------
    data : pds.DataFrame or xr.DataSet
        A pandas DataFrame or xarray DataSet holding the data from the HDF5
        file
    metadata : pysat.Meta
        Metadata from the HDF5 file, as well as default values from pysat

    Examples
    --------
    ::
        inst = pysat.Instrument('jro', 'isr', 'drifts')
        inst.load(2010,18)

    """

    # Ensure 'time' wasn't included as a coordinate, since it is the default
    if 'time' in xarray_coords:
        xarray_coords.pop(xarray_coords.index('time'))

    # Open the specified file
    filed = h5py.File(fnames[0], 'r')
    # data
    file_data = filed['Data']['Table Layout']
    # metadata
    file_meta = filed['Metadata']['Data Parameters']
    # load up what is offered into pysat.Meta
    meta = pysat.Meta()
    meta.info = {'acknowledgements': "See 'meta.Experiment_Notes' for " +
                 "instrument specific acknowledgements\n" + cedar_rules(),
                 'references': "See 'meta.Experiment_Notes' for references"}
    labels = []
    for item in file_meta:
        # handle difference in string output between python 2 and 3
        name_string = item[0]
        unit_string = item[3]
        desc_string = item[1]
        if sys.version_info[0] >= 3:
            name_string = name_string.decode('UTF-8')
            unit_string = unit_string.decode('UTF-8')
            desc_string = desc_string.decode('UTF-8')
        labels.append(name_string)
        meta[name_string.lower()] = {'long_name': name_string,
                                     'units': unit_string,
                                     'desc': desc_string}

    # add additional metadata notes
    # custom attributes attached to meta are attached to
    # corresponding Instrument object when pysat receives
    # data and meta from this routine
    for key in filed['Metadata']:
        if key != 'Data Parameters':
            setattr(meta, key.replace(' ', '_'), filed['Metadata'][key][:])
    # data into frame, with labels from metadata
    data = pds.DataFrame.from_records(file_data, columns=labels)
    # lowercase variable names
    data.columns = [item.lower() for item in data.columns]
    # datetime index from times
    time_keys = np.array(['year', 'month', 'day', 'hour', 'min', 'sec'])
    if not np.all([key in data.columns for key in time_keys]):
        time_keys = [key for key in time_keys if key not in data.columns]
        raise ValueError("unable to construct time index, missing " +
                         "{:}".format(time_keys))

    uts = 3600.0 * data.loc[:, 'hour'] + 60.0 * data.loc[:, 'min'] \
        + data.loc[:, 'sec']
    time = pysat.utils.time.create_datetime_index(year=data.loc[:, 'year'],
                                                  month=data.loc[:, 'month'],
                                                  day=data.loc[:, 'day'],
                                                  uts=uts)
    # Declare index or recast as xarray
    if len(xarray_coords) > 0:
        if not np.all([xkey.lower() in data.columns
                       for xkey in xarray_coords]):
            estr = 'unknown coordinate key in {:}, '.format(xarray_coords)
            estr += 'use only {:}'.format(data.columns)
            raise ValueError(estr)

        # Append time to the data frame and add as the first coordinate
        data = data.assign(time=pds.Series(time, index=data.index))
        xarray_coords.insert(0, 'time')

        # Set the indices
        data = data.set_index(xarray_coords)

        # Recast the data as an xarray
        data = data.to_xarray()
    else:
        # Set the index to time, and put up a warning if there are duplicate
        # times.  This could mean the data should be stored as an xarray
        # DataSet
        data.index = time

        if np.any(time.duplicated()):
            logger.warning("duplicated time indices, consider specifing " +
                  "additional coordinates and storing the data as an xarray" +
                  " DataSet")

    return data, meta


def download(date_array, inst_code=None, kindat=None, data_path=None,
             user=None, password=None, url="http://cedar.openmadrigal.org",
             file_format='hdf5'):
    """Downloads data from Madrigal.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    inst_code : string (None)
        Madrigal instrument code(s), cast as a string.  If multiple are used,
        separate them with commas.
    kindat : string  (None)
        Experiment instrument code(s), cast as a string.  If multiple are used,
        separate them with commas.
    data_path : string (None)
        Path to directory to download data to.
    user : string (None)
        User string input used for download. Provided by user and passed via
        pysat. If an account
        is required for dowloads this routine here must error if user not
        supplied.
    password : string (None)
        Password for data download.
    url : string ('http://cedar.openmadrigal.org')
        URL for Madrigal site
    file_format : string ('hdf5')
        File format for Madrigal data.  Load routines currently only accept
        'hdf5', but any of the Madrigal options may be used here.

    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.

    Notes
    -----
    The user's names should be provided in field user. Ruby Payne-Scott should
    be entered as Ruby+Payne-Scott

    The password field should be the user's email address. These parameters
    are passed to Madrigal when downloading.

    The affiliation field is set to pysat to enable tracking of pysat
    downloads.

    """

    if inst_code is None:
        raise ValueError("Must supply Madrigal instrument code")

    if kindat is None:
        raise ValueError("Must supply Madrigal experiment code")

    # currently passes things along if no user and password supplied
    # need to do this for testing
    # TODO, implement user and password values in test code
    # specific to each instrument
    if user is None:
        logger.info('No user information supplied for download.')
        user = 'pysat_testing'
    if password is None:
        logger.info('Please provide email address in password field.')
        password = 'pysat_testing@not_real_email.org'

    # Initialize the connection to Madrigal
    web_data = madrigalWeb.MadrigalData(url)

    # Get the list of desired remote files
    start = date_array.min()
    stop = date_array.max()
    if start == stop:
        stop += dt.timedelta(days=1)
    files = get_remote_filenames(inst_code=inst_code, kindat=kindat, user=user,
                                 password=password, web_data=web_data, url=url,
                                 start=start, stop=stop)

    for mad_file in files:
        local_file = os.path.join(data_path, os.path.basename(mad_file.name))

        if not os.path.isfile(local_file):
            web_data.downloadFile(mad_file.name, local_file, user, password,
                                  "pysat", format=file_format)


def get_remote_filenames(inst_code=None, kindat=None, user=None,
                         password=None, web_data=None,
                         url="http://cedar.openmadrigal.org",
                         start=dt.datetime(1900,1,1), stop=dt.datetime.now(),
                         date_array=None):
    """Retrieve the remote filenames for a specified Madrigal instrument
    (and experiment)

    Parameters
    ----------
    inst_code : string (None)
        Madrigal instrument code(s), cast as a string.  If multiple are used,
        separate them with commas.
    kindat : string (None)
        Madrigal experiment code(s), cast as a string.  If multiple are used,
        separate them with commas.  If not supplied, all will be returned.
    data_path : string (None)
        Path to directory to download data to.
    user : string (None)
        User string input used for download. Provided by user and passed via
        pysat. If an account
        is required for dowloads this routine here must error if user not
        supplied.
    password : string (None)
        Password for data download.
    web_data : MadrigalData (None)
        Open connection to Madrigal database or None (will initiate using url)
    url : string ('http://cedar.openmadrigal.org')
        URL for Madrigal site
    start : dt.datetime
        Starting time for file list (defaults to 01-01-1900)
    stop : dt.datetime
        Ending time for the file list (defaults to time of run)
    date_array : dt.datetime (None)
        Array of datetimes to download data for. The sequence of dates need not
        be contiguous and will be used instead of start and stop if supplied.

    Returns
    -------
    Void : (NoneType)
        Downloads data to disk.

    Notes
    -----
    The user's names should be provided in field user. Ruby Payne-Scott should
    be entered as Ruby+Payne-Scott

    The password field should be the user's email address. These parameters
    are passed to Madrigal when downloading.

    The affiliation field is set to pysat to enable tracking of pysat
    downloads.


    """

    if inst_code is None:
        raise ValueError("Must supply Madrigal instrument code")

    if kindat is None:
        kindat = []
    else:
        kindat = [int(kk) for kk in kindat.split(",")]

    # currently passes things along if no user and password supplied
    # need to do this for testing
    # TODO, implement user and password values in test code
    # specific to each instrument
    if user is None:
        print('No user information supplied for download.')
        user = 'pysat_testing'
    if password is None:
        print('Please provide email address in password field.')
        password = 'pysat_testing@not_real_email.org'

    # If date_array supplied, overwrite start and stop
    if date_array is not None:
        if len(date_array) == 0:
            raise ValueError('unknown date_array supplied: {:}'.format(
                date_array))
        start = date_array.min()
        stop = date_array.max()
        if start == stop:
            stop += dt.timedelta(days=1)

    # open connection to Madrigal
    if web_data is None:
        web_data = madrigalWeb.MadrigalData(url)

    # get list of experiments for instrument from 1900 till now
    exp_list = web_data.getExperiments(inst_code, start.year, start.month,
                                       start.day, start.hour, start.minute,
                                       start.second, stop.year, stop.month,
                                       stop.day, stop.hour, stop.minute,
                                       stop.second)

    # iterate over experiments to grab files for each one
    files = list()
    print("Found {:d} Madrigral experiments".format(len(exp_list)))
    for exp in exp_list:
        if good_exp(exp, date_array=date_array):
            file_list = web_data.getExperimentFiles(exp.id)

            if len(kindat) == 0:
                files.extend(file_list)
            else:
                for file_obj in file_list:
                    if file_obj.kindat in kindat:
                        files.append(file_obj)

    return files

def good_exp(exp, date_array=None):
    """ Determine if a Madrigal experiment has good data for specified dates

    Parameters
    ----------
    exp : MadrigalExperimentFile
        MadrigalExperimentFile object
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.

    Returns
    -------
    gflag : boolean
        True if good, False if bad

    """

    gflag = False

    if exp.id != -1:
        if date_array is None:
            gflag = True
        else:
            exp_start = dt.datetime(exp.startyear, exp.startmonth, exp.startday,
                                    exp.starthour, exp.startmin, exp.startsec)
            exp_end = dt.datetime(exp.endyear, exp.endmonth, exp.endday,
                                  exp.endhour, exp.endmin, exp.endsec)

            for date_val in date_array:
                if date_val >= exp_start and date_val < exp_end:
                    gflag = True
                    break

    return gflag

def list_remote_files(tag, sat_id, inst_code=None, kindat=None, user=None,
                      password=None, supported_tags=None,
                      url="http://cedar.openmadrigal.org",
                      two_digit_year_break=None, start=dt.datetime(1900,1,1),
                      stop=dt.datetime.now()):
    """List files available from Madrigal.

    Parameters
    ----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    inst_code : string (None)
        Madrigal instrument code(s), cast as a string.  If multiple are used,
        separate them with commas.
    kindat : string (None)
        Madrigal experiment code(s), cast as a string.  If multiple are used,
        separate them with commas.  If not supplied, all will be returned.
    data_path : string (None)
        Path to directory to download data to.
    user : string (None)
        User string input used for download. Provided by user and passed via
        pysat. If an account
        is required for dowloads this routine here must error if user not
        supplied.
    password : string (None)
        Password for data download.
    supported_tags : (dict or NoneType)
        keys are sat_id, each containing a dict keyed by tag
        where the values file format template strings. (default=None)
    url : string ('http://cedar.openmadrigal.org')
        URL for Madrigal site
    two_digit_year_break : int
        If filenames only store two digits for the year, then
        '1900' will be added for years >= two_digit_year_break
        and '2000' will be added for years < two_digit_year_break.
    start : (dt.datetime)
        Starting time for file list (defaults to 01-01-1900)
    stop : (dt.datetime)
        Ending time for the file list (defaults to time of run)

    Returns
    -------
    Void : (NoneType)
        Downloads data to disk.

    Notes
    -----
    The user's names should be provided in field user. Ruby Payne-Scott should
    be entered as Ruby+Payne-Scott

    The password field should be the user's email address. These parameters
    are passed to Madrigal when downloading.

    The affiliation field is set to pysat to enable tracking of pysat
    downloads.

    Examples
    --------
    This method is intended to be set in an instrument support file at the
    top level using functools.partial
    ::
        list_remote_files = functools.partial(mad_meth.list_remote_files,
                                              supported_tags=supported_tags,
                                              inst_code=madrigal_inst_code)

    """
    if inst_code is None:
        raise ValueError("Must supply Madrigal instrument code")

    # currently passes things along if no user and password supplied
    # need to do this for testing
    # TODO, implement user and password values in test code
    # specific to each instrument
    if user is None:
        logger.info('No user information supplied for download.')
        user = 'pysat_testing'
    if password is None:
        logger.info('Please provide email address in password field.')
        password = 'pysat_testing@not_real_email.org'

    # Test input
    try:
        format_str = supported_tags[sat_id][tag]
    except KeyError:
        raise ValueError('Problem parsing supported_tags')

    # Retrieve remote file list
    files = get_remote_filenames(inst_code=inst_code, kindat=kindat, user=user,
                                 password=password, url=url, start=start,
                                 stop=stop)

    # parse these filenames to grab out the ones we want
    logger.info("Parsing filenames")
    stored = pysat._files.parse_fixed_width_filenames(files, format_str)

    # process the parsed filenames and return a properly formatted Series
    logger.info("Processing filenames")
    return pysat._files.process_parsed_filenames(stored, two_digit_year_break)


def filter_data_single_date(self):
    """Filters data to a single date.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    Note
    ----
    Madrigal serves multiple days within a single JRO file
    to counter this, we will filter each loaded day so that it only
    contains the relevant day of data. This is only applied if loading
    by date. It is not applied when supplying pysat with a specific
    filename to load, nor when data padding is enabled. Note that when
    data padding is enabled the final data available within the instrument
    will be downselected by pysat to only include the date specified.

    This routine is intended to be added to the Instrument
    nanokernel processing queue via
    ::

        inst = pysat.Instrument()
        inst.custom.add(filter_data_single_date, 'modify')

    This function will then be automatically applied to the
    Instrument object data on every load by the pysat nanokernel.

    Warnings
    --------
    For the best performance, this function should be added first in the queue.
    This may be ensured by setting the default function in a
    pysat instrument file to this one.

    within platform_name.py set
    ::

        default = pysat.instruments.methods.madrigal.filter_data_single_date

    at the top level

    """

    # only do this if loading by date!
    if self._load_by_date and self.pad is None:
        # identify times for the loaded date
        idx, = np.where((self.index >= self.date) &
                        (self.index < (self.date+pds.DateOffset(days=1))))
        # downselect from all data
        self.data = self[idx]
