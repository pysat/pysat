from importlib import reload as re_load
import numpy as np
import os

from portalocker import Lock, TemporaryFileLock
import xarray as xr

import pysat


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

    # account for a user prefix in the path, such as ~
    path = os.path.expanduser(path)
    # account for the presence of $HOME or similar
    path = os.path.expandvars(path)

    if os.path.isdir(path):
        if store:
            data_path_file = os.path.join(os.path.expanduser('~'),
                                          '.pysat', 'data_path.txt')
            with NetworkLock(data_path_file, 'w', pysat.file_timeout) as fout:
                fout.write(path)

        pysat.data_dir = path
        pysat._files = re_load(pysat._files)
        pysat._instrument = re_load(pysat._instrument)
    else:
        raise ValueError(' '.join(('Path {:s} does not lead to a valid',
                                   'directory.')).format(path))


def scale_units(out_unit, in_unit):
    """ Determine the scaling factor between two units

    Parameters
    ----------
    out_unit : str
        Desired unit after scaling
    in_unit : str
        Unit to be scaled

    Returns
    -------
    unit_scale : float
        Scaling factor that will convert from in_units to out_units

    Note
    ----
    Accepted units include degrees ('deg', 'degree', 'degrees'),
    radians ('rad', 'radian', 'radians'),
    hours ('h', 'hr', 'hrs', 'hour', 'hours'), and lengths ('m', 'km', 'cm').
    Can convert between degrees, radians, and hours or different lengths.

    Example
    -------
    ::

        import numpy as np
        two_pi = 2.0 * np.pi
        scale = scale_units("deg", "RAD")
        two_pi *= scale
        two_pi # will show 360.0


    """

    if out_unit == in_unit:
        return 1.0

    accepted_units = {'deg': ['deg', 'degree', 'degrees'],
                      'rad': ['rad', 'radian', 'radians'],
                      'h': ['h', 'hr', 'hrs', 'hours'],
                      'm': ['m', 'km', 'cm'],
                      'm/s': ['m/s', 'cm/s', 'km/s', 'm s$^{-1}$',
                              'cm s$^{-1}$', 'km s$^{-1}$', 'm s-1', 'cm s-1',
                              'km s-1']}
    replace_str = {'/s': [' s$^{-1}$', ' s-1']}

    scales = {'deg': 180.0, 'rad': np.pi, 'h': 12.0,
              'm': 1.0, 'km': 0.001, 'cm': 100.0,
              'm/s': 1.0, 'cm/s': 100.0, 'km/s': 0.001}

    # Test input and determine transformation type
    out_key = out_unit.lower()
    in_key = in_unit.lower()
    for kk in accepted_units.keys():
        if out_key in accepted_units.keys() and in_key in accepted_units.keys():
            break

        if (out_key not in accepted_units.keys()
                and out_unit.lower() in accepted_units[kk]):
            out_key = kk
        if (in_key not in accepted_units.keys()
                and in_unit.lower() in accepted_units[kk]):
            in_key = kk

    if (out_key not in accepted_units.keys()
            and in_key not in accepted_units.keys()):
        raise ValueError(''.join(['Cannot scale {:s} and '.format(in_unit),
                                  '{:s}, unknown units'.format(out_unit)]))

    if out_key not in accepted_units.keys():
        raise ValueError('Unknown output unit {:}'.format(out_unit))

    if in_key not in accepted_units.keys():
        raise ValueError('Unknown input unit {:}'.format(in_unit))

    if out_key == 'm' or out_key == 'm/s' or in_key == 'm' or in_key == 'm/s':
        if in_key != out_key:
            raise ValueError('Cannot scale {:s} and {:s}'.format(out_unit,
                                                                 in_unit))
        # Recast units as keys for the scales dictionary and ensure that
        # the format is consistent
        rkey = ''
        for rr in replace_str.keys():
            if out_key.find(rr):
                rkey = rr

        out_key = out_unit.lower()
        in_key = in_unit.lower()

        if rkey in replace_str.keys():
            for rval in replace_str[rkey]:
                out_key = out_key.replace(rval, rkey)
                in_key = in_key.replace(rval, rkey)

    unit_scale = scales[out_key] / scales[in_key]

    return unit_scale


def load_netcdf4(fnames=None, strict_meta=False, file_format=None,
                 epoch_name='Epoch', units_label='units',
                 name_label='long_name', notes_label='notes',
                 desc_label='desc', plot_label='label', axis_label='axis',
                 scale_label='scale', min_label='value_min',
                 max_label='value_max', fill_label='fill',
                 pandas_format=True):
    # unix_time=False, **kwargs):
    """Load netCDF-3/4 file produced by pysat.

    Parameters
    ----------
    fnames : string or array_like of strings
        filenames to load (default=None)
    strict_meta : boolean
        check if metadata across fnames is the same (default=False)
    file_format : string
        file_format keyword passed to netCDF4 routine
        NETCDF3_CLASSIC, NETCDF3_64BIT, NETCDF4_CLASSIC, and NETCDF4
        (default=None)
    epoch_name : string
        (default='Epoch')
    units_label : string
        keyword for unit information (default='units')
    name_label : string
        keyword for informative name label (default='long_name')
    notes_label : string
        keyword for file notes (default='notes')
    desc_label : string
        keyword for data descriptions (default='desc')
    plot_label : string
        keyword for name to use on plot labels (default='label')
    axis_label : string
        keyword for axis labels (default='axis')
    scale_label : string
        keyword for plot scaling (default='scale')
    min_label : string
        keyword for minimum in allowable value range (default='value_min')
    max_label : string
        keyword for maximum in allowable value range (defualt='value_max')
    fill_label : string
        keyword for fill values (default='fill')

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
    import pysat

    if fnames is None:
        raise ValueError("Must supply a filename/list of filenames")
    if isinstance(fnames, str):
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
    mdata = pysat.Meta(units_label=units_label,
                       name_label=name_label,
                       notes_label=notes_label,
                       desc_label=desc_label,
                       plot_label=plot_label,
                       axis_label=axis_label,
                       scale_label=scale_label,
                       min_label=min_label,
                       max_label=max_label,
                       fill_label=fill_label)

    if pandas_format:
        for fname in fnames:
            with TemporaryFileLock(fname + '.Lock', pysat.file_timeout), \
                    netCDF4.Dataset(fname, mode='r',
                                    format=file_format) as data:
                # build up dictionary with all global ncattrs
                # and add those attributes to a pysat meta object
                ncattrsList = data.ncattrs()
                for d in ncattrsList:
                    if hasattr(mdata, d):
                        mdata.__setattr__(d + '_', data.getncattr(d))
                    else:
                        mdata.__setattr__(d, data.getncattr(d))

                loadedVars = {}
                for key in data.variables.keys():
                    # load up metadata.  From here group unique
                    # dimensions and act accordingly, 1D, 2D, 3D
                    if len(data.variables[key].dimensions) == 1:
                        if pandas_format:
                            # load 1D data variable
                            # assuming basic time dimension
                            loadedVars[key] = data.variables[key][:]
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

                    if len(data.variables[key].dimensions) >= 3:
                        raise ValueError(' '.join(('pysat only supports 1D',
                                                   'and 2D data in pandas.',
                                                   'Please use xarray for',
                                                   'this data product.')))

                # we now have a list of keys that need to go into a dataframe,
                # could be more than one, collect unique dimensions for 2D keys
                for dim in set(two_d_dims):
                    # first or second dimension could be epoch
                    # Use other dimension name as variable name
                    if dim[0] == epoch_name:
                        obj_key = dim[1]
                    elif dim[1] == epoch_name:
                        obj_key = dim[0]
                    else:
                        raise KeyError('Epoch not found!')
                    # collect variable names associated with dimension
                    idx_bool = [dim == i for i in two_d_dims]
                    idx, = np.where(np.array(idx_bool))
                    obj_var_keys = []
                    clean_var_keys = []
                    for i in idx:
                        obj_var_keys.append(two_d_keys[i])
                        clean_var_keys.append(
                            two_d_keys[i].split(obj_key + '_')[-1])

                    # figure out how to index this data, it could provide its
                    # own index - or we may have to create simple integer based
                    # DataFrame access. If the dimension is stored as its own
                    # variable then use that info for index
                    if obj_key in obj_var_keys:
                        # string used to indentify dimension also in
                        # data.variables will be used as an index
                        index_key_name = obj_key
                        # if the object index uses UNIX time, process into
                        # datetime index
                        if (data.variables[obj_key].getncattr(name_label)
                                == epoch_name):
                            # name to be used in DataFrame index
                            index_name = epoch_name
                            time_index_flag = True
                        else:
                            time_index_flag = False
                            # label to be used in DataFrame index
                            index_name = \
                                data.variables[obj_key].getncattr(name_label)
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
                        for nc_key in data.variables[obj_key].ncattrs():
                            dim_meta_dict[nc_key] = \
                                data.variables[obj_key].getncattr(nc_key)
                        mdata[obj_key] = dim_meta_dict

                    # iterate over all variables with this dimension
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
                    step = len(data.variables[obj_var_keys[0]][0, :])
                    # check if there is an index we should use
                    if not (index_key_name is None):
                        # an index was found
                        time_var = loop_dict.pop(index_key_name)
                        if time_index_flag:
                            # create datetime index from data
                            time_var = pds.to_datetime(1E6 * time_var)
                        new_index = time_var
                        new_index_name = index_name
                    else:
                        # using integer indexing
                        new_index = np.arange((loop_lim * step),
                                              dtype=int) % step
                        new_index_name = 'index'
                    # load all data into frame
                    if len(loop_dict.keys()) > 1:
                        loop_frame = pds.DataFrame(loop_dict,
                                                   columns=clean_var_keys)
                        if obj_key in loop_frame:
                            del loop_frame[obj_key]
                        # break massive frame into bunch of smaller frames
                        for i in np.arange(loop_lim, dtype=int):
                            loop_list.append(loop_frame.iloc[(step * i):
                                                             (step * (i + 1)),
                                                             :])
                            loop_list[-1].index = new_index[(step * i):
                                                            (step * (i + 1))]
                            loop_list[-1].index.name = new_index_name
                    else:
                        loop_frame = pds.Series(loop_dict[clean_var_keys[0]],
                                                name=obj_var_keys[0])
                        # break massive series into bunch of smaller series
                        for i in np.arange(loop_lim, dtype=int):
                            loop_list.append(loop_frame.iloc[(step * i):
                                                             (step * (i + 1))])
                            loop_list[-1].index = new_index[(step * i):
                                                            (step * (i + 1))]
                            loop_list[-1].index.name = new_index_name

                    # add 2D object data, all based on a unique dimension within
                    # netCDF, to loaded data dictionary
                    loadedVars[obj_key] = loop_list
                    del loop_list

                # prepare dataframe index for this netcdf file
                time_var = loadedVars.pop(epoch_name)

                # convert from GPS seconds to seconds used in pandas (unix time,
                # no leap)
                # time_var = convert_gps_to_unix_seconds(time_var)
                loadedVars[epoch_name] = \
                    pds.to_datetime((1E6 * time_var).astype(int))
                running_store.append(loadedVars)
                running_idx += len(loadedVars[epoch_name])

                if strict_meta:
                    if saved_mdata is None:
                        saved_mdata = copy.deepcopy(mdata)
                    elif (mdata != saved_mdata):
                        raise ValueError(' '.join(('Metadata across filenames',
                                                   'is not the same.')))

        # combine all of the data loaded across files together
        out = []
        for item in running_store:
            out.append(pds.DataFrame.from_records(item, index=epoch_name))
        out = pds.concat(out, axis=0)
    else:
        if len(fnames) == 1:
            out = xr.open_dataset(fnames[0])
        else:
            out = xr.open_mfdataset(fnames, combine='by_coords')
        for key in out.variables.keys():
            # Copy the variable attributes from the data object to the metadata
            meta_dict = {}
            for nc_key in out.variables[key].attrs.keys():
                meta_dict[nc_key] = out.variables[key].attrs[nc_key]
            mdata[key] = meta_dict
            # Remove variable attributes from the data object
            out.variables[key].attrs = {}
        # Copy the file attributes from the data object to the metadata
        for d in out.attrs.keys():
            if hasattr(mdata, d):
                mdata.__setattr__(d + '_', out.attrs[d])
            else:
                mdata.__setattr__(d, out.attrs[d])
        # Remove attributes from the data object
        out.attrs = {}

    return out, mdata


class NetworkLock(Lock):
    def __init__(self, *args, **kwargs):
        """Lock manager compatible with networked file systems
        """

        super(NetworkLock, self).__init__(*args, **kwargs)

    def release(self):
        '''Releases the Lock so the file system

        From portalocker docs:
          On some networked filesystems it might be needed to force
          a `os.fsync()` before closing the file so it's
          actually written before another client reads the file.

        '''

        self.fh.flush()
        os.fsync(self.fh.fileno())

        super(NetworkLock, self).release()
