import numpy as np
import os

import pandas as pds

import pysat


def list_files(tag=None, sat_id=None, data_path=None, format_str=None,
               file_date_range=None, test_dates=None):
    """Produce a fake list of files spanning three years

    Parameters
    ----------
    tag : (str)
        pysat instrument tag (default=None)
    sat_id : (str)
        pysat satellite ID tag (default=None)
    data_path : (str)
        pysat data path (default=None)
    format_str : (str)
        file format string (default=None)
    file_date_range : (pds.date_range)
        File date range. The default mode generates a list of 3 years of daily
        files (1 year back, 2 years forward) based on the test_dates passed
        through below.  Otherwise, accepts a range of files specified by the
        user.
        (default=None)
    test_dates : (dt.datetime)
        Pass the _test_date object through from the test instrument files

    Returns
    -------
    Series of filenames indexed by file time

    """

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

    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None, user=None,
             password=None):
    """Simple pass function for pysat compatibility for test instruments.

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

    pass


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
        slt) that will reset to data_range[0] once it reached data_range[1].
        If False, continue to monotonically increase
    """

    if cyclic:
        uts_root = np.mod(t0, period)
        data = (np.mod(uts_root + num_array, period)
                * (np.diff(data_range)[0] / float(period))) + data_range[0]
    else:
        data = ((t0 + num_array) / period).astype(int)

    return data


def generate_times(fnames, sat_id, freq='1S'):
    """Construct list of times for simulated instruments

    Parameters
    ----------
    fnames : (list)
        List of filenames.  Currently, only the first is used.  Does not
        support multi-file days as of yet.
    sat_id : (str or NoneType)
        Instrument satellite ID (accepts '' or a number (i.e., '10'), which
        specifies the number of data points to include in the test instrument)
    freq : string
        Frequency of temporal output, compatible with pandas.date_range
        [default : '1S']

    Outputs
    -------
    uts : (array)
        Array of integers representing uts for a given day
    index : (DatetimeIndex)
        The DatetimeIndex to be used in the pysat test instrument objects
    date : (datetime)
        The requested date reconstructed from the fake file name
    """

    # TODO: Expand for multi-file days
    # grab date from filename
    parts = os.path.split(fnames[0])[-1].split('-')
    yr = int(parts[0])
    month = int(parts[1])
    day = int(parts[2][0:2])
    date = pysat.datetime(yr, month, day)

    # Create one day of data at desired frequency
    index = pds.date_range(start=date, end=date+pds.DateOffset(seconds=86399),
                           freq=freq)
    # Allow numeric string to select first set of data
    try:
        index = index[0:int(sat_id)]
    except ValueError:
        # non-integer sat_id produces ValueError
        pass

    uts = index.hour*3600 + index.minute*60 + index.second

    return uts, index, date


def define_period():
    """Define the default periods for the fake data functions

    Parameters
    ----------
    None

    Returns
    -------
    period : dict
        Dictionary of periods to use in test instruments

    """

    period = {'lt': 5820, # 97 minutes
              'lon': 6240, # 104 minutes
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
             'angle': [0.0, 2.0*np.pi]}

    return range
