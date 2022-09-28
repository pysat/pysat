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
import warnings
import xarray as xr

import pysat


def scale_units(out_unit, in_unit):
    """Determine the scaling factor between two units.

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
    hours ('h', 'hr', 'hrs', 'hour', 'hours'), lengths ('m', 'km', 'cm'),
    volumes ('m-3', 'cm-3', '/cc', 'n/cc', 'km-3', 'm$^{-3}$', 'cm$^{-3}$',
    'km$^{-3}$'), and speeds ('m/s', 'cm/s', 'km/s', 'm s$^{-1}$',
    'cm s$^{-1}$', 'km s$^{-1}$', 'm s-1', 'cm s-1', 'km s-1').
    Can convert between degrees, radians, and hours or different lengths,
    volumes, or speeds.

    Examples
    --------
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
                              'km s-1'],
                      'm-3': ['m-3', 'cm-3', 'km-3', 'n/cc', '/cc', '#/cc',
                              '#/cm3', '#/cm^3', '#/km3', '#/km^3', '#/m3',
                              '#/m^3', 'm$^{-3}$', 'cm$^{-3}$', 'km$^{-3}$',
                              'cm^-3', 'm^-3', 'km^-3', 'cm^{-3}', 'm^{-3}',
                              'km^{-3}']}
    replace_str = {'/s': [' s$^{-1}$', ' s-1'], '': ['#'], 'km-3': ['/km^3'],
                   '-3': ['$^{-3}$', '^{-3}', '^-3'],
                   'cm-3': ['n/cc', '/cc', '/cm^3'], 'm-3': ['/m^3']}

    scales = {'deg': 180.0, 'rad': np.pi, 'h': 12.0,
              'm': 1.0, 'km': 0.001, 'cm': 100.0,
              'm/s': 1.0, 'cm/s': 100.0, 'km/s': 0.001,
              'm-3': 1.0, 'cm-3': 1.0e6, 'km-3': 1.0e-9}

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

    if out_key in ['m', 'm/s', 'm-3'] or in_key in ['m', 'm/s', 'm-3']:
        if in_key != out_key:
            raise ValueError('Cannot scale {:s} and {:s}'.format(out_unit,
                                                                 in_unit))

        # Recast units as keys for the scales dictionary and ensure that
        # the format is consistent
        rkeys = []
        for rr in replace_str.keys():
            if out_key.find(rr) >= 0 or rr.find(out_key) >= 0:
                rkeys.append(rr)

        # Redefine keys to find correct values for scaling
        out_key = out_unit.lower()
        in_key = in_unit.lower()

        for rkey in rkeys:
            for rval in replace_str[rkey]:
                out_key = out_key.replace(rval, rkey)
                in_key = in_key.replace(rval, rkey)

    # Calculate the scaling factor
    unit_scale = scales[out_key] / scales[in_key]

    return unit_scale


def listify(iterable):
    """Produce a flattened list of items from input that may not be iterable.

    Parameters
    ----------
    iterable : iter-like
        An iterable object that will be wrapped within a list

    Returns
    -------
    list
        An enclosing 1-D list of iterable if not already a list

    Note
    ----
    Does not accept dict_keys or dict_values as input.

    """

    # Cast as an array-like object
    arr_iter = np.asarray(iterable)

    # Treat output differently based on the array shape
    if arr_iter.shape == ():
        list_iter = [arr_iter.tolist()]
    elif arr_iter.shape[0] == 0:
        list_iter = arr_iter.tolist()
    else:
        list_iter = arr_iter.flatten().tolist()

    return list_iter


def stringify(strlike):
    """Convert input into a str type.

    Parameters
    ----------
    strlike: str or bytes
        Input values in str or byte form

    Returns
    -------
    strlike: str or input type
        If input is not string-like then the input type is retained.

    """

    if isinstance(strlike, bytes):
        return strlike.decode('utf-8')
    return strlike


def load_netcdf4(fnames=None, strict_meta=False, file_format='NETCDF4',
                 epoch_name='Epoch', epoch_unit='ms', epoch_origin='unix',
                 pandas_format=True, decode_timedelta=False,
                 labels={'units': ('units', str), 'name': ('long_name', str),
                         'notes': ('notes', str), 'desc': ('desc', str),
                         'min_val': ('value_min', np.float64),
                         'max_val': ('value_max', np.float64),
                         'fill_val': ('fill', np.float64)}):
    """Load netCDF-3/4 file produced by pysat.

    .. deprecated:: 3.0.2
       Function moved to `pysat.utils.io.load_netcdf`, this wrapper will be
       removed in the 3.2.0+ release.
       No longer allow non-string file formats in the 3.2.0+ release.

    Parameters
    ----------
    fnames : str, array_like, or NoneType
        Filename(s) to load, will fail if None (default=None)
    strict_meta : bool
        Flag that checks if metadata across fnames is the same if True
        (default=False)
    file_format : str
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        (default='NETCDF4')
    epoch_name : str
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
    pandas_format : bool
        Flag specifying if data is stored in a pandas DataFrame (True) or
        xarray Dataset (False). (default=False)
    decode_timedelta : bool
        Used for xarray datasets.  If True, variables with unit attributes that
        are 'timelike' ('hours', 'minutes', etc) are converted to
        `np.timedelta64`. (default=False)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})

    Returns
    -------
    data : pandas.DataFrame or xarray.Dataset
        Class holding file data
    meta : pysat.Meta
        Class holding file meta data

    Raises
    ------
    ValueError
        If kwargs that should be args are not set on instantiation.
    KeyError
        If epoch/time dimension could not be identified.

    """
    warnings.warn("".join(["function moved to `pysat.utils.io`, deprecated ",
                           "wrapper will be removed in pysat 3.2.0+"]),
                  DeprecationWarning, stacklevel=2)

    if fnames is None:
        warnings.warn("".join(["`fnames` as a kwarg has been deprecated, must ",
                               "supply a string or list of strings in 3.2.0+"]),
                      DeprecationWarning, stacklevel=2)
        raise ValueError("Must supply a filename/list of filenames")

    if file_format is None:
        warnings.warn("".join(["`file_format` must be a string value in ",
                               "3.2.0+, instead of None use 'NETCDF4' for ",
                               "same behavior."]),
                      DeprecationWarning, stacklevel=2)
        file_format = 'NETCDF4'

    data, meta = pysat.utils.io.load_netcdf(fnames, strict_meta=strict_meta,
                                            file_format=file_format,
                                            epoch_name=epoch_name,
                                            epoch_unit=epoch_unit,
                                            epoch_origin=epoch_origin,
                                            pandas_format=pandas_format,
                                            decode_timedelta=decode_timedelta,
                                            labels=labels)

    return data, meta


def get_mapped_value(value, mapper):
    """Adjust value using mapping dict or function.

    Parameters
    ----------
    value : str
        MetaData variable name to be adjusted
    mapper : dict or function
        Dictionary with old names as keys and new names as variables or
        a function to apply to all names

    Returns
    -------
    mapped_val : str or NoneType
        Adjusted MetaData variable name or NoneType if input value
        should stay the same

    """
    if isinstance(mapper, dict):
        if value in mapper.keys():
            mapped_val = mapper[value]
        else:
            mapped_val = None
    else:
        mapped_val = mapper(value)

    return mapped_val


def fmt_output_in_cols(out_strs, ncols=3, max_num=6, lpad=None):
    """Format a string with desired output values in columns.

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
    output : str
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
    instrument_optional_load = []
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
            for iid in info.keys():
                for tag in info[iid].keys():
                    in_dict = {'inst_module': module, 'tag': tag,
                               'inst_id': iid}
                    # Add username and password info if needed
                    if user_info and inst_module in user_info:
                        in_dict['user_info'] = user_info[inst_module]
                    # Initialize instrument so that pysat can generate skip
                    # flags where appropriate
                    inst = pysat.Instrument(inst_module=module,
                                            tag=tag,
                                            inst_id=iid,
                                            temporary_file_list=True)
                    # Set flag to skip tests on a CI environment.
                    # To test CI config on a local system, change first
                    # condition to (os.environ.get('CI') is None).
                    ci_skip = ((os.environ.get('CI') == 'true')
                               and not inst._test_download_ci)
                    # Some instruments will be skipped in CI but run
                    # locally. Check for this flag.
                    if not ci_skip:
                        # Check if instrument is configured for download tests.
                        if inst._test_download:
                            instrument_download.append(in_dict)
                            if hasattr(module, '_test_load_opt'):
                                # Add optional load tests
                                try:
                                    kw_list = module._test_load_opt[iid][tag]
                                    kw_list = pysat.utils.listify(kw_list)
                                    for kwargs in kw_list:
                                        in_dict['kwargs'] = kwargs
                                        instrument_optional_load.append(in_dict)
                                except KeyError:
                                    # Option does not exist for tag/inst_id
                                    # combo
                                    pass

                        elif not inst._password_req:
                            # We don't want to test download for this combo, but
                            # we do want to test the download warnings for
                            # instruments without a password requirement
                            instrument_no_download.append(in_dict)

    # load options requires all downloaded instruments plus additional options
    output = {'names': instrument_names,
              'download': instrument_download,
              'load_options': instrument_download + instrument_optional_load,
              'no_download': instrument_no_download}

    return output


def display_instrument_stats(inst_locs=None):
    """Display supported instrument stats.

    Parameters
    ----------
    inst_locs : list of packages
        List of instrument library modules to inspect for pysat support.
        If None, report on default pysat package.  (default=None)

    """

    if inst_locs is None:
        inst_locs = [pysat.instruments]

    num_dl = 0
    num_nodl = 0
    for inst_loc in inst_locs:
        instruments = generate_instrument_list(inst_loc=inst_loc)
        num_dl += len(instruments['download'])
        num_nodl += len(instruments['no_download'])

    print("\n{:} supported data products with download access".format(num_dl))
    print("{:} supported data products with local access".format(num_nodl))
    return


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
    """Unit tests for NetworkLock manager."""

    def __init__(self, *args, **kwargs):
        """Initialize lock manager compatible with networked file systems.

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

        Examples
        --------
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
        """Release the Lock from the file system.

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
