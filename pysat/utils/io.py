#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Input/Output utilities for pysat data."""
import copy
import datetime as dt
import netCDF4
import numpy as np
import os
import pandas as pds
import warnings
import xarray as xr

import pysat


def pysat_meta_to_xarray_attr(xr_data, pysat_meta, epoch_name):
    """Attach pysat metadata to xarray Dataset as attributes.

    Parameters
    ----------
    xr_data : xarray.Dataset
        Xarray Dataset whose attributes will be updated.
    pysat_meta : dict
        Output starting from `Instrument.meta.to_dict()` supplying attribute
        data.
    epoch_name : str
        Label for datetime index information.

    """

    # Get a list of all data, expect for the time dimension.
    xarr_vars = xarray_vars_no_time(xr_data, epoch_name)

    # pysat meta -> dict export has lowercase names
    xarr_lvars = [var.lower() for var in xarr_vars]

    # Cycle through all the pysat MetaData measurements
    for data_key in pysat_meta.keys():

        # Information about epoch added to meta during to_netcdf
        if data_key != epoch_name:
            # Select the measurements that are also in the xarray data
            data_key = data_key.lower()
            if data_key in xarr_lvars:
                for i in range(len(xarr_lvars)):
                    if data_key == xarr_lvars[i]:
                        break

                # Cycle through all the pysat MetaData labels and transfer
                for meta_key in pysat_meta[data_key].keys():
                    # Assign attributes
                    xr_data[xarr_vars[i]].attrs[meta_key] = pysat_meta[
                        data_key][meta_key]

            else:
                wstr = ''.join(['Did not find data for metadata variable ',
                                data_key, '.'])
                warnings.warn(wstr)

    # Transfer metadata for the main time index. Cycle through all the pysat
    # MetaData labels and transfer.
    if epoch_name in pysat_meta.keys():
        for meta_key in pysat_meta[epoch_name].keys():
            # Assign attributes
            xr_data[epoch_name].attrs[meta_key] = pysat_meta[epoch_name][
                meta_key]

    return


def filter_netcdf4_metadata(inst, mdata_dict, coltype, remove=False,
                            check_type=None, export_nan=None, varname=''):
    """Filter metadata properties to be consistent with netCDF4.

    Parameters
    ----------
    inst : pysat.Instrument
        Object containing data and metadata
    mdata_dict : dict
        Dictionary equivalent to Meta object info
    coltype : type or dtype
        Data type provided by `pysat.Instrument._get_data_info`.  If boolean,
        int will be used instead.
    remove : bool
        Remove metadata that should be the same type as `coltype`, but isn't
        if True.  Recast data if False. (default=False)
    check_type : list or NoneType
        List of keys associated with `meta_dict` that should have the same
        data type as `coltype`.  These will be removed from the filtered
        output if they differ.  If None, this check will not be performed.
        (default=None)
    export_nan : list or NoneType
        Metadata parameters allowed to be NaN. If None, assumes no Metadata
        parameters are allowed to be Nan. (default=None)
    varname : str
        Variable name to be processed. Used for error feedback. (default='')

    Returns
    -------
    filtered_dict : dict
        Modified as needed for netCDf4

    Warnings
    --------
    UserWarning
        When data are removed due to conflict between value and type, and
        removal was not explicitly requested (`remove` is False).

    Note
    ----
    Metadata values that are NaN and not listed in export_nan are removed.

    """

    # Set the empty lists for NoneType inputs
    if check_type is None:
        check_type = []

    if export_nan is None:
        export_nan = []

    if coltype is bool:
        coltype = int
    elif isinstance(coltype, np.dtype):
        coltype = coltype.type

    # Remove any metadata with a value of NaN not present in `export_nan`
    filtered_dict = mdata_dict.copy()
    for key, value in mdata_dict.items():
        try:
            if np.isnan(value):
                if key not in export_nan:
                    filtered_dict.pop(key)
        except TypeError:
            # If a TypeError thrown, it's not NaN because it's not a float
            pass

    # Coerce boolean types to integers, remove NoneType, and test for
    # consisent data type
    remove_keys = list()
    for key in filtered_dict:
        # Cast the boolean data as integers
        if isinstance(filtered_dict[key], bool):
            filtered_dict[key] = int(filtered_dict[key])

        # Remove NoneType data and check for matching data types
        if filtered_dict[key] is None:
            remove_keys.append(key)
        elif key in check_type and not isinstance(filtered_dict[key], coltype):
            if remove:
                remove_keys.append(key)
            else:
                try:
                    filtered_dict[key] = coltype(filtered_dict[key])
                except (TypeError, ValueError):
                    warnings.warn(''.join(['Unable to cast ', key, ' data, ',
                                           repr(filtered_dict[key]), ', as ',
                                           repr(coltype), '; removing from ',
                                           'variable "', varname, '."']))
                    remove_keys.append(key)

    for key in remove_keys:
        del filtered_dict[key]

    return filtered_dict


def add_netcdf4_standards_to_metadict(inst, in_meta_dict, epoch_name,
                                      check_type=None, export_nan=None):
    """Add metadata variables needed to meet SPDF ISTP/IACG NetCDF standards.

    Parameters
    ----------
    inst : pysat.Instrument
        Object containing data and meta data
    in_meta_dict : dict
        Metadata dictionary, can be obtained from `inst.meta.to_dict()`.
    epoch_name : str
        Name for epoch or time-index variable.
    check_type : NoneType or list
        List of keys associated with `meta_dict` that should have the same
        data type as `coltype`. Passed to
        `pysat.utils.io.filter_netcdf4_metadata`. (default=None)
    export_nan : NoneType or list
        Metadata parameters allowed to be NaN. Passed along to
        `pysat.utils.io.filter_netcdf4_metadata`. (default=None)

    Returns
    -------
    in_meta_dict : dict
        Input dictionary with additional information for standards.

    See Also
    --------
    filter_netcdf4_metadata :
        Removes unsupported SPDF ISTP/IACG variable metadata.

    Note
    ----
    Removes unsupported SPDF ISTP/IACG variable metadata.

    For xarray inputs, converts datetimes to integers representing milliseconds
    since 1970. This does not include the main index, 'time'.

    """

    # Update the non-time variable meta data standards
    out_meta_dict = copy.deepcopy(in_meta_dict)
    for var in inst.vars_no_time:
        # Get the data variable information
        _, coltype, datetime_flag = inst._get_data_info(inst[var])

        # Update the standard metadata values
        meta_dict = {'Depend_0': epoch_name, 'Display_Type': 'Time Series',
                     'Var_Type': 'data'}

        lower_var = var.lower()

        # Update metadata based on data type.
        if datetime_flag:
            time_meta = return_epoch_metadata(inst, epoch_name)
            time_meta.pop('MonoTon')
            if inst.pandas_format:
                # Pandas file create will set long_name to 'Epoch'
                pass
            else:
                # Convert times to integers
                inst[var] = (inst[var].values.astype(np.int64)
                             * 1.0E-6).astype(np.int64)

            meta_dict.update(time_meta)

        if inst[var].dtype == np.dtype('O') and coltype != str:
            # This is a Series or DataFrame, possibly with more dimensions.
            # Series and DataFrame data must be treated differently.
            try:
                # Assume it is a DataFrame and get a list of subvariables
                subvars = inst[0, var].columns
                is_frame = True
            except AttributeError:
                # Data is Series of Series, which doesn't have columns.
                subvars = [inst[0, var].name]
                is_frame = False

            # Get the dimensions and their names
            dims = np.shape(inst[0, var])
            obj_dim_names = []
            if len(dims) == 1:
                # Pad the dimensions so that the rest of the code works
                # for either a Series or a DataFrame.
                dims = (dims[0], 0)

            for dim in dims[:-1]:
                # Don't need to go over last dimension value,
                # it covers number of columns (if a DataFrame).
                obj_dim_names.append(var)

            # Set the base-level meta data.
            meta_dict['Depend_1'] = obj_dim_names[-1]

            # Cycle through each of the sub-variable, updating metadata.
            for svar in subvars:
                # Find the subvariable data within the main variable,
                # checking that this is not an empty DataFrame or
                # Series. Determine the underlying data types.
                good_data_loc = 0
                for idat in np.arange(len(inst.data)):
                    if len(inst[idat, var]) > 0:
                        good_data_loc = idat
                        break

                # Get the correct location of the sub-variable based on
                # the object type.
                if is_frame:
                    good_data = inst[good_data_loc, var][svar]
                else:
                    good_data = inst[good_data_loc, var]

                # Get subvariable information
                _, sctype, sdflag = inst._get_data_info(good_data)

                if not sdflag:
                    # Not a datetime index
                    smeta_dict = {'Depend_0': epoch_name,
                                  'Depend_1': obj_dim_names[-1],
                                  'Display_Type': 'Multidimensional',
                                  'Format': inst._get_var_type_code(sctype),
                                  'Var_Type': 'data'}
                else:
                    # Attach datetime index metadata
                    smeta_dict = return_epoch_metadata(inst, epoch_name)
                    smeta_dict.pop('MonoTon')

                # Construct name, variable_subvariable, and store.
                sname = '_'.join([lower_var, svar.lower()])
                if sname in out_meta_dict:
                    out_meta_dict[sname].update(smeta_dict)
                else:
                    warnings.warn(''.join(['Unable to find MetaData for ',
                                           svar, ' subvariable of ', var]))
                    out_meta_dict[sname] = smeta_dict

                # Filter metadata
                remove = True if sctype == str else False
                out_meta_dict[sname] = filter_netcdf4_metadata(
                    inst, out_meta_dict[sname], sctype, remove=remove,
                    check_type=check_type, export_nan=export_nan, varname=sname)

            # Get information on the subvar index. This information
            # stored under primary variable name.
            sub_index = inst[good_data_loc, var].index
            _, coltype, datetime_flag = inst._get_data_info(sub_index)
            meta_dict['Format'] = inst._get_var_type_code(coltype)

            # Deal with index information for holding variable
            _, index_type, index_flag = inst._get_data_info(
                inst[good_data_loc, var].index)

            # Update metadata when a datetime index found
            if index_flag:
                update_dict = return_epoch_metadata(inst, epoch_name)
                update_dict.pop('MonoTon')
                update_dict.update(meta_dict)
            else:
                if inst[good_data_loc, var].index.name is not None:
                    name = inst[good_data_loc, var].index.name
                else:
                    name = var
                update_dict = {inst.meta.labels.name: name}
                update_dict.update(meta_dict)

            if lower_var in out_meta_dict:
                out_meta_dict[lower_var].update(update_dict)
            else:
                warnings.warn(''.join(['Unable to find MetaData for ',
                                       var]))
                out_meta_dict[lower_var] = update_dict

            # Filter metdata for other netCDF4 requirements
            remove = True if index_type == str else False
            out_meta_dict[lower_var] = filter_netcdf4_metadata(
                inst, out_meta_dict[lower_var], index_type, remove=remove,
                check_type=check_type, export_nan=export_nan, varname=lower_var)

        else:
            # Dealing with 1D data or xarray format
            meta_dict['Format'] = inst._get_var_type_code(coltype)

            if not inst.pandas_format:
                for i, dim in enumerate(list(inst[var].dims)):
                    meta_dict['Depend_{:1d}'.format(i)] = dim
                num_dims = len(inst[var].dims)
                if num_dims >= 2:
                    meta_dict['Display_Type'] = 'Multidimensional'

            # Update the meta data
            if lower_var in out_meta_dict:
                out_meta_dict[lower_var].update(meta_dict)
            else:
                warnings.warn(''.join(['Unable to find MetaData for ',
                                       var]))
                out_meta_dict[lower_var] = meta_dict

            # Filter metdata for other netCDF4 requirements
            remove = True if coltype == str else False
            out_meta_dict[lower_var] = filter_netcdf4_metadata(
                inst, out_meta_dict[lower_var], coltype, remove=remove,
                check_type=check_type, export_nan=export_nan, varname=lower_var)

    return out_meta_dict


def remove_netcdf4_standards_from_meta(mdict, epoch_name, labels):
    """Remove metadata from loaded file using SPDF ISTP/IACG NetCDF standards.

    Parameters
    ----------
    mdict : dict
        Contains all of the loaded file's metadata.
    epoch_name : str
        Name for epoch or time-index variable. Use '' if no epoch variable.
    labels : Meta.labels
        `Meta.labels` instance.

    Returns
    -------
    mdict : dict
        File metadata with unnecessary netCDF4 SPDF information removed.

    See Also
    --------
    add_netcdf4_standards_to_metadict : Adds SPDF ISTP/IACG netCDF4 metadata.

    Note
    ----
    Removes metadata for `epoch_name`. Also removes metadata such as 'Depend_*',
    'Display_Type', 'Var_Type', 'Format', 'Time_Scale', 'MonoTon',
    'calendar', and 'Time_Base'.

    """

    # Metadata added by `add_netcdf4_standards_to_metadict` or similar
    # method to maintain basic compliance with SPDF ISTP/IACG NetCDF standards.
    vals = ['Depend_0', 'Depend_1', 'Depend_2', 'Depend_3', 'Depend_4',
            'Depend_5', 'Depend_6', 'Depend_7', 'Depend_8', 'Depend_9',
            'Display_Type', 'Var_Type', 'Format',
            'MonoTon']
    lower_vals = [val.lower() for val in vals]
    time_vals = ['Time_Scale', 'calendar', 'Time_Base']
    lower_time_vals = [val.lower() for val in time_vals]

    for key in mdict.keys():
        lower_sub_keys = [ckey.lower() for ckey in mdict[key].keys()]
        sub_keys = list(mdict[key].keys())

        if 'meta' in lower_sub_keys:
            # Higher dimensional data, recursive treatment.
            mdict[key]['meta'] = remove_netcdf4_standards_from_meta(
                mdict[key]['meta'], '', labels)

        # Check for presence of time information
        for lval in lower_sub_keys:
            if lval in lower_time_vals:
                # Remove time related information, as well as units.
                for val in time_vals:
                    if val in mdict[key]:
                        mdict[key].pop(val)

                if labels.units in mdict[key]:
                    mdict[key][labels.units] = ''

                break

        # Remove any entries with label in `vals`
        for val, lval in zip(vals, lower_vals):
            if lval in lower_sub_keys:
                for i, check_val in enumerate(lower_sub_keys):
                    if check_val == lval:
                        mdict[key].pop(sub_keys[i])

    # Remove epoch metadata
    if epoch_name != '':
        if epoch_name in mdict:
            mdict.pop(epoch_name)

    return mdict


def default_from_netcdf_translation_table(meta):
    """Create metadata translation table with minimal netCDF requirements.

    Parameters
    ----------
    meta : pysat.Meta
        Meta instance to get appropriate default values for.

    Returns
    -------
    trans_table : dict
        Keyed by `self.labels` with a list of strings to be used
        when writing netcdf files.

    Note
    ----
    The purpose of this function is to maintain default compatibility
    with `meta.labels` and existing code that writes and reads netcdf
    files via pysat while also changing the labels for metadata within
    the file.

    """

    # Define a default translation with labels required by netCDF4.
    # We need to keep 'fill' for backwards compatibility. Unintended use
    # of 'fill' in pysat generated files in at least v3.0.1.
    trans_table = {'_FillValue': meta.labels.fill_val,
                   'FillVal': meta.labels.fill_val,
                   'fill': meta.labels.fill_val}

    return trans_table


def default_to_netcdf_translation_table(inst):
    """Create metadata translation table with minimal netCDF requirements.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object to be written to file.

    Returns
    -------
    trans_table : dict
        Keyed by `self.labels` with a list of strings to be used
        when writing netcdf files.

    """

    # Define a default translation, starting with pysat defaults.
    trans_table = {val: [val] for val in inst.meta.labels.label_attrs.keys()}

    # Update labels required by netCDF4
    trans_table['fill'] = ['_FillValue', 'FillVal', 'fill']

    return trans_table


def apply_table_translation_to_file(inst, meta_dict, trans_table=None):
    """Translate labels in `meta_dict` using `trans_table`.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object with data to be written to file.
    meta_dict : dict
        Output starting from `Instrument.meta.to_dict() `supplying attribute
        data.
    trans_table : dict or NoneType
        Keyed by current metalabels containing a list of
        metadata labels to use within the returned dict. If None,
        a default translation using `self.labels` will be used except
        `self.labels.fill_val` will be mapped to
        `['_FillValue', 'FillVal', 'fill']`.

    Returns
    -------
    export_dict : dict
        A dictionary of the metadata for each variable of an output file.

    """

    export_dict = {}

    if trans_table is None:
        trans_table = default_to_netcdf_translation_table(inst)

    # Confirm there are no duplicated translation labels
    trans_labels = [trans_table[key] for key in trans_table.keys()]
    for i in np.arange(len(trans_labels)):
        item = trans_labels.pop(0)
        if item in trans_labels:
            estr = ''.join(['There is a duplicated variable label value in ',
                            '`trans_table`: ', item])
            raise ValueError(estr)

    # Translate each metadata label if a translation is provided
    for key in meta_dict.keys():
        export_dict[key] = {}
        loop_meta_dict = meta_dict[key]
        for orig_key in loop_meta_dict:
            if orig_key in trans_table:
                for translated_key in trans_table[orig_key]:
                    export_dict[key][translated_key] = loop_meta_dict[orig_key]
            else:
                export_dict[key][orig_key] = loop_meta_dict[orig_key]

    return export_dict


def apply_table_translation_from_file(trans_table, meta_dict):
    """Modify `meta_dict` by applying `trans_table` to metadata keys.

    Parameters
    ----------
    trans_table : dict
       Mapping of metadata label used in a file to new value.
    meta_dict : dict
       Dictionary with metadata information from a loaded file.

    Returns
    -------
    filt_dict : dict
       `meta_dict` after the mapping in `trans_table` applied.

    Note
    ----
    The purpose of this function is to maintain default compatibility
    with `meta.labels` and existing code that writes and reads netcdf
    files via pysat while also changing the labels for metadata within
    the file.

    """

    filt_dict = {}
    for var_key in meta_dict:
        filt_dict[var_key] = {}

        # Iterate over metadata for given variable `var_key`
        for file_key in meta_dict[var_key].keys():
            # Apply translation if defined
            if file_key in trans_table:
                new_key = trans_table[file_key]
            else:
                new_key = file_key

            # Add to processed dict
            if new_key not in filt_dict[var_key]:
                filt_dict[var_key][new_key] = meta_dict[var_key][file_key]
            else:
                # `new_key` already present, ensure value consistent.
                if filt_dict[var_key][new_key] != meta_dict[var_key][file_key]:
                    try:
                        check1 = not np.isnan(filt_dict[var_key][new_key])
                        check2 = not np.isnan(meta_dict[var_key][file_key])
                        check = check1 and check2
                    except TypeError:
                        check = True

                    if check:
                        wstr = ''.join(['Inconsistent values between multiple ',
                                        'file parameters and single ',
                                        'translated metadata parameter "{}"',
                                        ' with values {} and {}.'])
                        wstr = wstr.format(new_key,
                                           meta_dict[var_key][file_key],
                                           filt_dict[var_key][new_key])
                        pysat.logger.warning(wstr)

        # Check translation table against available metadata
        for trans_key in trans_table.keys():
            if trans_key not in meta_dict[var_key].keys():
                wstr = 'Translation label "{}" not found for variable "{}".'
                pysat.logger.debug(wstr.format(trans_key, var_key))

        # Check for higher order metadata
        if 'meta' in meta_dict[var_key].keys():
            # Recursive call to process metadata
            ldict = meta_dict[var_key]['meta']
            filt_dict[var_key]['meta'] = \
                apply_table_translation_from_file(trans_table, ldict)

    return filt_dict


def meta_array_expander(meta_dict):
    """Expand meta arrays by storing each element with new incremented label.

    If `meta_dict[variable]['label'] = [ item1, item2, ..., itemn]` then
    the returned dict will contain: `meta_dict[variable]['label0'] = item1`,
    `meta_dict[variable]['label1'] = item2`, and so on up to
    `meta_dict[variable]['labeln-1'] = itemn`.

    Parameters
    ----------
    meta_dict : dict
        Keyed by variable name with a dict as a value. Each variable
        dict is keyed by metadata name and the value is the metadata.

    Returns
    -------
    meta_dict : dict
        Input dict with expanded array elements.

    Note
    ----
    pysat.Meta can not take array-like or list-like data.

    """

    meta_dict = copy.deepcopy(meta_dict)

    # Meta cannot take array data, if present save it as separate meta data
    # labels.
    for key in meta_dict.keys():
        loop_dict = {}
        for meta_key in meta_dict[key].keys():
            # Check for higher order data from 2D pandas support
            if meta_key == 'meta':
                loop_dict[meta_key] = meta_array_expander(
                    meta_dict[key][meta_key])
                continue

            tst_array = np.asarray(meta_dict[key][meta_key])
            if tst_array.shape == ():
                loop_dict[meta_key] = meta_dict[key][meta_key]
            elif tst_array.shape == (1, ):
                loop_dict[meta_key] = tst_array[0]
            else:
                for i, val in enumerate(tst_array):
                    nc_label = "{:}{:d}".format(meta_key, i)
                    loop_dict[nc_label] = val

        meta_dict[key] = loop_dict

    return meta_dict


def load_netcdf(fnames, strict_meta=False, file_format='NETCDF4',
                epoch_name=None, epoch_unit='ms', epoch_origin='unix',
                pandas_format=True, decode_timedelta=False,
                labels={'units': ('units', str), 'name': ('long_name', str),
                        'notes': ('notes', str), 'desc': ('desc', str),
                        'plot': ('plot_label', str), 'axis': ('axis', str),
                        'scale': ('scale', str),
                        'min_val': ('value_min', np.float64),
                        'max_val': ('value_max', np.float64),
                        'fill_val': ('fill', np.float64)},
                meta_processor=None, meta_translation=None,
                drop_meta_labels=None, decode_times=None):
    """Load netCDF-3/4 file produced by pysat.

    Parameters
    ----------
    fnames : str or array_like
        Filename(s) to load, will fail if None. (default=None)
    strict_meta : bool
        Flag that checks if metadata across `fnames` is the same if True
        (default=False)
    file_format : str
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        (default='NETCDF4')
    epoch_name : str or NoneType
        Data key for epoch variable.  The epoch variable is expected to be an
        array of integer or float values denoting time elapsed from an origin
        specified by `epoch_origin` with units specified by `epoch_unit`. This
        epoch variable will be converted to a `DatetimeIndex` for consistency
        across pysat instruments. If None, then `epoch_name` set by
        the `load_netcdf_pandas` or `load_netcdf_xarray` as appropriate.
        (default=None)
    epoch_unit : str
        The pandas-defined unit of the epoch variable ('D', 's', 'ms', 'us',
        'ns'). (default='ms')
    epoch_origin : str or timestamp-convertable
        Origin of epoch calculation, following convention for
        `pandas.to_datetime`.  Accepts timestamp-convertable objects, as well as
        two specific strings for commonly used calendars.  These conversions are
        handled by `pandas.to_datetime`.
        If ‘unix’ (or POSIX) time; origin is set to 1970-01-01.
        If ‘julian’, `epoch_unit` must be ‘D’, and origin is set to beginning of
        Julian Calendar. Julian day number 0 is assigned to the day starting at
        noon on January 1, 4713 BC. (default='unix')
    pandas_format : bool
        Flag specifying if data is stored in a pandas DataFrame (True) or
        xarray Dataset (False). (default=False)
    decode_timedelta : bool
        Used for xarray data (`pandas_format` is False).  If True, variables
        with unit attributes that  are 'timelike' ('hours', 'minutes', etc) are
        converted to `np.timedelta64`. (default=False)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})
    meta_processor : function or NoneType
        If not None, a dict containing all of the loaded metadata will be
        passed to `meta_processor` which should return a filtered version
        of the input dict. The returned dict is loaded into a pysat.Meta
        instance and returned as `meta`. (default=None)
    meta_translation : dict or NoneType
        Translation table used to map metadata labels in the file to
        those used by the returned `meta`. Keys are labels from file
        and values are labels in `meta`. Redundant file labels may be
        mapped to a single pysat label. If None, will use
        `default_from_netcdf_translation_table`. This feature
        is maintained for file compatibility. To disable all translation,
        input an empty dict. (default=None)
    drop_meta_labels : list or NoneType
        List of variable metadata labels that should be dropped. Applied
        to metadata as loaded from the file. (default=None)
    decode_times : bool or NoneType
        If True, variables with unit attributes that are 'timelike' ('hours',
        'minutes', etc) are converted to `np.timedelta64` by xarray. If False,
        then `epoch_name` will be converted to datetime using `epoch_unit`
        and `epoch_origin`. If None, will be set to False for backwards
        compatibility. For xarray only. (default=None)

    Returns
    -------
    data : pandas.DataFrame or xarray.Dataset
        Class holding file data
    meta : pysat.Meta
        Class holding file meta data

    Raises
    ------
    KeyError
        If epoch/time dimension could not be identified.
    ValueError
        When attempting to load data with more than 2 dimensions or if
        `strict_meta` is True and meta data changes across files.

    See Also
    --------
    load_netcdf_pandas, load_netcdf_xarray, pandas.to_datetime

    """
    # Load data by type
    if pandas_format:
        if decode_times is not None:
            estr = ''.join(['`decode_times` not supported for pandas.'])
            raise ValueError(estr)

        data, meta = load_netcdf_pandas(fnames, strict_meta=strict_meta,
                                        file_format=file_format,
                                        epoch_name=epoch_name,
                                        epoch_unit=epoch_unit,
                                        epoch_origin=epoch_origin,
                                        labels=labels,
                                        meta_processor=meta_processor,
                                        meta_translation=meta_translation,
                                        drop_meta_labels=drop_meta_labels)
    else:
        data, meta = load_netcdf_xarray(fnames, strict_meta=strict_meta,
                                        file_format=file_format,
                                        epoch_name=epoch_name,
                                        epoch_unit=epoch_unit,
                                        epoch_origin=epoch_origin,
                                        decode_timedelta=decode_timedelta,
                                        labels=labels,
                                        meta_processor=meta_processor,
                                        meta_translation=meta_translation,
                                        drop_meta_labels=drop_meta_labels,
                                        decode_times=decode_times)

    return data, meta


def load_netcdf_pandas(fnames, strict_meta=False, file_format='NETCDF4',
                       epoch_name='Epoch', epoch_unit='ms', epoch_origin='unix',
                       labels={'units': ('units', str),
                               'name': ('long_name', str),
                               'notes': ('notes', str), 'desc': ('desc', str),
                               'plot': ('plot_label', str),
                               'axis': ('axis', str), 'scale': ('scale', str),
                               'min_val': ('value_min', np.float64),
                               'max_val': ('value_max', np.float64),
                               'fill_val': ('fill', np.float64)},
                       meta_processor=None, meta_translation=None,
                       drop_meta_labels=None):
    """Load netCDF-3/4 file produced by pysat in a pandas format.

    Parameters
    ----------
    fnames : str or array_like
        Filename(s) to load
    strict_meta : bool
        Flag that checks if metadata across `fnames` is the same if True
        (default=False)
    file_format : str
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        (default='NETCDF4')
    epoch_name : str or NoneType
        Data key for epoch variable.  The epoch variable is expected to be an
        array of integer or float values denoting time elapsed from an origin
        specified by `epoch_origin` with units specified by `epoch_unit`. This
        epoch variable will be converted to a `DatetimeIndex` for consistency
        across pysat instruments.  (default='Epoch')
    epoch_unit : str
        The pandas-defined unit of the epoch variable ('D', 's', 'ms', 'us',
        'ns'). (default='ms')
    epoch_origin : str or timestamp-convertable
        Origin of epoch calculation, following convention for
        `pandas.to_datetime`.  Accepts timestamp-convertable objects, as well as
        two specific strings for commonly used calendars.  These conversions are
        handled by `pandas.to_datetime`.
        If ‘unix’ (or POSIX) time; origin is set to 1970-01-01.
        If ‘julian’, `epoch_unit` must be ‘D’, and origin is set to beginning of
        Julian Calendar. Julian day number 0 is assigned to the day starting at
        noon on January 1, 4713 BC. (default='unix')
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})
    meta_processor : function or NoneType
        If not None, a dict containing all of the loaded metadata will be
        passed to `meta_processor` which should return a filtered version
        of the input dict. The returned dict is loaded into a pysat.Meta
        instance and returned as `meta`. (default=None)
    meta_translation : dict or NoneType
        Translation table used to map metadata labels in the file to
        those used by the returned `meta`. Keys are labels from file
        and values are labels in `meta`. Redundant file labels may be
        mapped to a single pysat label. If None, will use
        `default_from_netcdf_translation_table`. This feature
        is maintained for file compatibility. To disable all translation,
        input an empty dict. (default=None)
    drop_meta_labels : list or NoneType
        List of variable metadata labels that should be dropped. Applied
        to metadata as loaded from the file. (default=None)

    Returns
    -------
    data : pandas.DataFrame
        Class holding file data
    meta : pysat.Meta
        Class holding file meta data

    Raises
    ------
    KeyError
        If epoch/time dimension could not be identified.
    ValueError
        When attempting to load data with more than 2 dimensions, or if
        `strict_meta` is True and meta data changes across files, or if
        epoch/time dimension could not be identified.

    See Also
    --------
    load_netcdf

    """

    if epoch_name is None:
        dstr = ''.join(['Assigning "Epoch" for time index. In the future, '
                        'this will be updated to "time." Set a value ',
                        'for `epoch_name` to silence this warning.'])
        warnings.warn(dstr, DeprecationWarning, stacklevel=2)
        epoch_name = 'Epoch'

    # Ensure inputs are in the correct format
    fnames = pysat.utils.listify(fnames)
    file_format = file_format.upper()

    # Initialize local variables
    saved_meta = None
    running_idx = 0
    running_store = []
    two_d_keys = []
    two_d_dims = []
    meta = pysat.Meta(labels=labels)

    # Store all metadata in a dict that may be filtered before
    # assignment to `meta`.
    full_mdict = {}

    if meta_translation is None:
        # Assign default translation using `meta`
        meta_translation = default_from_netcdf_translation_table(meta)

    # Drop metadata labels initialization
    if drop_meta_labels is None:
        drop_meta_labels = []
    else:
        drop_meta_labels = pysat.utils.listify(drop_meta_labels)

    # Need to use name label later to identify variables with long_name 'Epoch'
    name_label = meta.labels.name
    for key in meta_translation.keys():
        if meta.labels.name in meta_translation[key]:
            name_label = key

    # Load data for each file
    for fname in fnames:
        with netCDF4.Dataset(fname, mode='r', format=file_format) as data:
            # Build a dictionary with all global ncattrs and add those
            # attributes to a pysat.MetaHeader object.
            for ncattr in data.ncattrs():
                setattr(meta.header, ncattr, data.getncattr(ncattr))

            # Load the metadata.  From here group unique dimensions and
            # act accordingly, 1D, 2D, 3D.
            loaded_vars = {}
            for key in data.variables.keys():
                if len(data.variables[key].dimensions) == 1:
                    # Load 1D data variables, assuming time is the dimension.
                    loaded_vars[key] = data.variables[key][:]

                    # Load up metadata
                    meta_dict = {}
                    for nc_key in data.variables[key].ncattrs():
                        meta_dict[nc_key] = data.variables[key].getncattr(
                            nc_key)
                    full_mdict[key] = meta_dict

                # TODO(#913): Remove 2D support
                if len(data.variables[key].dimensions) == 2:
                    # Part of a DataFrame to store within the main DataFrame
                    two_d_keys.append(key)
                    two_d_dims.append(data.variables[key].dimensions)

                if len(data.variables[key].dimensions) >= 3:
                    raise ValueError(' '.join(('pysat only supports 1D and 2D',
                                               'data in pandas. Please use',
                                               'xarray for this file.')))

            # TODO(#913): Remove 2D support
            # We now have a list of keys that need to go into a dataframe,
            # could be more than one, collect unique dimensions for 2D keys.
            for dim in set(two_d_dims):
                # First or second dimension could be epoch. Use other
                # dimension name as variable name.
                if dim[0] == epoch_name:
                    obj_key = dim[1]
                elif dim[1] == epoch_name:
                    obj_key = dim[0]
                else:
                    estr = ''.join(['Epoch label: "', epoch_name, '"',
                                    ' was not found in loaded dimensions [',
                                    ', '.join(dim), ']'])
                    raise KeyError(estr)

                # Collect variable names associated with dimension
                idx_bool = [dim == i for i in two_d_dims]
                idx, = np.where(np.array(idx_bool))
                obj_var_keys = []
                clean_var_keys = []
                for i in idx:
                    obj_var_keys.append(two_d_keys[i])
                    clean_var_keys.append(
                        two_d_keys[i].split(obj_key + '_')[-1])

                # Figure out how to index this data, it could provide its
                # own index - or we may have to create simple integer based
                # DataFrame access. If the dimension is stored as its own
                # variable then use that info for index.
                if obj_key in obj_var_keys:
                    # String used to indentify dimension also in
                    # data.variables will be used as an index.
                    index_key_name = obj_key

                    # If the object index uses UNIX time, process into
                    # datetime index.
                    if data.variables[obj_key].getncattr(
                            name_label) == epoch_name:
                        # Found the name to be used in DataFrame index
                        index_name = epoch_name
                        time_index_flag = True
                    else:
                        time_index_flag = False

                        # Label to be used in DataFrame index
                        index_name = data.variables[obj_key].getncattr(
                            name_label)
                else:
                    # Dimension is not itself a variable
                    index_key_name = None

                # Iterate over the variables and grab metadata
                dim_meta_data = {}

                # Store attributes in metadata, except for the dimension name.
                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    meta_dict = {}
                    for nc_key in data.variables[key].ncattrs():
                        meta_dict[nc_key] = data.variables[key].getncattr(
                            nc_key)

                    dim_meta_data[clean_key] = meta_dict

                dim_meta_dict = {'meta': dim_meta_data}

                # Add top level meta
                if index_key_name is not None:
                    for nc_key in data.variables[obj_key].ncattrs():
                        dim_meta_dict[nc_key] = data.variables[
                            obj_key].getncattr(nc_key)
                    full_mdict[obj_key] = dim_meta_dict

                # Iterate over all variables with this dimension
                # data storage, whole shebang.
                loop_dict = {}

                # List holds a series of slices, parsed from dict above.
                loop_list = []
                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    loop_dict[clean_key] = data.variables[
                        key][:, :].flatten(order='C')

                # Find the number of time values
                loop_lim = data.variables[obj_var_keys[0]].shape[0]

                # Find the number of values per time
                step = len(data.variables[obj_var_keys[0]][0, :])

                # Check if there is an index we should use
                if not (index_key_name is None):
                    time_var = loop_dict.pop(index_key_name)
                    if time_index_flag:
                        # Create datetime index from data
                        time_var = pds.to_datetime(time_var, unit=epoch_unit,
                                                   origin=epoch_origin)
                    new_index = time_var
                    new_index_name = index_name
                else:
                    # Using integer indexing if no index identified
                    new_index = np.arange((loop_lim * step),
                                          dtype=np.int64) % step
                    new_index_name = 'index'

                # Load all data into frame
                if len(loop_dict.keys()) > 1:
                    loop_frame = pds.DataFrame(loop_dict,
                                               columns=clean_var_keys)
                    if obj_key in loop_frame:
                        del loop_frame[obj_key]

                    # Break massive frame into bunch of smaller frames
                    for i in np.arange(loop_lim, dtype=np.int64):
                        loop_list.append(loop_frame.iloc[(step * i):
                                                         (step * (i + 1)), :])
                        loop_list[-1].index = new_index[(step * i):
                                                        (step * (i + 1))]
                        loop_list[-1].index.name = new_index_name
                else:
                    loop_frame = pds.Series(loop_dict[clean_var_keys[0]],
                                            name=obj_var_keys[0])

                    # Break massive series into bunch of smaller series
                    for i in np.arange(loop_lim, dtype=np.int64):
                        loop_list.append(loop_frame.iloc[(step * i):
                                                         (step * (i + 1))])
                        loop_list[-1].index = new_index[(step * i):
                                                        (step * (i + 1))]
                        loop_list[-1].index.name = new_index_name

                # Add 2D object data, all based on a unique dimension within
                # netCDF, to loaded data dictionary.
                loaded_vars[obj_key] = loop_list
                del loop_list

            # Prepare dataframe index for this netcdf file
            if epoch_name not in loaded_vars.keys():
                estr = ''.join(['Epoch label: "', epoch_name, '"',
                                ' was not found in loaded dimensions [',
                                ', '.join(loaded_vars.keys()), ']'])
                raise KeyError(estr)

            time_var = loaded_vars.pop(epoch_name)
            loaded_vars[epoch_name] = pds.to_datetime(time_var, unit=epoch_unit,
                                                      origin=epoch_origin)
            running_store.append(loaded_vars)
            running_idx += len(loaded_vars[epoch_name])

            if strict_meta:
                if saved_meta is None:
                    saved_meta = full_mdict.copy()
                elif full_mdict != saved_meta:
                    raise ValueError(' '.join(('Metadata across filenames',
                                               'is not the same.')))

    # Combine all of the data loaded across files together
    out = []
    for item in running_store:
        out.append(pds.DataFrame.from_records(item, index=epoch_name))
    data = pds.concat(out, axis=0)

    # Process the metadata. First, drop labels as requested.
    for var in full_mdict:
        for label in drop_meta_labels:
            if label in full_mdict[var]:
                full_mdict[var].pop(label)
            if 'meta' in full_mdict[var]:
                for var2 in full_mdict[var]['meta'].keys():
                    if label in full_mdict[var]['meta'][var2]:
                        full_mdict[var]['meta'][var2].pop(label)

    # Second, remove some items pysat added for netcdf compatibility.
    filt_mdict = remove_netcdf4_standards_from_meta(full_mdict, epoch_name,
                                                    meta.labels)
    # Translate labels from file to pysat compatible labels using
    # `meta_translation`.
    filt_mdict = apply_table_translation_from_file(meta_translation, filt_mdict)

    # Next, allow processing by developers so they can deal with
    # issues with specific files.
    if meta_processor is not None:
        filt_mdict = meta_processor(filt_mdict)

    # Meta cannot take array data, if present save it as seperate meta data
    # labels.
    filt_mdict = meta_array_expander(filt_mdict)

    # Assign filtered metadata to pysat.Meta instance
    for key in filt_mdict:
        if 'meta' in filt_mdict[key].keys():
            # Higher order metadata
            dim_meta = pysat.Meta(labels=labels)
            for skey in filt_mdict[key]['meta'].keys():
                dim_meta[skey] = filt_mdict[key]['meta'][skey]

            # Remove HO metdata that was just transfered elsewhere
            filt_mdict[key].pop('meta')

            # Assign standard metdata
            meta[key] = filt_mdict[key]

            # Assign HO metadata
            meta[key] = {'meta': dim_meta}
        else:
            # Standard metadata
            meta[key] = filt_mdict[key]

    return data, meta


def load_netcdf_xarray(fnames, strict_meta=False, file_format='NETCDF4',
                       epoch_name='time', epoch_unit='ms', epoch_origin='unix',
                       decode_timedelta=False,
                       labels={'units': ('units', str),
                               'name': ('long_name', str),
                               'notes': ('notes', str), 'desc': ('desc', str),
                               'plot': ('plot_label', str),
                               'axis': ('axis', str),
                               'scale': ('scale', str),
                               'min_val': ('value_min', np.float64),
                               'max_val': ('value_max', np.float64),
                               'fill_val': ('fill', np.float64)},
                       meta_processor=None, meta_translation=None,
                       drop_meta_labels=None, decode_times=False):
    """Load netCDF-3/4 file produced by pysat into an xarray Dataset.

    Parameters
    ----------
    fnames : str or array_like
        Filename(s) to load.
    strict_meta : bool
        Flag that checks if metadata across `fnames` is the same if True.
        (default=False)
    file_format : str or NoneType
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        (default='NETCDF4')
    epoch_name : str or NoneType
        Data key for epoch variable.  The epoch variable is expected to be an
        array of integer or float values denoting time elapsed from an origin
        specified by `epoch_origin` with units specified by `epoch_unit`. This
        epoch variable will be converted to a `DatetimeIndex` for consistency
        across pysat instruments.  (default='time')
    epoch_unit : str
        The pandas-defined unit of the epoch variable ('D', 's', 'ms', 'us',
        'ns'). (default='ms')
    epoch_origin : str or timestamp-convertable
        Origin of epoch calculation, following convention for
        `pandas.to_datetime`.  Accepts timestamp-convertable objects, as well as
        two specific strings for commonly used calendars.  These conversions are
        handled by `pandas.to_datetime`.
        If ‘unix’ (or POSIX) time; origin is set to 1970-01-01.
        If ‘julian’, `epoch_unit` must be ‘D’, and origin is set to beginning of
        Julian Calendar. Julian day number 0 is assigned to the day starting at
        noon on January 1, 4713 BC. (default='unix')
    decode_timedelta : bool
        If True, variables with unit attributes that are 'timelike' ('hours',
        'minutes', etc) are converted to `np.timedelta64`. (default=False)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})
    meta_processor : function or NoneType
        If not None, a dict containing all of the loaded metadata will be
        passed to `meta_processor` which should return a filtered version
        of the input dict. The returned dict is loaded into a pysat.Meta
        instance and returned as `meta`. (default=None)
    meta_translation : dict or NoneType
        Translation table used to map metadata labels in the file to
        those used by the returned `meta`. Keys are labels from file
        and values are labels in `meta`. Redundant file labels may be
        mapped to a single pysat label. If None, will use
        `default_from_netcdf_translation_table`. This feature
        is maintained for compatibility. To disable all translation,
        input an empty dict. (default=None)
    drop_meta_labels : list or NoneType
        List of variable metadata labels that should be dropped. Applied
        to metadata as loaded from the file. (default=None)
    decode_times : bool or NoneType
        If True, variables with unit attributes that are 'timelike' ('hours',
        'minutes', etc) are converted to `np.timedelta64` by xarray. If False,
        then `epoch_name` will be converted to datetime using `epoch_unit`
        and `epoch_origin`. If None, will be set to False for backwards
        compatibility. (default=None)

    Returns
    -------
    data : xarray.Dataset
        Class holding file data
    meta : pysat.Meta
        Class holding file meta data

    See Also
    --------
    load_netcdf

    """

    if decode_times is None:
        dstr = ''.join(['Defaulting to `decode_times=False`. In the future ',
                        'the default will be updated to `True`. Set a value ',
                        'for `decode_times` to silence this warning.'])
        warnings.warn(dstr, DeprecationWarning, stacklevel=2)
        decode_times = False

    if epoch_name is None:
        epoch_name = 'time'

    # Ensure inputs are in the correct format
    fnames = pysat.utils.listify(fnames)
    file_format = file_format.upper()

    # Initialize local variables
    meta = pysat.Meta(labels=labels)

    # Store all metadata in a dict that may be filtered before
    # assignment to `meta`.
    full_mdict = {}

    if meta_translation is None:
        # Assign default translation using `meta`
        meta_translation = default_from_netcdf_translation_table(meta)

    # Drop metadata labels initialization
    if drop_meta_labels is None:
        drop_meta_labels = []
    else:
        drop_meta_labels = pysat.utils.listify(drop_meta_labels)

    # Load the data differently for single or multiple files
    if len(fnames) == 1:
        data = xr.open_dataset(fnames[0], decode_timedelta=decode_timedelta,
                               decode_times=decode_times)
    else:
        data = xr.open_mfdataset(fnames, decode_timedelta=decode_timedelta,
                                 combine='by_coords', decode_times=decode_times)

    # Need to get a list of all variables, dimensions, and coordinates.
    all_vars = xarray_all_vars(data)

    # Rename `epoch_name` to 'time'
    if epoch_name != 'time':
        if 'time' not in all_vars:
            if epoch_name in data.dims:
                data = data.rename({epoch_name: 'time'})
            elif epoch_name in all_vars:
                data = data.rename({epoch_name: 'time'})
                wstr = ''.join(['Epoch label: "', epoch_name, '"',
                                ' is not a dimension.'])
                pysat.logger.warning(wstr)
            else:
                estr = ''.join(['Epoch label: "', epoch_name, '"',
                                ' was not found in loaded dimensions [',
                                ', '.join(all_vars), ']'])
                raise KeyError(estr)
        else:
            estr = ''.join(["'time' already present in file. Can't rename ",
                            epoch_name, " to 'time'. To load this file ",
                            "it may be necessary to set `decode_times=True`."])
            raise ValueError(estr)

    # Convert 'time' to datetime objects, depending upon settings.
    # If decode_times False, apply our own calculation. If True,
    # datetime objects were created by xarray.
    if not decode_times:
        edates = pds.to_datetime(data['time'].values, unit=epoch_unit,
                                 origin=epoch_origin)
        data['time'] = xr.DataArray(edates, coords=data['time'].coords)

    # Need to get a list of all variables, dimensions, and coordinates.
    # Variables could have been altered since last call.
    all_vars = xarray_all_vars(data)

    # Copy the variable attributes from the data object to the metadata
    for key in all_vars:
        meta_dict = {}
        for nc_key in data[key].attrs.keys():
            meta_dict[nc_key] = data[key].attrs[nc_key]

        full_mdict[key] = meta_dict

        # Remove variable attributes from the data object
        data[key].attrs = {}

    # Copy the file attributes from the data object to the metadata
    for data_attr in data.attrs.keys():
        setattr(meta.header, data_attr, getattr(data, data_attr))

    # Process the metadata. First, drop labels as requested.
    for var in full_mdict:
        for label in drop_meta_labels:
            if label in full_mdict[var]:
                full_mdict[var].pop(label)

    # Second, remove some items pysat added for netcdf compatibility.
    filt_mdict = remove_netcdf4_standards_from_meta(full_mdict, epoch_name,
                                                    meta.labels)

    # Translate labels from file to pysat compatible labels using
    # `meta_translation`.
    filt_mdict = apply_table_translation_from_file(meta_translation, filt_mdict)

    # Next, allow processing by developers so they can deal with
    # issues with specific files.
    if meta_processor is not None:
        filt_mdict = meta_processor(filt_mdict)

    # Meta cannot take array data, if present save it as seperate meta data
    # labels.
    filt_mdict = meta_array_expander(filt_mdict)

    # Assign filtered metadata to pysat.Meta instance
    for key in filt_mdict:
        meta[key] = filt_mdict[key]

    # Remove attributes from the data object
    data.attrs = {}

    # Close any open links to file through xarray
    data.close()

    return data, meta


def return_epoch_metadata(inst, epoch_name):
    """Create epoch or time-index metadata.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object with data and metadata.
    epoch_name : str
        Data key for time-index or epoch data.

    Returns
    -------
    meta_dict : dict
        Dictionary with epoch metadata, keyed by
        metadata label.

    """
    # Get existing meta data
    if epoch_name in inst.meta:
        new_dict = inst.meta[inst.meta.var_case_name(epoch_name)].to_dict()
    else:
        new_dict = {}

    # Update basic labels, if they are missing.
    epoch_label = 'Milliseconds since 1970-1-1 00:00:00'
    basic_labels = [inst.meta.labels.units]

    for label in basic_labels:
        if label not in new_dict or len(new_dict[label]) == 0:
            new_dict[label] = epoch_label

    # Assign name
    new_dict[inst.meta.labels.name] = epoch_name

    # Update the time standards
    time_dict = {'calendar': 'standard', 'Format': 'i8', 'Var_Type': 'data',
                 'Time_Base': epoch_label, 'Time_Scale': 'UTC'}

    if inst.index.is_monotonic_increasing:
        time_dict['MonoTon'] = 'increase'
    elif inst.index.is_monotonic_decreasing:
        time_dict['MonoTon'] = 'decrease'

    new_dict.update(time_dict)

    return new_dict


def xarray_vars_no_time(data, time_label='time'):
    """Extract all DataSet variables except `time_label` dimension.

    Parameters
    ----------
    data : xarray.Dataset
        Dataset to get variables from.
    time_label : str
        Label used within `data` for time information.

    Returns
    -------
    vars : list
        All variables, dimensions, and coordinates, except for `time_label`.

    Raises
    ------
    ValueError
        If `time_label` not present in `data`.

    """
    vars = list(data.variables.keys())

    # Remove `time_label` dimension
    if time_label in vars:
        for i, var in enumerate(vars):
            if var == time_label:
                vars.pop(i)
                break
    else:
        estr = ''.join(["Didn't find time dimension '", time_label, "'"])
        raise ValueError(estr)

    return vars


def xarray_all_vars(data):
    """Extract all variable names, including dimensions and coordinates.

    Parameters
    ----------
    data : xarray.Dataset
        Dataset to get all variables from.

    Returns
    -------
    all_vars : list
        List of all `data.data_vars`, `data.dims`, and `data.coords`.

    """

    # Construct a list of all variables, dimensions, and coordinates.
    # Start by obtaining the dimensions.
    all_vars = list(data.dims)

    # Add coordinate information
    coords = list(data.coords)
    for coord in coords:
        if coord not in all_vars:
            all_vars.append(coord)

    # Add variable information
    vars = list(data.data_vars.keys())
    for var in vars:
        if var not in all_vars:
            all_vars.append(var)

    return all_vars


def inst_to_netcdf(inst, fname, base_instrument=None, epoch_name=None,
                   mode='w', zlib=False, complevel=4, shuffle=True,
                   preserve_meta_case=False, check_type=None, export_nan=None,
                   unlimited_time=True, meta_translation=None,
                   meta_processor=None):
    """Store pysat data in a netCDF4 file.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object with loaded data to save
    fname : str
        Output filename with full path
    base_instrument : pysat.Instrument or NoneType
        Class used as a comparison, only attributes that are present with
        `inst` and not on `base_instrument` are written to netCDF. Using None
        assigns an unmodified pysat.Instrument object. (default=None)
    epoch_name : str or NoneType
        Label in file for datetime index of `inst`. If None, uses
        'Epoch' for pandas data formats, and uses 'time' for xarray formats.
    mode : str
        Write (‘w’) or append (‘a’) mode. If mode=’w’, any existing file at
        this location will be overwritten. If mode=’a’, existing variables will
        be overwritten. (default='w')
    zlib : bool
        Flag for engaging zlib compression, if True compression is used
        (default=False)
    complevel : int
        An integer flag between 1 and 9 describing the level of compression
        desired. Ignored if zlib=False. (default=4)
    shuffle : bool
        The HDF5 shuffle filter will be applied before compressing the data.
        This significantly improves compression. Ignored if zlib=False.
        (default=True)
    preserve_meta_case : bool
        Flag specifying the case of the meta data variable strings. If True,
        then the variable strings within the MetaData object (which
        preserves case) are used to name variables in the written netCDF
        file. If False, then the variable strings used to access data from
        the pysat.Instrument object are used instead. (default=False)
    check_type : list or NoneType
        List of keys associated with `meta_dict` that should have the same
        data type as `coltype`.  These will be removed from the filtered
        output if they differ.  If None, this check will default to
        include fill, min, and max values. (default=None)
    export_nan : list or NoneType
        By default, the metadata variables where a value of NaN is allowed
        and written to the netCDF4 file is maintained by the Meta object
        attached to the pysat.Instrument object. A list supplied here
        will override the settings provided by Meta, and all parameters
        included will be written to the file. If not listed
        and a value is NaN then that attribute simply won't be included in
        the netCDF4 file. (default=None)
    unlimited_time : bool
        Flag specifying whether or not the epoch/time dimension should be
        unlimited; it is when the flag is True. (default=True)
    meta_translation : dict or NoneType
        The keys in the input dict are used to map
        metadata labels for `inst` to one or more values used when writing
        the file. E.g., `{meta.labels.fill_val: ['FillVal', '_FillValue']}`
        would result in both 'FillVal' and '_FillValue' being used to store
        variable fill values in the netCDF file. Overrides use of
        `inst._meta_translation_table`.
    meta_processor : function or NoneType
        If not None, a dict containing all of the metadata will be
        passed to `meta_processor` which should return a processed version
        of the input dict. If None and `inst` has a valid
        `inst._export_meta_post_processing` function then that
        function is used for `meta_processor`. (default=None)

    Note
    ----
    Depending on which kwargs are specified, the input class, `inst`, will
    be modified.

    Stores 1-D data along dimension 'Epoch' - the date time index.

    Stores higher order data (e.g. dataframes within series) separately

    - The name of the main variable column is used to prepend subvariable
      names within netCDF, var_subvar_sub
    - A netCDF4 dimension is created for each main variable column
      with higher order data; first dimension Epoch
    - The index organizing the data stored as a dimension variable
      and `long_name` will be set to 'Epoch'.
    - `from_netcdf` uses the variable dimensions to reconstruct data
      structure

    All attributes attached to instrument meta are written to netCDF attrs
    with the exception of 'Date_End', 'Date_Start', 'File', 'File_Date',
    'Generation_Date', and 'Logical_File_ID'. These are defined within
    to_netCDF at the time the file is written, as per the adopted standard,
    SPDF ISTP/IACG Modified for NetCDF. Atrributes 'Conventions' and
    'Text_Supplement' are given default values if not present.

    """
    # Check epoch name information
    if epoch_name is None:
        if inst.pandas_format:
            dstr = ''.join(['Assigning "Epoch" for time label when written',
                            ' to file. In the future, the default will ',
                            'be updated to "time."'])
            warnings.warn(dstr, DeprecationWarning, stacklevel=2)
            epoch_name = 'Epoch'
        else:
            pysat.logger.debug('Assigning "time" for time index.')
            epoch_name = 'time'

    # Ensure there is data to write
    if inst.empty:
        pysat.logger.warning('Empty Instrument, not writing {:}'.format(fname))
        return

    # Ensure directory path leading up to filename exists
    pysat.utils.files.check_and_make_path(os.path.split(fname)[0])

    # Check export NaNs first
    if export_nan is None:
        dstr = '`export_nan` not defined, using `self.meta._export_nan`.'
        pysat.logger.debug(dstr)
        export_nan = inst.meta._export_nan

    # Add standard fill, value_max, and value_min values to `check_type`
    if check_type is None:
        check_type = [inst.meta.labels.fill_val, inst.meta.labels.max_val,
                      inst.meta.labels.min_val]
    else:
        for label in [inst.meta.labels.fill_val, inst.meta.labels.max_val,
                      inst.meta.labels.min_val]:
            if label not in check_type:
                check_type.append(label)

    # Base_instrument used to define the standard attributes attached
    # to the instrument object. Any additional attributes added
    # to the main input Instrument will be written to the netCDF4
    if base_instrument is None:
        base_attrb = dir(pysat.Instrument())

    # Store any non standard attributes. Compare this Instrument's attributes
    # to the standard, filtering out any 'private' attributes (those that start
    # with a '_') and saving any custom public attributes
    inst_attrb = dir(inst)

    # Add the global meta data
    if hasattr(inst.meta, 'header') and len(inst.meta.header.global_attrs) > 0:
        attrb_dict = inst.meta.header.to_dict()
    else:
        attrb_dict = {}

    for ikey in inst_attrb:
        if ikey not in base_attrb:
            if ikey.find('_') != 0:
                attrb_dict[ikey] = getattr(inst, ikey)

    # Add additional metadata to conform to standards
    attrb_dict['pysat_version'] = pysat.__version__
    if 'Conventions' not in attrb_dict:
        attrb_dict['Conventions'] = 'pysat-simplified SPDF ISTP/IACG for NetCDF'
    if 'Text_Supplement' not in attrb_dict:
        attrb_dict['Text_Supplement'] = ''

    # Remove any attributes with the names below. pysat is responsible
    # for including them in the file.
    pysat_items = ['Date_End', 'Date_Start', 'File', 'File_Date',
                   'Generation_Date', 'Logical_File_ID']
    for pitem in pysat_items:
        if pitem in attrb_dict:
            pysat.logger.debug('Removing {} attribute and replacing.'.format(
                pitem))
            attrb_dict.pop(pitem)

    # Set the general file information
    attrb_dict['platform'] = inst.platform
    attrb_dict['name'] = inst.name
    attrb_dict['tag'] = inst.tag
    attrb_dict['inst_id'] = inst.inst_id
    attrb_dict['acknowledgements'] = inst.acknowledgements
    attrb_dict['references'] = inst.references
    attrb_dict['Date_End'] = dt.datetime.strftime(
        inst.index[-1], '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f')
    attrb_dict['Date_End'] = attrb_dict['Date_End'][:-3] + ' UTC'

    attrb_dict['Date_Start'] = dt.datetime.strftime(
        inst.index[0], '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f')
    attrb_dict['Date_Start'] = attrb_dict['Date_Start'][:-3] + ' UTC'
    attrb_dict['File'] = os.path.split(fname)
    attrb_dict['File_Date'] = inst.index[-1].strftime(
        '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f')
    attrb_dict['File_Date'] = attrb_dict['File_Date'][:-3] + ' UTC'
    attrb_dict['Generation_Date'] = dt.datetime.utcnow().strftime('%Y%m%d')
    attrb_dict['Logical_File_ID'] = os.path.split(fname)[-1].split('.')[:-1]

    # Check for binary types, convert to string or int when found
    for akey in attrb_dict.keys():
        if attrb_dict[akey] is None:
            attrb_dict[akey] = ''
        elif isinstance(attrb_dict[akey], bool):
            attrb_dict[akey] = int(attrb_dict[akey])

    # Check if there are multiple variables with same characters,
    # but with a different case.
    lower_variables = [var.lower() for var in inst.variables]
    unique_lower_variables = np.unique(lower_variables)
    if len(unique_lower_variables) != len(lower_variables):
        raise ValueError(' '.join(('There are multiple variables with the',
                                   'same name but different case which',
                                   'results in a loss of metadata. Please',
                                   'make the names unique.')))

    # Begin processing metadata for writing to the file. Translate metadata
    # to standards needed by file as passed by user in `meta_translation`.
    if meta_translation is None:
        if inst._meta_translation_table is not None:
            meta_translation = inst._meta_translation_table
            pysat.logger.debug(' '.join(('Using Metadata Translation Table:',
                                         str(inst._meta_translation_table))))
        else:
            meta_translation = default_to_netcdf_translation_table(inst)

    # Ensure input dictionary unaffected by processing
    meta_translation = copy.deepcopy(meta_translation)

    # Ensure `meta_translation` has default values for items not assigned.
    # This is needed for the higher order pandas support and may be removed.
    def_meta_trans = default_to_netcdf_translation_table(inst)
    for key in def_meta_trans.keys():
        if key not in meta_translation:
            meta_translation[key] = def_meta_trans[key]

    # Get current metadata in dictionary form
    export_meta = inst.meta.to_dict()

    # Add in epoch metadata, not normally stored in meta.
    epoch_meta = return_epoch_metadata(inst, epoch_name)
    export_meta[epoch_name] = epoch_meta

    # Ensure the metadata is set and updated to netCDF4 standards
    export_meta = add_netcdf4_standards_to_metadict(inst, export_meta,
                                                    epoch_name,
                                                    check_type=check_type,
                                                    export_nan=export_nan)

    # Translate labels in export_meta into labels the user actually specified
    export_meta = apply_table_translation_to_file(inst, export_meta,
                                                  meta_translation)

    # Apply instrument specific post-processing to the `export_meta`
    if meta_processor is None:
        if hasattr(inst._export_meta_post_processing, '__call__'):
            meta_processor = inst._export_meta_post_processing

    if meta_processor is not None:
        export_meta = meta_processor(export_meta)

    # Handle output differently, depending on data format.
    if inst.pandas_format:
        # General process for writing data:
        # 1) take care of the EPOCH information,
        # 2) iterate over the variable colums in Instrument.data and check
        #    the type of data,
        #    - if 1D column:
        #      A) do simple write (type is not an object)
        #      B) if it is an object, then check if writing strings
        #      C) if not strings, write object
        #    - if column is a Series of Frames, write as 2D variables
        # 3) metadata must be filtered before writing to netCDF4, since
        #    string variables can't have a fill value
        with netCDF4.Dataset(fname, mode=mode, format='NETCDF4') as out_data:
            # Attach the global attributes
            out_data.setncatts(attrb_dict)

            # Specify the number of items, to reduce function calls.
            num = len(inst.index)

            # Write out the datetime index
            if unlimited_time:
                out_data.createDimension(epoch_name, None)
            else:
                out_data.createDimension(epoch_name, num)
            cdfkey = out_data.createVariable(epoch_name, 'i8',
                                             dimensions=(epoch_name),
                                             zlib=zlib,
                                             complevel=complevel,
                                             shuffle=shuffle)

            # Attach epoch metadata
            cdfkey.setncatts(export_meta[epoch_name])

            # Attach the time index to the data
            cdfkey[:] = (inst.index.values.astype(np.int64)
                         * 1.0E-6).astype(np.int64)

            # Iterate over all of the columns in the Instrument dataframe
            # check what kind of data we are dealing with, then store
            for key in inst.variables:
                # Get information on type data we are dealing with.  `data` is
                # data in prior type (multiformat support).  `coltype` is the
                # direct type, and np.int64 and datetime_flag lets you know if
                # the data is full of time information.
                if preserve_meta_case:
                    # Use the variable case stored in the MetaData object
                    case_key = inst.meta.var_case_name(key)
                else:
                    # Use variable names used by user when working with data
                    case_key = key
                lower_key = key.lower()

                data, coltype, datetime_flag = inst._get_data_info(inst[key])

                # Operate on data based upon type
                if inst[key].dtype != np.dtype('O'):
                    # Not an object, normal basic 1D data.
                    cdfkey = out_data.createVariable(case_key, coltype,
                                                     dimensions=(epoch_name),
                                                     zlib=zlib,
                                                     complevel=complevel,
                                                     shuffle=shuffle)
                    # Set metadata
                    cdfkey.setncatts(export_meta[lower_key])

                    # Assign data
                    if datetime_flag:
                        # Datetime is in nanoseconds, storing milliseconds.
                        cdfkey[:] = (data.values.astype(coltype)
                                     * 1.0E-6).astype(coltype)
                    else:
                        # Not datetime data, just store as is.
                        cdfkey[:] = data.values.astype(coltype)
                else:
                    # It is a Series of objects.  First, figure out what the
                    # individual object types are.  Then, act as needed.

                    # Use info in coltype to get real datatype of object
                    if coltype == str:
                        cdfkey = out_data.createVariable(case_key, coltype,
                                                         dimensions=epoch_name,
                                                         complevel=complevel,
                                                         shuffle=shuffle)

                        # Set metadata
                        cdfkey.setncatts(export_meta[lower_key])

                        # Time to actually write the data now
                        cdfkey[:] = data.values

                    else:
                        # Still dealing with an object, not just a Series of
                        # strings. Maps to `if` check on coltypes, being
                        # string-based. Presuming a Series with a DataFrame or
                        # Series in each location. Start by collecting some
                        # basic info on dimensions sizes, names, then create
                        # corresponding netCDF4 dimensions total dimensions
                        # stored for object are epoch plus ones created below
                        dims = np.shape(inst[key].iloc[0])
                        obj_dim_names = []

                        # Pad dimensions so that the rest of the code works
                        # for either a Series or a DataFrame.
                        if len(dims) == 1:
                            dims = (dims[0], 0)

                        # Don't need to go over last dimension value,
                        # it covers number of columns (if a frame).
                        for i, dim in enumerate(dims[:-1]):
                            obj_dim_names.append(case_key)
                            out_data.createDimension(obj_dim_names[-1], dim)

                        # Create simple tuple with information needed to create
                        # the right dimensions for variables that will
                        # be written to file.
                        var_dim = tuple([epoch_name] + obj_dim_names)

                        # Determine whether data is in a DataFrame or Series
                        try:
                            # Start by assuming it is a DataFrame
                            iterable = inst[key].iloc[0].columns
                            is_frame = True
                        except AttributeError:
                            # Otherwise get sub-variables for a Series
                            iterable = [inst[key].iloc[0].name]
                            is_frame = False

                        # Find the subvariable data within the main variable,
                        # checking that this is not an empty DataFrame or
                        # Series. Determine the underlying data types.
                        good_data_loc = 0
                        for idat in np.arange(len(inst.data)):
                            if len(inst.data[key].iloc[0]) > 0:
                                good_data_loc = idat
                                break

                        # Found a place with data, if there is one
                        # now iterate over the subvariables, get data info
                        # create netCDF4 variables and store the data
                        # stored name is variable_subvariable.
                        for col in iterable:
                            if is_frame:
                                # We are working with a DataFrame, so
                                # multiple subvariables stored under a single
                                # main variable heading.
                                idx = inst[key].iloc[good_data_loc][col]
                                data, coltype, _ = inst._get_data_info(idx)

                                # netCDF4 doesn't support string compression
                                if coltype == str:
                                    lzlib = False
                                else:
                                    lzlib = zlib

                                cdfkey = out_data.createVariable(
                                    '_'.join((case_key, col)), coltype,
                                    dimensions=var_dim, zlib=lzlib,
                                    complevel=complevel, shuffle=shuffle)

                                # Set metadata
                                lkey = '_'.join((lower_key, col.lower()))
                                cdfkey.setncatts(export_meta[lkey])

                                # Attach data.  It may be slow to repeatedly
                                # call the store method as well astype method
                                # below collect data into a numpy array, then
                                # write the full array in one go.
                                temp_cdf_data = np.zeros(
                                    (num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = inst[
                                        key].iloc[i][col].values

                                # Write data
                                cdfkey[:, :] = temp_cdf_data
                            else:
                                # We are dealing with a Series.  Get
                                # information from within the series.
                                idx = inst[key].iloc[good_data_loc]
                                data, coltype, _ = inst._get_data_info(idx)

                                # netCDF4 doesn't support string compression
                                if coltype == str:
                                    lzlib = False
                                else:
                                    lzlib = zlib

                                cdfkey = out_data.createVariable(
                                    case_key + '_data', coltype,
                                    dimensions=var_dim, zlib=lzlib,
                                    complevel=complevel, shuffle=shuffle)

                                # Set metadata
                                tempk = '_'.join([lower_key, lower_key])
                                cdfkey.setncatts(export_meta[tempk])

                                # Attach data
                                temp_cdf_data = np.zeros(
                                    (num, dims[0]), dtype=coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = inst[i, key].values

                                # Write data
                                cdfkey[:, :] = temp_cdf_data

                        # We are done storing the actual data for the given
                        # higher order variable. Now we need to store the index
                        # for all of that fancy data.

                        # Get index information
                        idx = good_data_loc
                        data, coltype, datetime_flag = inst._get_data_info(
                            inst[key].iloc[idx].index)

                        # Create dimension variable to store index in netCDF4
                        cdfkey = out_data.createVariable(case_key, coltype,
                                                         dimensions=var_dim,
                                                         zlib=zlib,
                                                         complevel=complevel,
                                                         shuffle=shuffle)
                        # Set meta data
                        cdfkey.setncatts(export_meta[lower_key])

                        # Treat time and non-time data differently
                        if datetime_flag:
                            # Set data
                            temp_cdf_data = np.zeros((num, dims[0]),
                                                     dtype=coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = inst[i, key].index.values
                            cdfkey[:, :] = (temp_cdf_data * 1.0E-6).astype(
                                coltype)

                        else:
                            # Set data
                            temp_cdf_data = np.zeros((num, dims[0]),
                                                     dtype=coltype)

                            for i in range(num):
                                temp_cdf_data[i, :] = inst[
                                    key].iloc[i].index.astype(coltype)
                            cdfkey[:, :] = temp_cdf_data
    else:
        # Attach the metadata to a separate xarray.Dataset object, ensuring
        # the Instrument data object is unchanged.
        xr_data = xr.Dataset(inst.data)

        # Convert datetime values into integers as done for pandas
        xr_data['time'] = (inst['time'].values.astype(np.int64)
                           * 1.0E-6).astype(np.int64)

        # Update 'time' dimension to `epoch_name`
        xr_data = xr_data.rename({'time': epoch_name})

        # Transfer metadata
        pysat_meta_to_xarray_attr(xr_data, export_meta, epoch_name)

        # If the case needs to be preserved, update Dataset variables.
        if preserve_meta_case:
            for var in xarray_vars_no_time(xr_data, time_label=epoch_name):
                # Use the variable case stored in the MetaData object
                case_var = inst.meta.var_case_name(var)

                if case_var != var:
                    xr_data = xr_data.rename({var: case_var})

        # Set the standard encoding values
        encoding = {var: {'zlib': zlib, 'complevel': complevel,
                          'shuffle': shuffle} for var in xr_data.keys()}

        # netCDF4 doesn't support compression for string data. Reset values
        # in `encoding` for data found to be string type.
        for var in xr_data.keys():
            vtype = xr_data[var].dtype

            # Account for possible type for unicode strings
            if vtype == np.dtype('<U4'):
                vtype = str

            if vtype == str:
                encoding[var]['zlib'] = False

        if unlimited_time:
            xr_data.encoding['unlimited_dims'] = {epoch_name: True}

        # Add general attributes
        xr_data.attrs = attrb_dict

        # Write the netCDF4 file
        xr_data.to_netcdf(fname, mode=mode, encoding=encoding)

        # Close for safety
        xr_data.close()

    return
