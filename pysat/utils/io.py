#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Input/Output utilities for pysat data."""


import datetime as dt
import netCDF4
import numpy as np
import os
import pandas as pds
import xarray as xr

import pysat


def pysat_meta_to_xarray_attr(xr_data, pysat_meta):
    """Attach pysat metadata to xarray Dataset as attributes.

    Parameters
    ----------
    xr_data : xarray.Dataset
        Xarray Dataset whose attributes will be updated
    pysat_meta : pysat.MetaData
        pysat MetaData class object supplying attribute data

    """

    def is_fill(meta_value):
        if meta_value is not None:
            try:
                if len(meta_value) > 0:
                    return False
            except TypeError:
                if not np.isnan(meta_value):
                    return False
        return True

    # Cycle through all the pysat MetaData measurements
    for data_key in pysat_meta.keys():
        # Select the measurements that are also in the xarray data
        if data_key in xr_data.data_vars.keys():
            # Cycle through all the pysat MetaData labels
            for meta_key in pysat_meta[data_key].keys():
                # Assign attributes if the MetaData is not set to a fill value
                if not is_fill(pysat_meta[data_key][meta_key]):
                    xr_data.data_vars[data_key].attrs[meta_key] = pysat_meta[
                        data_key][meta_key]

    return


def filter_netcdf4_metadata(inst, mdata_dict, coltype, remove=False,
                            export_nan=None):
    """Filter metadata properties to be consistent with netCDF4.

    Parameters
    ----------
    mdata_dict : dict
        Dictionary equivalent to Meta object info
    coltype : type
        Data type provided by pysat.Instrument._get_data_info
    remove : bool
        Removes FillValue and associated parameters disallowed for strings
        (default=False)
    export_nan : list or NoneType
        Metadata parameters allowed to be NaN (default=None)

    Returns
    -------
    dict
        Modified as needed for netCDf4

    Warnings
    --------
    UserWarning
        When data removed due to conflict between value and type

    Note
    ----
    Remove forced to True if coltype consistent with a string type

    Metadata values that are NaN and not listed in export_nan are removed.

    """

    # Remove any metadata with a value of NaN not present in export_nan
    filtered_dict = mdata_dict.copy()
    for key, value in mdata_dict.items():
        try:
            if np.isnan(value):
                if key not in export_nan:
                    filtered_dict.pop(key)
        except TypeError:
            # If a TypeError thrown, it's not NaN
            pass
    mdata_dict = filtered_dict

    # Coerce boolean types to integers
    for key in mdata_dict:
        if type(mdata_dict[key]) == bool:
            mdata_dict[key] = int(mdata_dict[key])

    if coltype == str:
        remove = True
        warnings.warn('FillValue is not an acceptable '
                      'parameter for strings - it will be removed')

    # Make sure _FillValue is the same type as the data
    estr = ''.join(('FillValue for {a:s}{b:s} cannot be safely casted to ',
                    '{c:s}, but casting anyways. This may result in ',
                    'unexpected behavior'))
    if '_FillValue' in mdata_dict.keys():
        if remove:
            mdata_dict.pop('_FillValue')
        else:
            if not np.can_cast(mdata_dict['_FillValue'], coltype):
                if 'FieldNam' in mdata_dict:
                    wstr = estr.format(a=mdata_dict['FieldNam'],
                                       b=" ({:s})".format(
                                           str(mdata_dict['_FillValue'])),
                                       c=coltype)
                else:
                    wstr = estr.format(a=str(mdata_dict['_FillValue']),
                                       b="", c=coltype)
                warnings.warn(wstr)

    # Check if load routine actually returns meta
    if self.meta.data.empty:
        self.meta[self.variables] = {self.meta.labels.name: self.variables,
                                     self.meta.labels.units:
                                     [''] * len(self.variables)}

    # Make sure FillValue is the same type as the data
    if 'FillVal' in mdata_dict.keys():
        if remove:
            mdata_dict.pop('FillVal')
        else:
            mdata_dict['FillVal'] = np.array(mdata_dict['FillVal']).astype(
                coltype)

    return mdata_dict


def update_meta_to_netcdf4_standards(inst, epoch_name):
    """Update metadata to meet SPDF ISTP/IACG NetCDF standards.

    Parameters
    ----------
    inst : pysat.Instrument
        Object containing data and meta data

    """
    # Ensure the time-index metadata is set and updated to netCDF4 standards
    inst.meta.add_epoch_metadata(epoch_name)

    # Update the time standards
    time_dict = inst.meta[epoch_name].to_dict()
    time_dict['calendar'] = 'standard'
    time_dict['Format'] = 'i8'
    time_dict['Var_Type'] = 'data'
    if inst.index.is_monotonic_increasing:
        time_dict['MonoTon'] = 'increase'
    elif inst.index.is_monotonic_decreasing:
        time_dict['MonoTon'] = 'decrease'
    time_dict['Time_Base'] = epoch_label
    time_dict['Time_Scale'] = 'UTC'
    time_dict = filter_netcdf4_metadata(new_dict, np.int64,
                                        export_nan=export_nan)
    inst.meta[epoch_name] = time_dict

    # Update the non-time variable meta data standards
    # HERE

    
    return;


def load_netcdf4(fnames, strict_meta=False, file_format=None,
                 epoch_name='Epoch', pandas_format=True,
                 labels={'units': ('units', str), 'name': ('long_name', str),
                         'notes': ('notes', str), 'desc': ('desc', str),
                         'plot': ('plot_label', str), 'axis': ('axis', str),
                         'scale': ('scale', str),
                         'min_val': ('value_min', np.float64),
                         'max_val': ('value_max', np.float64),
                         'fill_val': ('fill', np.float64)}):
    """Load netCDF-3/4 file produced by pysat.

    Parameters
    ----------
    fnames : str, array_like, or NoneType
        Filename(s) to load, will fail if None (default=None)
    strict_meta : bool
        Flag that checks if metadata across fnames is the same if True
        (default=False)
    file_format : str or NoneType
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        If None, defaults to 'NETCDF4'. (default=None)
    epoch_name : str
        Data key for time variable (default='Epoch')
    pandas_format : bool
        Flag specifying if data is stored in a pandas DataFrame (True) or
        xarray Dataset (False). (default=False)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})

    Returns
    -------
    out : pandas.DataFrame or xarray.Dataset
        Class holding file data
    meta : pysat.Meta
        Class holding file meta data

    Raises
    ------
    KeyError
        If epoch/time dimension could not be identified.

    """
    # Process the input values
    fnames = listify(fnames)

    if file_format is None:
        file_format = 'NETCDF4'
    else:
        file_format = file_format.upper()

    # Initialize local variables
    saved_meta = None
    running_idx = 0
    running_store = []
    two_d_keys = []
    two_d_dims = []
    meta = pysat.Meta(labels=labels)

    # Load data by type
    if pandas_format:
        # The data is in a pandas.DataFrame
        for fname in fnames:
            with netCDF4.Dataset(fname, mode='r', format=file_format) as data:
                # Build a dictionary with all global ncattrs and add those
                # attributes to a pysat meta object
                for ncattr in data.ncattrs():
                    if hasattr(meta, ncattr):
                        meta.__setattr__('{:}_'.format(ncattr),
                                         data.getncattr(ncattr))
                    else:
                        meta.__setattr__(ncattr, data.getncattr(ncattr))

                loaded_vars = {}
                for key in data.variables.keys():
                    # Load the metadata.  From here group unique dimensions and
                    # act accordingly, 1D, 2D, 3D
                    if len(data.variables[key].dimensions) == 1:
                        if pandas_format:
                            # Load 1D data variables, assuming basic
                            # time dimension
                            loaded_vars[key] = data.variables[key][:]

                        # Load up metadata
                        meta_dict = {}
                        for nc_key in data.variables[key].ncattrs():
                            meta_dict[nc_key] = data.variables[key].getncattr(
                                nc_key)
                        meta[key] = meta_dict

                    if len(data.variables[key].dimensions) == 2:
                        # Part of dataframe within dataframe
                        two_d_keys.append(key)
                        two_d_dims.append(data.variables[key].dimensions)

                    if len(data.variables[key].dimensions) >= 3:
                        raise ValueError(' '.join(('pysat only supports 1D',
                                                   'and 2D data in pandas.',
                                                   'Please use xarray for',
                                                   'this data product.')))

                # We now have a list of keys that need to go into a dataframe,
                # could be more than one, collect unique dimensions for 2D keys
                for dim in set(two_d_dims):
                    # First or second dimension could be epoch. Use other
                    # dimension name as variable name
                    if dim[0] == epoch_name:
                        obj_key = dim[1]
                    elif dim[1] == epoch_name:
                        obj_key = dim[0]
                    else:
                        raise KeyError('Epoch not found!')

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
                    # variable then use that info for index
                    if obj_key in obj_var_keys:
                        # String used to indentify dimension also in
                        # data.variables will be used as an index
                        index_key_name = obj_key

                        # If the object index uses UNIX time, process into
                        # datetime index
                        if data.variables[obj_key].getncattr(
                                meta.labels.name) == epoch_name:
                            # Found the name to be used in DataFrame index
                            index_name = epoch_name
                            time_index_flag = True
                        else:
                            time_index_flag = False

                            # Label to be used in DataFrame index
                            index_name = data.variables[obj_key].getncattr(
                                meta.labels.name)
                    else:
                        # Dimension is not itself a variable
                        index_key_name = None

                    # Iterate over the variables and grab metadata
                    dim_meta_data = pysat.Meta(labels=labels)

                    # Store attributes in metadata, exept for dim name
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
                        meta[obj_key] = dim_meta_dict

                    # Iterate over all variables with this dimension
                    # data storage, whole shebang
                    loop_dict = {}

                    # List holds a series of slices, parsed from dict above
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
                            time_var = pds.to_datetime(1.0E6 * time_var)
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
                                                             (step * (i + 1)),
                                                             :])
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
                    # netCDF, to loaded data dictionary
                    loaded_vars[obj_key] = loop_list
                    del loop_list

                # Prepare dataframe index for this netcdf file
                time_var = loaded_vars.pop(epoch_name)

                # Convert from GPS seconds to seconds used in pandas (unix time,
                # no leap)
                # time_var = convert_gps_to_unix_seconds(time_var)
                loaded_vars[epoch_name] = pds.to_datetime(
                    (1.0E6 * time_var).astype(np.int64))
                running_store.append(loaded_vars)
                running_idx += len(loaded_vars[epoch_name])

                if strict_meta:
                    if saved_meta is None:
                        saved_meta = meta.copy()
                    elif (meta != saved_meta):
                        raise ValueError(' '.join(('Metadata across filenames',
                                                   'is not the same.')))

        # Combine all of the data loaded across files together
        out = []
        for item in running_store:
            out.append(pds.DataFrame.from_records(item, index=epoch_name))
        out = pds.concat(out, axis=0)
    else:
        # The data is in xarray format, load differently for single or
        # multiple files
        if len(fnames) == 1:
            out = xr.open_dataset(fnames[0])
        else:
            out = xr.open_mfdataset(fnames, combine='by_coords')

        # Copy the variable attributes from the data object to the metadata
        for key in out.variables.keys():
            meta_dict = {}
            for nc_key in out.variables[key].attrs.keys():
                meta_dict[nc_key] = out.variables[key].attrs[nc_key]
            meta[key] = meta_dict

            # Remove variable attributes from the data object
            out.variables[key].attrs = {}

        # Copy the file attributes from the data object to the metadata
        for out_attr in out.attrs.keys():
            if hasattr(meta, out_attr):
                set_attr = "".join([out_attr, "_"])
                meta.__setattr__(set_attr, out.attrs[out_attr])
            else:
                meta.__setattr__(out_attr, out.attrs[out_attr])

        # Remove attributes from the data object
        out.attrs = {}

    return out, meta


def inst_to_netcdf4(inst, fname, base_instrument=None, epoch_name='Epoch',
                    zlib=False, complevel=4, shuffle=True,
                    preserve_meta_case=False, export_nan=None,
                    unlimited_time=True):
    """Store pysat data in a netCDF4 file.

    .. deprecated:: 3.2.0
        Removed `base_instrument` as a kwarg.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object with loaded data to save
    fname : str
        Output filename with full path
    base_instrument : pysat.Instrument or NoneType
        Class used as a comparison, only attributes that are present with
        self and not on base_instrument are written to netCDF. Using None
        assigns an unmodified pysat.Instrument object. (default=None)
    epoch_name : str
        Label in file for datetime index of Instrument object
    zlib : bool
        Flag for engaging zlib compression (True - compression on)
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

    Note
    ----
    Stores 1-D data along dimension 'epoch' - the date time index.

    Stores higher order data (e.g. dataframes within series) separately

    - The name of the main variable column is used to prepend subvariable
      names within netCDF, var_subvar_sub
    - A netCDF4 dimension is created for each main variable column
      with higher order data; first dimension Epoch
    - The index organizing the data stored as a dimension variable
    - from_netcdf4 uses the variable dimensions to reconstruct data
      structure

    All attributes attached to instrument meta are written to netCDF attrs
    with the exception of 'Date_End', 'Date_Start', 'File', 'File_Date',
    'Generation_Date', and 'Logical_File_ID'. These are defined within
    to_netCDF at the time the file is written, as per the adopted standard,
    SPDF ISTP/IACG Modified for NetCDF. Atrributes 'Conventions' and
    'Text_Supplement' are given default values if not present.

    """
    epoch_label = 'Milliseconds since 1970-1-1 00:00:00'

    # Check export NaNs first
    if export_nan is None:
        export_nan = inst.meta._export_nan

    # Ensure the metadata is set and updated to netCDF4 standards
    update_meta_to_netcdf4_standards(inst, epoch_name)

    # Base_instrument used to define the standard attributes attached
    # to the instrument object. Any additional attributes added
    # to the main input Instrument will be written to the netCDF4
    if base_instrument is None:
        base_attrb = dir(pysat.Instrument())
    else:
        warnings.warn("".join(["`base_instrument` has been deprecated and will",
                               "be removed in 3.2.0+"]),
                      DeprecationWarning, stacklevel=2)
        base_attrb = dir(base_instrument)

    # Store any non standard attributes. Compare this Instrument's attributes
    # to the standard, filtering out any 'private' attributes (those that start
    # with a '_') and saving any custom public attributes
    inst_attrb = dir(inst)
    attrb_dict = {}
    for ikey in inst_attrb:
        if ikey not in base_attrb:
            if ikey.find('_') != 0:
                attrb_dict[key] = getattr(inst, ikey)

    # Add additional metadata to conform to standards
    attrb_dict['pysat_version'] = pysat.__version__
    if 'Conventions' not in attrb_dict:
        attrb_dict['Conventions'] = 'SPDF ISTP/IACG Modified for NetCDF'
    if 'Text_Supplement' not in attrb_dict:
        attrb_dict['Text_Supplement'] = ''

    # Remove any attributes with the names below. pysat is responsible
    # for including them in the file.
    pysat_items = ['Date_End', 'Date_Start', 'File', 'File_Date',
                   'Generation_Date', 'Logical_File_ID']
    for pitem in pysat_items:
        if pitem in attrb_dict:
            attrb_dict.pop(pitem)

    # Set the general file information
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

    # Handle output differently, depending on data format
    if inst.pandas_format:
        # Begin processing metadata for writing to the file. Look to see if the
        # user supplied a list of export keys corresponding to internally
        # tracked pysat metadat
        export_meta = inst.generic_meta_translator(inst.meta)
        if inst._meta_translation_table is None:
            # Didn't find a translation table, using the strings
            # attached to the supplied pysat.Instrument object
            export_name_labels = [inst.meta.labels.name]
            export_units_labels = [inst.meta.labels.units]
            export_desc_labels = [inst.meta.labels.desc]
            export_notes_labels = [inst.meta.labels.notes]
        else:
            # User supplied labels in translation table
            export_name_labels = inst._meta_translation_table['name']
            export_units_labels = inst._meta_translation_table['units']
            export_desc_labels = inst._meta_translation_table['desc']
            export_notes_labels = inst._meta_translation_table['notes']
            logger.info(' '.join(('Using Metadata Translation Table:',
                                  str(inst._meta_translation_table))))

        # Apply instrument specific post-processing to the export_meta
        if hasattr(inst._export_meta_post_processing, '__call__'):
            export_meta = inst._export_meta_post_processing(export_meta)

        # Check if there are multiple variables with same characters
        # but with different case
        lower_variables = [var.lower() for var in inst.variables]
        unique_lower_variables = np.unique(lower_variables)
        if len(unique_lower_variables) != len(lower_variables):
            raise ValueError(' '.join(('There are multiple variables with the',
                                       'same name but different case which',
                                       'results in a loss of metadata. Please',
                                       'make the names unique.')))

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
        with netCDF4.Dataset(fname, mode='w', format='NETCDF4') as out_data:
            # Specify the number of items, to reduce function calls
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
            cdfkey.setncatts(inst.meta[epoch_name].to_dict())

            # Attach the time index to the data
            cdfkey[:] = (inst.index.values.astype(np.int64)
                         * 1.0E-6).astype(np.int64)

            # Iterate over all of the columns in the Instrument dataframe
            # check what kind of data we are dealing with, then store
            for key in inst.variables:
                # Get information on type data we are dealing with.  `data` is
                # data in prior type (multiformat support).  `coltype` is the
                # direct type, and np.int64 and datetime_flag lets you know if
                # the data is full of time information
                if preserve_meta_case:
                    # Use the variable case stored in the MetaData object
                    case_key = inst.meta.var_case_name(key)
                else:
                    # Use variable names used by user when working with data
                    case_key = key

                data, coltype, datetime_flag = inst._get_data_info(inst[key])

                # Operate on data based upon type
                if inst[key].dtype != np.dtype('O'):
                    # Not an object, normal basic 1D data
                    cdfkey = out_data.createVariable(case_key, coltype,
                                                     dimensions=(epoch_name),
                                                     zlib=zlib,
                                                     complevel=complevel,
                                                     shuffle=shuffle)

                    # Attach any meta data, after filtering for standards
                    try:
                        # Attach dimension metadata
                        new_dict = export_meta[case_key]
                        new_dict['Depend_0'] = epoch_name
                        new_dict['Display_Type'] = 'Time Series'
                        new_dict['Format'] = inst._get_var_type_code(coltype)
                        new_dict['Var_Type'] = 'data'
                        new_dict = filter_netcdf4_metadata(
                            new_dict, coltype, export_nan=export_nan)
                        cdfkey.setncatts(new_dict)
                    except KeyError as err:
                        logger.info(' '.join((str(err), '\n',
                                              ' '.join(('Unable to find'
                                                        'MetaData for',
                                                        key)))))
                    # Assign data
                    if datetime_flag:
                        # Datetime is in nanoseconds, storing milliseconds
                        cdfkey[:] = (data.values.astype(coltype)
                                     * 1.0E-6).astype(coltype)
                    else:
                        # Not datetime data, just store as is
                        cdfkey[:] = data.values.astype(coltype)

                # Back to main check on type of data to write
                else:
                    # It is a Series of objects.  First, figure out what the
                    # individual object typess are.  Then, act as needed.

                    # Use info in coltype to get real datatype of object
                    if (coltype == str):
                        cdfkey = out_data.createVariable(case_key, coltype,
                                                         dimensions=epoch_name,
                                                         zlib=zlib,
                                                         complevel=complevel,
                                                         shuffle=shuffle)
                        # Attach any meta data
                        try:
                            # Attach dimension metadata
                            new_dict = export_meta[case_key]
                            new_dict['Depend_0'] = epoch_name
                            new_dict['Display_Type'] = 'Time Series'
                            new_dict['Format'] = inst._get_var_type_code(
                                coltype)
                            new_dict['Var_Type'] = 'data'

                            # No FillValue or FillVal allowed for strings
                            new_dict = inst._filter_netcdf4_metadata(
                                new_dict, coltype, remove=True,
                                export_nan=export_nan)

                            # Really attach metadata now
                            cdfkey.setncatts(new_dict)
                        except KeyError:
                            logger.info(' '.join(('Unable to find MetaData for',
                                                  key)))

                        # Time to actually write the data now
                        cdfkey[:] = data.values

                    # Still dealing with an object, not just a Series of
                    # strings. Maps to `if` check on coltypes, being
                    # string-based.
                    else:
                        # Presuming a series with a dataframe or series in each
                        # location start by collecting some basic info on
                        # dimensions sizes, names, then create corresponding
                        # netCDF4 dimensions total dimensions stored for object
                        # are epoch plus ones created below
                        dims = np.shape(inst[key].iloc[0])
                        obj_dim_names = []
                        if len(dims) == 1:
                            # generally working with higher dimensional data
                            # pad dimensions so that the rest of the code works
                            # for either a Series or a Frame
                            dims = (dims[0], 0)
                        for i, dim in enumerate(dims[:-1]):
                            # Don't need to go over last dimension value,
                            # it covers number of columns (if a frame)
                            obj_dim_names.append(case_key)
                            out_data.createDimension(obj_dim_names[-1], dim)

                        # Create simple tuple with information needed to create
                        # the right dimensions for variables that will
                        # be written to file
                        var_dim = tuple([epoch_name] + obj_dim_names)

                        # We need to do different things if a series or
                        # dataframe stored
                        try:
                            # Start by assuming it is a dataframe and get a
                            # list of subvariables
                            iterable = inst[key].iloc[0].columns

                            # Store our newfound knowledge, we are dealing with
                            # a series of DataFrames
                            is_frame = True
                        except AttributeError:
                            # turns out data is Series of Series
                            # which doesn't have columns
                            iterable = [inst[key].iloc[0].name]
                            is_frame = False

                        # Find location within main variable that actually
                        # has subvariable data (not just empty frame/series)
                        # so we can determine what the real underlying data
                        # types are
                        good_data_loc = 0
                        for jjj in np.arange(len(inst.data)):
                            if len(inst.data[key].iloc[0]) > 0:
                                data_loc = jjj
                                break

                        # Found a place with data, if there is one
                        # now iterate over the subvariables, get data info
                        # create netCDF4 variables and store the data
                        # stored name is variable_subvariable
                        for col in iterable:
                            if is_frame:
                                # We are working with a dataframe so
                                # multiple subvariables stored under a single
                                # main variable heading
                                idx = inst[key].iloc[good_data_loc][col]
                                data, coltype, _ = inst._get_data_info(idx)
                                cdfkey = out_data.createVariable(
                                    '_'.join((case_key, col)), coltype,
                                    dimensions=var_dim, zlib=zlib,
                                    complevel=complevel, shuffle=shuffle)

                                # Attach any meta data
                                try:
                                    new_dict = export_meta['_'.join((case_key,
                                                                     col))]
                                    new_dict['Depend_0'] = epoch_name
                                    new_dict['Depend_1'] = obj_dim_names[-1]
                                    new_dict['Display_Type'] = 'Spectrogram'
                                    new_dict['Format'] = \
                                        inst._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    new_dict = inst._filter_netcdf4_metadata(
                                        new_dict, coltype,
                                        export_nan=export_nan)
                                    cdfkey.setncatts(new_dict)
                                except KeyError as err:
                                    logger.info(' '.join((str(err), '\n',
                                                          'Unable to find',
                                                          'MetaData for',
                                                          ', '.join((key,
                                                                     col)))))

                                # Attach data.  It may be slow to repeatedly
                                # call the store method as well astype method
                                # below collect data into a numpy array, then
                                # write the full array in one go
                                temp_cdf_data = np.zeros(
                                    (num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = \
                                        inst[key].iloc[i][col].values

                                # Write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                            else:
                                # We are dealing with a Series.  Get
                                # information from within the series
                                idx = inst[key].iloc[good_data_loc]
                                data, coltype, _ = inst._get_data_info(idx)
                                cdfkey = out_data.createVariable(
                                    case_key + '_data', coltype,
                                    dimensions=var_dim, zlib=zlib,
                                    complevel=complevel, shuffle=shuffle)

                                # Attach any meta data
                                try:
                                    new_dict = export_meta[case_key]
                                    new_dict['Depend_0'] = epoch_name
                                    new_dict['Depend_1'] = obj_dim_names[-1]
                                    new_dict['Display_Type'] = 'Spectrogram'
                                    new_dict['Format'] = \
                                        inst._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    new_dict = inst._filter_netcdf4_metadata(
                                        new_dict, coltype,
                                        export_nan=export_nan)

                                    # Really attach metadata now
                                    cdfkey.setncatts(new_dict)
                                except KeyError as err:
                                    logger.info(' '.join((str(err), '\n',
                                                          'Unable to find ',
                                                          'MetaData for,',
                                                          key)))
                                # Attach data
                                temp_cdf_data = np.zeros(
                                    (num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = inst[i, key].values
                                # write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                        # We are done storing the actual data for the given
                        # higher order variable. Now we need to store the index
                        # for all of that fancy data.

                        # Get index information
                        idx = good_data_loc
                        data, coltype, datetime_flag = inst._get_data_info(
                            inst[key].iloc[idx].index)

                        # Create dimension variable for to store index in
                        # netCDF4
                        cdfkey = out_data.createVariable(case_key, coltype,
                                                         dimensions=var_dim,
                                                         zlib=zlib,
                                                         complevel=complevel,
                                                         shuffle=shuffle)

                        # Work with metadata
                        new_dict = export_meta[case_key]
                        new_dict['Depend_0'] = epoch_name
                        new_dict['Depend_1'] = obj_dim_names[-1]
                        new_dict['Display_Type'] = 'Time Series'
                        new_dict['Format'] = inst._get_var_type_code(coltype)
                        new_dict['Var_Type'] = 'data'

                        if datetime_flag:
                            for export_name_label in export_name_labels:
                                new_dict[export_name_label] = epoch_name
                            for export_units_label in export_units_labels:
                                new_dict[export_units_label] = epoch_label
                            new_dict = inst._filter_netcdf4_metadata(
                                new_dict, coltype, export_nan=export_nan)

                            # Set metadata dict
                            cdfkey.setncatts(new_dict)

                            # Set data
                            temp_cdf_data = np.zeros((num,
                                                      dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = inst[i, key].index.values
                            cdfkey[:, :] = (temp_cdf_data.astype(coltype)
                                            * 1.0E-6).astype(coltype)

                        else:
                            if inst[key].iloc[data_loc].index.name is not None:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = \
                                        inst[key].iloc[data_loc].index.name
                            else:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = key
                            new_dict = inst._filter_netcdf4_metadata(
                                new_dict, coltype, export_nan=export_nan)

                            # Assign metadata dict
                            cdfkey.setncatts(new_dict)

                            # Set data
                            temp_cdf_data = np.zeros(
                                (num, dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = \
                                    inst[key].iloc[i].index.astype(str)
                            cdfkey[:, :] = temp_cdf_data.astype(coltype)

            # Attach attributes
            out_data.setncatts(attrb_dict)
    else:
        # Attach the metadata to the xarray.Dataset
        xr_data = pysat.data
        pysat_meta_to_xarray_attr(xr_data, pysat.meta)
        

        
    return

