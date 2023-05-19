#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Coordinate transformation functions for pysat."""

import datetime as dt
import numpy as np
import pandas as pds
import xarray as xr

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


def establish_common_coord(coord_vals, common=True):
    """Create a coordinate array that is appropriate for multiple data sets.

    Parameters
    ----------
    coord_vals : list-like
        A list of coordinate arrays of the same type: e.g., all geodetic
        latitude in degrees
    common : bool
        True to include locations where all coordinate arrays cover, False to
        use the maximum location range from the list of coordinates
        (default=True)

    Returns
    -------
    out_coord : array-like
        An array appropriate for the list of coordinate values

    Note
    ----
    Assumes that the supplied coordinates are distinct representations of
    the same value in the same units and range (e.g., longitude in degrees
    from 0-360).

    """

    start_val = None
    end_val = None
    res = None

    for coord_spec in coord_vals:
        # Ensure the coordinate specification is array-like
        coord_spec = np.asarray(coord_spec)
        if coord_spec.shape == ():
            coord_spec = np.asarray([coord_spec])

        if start_val is None:
            # Initialize the start and stop values
            start_val = coord_spec[0]
            end_val = coord_spec[-1]

            # Determine the resolution
            if start_val == end_val:
                res = np.inf
            else:
                res = (coord_spec[1:] - coord_spec[:-1]).mean()
        else:
            # Adjust the start and stop time as appropriate
            if common:
                if start_val < coord_spec[0]:
                    start_val = coord_spec[0]
                if end_val > coord_spec[-1]:
                    end_val = coord_spec[-1]
            else:
                if start_val > coord_spec[0]:
                    start_val = coord_spec[0]
                if end_val < coord_spec[-1]:
                    end_val = coord_spec[-1]

            # Update the resolution
            new_res = (coord_spec[1:] - coord_spec[:-1]).mean()
            if new_res < res:
                res = new_res

    # Construct the common index
    npnts = int((end_val - start_val) / res) + 1
    out_coord = np.linspace(start_val, end_val, npnts)

    return out_coord


def expand_xarray_dims(data_list, meta, dims_equal=False, exclude_dims=None):
    """Ensure that dimensions do not vary when concatenating data.

    Parameters
    ----------
    data_list : list-like
        List of xr.Dataset objects with the same dimensions and variables
    meta : pysat.Meta
        Metadata for the data in `data_list`
    dims_equal : bool
        Assert that all xr.Dataset objects have the same dimensions if True,
        the Datasets in `data_list` may have differing dimensions if False.
        (default=False)
    exclude_dims : list-like or NoneType
        Dimensions to exclude from evaluation or None (default=None)

    Returns
    -------
    out_list : list-like
        List of xr.Dataset objects with the same dimensions and variables,
        and with dimensions that all have the same values and data padded when
        needed.

    """
    # Get a list of the dimensions to exclude
    if exclude_dims is None:
        exclude_dims = []
    else:
        exclude_dims = pysat.utils.listify(exclude_dims)

    # Get a list of all the dimensions
    if dims_equal:
        if len(data_list) > 0:
            dims = [dim_key for dim_key in list(data_list[0].dims.keys())
                    if dim_key not in exclude_dims]
        else:
            dims = []
    else:
        dims = list()
        for sdata in data_list:
            if len(dims) == 0:
                dims = [dim_key for dim_key in list(sdata.dims.keys())
                        if dim_key not in exclude_dims]
            else:
                for dim in list(sdata.dims.keys()):
                    if dim not in dims and dim not in exclude_dims:
                        dims.append(dim)

    # After loading all the data, determine which dimensions may need to be
    # expanded, as they could differ in dimensions from file to file
    combo_dims = {dim: max([sdata.dims[dim] for sdata in data_list
                            if dim in sdata.dims]) for dim in dims}

    # Expand the data so that all dimensions are the same shape
    out_list = list()
    for i, sdata in enumerate(data_list):
        # Determine which dimensions need to be updated
        fix_dims = [dim for dim in sdata.dims.keys() if dim in combo_dims.keys()
                    and sdata.dims[dim] < combo_dims[dim]]

        new_data = {}
        update_new = False
        for dvar in sdata.data_vars.keys():
            # See if any dimensions need to be updated
            update_dims = list(set(sdata[dvar].dims) & set(fix_dims))

            # Save the old data as is, or pad it to have the right dims
            if len(update_dims) > 0:
                update_new = True
                new_shape = list(sdata[dvar].values.shape)
                old_slice = [slice(0, ns) for ns in new_shape]

                for dim in update_dims:
                    idim = list(sdata[dvar].dims).index(dim)
                    new_shape[idim] = combo_dims[dim]

                # Get the fill value
                if dvar in meta:
                    # If available, take it from the metadata
                    fill_val = meta[dvar, meta.labels.fill_val]
                else:
                    # Otherwise, use the data type
                    ftype = type(sdata[dvar].values.flatten()[0])
                    fill_val = meta.labels.default_values_from_type(
                        meta.labels.label_type['fill_val'], ftype)

                # Set the new data for output
                new_dat = np.full(shape=new_shape, fill_value=fill_val)
                new_dat[tuple(old_slice)] = sdata[dvar].values
                new_data[dvar] = (sdata[dvar].dims, new_dat)
            else:
                new_data[dvar] = sdata[dvar]

        # Get the updated dataset
        out_list.append(xr.Dataset(new_data) if update_new else sdata)

    return out_list
