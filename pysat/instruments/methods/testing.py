#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Standard functions for the test instruments."""

import datetime as dt
import os

import numpy as np
import pandas as pds
import time
import warnings
import xarray as xr

import pysat
from pysat.utils import NetworkLock
from pysat.utils import time as putime

ackn_str = ' '.join(("Test instruments provided through the pysat project.",
                     "https://www.github.com/pysat/pysat"))

# Load up citation information
with pysat.utils.NetworkLock(pysat.citation, 'r') as locked_file:
    refs = locked_file.read()


def init(self, test_init_kwarg=None):
    """Initialize the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Shifts time index of files by 5-minutes if `mangle_file_dates`
    set to True at pysat.Instrument instantiation.

    Creates a file list for a given range if the `file_date_range`
    keyword is set at instantiation.

    Parameters
    ----------
    test_init_kwarg : any
        Testing keyword (default=None)

    """

    pysat.logger.info(ackn_str)
    self.acknowledgements = ackn_str
    self.references = refs

    # Assign parameters for testing purposes
    self.new_thing = True
    self.test_init_kwarg = test_init_kwarg

    return


def clean(self, test_clean_kwarg=None):
    """Pass through when asked to clean a test instrument.

    Parameters
    ----------
    test_clean_kwarg : any
        Testing keyword. If these keywords contain 'logger', 'warning', or
        'error', the message entered as the value to that key will be returned
        as a logging.WARNING, UserWarning, or ValueError, respectively. If the
        'change' kwarg is set, the clean level will be changed to the specified
        value. (default=None)

    """

    self.test_clean_kwarg = test_clean_kwarg

    if isinstance(test_clean_kwarg, dict):
        if 'change' in test_clean_kwarg.keys():
            self.clean_level = test_clean_kwarg['change']

        if 'logger' in test_clean_kwarg.keys():
            pysat.logger.warning(test_clean_kwarg['logger'])

        if 'warning' in test_clean_kwarg.keys():
            warnings.warn(test_clean_kwarg['warning'], UserWarning)

        if 'error' in test_clean_kwarg.keys():
            raise ValueError(test_clean_kwarg['error'])

    return


# Optional methods
def concat_data(self, new_data, **kwargs):
    """Concatonate data to self.data for extra time dimensions.

    Parameters
    ----------
    new_data : xarray.Dataset or list of such objects
        New data objects to be concatonated
    **kwargs : dict
        Optional keyword arguments passed to xr.concat

    Note
    ----
    Expects the extra time dimensions to have a variable name that starts
    with 'time', and no other dimensions to have a name that fits this format.

    """
    # Establish the time dimensions, ensuring the standard variable is included
    # whether or not it is treated as a variable
    time_dims = [self.index.name]
    time_dims.extend([var for var in self.variables if var.find('time') == 0
                      and var != self.index.name])

    # Concatonate using the appropriate method for the number of time
    # dimensions
    if len(time_dims) == 1:
        # There is only one time dimensions, but other dimensions may
        # need to be adjusted
        new_data = pysat.utils.coords.expand_xarray_dims(
            new_data, self.meta, exclude_dims=time_dims)

        # Specify the dimension, if not otherwise specified
        if 'dim' not in kwargs:
            kwargs['dim'] = self.index.name

        self.data = xr.concat(new_data, **kwargs)
    else:
        inners = None
        for ndata in new_data:
            # Separate into inner datasets
            inner_keys = {dim: [key for key in ndata.keys()
                                if dim in ndata[key].dims] for dim in time_dims}
            inner_dat = {dim: ndata.get(inner_keys[dim]) for dim in time_dims}

            # Add 'single_var's into 'time' dataset to keep track
            sv_keys = [val.name for val in ndata.values()
                       if 'single_var' in val.dims]
            singlevar_set = ndata.get(sv_keys)
            inner_dat[self.index.name] = xr.merge([inner_dat[self.index.name],
                                                   singlevar_set])

            # Concatenate along desired dimension with previous data
            if inners is None:
                # No previous data, assign the data separated by dimension
                inners = dict(inner_dat)
            else:
                # Concatenate with existing data
                inners = {dim: xr.concat([inners[dim], inner_dat[dim]],
                                         dim=dim) for dim in time_dims}

        # Combine all time dimensions
        if inners is not None:
            data_list = [inners[dim] for dim in time_dims]
            self.data = xr.merge(data_list)
    return


def preprocess(self, test_preprocess_kwarg=None):
    """Perform standard preprocessing.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue). Object
    modified in place.

    Parameters
    ----------
    test_preprocess_kwarg : any
        Testing keyword (default=None)

    """
    self.test_preprocess_kwarg = test_preprocess_kwarg

    return


# Utility functions
def initialize_test_meta(epoch_name, data_keys):
    """Initialize meta data for test instruments.

    This routine should be applied to test instruments at the end of the load
    routine.

    Parameters
    ----------
    epoch_name : str
        The variable name of the instrument epoch.
    data : pds.DataFrame or xr.Dataset
        The dataset keys from the instrument.

    """
    # Create standard metadata for all parameters
    data_types = {'uts': float, 'mlt': float, 'slt': float, 'longitude': float,
                  'latitude': float, 'altitude': float, 'orbit_num': int,
                  'dummy1': int, 'dummy2': int, 'dummy3': int, 'dummy4': int,
                  'unicode_dummy': str, 'string_dummy': str,
                  'dummy_drifts': float, 'int8_dummy': int, 'int16_dummy': int,
                  'int32_dummy': int, 'int64_dummy': int, 'profiles': int,
                  'series_profiles': float}
    meta = pysat.Meta(data_types=data_types)
    meta['uts'] = {'units': 's', 'long_name': 'Universal Time',
                   'desc': 'Number of seconds since mindight UT',
                   'value_min': 0.0, 'value_max': 86400.0}
    meta['mlt'] = {'units': 'hours', 'long_name': 'Magnetic Local Time',
                   'value_min': 0.0, 'value_max': 24.0,
                   'desc': 'Local time at magnetic field line at equator.'}
    meta['slt'] = {'units': 'hours', 'long_name': 'Solar Local Time',
                   'value_min': 0.0, 'value_max': 24.0,
                   'desc': 'Mean solar time.',
                   'notes': 'Example of notes.'}
    meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude',
                         'value_min': 0.0, 'value_max': 360.0,
                         'desc': 'Geographic Longitude'}
    meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude',
                        'value_min': -90.0, 'value_max': 90.0,
                        'desc': 'Geographic Latituce'}
    meta['altitude'] = {'units': 'km', 'long_name': 'Altitude',
                        'value_min': 0.0, 'value_max': np.inf,
                        'desc': 'Height above mean Earth.'}
    meta['orbit_num'] = {'units': '', 'long_name': 'Orbit Number',
                         'desc': 'Orbit Number', 'value_min': 0,
                         'value_max': 25000, 'fill': -1,
                         'notes': ''.join(['Number of orbits since the start ',
                                           'of the mission. For this ',
                                           'simulation we use the number of ',
                                           '5820 second periods since the ',
                                           'start, 2008-01-01.'])}

    meta['dummy1'] = {'value_min': 0, 'value_max': 24, 'fill': -1}
    meta['dummy2'] = {'value_min': 0, 'value_max': 24, 'fill': -1}
    meta['dummy3'] = {'value_min': 0., 'value_max': 24024.}
    meta['dummy4'] = {'desc': 'Dummy variable - UTS like', 'value_min': 0.,
                      'value_max': 86400., 'fill': np.nan}

    meta['unicode_dummy'] = {'desc': 'Dummy unicode variable.', 'units': ''}
    meta['string_dummy'] = {'desc': 'Dummy string variable.', 'units': ''}

    meta['dummy_drifts'] = {'desc': 'Dummy drift values.', 'value_min': -1000.,
                            'value_max': 1000., 'fill': np.nan}

    # Add metadata for integer dummy variables
    meta_dict = {'value_min': 0, 'value_max': 2, 'fill': -1}
    var_list = ['int8_dummy', 'int16_dummy', 'int32_dummy', 'int64_dummy']
    for var in var_list:
        meta[var] = meta_dict

    # Standard metadata required for xarray
    meta['profiles'] = {'long_name': 'profiles', 'value_min': 0,
                        'value_max': 4294967295, 'fill': -1,
                        'desc': ''.join(['Testing profile multi-dimensional ',
                                         'data indexed by time.']),
                        'notes': ''.join([
                            'Note the value_max is largest netCDF4 supports, ',
                            'but is lower than actual 64-bit int limit.'])}

    # Optional and standard metadata for xarray
    for var in data_keys:
        if var.find('variable_profiles') == 0:
            meta[var] = {'desc': 'Profiles with variable altitude.'}

            if len(var) > 17:
                tvar = 'time{:s}'.format(var[17:])
                meta[tvar] = {'desc': 'Additional time variable.'}

    # Standard metadata required for xarray.
    meta['profile_height'] = {'value_min': 0, 'value_max': 14, 'fill': -1,
                              'desc': 'Altitude of profile data.'}
    meta['variable_profile_height'] = {'long_name': 'Variable Profile Height'}

    # Standard metadata required for xarray.
    meta['images'] = {'desc': 'pixel value of image',
                      'notes': 'function of image_lat and image_lon'}
    meta['x'] = {'desc': 'x-value of image pixel',
                 'notes': 'Dummy Variable',
                 'value_min': 0, 'value_max': 7, 'fill': -1}
    meta['y'] = {'desc': 'y-value of image pixel',
                 'notes': 'Dummy Variable',
                 'value_min': 0, 'value_max': 7, 'fill': -1}
    meta['z'] = {'desc': 'z-value of profile height',
                 'notes': 'Dummy Variable',
                 'value_min': 0, 'value_max': 5, 'fill': -1}
    meta['image_lat'] = {'desc': 'Latitude of image pixel',
                         'notes': 'Dummy Variable',
                         'value_min': -90., 'value_max': 90.}
    meta['image_lon'] = {'desc': 'Longitude of image pixel',
                         'notes': 'Dummy Variable',
                         'value_min': 0., 'value_max': 360.}

    # Drop unused meta data for desired instrument.
    for var in meta.keys():
        if var not in data_keys:
            meta.drop(var)

    return meta


def list_files(tag='', inst_id='', data_path='', format_str=None,
               file_date_range=None, test_dates=None, mangle_file_dates=False,
               test_list_files_kwarg=None):
    """Produce a fake list of files spanning three years.

    Parameters
    ----------
    tag : str
        Tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    inst_id : str
        Instrument ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    data_path : str
        Path to data directory. This input is nominally provided by pysat
        itself. (default='')
    format_str : str or NoneType
        File format string. This is passed from the user at pysat.Instrument
         instantiation, if provided. (default=None)
    file_date_range : pds.date_range
        File date range. The default mode generates a list of 3 years of daily
        files (1 year back, 2 years forward) based on the test_dates passed
        through below.  Otherwise, accepts a range of files specified by the
        user. (default=None)
    test_dates : dt.datetime or NoneType
        Pass the _test_date object through from the test instrument files
    mangle_file_dates : bool
        If True, file dates are shifted by 5 minutes. (default=False)
    test_list_files_kwarg : any
        Testing keyword (default=None)

    Returns
    -------
    Series of filenames indexed by file time

    """

    # Support keyword testing
    pysat.logger.info(''.join(('test_list_files_kwarg = ',
                               str(test_list_files_kwarg))))

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


def list_remote_files(tag='', inst_id='', data_path='', format_str=None,
                      start=None, stop=None, test_dates=None, user=None,
                      password=None, mangle_file_dates=False,
                      test_list_remote_kwarg=None):
    """Produce a fake list of files to simulate new files on a remote server.

    Note
    ----
    List spans three years and one month.

    Parameters
    ----------
    tag : str
        Tag name used to identify particular data set.
        This input is nominally provided by pysat itself. (default='')
    inst_id : str
        Instrument ID used to identify particular data.
        This input is nominally provided by pysat itself. (default='')
    data_path : str
        Path to data directory. This input is nominally provided by pysat
        itself. (default='')
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
    user : str or NoneType
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied. (default=None)
    password : str or NoneType
        Password for data download. (default=None)
    mangle_file_dates : bool
        If True, file dates are shifted by 5 minutes. (default=False)
    test_list_remote_kwarg : any
        Testing keyword (default=None)

    Returns
    -------
    pds.Series
        Filenames indexed by file time, see list_files for more info

    """

    # Support keyword testing
    pysat.logger.info(''.join(('test_list_remote_kwarg = ',
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


def download(date_array, tag, inst_id, data_path='', user=None,
             password=None, test_download_kwarg=None):
    """Pass through when asked to download for a test instrument.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : str
        Tag identifier used for particular dataset. This input is provided by
        pysat.
    inst_id : str
        Instrument ID string identifier used for particular dataset. This input
        is provided by pysat.
    data_path : str
        Path to directory to download data to. (default='')
    user : string or NoneType
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for downloads this routine here must
        error if user not supplied. (default=None)
    password : string or NoneType
        Password for data download. (default=None)
    test_download_kwarg : any
        Testing keyword (default=None)

    Raises
    ------
    ValueError
        When user/password are required but not supplied

    Warnings
    --------
    When no download support will be provided

    Note
    ----
    This routine is invoked by pysat and is not intended for direct use by the
    end user.

    """

    # Support keyword testing
    pysat.logger.info(''.join(('test_download_kwarg = ',
                               str(test_download_kwarg))))

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
    """Generate fake data over a given range.

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


def generate_times(fnames, num, freq='1s', start_time=None):
    """Construct list of times for simulated instruments.

    Parameters
    ----------
    fnames : list
        List of filenames.
    num : int
        Maximum number of times to generate.  Data points will not go beyond the
        current day.
    freq : str
        Frequency of temporal output, compatible with pandas.date_range
        (default='1s')
    start_time : dt.timedelta or NoneType
        Offset time of start time in fractional hours since midnight UT.
        If None, set to 0.
        (default=None)

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

    if start_time is not None and not isinstance(start_time, dt.timedelta):
        raise ValueError('start_time must be a dt.timedelta object')

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
        if start_time is not None:
            start_date = date + start_time
        else:
            start_date = date
        index = pds.date_range(start=start_date, end=end_date, freq=freq)
        index = index[0:num]
        indices.extend(index)
        uts.extend(index.hour * 3600 + index.minute * 60 + index.second
                   + index.microsecond * 1e-6 + 86400. * loop)

    # Combine index times together
    index = pds.DatetimeIndex(indices)

    # Make UTS an array
    uts = np.array(uts)

    return uts, index, dates


def define_period():
    """Define the default periods for the fake data functions.

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
    """Define the default ranges for the fake data functions.

    Returns
    -------
    def_range : dict
        Dictionary of periods to use in test instruments

    """

    def_range = {'lt': [0.0, 24.0],
                 'lon': [0.0, 360.0],
                 'angle': [0.0, 2.0 * np.pi]}

    return def_range


def create_files(inst, start, stop, freq='1D', use_doy=True,
                 root_fname='pysat_testing_{year:04d}_{day:03d}.txt',
                 version=False, content=None, timeout=None):
    """Create a file set using the year and day of year.

    Parameters
    ----------
    inst : pysat.Instrument
        A test instrument, used to generate file path
    start : dt.datetime
        The date for the first file to create
    stop : dt.datetime
        The date for the last file to create
    freq : str
        Frequency of file output.  Codes correspond to pandas.date_range
        codes (default='1D')
    use_doy : bool
        If True use Day of Year (doy), if False use day of month and month.
        (default=True)
    root_fname : str
        The format of the file name to create. Supports standard pysat template
        variables 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', 'cycle'. (default='pysat_testing_{year:04d}_{day:03d}.txt')
    version : bool
        If True, iterate over version / revision / cycle. If False,
        ignore version / revision / cycle. (default=False)
    content : str
        Custom text to write to temporary files (default=None)
    timeout : float
        Time is seconds to lock the files being created.  If None, no timeout is
        used.  (default=None)

    Examples
    --------
    ::

        # Commands below create empty files located at `inst.files.data_path`,
        # one per day, spanning 2008, where `year`, `month`, and `day`
        # are filled in using the provided template string appropriately.
        # The produced files are named like: 'pysat_testing_2008_01_01.txt'
        import datetime as dt
        inst = pysat.Instrument('pysat', 'testing')
        root_fname='pysat_testing_{year:04d}_{month:02d}_{day:02d}.txt'
        create_files(inst, dt.datetime(2008, 1, 1), dt.datetime(2008, 12, 31),
                     root_fname=root_fname, use_doy=False)


        # The command below uses the default values for `create_files`, which
        # produces a daily set of files, labeled by year and day of year.
        # The files are names like: 'pysat_testing_2008_001.txt'
        create_files(inst, dt.datetime(2008, 1, 1), dt.datetime(2008, 12, 31))

    """

    # Define the time range and file naming variables
    dates = putime.create_date_range(start, stop, freq=freq)

    if version:
        versions = np.array([1, 2])
        revisions = np.array([0, 1])
        cycles = np.array([0, 1])
    else:
        versions = [None]
        revisions = [None]
        cycles = [None]

    # Create empty files
    for date in dates:
        yr, doy = putime.getyrdoy(date)
        if not use_doy:
            doy = date.day
        for version in versions:
            for revision in revisions:
                for cycle in cycles:

                    fname = os.path.join(inst.files.data_path,
                                         root_fname.format(year=yr,
                                                           day=doy,
                                                           month=date.month,
                                                           hour=date.hour,
                                                           minute=date.minute,
                                                           second=date.second,
                                                           version=version,
                                                           revision=revision,
                                                           cycle=cycle))
                    with NetworkLock(fname, 'w') as fout:
                        if content is not None:
                            fout.write(content)
                        if timeout is not None:
                            time.sleep(timeout)
    return


def non_monotonic_index(index):
    """Adjust the index to be non-monotonic.

    Parameters
    ----------
    index : pds.DatetimeIndex
        The index generated in an instrument test file.

    Returns
    -------
    new_index : pds.DatetimeIndex
        A non-montonic index

    """

    new_index = index.tolist()

    # Create a non-monotonic index
    new_index[6:9], new_index[3:6] = new_index[3:6], new_index[6:9]

    # Convert back to DatetimeIndex
    new_index = pds.to_datetime(new_index)

    return new_index


def non_unique_index(index):
    """Adjust the index to be non-unique.

    Parameters
    ----------
    index : pds.DatetimeIndex
        The index generated in an instrument test file.

    Returns
    -------
    new_index : pds.DatetimeIndex
        A non-unique index

    """

    new_index = index.tolist()

    # Create a non-unique index
    new_index[1:3] = [new_index[1]] * 2

    # Convert back to DatetimeIndex
    new_index = pds.to_datetime(new_index)

    return new_index
