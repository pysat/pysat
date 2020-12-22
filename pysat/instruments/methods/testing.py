import datetime as dt
import numpy as np
import os
import warnings

import pandas as pds


ackn_str = ' '.join(("Test instruments provided through the pysat project.",
                     "https://www.github.com/pysat/pysat"))
refs = ' '.join(("Russell Stoneback, Jeff Klenzing, Angeline Burrell, Carey",
                 "Spence, Asher Pembroke, Matthew Depew, … Asher Pembroke.",
                 "(2019, November 18). pysat/pysat v2.1 (Version v2.1).",
                 "Zenodo. http://doi.org/10.5281/zenodo.3546270"))


def list_files(tag=None, inst_id=None, data_path=None, format_str=None,
               file_date_range=None, test_dates=None):
    """Produce a fake list of files spanning three years

    Parameters
    ----------
    tag : str
        pysat instrument tag (default=None)
    inst_id : str
        pysat satellite ID tag (default=None)
    data_path : str
        pysat data path (default=None)
    format_str : str
        file format string (default=None)
    file_date_range : pds.date_range
        File date range. The default mode generates a list of 3 years of daily
        files (1 year back, 2 years forward) based on the test_dates passed
        through below.  Otherwise, accepts a range of files specified by the
        user.
        (default=None)
    test_dates : dt.datetime
        Pass the _test_date object through from the test instrument files

    Returns
    -------
    Series of filenames indexed by file time

    """

    if data_path is None:
        data_path = ''
    # Determine the appropriate date range for the fake files
    if file_date_range is None:
        start = test_dates[''][''] - pds.DateOffset(years=1)
        stop = (test_dates[''][''] + pds.DateOffset(years=2)
                - pds.DateOffset(days=1))
        file_date_range = pds.date_range(start, stop)

    index = file_date_range

    # Create the list of fake filenames
    names = [data_path + date.strftime('%Y-%m-%d') + '.nofile'
             for date in index]

    return pds.Series(names, index=index)


def list_remote_files(tag=None, inst_id=None, data_path=None, format_str=None,
                      start=None, stop=None, test_dates=None):
    """Produce a fake list of files spanning three years and one month to
    simulate new data files on a remote server

    Parameters
    ----------
    tag : str
        pysat instrument tag (default=None)
    inst_id : str
        pysat satellite ID tag (default=None)
    data_path : str
        pysat data path (default=None)
    format_str : str
        file format string (default=None)
    start : dt.datetime or NoneType
        Starting time for file list. A None value will start 1 year before
        test_date
        (default=None)
    stop : dt.datetime or NoneType
        Ending time for the file list.  A None value will stop 2 years 1 month
        after test_date
        (default=None)
    test_dates : dt.datetime
        Pass the _test_date object through from the test instrument files

    Returns
    -------
    Series of filenames indexed by file time

    """

    # Determine the appropriate date range for the fake files
    if start is None:
        start = test_dates[''][''] - pds.DateOffset(years=1)
    if stop is None:
        stop = (test_dates[''][''] + pds.DateOffset(years=2)
                - pds.DateOffset(days=1) + pds.DateOffset(months=1))
    file_date_range = pds.date_range(start, stop)

    return list_files(tag=tag, inst_id=inst_id, data_path=data_path,
                      format_str=format_str, file_date_range=file_date_range,
                      test_dates=test_dates)


def download(date_array, tag, inst_id, data_path=None, user=None,
             password=None):
    """Simple pass function for pysat compatibility for test instruments.

    This routine is invoked by pysat and is not intended for direct use by the
    end user.

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

    if tag == 'no_download':
        warnings.warn('This simulates an instrument without download support')
    # Check that user name and password are passed through the unit tests
    if tag == 'user_password':
        if (not user) and (not password):
            # Note that this line will be uncovered if test succeeds
            raise ValueError(' '.join(('Tests are not passing user and',
                                       'password to test instruments')))

    return


def generate_fake_data(t0, num_array, period=5820, data_range=[0.0, 24.0],
                       cyclic=True):
    """Generates fake data over a given range

    Parameters
    ----------
    t0 : float
        Start time in seconds
    num_array : array_like
        Array of time steps from t0.  This is the index of the fake data
    period : int
        The number of seconds per period.
        (default = 5820)
    data_range : float
        For cyclic functions, the range of data values cycled over one period.
        Not used for non-cyclic functions.
        (default = 24.0)
    cyclic : bool
        If True, assume that fake data is a cyclic function (ie, longitude,
        slt) that will reset to data_range[0] once it reaches data_range[1].
        If False, continue to monotonically increase
    """

    if cyclic:
        uts_root = np.mod(t0, period)
        data = (np.mod(uts_root + num_array, period)
                * (np.diff(data_range)[0] / float(period))) + data_range[0]
    else:
        data = ((t0 + num_array) / period).astype(int)

    return data


def generate_times(fnames, num, freq='1S'):
    """Construct list of times for simulated instruments

    Parameters
    ----------
    fnames : list
        List of filenames.
    num : int
        Number of times to generate
    freq : string
        Frequency of temporal output, compatible with pandas.date_range
        [default : '1S']

    Outputs
    -------
    uts : array
        Array of integers representing uts for a given day
    index : DatetimeIndex
        The DatetimeIndex to be used in the pysat test instrument objects
    date : datetime
        The requested date reconstructed from the fake file name
    """

    if isinstance(num, str):
        estr = ''.join(('generate_times support for input strings interpreted ',
                        'as the number of times has been deprecated. Please ',
                        'switch to using integers.'))
        warnings.warn(estr, DeprecationWarning)

    uts = []
    indices = []
    dates = []
    for loop, fname in enumerate(fnames):
        # grab date from filename
        parts = os.path.split(fname)[-1].split('-')
        yr = int(parts[0])
        month = int(parts[1])
        day = int(parts[2][0:2])
        date = dt.datetime(yr, month, day)
        dates.append(date)

        # Create one day of data at desired frequency
        end_date = date + dt.timedelta(seconds=86399)
        index = pds.date_range(start=date, end=end_date, freq=freq)
        index = index[0:num]
        indices.extend(index)
        uts.extend(index.hour * 3600 + index.minute * 60 + index.second
                   + 86400. * loop)
    # combine index times together
    index = pds.DatetimeIndex(indices)
    # make UTS an array
    uts = np.array(uts)

    return uts, index, dates


def define_period():
    """Define the default periods for the fake data functions

    Parameters
    ----------
    None

    Returns
    -------
    period : dict
        Dictionary of periods to use in test instruments

    Note
    ----
    Local time and longitude slightly out of sync to simulate motion of Earth

    """

    period = {'lt': 5820,  # 97 minutes
              'lon': 6240,  # 104 minutes
              'angle': 5820}

    return period


def define_range():
    """Define the default ranges for the fake data functions

    Parameters
    ----------
    None

    Returns
    -------
    range : dict
        Dictionary of periods to use in test instruments

    """

    range = {'lt': [0.0, 24.0],
             'lon': [0.0, 360.0],
             'angle': [0.0, 2.0 * np.pi]}

    return range
