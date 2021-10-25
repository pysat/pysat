#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Date and time handling utilities."""

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

    Raises
    ------
    AttributeError
        If input date does not have `toordinal` method

    """

    try:
        doy = date.toordinal() - dt.datetime(date.year, 1, 1).toordinal() + 1
    except AttributeError:
        raise AttributeError(''.join(("Must supply a datetime object or an ",
                                      "equivalent class object with the ",
                                      "`toordinal` method")))
    else:
        return date.year, doy


def datetime_to_dec_year(dtime):
    """Convert datetime timestamp to a decimal year.

    Parameters
    ----------
    dtime : dt.datetime
        Datetime timestamp

    Returns
    -------
    year : float
        Year with decimal containing time increments of less than a year

    """

    year = float(dtime.year)
    day = float(dtime.strftime("%j")) - 1.0
    days_of_year = float(dt.datetime(dtime.year, 12, 31).strftime("%j"))

    # Add fraction of day to the day
    day += (dtime.hour + (dtime.minute
                          + (dtime.second + dtime.microsecond * 1.0e-6) / 60.0)
            / 60.0) / 24.0

    # Determine the fraction of days in this year and add to year
    year += (day / days_of_year)

    return year


def parse_date(str_yr, str_mo, str_day, str_hr='0', str_min='0', str_sec='0',
               century=2000):
    """Convert string dates to dt.datetime.

    Parameters
    ----------
    str_yr : str
        String containing the year (2 or 4 digits)
    str_mo : str
        String containing month digits
    str_day : str
        String containing day of month digits
    str_hr : str
        String containing the hour of day (default='0')
    str_min : str
        String containing the minutes of hour (default='0')
    str_sec : str
        String containing the seconds of minute (default='0')
    century : int
        Century, only used if str_yr is a 2-digit year (default=2000)

    Returns
    -------
    out_date : dt.datetime
        datetime object

    Raises
    ------
    ValueError
        If any input results in an unrealistic datetime object value

    """

    yr = int(str_yr) + century if len(str_yr) == 2 else int(str_yr)
    out_date = dt.datetime(yr, int(str_mo), int(str_day), int(str_hr),
                           int(str_min), np.int64(str_sec))

    return out_date


def calc_res(index, use_mean=False):
    """Determine the resolution for a time index.

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

    Raises
    ------
    ValueError
        If `index` is too short to calculate a time resolution

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
    """Determine the frequency for a time index.

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
    """Convert a frequency string to a resolution value in seconds.

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

    References
    ----------
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
    """Create array of datetime objects using input freq from start to stop.

    Parameters
    ----------
    start : dt.datetime or list-like of dt.datetime
        The beginning of the date range.  Supports list, tuple, or ndarray of
        start dates.
    stop : dt.datetime or list-like of dt.datetime
        The end of the date range.  Supports list, tuple, or ndarray of
        stop dates.
    freq : str
        The frequency of the desired output.  Codes correspond to pandas
        date_range codes: 'D' daily, 'M' monthly, 'S' secondly

    Returns
    -------
    season : pds.date_range
        Range of dates over desired time with desired frequency.

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
    """Create a timeseries index using supplied date and time.

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
            Array of UT seconds as np.float64 values (default=None)

    Returns
    -------
        Pandas timeseries index.

    Note
    ----
    Leap seconds have no meaning here.

    """

    # Get list of unique year, and month
    if not hasattr(year, '__iter__'):
        raise ValueError('Must provide an iterable for all inputs.')
    if len(year) == 0:
        raise ValueError('Length of array must be larger than 0.')

    # Establish default month
    if month is None:
        # If no month, assume January.  All days will be treated as day of year.
        month = np.ones(shape=len(year))

    # Initial day is first of given month.
    day0 = np.ones(shape=len(year))

    if day is None:
        # If no day, assume first of month.
        day = day0
    if uts is None:
        # If no seconds, assume start of day.
        uts = np.zeros(shape=len(year))

    # Initialize all dates as first of month and convert to index.
    # This method allows month-day and day of year to be used.
    df = pds.DataFrame({'year': year, 'month': month, 'day': day0})
    index = pds.DatetimeIndex(pds.to_datetime(df))

    # Add days (offset by 1) to each index.
    # Day is added here in case input is in day of year format.
    index += (day - 1).astype('timedelta64[D]')

    # Add seconds to each index.  Need to convert to nanoseconds first.
    index += (1e9 * uts).astype('timedelta64[ns]')

    return index


def filter_datetime_input(date):
    """Create a datetime object that only includes year, month, and day.

    Parameters
    ----------
    date : NoneType, array-like, or datetime
        Single or sequence of datetime inputs

    Returns
    -------
    out_date: NoneType, datetime, or array-like
        NoneType input yeilds NoneType output, array-like yeilds list of
        datetimes, datetime object yeilds like.  All datetime output excludes
        the sub-daily temporal increments (keeps only date information).

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
    """Obtain today's date (UTC), with no hour, minute, second, etc.

    Returns
    -------
    today_utc: datetime
        Today's date in UTC

    """
    today_utc = filter_datetime_input(dt.datetime.utcnow())

    return today_utc
