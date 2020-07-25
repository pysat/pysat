"""
pysat.model_utils - interface for modeled observations
======================================================

Main Features
-------------
- Comparison of models and measured data.
- Matching of instruments to modelled data parameters.
- Extraction of instrument-aligned data from a modelled data set.
"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import numpy as np
import pandas as pds
import warnings

from pysat import logger


def satellite_view_through_model(sat, tie, scoords, tlabels):
    """Interpolate model values onto satellite orbital path.

    .. deprecated:: 2.2.0
      `satellite_view_through_model` will be removed in pysat 3.0.0, it will
      be added to pysatModels

    Parameters
    ----------
    sat : pysat.Instrument object
        Instrument object with some form of coordinates
    tie : ucar_tiegcm object
        Model run loaded as tie_gcm object
    scoords : string or list of strings
        Variable names reflecting coordinates in sat to interpolate model onto
    tlabels : string or list of strings
        Variable names from model to interpolate onto sat locations
    """

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatModelUtils instead:"
                            "https://github.com/pysat/pysatModelUtils"]),
                  DeprecationWarning, stacklevel=2)

    # tiegcm is in pressure levels, need in altitude, but on regular
    # grid
    import scipy.interpolate as interpolate

    # create input array using satellite time/position
    if isinstance(scoords, str):
        scoords = [scoords]
    coords = [sat[coord] for coord in scoords]
    coords.insert(0, sat.index.values.astype(int))
    sat_pts = [inp for inp in zip(*coords)]

    interp = {}
    if isinstance(tlabels, str):
        tlabels = [tlabels]
    for label in tlabels:
        points = [tie.data.coords[dim].values if dim != 'time' else
                  tie.data.coords[dim].values.astype(int)
                  for dim in tie[label].dims]
        interp[label] = interpolate.RegularGridInterpolator(points,
                                                            tie[label].values,
                                                            bounds_error=False,
                                                            fill_value=None)
        sat[''.join(('model_', label))] = interp[label](sat_pts)


def compare_model_and_inst(pairs=None, inst_name=[], mod_name=[],
                           methods=['all']):
    """Compare modelled and measured data

    .. deprecated:: 2.2.0
      `satellite_view_through_model` will be removed in pysat 3.0.0, it will
      be added to pysatModels

    Parameters
    ------------
    pairs : xarray.Dataset instance
        Dataset containing only the desired observation-model data pairs
    inst_name : list of strings
        ordered list of instrument measurements to compare to modelled data
    mod_name : list of strings
        ordered list of modelled data to compare to instrument measurements
    methods : list of strings
        statistics to calculate.  See Notes for accecpted inputs

    Returns
    ----------
    stat_dict : dict of dicts
        Dictionary where the first layer of keys denotes the instrument data
        name and the second layer provides the desired statistics
    data_units : dict
        Dictionary containing the units for the data

    Notes
    -----
    Statistics are calculated using PyForecastTools (imported as verify).
    See notes there for more details.

    all - all statistics
    all_bias - bias, meanPercentageError, medianLogAccuracy,
               symmetricSignedBias
    accuracy - returns dict with mean squared error, root mean squared error,
               mean absolute error, and median absolute error
    scaledAccuracy - returns dict with normaled root mean squared error, mean
                     absolute scaled error, mean absolute percentage error,
                     median absolute percentage error, median symmetric
                     accuracy
    bias - scale-dependent bias as measured by the mean error
    meanPercentageError - mean percentage error
    medianLogAccuracy - median of the log accuracy ratio
    symmetricSignedBias - Symmetric signed bias, as a percentage
    meanSquaredError - mean squared error
    RMSE - root mean squared error
    meanAbsError - mean absolute error
    medAbsError - median absolute error
    nRMSE - normaized root mean squared error
    scaledError - scaled error (see PyForecastTools for references)
    MASE - mean absolute scaled error
    forecastError - forecast error (see PyForecastTools for references)
    percError - percentage error
    absPercError - absolute percentage error
    logAccuracy - log accuracy ratio
    medSymAccuracy - Scaled measure of accuracy
    meanAPE - mean absolute percentage error

    """
    import verify  # PyForecastTools
    from pysat import utils

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatModelUtils instead:"
                            "https://github.com/pysat/pysatModelUtils"]),
                  DeprecationWarning, stacklevel=2)

    method_rout = {"bias": verify.bias, "accuracy": verify.accuracy,
                   "meanPercentageError": verify.meanPercentageError,
                   "medianLogAccuracy": verify.medianLogAccuracy,
                   "symmetricSignedBias": verify.symmetricSignedBias,
                   "meanSquaredError": verify.meanSquaredError,
                   "RMSE": verify.RMSE, "meanAbsError": verify.meanAbsError,
                   "medAbsError": verify.medAbsError, "MASE": verify.MASE,
                   "scaledAccuracy": verify.scaledAccuracy,
                   "nRMSE": verify.nRMSE, "scaledError": verify.scaledError,
                   "forecastError": verify.forecastError,
                   "percError": verify.percError, "meanAPE": verify.meanAPE,
                   "absPercError": verify.absPercError,
                   "logAccuracy": verify.logAccuracy,
                   "medSymAccuracy": verify.medSymAccuracy}

    replace_keys = {'MSE': 'meanSquaredError', 'MAE': 'meanAbsError',
                    'MdAE': 'medAbsError', 'MAPE': 'meanAPE',
                    'MdSymAcc': 'medSymAccuracy'}

    # Grouped methods for things that don't have convenience functions
    grouped_methods = {"all_bias": ["bias", "meanPercentageError",
                                    "medianLogAccuracy",
                                    "symmetricSignedBias"],
                       "all": list(method_rout.keys())}

    # Replace any group method keys with the grouped methods
    for gg in [(i, mm) for i, mm in enumerate(methods)
               if mm in list(grouped_methods.keys())]:
        # Extend the methods list to include all the grouped methods
        methods.extend(grouped_methods[gg[1]])
        # Remove the grouped method key
        methods.pop(gg[0])

    # Ensure there are no duplicate methods
    methods = list(set(methods))

    # Test the input
    if pairs is None:
        raise ValueError('must provide Dataset of paired observations')

    if len(inst_name) != len(mod_name):
        raise ValueError('must provide equal number of instrument and model ' +
                         'data names for comparison')

    if not np.all([iname in pairs.data_vars.keys() for iname in inst_name]):
        raise ValueError('unknown instrument data value supplied')

    if not np.all([iname in pairs.data_vars.keys() for iname in mod_name]):
        raise ValueError('unknown model data value supplied')

    if not np.all([mm in list(method_rout.keys()) for mm in methods]):
        known_methods = list(method_rout.keys())
        known_methods.extend(list(grouped_methods.keys()))
        unknown_methods = [mm for mm in methods
                           if mm not in list(method_rout.keys())]
        raise ValueError('unknown statistical method(s) requested:\n' +
                         '{:}\nuse only:\n{:}'.format(unknown_methods,
                                                      known_methods))

    # Initialize the output
    stat_dict = {iname: dict() for iname in inst_name}
    data_units = {iname: pairs.data_vars[iname].units for iname in inst_name}

    # Cycle through all of the data types
    for i, iname in enumerate(inst_name):
        # Determine whether the model data needs to be scaled
        iscale = utils.scale_units(pairs.data_vars[iname].units,
                                   pairs.data_vars[mod_name[i]].units)
        mod_scaled = pairs.data_vars[mod_name[i]].values.flatten() * iscale

        # Flatten both data sets, since accuracy routines require 1D arrays
        inst_dat = pairs.data_vars[iname].values.flatten()

        # Ensure no NaN are used in statistics
        inum = np.where(np.isfinite(mod_scaled) & np.isfinite(inst_dat))[0]


        if inum.shape[0] < 2:
            # Not all data types can use all statistics.  Print warnings
            # instead of stopping processing.  Only valid statistics
            # will be included in output
            logger.info("{:s} can't calculate stats for {:d} finite samples".format( \
                                                        iname, inum.shape[0]))
            stat_dict
        else:
            # Calculate all of the desired statistics
            for mm in methods:
                try:
                    stat_dict[iname][mm] = method_rout[mm](mod_scaled[inum],
                                                           inst_dat[inum])

                    # Convenience functions add layers to the output, remove
                    # these layers
                    if hasattr(stat_dict[iname][mm], "keys"):
                        for nn in stat_dict[iname][mm].keys():
                            new = replace_keys[nn] if nn in replace_keys.keys()\
                                else nn
                            stat_dict[iname][new] = stat_dict[iname][mm][nn]
                        del stat_dict[iname][mm]
                except ValueError as verr:
                    # Not all data types can use all statistics.  Print warnings
                    # instead of stopping processing.  Only valid statistics
                    # will be included in output
                    logger.warning("{:s} can't use {:s}: {:}".format(iname, mm, verr))
                except NotImplementedError:
                    # Not all data types can use all statistics.  Print warnings
                    # instead of stopping processing.  Only valid statistics
                    # will be included in output
                    logger.warning("{:s} can't implement {:s}".format(iname, mm))

    return stat_dict, data_units


def collect_inst_model_pairs(start=None, stop=None, tinc=None, inst=None,
                             user=None, password=None, model_files=None,
                             model_load_rout=None, inst_lon_name=None,
                             mod_lon_name=None, inst_name=[], mod_name=[],
                             mod_datetime_name=None, mod_time_name=None,
                             mod_units=[], sel_name=None, method='linear',
                             model_label='model', inst_clean_rout=None,
                             comp_clean='clean'):
    """Pair instrument and model data, applying data cleaning after finding the
    times and locations where the instrument and model align

    .. deprecated:: 2.2.0
      `collect_inst_model_pairs` will be removed in pysat 3.0.0, it will
      be added to pysatModels

    Parameters
    ----------
    start : dt.datetime
        Starting datetime
    stop : dt.datetime
        Ending datetime
    tinc : dt.timedelta
        Time incriment for model files
    inst : pysat.Instrument instance
        instrument object for which modelled data will be extracted
    user : string
        User name (needed for some data downloads)
    password : string
        Password (needed for some data downloads)
    model_files : string
        string format that will construct the desired model filename from a
        datetime object
    model_load_rout : routine
        Routine to load model data into an xarray using filename and datetime
        as input
    inst_lon_name : string
        variable name for instrument longitude
    mod_lon_name : string
        variable name for model longitude
    inst_name : list of strings
        list of names of the data series to use for determing instrument
        location
    mod_name : list of strings
        list of names of the data series to use for determing model locations
        in the same order as inst_name.  These must make up a regular grid.
    mod_datetime_name : string
        Name of the data series in the model Dataset containing datetime info
    mod_time_name : string
        Name of the time coordinate in the model Dataset
    mod_units : list of strings
        units for each of the mod_name location attributes.  Currently
        supports: rad/radian(s), deg/degree(s), h/hr(s)/hour(s), m, km, and cm
    sel_name : list of strings or NoneType
        list of names of modelled data indices to append to instrument object,
        or None to append all modelled data (default=None)
    method : string
        Interpolation method.  Supported are 'linear', 'nearest', and
        'splinef2d'.  The last is only supported for 2D data and is not
        recommended here.  (default='linear')
    model_label : string
        name of model, used to identify interpolated data values in instrument
        (default="model")
    inst_clean_rout : routine
        Routine to clean the instrument data
    comp_clean : string
        Clean level for the comparison data ('clean', 'dusty', 'dirty', 'none')
        (default='clean')

    Returns
    -------
    matched_inst : pysat.Instrument instance
        instrument object and paired modelled data

    """
    from os import path
    import pysat

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatModelUtils instead:"
                            "https://github.com/pysat/pysatModelUtils"]),
                  DeprecationWarning, stacklevel=2)

    matched_inst = None

    # Test the input
    if start is None or stop is None:
        raise ValueError('Must provide start and end time for comparison')

    if inst is None:
        raise ValueError('Must provide a pysat instrument object')

    if model_files is None:
        raise ValueError('Must provide list of modelled data')

    if model_load_rout is None:
        raise ValueError('Need routine to load modelled data')

    if mod_datetime_name is None:
        raise ValueError('Need time coordinate name for model datasets')

    if mod_time_name is None:
        raise ValueError('Need time coordinate name for model datasets')

    if len(inst_name) == 0:
        estr = 'Must provide instrument location attribute names as a list'
        raise ValueError(estr)

    if len(inst_name) != len(mod_name):
        estr = 'Must provide the same number of instrument and model '
        estr += 'location attribute names as a list'
        raise ValueError(estr)

    if len(mod_name) != len(mod_units):
        raise ValueError('Must provide units for each model location ' +
                         'attribute')

    if inst_clean_rout is None:
        raise ValueError('Need routine to clean the instrument data')

    # Download the instrument data, if needed
    # Could use some improvement, for not re-downloading times that you already
    # have
    if (stop - start).days != len(inst.files[start:stop]):
        inst.download(start=start, stop=stop, user=user, password=password)

    # Cycle through the times, loading the model and instrument data as needed
    istart = start
    while start < stop:
        mod_file = start.strftime(model_files)

        if path.isfile(mod_file):
            try:
                mdata = model_load_rout(mod_file, start)
                lon_high = float(mdata.coords[mod_lon_name].max())
                lon_low = float(mdata.coords[mod_lon_name].min())
            except Exception as err:
                print("unable to load {:s}: {:}".format(mod_file, err))
                mdata = None
        else:
            mdata = None

        if mdata is not None:
            # Load the instrument data, if needed
            if inst.empty or inst.index[-1] < istart:
                inst.custom.add(pysat.utils.coords.update_longitude, 'modify',
                                low=lon_low, lon_name=inst_lon_name,
                                high=lon_high)
                inst.load(date=istart)

            if not inst.empty and inst.index[0] >= istart:
                added_names = extract_modelled_observations(inst=inst, \
                                        model=mdata, \
                                        inst_name=inst_name, \
                                        mod_name=mod_name, \
                                        mod_datetime_name=mod_datetime_name, \
                                        mod_time_name=mod_time_name, \
                                        mod_units=mod_units, \
                                        sel_name=sel_name, \
                                        method=method, \
                                        model_label=model_label)

                if len(added_names) > 0:
                    # Clean the instrument data
                    inst.clean_level = comp_clean
                    inst_clean_rout(inst)

                    im = list()
                    for aname in added_names:
                        # Determine the number of good points
                        if inst.pandas_format:
                            imnew = np.where(np.isfinite(inst[aname]))
                        else:
                            imnew = np.where(np.isfinite(inst[aname].values))

                        # Some data types are higher dimensions than others,
                        # make sure we end up choosing a high dimension one
                        # so that we don't accidently throw away paired data
                        if len(im) == 0 or len(im[0]) < len(imnew[0]):
                            im = imnew

                    # If the data is 1D, save it as a list instead of a tuple
                    if len(im) == 1:
                        im = im[0]
                    else:
                        im = {kk: np.unique(im[i])
                              for i, kk in enumerate(inst.data.coords.keys())}

                    # Save the clean, matched data
                    if matched_inst is None:
                        matched_inst = pysat.Instrument
                        matched_inst.meta = inst.meta
                        matched_inst.data = inst[im]
                    else:
                        idata = inst[im]
                        matched_inst.data = \
                            inst.concat_data([matched_inst.data, idata])

                    # Reset the clean flag
                    inst.clean_level = 'none'

        # Cycle the times
        if tinc.total_seconds() <= 86400.0:
            start += tinc
            if start + tinc > istart + dt.timedelta(days=1):
                istart += dt.timedelta(days=1)
        else:
            if start + tinc >= istart + dt.timedelta(days=1):
                istart += dt.timedelta(days=1)
            if istart >= start + tinc:
                start += tinc

    # Recast as xarray and add units
    if matched_inst is not None:
        if inst.pandas_format:
            matched_inst.data = matched_inst.data.to_xarray()
        for im in inst.meta.data.units.keys():
            if im in matched_inst.data.data_vars.keys():
                matched_inst.data.data_vars[im].attrs['units'] = \
                    inst.meta.data.units[im]

    return matched_inst


def extract_modelled_observations(inst=None, model=None, inst_name=[],
                                  mod_name=[], mod_datetime_name=None,
                                  mod_time_name=None, mod_units=[],
                                  sel_name=None, method='linear',
                                  model_label='model'):
    """Extracts instrument-aligned data from a modelled data set

    .. deprecated:: 2.2.0
      `extract_modelled_observations` will be removed in pysat 3.0.0, it will
      be added to pysatModels

    Parameters
    ----------
    inst : pysat.Instrument instance
        instrument object for which modelled data will be extracted
    model : xarray Dataset
        modelled data set
    inst_name : list of strings
        list of names of the data series to use for determing instrument
        location
    mod_name : list of strings
        list of names of the data series to use for determing model locations
        in the same order as inst_name.  These must make up a regular grid.
    mod_datetime_name : string
        Name of the data series in the model Dataset containing datetime info
    mod_time_name : string
        Name of the time coordinate in the model Dataset
    mod_units : list of strings
        units for each of the mod_name location attributes.  Currently
        supports: rad/radian(s), deg/degree(s), h/hr(s)/hour(s), m, km, and cm
    sel_name : list of strings or NoneType
        list of names of modelled data indices to append to instrument object,
        or None to append all modelled data (default=None)
    method : string
        Interpolation method.  Supported are 'linear', 'nearest', and
        'splinef2d'.  The last is only supported for 2D data and is not
        recommended here.  (default='linear')
    model_label : string
        name of model, used to identify interpolated data values in instrument
        (default="model")

    Returns
    -------
    added_names : list of strings
        list of names of modelled data added to the instrument

    Notes
    --------
    For best results, select clean instrument data after alignment with model

    """
    from scipy import interpolate
    from pysat import utils

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatModelUtils instead:"
                            "https://github.com/pysat/pysatModelUtils"]),
                  DeprecationWarning, stacklevel=2)

    # Test input
    if inst is None:
        raise ValueError('Must provide a pysat instrument object')

    if model is None:
        raise ValueError('Must provide modelled data')

    if mod_datetime_name is None:
        raise ValueError('Need datetime key for model datasets')

    if mod_time_name is None:
        raise ValueError('Need time coordinate name for model datasets')

    if len(inst_name) == 0:
        estr = 'Must provide instrument location attribute names as a list'
        raise ValueError(estr)

    if len(inst_name) != len(mod_name):
        estr = 'Must provide the same number of instrument and model '
        estr += 'location attribute names as a list'
        raise ValueError(estr)

    if len(mod_name) != len(mod_units):
        raise ValueError('Must provide units for each model location ' +
                         'attribute')

    inst_scale = np.ones(shape=len(inst_name), dtype=float)
    for i, ii in enumerate(inst_name):
        if ii not in list(inst.data.keys()):
            raise ValueError('Unknown instrument location index ' +
                             '{:}'.format(ii))
        inst_scale[i] = utils.scale_units(mod_units[i],
                                          inst.meta.data.units[ii])

    # Determine which data to interpolate and initialize the interpolated
    # output
    if sel_name is None:
        sel_name = list(model.data_vars.keys())

    for mi in mod_name:
        if mi in sel_name:
            sel_name.pop(sel_name.index(mi))

    # Determine the model time resolution
    tm_sec = (np.array(model.data_vars[mod_datetime_name][1:]) -
              np.array(model.data_vars[mod_datetime_name][:-1])).min()
    tm_sec /= np.timedelta64(1, 's')
    ti_sec = (inst.index[1:] - inst.index[:-1]).min().total_seconds()
    min_del = tm_sec if tm_sec < ti_sec else ti_sec

    # Determine which instrument observations are within the model time
    # resolution of a model run
    mind = list()
    iind = list()
    for i, tt in enumerate(np.array(model.data_vars[mod_datetime_name])):
        del_sec = abs(tt - inst.index).total_seconds()
        if del_sec.min() <= min_del:
            iind.append(del_sec.argmin())
            mind.append(i)

    # Determine the model coordinates closest to the satellite track
    interp_data = dict()
    interp_shape = inst.index.shape if inst.pandas_format else \
        inst.data.data_vars.items()[0][1].shape
    inst_coord = {kk: getattr(inst.data, inst_name[i]).values * inst_scale[i]
                  for i, kk in enumerate(mod_name)}
    for i, ii in enumerate(iind):
        # Cycle through each model data type, since it may not depend on
        # all the dimensions
        for mdat in sel_name:
            # Determine the dimension values
            dims = list(model.data_vars[mdat].dims)
            ndim = model.data_vars[mdat].data.shape
            indices = {mod_time_name: mind[i]}

            # Construct the data needed for interpolation
            values = model[indices][mdat].data
            points = [model.coords[kk].data for kk in dims if kk in mod_name]
            get_coords = True if len(points) > 0 else False
            idims = 0

            while get_coords:
                if inst.pandas_format:
                    # This data iterates only by time
                    xout = ii
                    xi = [inst_coord[kk][ii] for kk in dims if kk in mod_name]
                    get_coords = False
                else:
                    # This data may have additional dimensions
                    if idims == 0:
                        # Determine the number of dimensions
                        idims = len(inst.data.coords)
                        idim_names = inst.data.coords.keys()[1:]

                        # Find relevent dimensions for cycling and slicing
                        ind_dims = [k for k, kk in enumerate(inst_name)
                                    if kk in idim_names]
                        imod_dims = [k for k in ind_dims
                                     if mod_name[k] in dims]
                        ind_dims = [inst.data.coords.keys().index(inst_name[k])
                                    for k in imod_dims]

                        # Set the number of cycles
                        icycles = 0
                        ncycles = sum([len(inst.data.coords[inst_name[k]])
                                       for k in imod_dims])
                        cinds = np.zeros(shape=len(imod_dims), dtype=int)

                    # Get the instrument coordinate for this cycle
                    if icycles < ncycles or icycles == 0:
                        ss = [ii if k == 0 else 0 for k in range(idims)]
                        se = [ii + 1 if k == 0 else
                              len(inst.data.coords[idim_names[k-1]])
                              for k in range(idims)]
                        xout = [cinds[ind_dims.index(k)] if k in ind_dims
                                else slice(ss[k], se[k]) for k in range(idims)]
                        xind = [cinds[ind_dims.index(k)] if k in ind_dims
                                else ss[k] for k in range(idims)]
                        xout = tuple(xout)
                        xind = tuple(xind)

                        xi = list()
                        for kk in dims:
                            if kk in mod_name:
                                # This is the next instrument coordinate
                                k = mod_name.index(kk)
                                if k in imod_dims:
                                    # This is an xarray coordiante
                                    xi.append(inst_coord[kk][cinds[k]])
                                else:
                                    # This is an xarray variable
                                    xi.append(inst_coord[kk][xind])

                        # Cycle the indices
                        if len(cinds) > 0:
                            k = 0
                            cinds[k] += 1

                            while cinds[k] > \
                                inst.data.coords.dims[inst_name[imod_dims[k]]]:
                                k += 1
                                if k < len(cinds):
                                    cinds[k-1] = 0
                                    cinds[k] += 1
                                else:
                                    break
                        icycles += 1

                    # If we have cycled through all the coordinates for this
                    # time, move onto the next time
                    if icycles >= ncycles:
                        get_coords = False

                # Interpolate the desired value
                try:
                    yi = interpolate.interpn(points, values, xi, method=method)
                except ValueError as verr:
                    if str(verr).find("requested xi is out of bounds") > 0:
                        # This is acceptable, pad the interpolated data with
                        # NaN
                        logger.warning("{:} for ".format(verr) +
                              "{:s} data at {:}".format(mdat, xi))
                        yi = [np.nan]
                    else:
                        raise ValueError(verr)

                # Save the output
                attr_name = "{:s}_{:s}".format(model_label, mdat)
                if attr_name not in interp_data.keys():
                    interp_data[attr_name] = np.full(shape=interp_shape,
                                                     fill_value=np.nan)
                interp_data[attr_name][xout] = yi[0]

    # Test and ensure the instrument data doesn't already have the interpolated
    # data.  This should not happen
    if np.any([mdat in inst.data.keys() for mdat in interp_data.keys()]):
        raise ValueError("instrument object already contains model data")

    # Update the instrument object and attach units to the metadata
    for mdat in interp_data.keys():
        attr_name = mdat.split("{:s}_".format(model_label))[-1]
        inst.meta[mdat] = {inst.units_label: model.data_vars[attr_name].units}

        if inst.pandas_format:
            inst[mdat] = pds.Series(interp_data[mdat], index=inst.index)
        else:
            inst.data = inst.data.assign(interp_key=(inst.data.coords.keys(),
                                                     interp_data[mdat]))
            inst.data.rename({"interp_key": mdat}, inplace=True)

    return interp_data.keys()
