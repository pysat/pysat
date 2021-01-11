"""
pysat.utils.coords - coordinate transformations for pysat
=========================================================

pysat.utils.coords contains a number of coordinate-transformation
functions used throughout the pysat package.
"""

import datetime as dt
import numpy as np
import pandas as pds


def adjust_cyclic_data(samples, high=(2.0 * np.pi), low=0.0):
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
    ----------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data
    high : float
        Highest allowed longitude value (default=180.0)
    low : float
        Lowest allowed longitude value (default=-180.0)

    Returns
    -------
    updates instrument data in column 'lon_name'

    """

    from pysat.utils.coords import adjust_cyclic_data

    if lon_name not in inst.data.keys():
        raise ValueError('unknown longitude variable name')

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
    ----------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data key (assumes data are in degrees)
    slt_name : string
        name of the output solar local time data key (default='slt')

    Returns
    -------
    updates instrument data in column specified by slt_name

    """

    if lon_name not in inst.data.keys():
        raise ValueError('unknown longitude variable name')

    # Convert from numpy epoch nanoseconds to UT seconds of day
    ut_hr = list()
    for nptime in inst.index.values.astype(int):
        # Numpy times come out in nanoseconds and timestamp converts
        # from seconds
        dtime = dt.datetime.utcfromtimestamp(nptime * 1.0e-9)
        ut_hr.append((dtime.hour * 3600.0 + dtime.minute * 60.0
                      + dtime.second + dtime.microsecond * 1.0e-6) / 3600.0)
    # Calculate solar local time
    slt = np.array([t + inst[lon_name][i] / 15.0 for i, t in enumerate(ut_hr)])

    # Ensure that solar local time falls between 0 and 24 hours
    slt = np.mod(slt, 24.0)

    # Add the solar local time to the instrument
    if inst.pandas_format:
        inst[slt_name] = pds.Series(slt, index=inst.data.index)
    else:
        inst.data = inst.data.assign({slt_name: (inst.data.coords.keys(), slt)})

    # Add units to the metadata
    inst.meta[slt_name] = {inst.meta.labels.units: 'h',
                           inst.meta.labels.name: "Solar Local Time",
                           inst.meta.labels.desc: "Solar local time in hours",
                           inst.meta.labels.min_val: 0.0,
                           inst.meta.labels.max_val: 24.0,
                           inst.meta.labels.fill_val: np.nan}

    return
