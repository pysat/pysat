#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""
pysat date and time utilities
"""

import datetime as dt
import numpy as np
import pandas as pds
import re


def getyrdoy(date):
    """Return a tuple of year, day of year for a supplied datetime object.

    Parameters
    ----------
    date : datetime.datetime
        Datetime object

    Returns
    -------
    year : int
        Integer year
    doy : int
        Integer day of year

    """

    try:
        doy = date.toordinal() - dt.datetime(date.year, 1, 1).toordinal() + 1
    except AttributeError:
        raise AttributeError(' '.join(("Must supply a pandas datetime object",
                                       "or equivalent")))
    else:
        return date.year, doy


def parse_date(str_yr, str_mo, str_day, str_hr='0', str_min='0', str_sec='0',
               century=2000):
    """ Basic date parser for file reading

    Parameters
    ----------
    str_yr : string
        String containing the year (2 or 4 digits)
    str_mo : string
        String containing month digits
    str_day : string
        String containing day of month digits
    str_hr : string
        String containing the hour of day (default='0')
    str_min : string
        String containing the minutes of hour (default='0')
    str_sec : string
        String containing the seconds of minute (default='0')
    century : int
        Century, only used if str_yr is a 2-digit year (default=2000)

    Returns
    -------
    out_date : dt.datetime
        datetime object

    """

    yr = int(str_yr) + century if len(str_yr) == 2 else int(str_yr)
    out_date = dt.datetime(yr, int(str_mo), int(str_day), int(str_hr),
                           int(str_min), np.int64(str_sec))

    return out_date


def calc_res(index, use_mean=False):
    """ Determine the resolution for a time index

    Parameters
    ----------
    index : array-like
        Datetime list, array, or Index
    use_mean : bool
        Use the minimum time difference if False, use the mean time difference
        if True (default=False)

    Returns
    -------
    res_sec : float
       Resolution value in seconds

    """

    # Test the length of the input
    if len(index) < 2:
        raise ValueError("insufficient data to calculate resolution")

    # Calculate the minimum temporal difference
    del_time = (np.array(index[1:]) - np.array(index[:-1]))

    if use_mean:
        del_time = del_time.mean()
    else:
        del_time = del_time.min()

    # Convert time difference to seconds, based on possible data types
    try:
        # First try as timedelta
        res_sec = del_time.total_seconds()
    except AttributeError as aerr:
        # Now try as numpy.timedelta64
        if isinstance(del_time, np.timedelta64):
            res_sec = np.float64(del_time) * 1.0e-9
        else:
            raise AttributeError("Input should be times: {:}".format(aerr))

    return res_sec


def calc_freq(index):
    """ Determine the frequency for a time index

    Parameters
    ----------
    index : array-like
        Datetime list, array, or Index

    Returns
    -------
    freq : str
       Frequency string as described in Pandas Offset Aliases

    Note
    ----
    Calculates the minimum time difference and sets that as the frequency.

    To reduce the amount of calculations done, the returned frequency is
    either in seconds (if no sub-second resolution is found) or nanoseconds.

    See Also
    --------
    pds.offsets.DateOffset

    """
    # Get the frequency of the index in seconds
    freq_sec = calc_res(index, use_mean=False)

    # Format output frequency
    if np.floor(freq_sec) == freq_sec:
        # The frequency is on the order of seconds or greater
        freq = "{:.0f}S".format(freq_sec)
    else:
        # There are sub-seconds.  Go straigt to nanosec for best resoution
        freq = "{:.0f}N".format(freq_sec * 1.0e9)

    return freq


def freq_to_res(freq):
    """Convert a frequency string to a resolution value in seconds

    Parameters
    ----------
    freq : str
       Frequency string as described in Pandas Offset Aliases

    Returns
    -------
    res_sec : np.float64
       Resolution value in seconds

    See Also
    --------
    pds.offsets.DateOffset

    Reference
    ---------
    Separating alpha and numeric portions of strings, as described in:
    https://stackoverflow.com/a/12409995

    """
    # Separate the alpha and numeric portions of the string
    regex = re.compile(r'(\d+|\s+)')
    out_str = [sval for sval in regex.split(freq) if len(sval) > 0]

    if len(out_str) > 2:
        raise ValueError('unexpected frequency format: {:s}'.format(freq))

    # Cast the alpha and numeric portions
    freq_str = out_str[-1]
    freq_num = 1.0 if len(out_str) == 1 else np.float64(out_str[0])

    # Calculate the resolution in seconds
    res_sec = pds.Timedelta(freq_num, unit=freq_str).total_seconds()

    return res_sec


def create_date_range(start, stop, freq='D'):
    """
    Return array of datetime objects using input frequency from start to stop

    Supports single datetime object or list, tuple, ndarray of start and
    stop dates.

    freq codes correspond to pandas date_range codes, D daily, M monthly,
    S secondly

    """

    if hasattr(start, '__iter__'):
        # missing check for datetime
        season = pds.date_range(start[0], stop[0], freq=freq)
        for (sta, stp) in zip(start[1:], stop[1:]):
            season = season.append(pds.date_range(sta, stp, freq=freq))
    else:
        season = pds.date_range(start, stop, freq=freq)
    return season


def create_datetime_index(year=None, month=None, day=None, uts=None):
    """Create a timeseries index using supplied year, month, day, and ut in
    seconds.

    Parameters
    ----------
        year : array_like or NoneType
            Array of year values as np.int (default=None)
        month : array_like or NoneType
           Array of month values as np.int. Leave None if using day for
           day of year. (default=None)
        day : array_like or NoneType
            Array of number of days as np.int. If month=None then value
            interpreted as day of year, otherwise, day of month. (default=None)
        uts : array-like or NoneType
            Array of UT seconds of minute as np.float64 values (default=None)

    Returns
    -------
        Pandas timeseries index.

    Note
    ----
    Leap seconds have no meaning here.

    """

    # We need a timeseries index for storing satellite data in pandas, but
    # creating a datetime object for everything is too slow.  Instead, we
    # calculate the number of nanoseconds elapsed since first sample and
    # create timeseries index from that.  This yields a factor of 20
    # improvement compared to previous method, which itself was an order of
    # magnitude faster than datetime.

    # Get list of unique year, and month
    if not hasattr(year, '__iter__'):
        raise ValueError('Must provide an iterable for all inputs.')
    if len(year) == 0:
        raise ValueError('Length of array must be larger than 0.')
    year = year.astype(int)
    if month is None:
        month = np.ones(len(year), dtype=int)
    else:
        month = month.astype(int)

    if uts is None:
        uts = np.zeros(len(year))
    if day is None:
        day = np.ones(len(year))
    day = day.astype(int)

    # Track changes in seconds
    uts_del = uts.copy().astype(np.float64)

    # Determine where there are changes in year and month that need to be
    # accounted for
    _, idx = np.unique((year * 100. + month), return_index=True)

    # Create another index array for faster algorithm below
    idx2 = np.hstack((idx, len(year) + 1))

    # Computes UTC seconds offset for each unique set of year and month
    for _idx, _idx2 in zip(idx[1:], idx2[2:]):
        temp = (dt.datetime(year[_idx], month[_idx], 1)
                - dt.datetime(year[0], month[0], 1))
        uts_del[_idx:_idx2] += temp.total_seconds()

    # Add in UTC seconds for days, ignores existence of leap seconds
    uts_del += (day - 1) * 86400.

    # Add in seconds since unix epoch to first day
    uts_del += (dt.datetime(year[0], month[0], 1)
                - dt.datetime(1970, 1, 1)).total_seconds()

    # Going to use routine that defaults to nanseconds for epoch
    uts_del *= 1E9
    return pds.to_datetime(uts_del)


def filter_datetime_input(date):
    """
    Returns datetime that only includes year, month, and day.

    Parameters
    ----------
    date : NoneType, array-like, or datetime
        Single or sequence of datetime inputs

    Returns
    -------
    out_date: NoneType, datetime, or list of datetimes
        NoneType input yeilds NoneType output, array-like yeilds list,
        datetime object yeilds like.  All datetime output excludes the
        sub-daily temporal increments (keeps only date information).

    Note
    ----
    Checks for timezone information not in UTC

    """

    if date is None:
        out_date = None
    else:
        # Check for timezone information and remove time of day for
        # single datetimes and iterable containers of datetime objects
        if hasattr(date, '__iter__'):
            out_date = []
            for in_date in date:
                if(in_date.tzinfo is not None
                   and in_date.utcoffset() is not None):
                    in_date = in_date.astimezone(tz=dt.timezone.utc)

                out_date.append(dt.datetime(in_date.year, in_date.month,
                                            in_date.day))
        else:
            if date.tzinfo is not None and date.utcoffset() is not None:
                date = date.astimezone(tz=dt.timezone.utc)

            out_date = dt.datetime(date.year, date.month, date.day)

    return out_date


def today():
    """Returns today's date (UTC), with no hour, minute, second, etc.

    Returns
    -------
    today_utc: datetime
        Today's date in UTC

    """
    today_utc = filter_datetime_input(dt.datetime.utcnow())

    return today_utc
