"""
pysat.utils.time - date and time operations in pysat
=========================================

pysat.utils.time contains a number of functions used throughout
the pysat package, including interactions with datetime objects,
seasons, and calculation of solar local time
"""

import numpy as np
import pandas as pds
from pysat import datetime


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
        doy = date.toordinal() - datetime(date.year, 1, 1).toordinal() + 1
    except AttributeError:
        raise AttributeError("Must supply a pandas datetime object or " +
                             "equivalent")
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
    str_hr : string ('0')
        String containing the hour of day
    str_min : string ('0')
        String containing the minutes of hour
    str_sec : string ('0')
        String containing the seconds of minute
    century : int (2000)
        Century, only used if str_yr is a 2-digit year

    Returns
    -------
    out_date : pds.datetime
        Pandas datetime object

    """

    yr = int(str_yr) + century if len(str_yr) == 2 else int(str_yr)
    out_date = pds.datetime(yr, int(str_mo), int(str_day), int(str_hr),
                            int(str_min), int(str_sec))

    return out_date


def calc_freq(index):
    """ Determine the frequency for a time index

    Parameters
    ----------
    index : (array-like)
        Datetime list, array, or Index

    Returns
    -------
    freq : (str)
       Frequency string as described in Pandas Offset Aliases

    Notes
    -----
    Calculates the minimum time difference and sets that as the frequency.

    To reduce the amount of calculations done, the returned frequency is
    either in seconds (if no sub-second resolution is found) or nanoseconds.

    """

    # Test the length of the input
    if len(index) < 2:
        raise ValueError("insufficient data to calculate frequency")

    # Calculate the minimum temporal difference
    del_time = (np.array(index[1:]) - np.array(index[:-1])).min()

    # Convert minimum to seconds
    try:
        # First try as timedelta
        freq_sec = del_time.total_seconds()
    except AttributeError as err:
        # Now try as numpy.timedelta64
        if isinstance(del_time, np.timedelta64):
            freq_sec = float(del_time) * 1.0e-9
        else:
            raise AttributeError("Input should be times: {:}".format(err))

    # Format output frequency
    if np.floor(freq_sec) == freq_sec:
        # The frequency is on the order of seconds or greater
        freq = "{:.0f}S".format(freq_sec)
    else:
        # There are sub-seconds.  Go straigt to nanosec for best resoution
        freq = "{:.0f}N".format(freq_sec * 1.0e9)

    return freq


def season_date_range(start, stop, freq='D'):
    """
    Deprecated Function, will be removed in future version.

    .. deprecated:: 2.1.0
      `season_date_range` will be removed in pysat 3.0.0, this will be
      replaced by create_date_range



    """

    import warnings

    warnings.warn(' '.join(["utils.time.season_date_range is deprecated, use",
                            "utils.time.create_date_range instead"]),
                  DeprecationWarning, stacklevel=2)

    season = create_date_range(start, stop, freq=freq)

    return season


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
        year : array_like of ints
        month : array_like of ints or None
        day : array_like of ints
            for day (default) or day of year (use month=None)
        uts : array_like of floats

    Returns
    -------
        Pandas timeseries index.

    Note
    ----
    Leap seconds have no meaning here.

    """

    # need a timeseries index for storing satellite data in pandas but
    # creating a datetime object for everything is too slow
    # so I calculate the number of nanoseconds elapsed since first sample,
    # and create timeseries index from that.
    # Factor of 20 improvement compared to previous method,
    # which itself was an order of magnitude faster than datetime.

    # get list of unique year, and month
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
    # track changes in seconds
    uts_del = uts.copy().astype(float)
    # determine where there are changes in year and month that need to be
    # accounted for
    _, idx = np.unique(year*100.+month, return_index=True)
    # create another index array for faster algorithm below
    idx2 = np.hstack((idx, len(year) + 1))
    # computes UTC seconds offset for each unique set of year and month
    for _idx, _idx2 in zip(idx[1:], idx2[2:]):
        temp = (datetime(year[_idx], month[_idx], 1) -
                datetime(year[0], month[0], 1))
        uts_del[_idx:_idx2] += temp.total_seconds()

    # add in UTC seconds for days, ignores existence of leap seconds
    uts_del += (day - 1) * 86400
    # add in seconds since unix epoch to first day
    uts_del += (datetime(year[0], month[0], 1) -
                datetime(1970, 1, 1)).total_seconds()
    # going to use routine that defaults to nanseconds for epoch
    uts_del *= 1E9
    return pds.to_datetime(uts_del)
