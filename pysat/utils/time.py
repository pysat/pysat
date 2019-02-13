"""
pysat.utils.time - date and time operations in pysat
=========================================

pysat.utils.time contains a number of functions used throughout
the pysat package, including interactions with datetime objects,
seasons, and calculation of solar local time
"""

import numpy as np


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


def season_date_range(start, stop, freq='D'):
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
    uts_del += (day-1)*86400
    # add in seconds since unix epoch to first day
    uts_del += (datetime(year[0], month[0], 1) -
                datetime(1970, 1, 1)).total_seconds()
    # going to use routine that defaults to nanseconds for epoch
    uts_del *= 1E9
    return pds.to_datetime(uts_del)


def adjust_cyclic_data(samples, high=2.0*np.pi, low=0.0):
    """Adjust cyclic values such as longitude to a different scale

    Parameters
    -----------
    samples : array_like
        Input array
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
    axis : int or NoneType
        Axis along which standard deviations are computed.  The default is to
        compute the standard deviation of the flattened array

    Returns
    --------
    out_samples : float
        Circular standard deviation

    """

    out_samples = np.asarray(samples)
    sample_range = high - low
    out_samples[out_samples >= high] -= sample_range
    out_samples[out_samples < low] += sample_range

    return out_samples


def update_longitude(inst, lon_name=None, high=180.0, low=-180.0):
    """ Update longitude to the desired range

    Parameters
    ------------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data
    high : float
        Highest allowed longitude value (default=180.0)
    low : float
        Lowest allowed longitude value (default=-180.0)

    Returns
    ---------
    updates instrument data in column 'lon_name'

    """
    from pysat.utils import adjust_cyclic_data

    if lon_name not in inst.data.keys():
        raise ValueError('uknown longitude variable name')

    new_lon = adjust_cyclic_data(inst[lon_name], high=high, low=low)

    # Update based on data type
    if inst.pandas_format:
        inst[lon_name] = new_lon
    else:
        inst[lon_name].data = new_lon

    return


def calc_solar_local_time(inst, lon_name=None, slt_name='slt'):
    """ Append solar local time to an instrument object

    Parameters
    ------------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data key (assumes data are in degrees)
    slt_name : string
        name of the output solar local time data key (default='slt')

    Returns
    ---------
    updates instrument data in column specified by slt_name

    """
    import datetime as dt

    if lon_name not in inst.data.keys():
        raise ValueError('uknown longitude variable name')

    # Convert from numpy epoch nanoseconds to UT seconds of day
    utsec = list()
    for nptime in inst.index.values.astype(int):
        # Numpy times come out in nanoseconds and timestamp converts
        # from seconds
        dtime = dt.datetime.fromtimestamp(nptime * 1.0e-9)
        utsec.append((dtime.hour * 3600.0 + dtime.minute * 60.0 +
                      dtime.second + dtime.microsecond * 1.0e-6) / 3600.0)

    # Calculate solar local time
    slt = np.array([t + inst[lon_name][i] / 15.0 for i, t in enumerate(utsec)])

    # Ensure that solar local time falls between 0 and 24 hours
    slt[slt >= 24.0] -= 24.0
    slt[slt < 0.0] += 24.0

    # Add the solar local time to the instrument
    if inst.pandas_format:
        inst[slt_name] = pds.Series(slt, index=inst.data.index)
    else:
        data = inst.data.assign(pysat_slt=(inst.data.coords.keys(), slt))
        data.rename({"pysat_slt": slt_name}, inplace=True)
        inst.data = data

    # Add units to the metadata
    inst.meta.__setitem__(slt_name, {inst.meta.units_label: 'h',
                                     inst.meta.name_label: "Solar Local Time",
                                     inst.meta.desc_label: "Solar local time",
                                     inst.meta.plot_label: "SLT",
                                     inst.meta.axis_label: "SLT",
                                     inst.meta.scale_label: "linear",
                                     inst.meta.min_label: 0.0,
                                     inst.meta.max_label: 24.0,
                                     inst.meta.fill_label: np.nan})

    return
