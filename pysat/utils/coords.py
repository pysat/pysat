#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Coordinate transformation functions for pysat."""

import datetime as dt
import numpy as np
import pandas as pds

import pysat


def adjust_cyclic_data(samples, high=2.0 * np.pi, low=0.0):
    """Adjust cyclic values such as longitude to a different scale.

    Parameters
    ----------
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
    -------
    out_samples : float
        Circular standard deviation

    """

    out_samples = np.asarray(samples)
    sample_range = high - low
    out_samples[out_samples >= high] -= sample_range
    out_samples[out_samples < low] += sample_range

    return out_samples


def update_longitude(inst, lon_name=None, high=180.0, low=-180.0):
    """Update longitude to the desired range.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument class object to be updated
    lon_name : str
        Name of the longtiude data in `inst`
    high : float
        Highest allowed longitude value (default=180.0)
    low : float
        Lowest allowed longitude value (default=-180.0)

    Note
    ----
    Updates instrument data in column provided by `lon_name`

    """
    if lon_name not in inst.variables:
        raise ValueError('unknown longitude variable name')

    new_lon = adjust_cyclic_data(inst[lon_name], high=high, low=low)

    # TODO(#988): Remove pandas/xarray logic after fixing issue in Instrument
    if inst.pandas_format:
        inst[lon_name] = new_lon
    else:
        inst.data = inst.data.update({lon_name: (inst[lon_name].dims, new_lon)})

    return


def calc_solar_local_time(inst, lon_name=None, slt_name='slt',
                          apply_modulus=True, ref_date=None):
    """Append solar local time to an instrument object.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument class object to be updated
    lon_name : str
        Name of the longtiude data key (assumes data are in degrees)
    slt_name : str
        Name of the output solar local time data key (default='slt')
    apply_modulus : bool
        If True, SLT values are confined to [0, 24), if False they may be
        positive or negative based on the value of their universal time
        relative to that of the reference date `ref_date`.
        (default=True)
    ref_date : dt.datetime or NoneType
        Reference initial date. If None, will use the date found at
        `inst.date`. Only valid if apply_modulus is True. (default=None)

    Note
    ----
    Updates Instrument data in column specified by `slt_name`, as well as
    Metadata

    """
    fill_val = np.nan

    if lon_name not in inst.data.keys():
        raise ValueError('unknown longitude variable name')

    if ref_date is not None and apply_modulus:
        istr = 'Keyword `ref_date` only supported if `apply_modulus`=False.'
        pysat.logger.info(istr)

    if ref_date is None:
        # Use date information attached to Instrument object
        ref_date = pds.Timestamp(inst.date)
    else:
        # Use user supplied reference date.
        ref_date = pds.Timestamp(ref_date)

    # Convert from numpy epoch nanoseconds to UT seconds of day
    ut_hr = list()
    for nptime in inst.index.values.astype(np.int64):
        # Numpy times come out in nanoseconds and timestamp converts
        # from seconds
        dtime = dt.datetime.utcfromtimestamp(nptime * 1.0e-9)
        ut_hr.append((dtime.hour * 3600.0 + dtime.minute * 60.0
                      + dtime.second + dtime.microsecond * 1.0e-6) / 3600.0)

    ut_hr = np.array(ut_hr)

    # Account for difference in days for calculations without modulus
    if not apply_modulus:
        day_diff = inst.index - ref_date
        day_diff = np.array([diff.days for diff in day_diff])
        ut_hr += day_diff * 24.

    # Calculate solar local time
    if inst[lon_name].shape == ut_hr.shape or inst[lon_name].shape == ():
        if inst[lon_name].shape == ():
            lon = np.float64(inst[lon_name])
        else:
            lon = inst[lon_name]

        slt = ut_hr + lon / 15.0
        coords = inst.index.name
    else:
        # This can only be accessed by xarray input, but longitude may or
        # may not depend on time
        if inst.index.name in inst[lon_name].coords:
            # Initalize the new shape and coordinatesx
            coords = [ckey for ckey in inst[lon_name].dims]
            slt = np.full(shape=inst[lon_name].shape, fill_value=fill_val)

            # Calculate for each UT hr
            for i, hr in enumerate(ut_hr):
                lon = inst[lon_name][inst.index.name == inst.index[0]]
                slt[i] = hr + lon / 15.0
        else:
            # Initialize the new shape and coordinates
            sshape = list(ut_hr.shape)
            sshape.extend(list(inst[lon_name].shape))

            coords = [ckey for ckey in inst[lon_name].dims]
            coords.insert(0, inst.index.name)

            slt = np.full(shape=sshape, fill_value=fill_val)

            # Calculate for each UT hr
            for i, hr in enumerate(ut_hr):
                slt[i] = hr + inst[lon_name] / 15.0

    if apply_modulus:
        # Ensure that solar local time falls between 0 and 24 hours
        slt = np.mod(slt, 24.0)
        min_val = 0.0
        max_val = 24.0
    else:
        # No modulus applied. Values are unbounded.
        min_val = -np.inf
        max_val = np.inf

    # Add the solar local time to the instrument
    if inst.pandas_format:
        inst[slt_name] = pds.Series(slt, index=inst.index)
    else:
        inst.data = inst.data.assign({slt_name: (coords, slt.data)})

    # Add units to the metadata
    inst.meta[slt_name] = {inst.meta.labels.units: 'h',
                           inst.meta.labels.name: "Solar Local Time",
                           inst.meta.labels.desc: "Solar local time in hours",
                           inst.meta.labels.min_val: min_val,
                           inst.meta.labels.max_val: max_val,
                           inst.meta.labels.fill_val: fill_val}

    return
