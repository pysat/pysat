from __future__ import print_function
from __future__ import absolute_import

import numpy as np


def set_data_dir(path=None, store=True):
    """
    Set the top level directory pysat uses to look for data and reload.

    Parameters
    ----------
    path : string
        valid path to directory pysat uses to look for data
    store : bool
        if True, store data directory for future runs
    """

    import os
    import sys
    import pysat
    if sys.version_info[0] >= 3:
        from importlib import reload as re_load
    else:
        re_load = reload

    if os.path.isdir(path):
        if store:
            with open(os.path.join(os.path.expanduser('~'), '.pysat',
                                   'data_path.txt'), 'w') as f:
                f.write(path)
        pysat.data_dir = path
        pysat._files = re_load(pysat._files)
        pysat._instrument = re_load(pysat._instrument)
    else:
        raise ValueError('Path %s does not lead to a valid directory.' % path)


def computational_form(data):
    """
    Repackages numbers, Series, or DataFrames

    Regardless of input format, mathematical operations may be performed on the output via the same pandas mechanisms.

    This method may be particularly useful in analysis methods that aim to be instrument independent. pysat.Instrument objects can package data in a variety of ways within a DataFrame, depending upon the scientific data source. Thus, a variety of data types will be encountered by instrument independent methods and computational_form method may reduce the effort required to support more generalized processing.

    Parameters
    ----------
    data : pandas.Series
        Series of numbers, Series, DataFrames

    Returns
    -------
    pandas.Series, DataFrame, or Panel
        repacked data, aligned by indices, ready for calculation
    """

    from pysat import DataFrame, Series, datetime, Panel

    if isinstance(data.iloc[0], DataFrame):
        dslice = Panel.from_dict(dict([(i, data.iloc[i])
                                       for i in xrange(len(data))]))
    elif isinstance(data.iloc[0], Series):
        dslice = DataFrame(data.tolist())
        dslice.index = data.index
    else:
        dslice = data
    return dslice


def load_netcdf4(fnames=None, strict_meta=False, file_format=None,
                 epoch_name='Epoch', units_label='units',
                 name_label='long_name', notes_label='notes',
                 desc_label='desc', plot_label='label', axis_label='axis',
                 scale_label='scale', min_label='value_min',
                 max_label='value_max', fill_label='fill'):
    # unix_time=False, **kwargs):
    """Load netCDF-3/4 file produced by pysat.

    Parameters
    ----------
    fnames : string or array_like of strings (None)
        filenames to load
    strict_meta : boolean (False)
        check if metadata across fnames is the same
    file_format : string (None)
        file_format keyword passed to netCDF4 routine
        NETCDF3_CLASSIC, NETCDF3_64BIT, NETCDF4_CLASSIC, and NETCDF4
    epoch_name : string ('Epoch')
    units_label : string ('units')
        keyword for unit information
    name_label : string ('long_name')
        keyword for informative name label
    notes_label : string ('notes')
        keyword for file notes
    desc_label : string ('desc')
        keyword for data descriptions
    plot_label : string ('label')
        keyword for name to use on plot labels
    axis_label : string ('axis')
        keyword for axis labels
    scale_label : string ('scale')
        keyword for plot scaling
    min_label : string ('value_min')
        keyword for minimum in allowable value range
    max_label : string ('value_max')
        keyword for maximum in allowable value range
    fill_label : string ('fill')
        keyword for fill values

    Returns
    --------
    out : pandas.core.frame.DataFrame
        DataFrame output
    mdata : pysat._meta.Meta
        Meta data
    """

    import copy
    import netCDF4
    import pandas as pds
    import string
    import pysat
    try:
        basestring
    except NameError:
        basestring = str

    if fnames is None:
        raise ValueError("Must supply a filename/list of filenames")
    if isinstance(fnames, basestring):
        fnames = [fnames]

    if file_format is None:
        file_format = 'NETCDF4'
    else:
        file_format = file_format.upper()

    saved_mdata = None
    running_idx = 0
    running_store = []
    two_d_keys = []
    two_d_dims = []
    three_d_keys = []
    three_d_dims = []

    for fname in fnames:
        with netCDF4.Dataset(fname, mode='r', format=file_format) as data:
            # build up dictionary with all global ncattrs
            # and add those attributes to a pysat meta object
            ncattrsList = data.ncattrs()
            mdata = pysat.Meta(units_label=units_label, name_label=name_label,
                               notes_label=notes_label, desc_label=desc_label,
                               plot_label=plot_label, axis_label=axis_label,
                               scale_label=scale_label,
                               min_label=min_label, max_label=max_label,
                               fill_label=fill_label)
            for d in ncattrsList:
                if hasattr(mdata, d):
                    mdata.__setattr__(d+'_', data.getncattr(d))
                else:
                    mdata.__setattr__(d, data.getncattr(d))

            # loadup all of the variables in the netCDF
            loadedVars = {}
            for key in data.variables.keys():
                # load up metadata.  From here group unique
                # dimensions and act accordingly, 1D, 2D, 3D
                if len(data.variables[key].dimensions) == 1:
                    # load 1D data variable
                    # assuming basic time dimension
                    loadedVars[key] = data.variables[key][:]
                    # if key != epoch_name:
                    # load up metadata
                    meta_dict = {}
                    for nc_key in data.variables[key].ncattrs():
                        meta_dict[nc_key] = \
                                data.variables[key].getncattr(nc_key)
                    mdata[key] = meta_dict
                if len(data.variables[key].dimensions) == 2:
                    # part of dataframe within dataframe
                    two_d_keys.append(key)
                    two_d_dims.append(data.variables[key].dimensions)

                if len(data.variables[key].dimensions) == 3:
                    # part of full/dedicated dataframe within dataframe
                    three_d_keys.append(key)
                    three_d_dims.append(data.variables[key].dimensions)

            # we now have a list of keys that need to go into a dataframe,
            # could be more than one, collect unique dimensions for 2D keys
            for dim in set(two_d_dims):
                # first dimension should be epoch
                # second dimension name used as variable name
                obj_key_name = dim[1]
                # collect variable names associated with dimension
                idx_bool = [dim == i for i in two_d_dims]
                idx, = np.where(np.array(idx_bool))
                obj_var_keys = []
                clean_var_keys = []
                for i in idx:
                    obj_var_keys.append(two_d_keys[i])
                    clean_var_keys.append(
                            two_d_keys[i].split(obj_key_name + '_')[-1])

                # figure out how to index this data, it could provide its own
                # index - or we may have to create simple integer based
                # DataFrame access. If the dimension is stored as its own
                # variable then use that info for index
                if obj_key_name in obj_var_keys:
                    # string used to indentify dimension also in data.variables
                    # will be used as an index
                    index_key_name = obj_key_name
                    # if the object index uses UNIX time, process into datetime
                    # index
                    if data.variables[obj_key_name].getncattr(name_label) == \
                            epoch_name:
                        # name to be used in DataFrame index
                        index_name = epoch_name
                        time_index_flag = True
                    else:
                        time_index_flag = False
                        # label to be used in DataFrame index
                        index_name = \
                            data.variables[obj_key_name].getncattr(name_label)
                else:
                    # dimension is not itself a variable
                    index_key_name = None

                # iterate over the variables and grab metadata
                dim_meta_data = pysat.Meta(units_label=units_label,
                                           name_label=name_label,
                                           notes_label=notes_label,
                                           desc_label=desc_label,
                                           plot_label=plot_label,
                                           axis_label=axis_label,
                                           scale_label=scale_label,
                                           min_label=min_label,
                                           max_label=max_label,
                                           fill_label=fill_label)

                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    # store attributes in metadata, exept for dim name
                    meta_dict = {}
                    for nc_key in data.variables[key].ncattrs():
                        meta_dict[nc_key] = \
                            data.variables[key].getncattr(nc_key)
                    dim_meta_data[clean_key] = meta_dict

                dim_meta_dict = {'meta': dim_meta_data}
                if index_key_name is not None:
                    # add top level meta
                    for nc_key in data.variables[obj_key_name].ncattrs():
                        dim_meta_dict[nc_key] = \
                            data.variables[obj_key_name].getncattr(nc_key)
                    mdata[obj_key_name] = dim_meta_dict

                # iterate over all variables with this dimension and store data
                # data storage, whole shebang
                loop_dict = {}
                # list holds a series of slices, parsed from dict above
                loop_list = []
                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    # data
                    loop_dict[clean_key] = \
                        data.variables[key][:, :].flatten(order='C')
                # number of values in time
                loop_lim = data.variables[obj_var_keys[0]].shape[0]
                # number of values per time
                step_size = len(data.variables[obj_var_keys[0]][0, :])
                # check if there is an index we should use
                if not (index_key_name is None):
                    # an index was found
                    time_var = loop_dict.pop(index_key_name)
                    if time_index_flag:
                        # create datetime index from data
                        if file_format == 'NETCDF4':
                            time_var = pds.to_datetime(1E6*time_var)
                        else:
                            time_var = pds.to_datetime(1E6*time_var)
                    new_index = time_var
                    new_index_name = index_name
                else:
                    # using integer indexing
                    new_index = np.arange(loop_lim*step_size,
                                          dtype=int) % step_size
                    new_index_name = 'index'
                # load all data into frame
                if len(loop_dict.keys()) > 1:
                    loop_frame = pds.DataFrame(loop_dict,
                                               columns=clean_var_keys)
                    if obj_key_name in loop_frame:
                        del loop_frame[obj_key_name]
                    # break massive frame into bunch of smaller frames
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:step_size*(i+1), :])
                        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name
                else:
                    loop_frame = pds.Series(loop_dict[clean_var_keys[0]],
                                            name=obj_var_keys[0])
                    # break massive series into bunch of smaller series
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:step_size*(i+1)])
                        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name
                
                # add 2D object data, all based on a unique dimension within
                # netCDF, to loaded data dictionary
                loadedVars[obj_key_name] = loop_list
                del loop_list

            # we now have a list of keys that need to go into a dataframe,
            # could be more than one, collect unique dimensions for 2D keys
            for dim in set(three_d_dims):
                # collect variable names associated with dimension
                idx_bool = [dim == i for i in three_d_dims]
                idx, = np.where(np.array(idx_bool))
                obj_var_keys = []
                for i in idx:
                    obj_var_keys.append(three_d_keys[i])

                for obj_key_name in obj_var_keys:
                    # store attributes in metadata
                    meta_dict = {}
                    for nc_key in data.variables[obj_key_name].ncattrs():
                        meta_dict[nc_key] = \
                            data.variables[obj_key_name].getncattr(nc_key)
                    mdata[obj_key_name] = meta_dict

                    # iterate over all variables with this dimension and store data
                    # data storage, whole shebang
                    loop_dict = {}
                    # list holds a series of slices, parsed from dict above
                    loop_list = []
                    loop_dict[obj_key_name] = \
                        data.variables[obj_key_name][:, :, :]
                    # number of values in time
                    loop_lim = data.variables[obj_key_name].shape[0]
                    # number of values per time
                    step_size_x = len(data.variables[obj_key_name][0, :, 0])
                    step_size_y = len(data.variables[obj_key_name][0, 0, :])
                    step_size = step_size_x
                    loop_dict[obj_key_name] = \
                        loop_dict[obj_key_name].reshape((loop_lim*step_size_x,
                                                         step_size_y))
                    # check if there is an index we should use
                    if not (index_key_name is None):
                        # an index was found
                        time_var = loop_dict.pop(index_key_name)
                        if time_index_flag:
                            # create datetime index from data
                            if file_format == 'NETCDF4':
                                time_var = pds.to_datetime(1E6*time_var)
                            else:
                                time_var = pds.to_datetime(1E6*time_var)
                        new_index = time_var
                        new_index_name = index_name
                    else:
                        # using integer indexing
                        new_index = np.arange(loop_lim*step_size,
                                              dtype=int) % step_size
                        new_index_name = 'index'
                    # load all data into frame
                    loop_frame = pds.DataFrame(loop_dict[obj_key_name])
                    # del loop_frame['dimension_1']
                    # break massive frame into bunch of smaller frames
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:step_size*(i+1), :])
                        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name

                    # add 2D object data, all based on a unique dimension within netCDF,
                    # to loaded data dictionary
                    loadedVars[obj_key_name] = loop_list
                    del loop_list

            # prepare dataframe index for this netcdf file
            time_var = loadedVars.pop(epoch_name)

            # convert from GPS seconds to seconds used in pandas (unix time,
            # no leap)
            # time_var = convert_gps_to_unix_seconds(time_var)
            if file_format == 'NETCDF4':
                loadedVars[epoch_name] = pds.to_datetime((1E6 *
                                                          time_var).astype(int))
            else:
                loadedVars[epoch_name] = pds.to_datetime((time_var *
                                                          1E6).astype(int))
            # loadedVars[epoch_name] = pds.to_datetime((time_var*1E6).astype(int))
            running_store.append(loadedVars)
            running_idx += len(loadedVars[epoch_name])

            if strict_meta:
                if saved_mdata is None:
                    saved_mdata = copy.deepcopy(mdata)
                elif (mdata != saved_mdata):
                    raise ValueError('Metadata across filenames is not the ' +
                                     'same.')

    # combine all of the data loaded across files together
    out = []
    for item in running_store:
        out.append(pds.DataFrame.from_records(item, index=epoch_name))
    out = pds.concat(out, axis=0)
    return out, mdata
