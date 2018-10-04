from __future__ import print_function
from __future__ import absolute_import

import functools

import datetime as dt
import numpy as np
import pandas as pds

def compare_model_and_inst(pairs=None, inst_name=[], mod_name=[],
                           methods='all'):
    """Compare modelled and measured data

    Parameters
    ------------
    pairs : xarray.Dataset instance
        Dataset containing only the desired observation-model data pairs
    inst_name : list of strings
        ordered list of instrument measurements to compare to modelled data
    mod_name : list of strings
        ordered list of modelled data to compare to instrument measurements
    methods : list of strings
        statistics to calculate.  Accpeted are: 'mean_err', 'mean_abs_err',
        'median_err', 'median_abs_err', 'moments_err', 'moments_abs_err',
        'quartiles_err', 'quantiles_abs_err', 'deciles_err', 'deciles_abs_err',
        'percent_bias', 'mean_sq_err', or 'all' to calculate all.
        (default='all')

    Returns
    ----------
    stat_dict : dict of dicts
        Dictionary where the first layer of keys denotes the instrument data
        name and the second layer provides the desired statistics
    data_units : dict
        Dictionary containing the units for the data
    """
    from scipy import stats
    from pysat import utils

    known_methods = ['mean_err', 'mean_abs_err', 'median_err', 'median_abs_err',
                     'moments_err', 'moments_abs_err', 'quartiles_err',
                     'quartiles_abs_err', 'deciles_err', 'deciles_abs_err',
                     'percent_bias', 'mean_sq_err']

    if methods == 'all':
        methods = known_methods

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

    if not np.all([mm in known_methods for mm in methods]):
        raise ValueError('unknown statistical method requested, use only ' +
                         '{:}'.format(known_methods))
    
    # Calculate differences, if needed
    diff_data = dict()
    for i,iname in enumerate(inst_name):
        iscale = utils.scale_units(pairs.data_vars[iname].units,
                                   pairs.data_vars[mod_name[i]].units)
        diff_data[iname] = pairs.data_vars[mod_name[i]] * iscale - \
                pairs.data_vars[iname]

    # Initialize the output
    stat_dict = {iname:dict() for iname in inst_name}
    data_units = {iname:pairs.data_vars[iname].units for iname in inst_name}

    # Calculate the desired statistics
    if 'mean_err' in methods:
        for iname in inst_name:
            stat_dict[iname]['mean_err'] = diff_data[iname].mean()
    if 'mean_abs_err' in methods:
        for iname in inst_name:
            stat_dict[iname]['mean_abs_err'] = abs(diff_data[iname]).mean()
    if 'median_err' in methods:
        for iname in inst_name:
            stat_dict[iname]['median_err'] = diff_data[iname].median()
    if 'median_abs_err' in methods:
        for iname in inst_name:
            stat_dict[iname]['median_abs_err'] = abs(diff_data[iname]).median()
    if 'moments_err' in methods:
        for iname in inst_name:
            mmean = diff_data[iname].mean()
            mstd = diff_data[iname].std()
            mskew = stats.skew(diff_data[iname], nan_policy='omit')
            mkurt = stats.kurtosis(diff_data[iname], nan_policy='omit')
            stat_dict[iname]['moments_err'] = [mmean, mstd, mskew, mkurt]
    if 'moments_abs_err' in methods:
        for iname in inst_name:
            mmean = abs(diff_data[iname]).mean()
            mstd = abs(diff_data[iname]).std()
            mskew = stats.skew(abs(diff_data[iname]), nan_policy='omit')
            mkurt = stats.kurtosis(abs(diff_data[iname]), nan_policy='omit')
            stat_dict[iname]['moments_abs_err'] = [mmean, mstd, mskew, mkurt]
    if 'quartiles_err' in methods:
        for iname in inst_name:
            q1 = np.quantile(diff_data[iname][~np.isnan(diff_data[iname])],
                             0.25)
            q3 = np.quantile(diff_data[iname][~np.isnan(diff_data[iname])],
                             0.75)
            stat_dict[iname]['quartiles_err'] = [q1, q3]
    if 'quartiles_abs_err' in methods:
        for iname in inst_name:
            q1 = np.quantile(abs(diff_data[iname][~np.isnan(diff_data[iname])]),
                             0.25)
            q3 = np.quantile(abs(diff_data[iname][~np.isnan(diff_data[iname])]),
                             0.75)
            stat_dict[iname]['quartiles_abs_err'] = [q1, q3]
    if 'deciles_err' in methods:
        for iname in inst_name:
            q1 = np.quantile(diff_data[iname][~np.isnan(diff_data[iname])], 0.1)
            q3 = np.quantile(diff_data[iname][~np.isnan(diff_data[iname])], 0.9)
            stat_dict[iname]['deciles_err'] = [q1, q3]
    if 'deciles_abs_err' in methods:
        for iname in inst_name:
            q1 = np.quantile(abs(diff_data[iname][~np.isnan(diff_data[iname])]),
                             0.1)
            q3 = np.quantile(abs(diff_data[iname][~np.isnan(diff_data[iname])]),
                             0.9)
            stat_dict[iname]['deciles_abs_err'] = [q1, q3]
    if 'percent_bias' in methods:
        for iname in inst_name:
            stat_dict[iname]['percent_bias'] = (diff_data[iname].sum() /
                                                pairs.data_vars[iname].sum()) \
                                                * 100.0
    if 'mean_sq_err' in methods:
        for iname in inst_name:
            stat_dict[iname]['mean_sq_err'] = (diff_data[iname]**2).mean()
        
    return stat_dict, data_units


def collect_inst_model_pairs(start=None, stop=None, tinc=None, inst=None,
                             user=None, password=None, model_files=None,
                             model_load_rout=None, inst_lon_name=None,
                             mod_lon_name=None, inst_name=[], mod_name=[],
                             mod_datetime_name=None, mod_time_name=None,
                             mod_units=[], sel_name=None, method='linear',
                             model_label='model', inst_clean_rout=None,
                             comp_clean='clean'):
    """Extracts instrument-aligned data from a modelled data set

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
    from pysat import utils

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
        raise ValueError('Must provide units for each model location attribute')

    if inst_clean_rout is None:
        raise ValueError('Need routine to clean the instrument data')

    # Download the instrument data, if needed
    # Could use some improvement, for not re-downloading times that you already have
    if (stop-start).days != len(inst.files[start:stop]):
        inst.download(start=start, stop=stop, user=user, password=password)

    # Cycle through the times, loading the model and instrument data as needed
    istart = start
    while start < stop:
        mod_file = start.strftime(model_files)

        if path.isfile(mod_file):
            mdata = model_load_rout(mod_file, start)
            lon_high = float(mdata.coords[mod_lon_name].max())
            lon_low = float(mdata.coords[mod_lon_name].min())
        else:
            mdata = None

        if mdata is not None:
            # Load the instrument data, if needed
            if inst.empty or inst.data.index[-1] < istart:
                inst.custom.add(utils.update_longitude, 'modify', low=lon_low,
                                lon_name=inst_lon_name, high=lon_high)
                inst.load(date=istart)

            if not inst.empty and inst.data.index[0] >= istart:
                added_names = extract_modelled_observations(inst=inst, \
                                model=mdata, inst_name=inst_name,
                                                            mod_name=mod_name, \
                                mod_datetime_name=mod_datetime_name, \
                                mod_time_name=mod_time_name, \
                                mod_units=mod_units, sel_name=sel_name, \
                                method=method, model_label=model_label)

                if len(added_names) > 0:
                    # Clean the instrument data
                    inst.clean_level = comp_clean
                    inst_clean_rout(inst)

                    im = [i for i,t in enumerate(inst[added_names[0]])
                          if not np.isnan(t)]

                    # Save the clean, matched data
                    if matched_inst is None:
                        matched_inst = inst.data.iloc[im]
                        matched_inst.meta = inst.meta
                    else:
                        matched_inst = matched_inst.append(inst.data.iloc[im])

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
        matched_inst = matched_inst.to_xarray()
        for im in inst.meta.data.units.keys():
            if im in matched_inst.data_vars.keys():
                matched_inst.data_vars[im].attrs['units'] = \
                    inst.meta.data.units[im]

    return matched_inst


def extract_modelled_observations(inst=None, model=None, inst_name=[],
                                  mod_name=[], mod_datetime_name=None,
                                  mod_time_name=None, mod_units=[],
                                  sel_name=None, method='linear',
                                  model_label='model'):
    """Extracts instrument-aligned data from a modelled data set

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
        raise ValueError('Must provide units for each model location attribute')

    inst_scale = np.ones(shape=len(inst_name), dtype=float)
    for i,ii in enumerate(inst_name):
        if not ii in list(inst.data.keys()):
            raise ValueError('Unknown instrument location index {:}'.format(ii))
        inst_scale[i] = utils.scale_units(mod_units[i],
                                          inst.meta.data.units[ii])

    # Determine which data to interpolate and initialize the interpolated output
    if sel_name is None:
        sel_name = list(model.data_vars.keys())

    for mi in mod_name:
        if mi in sel_name:
            sel_name.pop(sel_name.index(mi))

    # Determine the model time resolution
    tm_sec = (np.array(model.data_vars[mod_datetime_name][1:]) -
              np.array(model.data_vars[mod_datetime_name][:-1])).min()
    tm_sec /= np.timedelta64(1, 's')
    ti_sec = (inst.data.index[1:] - inst.data.index[:-1]).min().total_seconds()
    min_del = tm_sec if tm_sec < ti_sec else ti_sec

    # Determine which instrument observations are within the model time
    # resolution of a model run
    mind = list()
    iind = list()
    for i,tt in enumerate(np.array(model.data_vars[mod_datetime_name])):
        del_sec = abs(tt - inst.data.index).total_seconds()
        if del_sec.min() < min_del:
            iind.append(del_sec.argmin())
            mind.append(i)

    # Determine the model coordinates closest to the satellite track
    interp_data = dict()
    inst_coord = {kk:getattr(inst.data, inst_name[i]) * inst_scale[i]
                  for i,kk in enumerate(mod_name)}
    for i,ii in enumerate(iind):
        # Cycle through each model data type, since it may not depend on
        # all the dimensions
        for mdat in sel_name:
            # Determine the dimension values
            dims = list(model.data_vars[mdat].dims)
            ndim = model.data_vars[mdat].data.shape
            indices = tuple([mind[i] if kk == mod_time_name
                             else slice(0,ndim[k]) for k,kk in enumerate(dims)])

            # Construct the data needed for interpolation
            points = [model.coords[kk].data for kk in dims if kk in mod_name]

            if len(points) > 0:
                xi = [inst_coord[kk][ii] for kk in dims if kk in mod_name]
                values = model.data_vars[mdat].data[indices]

                # Interpolate the desired value
                yi = interpolate.interpn(points, values, xi, method=method)

                # Save the output
                attr_name = "{:s}_{:s}".format(model_label, mdat)
                if not attr_name in interp_data.keys():
                    interp_data[attr_name] = \
                        np.empty(shape=inst.data.index.shape,
                                 dtype=float) * np.nan
                interp_data[attr_name][ii] = yi[0]

    # Update the instrument object and attach units to the metadata
    for mdat in interp_data.keys():
        inst[mdat] = pds.Series(interp_data[mdat], index=inst.data.index)

        attr_name = mdat.split("{:s}_".format(model_label))[-1]
        inst.meta.data.units[mdat] = model.data_vars[attr_name].units

    return interp_data.keys()
    

