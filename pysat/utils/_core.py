#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import datetime as dt
import importlib
import netCDF4
import numpy as np
import os
import pandas as pds
from portalocker import Lock
import xarray as xr

import pysat


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


def listify(iterable):
    """Returns a flattened list of iterable if not already a list

    Parameters
    ----------
    iterable : iter-like
        An iterable object that will be wrapped within a list

    Returns
    -------
    list
        An enclosing 1-D list of iterable if not already a list

    """

    arr_iter = np.asarray(iterable)
    if arr_iter.shape == ():
        list_iter = [arr_iter.tolist()]
    elif arr_iter.shape[0] == 0:
        list_iter = arr_iter.tolist()
    else:
        list_iter = arr_iter.flatten().tolist()

    return list_iter


def load_netcdf4(fnames=None, strict_meta=False, file_format=None,
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
    fnames : string, array_like of strings, or NoneType
        Filename(s) to load, will fail if None (default=None)
    strict_meta : boolean
        Flag that checks if metadata across fnames is the same if True
        (default=False)
    file_format : string or NoneType
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        If None, defaults to 'NETCDF4'. (default=None)
    epoch_name : string
        Data key for time variable (default='Epoch')
    pandas_format : bool
        Flag specifying if data is stored in a pandas DataFrame (True) or
        xarray Dataset (False). (default=False)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'plot': ('plot_label', str), 'axis': ('axis', str),
        'scale': ('scale', str), 'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})

    Returns
    --------
    out : pandas.DataFrame
        DataFrame output
    meta : pysat.Meta
        Meta data

    Raises
    ------
    ValueError
        If kwargs that should be args are not set on instantiation.

    """

    if fnames is None:
        raise ValueError("Must supply a filename/list of filenames")
    fnames = listify(fnames)

    if file_format is None:
        file_format = 'NETCDF4'
    else:
        file_format = file_format.upper()

    saved_meta = None
    running_idx = 0
    running_store = []
    two_d_keys = []
    two_d_dims = []
    meta = pysat.Meta(labels=labels)

    if pandas_format:
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
                            meta_dict[nc_key] = \
                                data.variables[key].getncattr(nc_key)
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
                    # collect variable names associated with dimension
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
                        # string used to indentify dimension also in
                        # data.variables will be used as an index
                        index_key_name = obj_key
                        # if the object index uses UNIX time, process into
                        # datetime index
                        if data.variables[obj_key].getncattr(
                                meta.labels.name) == epoch_name:
                            # Name to be used in DataFrame index
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

                    for key, clean_key in zip(obj_var_keys, clean_var_keys):
                        # store attributes in metadata, exept for dim name
                        meta_dict = {}
                        for nc_key in data.variables[key].ncattrs():
                            meta_dict[nc_key] = \
                                data.variables[key].getncattr(nc_key)
                        dim_meta_data[clean_key] = meta_dict

                    dim_meta_dict = {'meta': dim_meta_data}
                    if index_key_name is not None:
                        # Add top level meta
                        for nc_key in data.variables[obj_key].ncattrs():
                            dim_meta_dict[nc_key] = \
                                data.variables[obj_key].getncattr(nc_key)
                        meta[obj_key] = dim_meta_dict

                    # Iterate over all variables with this dimension
                    # data storage, whole shebang
                    loop_dict = {}

                    # List holds a series of slices, parsed from dict above
                    loop_list = []
                    for key, clean_key in zip(obj_var_keys, clean_var_keys):
                        # data
                        loop_dict[clean_key] = \
                            data.variables[key][:, :].flatten(order='C')

                    # Number of values in time
                    loop_lim = data.variables[obj_var_keys[0]].shape[0]

                    # Number of values per time
                    step = len(data.variables[obj_var_keys[0]][0, :])

                    # Check if there is an index we should use
                    if not (index_key_name is None):
                        # An index was found
                        time_var = loop_dict.pop(index_key_name)
                        if time_index_flag:
                            # Create datetime index from data
                            time_var = pds.to_datetime(1.0E6 * time_var)
                        new_index = time_var
                        new_index_name = index_name
                    else:
                        # Using integer indexing
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
        if len(fnames) == 1:
            out = xr.open_dataset(fnames[0])
        else:
            out = xr.open_mfdataset(fnames, combine='by_coords')
        for key in out.variables.keys():
            # Copy the variable attributes from the data object to the metadata
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


def fmt_output_in_cols(out_strs, ncols=3, max_num=6, lpad=None):
    """ Format a string with desired output values in columns

    Parameters
    ----------
    out_strs : array-like
        Array like object containing strings to print
    ncols : int
        Number of columns to print (default=3)
    max_num : int
        Maximum number of out_strs members to print.  Best display achieved if
        this number is divisable by 2 and ncols (default=6)
    lpad : int or NoneType
        Left padding or None to use length of longest string + 1 (default=None)

    Returns
    -------
    output : string
        String with desired data formatted in columns

    """
    output = ""

    # Ensure output strings are array-like
    out_strs = np.asarray(out_strs)
    if out_strs.shape == ():
        out_strs = np.array([out_strs])

    # If there are more data values than desired, keep the first and last
    out_len = len(out_strs)
    middle = -1
    if out_len > max_num:
        nhalf = np.int64(max_num / 2)
        middle = nhalf // ncols
        if middle == 0:
            middle = 1
        nsel = [0] if nhalf == 0 else [i for i in range(nhalf)]
        nsel.extend([i for i in np.arange(out_len - nhalf, out_len)])
    else:
        nsel = np.arange(0, out_len)
    sel_len = len(nsel)

    # If desired, determine the left padding spacing
    if lpad is None:
        lpad = max([len(ostr) for ostr in out_strs[nsel]]) + 1

    # Print out the groups of variables in rows
    num = sel_len // ncols
    for i in range(num):
        # If data has been cut, indicate this with an ellipses row
        if i == middle:
            middle = -1
            output += "...".center(lpad * ncols) + '\n'

        # Print out data for each selected column in this row
        for j in range(ncols):
            output += out_strs[nsel][ncols * i + j].ljust(lpad)
        output += '\n'

    # Print out remaining variables one at a time on a single line
    extra_cols = sel_len - ncols * num
    if extra_cols > 0:
        for i in range(extra_cols):
            if middle >= 0:
                if i == 0 and num > 0:
                    output += "...".center(lpad * ncols) + '\n'
                elif num == 0 and i == nhalf:
                    output += "...".center(lpad if lpad > 4 else 4)
            output += out_strs[nsel][i + ncols * num].ljust(lpad)
        output += '\n'

    return output


def generate_instrument_list(inst_loc, user_info=None):
    """Iterate through and classify instruments in a given subpackage.


    Parameters
    ----------
    inst_loc : python subpackage
        The location of the instrument subpackage to test, e.g.,
        'pysat.instruments'
    user_info : dict or NoneType
        Nested dictionary with user and password info for instrument module
        name.  If None, no user or password is assumed. (default=None)
        EX: user_info = {'jro_isr': {'user': 'myname', 'password': 'email'}}

    Returns
    -------
    output : dict
        Dictionary with keys 'names', 'download', 'no_download' that contain
        lists with different information for each key:
        'names' - list of platform_name combinations
        'download' - dict containing 'inst_module', 'tag', and 'inst_id' for
        instruments with download routines
        'no_download' - dict containing 'inst_module', 'tag', and 'inst_id' for
        instruments without download routines

    Note
    ----
    This routine currently supports classification of instruments for unit
    tests both in the core package and in seperate instrument packages that
    use pysat.

    """

    instrument_names = inst_loc.__all__
    instrument_download = []
    instrument_no_download = []

    # Look through list of available instrument modules in the given location
    for inst_module in instrument_names:
        try:
            module = importlib.import_module(''.join(('.', inst_module)),
                                             package=inst_loc.__name__)
        except ImportError:
            # If this can't be imported, we can't pull out the info for the
            # download / no_download tests.  Leaving in basic tests for all
            # instruments, but skipping the rest.  The import error will be
            # caught as part of the pytest.mark.all_inst tests in InstTestClass
            pass
        else:
            # try to grab basic information about the module so we
            # can iterate over all of the options
            try:
                info = module._test_dates
            except AttributeError:
                # If a module does not have a test date, add it anyway for
                # other tests.  This will be caught later by
                # InstTestClass.test_instrument_test_dates
                info = {}
                info[''] = {'': dt.datetime(2009, 1, 1)}
                module._test_dates = info
            for inst_id in info.keys():
                for tag in info[inst_id].keys():
                    inst_dict = {'inst_module': module, 'tag': tag,
                                 'inst_id': inst_id}
                    # Add username and password info if needed
                    if user_info and inst_module in user_info:
                        inst_dict['user_info'] = user_info[inst_module]
                    # Initialize instrument so that pysat can generate skip
                    # flags where appropriate
                    inst = pysat.Instrument(inst_module=module,
                                            tag=tag,
                                            inst_id=inst_id,
                                            temporary_file_list=True)
                    travis_skip = ((os.environ.get('TRAVIS') == 'true')
                                   and not inst._test_download_travis)
                    if inst._test_download:
                        if not travis_skip:
                            instrument_download.append(inst_dict)
                    elif not inst._password_req:
                        # we don't want to test download for this combo
                        # But we do want to test the download warnings
                        # for instruments without a password requirement
                        instrument_no_download.append(inst_dict)

    output = {'names': instrument_names,
              'download': instrument_download,
              'no_download': instrument_no_download}

    return output


def available_instruments(inst_loc=None):
    """Obtain basic information about instruments in a given subpackage.

    Parameters
    ----------
    inst_loc : python subpackage or NoneType
        The location of the instrument subpackage (e.g., pysat.instruments)
        or None to list all registered instruments (default=None)

    Returns
    -------
    inst_info : dict
        Nested dictionary with 'platform', 'name', 'inst_module',
        'inst_ids_tags', 'inst_id', and 'tag' with the tag descriptions given
        as the value for each unique dictionary combination.

    """

    def get_inst_id_dict(inst_module_name):
        try:
            module = importlib.import_module(inst_module_name)
            inst_ids = {inst_id: {tag: module.tags[tag]
                                  for tag in module.inst_ids[inst_id]}
                        for inst_id in module.inst_ids.keys()}
        except ImportError as ierr:
            inst_ids = {'ERROR': {'ERROR': str(ierr)}}
        return inst_ids

    # Get user modules dictionary.
    user_modules = pysat.params['user_modules']

    if inst_loc is None:
        # Access the registered instruments
        inst_info = dict()

        # Cycle through each instrument platform and name to reshape the
        # dictionary and get the instrument tags and inst_ids
        for platform in user_modules.keys():
            inst_info[platform] = dict()
            for name in user_modules[platform].keys():
                inst_ids = get_inst_id_dict(user_modules[platform][name])
                inst_info[platform][name] = {'inst_module':
                                             user_modules[platform][name],
                                             'inst_ids_tags': inst_ids}
    else:
        # Access the instruments in the specified module
        inst_mods = inst_loc.__all__
        inst_info = dict()

        # Cycle through the available instrument modules
        for inst_mod in inst_mods:
            # Get the platform, name, and instrument module name
            platform = inst_mod.split('_')[0]
            name = '_'.join(inst_mod.split('_')[1:])
            mod_name = '.'.join([inst_loc.__name__, inst_mod])

            # Initialize the dictionary for this platform and name
            if platform not in inst_info.keys():
                inst_info[platform] = dict()

            # Finalize the dictionary
            inst_info[platform][name] = {
                'inst_module': mod_name,
                'inst_ids_tags': get_inst_id_dict(mod_name)}

    return inst_info


def display_available_instruments(inst_loc=None, show_inst_mod=None,
                                  show_platform_name=None):
    """Display basic information about instruments in a given subpackage.

    Parameters
    ----------
    inst_loc : python subpackage or NoneType
        The location of the instrument subpackage (e.g., pysat.instruments)
        or None to list all registered instruments (default=None)
    show_inst_mod : boolean or NoneType
        Displays the instrument module if True, does not include it if False,
        and reverts to standard display based on inst_loc type if None.
        (default=None)
    show_platform_name : boolean or NoneType
        Displays the platform and name if True, does not include it if False,
        and reverts to standard display based on inst_loc type if None.
        (default=None)

    Note
    ----
    Prints to standard out, a user-friendly interface for availabe_instruments.
    Defaults to including the instrument module and not the platform/name values
    if inst_loc is an instrument module and to including the platform/name
    values and not the instrument module if inst_loc is None (listing the
    registered instruments).

    """

    inst_info = available_instruments(inst_loc)

    if show_platform_name is None and inst_loc is None:
        show_platform_name = True
        plat_keys = sorted([platform for platform in inst_info.keys()])
    else:
        plat_keys = inst_info.keys()

    if show_inst_mod is None and inst_loc is not None:
        show_inst_mod = True

    if show_platform_name:
        header = "Platform   Name   "
    else:
        header = ""

    if show_inst_mod:
        header = "{:s}Instrument_Module".format(header)

    header = "{:s}      [Tag   Inst_ID]  Description".format(header)
    print(header)
    print("-" * len(header))
    for platform in plat_keys:
        for name in inst_info[platform].keys():
            mod_str = ""
            for inst_id in inst_info[platform][name]['inst_ids_tags'].keys():
                for tag in inst_info[platform][name][
                        'inst_ids_tags'][inst_id].keys():
                    if len(mod_str) == 0:
                        if show_platform_name:
                            mod_str = "".join([platform.__repr__(), " ",
                                               name.__repr__(), " "])
                        if show_inst_mod:
                            mod_str = "{:s}{:s}".format(
                                mod_str,
                                inst_info[platform][name]['inst_module'])
                    else:
                        mod_str = " " * len(mod_str)

                    print("".join([mod_str, " [", tag.__repr__(), " ",
                                   inst_id.__repr__(), "]  ",
                                   inst_info[platform][name]['inst_ids_tags'][
                                       inst_id][tag]]))
    return


class NetworkLock(Lock):
    def __init__(self, *args, **kwargs):
        """Lock manager compatible with networked file systems.

        Parameters
        ----------
        *args : list reference
            References a list of input arguments
        **kwargs : dict reference
            References a dict of input keyword argument

        Note
        ----
        See portalocker.utils.Lock for more details
        (:class:`portalocker.utils.Lock`)

        Example
        -------
        ::

            from pysat.utils import NetworkLock

            with NetworkLock(file_to_be_written, 'w') as locked_file:
                locked_file.write('content')

        """

        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
            del kwargs['timeout']
        else:
            timeout = pysat.params['file_timeout']

        super(NetworkLock, self).__init__(timeout=timeout,
                                          *args, **kwargs)

    def release(self):
        """Releases the Lock so the file system

        From portalocker docs:
          On some networked filesystems it might be needed to force
          a `os.fsync()` before closing the file so it's
          actually written before another client reads the file.

        """

        self.fh.flush()
        try:
            # In case of network file system
            os.fsync(self.fh.fileno())
        except OSError:
            # Not a network file system
            pass

        super(NetworkLock, self).release()
