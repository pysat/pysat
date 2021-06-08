import datetime as dt
import numpy as np
import os
import pandas as pds
import warnings

import pysat

logger = pysat.logger

ackn_str = ' '.join(("Test instruments provided through the pysat project.",
                     "https://www.github.com/pysat/pysat"))

# Load up citation information
with pysat.utils.NetworkLock(os.path.join(pysat.here, 'citation.txt'), 'r') as \
        locked_file:
    refs = locked_file.read()


def init(self, test_init_kwarg=None):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Shifts time index of files by 5-minutes if mangle_file_dates
    set to True at pysat.Instrument instantiation.

    Creates a file list for a given range if the file_date_range
    keyword is set at instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object
    test_init_kwarg : any or NoneType
        Testing keyword (default=None)

    """

    logger.info(ackn_str)
    self.acknowledgements = ackn_str
    self.references = refs

    # Assign parameters for testing purposes
    self.new_thing = True
    self.test_init_kwarg = test_init_kwarg

    return


def clean(self, test_clean_kwarg=None):
    """Cleaning function

    Parameters
    ----------
    self : pysat.Instrument
        This object
    test_clean_kwarg : any or NoneType
        Testing keyword (default=None)

    """

    self.test_clean_kwarg = test_clean_kwarg

    return


# Optional method
def preprocess(self, test_preprocess_kwarg=None):
    """Customization method that performs standard preprocessing.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue). Object
    modified in place.

    Parameters
    ----------
    test_preprocess_kwarg : any or NoneType
        Testing keyword (default=None)

    """

    self.test_preprocess_kwarg = test_preprocess_kwarg

    return


def list_files(tag=None, inst_id=None, data_path=None, format_str=None,
               file_date_range=None, test_dates=None, mangle_file_dates=False,
               test_list_files_kwarg=None):
    """Produce a fake list of files spanning three years

    Parameters
    ----------
    tag : str or NoneType
        pysat instrument tag (default=None)
    inst_id : str or NoneType
        pysat satellite ID tag (default=None)
    data_path : str or NoneType
        pysat data path (default=None)
    format_str : str or NoneType
        file format string (default=None)
    file_date_range : pds.date_range
        File date range. The default mode generates a list of 3 years of daily
        files (1 year back, 2 years forward) based on the test_dates passed
        through below.  Otherwise, accepts a range of files specified by the
        user.
        (default=None)
    test_dates : dt.datetime or NoneType
        Pass the _test_date object through from the test instrument files
    mangle_file_dates : bool
        If True, file dates are shifted by 5 minutes. (default=False)
    test_list_files_kwarg : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    Series of filenames indexed by file time

    """

    # Support keyword testing
    logger.info(''.join(('test_list_files_kwarg = ',
                         str(test_list_files_kwarg))))

    if data_path is None:
        data_path = ''

    # Determine the appropriate date range for the fake files
    if file_date_range is None:
        start = test_dates[''][''] - pds.DateOffset(years=1)
        stop = (test_dates[''][''] + pds.DateOffset(years=2)
                - pds.DateOffset(days=1))
        file_date_range = pds.date_range(start, stop)

    index = file_date_range

    # Mess with file dates if kwarg option set
    if mangle_file_dates:
        index = index + dt.timedelta(minutes=5)

    # Create the list of fake filenames
    names = [data_path + date.strftime('%Y-%m-%d') + '.nofile'
             for date in index]

    return pds.Series(names, index=index)


def list_remote_files(tag=None, inst_id=None, data_path=None, format_str=None,
                      start=None, stop=None, test_dates=None, user=None,
                      password=None, mangle_file_dates=False,
                      test_list_remote_kwarg=None):
    """Produce a fake list of files spanning three years and one month to
    simulate new data files on a remote server

    Parameters
    ----------
    tag : str or NoneType
        pysat instrument tag (default=None)
    inst_id : str or NoneType
        pysat satellite ID tag (default=None)
    data_path : str or NoneType
        pysat data path (default=None)
    format_str : str or NoneType
        file format string (default=None)
    start : dt.datetime or NoneType
        Starting time for file list. A None value will start 1 year before
        test_date
        (default=None)
    stop : dt.datetime or NoneType
        Ending time for the file list.  A None value will stop 2 years 1 month
        after test_date
        (default=None)
    test_dates : dt.datetime or NoneType
        Pass the _test_date object through from the test instrument files
    user : string or NoneType
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied. (default=None)
    password : string or NoneType
        Password for data download. (default=None)
    mangle_file_dates : bool
        If True, file dates are shifted by 5 minutes. (default=False)
    test_list_remote_kwarg : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    pds.Series
        Filenames indexed by file time, see list_files for more info

    """

    # Support keyword testing
    logger.info(''.join(('test_list_remote_kwarg = ',
                         str(test_list_remote_kwarg))))

    # Determine the appropriate date range for the fake files
    if start is None:
        start = test_dates[''][''] - pds.DateOffset(years=1)

    if stop is None:
        stop = (test_dates[''][''] + pds.DateOffset(years=2)
                - pds.DateOffset(days=1) + pds.DateOffset(months=1))

    file_date_range = pds.date_range(start, stop)

    return list_files(tag=tag, inst_id=inst_id, data_path=data_path,
                      format_str=format_str, file_date_range=file_date_range,
                      mangle_file_dates=mangle_file_dates,
                      test_dates=test_dates)


def download(date_array, tag, inst_id, data_path=None, user=None,
             password=None, test_download_kwarg=None):
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
        Instrument ID string identifier used for particular dataset. This input
        is provided by pysat. (default='')
    data_path : string or NoneType
        Path to directory to download data to. (default=None)
    user : string or NoneType
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for downloads this routine here must
        error if user not supplied. (default=None)
    password : string or NoneType
        Password for data download. (default=None)
    test_download_kwarg : any or NoneType
        Testing keyword (default=None)

    Raises
    ------
    ValueError
        When user/password are required but not supplied

    Warnings
    --------
    When no download support will be provided

    """

    # Support keyword testing
    logger.info(''.join(('test_download_kwarg = ', str(test_download_kwarg))))

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

    Returns
    -------
    data : array-like
        Array with fake data

    """

    if cyclic:
        uts_root = np.mod(t0, period)
        data = (np.mod(uts_root + num_array, period)
                * (np.diff(data_range)[0] / np.float64(period))) + data_range[0]
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

    Returns
    -------
    uts : array
        Array of integers representing uts for a given day
    index : pds.DatetimeIndex
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
        # Grab date from filename
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

    # Combine index times together
    index = pds.DatetimeIndex(indices)

    # Make UTS an array
    uts = np.array(uts)

    return uts, index, dates


def define_period():
    """Define the default periods for the fake data functions

    Returns
    -------
    def_period : dict
        Dictionary of periods to use in test instruments

    Note
    ----
    Local time and longitude slightly out of sync to simulate motion of Earth

    """

    def_period = {'lt': 5820,  # 97 minutes
                  'lon': 6240,  # 104 minutes
                  'angle': 5820}

    return def_period


def define_range():
    """Define the default ranges for the fake data functions

    Returns
    -------
    def_range : dict
        Dictionary of periods to use in test instruments

    """

    def_range = {'lt': [0.0, 24.0],
                 'lon': [0.0, 360.0],
                 'angle': [0.0, 2.0 * np.pi]}

    return def_range


def eval_dep_warnings(warns, check_msgs):
    """Evaluate deprecation warnings by category and message

    Parameters
    ----------
    warns : list
        List of warnings.WarningMessage objects
    check_msgs : list
        List of strings containing the expected warning messages

    Returns
    -------
    found_msgs : list
        List of booleans corresponding to `check_msgs`, which are True when
        the messages are found and False when they are not

    """

    # Initialize the output
    found_msgs = [False for msg in check_msgs]

    # Test the warning messages, ensuring each attribute is present
    for iwar in warns:
        if iwar.category == DeprecationWarning:
            for i, msg in enumerate(check_msgs):
                if str(iwar.message).find(msg) >= 0:
                    found_msgs[i] = True

    return found_msgs
