#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
import copy
import datetime as dt
import errno
import functools
import importlib
import inspect
import os
import sys
import types
import warnings
import weakref

import netCDF4
import numpy as np
import pandas as pds
import xarray as xr

import pysat
from pysat import utils
from pysat import logger

from pysat.utils.time import filter_datetime_input


class Instrument(object):
    """Download, load, manage, modify and analyze science data.

    Parameters
    ----------
    platform : string
        name of instrument platform (default='')
    name : string
        name of instrument (default='')
    tag : string
        identifies particular subset of instrument data
        (default='')
    inst_id : string
        Secondary level of identification, such as spacecraft within a
        constellation platform (default='')
    clean_level : str or NoneType
        Level of data quality. If not provided, will default to the
        setting in `pysat.params['clean_level']` (default=None)
    pad : pandas.DateOffset, dictionary, or NoneType
        Length of time to pad the begining and end of loaded data for
        time-series processing. Extra data is removed after applying all
        custom functions. Dictionary, if supplied, is simply passed to
        pandas DateOffset. (default=None)
    orbit_info : dict
        Orbit information, {'index': index, 'kind': kind, 'period': period}.
        See pysat.Orbits for more information.  (default={})
    inst_module : module or NoneType
        Provide instrument module directly, takes precedence over platform/name
        (default=None)
    update_files : boolean or Nonetype
        If True, immediately query filesystem for instrument files and store.
        If False, the local files are presumed to be the same. By default,
        this setting will be obtained from `pysat.params` (default=None)
    temporary_file_list : boolean
        If true, the list of Instrument files will not be written to disk.
        Prevents a race condition when running multiple pysat processes.
        (default=False)
    strict_time_flag : boolean
        If true, pysat will check data to ensure times are unique and
        monotonically increasing. (default=True)
    directory_format : string, function, or NoneType
        Directory naming structure in string format. Variables such as platform,
        name, and tag will be filled in as needed using python string
        formatting. The default directory structure, which is used if None is
        specified, is '{platform}/{name}/{tag}'. If a function is provided, it
        must take `tag` and `inst_id` as arguments and return an appropriate
        string. (default=None)
    file_format : str or NoneType
        File naming structure in string format.  Variables such as year,
        month, and inst_id will be filled in as needed using python string
        formatting.  The default file format structure is supplied in the
        instrument list_files routine. (default=None)
    ignore_empty_files : boolean
        if True, the list of files found will be checked to
        ensure the filesizes are greater than zero. Empty files are
        removed from the stored list of files. (default=False)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', float),
        'max_val': ('value_max', float), 'fill_val': ('fill', float)})

    Attributes
    ----------
    bounds : (datetime/filename/None, datetime/filename/None)
        bounds for loading data, supply array_like for a season with gaps.
        Users may provide as a tuple or tuple of lists, but the attribute is
        stored as a tuple of lists for consistency
    custom_functions : list
        List of functions to be applied by instrument nano-kernel
    custom_args : list
        List of lists containing arguments to be passed to particular
        custom function
    custom_kwargs : list
        List of dictionaries with keywords and values to be passed
        to a custom function
    data : pandas.DataFrame or xarray.Dataset
        loaded science data
    date : dt.datetime
        date for loaded data
    yr : int
        year for loaded data
    doy : int
        day of year for loaded data
    files : pysat.Files
        interface to instrument files
    kwargs : dictionary
        keyword arguments passed to the standard Instrument routines
    meta_labels : dict
        Dict containing defaults for new Meta data labels
    meta : pysat.Meta
        interface to instrument metadata, similar to netCDF 1.6
    orbits : pysat.Orbits
        interface to extracting data orbit-by-orbit

    Note
    ----
    pysat attempts to load the module platform_name.py located in the
    pysat/instruments directory. This module provides the underlying
    functionality to download, load, and clean instrument data. Alternatively,
    the module may be supplied directly using keyword inst_module.

    Examples
    --------
    ::

        # 1-second mag field data
        vefi = pysat.Instrument(platform='cnofs',
                                name='vefi',
                                tag='dc_b',
                                clean_level='clean')
        start = dt.datetime(2009,1,1)
        stop = dt.datetime(2009,1,2)
        vefi.download(start, stop)
        vefi.load(date=start)
        print(vefi['dB_mer'])
        print(vefi.meta['db_mer'])

        # 1-second thermal plasma parameters
        ivm = pysat.Instrument(platform='cnofs',
                               name='ivm',
                               tag='',
                               clean_level='clean')
        ivm.download(start,stop)
        ivm.load(2009,1)
        print(ivm['ionVelmeridional'])

        # Ionosphere profiles from GPS occultation. Enable binning profile
        # data using a constant step-size. Feature provided by the underlying
        # COSMIC support code.
        cosmic = pysat.Instrument('cosmic',
                                  'gps',
                                  'ionprf',
                                  altitude_bin=3)
        cosmic.download(start, stop, user=user, password=password)
        cosmic.load(date=start)

        # Nano-kernel functionality enables instrument objects that are
        # 'set and forget'. The functions are always run whenever
        # the instrument load routine is called so instrument objects may
        # be passed safely to other routines and the data will always
        # be processed appropriately.

        # Define custom function to modify Instrument in place.
        def custom_func(inst, opt_param1=False, opt_param2=False):
            # perform calculations and store in new_data
            inst['new_data'] = new_data
            return

        inst = pysat.Instrument('pysat', 'testing')
        inst.custom_attach(custom_func, kwargs={'opt_param1': True})

        # Custom methods are applied to data when loaded.
        inst.load(date=date)

        print(inst['new_data2'])

        # Custom methods may also be attached at instantiation.
        # Create a dictionary for each custom method and associated inputs
        custom_func_1 = {'function': custom_func,
                         'kwargs': {'opt_param1': True}}
        custom_func_2 = {'function': custom_func, 'args'=[True, False]}
        custom_func_3 = {'function': custom_func, 'at_pos'=0,
                         'kwargs': {'opt_param2': True}}

        # Combine all dicts into a list in order of application and execution,
        # although this can be modified by specifying 'at_pos'. The actual
        # order these functions will run is: 3, 1, 2
        custom = [custom_func_1, custom_func_2, custom_func_3]

        # Instantiate pysat.Instrument
        inst = pysat.Instrument(platform, name, inst_id=inst_id, tag=tag,
                                custom=custom)

    """

    # -----------------------------------------------------------------------
    # Define all magic methods

    def __init__(self, platform=None, name=None, tag=None, inst_id=None,
                 clean_level=None, update_files=None, pad=None,
                 orbit_info=None, inst_module=None, directory_format=None,
                 file_format=None, temporary_file_list=False,
                 strict_time_flag=True, ignore_empty_files=False,
                 labels={'units': ('units', str), 'name': ('long_name', str),
                         'notes': ('notes', str), 'desc': ('desc', str),
                         'min_val': ('value_min', float),
                         'max_val': ('value_max', float),
                         'fill_val': ('fill', float)}, custom=None, **kwargs):

        # Set default tag and inst_id
        self.tag = tag.lower() if tag is not None else ''
        self.inst_id = inst_id.lower() if inst_id is not None else ''
        self.inst_module = inst_module

        if self.inst_module is None:
            # Use strings to look up module name
            if isinstance(platform, str) and isinstance(name, str):
                self.platform = platform.lower()
                self.name = name.lower()

                # Look to module for instrument functions and defaults
                self._assign_attrs(by_name=True)
            elif (platform is None) and (name is None):
                # Creating "empty" Instrument object with this path
                self.name = ''
                self.platform = ''
                self._assign_attrs()
            else:
                raise ValueError(' '.join(('Inputs platform and name must both',
                                           'be strings, or both None.')))
        else:
            # User has provided a module, assign platform and name here
            for iattr in ['platform', 'name']:
                if hasattr(self.inst_module, iattr):
                    setattr(self, iattr,
                            getattr(self.inst_module, iattr).lower())
                else:
                    raise AttributeError(
                        ''.join(['Supplied module {:}'.format(self.inst_module),
                                 ' is missing required attribute: ', iattr]))

            # Look to supplied module for instrument functions and non-default
            # attribute values
            self._assign_attrs(inst_module=self.inst_module)

        # More reasonable defaults for optional parameters
        self.clean_level = (clean_level.lower() if clean_level is not None
                            else pysat.params['clean_level'])

        # Assign strict_time_flag
        self.strict_time_flag = strict_time_flag

        # Assign directory format information, which tells pysat how to look in
        # sub-directories for files.
        if directory_format is not None:
            # assign_func sets some instrument defaults, but user inputs
            # take precedence
            self.directory_format = directory_format

        # The value provided by the user or the Instrument may be either
        # a string or a function
        if self.directory_format is not None:
            if callable(self.directory_format):
                self.directory_format = self.directory_format(tag, inst_id)
        else:
            # Value not provided by user or developer. Use stored value.
            self.directory_format = pysat.params['directory_format']

        # Assign the file format string, if provided by user. This enables
        # users to temporarily put in a new string template for files that may
        # not match the standard names obtained from the download routine.
        if file_format is not None:
            self.file_format = file_format

        # Check to make sure value is reasonable
        if self.file_format is not None:
            # Check if it is an iterable string.  If it isn't formatted
            # properly, raise a ValueError
            if(not isinstance(self.file_format, str)
               or (self.file_format.find("{") < 0)
               or (self.file_format.find("}") < 0)):
                raise ValueError(''.join(['file format set to default, ',
                                          'supplied string must be iterable ',
                                          '[{:}]'.format(self.file_format)]))

        # set up empty data and metadata
        # check if pandas or xarray format
        if self.pandas_format:
            self._null_data = pds.DataFrame(None)
            self._data_library = pds.DataFrame
        else:
            self._null_data = xr.Dataset(None)
            self._data_library = xr.Dataset

        # assign null data for user selected data type
        self.data = self._null_data.copy()

        # Create Meta instance with appropriate labels.  Meta class methods will
        # use Instrument definition of MetaLabels over the Metadata declaration
        self.meta_labels = labels
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta.mutable = False

        # Nano-kernel processing variables. Feature processes data on each load.
        self.custom_functions = []
        self.custom_args = []
        self.custom_kwargs = []

        # Process provided user input for custom methods, if provided.
        if custom is not None:
            # Required keys.
            req_key = 'function'

            for cust in custom:
                # Check if required keys present in input.
                if req_key not in cust:
                    estr = ''.join(('Input dict to custom is missing the ',
                                    'required key: ', req_key))
                    raise ValueError(estr)

                # Set the custom kwargs
                cust_kwargs = dict()
                for ckey in cust.keys():
                    if ckey != req_key:
                        cust_kwargs[ckey] = cust[ckey]

                # Inputs have been checked, add to Instrument object.
                self.custom_attach(cust['function'], **cust_kwargs)

        # Create arrays to store data around loaded day. This enables padding
        # across day breaks with minimal loads
        self._next_data = self._null_data.copy()
        self._next_data_track = []
        self._prev_data = self._null_data.copy()
        self._prev_data_track = []
        self._curr_data = self._null_data.copy()

        # Initialize the padding
        if isinstance(pad, (dt.timedelta, pds.DateOffset)) or pad is None:
            self.pad = pad
        elif isinstance(pad, dict):
            self.pad = pds.DateOffset(**pad)
        else:
            raise ValueError(' '.join(['pad must be a dict, NoneType,',
                                       'datetime.timedelta, or',
                                       'pandas.DateOffset instance.']))

        # Store kwargs, passed to standard routines first
        self.kwargs = {}
        self.kwargs_supported = {}
        saved_keys = []
        partial_func = ['list_files', 'list_remote_files', 'download',
                        'preprocess', 'clean', 'load', 'init']
        # Expected function keywords
        exp_keys = ['list_files', 'load', 'preprocess', 'download',
                    'list_remote_files', 'clean', 'init']
        for fkey in exp_keys:
            func_name = _kwargs_keys_to_func_name(fkey)
            func = getattr(self, func_name)

            # Get dict of supported keywords and values
            default_kwargs = _get_supported_keywords(func)

            # Check if kwargs are in list
            good_kwargs = [ckey for ckey in kwargs.keys()
                           if ckey in default_kwargs]

            # Store appropriate user supplied keywords for this function
            self.kwargs[fkey] = {gkey: kwargs[gkey] for gkey in good_kwargs}

            # Store all supported keywords for user edification
            self.kwargs_supported[fkey] = default_kwargs

            # Keep a copy of user provided values
            user_values = copy.deepcopy(self.kwargs[fkey])

            # Add in defaults if not already present
            for dkey in default_kwargs.keys():
                if dkey not in good_kwargs:
                    self.kwargs[fkey][dkey] = default_kwargs[dkey]

            # Determine the number of kwargs in this function
            fkwargs = [gkey for gkey in self.kwargs[fkey].keys()]

            # Keep only the user provided kwargs
            if len(fkwargs) > 0:
                # Store these keys so they may be used as part of a comparison
                # test to ensure all user supplied keys are used.
                saved_keys.extend(fkwargs)

                # Assign user keywords to relevant function
                if fkey in partial_func:
                    pfunc = functools.partial(func, **self.kwargs[fkey])
                    setattr(self, func_name, pfunc)
                    # Only retain the user provided keywords. These partial
                    # keywords need to be retained so that __repr__ can
                    # provide an accurate reconstruction.
                    self.kwargs[fkey] = user_values

        # Test for user supplied keys that are not used
        missing_keys = []
        for custom_key in kwargs:
            if custom_key not in saved_keys and (custom_key not in exp_keys):
                missing_keys.append(custom_key)

        if len(missing_keys) > 0:
            raise ValueError('unknown keyword{:s} supplied: {:}'.format(
                '' if len(missing_keys) == 1 else 's', missing_keys))

        # Instantiate the Files class
        temporary_file_list = not temporary_file_list

        if ignore_empty_files is None:
            ignore_empty_files = pysat.params['ignore_empty_files']
        if update_files is None:
            update_files = pysat.params['update_files']

        self.files = pysat.Files(self, directory_format=self.directory_format,
                                 update_files=update_files,
                                 file_format=self.file_format,
                                 write_to_disk=temporary_file_list,
                                 ignore_empty_files=ignore_empty_files)

        # Set bounds for iteration. self.bounds requires the Files class, and
        # setting bounds to (None, None) loads the default bounds.
        self.bounds = (None, None)
        self.date = None
        self._fid = None
        self.yr = None
        self.doy = None
        self._load_by_date = False

        # Initialize orbit support
        if orbit_info is None:
            if self.orbit_info is None:
                # If default info not provided, use class defaults
                self.orbit_info = dict()
        else:
            self.orbit_info = orbit_info
        self.orbits = pysat.Orbits(self, **self.orbit_info)

        # Create empty placeholder for meta translation table
        # gives information about how to label metadata for netcdf export
        # if None, pysat metadata labels will be used
        self._meta_translation_table = None

        # Create a placeholder for a post-processing function to be applied
        # to the metadata dictionary before export. If None, no post-processing
        # will occur
        self._export_meta_post_processing = None

        # Start with a daily increment for loading
        self.load_step = dt.timedelta(days=1)

        # Run instrument init function, a basic pass function is used if the
        # user doesn't supply the init function
        self._init_rtn(**self.kwargs['init'])

        # Store base attributes, used in particular by Meta class
        self._base_attr = dir(self)

    def __eq__(self, other):
        """Perform equality check

        Parameters
        ----------
        other : any
            Other object to compare for equality

        Returns
        -------
        bool
            True if objects are identical, False if they are not.

        """

        # Check if other is the same class (Instrument). Exit early if not.
        if not isinstance(other, self.__class__):
            return False

        # Check if both objects are the same data type. Exit early if not.
        if self.pandas_format != other.pandas_format:
            return False

        # Both the same data type, do both have data?
        if self.empty and other.empty:
            # This check needed to establish next check
            pass
        elif self.empty or other.empty:
            # Only one has data, exit early.
            return False

        # If data is the same, check other attributes. Partial functions
        # required their own path for equality, string comparisons!
        partial_funcs = ['_init_rtn', '_clean_rtn', '_preprocess_rtn',
                         '_list_files_rtn', '_download_rtn',
                         '_list_remote_files_rtn', '_load_rtn']

        # If the type is the same then check everything that is attached to
        # the Instrument object. Includes attributes, methods, variables, etc.
        checks = []
        key_check = []
        for key in self.__dict__.keys():
            if key not in ['data', '_null_data', '_next_data',
                           '_curr_data', '_prev_data']:
                key_check.append(key)
                if key in other.__dict__.keys():
                    if key in partial_funcs:
                        # Partial function comparison doesn't work directly.
                        try:
                            checks.append(str(self.__dict__[key])
                                          == str(other.__dict__[key]))
                        except AttributeError:
                            # If an item missing a required attribute
                            return False

                    else:
                        # General check for everything else.
                        checks.append(np.all(self.__dict__[key]
                                             == other.__dict__[key]))

                else:
                    # Both objects don't have the same attached objects
                    return False
            else:
                # Data comparison area. Established earlier both have data.
                if self.pandas_format:
                    try:
                        # Check is sensitive to the index labels. Errors
                        # if index is not identical.
                        checks.append(np.all(self.__dict__[key]
                                             == other.__dict__[key]))
                    except ValueError:
                        return False

                else:
                    checks.append(xr.Dataset.equals(self.data,
                                                    other.data))

        # Confirm that other Instrument object doesn't have extra terms
        for key in other.__dict__.keys():
            if key not in self.__dict__.keys():
                return False

        # Confirm all checks are True
        test_data = np.all(checks)

        return test_data

    def __repr__(self):
        """ Print the basic Instrument properties"""

        # Create string for custom attached methods
        cstr = '['
        for func, arg, kwarg in zip(self.custom_functions, self.custom_args,
                                    self.custom_kwargs):
            tstr = "".join(("'function': {sfunc}, 'args': {sargs}, ",
                            "'kwargs': {kargs}"))
            tstr = tstr.format(sfunc=repr(func), sargs=repr(arg),
                               kargs=repr(kwarg))
            cstr = "".join((cstr, '{', tstr, '}, '))
        cstr += ']'

        # Deconstruct the kwargs
        in_kwargs = dict()

        for sort_key in self.kwargs.keys():
            for meth_key in self.kwargs[sort_key]:
                in_kwargs[meth_key] = self.kwargs[sort_key][meth_key]

        # Get the inst_module string
        if self.inst_module is None:
            istr = "None"
        else:
            istr = getattr(self.inst_module, "__name__")

        # Create string for other parts Instrument instantiation
        out_str = "".join(["pysat.Instrument(platform='", self.platform,
                           "', name='", self.name, "', inst_id='", self.inst_id,
                           "', clean_level='", self.clean_level,
                           "', pad={:}, orbit_info=".format(self.pad),
                           "{:}, ".format(self.orbit_info),
                           "inst_module=", istr, ", custom=", cstr,
                           ", **{:}".format(in_kwargs), ")"])

        return out_str

    def __str__(self):
        """ Descriptively print the basic Instrument properties"""

        # Get the basic Instrument properties
        output_str = 'pysat Instrument object\n'
        output_str += '-----------------------\n'
        output_str += "Platform: '{:s}'\n".format(self.platform)
        output_str += "Name: '{:s}'\n".format(self.name)
        output_str += "Tag: '{:s}'\n".format(self.tag)
        output_str += "Instrument id: '{:s}'\n".format(self.inst_id)

        # Print out the data processing information
        output_str += '\nData Processing\n'
        output_str += '---------------\n'
        output_str += "Cleaning Level: '{:s}'\n".format(self.clean_level)
        output_str += 'Data Padding: {:s}\n'.format(self.pad.__str__())
        for routine in self.kwargs.keys():
            output_str += 'Keyword Arguments Passed to {:s}: '.format(routine)
            output_str += "{:s}\n".format(self.kwargs[routine].__str__())

        num_funcs = len(self.custom_functions)
        output_str += "Custom Functions: {:d} applied\n".format(num_funcs)
        if num_funcs > 0:
            for i, func in enumerate(self.custom_functions):
                output_str += "    {:d}: {:}\n".format(i, func.__repr__())
                if len(self.custom_args[i]) > 0:
                    ostr = "     : Args={:}\n".format(self.custom_args[i])
                    output_str += ostr
                if len(self.custom_kwargs[i]) > 0:
                    ostr = "     : Kwargs={:}\n".format(self.custom_kwargs[i])
                    output_str += ostr
        output_str += '\n'

        # Print out the orbit settings
        if self.orbits.orbit_index is not None:
            output_str += '{:s}\n'.format(self.orbits.__str__())

        # Print the local file information
        output_str += self.files.__str__()

        # Display loaded data
        output_str += '\n\nLoaded Data Statistics\n'
        output_str += '----------------------\n'
        if not self.empty:
            num_vars = len(self.variables)

            output_str += 'Date: ' + self.date.strftime('%d %B %Y') + '\n'
            output_str += 'DOY: {:03d}\n'.format(self.doy)
            output_str += 'Time range: '
            output_str += self.index[0].strftime('%d %B %Y %H:%M:%S')
            output_str += ' --- '
            output_str += self.index[-1].strftime('%d %B %Y %H:%M:%S\n')
            output_str += 'Number of Times: {:d}\n'.format(len(self.index))
            output_str += 'Number of variables: {:d}\n'.format(num_vars)

            output_str += '\nVariable Names:\n'
            output_str += utils._core.fmt_output_in_cols(self.variables)

            # Print the short version of the metadata
            output_str += '\n{:s}'.format(self.meta.__str__(long_str=False))
        else:
            output_str += 'No loaded data.\n'

        return output_str

    def __getitem__(self, key):
        """
        Convenience notation for accessing data; inst['name'] is inst.data.name

        Parameters
        ----------
        key : str, tuple, or dict
            Data variable name, tuple with a slice, or dict used to locate
            desired data

        Note
        ----
        See pandas or xarray .loc and .iloc documentation for more details

        Examples
        --------
        ::

            # By name
            inst['name']
            # By list of names
            inst[['name1', 'name2']]
            # By position
            inst[row_index, 'name']
            # Slicing by row
            inst[row1:row2, 'name']
            # By Date
            inst[datetime, 'name']
            # Slicing by date, inclusive
            inst[datetime1:datetime2, 'name']
            # Slicing by name and row/date
            inst[datetime1:datetime2, 'name1':'name2']

        """

        if self.pandas_format:
            if isinstance(key, str):
                return self.data[key]
            elif isinstance(key, tuple):
                try:
                    # Pass keys directly through
                    return self.data.loc[key[0], key[1]]
                except (KeyError, TypeError):
                    # TypeError for single integer
                    # KeyError for list, array, slice of integers
                    # Assume key[0] is integer (including list or slice)
                    return self.data.loc[self.data.index[key[0]], key[1]]
            else:
                try:
                    # integer based indexing
                    return self.data.iloc[key]
                except (TypeError, ValueError):
                    # If it's not an integer, TypeError is thrown
                    # If it's a list, ValueError is thrown
                    return self.data[key]
        else:
            return self.__getitem_xarray__(key)

    def __getitem_xarray__(self, key):
        """
        Convenience notation for accessing data; inst['name'] is inst.data.name

        Parameters
        ----------
        key : str, tuple, or dict
            Data variable name, tuple with a slice, or dict used to locate
            desired data

        Returns
        -------
        xr.Dataset
            Dataset of with only the desired values

        Note
        ----
        See xarray .loc and .iloc documentation for more details

        Examples
        --------
        ::

            # By name
            inst['name']
            # By position
            inst[row_index, 'name']
            # Slicing by row
            inst[row1:row2, 'name']
            # By Date
            inst[datetime, 'name']
            # Slicing by date, inclusive
            inst[datetime1:datetime2, 'name']
            # Slicing by name and row/date
            inst[datetime1:datetime2, 'name1':'name2']

        """
        if 'Epoch' in self.data.indexes:
            epoch_name = 'Epoch'
        elif 'time' in self.data.indexes:
            epoch_name = 'time'
        else:
            return xr.Dataset(None)

        if isinstance(key, tuple):
            if len(key) == 2:
                # Support slicing time, variable name
                try:
                    return self.data.isel(indexers={epoch_name: key[0]})[key[1]]
                except (TypeError, KeyError):
                    try:
                        return self.data.sel(indexers={epoch_name:
                                                       key[0]})[key[1]]
                    except TypeError:
                        # Construct dataset from names
                        return self.data[self.variables[key[1]]]
                except ValueError as verr:
                    # This may be multidimensional indexing, where the mutliple
                    # dimensions are contained within an iterable object
                    var_name = key[-1]

                    # If this is not true, raise the original error
                    if len(key[0]) != len(self[var_name].dims):
                        raise ValueError(verr)

                    # Construct a dictionary with dimensions as keys and the
                    # indexes to select for each dimension as values
                    indict = dict()
                    for i, dim in enumerate(self[var_name].dims):
                        indict[dim] = key[0][i]

                    return self.data[var_name][indict]
            else:
                # Multidimensional indexing where the multple dimensions are
                # not contained within another object
                var_name = key[-1]

                # Ensure the dimensions are appropriate
                if len(key) - 1 != len(self[var_name].dims):
                    raise ValueError("indices don't match data dimensions")

                # Construct a dictionary with dimensions as keys and the
                # indexes to select for each dimension as values
                indict = dict()
                for i, dim in enumerate(self[var_name].dims):
                    indict[dim] = key[i]

                return self.data[var_name][indict]
        else:
            try:
                # Grab a particular variable by name
                return self.data[key]
            except (TypeError, KeyError):
                # If that didn't work, likely need to use `isel` or `sel`
                try:
                    # Try to get all data variables, but for a subset of time
                    # using integer indexing
                    return self.data.isel(indexers={epoch_name: key})
                except (TypeError, KeyError):
                    # Try to get a subset of time, using label based indexing
                    return self.data.sel(indexers={epoch_name: key})

    def __setitem__(self, key, new):
        """Convenience method for adding data to instrument.

        Parameters
        ----------
        key : str, tuple, dict
            String label, or dict or tuple of indices for new data
        new : dict, pandas.DataFrame, or xarray.Dataset
            New data as a dict (assigned with key 'data'), DataFrame, or
            Dataset

        Examples
        --------
        ::

            # Simple Assignment, default metadata assigned
            # 'long_name' = 'name'
            # 'units' = ''
            inst['name'] = newData
            # Assignment with Metadata
            inst['name'] = {'data':new_data,
                            'long_name':long_name,
                            'units':units}

        Note
        ----
        If no metadata provided and if metadata for 'name' not already stored
        then default meta information is also added,
        long_name = 'name', and units = ''.

        """

        # add data to main pandas.DataFrame, depending upon the input
        # aka slice, and a name
        if self.pandas_format:
            if isinstance(key, tuple):
                try:
                    # Pass directly through to loc
                    # This line raises a FutureWarning if key[0] is a slice
                    # The future behavior is TypeError, which is already
                    # handled correctly below
                    self.data.loc[key[0], key[1]] = new
                except (KeyError, TypeError):
                    # TypeError for single integer, slice (pandas 2.0)
                    # KeyError for list, array
                    # Assume key[0] is integer (including list or slice)
                    self.data.loc[self.data.index[key[0]], key[1]] = new
                self.meta[key[1]] = {}
                return
            elif not isinstance(new, dict):
                # make it a dict to simplify downstream processing
                new = {'data': new}

            # input dict must have data in 'data',
            # the rest of the keys are presumed to be metadata
            in_data = new.pop('data')
            if hasattr(in_data, '__iter__'):
                if isinstance(in_data, pds.DataFrame):
                    pass
                    # filter for elif
                elif isinstance(next(iter(in_data), None), pds.DataFrame):
                    # Input is a list_like of frames, denoting higher order data
                    if ('meta' not in new) and (key not in self.meta.keys_nD()):
                        # Create an empty Meta instance but with variable names.
                        # This will ensure the correct defaults for all
                        # subvariables.  Meta can filter out empty metadata as
                        # needed, the check above reduces the need to create
                        # Meta instances
                        ho_meta = pysat.Meta(labels=self.meta_labels)
                        ho_meta[in_data[0].columns] = {}
                        self.meta[key] = ho_meta

            # assign data and any extra metadata
            self.data[key] = in_data
            self.meta[key] = new

        else:
            # xarray format chosen for Instrument object
            if not isinstance(new, dict):
                new = {'data': new}
            in_data = new.pop('data')

            if 'Epoch' in self.data.indexes:
                epoch_name = 'Epoch'
            elif 'time' in self.data.indexes:
                epoch_name = 'time'
            else:
                raise ValueError(' '.join(('Unsupported time index name,',
                                           '"Epoch" or "time".')))

            if isinstance(key, tuple):
                # user provided more than one thing in assignment location
                # something like, index integers and a variable name
                # self[idx, 'variable'] = stuff
                # or, self[idx1, idx2, idx3, 'variable'] = stuff
                # construct dictionary of dimensions and locations for
                # xarray standards
                indict = {}
                for i, dim in enumerate(self[key[-1]].dims):
                    indict[dim] = key[i]
                try:
                    # Try loading as values
                    self.data[key[-1]].loc[indict] = in_data
                except (TypeError, KeyError):
                    # Try loading indexed as integers
                    self.data[key[-1]][indict] = in_data

                self.meta[key[-1]] = new
                return
            elif isinstance(key, str):
                # Assigning basic variables

                if isinstance(in_data, xr.DataArray):
                    # If xarray input, take as is
                    self.data[key] = in_data
                elif len(np.shape(in_data)) == 1:
                    # If not an xarray input, but still iterable, then we
                    # go through to process the 1D input
                    if len(in_data) == len(self.index):
                        # 1D input has the correct length for storage along
                        # 'Epoch'
                        self.data[key] = (epoch_name, in_data)
                    elif len(in_data) == 1:
                        # only provided a single number in iterable, make that
                        # the input for all times
                        self.data[key] = (epoch_name,
                                          [in_data[0]] * len(self.index))
                    elif len(in_data) == 0:
                        # Provided an empty iterable, make everything NaN
                        self.data[key] = (epoch_name,
                                          [np.nan] * len(self.index))
                elif len(np.shape(in_data)) == 0:
                    # Not an iterable input, rather a single number.  Make
                    # that number the input for all times
                    self.data[key] = (epoch_name, [in_data] * len(self.index))
                else:
                    # Multidimensional input that is not an xarray.  The user
                    # needs to provide everything that is required for success
                    if isinstance(in_data, tuple):
                        self.data[key] = in_data
                    else:
                        raise ValueError(' '.join(('Must provide dimensions',
                                                   'for xarray multidim',
                                                   'data using input tuple.')))

            elif hasattr(key, '__iter__'):
                # Multiple input strings (keys) are provided, but not in tuple
                # form.  Recurse back into this function, setting each input
                # individually
                for keyname in key:
                    self.data[keyname] = in_data[keyname]

            # Attach metadata
            self.meta[key] = new

        return

    def __iter__(self):
        """Iterates instrument object by loading subsequent days or files.

        Note
        ----
        Limits of iteration, and iteration type (date/file)
        set by `bounds` attribute.

        Default bounds are the first and last dates from files on local system.

        Examples
        --------
        ::

            inst = pysat.Instrument(platform=platform, name=name, tag=tag)
            start = dt.datetime(2009, 1, 1)
            stop = dt.datetime(2009, 1, 31)
            inst.bounds = (start, stop)
            for inst in inst:
                print('Another day loaded', inst.date)

        """

        if self._iter_type == 'file':
            width = self._iter_width
            for fname in self._iter_list:
                # Without a copy, a = [inst for inst in inst] leads to
                # every item being the last day loaded.
                # With the copy, behavior is as expected. Making a copy
                # of an empty object is going to be faster than a full one.
                self.data = self._null_data
                local_inst = self.copy()
                # load range of files
                # get location for second file, width of 1 loads only one file
                nfid = self.files.get_index(fname) + width - 1
                local_inst.load(fname=fname, stop_fname=self.files[nfid])
                yield local_inst

        elif self._iter_type == 'date':
            # Iterate over dates. A list of dates is generated whenever
            # bounds are set
            for date in self._iter_list:
                # Use a copy trick, starting with null data in object
                self.data = self._null_data
                local_inst = self.copy()

                # Set the user-specified range of dates
                end_date = date + self._iter_width

                # Load the range of dates
                local_inst.load(date=date, end_date=end_date)
                yield local_inst

        # Add last loaded data/metadata from local_inst into the original object
        # Making copy here to ensure there are no left over references
        # to the local_inst object in the loop that would interfere with
        # garbage collection. Don't want to make a copy of underlying data.
        local_inst_data = local_inst.data
        local_inst.data = local_inst._null_data
        self.data = local_inst_data
        self.meta = local_inst.meta.copy()

    # -----------------------------------------------------------------------
    # Define all hidden methods

    def _empty(self, data=None):
        """Boolean flag reflecting lack of data

        Parameters
        ----------
        data : NoneType, pds.DataFrame, or xr.Dataset
            Data object

        Returns
        -------
        bool
            True if there is no Instrument data, False if there is data

        """

        if data is None:
            data = self.data
        if self.pandas_format:
            return data.empty
        else:
            if 'time' in data.indexes:
                return len(data.indexes['time']) == 0
            elif 'Epoch' in data.indexes:
                return len(data.indexes['Epoch']) == 0
            else:
                return True

    def _index(self, data=None):
        """Returns time index of loaded data

        Parameters
        ----------
        data : NoneType, pds.DataFrame, or xr.Dataset
            Data object

        Returns
        -------
        pds.Series
            Series containing the time indeces for the Instrument data

        """
        if data is None:
            data = self.data

        if self.pandas_format:
            return data.index
        else:
            if 'time' in data.indexes:
                return data.indexes['time']
            elif 'Epoch' in data.indexes:
                return data.indexes['Epoch']
            else:
                return pds.Index([])

    def _pass_method(*args, **kwargs):
        """ Default method for updatable Instrument methods
        """
        pass

    def _assign_attrs(self, by_name=False, inst_module=None):
        """Assign all external instrument attributes to the Instrument object

        Parameters
        ----------
        by_name : boolean
            If True, uses self.platform and self.name to load the Instrument,
            if False uses inst_module. (default=False)
        inst_module : module or NoneType
            Instrument module or None, if not specified (default=None)

        Raises
        ------
        KeyError
            If unknown platform or name supplied
        ImportError
            If there was an error importing the instrument module
        AttributeError
            If a required Instrument method is missing

        Note
        ----
        methods
            init, preprocess, and clean
        functions
            load, list_files, download, and list_remote_files
        attributes
            directory_format, file_format, multi_file_day, orbit_info, and
            pandas_format
        test attributes
            _download_test, _download_test_travis, and _password_req

        """
        # Declare the standard Instrument methods and attributes
        inst_methods = {'required': ['init', 'clean'],
                        'optional': ['preprocess']}
        inst_funcs = {'required': ['load', 'list_files', 'download'],
                      'optional': ['list_remote_files']}
        inst_attrs = {'directory_format': None, 'file_format': None,
                      'multi_file_day': False, 'orbit_info': None,
                      'pandas_format': True}
        test_attrs = {'_test_download': True, '_test_download_travis': True,
                      '_password_req': False}

        # Set method defaults
        for mname in [mm for val in inst_methods.values() for mm in val]:
            local_name = _kwargs_keys_to_func_name(mname)
            setattr(self, local_name, self._pass_method)

        # Set function defaults
        for mname in [mm for val in inst_funcs.values() for mm in val]:
            local_name = _kwargs_keys_to_func_name(mname)
            setattr(self, local_name, _pass_func)

        # Set attribute defaults
        for iattr in inst_attrs.keys():
            setattr(self, iattr, inst_attrs[iattr])

        # Set test defaults
        for iattr in test_attrs.keys():
            setattr(self, iattr, test_attrs[iattr])

        # Get the instrument module information, returning with defaults
        # if none is supplied
        if by_name:
            # pysat platform is reserved for modules within pysat.instruments
            if self.platform == 'pysat':
                # Look within pysat
                inst = importlib.import_module(
                    ''.join(('.', self.platform, '_', self.name)),
                    package='pysat.instruments')
            else:
                # Not a native pysat.Instrument.  First, get the supporting
                # instrument module from the pysat registry.
                user_modules = pysat.params['user_modules']
                if self.platform not in user_modules.keys():
                    raise KeyError('unknown platform supplied: {:}'.format(
                        self.platform))

                if self.name not in user_modules[self.platform].keys():
                    raise KeyError(''.join(['unknown name supplied: ',
                                            self.name, ' not assigned to the ',
                                            self.platform, ' platform']))

                mod = user_modules[self.platform][self.name]

                # Import the registered module.  Though modules are checked to
                # ensure they may be imported when registered, something may
                # have changed on the system since it was originally checked.
                try:
                    inst = importlib.import_module(mod)
                except ImportError as ierr:
                    estr = ' '.join(('unable to locate or import module for',
                                     'platform {:}, name {:}'))
                    estr = estr.format(self.platform, self.name)
                    logger.error(estr)
                    raise ImportError(ierr)
        elif inst_module is not None:
            # User supplied an object with relevant instrument routines
            inst = inst_module
        else:
            # No module or name info, default pass functions assigned
            return

        # Assign the Instrument methods
        missing = list()
        for mstat in inst_methods.keys():
            for mname in inst_methods[mstat]:
                if hasattr(inst, mname):
                    local_name = _kwargs_keys_to_func_name(mname)
                    # Remote functions are not attached as methods unless
                    # cast that way, specifically
                    # https://stackoverflow.com/questions/972/
                    #         adding-a-method-to-an-existing-object-instance
                    local_method = types.MethodType(getattr(inst, mname), self)
                    setattr(self, local_name, local_method)
                else:
                    missing.append(mname)
                    if mstat == "required":
                        raise AttributeError(
                            "".join(['A `', mname, '` method is required',
                                     ' for every Instrument']))

        if len(missing) > 0:
            logger.debug('Missing Instrument methods: {:}'.format(missing))

        # Assign the Instrument functions
        missing = list()
        for mstat in inst_funcs.keys():
            for mname in inst_funcs[mstat]:
                if hasattr(inst, mname):
                    local_name = _kwargs_keys_to_func_name(mname)
                    setattr(self, local_name, getattr(inst, mname))
                else:
                    missing.append(mname)
                    if mstat == "required":
                        raise AttributeError(
                            "".join(['A `', mname, '` function is required',
                                     ' for every Instrument']))

        if len(missing) > 0:
            logger.debug('Missing Instrument methods: {:}'.format(missing))

        # Look for instrument default parameters
        missing = list()
        for iattr in inst_attrs.keys():
            if hasattr(inst, iattr):
                setattr(self, iattr, getattr(inst, iattr))
            else:
                missing.append(iattr)

        if len(missing) > 0:
            logger.debug(''.join(['These Instrument attributes kept their ',
                                  'default  values: {:}'.format(missing)]))

        # Check for download flags for tests
        missing = list()
        for iattr in test_attrs.keys():
            # Check and see if this instrument has the desired test flag
            if hasattr(inst, iattr):
                local_attr = getattr(inst, iattr)

                # Test to see that this attribute is set for the desired
                # inst_id and tag
                if self.inst_id in local_attr.keys():
                    if self.tag in local_attr[self.inst_id].keys():
                        # Update the test attribute value
                        setattr(self, iattr, local_attr[self.inst_id][self.tag])
                    else:
                        missing.append(iattr)
                else:
                    missing.append(iattr)
            else:
                missing.append(iattr)

        if len(missing) > 0:
            logger.debug(''.join(['These Instrument test attributes kept their',
                                  ' default  values: {:}'.format(missing)]))
        return

    def _load_data(self, date=None, fid=None, inc=None):
        """
        Load data for an instrument on given date or fid, depending upon input.

        Parameters
        ----------
        date : dt.datetime or NoneType
            file date (default=None)
        fid : int or NoneType
            filename index value (default=None)
        inc : dt.timedelta or int
            Increment of files or dates to load, starting from the
            root date or fid (default=None)

        Returns
        -------
        data : pds.DataFrame or xr.Dataset
            pysat data
        meta : pysat.Meta
            pysat meta data
        """

        date = filter_datetime_input(date)
        if fid is not None:
            # get filename based off of index value
            # inclusive loading on filenames
            fname = self.files[fid:(fid + inc + 1)]
        elif date is not None:
            fname = self.files[date:(date + inc)]
        else:
            raise ValueError('Must supply either a date or file id number.')

        if len(fname) > 0:
            load_fname = [os.path.join(self.files.data_path, f) for f in fname]
            try:
                data, mdata = self._load_rtn(load_fname, tag=self.tag,
                                             inst_id=self.inst_id,
                                             **self.kwargs['load'])

                # ensure units and name are named consistently in new Meta
                # object as specified by user upon Instrument instantiation
                mdata.accept_default_labels(self.meta)
                bad_datetime = False
            except pds.errors.OutOfBoundsDatetime:
                bad_datetime = True
                data = self._null_data.copy()
                mdata = pysat.Meta(labels=self.meta_labels)

        else:
            bad_datetime = False
            data = self._null_data.copy()
            mdata = pysat.Meta(labels=self.meta_labels)

        output_str = '{platform} {name} {tag} {inst_id}'
        output_str = output_str.format(platform=self.platform,
                                       name=self.name, tag=self.tag,
                                       inst_id=self.inst_id)

        # Check that data and metadata are the data types we expect
        if not isinstance(data, self._data_library):
            raise TypeError(' '.join(('Data returned by instrument load',
                            'routine must be a', self._data_library)))
        if not isinstance(mdata, pysat.Meta):
            raise TypeError('Metadata returned must be a pysat.Meta object')

        # Let user know whether or not data was returned
        ind = data.index if self.pandas_format else data.indexes
        if len(ind) > 0:
            if date is not None:
                output_str = ' '.join(('Returning', output_str, 'data for',
                                       date.strftime('%d %B %Y')))
            else:
                if len(fname) == 1:
                    # this check was zero
                    output_str = ' '.join(('Returning', output_str,
                                           'data from', fname[0]))
                else:
                    output_str = ' '.join(('Returning', output_str,
                                           'data from', fname[0], '::',
                                           fname[-1]))
        else:
            # no data signal
            if date is not None:
                if bad_datetime:
                    output_str = ' '.join(('Bad datetime for', output_str,
                                           date.strftime('%d %B %Y')))
                else:
                    output_str = ' '.join(('No', output_str, 'data for',
                                           date.strftime('%d %B %Y')))
            else:
                if len(fname) == 1:
                    output_str = ' '.join(('No', output_str, 'data for',
                                           fname[0]))
                elif len(fname) == 0:
                    output_str = ' '.join(('No', output_str, 'valid',
                                           'filenames found'))
                else:
                    output_str = ' '.join(('No', output_str, 'data for',
                                           fname[0], '::',
                                           fname[-1]))

        # Remove extra spaces, if any are present
        output_str = " ".join(output_str.split())
        logger.info(output_str)
        return data, mdata

    def _load_next(self):
        """Load the next days data (or file) without incrementing the date

        Returns
        -------
        data : (pds.DataFrame or xr.Dataset)
            pysat data
        meta : (pysat.Meta)
            pysat meta data

        Note
        ----
        Repeated calls will not advance date/file and will produce the same
        data.

        Uses info stored in object to either increment the date,
        or the file. Looks for self._load_by_date flag.

        """
        if self._load_by_date:
            next_date = self.date + self.load_step
            return self._load_data(date=next_date, inc=self.load_step)
        else:
            next_id = self._fid + self.load_step + 1
            return self._load_data(fid=next_id, inc=self.load_step)

    def _load_prev(self):
        """Load the previous days data (or file) without decrementing the date

        Returns
        -------
        data : (pds.DataFrame or xr.Dataset)
            pysat data
        meta : (pysat.Meta)
            pysat meta data

        Note
        ----
        Repeated calls will not decrement date/file and will produce the same
        data

        Uses info stored in object to either decrement the date,
        or the file. Looks for self._load_by_date flag.

        """

        if self._load_by_date:
            prev_date = self.date - self.load_step
            return self._load_data(date=prev_date, inc=self.load_step)
        else:
            prev_id = self._fid - self.load_step - 1
            return self._load_data(fid=prev_id, inc=self.load_step)

    def _set_load_parameters(self, date=None, fid=None):
        """ Set the necesssary load attributes

        Parameters
        ----------
        date : (dt.datetime.date object or NoneType)
            file date
        fid : (int or NoneType)
            filename index value

        """
        # Filter supplied data so that it is only year, month, and day and
        # then store as part of instrument object.  Filtering is performed
        # by the class property `self.date`
        self.date = date
        self._fid = fid

        if date is not None:
            year, doy = utils.time.getyrdoy(date)
            self.yr = year
            self.doy = doy
            self._load_by_date = True
        else:
            self.yr = None
            self.doy = None
            self._load_by_date = False

    def _get_var_type_code(self, coltype):
        """Determines the two-character type code for a given variable type

        Parameters
        ----------
        coltype : type or np.dtype
            The type of the variable

        Returns
        -------
        str
            The variable type code for the given type

        Raises
        ------
        TypeError
            When coltype is unknown

        Note
        ----
        Understands np.dtype, numpy int, uint, and float variants, and
        str subclasses

        """
        var_types = {np.int64: 'i8', np.int32: 'i4', np.int16: 'i2',
                     np.int8: 'i1', np.uint64: 'u8', np.uint32: 'u4',
                     np.uint16: 'u2', np.uint8: 'u1', np.float64: 'f8',
                     np.float32: 'f4'}

        if isinstance(coltype, np.dtype):
            var_type = coltype.kind + str(coltype.itemsize)
            return var_type
        else:
            if coltype in var_types.keys():
                return var_types[coltype]
            elif issubclass(coltype, str):
                return 'S1'
            else:
                raise TypeError('Unknown Variable Type' + str(coltype))

    def _get_data_info(self, data):
        """Support file writing by determining data type and other options

        Parameters
        ----------
        data : pandas object
            Data to be written

        Returns
        -------
        data : pandas object
            Data that was supplied, reformatted if necessary
        data_type : type
            Type for data values
        datetime_flag : bool
            True if data is np.datetime64, False otherwise

        """
        # Get the data type
        data_type = data.dtype

        # Check for object type
        if data_type != np.dtype('O'):
            # Simple data, not an object

            if data_type == np.dtype('<M8[ns]'):
                data_type = np.int64
                datetime_flag = True
            else:
                datetime_flag = False
        else:
            # We're dealing with a more complicated object. Iterate
            # over elements until we hit something that is something,
            # and not NaN
            data_type = type(data.iloc[0])
            for i in np.arange(len(data)):
                if len(data.iloc[i]) > 0:
                    data_type = type(data.iloc[i])
                    if not isinstance(data_type, float):
                        break
            datetime_flag = False

        return data, data_type, datetime_flag

    def _filter_netcdf4_metadata(self, mdata_dict, coltype, remove=False,
                                 export_nan=None):
        """Filter metadata properties to be consistent with netCDF4.

        Parameters
        ----------
        mdata_dict : dict
            Dictionary equivalent to Meta object info
        coltype : type
            Type provided by _get_data_info
        remove : bool
            Removes FillValue and associated parameters disallowed for strings
            (default=False)
        export_nan : list or NoneType
            Metadata parameters allowed to be NaN (default=None)

        Returns
        -------
        dict
            Modified as needed for netCDf4

        Note
        ----
        Remove forced to True if coltype consistent with a string type

        Metadata values that are NaN and not listed in export_nan are
        filtered out.

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
        if '_FillValue' in mdata_dict.keys():
            if remove:
                mdata_dict.pop('_FillValue')
            else:
                if not np.can_cast(mdata_dict['_FillValue'], coltype):
                    if 'FieldNam' in mdata_dict:
                        estr = ' '.join(('FillValue for {a:s} ({b:s}) cannot',
                                         'be safely casted to {c:s} Casting',
                                         'anyways. This may result in',
                                         'unexpected behavior'))
                        estr.format(a=mdata_dict['FieldNam'],
                                    b=str(mdata_dict['_FillValue']),
                                    c=coltype)
                        warnings.warn(estr)
                    else:
                        estr = ' '.join(('FillValue {a:s} cannot be safely',
                                         'casted to {b:s}. Casting anyways.',
                                         'This may result in unexpected',
                                         'behavior'))
                        estr.format(a=str(mdata_dict['_FillValue']),
                                    b=coltype)

        # check if load routine actually returns meta
        if self.meta.data.empty:
            self.meta[self.variables] = {self.meta.labels.name: self.variables,
                                         self.meta.labels.units:
                                         [''] * len(self.variables)}

        # Make sure FillValue is the same type as the data
        if 'FillVal' in mdata_dict.keys():
            if remove:
                mdata_dict.pop('FillVal')
            else:
                mdata_dict['FillVal'] = np.array(
                    mdata_dict['FillVal']).astype(coltype)

        return mdata_dict

    # -----------------------------------------------------------------------
    # Define all accessible methods

    @property
    def bounds(self):
        """Boundaries for iterating over instrument object by date or file.

        Parameters
        ----------
        start : datetime object, filename, or None
            start of iteration, if None uses first data date.
            list-like collection also accepted. (default=None)
        stop :  datetime object, filename, or None
            stop of iteration, inclusive. If None uses last data date.
            list-like collection also accepted. (default=None)
        step : str, int, or None
            Step size used when iterating from start to stop. Use a
            Pandas frequency string ('3D', '1M') when setting bounds by date,
            an integer when setting bounds by file. Defaults to a single
            day/file (default='1D', 1).
        width : pandas.DateOffset, int, or None
            Data window used when loading data within iteration. Defaults to a
            single day/file if not assigned. (default=dt.timedelta(days=1),
            1)

        Note
        ----
        Both start and stop must be the same type (date, or filename) or None.
        Only the year, month, and day are used for date inputs.

        Examples
        --------
        ::

            import datetime as dt
            import pandas as pds
            import pysat

            inst = pysat.Instrument(platform=platform,
                                    name=name,
                                    tag=tag)
            start = dt.datetime(2009, 1, 1)
            stop = dt.datetime(2009, 1, 31)

            # Defaults to stepping by a single day and a data loading window
            # of one day/file.
            inst.bounds = (start, stop)

            # Set bounds by file. Iterates a file at a time.
            inst.bounds = ('filename1', 'filename2')

            # Create a more complicated season, multiple start and stop dates.
            start2 = dt.datetetime(2010,1,1)
            stop2 = dt.datetime(2010,2,14)
            inst.bounds = ([start, start2], [stop, stop2])

            # Iterate via a non-standard step size of two days.
            inst.bounds = ([start, start2], [stop, stop2], '2D')

            # Load more than a single day/file at a time when iterating
            inst.bounds = ([start, start2], [stop, stop2], '2D',
                           dt.timedelta(days=3))

        """

        return (self._iter_start, self._iter_stop, self._iter_step,
                self._iter_width)

    @bounds.setter
    def bounds(self, value=None):
        # Set the bounds property.  See property docstring for details

        if value is None:
            # User wants defaults
            value = (None, None, None, None)

        if len(value) < 2:
            raise ValueError(' '.join(('Must supply both a start and stop',
                                       'date/file. Supply None if you want the',
                                       'first/last possible.')))
        elif len(value) == 2:
            # Includes start and stop only
            self._iter_step = None
            self._iter_width = None
        elif len(value) == 3:
            # Also includes step size
            self._iter_step = value[2]
            self._iter_width = None
        elif len(value) == 4:
            # Also includes loading window (data width)
            self._iter_step = value[2]
            self._iter_width = value[3]
        else:
            raise ValueError('Too many input arguments.')

        # Pull out start and stop times now that other optional items have
        # been checked out.
        start = value[0]
        stop = value[1]

        if (start is None) and (stop is None):
            # Set default using first and last file date
            self._iter_start = [self.files.start_date]
            self._iter_stop = [self.files.stop_date]
            self._iter_type = 'date'
            if self._iter_step is None:
                self._iter_step = '1D'
            if self._iter_width is None:
                self._iter_width = dt.timedelta(days=1)
            if self._iter_start[0] is not None:
                # There are files. Use those dates.
                ustops = [istop - self._iter_width + dt.timedelta(days=1)
                          for istop in self._iter_stop]
                ufreq = self._iter_step
                self._iter_list = utils.time.create_date_range(self._iter_start,
                                                               ustops,
                                                               freq=ufreq)
            else:
                # Instrument has no files
                self._iter_list = []
        else:
            # User provided some inputs
            starts = np.asarray([start])
            stops = np.asarray([stop])

            # Ensure consistency if list-like already
            if len(starts.shape) > 1:
                starts = starts[0]
            if len(stops.shape) > 1:
                stops = stops[0]

            # check equal number of elements
            if len(starts) != len(stops):
                estr = ' '.join(('Both start and stop must have the same',
                                 'number of elements'))
                raise ValueError(estr)

            # check everything is the same type
            base = type(starts[0])
            for lstart, lstop in zip(starts, stops):
                etype = type(lstop)
                check1 = not isinstance(lstart, etype)
                check2 = not isinstance(lstart, base)
                if check1 or check2:
                    # Method allows for inputs like inst.bounds = (start, None)
                    # and bounds will fill the None with actual start or stop.
                    # Allow for a Nonetype only if length is one.
                    if len(starts) == 1 and (start is None):
                        # we are good on type change, start is None, no error
                        break
                    elif len(stops) == 1 and (stop is None):
                        # we are good on type change, stop is None, no error
                        break
                    raise ValueError(' '.join(('Start and stop items must all',
                                               'be of the same type')))

            # set bounds based upon passed data type
            if isinstance(starts[0], str) or isinstance(stops[0], str):
                # one of the inputs is a string
                self._iter_type = 'file'
                # could be (string, None) or (None, string)
                # replace None with first/last, as appropriate
                if starts[0] is None:
                    starts = [self.files[0]]
                if stops[0] is None:
                    stops = [self.files[-1]]
                # Default step size
                if self._iter_step is None:
                    self._iter_step = 1
                # Default window size
                if self._iter_width is None:
                    self._iter_width = 1

                self._iter_list = []
                for istart, istop in zip(starts, stops):
                    # Ensure istart begins before istop. Get the index of
                    # the file start/stop times from main file list.
                    start_idx = self.files.get_index(istart)
                    stop_idx = self.files.get_index(istop)
                    if stop_idx < start_idx:
                        estr = ' '.join(('Bounds must be in increasing date',
                                         'order.', istart, 'occurs after',
                                         istop))
                        raise ValueError(estr)
                    itemp = self.files.get_file_array([istart], [istop])
                    # downselect based upon step size
                    itemp = itemp[::self._iter_step]
                    # Make sure iterations don't go past last day
                    # get index of last in iteration list
                    iter_idx = self.files.get_index(itemp[-1])
                    # don't let loaded data go past stop bound
                    if iter_idx + self._iter_width - 1 > stop_idx:
                        i = np.ceil((self._iter_width - 1) / self._iter_step)
                        i = -int(i)
                        self._iter_list.extend(itemp[:i])
                    else:
                        self._iter_list.extend(itemp)

            elif isinstance(starts[0], dt.datetime) or isinstance(stops[0],
                                                                  dt.datetime):
                # One of the inputs is a date
                self._iter_type = 'date'

                if starts[0] is None:
                    # Start and stop dates on self.files already filtered
                    # to include only year, month, and day
                    starts = [self.files.start_date]
                if stops[0] is None:
                    stops = [self.files.stop_date]
                # Default step size
                if self._iter_step is None:
                    self._iter_step = '1D'
                # Default window size
                if self._iter_width is None:
                    self._iter_width = dt.timedelta(days=1)

                # Create list-like of dates for iteration
                starts = filter_datetime_input(starts)
                stops = filter_datetime_input(stops)
                freq = self._iter_step
                width = self._iter_width

                # Ensure inputs are in reasonable date order
                for start, stop in zip(starts, stops):
                    if start > stop:
                        estr = ' '.join(('Bounds must be set in increasing',
                                         'date order.',
                                         start.strftime('%d %B %Y'),
                                         'is later than',
                                         stop.strftime('%d %B %Y')))
                        raise ValueError(estr)

                # account for width of load. Don't extend past bound.
                ustops = [stop - width + dt.timedelta(days=1)
                          for stop in stops]
                self._iter_list = utils.time.create_date_range(starts,
                                                               ustops,
                                                               freq=freq)
                # go back to time index
                self._iter_list = pds.DatetimeIndex(self._iter_list)

            else:
                raise ValueError(' '.join(('Input is not a known type, string',
                                           'or datetime')))
            self._iter_start = starts
            self._iter_stop = stops

        return

    @property
    def empty(self):
        """Boolean flag reflecting lack of data.

        True if there is no Instrument data."""

        if self.pandas_format:
            return self.data.empty
        else:
            if 'time' in self.data.indexes:
                return len(self.data.indexes['time']) == 0
            elif 'Epoch' in self.data.indexes:
                return len(self.data.indexes['Epoch']) == 0
            else:
                return True

    @property
    def date(self):
        """Date for loaded data."""
        return self._date

    @date.setter
    def date(self, new_date):
        # Set the date property, see property docstring for details
        self._date = filter_datetime_input(new_date)

    @property
    def index(self):
        """Returns time index of loaded data."""
        return self._index()

    @property
    def variables(self):
        """Returns list of variables within loaded data."""

        if self.pandas_format:
            return self.data.columns
        else:
            return list(self.data.variables.keys())

    def copy(self):
        """Deep copy of the entire Instrument object.

        Returns
        -------
        pysat.Instrument

        """
        # Copy doesn't work with module objects. Store module and files class,
        # set module variable/files to `None`, make the copy, reassign the
        # saved modules.
        saved_module = self.inst_module

        # The files/orbits class copy() not invoked with deepcopy
        saved_files = self.files
        saved_orbits = self.orbits

        self.inst_module = None
        self.files = None
        self.orbits = None

        # Copy non-problematic parameters
        inst_copy = copy.deepcopy(self)

        # Restore links to the instrument support functions module
        inst_copy.inst_module = saved_module
        self.inst_module = saved_module

        # Reattach files and copy
        inst_copy.files = saved_files.copy()
        self.files = saved_files

        # Reattach orbits and copy
        inst_copy.orbits = saved_orbits.copy()
        self.orbits = saved_orbits

        # Support a copy if a user does something like,
        # self.orbits.inst.copy(), or
        # self.files.inst_info['inst'].copy()
        if not isinstance(inst_copy, weakref.ProxyType):
            inst_copy.files.inst_info['inst'] = weakref.proxy(inst_copy)
            inst_copy.orbits.inst = weakref.proxy(inst_copy)
        else:
            inst_copy.files.inst_info['inst'] = inst_copy
            inst_copy.orbits.inst = inst_copy

        return inst_copy

    def concat_data(self, new_data, prepend=False, **kwargs):
        """Concats new_data to self.data for xarray or pandas as needed

        Parameters
        ----------
        new_data : pds.DataFrame, xr.Dataset, or list of such objects
            New data objects to be concatonated
        prepend : boolean
            If True, assign new data before existing data; if False append new
            data (default=False)
        **kwargs : dict
            Optional keyword arguments passed to pds.concat or xr.concat

        Note
        ----
        For pandas, sort=False is passed along to the underlying
        pandas.concat method. If sort is supplied as a keyword, the
        user provided value is used instead.  Recall that sort orders the
        data columns, not the data values or the index.

        For xarray, dim=Instrument.index.name is passed along to xarray.concat
        except if the user includes a value for dim as a keyword argument.

        """
        # Order the data to be concatonated in a list
        if not isinstance(new_data, list):
            new_data = [new_data]

        if prepend:
            new_data.append(self.data)
        else:
            new_data.insert(0, self.data)

        # Retrieve the appropriate concatonation function
        if self.pandas_format:
            # Specifically do not sort unless otherwise specified
            if 'sort' not in kwargs:
                kwargs['sort'] = False
            concat_func = pds.concat
        else:
            # Specify the dimension, if not otherwise specified
            if 'dim' not in kwargs:
                kwargs['dim'] = self.index.name
            concat_func = xr.concat

        # Assign the concatonated data to the instrument
        self.data = concat_func(new_data, **kwargs)
        return

    def custom_attach(self, function, at_pos='end', args=[], kwargs={}):
        """Attach a function to custom processing queue.

        Custom functions are applied automatically whenever `.load()`
        command called.

        Parameters
        ----------
        function : string or function object
            name of function or function object to be added to queue
        at_pos : string or int
            Accepts string 'end' or a number that will be used to determine
            the insertion order if multiple custom functions are attached
            to an Instrument object. (default='end').
        args : list or tuple
            Ordered arguments following the instrument object input that are
            required by the custom function (default=[])
        kwargs : dict
            Dictionary of keyword arguments required by the custom function
            (default={})

        Note
        ----
        Functions applied using `custom_attach` may add, modify, or use
        the data within Instrument inside of the function, and so should not
        return anything.

        """

        # Test the positioning input
        pos_list = list(np.arange(0, len(self.custom_functions), 1))
        pos_list.append('end')

        if at_pos not in pos_list:
            logger.warning(''.join(['unknown position specified, including ',
                                    'function at end of current list']))
            at_pos = 'end'

        # Convert string to function object, if necessary
        if isinstance(function, str):
            function = eval(function)

        # If the position is 'end' or greater
        if (at_pos == 'end') | (at_pos == len(self.custom_functions)):
            # store function object
            self.custom_functions.append(function)
            self.custom_args.append(args)
            self.custom_kwargs.append(kwargs)
        else:
            # user picked a specific location to insert
            self.custom_functions.insert(at_pos, function)
            self.custom_args.insert(at_pos, args)
            self.custom_kwargs.insert(at_pos, kwargs)

        return

    def custom_apply_all(self):
        """ Apply all of the custom functions to the satellite data object.

        Raises
        ------
        ValueError
            Raised when function returns any value

        Note
        ----
        This method does not generally need to be invoked directly by users.

        """

        if len(self.custom_functions) > 0:
            for func, arg, kwarg in zip(self.custom_functions,
                                        self.custom_args,
                                        self.custom_kwargs):
                if not self.empty:
                    # Custom functions do nothing or modify loaded data. Methods
                    # are run on Instrument object directly and any changes to
                    # object by the method are retained. No data may be returned
                    # by method itself.
                    null_out = func(self, *arg, **kwarg)
                    if null_out is not None:
                        raise ValueError(''.join(('Custom functions should not',
                                                  ' return any information via',
                                                  ' return. Information may ',
                                                  'only be propagated back by',
                                                  ' modifying supplied pysat ',
                                                  'object.')))
        return

    def custom_clear(self):
        """Clear the custom function list.
        """
        self.custom_functions = []
        self.custom_args = []
        self.custom_kwargs = []
        return

    def today(self):
        """Returns today's date (UTC), with no hour, minute, second, etc.

        Returns
        -------
        today_utc: datetime
            Today's date in UTC

        """
        today_utc = filter_datetime_input(dt.datetime.utcnow())

        return today_utc

    def tomorrow(self):
        """Returns tomorrow's date (UTC), with no hour, minute, second, etc.

        Returns
        -------
        datetime
            Tomorrow's date in UTC

        """

        return self.today() + dt.timedelta(days=1)

    def yesterday(self):
        """Returns yesterday's date (UTC), with no hour, minute, second, etc.

        Returns
        -------
        datetime
            Yesterday's date in UTC

        """

        return self.today() - dt.timedelta(days=1)

    def next(self, verifyPad=False):
        """Manually iterate through the data loaded in Instrument object.

        Bounds of iteration and iteration type (day/file) are set by
        `bounds` attribute.

        Parameters
        ----------
        verifyPad : bool
            Passed to `self.load()`. If True, then padded data within
            the load method will be retained. (default=False)

        Note
        ----
        If there were no previous calls to load then the
        first day(default)/file will be loaded.

        """

        # make sure we can iterate
        if len(self._iter_list) == 0:
            # nothing to potentially iterate over
            raise StopIteration(''.join(('File list is empty. ',
                                         'Nothing to be done.')))

        if self._iter_type == 'date':
            if self.date is not None:
                # data is already loaded in .data
                idx, = np.where(self.date == self._iter_list)
                if len(idx) == 0:
                    estr = ''.join(('Unable to find loaded date ',
                                    'in the supported iteration list. ',
                                    'Please check the Instrument bounds, ',
                                    '`self.bounds` for supported iteration',
                                    'ranges.'))
                    raise StopIteration(estr)
                elif idx[-1] >= len(self._iter_list) - 1:
                    # gone to far!
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    # not going past the last day, safe to move forward
                    date = self._iter_list[idx[0] + 1]
                    end_date = date + self._iter_width
            else:
                # no data currently loaded, start at the beginning
                date = self._iter_list[0]
                end_date = date + self._iter_width
            # perform load
            self.load(date=date, end_date=end_date, verifyPad=verifyPad)

        elif self._iter_type == 'file':
            first = self.files.get_index(self._iter_list[0])
            last = self.files.get_index(self._iter_list[-1])
            step = self._iter_step
            width = self._iter_width
            if self._fid is not None:
                # data already loaded in .data
                if (self._fid < first) | (self._fid + step > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    # step size already accounted for in the list of files
                    # get location of current file in iteration list
                    idx = None
                    fname = self.files[self._fid]
                    for i, name in enumerate(self._iter_list):
                        if name == fname:
                            idx = i
                            break
                    if idx is None:
                        estr = ''.join(('Unable to find loaded filename ',
                                        'in the supported iteration list. ',
                                        'Please check the Instrument bounds, ',
                                        '`self.bounds` for supported iteration',
                                        'ranges.'))
                        raise StopIteration(estr)
                    fname = self._iter_list[idx + 1]
            else:
                # no data loaded yet, start with the first file
                fname = self._iter_list[0]

            # load range of files at a time
            # get location for second file. Note a width of 1 loads single file
            nfid = self.files.get_index(fname) + width - 1
            self.load(fname=fname, stop_fname=self.files[nfid],
                      verifyPad=verifyPad)

        return

    def prev(self, verifyPad=False):
        """Manually iterate backwards through the data in Instrument object.

        Bounds of iteration and iteration type (day/file)
        are set by `bounds` attribute.

        Parameters
        ----------
        verifyPad : bool
            Passed to `self.load()`. If True, then padded data within
            the load method will be retained. (default=False)

        Note
        ----
        If there were no previous calls to load then the
        first day(default)/file will be loaded.

        """
        # make sure we can iterate
        if len(self._iter_list) == 0:
            # nothing to potentially iterate over
            raise StopIteration(''.join(('File list is empty. ',
                                         'Nothing to be done.')))

        if self._iter_type == 'date':
            if self.date is not None:
                # some data already loaded in .data
                idx, = np.where(self._iter_list == self.date)
                if len(idx) == 0:
                    estr = ''.join(('Unable to find loaded date ',
                                    'in the supported iteration list. ',
                                    'Please check the Instrument bounds, ',
                                    '`self.bounds` for supported iteration',
                                    'ranges.'))
                    raise StopIteration(estr)
                elif idx[0] == 0:
                    # too far!
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    # not on first day, safe to move backward
                    date = self._iter_list[idx[0] - 1]
                    end_date = self._iter_list[idx[0] - 1] + self._iter_width
                    self.load(date=date, end_date=end_date, verifyPad=verifyPad)
            else:
                # no data currently loaded, start at the end
                end_date = self._iter_list[-1] + self._iter_width
                date = self._iter_list[-1]
                self.load(date=date, end_date=end_date, verifyPad=verifyPad)

        elif self._iter_type == 'file':
            first = self.files.get_index(self._iter_list[0])
            last = self.files.get_index(self._iter_list[-1])
            step = self._iter_step
            width = self._iter_width
            if self._fid is not None:
                if (self._fid - step < first) or (self._fid > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    # find location of file
                    idx = None
                    fname = self.files[self._fid]
                    for i, name in enumerate(self._iter_list):
                        if name == fname:
                            idx = i
                            break
                    if idx is None:
                        estr = ''.join(('Unable to find loaded filename ',
                                        'in the supported iteration list. ',
                                        'Please check the Instrument bounds, ',
                                        '`self.bounds` for supported iteration',
                                        'ranges.'))
                        raise StopIteration(estr)
                    fname = self._iter_list[idx - 1]
            else:
                fname = self._iter_list[-1]

            nfid = self.files.get_index(fname) + width - 1
            self.load(fname=fname, stop_fname=self.files[nfid],
                      verifyPad=verifyPad)

        return

    def rename(self, var_names, lowercase_data_labels=False):
        """Renames variable within both data and metadata.

        Parameters
        ----------
        var_names : dict or other map
            Existing var_names are keys, values are new var_names
        lowercase_data_labels : bool
            If True, the labels applied to inst.data are forced to lowercase.
            The supplied case in var_names is retained within inst.meta.

        Examples
        --------
        ::

            # standard renaming
            new_var_names = {'old_name': 'new_name',
                         'old_name2':, 'new_name2'}
            inst.rename(new_var_names)


        If using a pandas DataFrame as the underlying data object,
        to rename higher-order variables supply a modified dictionary.
        Note that this rename will be invoked individually for all
        times in the dataset.
        ::

            # applies to higher-order datasets
            # that are loaded into pandas
            # general example
            new_var_names = {'old_name': 'new_name',
                             'old_name2':, 'new_name2',
                             'col_name': {'old_ho_name': 'new_ho_name'}}
            inst.rename(new_var_names)

            # specific example
            inst = pysat.Instrument('pysat', 'testing2D')
            inst.load(2009, 1)
            var_names = {'uts': 'pysat_uts',
                     'profiles': {'density': 'pysat_density'}}
            inst.rename(var_names)


        pysat supports differing case for variable labels across the
        data and metadata objects attached to an Instrument. Since
        metadata is case-preserving (on assignment) but case-insensitive,
        the labels used for data are always valid for metadata. This
        feature may be used to provide friendlier variable names within
        pysat while also maintaining external format compatibility
        when writing files.
        ::

            # example with lowercase_data_labels
            inst = pysat.Instrument('pysat', 'testing2D')
            inst.load(2009, 1)
            var_names = {'uts': 'Pysat_UTS',
                     'profiles': {'density': 'PYSAT_density'}}
            inst.rename(var_names, lowercase_data_labels=True)

            # note that 'Pysat_UTS' was applied to data as 'pysat_uts'
            print(inst['pysat_uts'])

            # case is retained within inst.meta, though
            # data access to meta is case insensitive
            print('True meta variable name is ', inst.meta['pysat_uts'].name)

            # Note that the labels in meta may be used when creating a file
            # thus 'Pysat_UTS' would be found in the resulting file
            inst.to_netcdf4('./test.nc', preserve_meta_case=True)

            # load in file and check
            raw = netCDF4.Dataset('./test.nc')
            print(raw.variables['Pysat_UTS'])


        """

        if self.pandas_format:
            # Check for standard rename variables as well as
            # renaming for higher order variables
            fdict = {}  # filtered old variable names
            hdict = {}  # higher order variable names

            # keys for existing higher order data labels
            ho_keys = [a for a in self.meta.keys_nD()]
            lo_keys = [a for a in self.meta.keys()]

            # iterate, collect normal variables
            # rename higher order variables
            for vkey in var_names:
                # original name, new name
                oname, nname = vkey, var_names[vkey]
                if oname not in ho_keys:
                    if oname in lo_keys:
                        # within low order (standard) variable name keys
                        # may be renamed directly
                        fdict[oname] = nname
                    else:
                        # not in standard or higher order variable name keys
                        estr = ' '.join((oname, ' is not',
                                         'a known variable.'))
                        raise ValueError(estr)
                else:
                    # Variable name is in higher order list
                    if isinstance(nname, dict):
                        # Changing a variable name within a higher order object
                        label = [k for k in nname.keys()][0]
                        hdict[label] = nname[label]
                        # ensure variable is there
                        if label not in self.meta[oname]['children']:
                            estr = ''.join((label, ' is not a known ',
                                            'higher-order variable under ',
                                            oname, '.'))
                            raise ValueError(estr)
                        # Check for lowercase flag
                        if lowercase_data_labels:
                            gdict = {}
                            gdict[label] = nname[label].lower()
                        else:
                            gdict = hdict
                        # Change variables for frame at each time
                        for i in np.arange(len(self.index)):
                            # within data itself
                            self[i, oname].rename(columns=gdict,
                                                  inplace=True)

                        # Change metadata, once per variable only hdict used as
                        # it retains user provided case
                        self.meta.ho_data[oname].data.rename(hdict,
                                                             inplace=True)
                        # Clear out dict for next loop
                        hdict.pop(label)
                    else:
                        # Changing the outer 'column' label
                        fdict[oname] = nname

            # Rename regular variables, single go check for lower case data
            # labels first
            if lowercase_data_labels:
                gdict = {}
                for fkey in fdict:
                    gdict[fkey] = fdict[fkey].lower()
            else:
                gdict = fdict

            # Change variable names for attached data object
            self.data.rename(columns=gdict, inplace=True)

        else:
            # xarray renaming: account for lowercase data labels first
            if lowercase_data_labels:
                gdict = {}
                for vkey in var_names:
                    gdict[vkey] = var_names[vkey].lower()
            else:
                gdict = var_names
            self.data = self.data.rename(gdict)

            # Set up dictionary for renaming metadata variables
            fdict = var_names

        # Update normal metadata parameters in a single go.  The case must
        # always be preserved in Meta object
        new_fdict = {}
        for fkey in fdict:
            case_old = self.meta.var_case_name(fkey)
            new_fdict[case_old] = fdict[fkey]
        self.meta.data.rename(index=new_fdict, inplace=True)

        return

    def generic_meta_translator(self, input_meta):
        """Translates the metadata contained in an object into a dictionary

        Parameters
        ----------
        input_meta : Meta
            The metadata object to translate

        Returns
        -------
        dict
            A dictionary of the metadata for each variable of an output file
            e.g. netcdf4

        """
        export_dict = {}
        if self._meta_translation_table is not None:
            # Create a translation table for the actual values of the meta
            # labels. The instrument specific translation table only stores the
            # names of the attributes that hold the various meta labels
            translation_table = {}
            for key in self._meta_translation_table:
                translation_table[getattr(self, key)] = \
                    self._meta_translation_table[key]
        else:
            translation_table = None
        # First Order Data
        for key in input_meta.data.index:
            if translation_table is None:
                export_dict[key] = input_meta.data.loc[key].to_dict()
            else:
                # Translate each key if a translation is provided
                export_dict[key] = {}
                meta_dict = input_meta.data.loc[key].to_dict()
                for orig_key in meta_dict:
                    if orig_key in translation_table:
                        for translated_key in translation_table[orig_key]:
                            export_dict[key][translated_key] = \
                                meta_dict[orig_key]
                    else:
                        export_dict[key][orig_key] = meta_dict[orig_key]

        # Higher Order Data
        for key in input_meta.ho_data:
            if key not in export_dict:
                export_dict[key] = {}
            for ho_key in input_meta.ho_data[key].data.index:
                new_key = '_'.join((key, ho_key))
                if translation_table is None:
                    export_dict[new_key] = \
                        input_meta.ho_data[key].data.loc[ho_key].to_dict()
                else:
                    # Translate each key if a translation is provided
                    export_dict[new_key] = {}
                    meta_dict = \
                        input_meta.ho_data[key].data.loc[ho_key].to_dict()
                    for orig_key in meta_dict:
                        if orig_key in translation_table:
                            for translated_key in translation_table[orig_key]:
                                export_dict[new_key][translated_key] = \
                                    meta_dict[orig_key]
                        else:
                            export_dict[new_key][orig_key] = \
                                meta_dict[orig_key]
        return export_dict

    def load(self, yr=None, doy=None, end_yr=None, end_doy=None, date=None,
             end_date=None, fname=None, stop_fname=None, verifyPad=False):
        """Load instrument data into Instrument.data object.

        Parameters
        ----------
        yr : integer
            Year for desired data. pysat will load all files with an
            associated date between yr, doy and yr, doy + 1 (default=None)
        doy : integer
            Day of year for desired data. Must be present with yr input.
            (default=None)
        end_yr : integer
            Used when loading a range of dates, from yr, doy to end_yr, end_doy
            based upon the dates associated with the Instrument's files. Date
            range is inclusive for yr, doy but exclusive for end_yr, end_doy.
            (default=None)
        end_doy : integer
            Used when loading a range of dates, from yr, doy to end_yr, end_doy
            based upon the dates associated with the Instrument's files. Date
            range is inclusive for yr, doy but exclusive for end_yr, end_doy.
            (default=None)
        date : dt.datetime
            Date to load data. pysat will load all files with an associated
            date between date and date + 1 day (default=None)
        end_date : dt.datetime
            Used when loading a range of data from `date` to `end_date` based
            upon the dates associated with the Instrument's files. Date range
            is inclusive for date but exclusive for end_date. (default=None)
        fname : str or NoneType
            Filename to be loaded (default=None)
        stop_fname : str or NoneType
            Used when loading a range of filenames from `fname` to `stop_fname`,
            inclusive. (default=None)
        verifyPad : bool
            If True, padding data not removed for debugging. Padding
            parameters are provided at Instrument instantiation. (default=False)

        Raises
        ------
        TypeError
            For incomplete or incorrect input
        ValueError
            For input incompatible with Instrument set-up

        Note
        ----
        Loads data for a chosen instrument into .data. Any functions chosen
        by the user and added to the custom processing queue (.custom.attach)
        are automatically applied to the data before it is available to
        user in .data.

        A mixed combination of `.load()` keywords such as `yr` and `date` are
        not allowed.

        Note
        -----
            `end` kwargs have exclusive ranges (stop before the condition is
            reached), while `stop` kwargs have inclusive ranges (stop once the
            condition is reached).

        Examples
        --------
        ::

            import datetime as dt
            import pysat

            inst = pysat.Instrument('pysat', 'testing')

            # load a single day by year and day of year
            inst.load(2009, 1)

            # load a single day by date
            date = dt.datetime(2009, 1, 1)
            inst.load(date=date)

            # load a single file, first file in this example
            inst.load(fname=inst.files[0])

            # load a range of days, data between
            # Jan. 1st (inclusive) - Jan. 3rd (exclusive)
            inst.load(2009, 1, 2009, 3)

            # same procedure using datetimes
            date = dt.datetime(2009, 1, 1)
            end_date = dt.datetime(2009, 1, 3)
            inst.load(date=date, end_date=end_date)

            # same procedure using filenames
            # note the change in index due to inclusive slicing on filenames!
            inst.load(fname=inst.files[0], stop_fname=inst.files[1])

        """
        # Set options used by loading routine based upon user input
        if (yr is not None) and (doy is not None):
            if doy < 1 or (doy > 366):
                estr = ''.join(('Day of year (doy) is only valid between and ',
                                'including 1-366.'))
                raise ValueError(estr)

            # Verify arguments make sense, in context
            _check_load_arguments_none([fname, stop_fname, date, end_date],
                                       raise_error=True)
            # Convert yr/doy to a date
            date = dt.datetime.strptime("{:.0f} {:.0f}".format(yr, doy),
                                        "%Y %j")
            self._set_load_parameters(date=date, fid=None)

            if (end_yr is not None) and (end_doy is not None):
                if end_doy < 1 or (end_doy > 366):
                    estr = ''.join(('Day of year (end_doy) is only valid ',
                                    'between and including 1-366.'))
                    raise ValueError(estr)
                end_date = dt.datetime.strptime(
                    "{:.0f} {:.0f}".format(end_yr, end_doy), "%Y %j")
                self.load_step = end_date - date
            elif (end_yr is not None) or (end_doy is not None):
                estr = ''.join(('Both end_yr and end_doy must be set, ',
                                'or neither.'))
                raise ValueError(estr)
            else:
                # increment end by a day if none supplied
                self.load_step = dt.timedelta(days=1)

            curr = self.date

        elif date is not None:
            # Verify arguments make sense, in context
            _check_load_arguments_none([fname, stop_fname, yr, doy, end_yr,
                                        end_doy], raise_error=True)

            # Ensure date portion from user is only year, month, day
            self._set_load_parameters(date=date, fid=None)
            date = filter_datetime_input(date)

            # Increment after determining the desired step size
            if end_date is not None:
                # Support loading a range of dates
                self.load_step = end_date - date
            else:
                # Defaults to single day load
                self.load_step = dt.timedelta(days=1)
            curr = date

        elif fname is not None:
            # Verify arguments make sense, in context
            _check_load_arguments_none([yr, doy, end_yr, end_doy, date,
                                        end_date], raise_error=True)

            # Date will have to be set later by looking at the data
            self._set_load_parameters(date=None,
                                      fid=self.files.get_index(fname))

            # Check for loading by file range
            if stop_fname is not None:
                # Get index for both files so the delta may be computed
                idx1 = self.files.get_index(fname)
                idx2 = self.files.get_index(stop_fname)
                diff = idx2 - idx1
                if diff < 0:
                    estr = ''.join(('`stop_fname` must occur at a later date ',
                                    'than `fname`. Swapping filename inputs ',
                                    'will resolve the error.'))
                    raise ValueError(estr)
                else:
                    self.load_step = diff
            else:
                # Increment one file at a time
                self.load_step = 0
            curr = self._fid.copy()

        elif _check_load_arguments_none([yr, doy, end_yr, end_doy, date,
                                         end_date, fname, stop_fname]):
            # Empty call, treat as if all data requested
            if self.multi_file_day:
                estr = ''.join(('`load()` is not supported with multi_file_day',
                                '=True.'))
                raise ValueError(estr)
            if self.pad is not None:
                estr = ' '.join(('`load()` is not supported with data padding',
                                 'enabled.'))
                raise ValueError(estr)

            date = self.files.files.index[0]
            end_date = self.files.files.index[-1] + dt.timedelta(days=1)

            self._set_load_parameters(date=date, fid=None)
            curr = date
            self.load_step = end_date - date
        else:
            estr = 'Unknown or incomplete input combination.'
            raise TypeError(estr)

        self.orbits._reset()

        # If `pad` or `multi_file_day` is True, need to load three days/files
        loop_pad = self.pad if self.pad is not None \
            else dt.timedelta(seconds=0)

        # Check for constiency between loading range and data padding, if any
        if self.pad is not None:
            if self._load_by_date:
                tdate = dt.datetime(2009, 1, 1)
                if tdate + self.load_step < tdate + loop_pad:
                    estr = ''.join(('Data padding window must be shorter than ',
                                    'data loading window. Load a greater ',
                                    'range of data or shorten the padding.'))
                    raise ValueError(estr)
            else:
                # Loading by file
                wstr = ''.join(('Using a data padding window ',
                                'when loading by file can produce unexpected ',
                                'results whenever the padding window ',
                                'is longer than the range of data in a file. ',
                                'Improving the breadth of the padding window ',
                                'is planned for the future.'))
                logger.warning(wstr)

        if (self.pad is not None) or self.multi_file_day:
            if self._empty(self._next_data) and self._empty(self._prev_data):
                # Data has not already been loaded for previous and next days
                # load data for all three
                logger.info('Initializing three day/file window')

                # Using current date or fid
                self._prev_data, self._prev_meta = self._load_prev()
                self._curr_data, self._curr_meta = \
                    self._load_data(date=self.date, fid=self._fid,
                                    inc=self.load_step)
                self._next_data, self._next_meta = self._load_next()
            else:
                if self._next_data_track == curr:
                    # Moving forward in time
                    del self._prev_data
                    self._prev_data = self._curr_data
                    self._prev_meta = self._curr_meta
                    self._curr_data = self._next_data
                    self._curr_meta = self._next_meta
                    self._next_data, self._next_meta = self._load_next()
                elif self._prev_data_track == curr:
                    # Moving backward in time
                    del self._next_data
                    self._next_data = self._curr_data
                    self._next_meta = self._curr_meta
                    self._curr_data = self._prev_data
                    self._curr_meta = self._prev_meta
                    self._prev_data, self._prev_meta = self._load_prev()
                else:
                    # Jumped in time/or switched from filebased to date based
                    # access
                    del self._prev_data
                    del self._curr_data
                    del self._next_data
                    self._prev_data, self._prev_meta = self._load_prev()
                    self._curr_data, self._curr_meta = \
                        self._load_data(date=self.date, fid=self._fid,
                                        inc=self.load_step)
                    self._next_data, self._next_meta = self._load_next()

            # Make sure datetime indices for all data is monotonic
            if not self._index(self._prev_data).is_monotonic_increasing:
                self._prev_data.sort_index(inplace=True)
            if not self._index(self._curr_data).is_monotonic_increasing:
                self._curr_data.sort_index(inplace=True)
            if not self._index(self._next_data).is_monotonic_increasing:
                self._next_data.sort_index(inplace=True)

            # Make tracking indexes consistent with new loads
            if self._load_by_date:
                self._next_data_track = curr + self.load_step
                self._prev_data_track = curr - self.load_step
            else:
                # File and date loads have to be treated differently
                # due to change in inclusive/exclusive range end
                # treatment. Loading by file is inclusive.
                self._next_data_track = curr + self.load_step + 1
                self._prev_data_track = curr - self.load_step - 1

            # Attach data to object
            if not self._empty(self._curr_data):
                # The data being added isn't empty, so copy the data values
                # and the meta data values
                self.data = self._curr_data.copy()
                self.meta = self._curr_meta.copy()
            else:
                # If a new default/empty Meta is added here then it creates
                # a bug by potentially overwriting existing, good meta data
                # with an empty Meta object. For example, this will happen if
                # a multi-day analysis ends on a day with no data.
                # Do not re-introduce this issue.
                self.data = self._null_data.copy()

            # Load by file or by date, as specified
            if self._load_by_date:
                # Multi-file days can extend past a single day, only want data
                # from a specific date if loading by day.  Set up times for
                # the possible data padding coming up.
                first_time = self.date
                first_pad = self.date - loop_pad
                last_time = self.date + self.load_step
                last_pad = self.date + self.load_step + loop_pad
                want_last_pad = False
            elif (not self._load_by_date) and (not self.multi_file_day):
                # Loading by file, can't be a multi_file-day flag situation
                first_time = self._index(self._curr_data)[0]
                first_pad = first_time - loop_pad
                last_time = self._index(self._curr_data)[-1]
                last_pad = last_time + loop_pad
                want_last_pad = True
            else:
                raise ValueError(" ".join(("Can't have multi_file_day and load",
                                           "by file.")))

            # Pad data based upon passed parameter
            if (not self._empty(self._prev_data)) & (not self.empty):
                stored_data = self.data  # .copy()
                temp_time = copy.deepcopy(self.index[0])

                # Pad data using access mechanisms that works for both pandas
                # and xarray
                self.data = self._prev_data.copy()

                # __getitem__ used below to get data from instrument object.
                # Details for handling pandas and xarray are different and
                # handled by __getitem__
                self.data = self[first_pad:temp_time]
                if not self.empty:
                    if self.index[-1] == temp_time:
                        self.data = self[:-1]
                    self.concat_data(stored_data, prepend=False)
                else:
                    self.data = stored_data

            if (not self._empty(self._next_data)) & (not self.empty):
                stored_data = self.data  # .copy()
                temp_time = copy.deepcopy(self.index[-1])

                # Pad data using access mechanisms that work foro both pandas
                # and xarray
                self.data = self._next_data.copy()
                self.data = self[temp_time:last_pad]
                if not self.empty:
                    if (self.index[0] == temp_time):
                        self.data = self[1:]
                    self.concat_data(stored_data, prepend=True)
                else:
                    self.data = stored_data

            self.data = self[first_pad:last_pad]

            # Want exclusive end slicing behavior from above
            if not self.empty:
                if (self.index[-1] == last_pad) & (not want_last_pad):
                    self.data = self[:-1]

        # If self.pad is False, load single day
        else:
            self.data, meta = self._load_data(date=self.date, fid=self._fid,
                                              inc=self.load_step)
            if not self.empty:
                self.meta = meta

                # If only some metadata included, define the remaining variables
                warn_default = False
                for var in self.variables:
                    if var not in self.meta:
                        default_warn = "".join(["Metadata set to defaults, as",
                                                " they were missing in the ",
                                                "Instrument"])
                        warn_default = True
                        self.meta[var] = {self.meta.labels.name: var,
                                          self.meta.labels.notes: default_warn}

                if warn_default:
                    warnings.warn(default_warn, stacklevel=2)

        # Check if load routine actually returns meta
        if self.meta.data.empty:
            self.meta[self.variables] = {self.meta.labels.name: self.variables}

        # If loading by file set the yr, doy, and date
        if not self._load_by_date:
            if self.pad is not None:
                temp = first_time
            else:
                temp = self.index[0]
            self.date = dt.datetime(temp.year, temp.month, temp.day)
            self.yr, self.doy = utils.time.getyrdoy(self.date)

        # Ensure data is unique and monotonic. Check occurs after all the data
        # padding loads, or individual load. Thus, it can potentially check
        # issues with padding or with raw data
        if not (self.index.is_monotonic_increasing and self.index.is_unique):
            message = ''
            if not self.index.is_unique:
                message = ' '.join((message, 'Loaded data is not unique.'))
            if not self.index.is_monotonic_increasing:
                message = ' '.join((message, 'Loaded data is not',
                                   'monotonically increasing. '))
            if self.strict_time_flag:
                raise ValueError(' '.join((message, 'To continue to use data,'
                                           'set inst.strict_time_flag=False',
                                           'before loading data')))
            else:
                warnings.warn(message, stacklevel=2)

        # Apply the instrument preprocess routine, if data present
        if not self.empty:
            # Does not require self as input, as it is a partial func
            self._preprocess_rtn(**self.kwargs['preprocess'])

        # Clean data, if data is present and cleaning requested
        if (not self.empty) & (self.clean_level != 'none'):
            self._clean_rtn(**self.kwargs['clean'])

        # Apply custom functions via the nanokernel in self.custom
        if not self.empty:
            self.custom_apply_all()

        # Remove the excess data padding, if any applied
        if (self.pad is not None) & (not self.empty) & (not verifyPad):
            self.data = self[first_time: last_time]
            if not self.empty:
                if (self.index[-1] == last_time) & (not want_last_pad):
                    self.data = self[:-1]

        # Transfer any extra attributes in meta to the Instrument object
        self.meta.transfer_attributes_to_instrument(self)
        self.meta.mutable = False
        sys.stdout.flush()
        return

    def remote_file_list(self, start=None, stop=None, **kwargs):
        """List remote files for chosen instrument

        Parameters
        ----------
        start : dt.datetime or NoneType
            Starting time for file list. A None value will start with the first
            file found.
            (default=None)
        stop : dt.datetime or NoneType
            Ending time for the file list.  A None value will stop with the last
            file found.
            (default=None)
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments.
            The keyword arguments 'user' and 'password' are expected for remote
            databases requiring sign in or registration.

        Returns
        -------
        Series
            pandas Series of filenames indexed by date and time

        Note
        ----
        Default behaviour is to return all files.  User may additionally
        specify a given year, year/month, or year/month/day combination to
        return a subset of available files.

        """

        # Add the function kwargs
        kwargs["start"] = start
        kwargs["stop"] = stop

        # Add the user-supplied kwargs
        rtn_key = 'list_remote_files'
        if rtn_key in self.kwargs.keys():
            for user_key in self.kwargs[rtn_key].keys():
                # Don't overwrite kwargs supplied directly to this routine
                if user_key not in kwargs.keys():
                    kwargs[user_key] = self.kwargs[rtn_key][user_key]

        # Return the function call
        return self._list_remote_files_rtn(self.tag, self.inst_id, **kwargs)

    def remote_date_range(self, start=None, stop=None, **kwargs):
        """Returns fist and last date for remote data

        Parameters
        ----------
        start : dt.datetime or NoneType
            Starting time for file list. A None value will start with the first
            file found.
            (default=None)
        stop : dt.datetime or NoneType
            Ending time for the file list.  A None value will stop with the last
            file found.
            (default=None)
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments.
            The keyword arguments 'user' and 'password' are expected for remote
            databases requiring sign in or registration.

        Returns
        -------
        List
            First and last datetimes obtained from remote_file_list

        Note
        ----
        Default behaviour is to search all files.  User may additionally
        specify a given year, year/month, or year/month/day combination to
        return a subset of available files.

        """

        files = self.remote_file_list(start=start, stop=stop, **kwargs)
        return [files.index[0], files.index[-1]]

    def download_updated_files(self, **kwargs):
        """Grabs a list of remote files, compares to local, then downloads new
        files.

        Parameters
        ----------
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments

        Note
        ----
        Data will be downloaded to pysat_data_dir/patform/name/tag

        If Instrument bounds are set to defaults they are updated
        after files are downloaded.

        """

        # get list of remote files
        remote_files = self.remote_file_list()
        if remote_files.empty:
            logger.warning(' '.join(('No remote files found. Unable to',
                                     'download latest data.')))
            return

        # Get current list of local files
        self.files.refresh()
        local_files = self.files.files

        # Compare local and remote files. First look for dates that are in
        # remote but not in local
        new_dates = []
        for date in remote_files.index:
            if date not in local_files:
                new_dates.append(date)

        # Now compare filenames between common dates as it may be a new version
        # or revision.  This will have a problem with filenames that are
        # faking daily data from monthly.
        for date in local_files.index:
            if date in remote_files.index:
                if remote_files[date] != local_files[date]:
                    new_dates.append(date)
        logger.info(' '.join(('Found {} files that'.format(len(new_dates)),
                              'are new or updated.')))

        # download date for dates in new_dates (also includes new names)
        self.download(date_array=new_dates, **kwargs)

    def download(self, start=None, stop=None, freq='D', date_array=None,
                 **kwargs):
        """Download data for given Instrument object from start to stop.

        Parameters
        ----------
        start : pandas.datetime (yesterday)
            start date to download data
        stop : pandas.datetime (tomorrow)
            stop date (inclusive) to download data
        freq : string
            Stepsize between dates for season, 'D' for daily, 'M' monthly
            (see pandas)
        date_array : list-like
            Sequence of dates to download date for. Takes precedence over
            start and stop inputs
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments.
            The keyword arguments 'user' and 'password' are expected for remote
            databases requiring sign in or registration.

        Note
        ----
        Data will be downloaded to pysat_data_dir/patform/name/tag

        If Instrument bounds are set to defaults they are updated
        after files are downloaded.

        """
        # Make sure directories are there, otherwise create them
        try:
            os.makedirs(self.files.data_path)
        except OSError as err:
            if err.errno != errno.EEXIST:
                # ok if directories already exist.
                # Include message from original error.
                msg = ''.join(('There was a problem creating the path: ',
                               self.files.data_path,
                               ', to store downloaded data for ', self.platform,
                               self.name, '. ', err.message))
                raise ValueError(msg)

        if start is None and stop is None and date_array is None:
            # Defaults for downloads are set here rather than in the method
            # signature since method defaults are only set once! If an
            # Instrument object persists longer than a day then the download
            # defaults would no longer be correct. Dates are always correct in
            # this setup.
            logger.info(''.join(['Downloading the most recent data by ',
                                 'default (yesterday through tomorrow).']))
            start = self.yesterday()
            stop = self.tomorrow()
        elif stop is None and date_array is None:
            stop = start + dt.timedelta(days=1)

        logger.info('Downloading data to: {}'.format(self.files.data_path))

        if date_array is None:
            # Create range of dates for downloading data.  Make sure dates are
            # whole days
            start = filter_datetime_input(start)
            stop = filter_datetime_input(stop)
            date_array = utils.time.create_date_range(start, stop, freq=freq)

        # Add necessary kwargs to the optional kwargs
        kwargs['tag'] = self.tag
        kwargs['inst_id'] = self.inst_id
        kwargs['data_path'] = self.files.data_path
        for kwarg in self.kwargs['download']:
            if kwarg not in kwargs:
                kwargs[kwarg] = self.kwargs['download'][kwarg]

        # Download the data
        self._download_rtn(date_array, **kwargs)

        # get current file date range
        first_date = self.files.start_date
        last_date = self.files.stop_date

        logger.info('Updating pysat file list')
        self.files.refresh()

        # if instrument object has default bounds, update them
        if len(self.bounds[0]) == 1:
            # get current bounds
            curr_bound = self.bounds
            if self._iter_type == 'date':
                if (curr_bound[0][0] == first_date
                        and curr_bound[1][0] == last_date):
                    logger.info('Updating instrument object bounds by date.')
                    self.bounds = (self.files.start_date, self.files.stop_date,
                                   curr_bound[2], curr_bound[3])
            if self._iter_type == 'file':
                # Account for the fact the file datetimes may not land
                # exactly at start or end of a day.
                dsel1 = slice(first_date, first_date + dt.timedelta(hours=23,
                                                                    minutes=59,
                                                                    seconds=59))
                dsel2 = slice(last_date, last_date + dt.timedelta(hours=23,
                                                                  minutes=59,
                                                                  seconds=59))
                if (curr_bound[0][0] == self.files[dsel1][0]
                        and curr_bound[1][0] == self.files[dsel2][-1]):
                    logger.info('Updating instrument object bounds by file.')
                    dsel1 = slice(self.files.start_date,
                                  self.files.start_date
                                  + dt.timedelta(hours=23, minutes=59,
                                                 seconds=59))
                    dsel2 = slice(self.files.stop_date, self.files.stop_date
                                  + dt.timedelta(hours=23, minutes=59,
                                                 seconds=59))
                    self.bounds = (self.files[dsel1][0],
                                   self.files[dsel2][-1],
                                   curr_bound[2], curr_bound[3])

        return

    def to_netcdf4(self, fname=None, base_instrument=None, epoch_name='Epoch',
                   zlib=False, complevel=4, shuffle=True,
                   preserve_meta_case=False, export_nan=None,
                   unlimited_time=True):
        """Stores loaded data into a netCDF4 file.

        Parameters
        ----------
        fname : str
            full path to save instrument object to
        base_instrument : pysat.Instrument
            used as a comparison, only attributes that are present with
            self and not on base_instrument are written to netCDF
        epoch_name : str
            Label in file for datetime index of Instrument object
        zlib : bool
            Flag for engaging zlib compression (True - compression on)
        complevel : int
            an integer between 1 and 9 describing the level of compression
            desired. Ignored if zlib=False. (default=4)
        shuffle : bool
            The HDF5 shuffle filter will be applied before compressing the data.
            This significantly improves compression. Ignored if zlib=False.
            (default=True)
        preserve_meta_case : bool
            if True, then the variable strings within the MetaData object, which
            preserves case, are used to name variables in the written netCDF
            file.
            If False, then the variable strings used to access data from the
            Instrument object are used instead. By default, the variable strings
            on both the data and metadata side are the same, though this
            relationship may be altered by a user. (default=False)
        export_nan : list or None
             By default, the metadata variables where a value of NaN is allowed
             and written to the netCDF4 file is maintained by the Meta object
             attached to the pysat.Instrument object. A list supplied here
             will override the settings provided by Meta, and all parameters
             included will be written to the file. If not listed
             and a value is NaN then that attribute simply won't be included in
             the netCDF4 file. (default=None)
        unlimited_time : bool
             If True, then the main epoch dimension will be set to 'unlimited'
             within the netCDF4 file. (default=True)

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

        # Check export nans first
        if export_nan is None:
            export_nan = self.meta._export_nan

        # Base_instrument used to define the standard attributes attached
        # to the instrument object. Any additional attributes added
        # to the main input Instrument will be written to the netCDF4
        base_instrument = Instrument() if base_instrument is None \
            else base_instrument

        # Begin processing metadata for writing to the file. Look to see if
        # user supplied a list of export keys corresponding to internally
        # tracked metadata within pysat
        export_meta = self.generic_meta_translator(self.meta)
        if self._meta_translation_table is None:
            # Didn't find a translation table, using the strings
            # attached to the supplied pysat.Instrument object
            export_name_labels = [self.meta.labels.name]
            export_units_labels = [self.meta.labels.units]
            export_desc_labels = [self.meta.labels.desc]
            export_notes_labels = [self.meta.labels.notes]
        else:
            # User supplied labels in translation table
            export_name_labels = self._meta_translation_table['name']
            export_units_labels = self._meta_translation_table['units']
            export_desc_labels = self._meta_translation_table['desc']
            export_notes_labels = self._meta_translation_table['notes']
            logger.info(' '.join(('Using Metadata Translation Table:',
                                  str(self._meta_translation_table))))

        # Apply instrument specific post-processing to the export_meta
        if hasattr(self._export_meta_post_processing, '__call__'):
            export_meta = self._export_meta_post_processing(export_meta)

        # Check if there are multiple variables with same characters
        # but with different case
        lower_variables = [var.lower() for var in self.variables]
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
            # number of items, yeah
            num = len(self.index)

            # write out the datetime index
            if unlimited_time:
                out_data.createDimension(epoch_name, None)
            else:
                out_data.createDimension(epoch_name, num)
            cdfkey = out_data.createVariable(epoch_name, 'i8',
                                             dimensions=(epoch_name),
                                             zlib=zlib,
                                             complevel=complevel,
                                             shuffle=shuffle)

            # grab existing metadata for Epoch or create suitable info
            if epoch_name in self.meta:
                new_dict = export_meta[self.meta.var_case_name(epoch_name)]
            else:
                # create empty shell
                new_dict = {}

            # update required and basic information if not present
            for export_name_label in export_name_labels:
                if export_name_label not in new_dict:
                    new_dict[export_name_label] = epoch_name

            for export_units_label in export_units_labels:
                if export_units_label not in new_dict:
                    new_dict[export_units_label] = \
                        'Milliseconds since 1970-1-1 00:00:00'

            for export_desc_label in export_desc_labels:
                if export_desc_label not in new_dict:
                    new_dict[export_desc_label] = \
                        'Milliseconds since 1970-1-1 00:00:00'

            for export_notes_label in export_notes_labels:
                if export_notes_label not in new_dict:
                    new_dict[export_notes_label] = ''

            new_dict['calendar'] = 'standard'
            new_dict['Format'] = 'i8'
            new_dict['Var_Type'] = 'data'
            if self.index.is_monotonic_increasing:
                new_dict['MonoTon'] = 'increase'
            elif self.index.is_monotonic_decreasing:
                new_dict['MonoTon'] = 'decrease'
            new_dict['Time_Base'] = 'Milliseconds since 1970-1-1 00:00:00'
            new_dict['Time_Scale'] = 'UTC'
            new_dict = self._filter_netcdf4_metadata(new_dict, np.int64,
                                                     export_nan=export_nan)
            # attach metadata
            cdfkey.setncatts(new_dict)

            # attach data
            cdfkey[:] = (self.index.values.astype(np.int64)
                         * 1.E-6).astype(np.int64)

            # iterate over all of the columns in the Instrument dataframe
            # check what kind of data we are dealing with, then store
            for key in self.variables:
                # get information on type data we are dealing with
                # data is data in proer type( multiformat support)
                # coltype is the direct type, np.int64
                # and datetime_flag lets you know if the data is full of time
                # information
                if preserve_meta_case:
                    # use the variable case stored in the MetaData object
                    case_key = self.meta.var_case_name(key)
                else:
                    # use variable names used by user when working with data
                    case_key = key

                data, coltype, datetime_flag = self._get_data_info(self[key])

                # operate on data based upon type
                if self[key].dtype != np.dtype('O'):
                    # not an object, normal basic 1D data
                    cdfkey = out_data.createVariable(case_key,
                                                     coltype,
                                                     dimensions=(epoch_name),
                                                     zlib=zlib,
                                                     complevel=complevel,
                                                     shuffle=shuffle)

                    # attach any meta data, after filtering for standards
                    try:
                        # attach dimension metadata
                        new_dict = export_meta[case_key]
                        new_dict['Depend_0'] = epoch_name
                        new_dict['Display_Type'] = 'Time Series'
                        new_dict['Format'] = self._get_var_type_code(coltype)
                        new_dict['Var_Type'] = 'data'
                        new_dict = self._filter_netcdf4_metadata(
                            new_dict, coltype, export_nan=export_nan)
                        cdfkey.setncatts(new_dict)
                    except KeyError as err:
                        logger.info(' '.join((str(err), '\n',
                                              ' '.join(('Unable to find'
                                                        'MetaData for',
                                                        key)))))
                    # assign data
                    if datetime_flag:
                        # datetime is in nanoseconds, storing milliseconds
                        cdfkey[:] = (data.values.astype(coltype)
                                     * 1.0E-6).astype(coltype)
                    else:
                        # not datetime data, just store as is
                        cdfkey[:] = data.values.astype(coltype)

                # back to main check on type of data to write
                else:
                    # It is a Series of objects.  First, figure out what the
                    # individual object typess are.  Then, act as needed.

                    # Use info in coltype to get real datatype of object
                    if (coltype == str):
                        cdfkey = out_data.createVariable(case_key,
                                                         coltype,
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
                            new_dict['Format'] = self._get_var_type_code(
                                coltype)
                            new_dict['Var_Type'] = 'data'

                            # No FillValue or FillVal allowed for strings
                            new_dict = self._filter_netcdf4_metadata(
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
                    # strings.  Maps to `if` check on coltypes, being
                    # string-based.
                    else:
                        # Presuming a series with a dataframe or series in each
                        # location start by collecting some basic info on
                        # dimensions sizes, names, then create corresponding
                        # netCDF4 dimensions total dimensions stored for object
                        # are epoch plus ones created below
                        dims = np.shape(self[key].iloc[0])
                        obj_dim_names = []
                        if len(dims) == 1:
                            # generally working with higher dimensional data
                            # pad dimensions so that the rest of the code works
                            # for either a Series or a Frame
                            dims = (dims[0], 0)
                        for i, dim in enumerate(dims[:-1]):
                            # don't need to go over last dimension value,
                            # it covers number of columns (if a frame)
                            obj_dim_names.append(case_key)
                            out_data.createDimension(obj_dim_names[-1], dim)

                        # create simple tuple with information needed to create
                        # the right dimensions for variables that will
                        # be written to file
                        var_dim = tuple([epoch_name] + obj_dim_names)

                        # We need to do different things if a series or
                        # dataframe stored
                        try:
                            # start by assuming it is a dataframe
                            # get list of subvariables
                            iterable = self[key].iloc[0].columns

                            # store our newfound knowledge, we are dealing with
                            # a series of DataFrames
                            is_frame = True
                        except AttributeError:
                            # turns out data is Series of Series
                            # which doesn't have columns
                            iterable = [self[key].iloc[0].name]
                            is_frame = False

                        # find location within main variable that actually
                        # has subvariable data (not just empty frame/series)
                        # so we can determine what the real underlying data
                        # types are
                        good_data_loc = 0
                        for jjj in np.arange(len(self.data)):
                            if len(self.data[key].iloc[0]) > 0:
                                data_loc = jjj
                                break

                        # found a place with data, if there is one
                        # now iterate over the subvariables, get data info
                        # create netCDF4 variables and store the data
                        # stored name is variable_subvariable
                        for col in iterable:
                            if is_frame:
                                # we are working with a dataframe so
                                # multiple subvariables stored under a single
                                # main variable heading
                                idx = self[key].iloc[good_data_loc][col]
                                data, coltype, _ = self._get_data_info(idx)
                                cdfkey = out_data.createVariable(
                                    '_'.join((case_key, col)), coltype,
                                    dimensions=var_dim, zlib=zlib,
                                    complevel=complevel, shuffle=shuffle)

                                # attach any meta data
                                try:
                                    new_dict = export_meta['_'.join((case_key,
                                                                     col))]
                                    new_dict['Depend_0'] = epoch_name
                                    new_dict['Depend_1'] = obj_dim_names[-1]
                                    new_dict['Display_Type'] = 'Spectrogram'
                                    new_dict['Format'] = \
                                        self._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    new_dict = self._filter_netcdf4_metadata(
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
                                        self[key].iloc[i][col].values

                                # Write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                            else:
                                # We are dealing with a Series.  Get
                                # information from within the series
                                idx = self[key].iloc[good_data_loc]
                                data, coltype, _ = self._get_data_info(idx)
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
                                        self._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    new_dict = self._filter_netcdf4_metadata(
                                        new_dict, coltype,
                                        export_nan=export_nan)

                                    # Really attach metadata now
                                    cdfkey.setncatts(new_dict)
                                except KeyError as err:
                                    logger.info(' '.join((str(err), '\n',
                                                          'Unable to find ',
                                                          'MetaData for,',
                                                          key)))
                                # attach data
                                temp_cdf_data = np.zeros(
                                    (num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = self[i, key].values
                                # write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                        # We are done storing the actual data for the given
                        # higher order variable. Now we need to store the index
                        # for all of that fancy data.

                        # Get index information
                        idx = good_data_loc
                        data, coltype, datetime_flag = self._get_data_info(
                            self[key].iloc[idx].index)

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
                        new_dict['Format'] = self._get_var_type_code(coltype)
                        new_dict['Var_Type'] = 'data'

                        if datetime_flag:
                            for export_name_label in export_name_labels:
                                new_dict[export_name_label] = epoch_name
                            for export_units_label in export_units_labels:
                                new_dict[export_units_label] = \
                                    'Milliseconds since 1970-1-1 00:00:00'
                            new_dict = self._filter_netcdf4_metadata(
                                new_dict, coltype, export_nan=export_nan)

                            # Set metadata dict
                            cdfkey.setncatts(new_dict)

                            # Set data
                            temp_cdf_data = np.zeros((num,
                                                      dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = self[i, key].index.values
                            cdfkey[:, :] = (temp_cdf_data.astype(coltype)
                                            * 1.E-6).astype(coltype)

                        else:
                            if self[key].iloc[data_loc].index.name is not None:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = \
                                        self[key].iloc[data_loc].index.name
                            else:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = key
                            new_dict = self._filter_netcdf4_metadata(
                                new_dict, coltype, export_nan=export_nan)

                            # Assign metadata dict
                            cdfkey.setncatts(new_dict)

                            # Set data
                            temp_cdf_data = np.zeros(
                                (num, dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = \
                                    self[key].iloc[i].index.astype(str)
                            cdfkey[:, :] = temp_cdf_data.astype(coltype)

            # Store any non standard attributes. Compare this Instrument's
            # attributes to base object
            base_attrb = dir(base_instrument)
            this_attrb = dir(self)

            # Filter out any 'private' attributes (those that start with a '_')
            adict = {}
            for key in this_attrb:
                if key not in base_attrb:
                    if key[0] != '_':
                        adict[key] = self.__getattribute__(key)

            # Add additional metadata to conform to standards
            adict['pysat_version'] = pysat.__version__
            if 'Conventions' not in adict:
                adict['Conventions'] = 'SPDF ISTP/IACG Modified for NetCDF'
            if 'Text_Supplement' not in adict:
                adict['Text_Supplement'] = ''

            # Remove any attributes with the names below.
            # pysat is responible for including them in the file.
            items = ['Date_End', 'Date_Start', 'File', 'File_Date',
                     'Generation_Date', 'Logical_File_ID']
            for item in items:
                if item in adict:
                    _ = adict.pop(item)

            adict['Date_End'] = dt.datetime.strftime(
                self.index[-1], '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f')
            adict['Date_End'] = adict['Date_End'][:-3] + ' UTC'

            adict['Date_Start'] = dt.datetime.strftime(
                self.index[0], '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f')
            adict['Date_Start'] = adict['Date_Start'][:-3] + ' UTC'
            adict['File'] = os.path.split(fname)
            adict['File_Date'] = self.index[-1].strftime(
                '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f')
            adict['File_Date'] = adict['File_Date'][:-3] + ' UTC'
            adict['Generation_Date'] = dt.datetime.utcnow().strftime('%Y%m%d')
            adict['Logical_File_ID'] = os.path.split(fname)[-1].split('.')[:-1]

            # check for binary types, convert when found
            for key in adict.keys():
                if adict[key] is None:
                    adict[key] = ''
                elif isinstance(adict[key], bool):
                    adict[key] = int(adict[key])

            # attach attributes
            out_data.setncatts(adict)
        return


#
# ----------------------------------------------
#   Utilities supporting the Instrument Object
# ----------------------------------------------
#


def _kwargs_keys_to_func_name(kwargs_key):
    """ Convert from self.kwargs key name to the function/method name

    Parameters
    ----------
    kwargs_key : str
        Key from self.kwargs dictionary

    Returns
    -------
    func_name : str
        Name of method or function associated with the input key

    """

    func_name = '_{:s}_rtn'.format(kwargs_key)
    return func_name


def _get_supported_keywords(local_func):
    """Return a dict of supported keywords

    Parameters
    ----------
    local_func : Python method or functools.partial
        Method used to load data within pysat

    Returns
    -------
    out_dict : dict
        dict of supported keywords and default values


    Note
    ----
    If the input is a partial function then the list of keywords returned only
    includes keywords that have not already been set as part of the
    functools.partial instantiation.

    """
    # account for keywords that are treated by Instrument as args
    pre_kws = ['fnames', 'inst_id', 'tag', 'date_array', 'data_path',
               'format_str', 'supported_tags', 'start', 'stop', 'freq']

    # check if partial function
    if isinstance(local_func, functools.partial):
        # get keyword arguments already applied to function
        existing_kws = local_func.keywords

        # pull out python function portion
        local_func = local_func.func
    else:
        existing_kws = {}

    # account for keywords already set since input was a partial function
    pre_kws.extend(existing_kws.keys())

    # Get the lists of arguments and defaults
    # The args and kwargs are both in the args list, and args are placed first
    #
    # modified from code on
    # https://stackoverflow.com/questions/196960/
    # can-you-list-the-keyword-arguments-a-function-receives
    sig = inspect.getfullargspec(local_func)
    func_args = list(sig.args)

    # Recast the function defaults as a list instead of NoneType or tuple.
    # inspect returns func_defaults=None when there are no defaults
    if sig.defaults is None:
        func_defaults = []
    else:
        func_defaults = [dval for dval in sig.defaults]

    # Remove arguments from the start of the func_args list
    while len(func_args) > len(func_defaults):
        func_args.pop(0)

    # Remove pre-existing keywords from output. Start by identifying locations
    pop_list = [i for i, arg in enumerate(func_args) if arg in pre_kws]

    # Remove pre-selected by cycling backwards through the list of indices
    for i in pop_list[::-1]:
        func_args.pop(i)
        func_defaults.pop(i)

    # Create the output dict
    out_dict = {akey: func_defaults[i] for i, akey in enumerate(func_args)}

    return out_dict


def _pass_func(*args, **kwargs):
    """ Default function for updateable Instrument methods
    """
    pass


def _check_load_arguments_none(args, raise_error=False):
    """Ensure all arguments are None.

    Used to support .load method checks that arguments that should be
    None are None, while also keeping the .load method readable.

    Parameters
    ----------
    args : iterable object
        Variables that are to checked to ensure None
    raise_error : bool
        If True, an error is raised if all args aren't None (default=False)

    Raises
    ------
    ValueError
        If all args aren't None and raise_error is True

    Raises
    -------
    bool
        True, if all args are None

    """

    all_none = True
    for arg in args:
        if arg is not None:
            all_none = False
            if raise_error:
                estr = ''.join(('An inconsistent set of inputs have been ',
                                'supplied as input. Please double-check that ',
                                'only date, filename, or year/day of year ',
                                'combinations are provided.'))
                raise ValueError(estr)

    return all_none
