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

import numpy as np
import pandas as pds
import xarray as xr

import pysat


class Instrument(object):
    """Download, load, manage, modify and analyze science data.

    Parameters
    ----------
    platform : str or NoneType
        Name of instrument platform. If None and `name` is also None, creates an
        Instrument with empty `platform` and `name` attributes. (default=None)
    name : str or NoneType
        Name of instrument. If None and `platform` is also None, creates an
        Instrument with empty `platform` and `name` attributes. (default=None)
    tag : str
        Identifies particular subset of instrument data (default='')
    inst_id : str
        Secondary level of identification, such as spacecraft within a
        constellation platform (default='')
    clean_level : str or NoneType
        Level of data quality. If not provided, will default to the
        setting in `pysat.params['clean_level']`. (default=None)
    update_files : bool or NoneType
        If True, immediately query filesystem for instrument files and store.
        If False, the local files are presumed to be the same. By default,
        this setting will be obtained from `pysat.params` (default=None)
    pad : pandas.DateOffset, dict, or NoneType
        Length of time to pad the begining and end of loaded data for
        time-series processing. Extra data is removed after applying all
        custom functions. Dictionary, if supplied, is simply passed to
        pandas DateOffset. (default=None)
    orbit_info : dict or NoneType
        Orbit information, {'index': index, 'kind': kind, 'period': period}.
        See pysat.Orbits for more information.  (default=None)
    inst_module : module or NoneType
        Provide instrument module directly, takes precedence over platform/name.
        (default=None)
    data_dir : str
        Directory without sub-directory variables that allows one to
        bypass the directories provided by pysat.params['data_dirs'].  Only
        applied if the directory exists. (default='')
    directory_format : str, function, or NoneType
        Sub-directory naming structure, which is expected to exist or be
        created within one of the `python.params['data_dirs']` directories.
        Variables such as `platform`, `name`, `tag`, and `inst_id` will be
        filled in as needed using python string formatting, if a string is
        supplied. The default directory structure, which is used if None is
        specified, is provided by pysat.params['directory_format'] and is
        typically '{platform}/{name}/{tag}/{inst_id}'. If a function is
        provided, it must take `tag` and `inst_id` as arguments and return an
        appropriate string. (default=None)
    file_format : str or NoneType
        File naming structure in string format.  Variables such as `year`,
        `month`, `day`, etc. will be filled in as needed using python
        string formatting.  The default file format structure is supplied
        in the instrument `list_files` routine. See
        `pysat.files.parse_delimited_filenames` and
        `pysat.files.parse_fixed_width_filenames` for more information.
        The value will be None if not specified by the user at instantiation.
        (default=None)
    temporary_file_list : bool
        If true, the list of Instrument files will not be written to disk
        (default=False)
    strict_time_flag : bool
        If true, pysat will check data to ensure times are unique and
        monotonically increasing (default=True)
    ignore_empty_files : bool
        Flag controling behavior for listing available files. If True, the list
        of files found will be checked to ensure the filesizes are greater than
        zero. Empty files are removed from the stored list of files.
        (default=False)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', float),
        'max_val': ('value_max', float), 'fill_val': ('fill', float)})
    custom : list or NoneType
        Input list containing dicts of inputs for `custom_attach` method inputs
        that may be applied or None (default=None)

    Attributes
    ----------
    platform
    name
    tag
    inst_id
    clean_level
    pad
    orbit_info
    inst_module
    data_dir
    directory_format
    file_format
    temporary_file_list
    strict_time_flag
    bounds : tuple
        Tuple of datetime objects or filenames indicating bounds for loading
        data, or a tuple of NoneType objects. Users may provide as a tuple or
        tuple of lists (useful for bounds with gaps). The attribute is always
        stored as a tuple of lists for consistency.
    custom_functions : list
        List of functions to be applied by instrument nano-kernel
    custom_args : list
        List of lists containing arguments to be passed to particular
        custom function
    custom_kwargs : list
        List of dictionaries with keywords and values to be passed
        to a custom function
    data : pandas.DataFrame or xarray.Dataset
        Class object holding the loaded science data
    date : dt.datetime or NoneType
        Date and time for loaded data, None if no data is loaded
    doy : int or NoneType
        Day of year for loaded data, None if no data is loaded
    files : pysat.Files
        Class to hold and interact with the available instrument files
    kwargs : dict
        Keyword arguments passed to the standard Instrument routines
    kwargs_supported : dict
        Stores all supported keywords for user edification
    kwargs_reserved : dict
        Keyword arguments for reserved method arguments
    load_step : dt.timedelta
        The temporal increment for loading data, defaults to a timestep of one
        day
    meta : pysat.Meta
        Class holding the instrument metadata
    meta_labels : dict
        Dict containing defaults for new Meta data labels
    orbits : pysat.Orbits
        Interface to extracting data orbit-by-orbit
    pandas_format : bool
        Flag indicating whether `data` is stored as a pandas.DataFrame (True)
        or an xarray.Dataset (False)
    today : dt.datetime
        Date and time for the current day in UT
    tomorrow : dt.datetime
        Date and time for tomorrow in UT
    variables : list
        List of loaded data variables
    yesterday : dt.datetime
        Date and time for yesterday in UT
    yr : int or NoneType
        Year for loaded data, None if no data is loaded

    Raises
    ------
    ValueError
        If platform and name are mixture of None and str, an unknown or reserved
         keyword is used, or if `file_format`, `custom`, or `pad` are improperly
         formatted

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
        vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b')
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2009, 1, 2)
        vefi.download(start, stop)
        vefi.load(date=start)
        print(vefi['dB_mer'])
        print(vefi.meta['db_mer'])

        # 1-second thermal plasma parameters
        ivm = pysat.Instrument(platform='cnofs', name='ivm')
        ivm.download(start, stop)
        ivm.load(2009, 1)
        print(ivm['ionVelmeridional'])

        # Ionosphere profiles from GPS occultation. Enable binning profile
        # data using a constant step-size. Feature provided by the underlying
        # COSMIC support code.
        cosmic = pysat.Instrument('cosmic', 'gps', 'ionprf', altitude_bin=3)
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
        # order these functions will run is: 3, 1, 2.
        custom = [custom_func_1, custom_func_2, custom_func_3]

        # Instantiate `pysat.Instrument`
        inst = pysat.Instrument(platform, name, inst_id=inst_id, tag=tag,
                                custom=custom)

    """

    # -----------------------------------------------------------------------
    # Define all magic methods

    def __init__(self, platform=None, name=None, tag='', inst_id='',
                 clean_level=None, update_files=None, pad=None,
                 orbit_info=None, inst_module=None, data_dir='',
                 directory_format=None, file_format=None,
                 temporary_file_list=False, strict_time_flag=True,
                 ignore_empty_files=False,
                 labels={'units': ('units', str), 'name': ('long_name', str),
                         'notes': ('notes', str), 'desc': ('desc', str),
                         'min_val': ('value_min', np.float64),
                         'max_val': ('value_max', np.float64),
                         'fill_val': ('fill', np.float64)},
                 custom=None, **kwargs):
        """Initialize `pysat.Instrument` object."""

        # Check for deprecated usage of None
        if None in [tag, inst_id]:
            warnings.warn(" ".join(["The usage of None in `tag` and `inst_id`",
                                    "has been deprecated and will be removed",
                                    "in 3.2.0+. Please use '' instead of",
                                    "None."]),
                          DeprecationWarning, stacklevel=2)

        # Set default tag, inst_id, and Instrument module
        self.tag = '' if tag is None else tag.lower()
        self.inst_id = '' if inst_id is None else inst_id.lower()

        self.inst_module = inst_module

        if self.inst_module is None:
            # Use strings to look up module name
            if isinstance(platform, str) and isinstance(name, str):
                self.platform = platform.lower()
                self.name = name.lower()

                if len(self.platform) > 0:
                    # Look to module for instrument functions and defaults
                    self._assign_attrs(by_name=True)
                else:
                    # Assign defaults since string is empty
                    self._assign_attrs()
            elif (platform is None) and (name is None):
                # Creating "empty" Instrument object with this path
                self.name = ''
                self.platform = ''
                self._assign_attrs()
            else:
                raise ValueError(' '.join(('Inputs platform and name must both',
                                           'be strings, or both None.')))
        else:
            # Check if user supplied platform or name
            if isinstance(platform, str) or isinstance(name, str):
                warnings.warn(" ".join(("inst_module supplied along with",
                                        "platform/name. Defaulting to",
                                        "inst_module specification.",
                                        "platform =", self.inst_module.platform,
                                        ", name =", self.inst_module.name)),
                              stacklevel=2)

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
            self._assign_attrs()

        # Store kwargs, passed to standard routines first
        self.kwargs = {}
        self.kwargs_supported = {}
        self.kwargs_reserved = _reserved_keywords.copy()
        saved_keys = []

        # Expected function keywords
        exp_keys = ['list_files', 'load', 'preprocess', 'download',
                    'list_remote_files', 'clean', 'init']
        for fkey in exp_keys:
            func_name = _kwargs_keys_to_func_name(fkey)
            func = getattr(self, func_name)

            # Get dict of supported keywords and values
            default_kwargs = _get_supported_keywords(func)

            # Expand the dict to include method keywords for load.
            # TODO(#1020): Remove this if statement for the 3.2.0+ release
            if fkey == 'load':
                meth = getattr(self, fkey)
                default_kwargs.update(_get_supported_keywords(meth))

            # Confirm there are no reserved keywords present
            for kwarg in kwargs.keys():
                if kwarg in self.kwargs_reserved:
                    estr = ''.join(('Reserved keyword "', kwarg, '" is not ',
                                    'allowed at instantiation.'))
                    raise ValueError(estr)

            # Check if kwargs are in list
            good_kwargs = [ckey for ckey in kwargs.keys()
                           if ckey in default_kwargs]

            # Store appropriate user supplied keywords for this function
            self.kwargs[fkey] = {gkey: kwargs[gkey] for gkey in good_kwargs}

            # Store all supported keywords for user edification
            self.kwargs_supported[fkey] = default_kwargs

            # Store keys to support check that all user supplied
            # keys are used.
            saved_keys.extend(default_kwargs.keys())

        # Test for user supplied keys that are not used
        missing_keys = []
        for custom_key in kwargs:
            if custom_key not in saved_keys and (custom_key not in exp_keys):
                missing_keys.append(custom_key)

        if len(missing_keys) > 0:
            raise ValueError('unknown keyword{:s} supplied: {:}'.format(
                '' if len(missing_keys) == 1 else 's', missing_keys))

        # More reasonable defaults for optional parameters
        self.clean_level = (clean_level.lower() if clean_level is not None
                            else pysat.params['clean_level'])

        # Assign `strict_time_flag`
        self.strict_time_flag = strict_time_flag

        # Assign directory format information, which tells pysat how to look in
        # sub-directories for files.
        if directory_format is not None:
            # `assign_func` sets some instrument defaults, but user inputs
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

        # Assign an absolute path for files that may not be part of the
        # standard pysat directory structure
        if os.path.isdir(data_dir):
            self.data_dir = data_dir
        else:
            if len(data_dir) > 0:
                pysat.logger.warning("data directory doesn't exist: {:}".format(
                    data_dir))
            self.data_dir = None

        # Check to make sure value is reasonable
        if self.file_format is not None:
            # Check if it is an iterable string
            if(not isinstance(self.file_format, str)
               or (self.file_format.find("{") < 0)
               or (self.file_format.find("}") < 0)):
                raise ValueError(''.join(['file format set to default, ',
                                          'supplied string must be iterable ',
                                          '[{:}]'.format(self.file_format)]))

        # Set up empty data and metadata.
        # Assign null data for user selected data type, `_null_data` assigned
        # when `self.pandas_format` is set in `_assign_attrs`.
        self.data = self._null_data.copy()

        # Create Meta instance with appropriate labels.  Meta class methods will
        # use Instrument definition of MetaLabels over the Metadata declaration.
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

        # Instantiate the Files class
        temporary_file_list = not temporary_file_list

        if ignore_empty_files is None:
            ignore_empty_files = pysat.params['ignore_empty_files']
        if update_files is None:
            update_files = pysat.params['update_files']

        self.files = pysat.Files(self, data_dir=self.data_dir,
                                 directory_format=self.directory_format,
                                 update_files=update_files,
                                 file_format=self.file_format,
                                 write_to_disk=temporary_file_list,
                                 ignore_empty_files=ignore_empty_files)

        # Set bounds for iteration. `self.bounds` requires the Files class, and
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

        # Create empty placeholder for the meta translation table, which
        # provides information about how to label metadata for netcdf export.
        # If None, pysat metadata labels will be used instead.
        self._meta_translation_table = None

        # Create a placeholder for a post-processing function to be applied
        # to the metadata dictionary before export. If None, no post-processing
        # will occur.
        self._export_meta_post_processing = None

        # Start with a daily increment for loading
        self.load_step = dt.timedelta(days=1)

        # Store base attributes, used in particular by Meta class
        self._base_attr = dir(self)

        # Run instrument init function, a basic pass function is used if the
        # user doesn't supply the init function
        self._init_rtn(**self.kwargs['init'])

        return

    def __eq__(self, other):
        """Perform equality check.

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
                        # General check for everything else
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
        """Print the basic Instrument properties."""

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

        # Get the `inst_module` string
        if self.inst_module is None:
            istr = "None"
        else:
            istr = getattr(self.inst_module, "__name__")

        # Create string for other parts Instrument instantiation
        out_str = "".join(["pysat.Instrument(platform='", self.platform,
                           "', name='", self.name, "', tag='", self.tag,
                           "', inst_id='", self.inst_id,
                           "', clean_level='", self.clean_level,
                           "', pad={:}, orbit_info=".format(self.pad),
                           "{:}, ".format(self.orbit_info),
                           "inst_module=", istr, ", custom=", cstr,
                           ", **{:}".format(in_kwargs), ")"])

        return out_str

    def __str__(self):
        """Descriptively print the basic Instrument properties."""

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
            output_str += 'Date: ' + self.date.strftime('%d %B %Y') + '\n'
            output_str += 'DOY: {:03d}\n'.format(self.doy)
            output_str += 'Time range: '
            output_str += self.index[0].strftime('%d %B %Y %H:%M:%S')
            output_str += ' --- '
            output_str += self.index[-1].strftime('%d %B %Y %H:%M:%S\n')
            output_str += 'Number of Times: {:d}\n'.format(len(self.index))
            output_str += 'Number of variables: {:d}\n'.format(
                len(self.variables))

            output_str += '\nVariable Names:\n'
            output_str += pysat.utils._core.fmt_output_in_cols(self.variables)

            # Print the short version of the metadata
            output_str += '\n{:s}'.format(self.meta.__str__(long_str=False))
        else:
            output_str += 'No loaded data.\n'

        return output_str

    def __getitem__(self, key):
        """Access data in `pysat.Instrument` object.

        Parameters
        ----------
        key : str, tuple, or dict
            Data variable name, tuple with a slice, or dict used to locate
            desired data.

        Raises
        ------
        ValueError
            When an underlying error for data access is raised

        Note
        ----
        `inst['name']` is equivalent to `inst.data.name`

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

            # Slicing by date, inclusive.
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
                except (KeyError, TypeError) as err1:
                    # TypeError for single integer. KeyError for list, array,
                    # slice of integers. Assume key[0] is integer
                    # (including list or slice).
                    try:
                        return self.data.loc[self.data.index[key[0]], key[1]]
                    except IndexError as err2:
                        err_message = '\n'.join(("original messages:",
                                                 str(err1), str(err2)))
                        raise ValueError(' '.join(("Check requested indexes,",
                                                   "data may not exist.",
                                                   err_message)))
            else:
                try:
                    # Integer based indexing
                    return self.data.iloc[key]
                except (TypeError, ValueError):
                    # If it's not an integer, TypeError is thrown. If it's a
                    # list, ValueError is thrown.
                    return self.data[key]
        else:
            return self.__getitem_xarray__(key)

    def __getitem_xarray__(self, key):
        """Access data in `pysat.Instrument` object with `xarray.Dataset`.

        Parameters
        ----------
        key : str, tuple, or dict
            Data variable name, tuple with a slice, or dict used to locate
            desired data

        Returns
        -------
        xr.Dataset
            Dataset of with only the desired values

        Raises
        ------
        ValueError
            Data access issues, passed from underlying xarray library, or a
            mismatch of indices and dimensions

        Note
        ----
        inst['name'] is `inst.data.name`

        See xarray `.loc` and `.iloc` documentation for more details

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
                if isinstance(key[1], slice):
                    # Extract subset of variables before epoch selection.
                    data_subset = self.data[self.variables[key[1]]]
                else:
                    # Extract single variable before epoch selection.
                    data_subset = self.data[key[1]]

                # If the input is a tuple, `key[0]` must be linked to the epoch.
                key_dict = {'indexers': {epoch_name: key[0]}}
                try:
                    # Assume key[0] is an integer
                    return data_subset.isel(**key_dict)
                except (KeyError, TypeError):
                    # Since `key[0]` is not an integer, use the `sel` method.
                    # KeyError raised when key is single datetime.
                    # TypeError raised when key is slice of datetimes.
                    return data_subset.sel(**key_dict)
                except ValueError as verr:
                    # This may be multidimensional indexing, where the
                    # multiple dimensions are contained within an iterable
                    # object.
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
                # Multidimensional indexing where the multiple dimensions are
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
            except (TypeError, KeyError, ValueError):
                # If that didn't work, likely need to use `isel` or `sel`
                # Link key to the epoch.
                key_dict = {'indexers': {epoch_name: key}}
                try:
                    # Try to get all data variables, but for a subset of time
                    # using integer indexing
                    return self.data.isel(**key_dict)
                except (KeyError, TypeError):
                    # Try to get a subset of time, using label based indexing
                    return self.data.sel(**key_dict)

    def __setitem__(self, key, new_data):
        """Set data in `pysat.Instrument` object.

        Parameters
        ----------
        key : str, tuple, dict
            String label, or dict or tuple of indices for new data
        new_data : dict, pandas.DataFrame, or xarray.Dataset
            New data as a dict (assigned with key 'data'), DataFrame, or
            Dataset

        Examples
        --------
        ::

            # Simple assignment, default metadata assigned
            # 'long_name' = 'name'
            # 'units' = ''
            inst['name'] = newData

            # Assignment with Metadata
            inst['name'] = {'data':new_data,
                            'long_name':long_name,
                            'units':units}

        Raises
        ------
        ValueError
            If underlying data's datetime index not stored as `Epoch` or `time`.
            If tuple not used when assigning dimensions for new multidimensional
            data.

        Note
        ----
        If no metadata provided and if metadata for 'name' not already stored
        then default meta information is also added,
        long_name = 'name', and units = ''.

        """

        new = copy.deepcopy(new_data)

        # Add data to main pandas.DataFrame, depending upon the input
        # slice, and a name
        if self.pandas_format:
            if isinstance(key, tuple):
                try:
                    # Pass directly through to loc. This line raises a
                    # FutureWarning if key[0] is a slice. The future behavior
                    # is TypeError, which is already handled correctly below.
                    self.data.loc[key[0], key[1]] = new
                except (KeyError, TypeError):
                    # TypeError for single integer, slice (pandas 2.0). KeyError
                    # for list, array. Assume key[0] is integer
                    # (including list or slice).
                    self.data.loc[self.data.index[key[0]], key[1]] = new
                self.meta[key[1]] = {}
                return
            elif not isinstance(new, dict):
                # Make it a dict to simplify downstream processing
                new = {'data': new}

            # Input dict must have data in 'data',
            # the rest of the keys are presumed to be metadata
            in_data = new.pop('data')

            # TODO(#908): remove code below with removal of 2D pandas support.
            if hasattr(in_data, '__iter__'):
                if not isinstance(in_data, pds.DataFrame) and isinstance(
                        next(iter(in_data), None), pds.DataFrame):
                    # Input is a list_like of frames, denoting higher order data
                    warnings.warn(" ".join(["Support for 2D pandas instrument",
                                            "data has been deprecated and will",
                                            "be removed in 3.2.0+.  Please",
                                            "either raise an issue with the",
                                            "developers or modify the load",
                                            "statement to use an",
                                            "xarray.Dataset."]),
                                  DeprecationWarning, stacklevel=2)

                    if ('meta' not in new) and (key not in self.meta.keys_nD()):
                        # Create an empty Meta instance but with variable names.
                        # This will ensure the correct defaults for all
                        # subvariables.  Meta can filter out empty metadata as
                        # needed, the check above reduces the need to create
                        # Meta instances.
                        ho_meta = pysat.Meta(labels=self.meta_labels)
                        ho_meta[in_data[0].columns] = {}
                        self.meta[key] = ho_meta

            # Assign data and any extra metadata
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
                # User provided more than one thing in assignment location
                # something like, index integers and a variable name,
                # self[idx, 'variable'] = stuff
                # or, self[idx1, idx2, idx3, 'variable'] = stuff.
                # Construct dictionary of dimensions and locations for
                # xarray standards.
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
                        # Only provided a single number in iterable, make that
                        # the input for all times
                        self.data[key] = (epoch_name,
                                          [in_data[0]] * len(self.index))
                    elif len(in_data) == 0:
                        # Provided an empty iterable, make everything NaN
                        self.data[key] = (epoch_name,
                                          [np.nan] * len(self.index))
                elif len(np.shape(in_data)) == 0:
                    # Not an iterable input, rather a single number.  Make
                    # that number the input for all times.
                    self.data[key] = (epoch_name, [in_data] * len(self.index))
                else:
                    # Multidimensional input that is not an xarray.  The user
                    # needs to provide everything that is required for success.
                    if isinstance(in_data, tuple):
                        self.data[key] = in_data
                    else:
                        raise ValueError(' '.join(('Must provide dimensions',
                                                   'for xarray multidim',
                                                   'data using input tuple.')))

            elif hasattr(key, '__iter__'):
                # Multiple input strings (keys) are provided, but not in tuple
                # form. Recurse back into this function, setting each input
                # individually.
                for keyname in key:
                    self.data[keyname] = in_data[keyname]

            # Attach metadata
            self.meta[key] = new

        return

    def __iter__(self):
        """Load data for subsequent days or files.

        Default bounds are the first and last dates from files on local system

        Note
        ----
        Limits of iteration, and iteration type (date/file) set by `bounds`
        attribute

        Examples
        --------
        ::

            inst = pysat.Instrument(platform=platform, name=name, tag=tag)
            start = dt.datetime(2009, 1, 1)
            stop = dt.datetime(2009, 1, 31)
            inst.bounds = (start, stop)
            for loop_inst in inst:
                print('Another day loaded ', loop_inst.date)

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

                # Load range of files. Get location for second file,
                # width of 1 loads only one file.
                nfid = self.files.get_index(fname) + width - 1
                local_inst.load(fname=fname, stop_fname=self.files[nfid])
                yield local_inst

        elif self._iter_type == 'date':
            # Iterate over dates. A list of dates is generated whenever
            # bounds are set.
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
        """Determine whether or not data has been loaded.

        Parameters
        ----------
        data : NoneType, pds.DataFrame, or xr.Dataset
            Data object. If None, will use `self.data`.

        Returns
        -------
        bool
            True if there is no Instrument data, False if there is data

        """

        # Support easy application to `self.data`
        if data is None:
            if hasattr(self, 'data'):
                data = self.data
            else:
                return True

        if self.pandas_format:
            return data.empty
        else:
            if len(data.indexes.keys()) > 0:
                # Check if all of the present keys are empty
                key_empty = []
                for key in data.indexes.keys():
                    key_empty.append(len(data.indexes[key]) == 0)
                return all(key_empty)
            else:
                # No keys, therefore empty
                return True

    def _index(self, data=None):
        """Retrieve the time index for the loaded data.

        Parameters
        ----------
        data : NoneType, pds.DataFrame, or xr.Dataset
            Data object. If None, use `self.data`.

        Returns
        -------
        pds.Series
            Series containing the time indices for the Instrument data

        """
        # Support easy application to `self.data`
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
        """Empty default method for updatable Instrument methods."""
        pass

    def _assign_attrs(self, by_name=False):
        """Assign all external instrument attributes to the Instrument object.

        Parameters
        ----------
        by_name : boolean
            If True, uses `self.platform` and `self.name` to load the
            Instrument, if False uses inst_module. (default=False)

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
            _test_download, _test_download_ci, and _password_req

        """
        # Declare the standard Instrument methods and attributes
        inst_methods = {'required': ['init', 'clean'],
                        'optional': ['preprocess']}
        inst_funcs = {'required': ['load', 'list_files', 'download'],
                      'optional': ['list_remote_files']}
        inst_attrs = {'directory_format': None, 'file_format': None,
                      'multi_file_day': False, 'orbit_info': None,
                      'pandas_format': True}
        test_attrs = {'_test_download': True, '_test_download_ci': True,
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
            # pysat platform is reserved for modules within `pysat.instruments`
            if self.platform == 'pysat':
                # Look within pysat
                self.inst_module = importlib.import_module(
                    ''.join(('.', self.platform, '_', self.name)),
                    package='pysat.instruments')
            else:
                # Not a native pysat.Instrument. First, get the supporting
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

                # Import the registered module. Though modules are checked to
                # ensure they may be imported when registered, something may
                # have changed on the system since it was originally checked.
                try:
                    self.inst_module = importlib.import_module(mod)
                except ImportError as ierr:
                    estr = ' '.join(('unable to locate or import module for',
                                     'platform {:}, name {:}'))
                    estr = estr.format(self.platform, self.name)
                    pysat.logger.error(estr)
                    raise ImportError(ierr)
        elif self.inst_module is None:
            # No module or name info, default pass functions assigned
            return

        # Check if `tag` and `inst_id` are appropriate for the module
        if self.inst_id not in self.inst_module.inst_ids.keys():
            inst_id_str = ', '.join([ikey.__repr__() for ikey
                                     in self.inst_module.inst_ids.keys()])
            estr = ''.join(("'", self.inst_id, "' is not one of the supported ",
                            'inst_ids. Supported inst_ids are: ',
                            inst_id_str, '.'))
            raise ValueError(estr)

        if self.tag not in self.inst_module.inst_ids[self.inst_id]:
            tag_str = ', '.join([tkey.__repr__() for tkey
                                 in self.inst_module.inst_ids[self.inst_id]])
            estr = ''.join(("'", self.tag, "' is not one of the supported ",
                            'tags. Supported tags are: ', tag_str, '.'))
            raise ValueError(estr)

        # Assign the Instrument methods
        missing = list()
        for mstat in inst_methods.keys():
            for mname in inst_methods[mstat]:
                if hasattr(self.inst_module, mname):
                    local_name = _kwargs_keys_to_func_name(mname)

                    # Remote functions are not attached as methods unless
                    # cast that way, specifically
                    # https://stackoverflow.com/questions/972/
                    #         adding-a-method-to-an-existing-object-instance
                    local_method = types.MethodType(getattr(self.inst_module,
                                                            mname), self)
                    setattr(self, local_name, local_method)
                else:
                    missing.append(mname)
                    if mstat == "required":
                        raise AttributeError(
                            "".join(['A `', mname, '` method is required',
                                     ' for every Instrument']))

        if len(missing) > 0:
            pysat.logger.debug(
                'Missing Instrument methods: {:}'.format(missing))

        # Assign the Instrument functions
        missing = list()
        for mstat in inst_funcs.keys():
            for mname in inst_funcs[mstat]:
                if hasattr(self.inst_module, mname):
                    local_name = _kwargs_keys_to_func_name(mname)
                    setattr(self, local_name, getattr(self.inst_module, mname))
                else:
                    missing.append(mname)
                    if mstat == "required":
                        raise AttributeError(
                            "".join(['A `', mname, '` function is required',
                                     ' for every Instrument']))

        if len(missing) > 0:
            pysat.logger.debug(
                'Missing Instrument methods: {:}'.format(missing))

        # Look for instrument default parameters
        missing = list()
        for iattr in inst_attrs.keys():
            if hasattr(self.inst_module, iattr):
                setattr(self, iattr, getattr(self.inst_module, iattr))
            else:
                missing.append(iattr)

        if len(missing) > 0:
            pysat.logger.debug(' '.join(['These Instrument attributes kept',
                                         'their default  values:',
                                         '{:}'.format(missing)]))

        # Check for download flags for tests
        missing = list()
        for iattr in test_attrs.keys():
            # Check and see if this instrument has the desired test flag
            if hasattr(self.inst_module, iattr):
                local_attr = getattr(self.inst_module, iattr)

                # Test to see that this attribute is set for the desired
                # `inst_id` and `tag`
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

        # Check and see if this instrument has deprecated _test_download_travis
        # TODO(#807): Remove this check once _test_download_travis is removed.
        if hasattr(self.inst_module, '_test_download_travis'):
            local_attr = getattr(self.inst_module, '_test_download_travis')

            # Test to see that this attribute is set for the desired
            # `inst_id` and `tag`.
            if self.inst_id in local_attr.keys():
                if self.tag in local_attr[self.inst_id].keys():
                    # Update the test attribute value
                    setattr(self, '_test_download_ci',
                            local_attr[self.inst_id][self.tag])
                    warnings.warn(" ".join(["`_test_download_travis` has been",
                                            "deprecated and will be replaced",
                                            "by `_test_download_ci` in",
                                            "3.2.0+"]),
                                  DeprecationWarning, stacklevel=2)

        if len(missing) > 0:
            pysat.logger.debug(' '.join(['These Instrument test attributes',
                                         'kept their default  values:',
                                         '{:}'.format(missing)]))
        return

    def _load_data(self, date=None, fid=None, inc=None, load_kwargs=None):
        """Load data for an instrument on given date or filename index.

        Parameters
        ----------
        date : dt.datetime or NoneType
            File date (default=None)
        fid : int or NoneType
            Filename index value (default=None)
        inc : dt.timedelta, int, or NoneType
            Increment of files or dates to load, starting from the
            root date or fid (default=None)
        load_kwargs : dict
            Dictionary of keywords that may be options for specific instruments.
            If None, uses `self.kwargs['load']`. (default=None)

        Returns
        -------
        data : pds.DataFrame or xr.Dataset
            pysat data
        meta : pysat.Meta
            pysat meta data

        Raises
        ------
        ValueError
            If both `date` and `fid` are None, or if `inc` left unspecified
        """
        # Set default `load_kwargs`
        if load_kwargs is None:
            load_kwargs = copy.deepcopy(self.kwargs['load'])

        if inc is None:
            raise ValueError('Must supply value for `inc`.')

        # Ensure that the local optional kwarg `use_header` is not passed
        # to the instrument routine.
        #
        # TODO(#1020): Remove after removing `use_header`
        if 'use_header' in load_kwargs.keys():
            del load_kwargs['use_header']

        date = pysat.utils.time.filter_datetime_input(date)

        if fid is not None:
            # Get filename based off of index value. Inclusive loading on
            # filenames per construction below.
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
                                             **load_kwargs)

                # Ensure units and name are named consistently in new Meta
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
                                      'routine must be a',
                                      repr(self._data_library),
                                      'and not', repr(type(data)))))
        if not isinstance(mdata, pysat.Meta):
            raise TypeError('Metadata returned must be a pysat.Meta object')

        # Let user know whether or not data was returned
        ind = data.index if self.pandas_format else data.indexes
        if len(ind) > 0:
            if date is not None:
                output_str = ' '.join(('Returning', output_str, 'data for',
                                       date.strftime('%d %B %Y')))
            else:
                output_str = ' '.join(('Returning', output_str, 'data from',
                                       fname[0]))
                if len(fname) > 1:
                    output_str = ' '.join((output_str, '::', fname[-1]))
        else:
            # There was no data signal
            if date is not None:
                if bad_datetime:
                    output_str = ' '.join(('Bad datetime for', output_str,
                                           date.strftime('%d %B %Y')))
                else:
                    output_str = ' '.join(('No', output_str, 'data for',
                                           date.strftime('%d %B %Y')))
            else:
                output_str = ' '.join(('No', output_str))
                if len(fname) == 0:
                    output_str = ' '.join((output_str, 'valid filenames found'))
                else:
                    output_str = ' '.join((output_str, 'data for', fname[0]))
                    if len(fname) > 1:
                        output_str = ' '.join((output_str, '::', fname[-1]))

        # Remove extra spaces, if any are present
        output_str = " ".join(output_str.split())
        pysat.logger.info(output_str)

        return data, mdata

    def _load_next(self):
        """Load the next days data (or file) without incrementing the date.

        Returns
        -------
        data : pds.DataFrame or xr.Dataset
            pysat data
        meta : pysat.Meta
            pysat meta data

        Note
        ----
        Repeated calls will not advance date/file and will produce the same
        data.

        Uses info stored in object to either increment the date,
        or the file. Looks for `self._load_by_date` flag.

        """
        if self._load_by_date:
            next_date = self.date + self.load_step
            return self._load_data(date=next_date, inc=self.load_step)
        else:
            next_id = self._fid + self.load_step + 1
            return self._load_data(fid=next_id, inc=self.load_step)

    def _load_prev(self):
        """Load the previous days data (or file) without decrementing the date.

        Returns
        -------
        data : pds.DataFrame or xr.Dataset
            pysat data
        meta : pysat.Meta
            pysat meta data

        Note
        ----
        Repeated calls will not decrement date/file and will produce the same
        data

        Uses info stored in object to either decrement the date,
        or the file. Looks for `self._load_by_date` flag.

        """
        load_kwargs = {'inc': self.load_step}

        if self._load_by_date:
            load_kwargs['date'] = self.date - self.load_step
        else:
            load_kwargs['fid'] = self._fid - self.load_step - 1

        return self._load_data(**load_kwargs)

    def _set_load_parameters(self, date=None, fid=None):
        """Set the necesssary load attributes.

        Sets `self._load_by_date`, `self.date`, `self._fid`, `self.yr`, and
        `self.doy`

        Parameters
        ----------
        date : dt.datetime.date or NoneType
            File date (default=None)
        fid : int or NoneType
            Filename index value (default=None)

        """
        # Filter supplied data so that it is only year, month, and day and
        # then store as part of instrument object.  Filtering is performed
        # by the class property `self.date`.
        self.date = date
        self._fid = fid

        if date is not None:
            year, doy = pysat.utils.time.getyrdoy(date)
            self.yr = year
            self.doy = doy
            self._load_by_date = True
        else:
            self.yr = None
            self.doy = None
            self._load_by_date = False
        return

    def _get_var_type_code(self, coltype):
        """Determine the two-character type code for a given variable type.

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
                     np.float32: 'f4', np.datetime64: 'i8'}

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
        """Support file writing by determining data type and other options.

        Parameters
        ----------
        data : pandas object
            Data to be written

        Returns
        -------
        data : pandas object
            Data that was supplied, reformatted if necessary
        data_type : type or dtype
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
            elif data_type == np.dtype('<U4'):
                data_type = str
                datetime_flag = False
            else:
                datetime_flag = False
        else:
            # We're dealing with a more complicated object. Iterate
            # over elements until we hit something that is something,
            # and not NaN.
            data_type = type(data.iloc[0])
            for i in np.arange(len(data)):
                if len(data.iloc[i]) > 0:
                    data_type = type(data.iloc[i])
                    if not isinstance(data_type, float) \
                            or (not isinstance(data_type, np.floating)):
                        break
            datetime_flag = False

        return data, data_type, datetime_flag

    def _filter_netcdf4_metadata(self, mdata_dict, coltype, remove=False,
                                 export_nan=None):
        """Filter metadata properties to be consistent with netCDF4.

        .. deprecated:: 3.0.2
            Moved to `pysat.utils.io.filter_netcdf4_metadata. This wrapper
            will be removed in 3.2.0+.

        Parameters
        ----------
        mdata_dict : dict
            Dictionary equivalent to Meta object info
        coltype : type
            Data type provided by `pysat.Instrument._get_data_info`
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

        See Also
        --------
        pysat.utils.io.filter_netcdf4_metadata

        """
        warnings.warn("".join(["`pysat.Instrument._filter_netcdf4_metadata` ",
                               "has been deprecated and will be removed ",
                               "in pysat 3.2.0+. Use `pysat.utils.io.",
                               "filter_netcdf4_metadata` instead."]),
                      DeprecationWarning, stacklevel=2)

        if remove:
            check_type = [self.meta.labels.fill_val, self.meta.labels.max_val,
                          self.meta.labels.min_val]
        else:
            check_type = None

        return pysat.utils.io.filter_netcdf4_metadata(self, mdata_dict, coltype,
                                                      remove=remove,
                                                      check_type=check_type,
                                                      export_nan=export_nan)

    # -----------------------------------------------------------------------
    # Define all accessible methods

    @property
    def bounds(self):
        """Boundaries for iterating over instrument object by date or file.

        Parameters
        ----------
        start : dt.datetime, str, or NoneType
            Start of iteration, if None uses first data date.
            list-like collection also accepted. (default=None)
        stop :  dt.datetime, str, or None
            Stop of iteration, inclusive. If None uses last data date.
            list-like collection also accepted. (default=None)
        step : str, int, or NoneType
            Step size used when iterating from start to stop. Use a
            Pandas frequency string ('3D', '1M') when setting bounds by date,
            an integer when setting bounds by file. Defaults to a single
            day/file (default='1D', 1).
        width : pandas.DateOffset, int, or NoneType
            Data window used when loading data within iteration. Defaults to a
            single day/file if not assigned. (default=dt.timedelta(days=1),
            1)

        Raises
        ------
        ValueError
            If `start` and `stop` don't have the same type, or if too many
            input argument supplied, or unequal number of elements in
            `start`/`stop`, or if bounds aren't in increasing order, or if
            the input type for `start` or `stop` isn't recognized

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

            # Iterate via a non-standard step size of two days
            inst.bounds = ([start, start2], [stop, stop2], '2D')

            # Load more than a single day/file at a time when iterating
            inst.bounds = ([start, start2], [stop, stop2], '2D',
                           dt.timedelta(days=3))

        """

        return (self._iter_start, self._iter_stop, self._iter_step,
                self._iter_width)

    @bounds.setter
    def bounds(self, value=None):
        # Set the bounds property.  See property docstring for details.

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
                self._iter_list = pysat.utils.time.create_date_range(
                    self._iter_start, ustops, freq=ufreq)
            else:
                # Instrument has no files
                self._iter_list = []
        else:
            # User provided some inputs, ensure always a 1D list
            starts = pysat.utils.listify(start)
            stops = pysat.utils.listify(stop)

            # Check equal number of elements
            if len(starts) != len(stops):
                estr = ' '.join(('Both start and stop must have the same',
                                 'number of elements'))
                raise ValueError(estr)

            # Check everything is the same type
            base = type(starts[0])
            for lstart, lstop in zip(starts, stops):
                etype = type(lstop)
                check1 = not isinstance(lstart, etype)
                check2 = not isinstance(lstart, base)
                if check1 or check2:
                    # Method allows for inputs like inst.bounds = (start, None)
                    # and bounds will fill the `None` with actual start or stop.
                    # Allow for a Nonetype only if length is one.
                    if len(starts) == 1 and (start is None):
                        # We are good on type change, start is None, no error
                        break
                    elif len(stops) == 1 and (stop is None):
                        # We are good on type change, stop is None, no error
                        break
                    raise ValueError(' '.join(('Start and stop items must all',
                                               'be of the same type')))

            # Set bounds based upon passed data type
            if isinstance(starts[0], str) or isinstance(stops[0], str):
                # One of the inputs is a string
                self._iter_type = 'file'

                # Could be (string, None) or (None, string). Replace None
                # with first/last, as appropriate.
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

                    # Account for width of load. Don't extend past bound.
                    stop_idx = stop_idx - self._iter_width + 1

                    # Stop index is exclusive when called this way, pad by 1
                    itemp = self.files.files.values[start_idx:(stop_idx + 1)]

                    # Downselect based on step size
                    itemp = itemp[::self._iter_step]
                    self._iter_list.extend(itemp)

            elif isinstance(starts[0], dt.datetime) or isinstance(stops[0],
                                                                  dt.datetime):
                # One of the inputs is a date
                self._iter_type = 'date'

                if starts[0] is None:
                    # Start and stop dates on `self.files` already filtered
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
                starts = pysat.utils.time.filter_datetime_input(starts)
                stops = pysat.utils.time.filter_datetime_input(stops)
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

                # Account for width of load. Don't extend past bound.
                ustops = [stop - width + dt.timedelta(days=1)
                          for stop in stops]

                # Date range is inclusive, no need to pad.
                self._iter_list = pysat.utils.time.create_date_range(starts,
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
    def date(self):
        """Date for loaded data."""
        return self._date

    @date.setter
    def date(self, new_date):
        # Set the date property, see property docstring for details
        self._date = pysat.utils.time.filter_datetime_input(new_date)

    @property
    def empty(self):
        """Boolean flag reflecting lack of data, True if there is no data."""
        return self._empty()

    @property
    def index(self):
        """Time index of the loaded data."""
        return self._index()

    @property
    def pandas_format(self):
        """Boolean flag for pandas data support."""
        return self._pandas_format

    @pandas_format.setter
    def pandas_format(self, new_value):
        # Set pandas_format attribute, see property docstring for details.
        # Note that `pandas_format` is assigned by default by `_assign_attrs()`.
        if self.empty:
            if new_value:
                self._null_data = pds.DataFrame(None)
                self._data_library = pds.DataFrame
            else:
                self._null_data = xr.Dataset(None)
                self._data_library = xr.Dataset

            self._pandas_format = new_value
        else:
            estr = ''.join(["Can't change data type setting while data is ",
                            'assigned to Instrument object.'])
            raise ValueError(estr)

        return

    @property
    def variables(self):
        """List of variables for the loaded data."""

        if self.pandas_format:
            return self.data.columns
        else:
            return list(self.data.variables.keys())

    @property
    def vars_no_time(self):
        """List of variables for the loaded data, excluding time index."""

        if self.pandas_format:
            return self.data.columns
        else:
            return pysat.utils.io.xarray_vars_no_time(self.data)

    def copy(self):
        """Create a deep copy of the entire Instrument object.

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
        # `self.orbits.inst.copy()`, or
        # `self.files.inst_info['inst'].copy()`
        if not isinstance(inst_copy, weakref.ProxyType):
            inst_copy.files.inst_info['inst'] = weakref.proxy(inst_copy)
            inst_copy.orbits.inst = weakref.proxy(inst_copy)
        else:
            inst_copy.files.inst_info['inst'] = inst_copy
            inst_copy.orbits.inst = inst_copy

        return inst_copy

    def concat_data(self, new_data, prepend=False, **kwargs):
        """Concatonate data to self.data for xarray or pandas as needed.

        Parameters
        ----------
        new_data : pandas.DataFrame, xarray.Dataset, or list of such objects
            New data objects to be concatonated
        prepend : bool
            If True, assign new data before existing data; if False append new
            data (default=False)
        **kwargs : dict
            Optional keyword arguments passed to pds.concat or xr.concat

        Note
        ----
        For pandas, sort=False is passed along to the underlying
        `pandas.concat` method. If sort is supplied as a keyword, the
        user provided value is used instead.  Recall that sort orders the
        data columns, not the data values or the index.

        For xarray, `dim=Instrument.index.name` is passed along to xarray.concat
        except if the user includes a value for dim as a keyword argument.

        """
        # Order the data to be concatenated in a list
        if not isinstance(new_data, list):
            new_data = [new_data]

        if prepend:
            new_data.append(self.data)
        else:
            new_data.insert(0, self.data)

        # Retrieve the appropriate concatenation function
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

        # Assign the concatenated data to the instrument
        self.data = concat_func(new_data, **kwargs)
        return

    def custom_attach(self, function, at_pos='end', args=None, kwargs=None):
        """Attach a function to custom processing queue.

        Custom functions are applied automatically whenever `.load()`
        command called.

        Parameters
        ----------
        function : str or function object
            Name of function or function object to be added to queue
        at_pos : str or int
            Accepts string 'end' or a number that will be used to determine
            the insertion order if multiple custom functions are attached
            to an Instrument object (default='end')
        args : list, tuple, or NoneType
            Ordered arguments following the instrument object input that are
            required by the custom function (default=None)
        kwargs : dict or NoneType
            Dictionary of keyword arguments required by the custom function
            (default=None)

        Note
        ----
        Functions applied using `custom_attach` may add, modify, or use
        the data within Instrument inside of the function, and so should not
        return anything.

        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        # Test the positioning input
        pos_list = list(np.arange(0, len(self.custom_functions), 1))
        pos_list.append('end')

        if at_pos not in pos_list:
            pysat.logger.warning(' '.join(['unknown position specified,',
                                           'including function at end of',
                                           'current list']))
            at_pos = 'end'

        # Convert string to function object, if necessary
        if isinstance(function, str):
            function = eval(function)

        # If the position is 'end' or greater
        if (at_pos == 'end') | (at_pos == len(self.custom_functions)):
            # Store function object
            self.custom_functions.append(function)
            self.custom_args.append(args)
            self.custom_kwargs.append(kwargs)
        else:
            # User picked a specific location to insert
            self.custom_functions.insert(at_pos, function)
            self.custom_args.insert(at_pos, args)
            self.custom_kwargs.insert(at_pos, kwargs)

        return

    def custom_apply_all(self):
        """Apply all of the custom functions to the satellite data object.

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
        """Clear the custom function list."""
        self.custom_functions = []
        self.custom_args = []
        self.custom_kwargs = []
        return

    def today(self):
        """Get today's date (UTC), with no hour, minute, second, etc.

        Returns
        -------
        today_utc: datetime
            Today's date in UTC

        """
        return pysat.utils.time.today()

    def tomorrow(self):
        """Get tomorrow's date (UTC), with no hour, minute, second, etc.

        Returns
        -------
        datetime
            Tomorrow's date in UTC

        """

        return self.today() + dt.timedelta(days=1)

    def yesterday(self):
        """Get yesterday's date (UTC), with no hour, minute, second, etc.

        Returns
        -------
        datetime
            Yesterday's date in UTC

        """

        return self.today() - dt.timedelta(days=1)

    def next(self, verifyPad=False):
        """Iterate forward through the data loaded in Instrument object.

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

        # Make sure we can iterate
        if len(self._iter_list) == 0:
            # Nothing to potentially iterate over
            raise StopIteration(''.join(('File list is empty. ',
                                         'Nothing to be done.')))

        if self._iter_type == 'date':
            if self.date is not None:
                # Data is already loaded in `.data`
                idx, = np.where(self.date == self._iter_list)
                if len(idx) == 0:
                    estr = ''.join(('Unable to find loaded date ',
                                    'in the supported iteration list. ',
                                    'Please check the Instrument bounds, ',
                                    '`self.bounds` for supported iteration',
                                    'ranges.'))
                    raise StopIteration(estr)
                elif idx[-1] >= len(self._iter_list) - 1:
                    # Gone too far!
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    # Not going past the last day, safe to move forward
                    date = self._iter_list[idx[0] + 1]
                    end_date = date + self._iter_width
            else:
                # No data currently loaded, start at the beginning
                date = self._iter_list[0]
                end_date = date + self._iter_width

            # Perform load
            self.load(date=date, end_date=end_date, verifyPad=verifyPad)

        elif self._iter_type == 'file':
            first = self.files.get_index(self._iter_list[0])
            last = self.files.get_index(self._iter_list[-1])
            step = self._iter_step
            width = self._iter_width
            if self._fid is not None:
                # Data already loaded in `.data`
                if (self._fid < first) | (self._fid + step > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    # Step size already accounted for in the list of files. Get
                    # location of current file in iteration list.
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
                # No data loaded yet, start with the first file
                fname = self._iter_list[0]

            # Get location for second file. Note a width of 1 loads single file.
            # Load range of files.
            nfid = self.files.get_index(fname) + width - 1
            self.load(fname=fname, stop_fname=self.files[nfid],
                      verifyPad=verifyPad)

        return

    def prev(self, verifyPad=False):
        """Iterate backwards through the data in Instrument object.

        Bounds of iteration and iteration type (day/file)
        are set by `bounds` attribute.

        Parameters
        ----------
        verifyPad : bool
            Passed to `self.load()`. If True, then padded data within
            the load method will be retained. (default=False)

        Note
        ----
        If there were no previous calls to load then the first day (default) or
        file will be loaded.

        """
        # Make sure we can iterate
        if len(self._iter_list) == 0:
            # Nothing to potentially iterate over
            raise StopIteration(''.join(('File list is empty. ',
                                         'Nothing to be done.')))

        if self._iter_type == 'date':
            if self.date is not None:
                # Some data has already been loaded in `self.data`
                idx, = np.where(self._iter_list == self.date)
                if len(idx) == 0:
                    estr = ''.join(('Unable to find loaded date ',
                                    'in the supported iteration list. ',
                                    'Please check the Instrument bounds, ',
                                    '`self.bounds` for supported iteration',
                                    'ranges.'))
                    raise StopIteration(estr)
                elif idx[0] == 0:
                    # We have gone too far!
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    # Not on first day, safe to move backward
                    date = self._iter_list[idx[0] - 1]
                    end_date = self._iter_list[idx[0] - 1] + self._iter_width
                    self.load(date=date, end_date=end_date, verifyPad=verifyPad)
            else:
                # No data currently loaded, start at the end
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
                    # Find location of the desired file
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

    def rename(self, mapper, lowercase_data_labels=False):
        """Rename variables within both data and metadata.

        Parameters
        ----------
        mapper : dict or func
            Dictionary with old names as keys and new names as variables or
            a function to apply to all names
        lowercase_data_labels : bool
            If True, the labels applied to `self.data` are forced to lowercase.
            The case supplied in `mapper` is retained within `inst.meta`.

        Examples
        --------
        ::

            # Standard renaming using a dict
            new_mapper = {'old_name': 'new_name', 'old_name2':, 'new_name2'}
            inst.rename(new_mapper)

            # Standard renaming using a function
            inst.rename(str.upper)


        If using a pandas-type Instrument with higher-order data and a
        dictionary mapper, the upper-level data key must contain a dictionary
        for renaming the dependent data variables.  The upper-level data key
        cannot be renamed. Note that this rename will be invoked individually
        for all times in the dataset.
        ::

            # Applies to higher-order datasets that are loaded into pandas
            inst = pysat.Instrument('pysat', 'testing2D')
            inst.load(2009, 1)
            mapper = {'uts': 'pysat_uts',
                      'profiles': {'density': 'pysat_density'}}
            inst.rename(mapper)
            print(inst[0, 'profiles'].columns)  # 'density' will be updated

            # To rename higher-order data at both levels using a dictionary,
            # you need two calls
            mapper2 = {'profiles': 'pysat_profile'}
            inst.rename(mapper2)
            print(inst[0, 'pysat_profile'].columns)

            # A function will affect both standard and higher-order data.
            # Remember this function also updates the Meta data.
            inst.rename(str.capitalize)
            print(inst.meta['Pysat_profile']['children'])


        pysat supports differing case for variable labels across the data and
        metadata objects attached to an Instrument. Since Meta is
        case-preserving (on assignment) but case-insensitive to access, the
        labels used for data are always valid for metadata. This feature may be
        used to provide friendlier variable names within pysat while also
        maintaining external format compatibility when writing files.
        ::

            # Example with lowercase_data_labels
            inst = pysat.Instrument('pysat', 'testing2D')
            inst.load(2009, 1)
            mapper = {'uts': 'Pysat_UTS',
                     'profiles': {'density': 'PYSAT_density'}}
            inst.rename(mapper, lowercase_data_labels=True)

            # Note that 'Pysat_UTS' was applied to data as 'pysat_uts'
            print(inst['pysat_uts'])

            # Case is retained within inst.meta, though data access to meta is
            # case insensitive
            print('True meta variable name is ', inst.meta['pysat_uts'].name)

            # Note that the labels in meta may be used when creating a file,
            # thus, 'Pysat_UTS' would be found in the resulting file
            inst.to_netcdf4('./test.nc', preserve_meta_case=True)

            # Load in file and check
            raw = netCDF4.Dataset('./test.nc')
            print(raw.variables['Pysat_UTS'])

        """

        # Mirror xarray/pandas behaviour and raise a ValueError if mapper is
        # a dict an an unknown variable name is provided.
        if isinstance(mapper, dict):
            for vkey in mapper.keys():
                if vkey not in self.variables:
                    raise ValueError(''.join(['cannot rename ', repr(vkey),
                                              ' because it is not a variable ',
                                              'in this Instrument']))

        if self.pandas_format:
            # Initialize dict for renaming normal pandas data
            pdict = {}

            # Collect normal variables and rename higher order variables
            for vkey in self.variables:
                map_key = pysat.utils.get_mapped_value(vkey, mapper)

                if map_key is not None:
                    # Treat higher-order pandas and normal pandas separately
                    if vkey in self.meta.keys_nD():
                        # Variable name is in higher order list
                        hdict = {}
                        if isinstance(map_key, dict):
                            # Changing a variable name within a higher order
                            # object using a dictionary. First ensure the
                            # variable exist.
                            for hkey in map_key.keys():
                                if hkey not in self.meta[
                                        vkey]['children'].keys():
                                    estr = ' '.join(
                                        ('cannot rename', repr(hkey),
                                         'because it is not a known ',
                                         'higher-order variable under',
                                         repr(vkey), '.'))
                                    raise ValueError(estr)
                            hdict = map_key
                        else:
                            # This is either a value or a mapping function
                            for hkey in self.meta[vkey]['children'].keys():
                                hmap = pysat.utils.get_mapped_value(hkey,
                                                                    mapper)
                                if hmap is not None:
                                    hdict[hkey] = hmap

                            pdict[vkey] = map_key

                        # Check for lowercase flag
                        change = True
                        if lowercase_data_labels:
                            gdict = {hkey: hdict[hkey].lower()
                                     for hkey in hdict.keys()
                                     if hkey != hdict[hkey].lower()}

                            if len(list(gdict.keys())) == 0:
                                change = False
                        else:
                            gdict = hdict

                        # Change the higher-order variable names frame-by-frame
                        if change:
                            for i in np.arange(len(self.index)):
                                if isinstance(self[i, vkey], pds.Series):
                                    if self[i, vkey].name in gdict:
                                        new_name = gdict[self[i, vkey].name]
                                        self[i, vkey].rename(new_name,
                                                             inplace=True)
                                    else:
                                        tkey = list(gdict.keys())[0]
                                        if self[i, vkey].name != gdict[tkey]:
                                            estr = ' '.join(
                                                ('cannot rename', hkey,
                                                 'because, it is not a known'
                                                 'known higher-order ',
                                                 'variable under', vkey, 'at',
                                                 'index {:d}.'.format(i)))
                                            raise ValueError(estr)
                                else:
                                    self[i, vkey].rename(columns=gdict,
                                                         inplace=True)

                    else:
                        # This is a normal variable. Add it to the pandas
                        # renaming dictionary after accounting for the
                        # `lowercase_data_labels` flag.
                        if lowercase_data_labels:
                            if vkey != map_key.lower():
                                pdict[vkey] = map_key.lower()
                        else:
                            pdict[vkey] = map_key

            # Change variable names for attached data object
            self.data.rename(columns=pdict, inplace=True)
        else:
            # Adjust mapper to account for lowercase data labels in Instrument
            # data, but not the metadata. Xarray requires dict input for rename.
            gdict = {}
            for vkey in self.variables:
                map_key = pysat.utils.get_mapped_value(vkey, mapper)
                if map_key is not None:
                    if lowercase_data_labels:
                        gdict[vkey] = map_key.lower()
                    else:
                        gdict[vkey] = map_key

            # Rename data variables using native xarray rename method
            self.data = self.data.rename(gdict)

        # Update the metadata, which does not use `lowercase_data_labels` flag
        self.meta.rename(mapper)

        return

    def generic_meta_translator(self, input_meta):
        """Convert the `input_meta` metadata into a dictionary.

        .. deprecated:: 3.0.2
           `generic_meta_translator` will be removed in the 3.2.0+ release.

        Parameters
        ----------
        input_meta : pysat.Meta
            The metadata object to translate

        Returns
        -------
        export_dict : dict
            A dictionary of the metadata for each variable of an output file

        Note
        ----
        Uses the translation dict, if present, at `self._meta_translation_table`
        to map existing metadata labels to a list of labels used in the
        returned dict.

        """

        dstr = ''.join(['This function has been deprecated. Please see ',
                        '`pysat.utils.io.apply_table_translation_to_file` and ',
                        '`self.meta.to_dict` to get equivalent functionality.'])
        warnings.warn(dstr, DeprecationWarning, stacklevel=2)

        meta_dict = input_meta.to_dict()
        trans_table = self._meta_translation_table
        exp_dict = pysat.utils.io.apply_table_translation_to_file(self,
                                                                  meta_dict,
                                                                  trans_table)

        return exp_dict

    def load(self, yr=None, doy=None, end_yr=None, end_doy=None, date=None,
             end_date=None, fname=None, stop_fname=None, verifyPad=False,
             use_header=False, **kwargs):
        """Load the instrument data and metadata.

        Parameters
        ----------
        yr : int or NoneType
            Year for desired data. pysat will load all files with an
            associated date between `yr`, `doy` and `yr`, `doy` + 1.
            (default=None)
        doy : int or NoneType
            Day of year for desired data. Must be present with `yr` input.
            (default=None)
        end_yr : int or NoneType
            Used when loading a range of dates, from `yr`, `doy` to `end_yr`,
            `end_doy` based upon the dates associated with the Instrument's
            files. Date range is inclusive for `yr`, `doy` but exclusive for
            `end_yr`, `end_doy`. (default=None)
        end_doy : int or NoneType
            Used when loading a range of dates, from `yr`, `doy` to `end_yr`,
            `end_doy` based upon the dates associated with the Instrument's
            files. Date range is inclusive for `yr`, `doy` but exclusive for
            `end_yr`, `end_doy`. (default=None)
        date : dt.datetime or NoneType
            Date to load data. pysat will load all files with an associated
            date between `date` and `date` + 1 day. (default=None)
        end_date : dt.datetime or NoneType
            Used when loading a range of data from `date` to `end_date` based
            upon the dates associated with the Instrument's files. Date range
            is inclusive for `date` but exclusive for `end_date`. (default=None)
        fname : str or NoneType
            Filename to be loaded (default=None)
        stop_fname : str or NoneType
            Used when loading a range of filenames from `fname` to `stop_fname`,
            inclusive. (default=None)
        verifyPad : bool
            If True, padding data not removed for debugging. Padding
            parameters are provided at Instrument instantiation. (default=False)
        use_header : bool
            If True, moves custom Meta attributes to MetaHeader instead of
            Instrument (default=False)
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments.

        Raises
        ------
        TypeError
            For incomplete or incorrect input
        ValueError
            For input incompatible with Instrument set-up

        Note
        ----
        Loads data for a chosen instrument into `.data`. Any functions chosen
        by the user and added to the custom processing queue (`.custom.attach`)
        are automatically applied to the data before it is available to
        user in `.data`.

        A mixed combination of `.load()` keywords such as `yr` and `date` are
        not allowed.

        `end` kwargs have exclusive ranges (stop before the condition is
        reached), while `stop` kwargs have inclusive ranges (stop once the
        condition is reached).

        Examples
        --------
        ::

            import datetime as dt
            import pysat

            inst = pysat.Instrument('pysat', 'testing')

            # Load a single day by year and day of year
            inst.load(2009, 1)

            # Load a single day by date
            date = dt.datetime(2009, 1, 1)
            inst.load(date=date)

            # Load a single file, first file in this example
            inst.load(fname=inst.files[0])

            # Load a range of days, data between
            # Jan. 1st (inclusive) - Jan. 3rd (exclusive)
            inst.load(2009, 1, 2009, 3)

            # Load a range of days using datetimes
            date = dt.datetime(2009, 1, 1)
            end_date = dt.datetime(2009, 1, 3)
            inst.load(date=date, end_date=end_date)

            # Load several files by filename. Note the change in index due to
            # inclusive slicing on filenames!
            inst.load(fname=inst.files[0], stop_fname=inst.files[1])

        """
        # Add the load kwargs from initialization those provided on input
        for lkey in self.kwargs['load'].keys():
            # Only use the initialized kwargs if a request hasn't been
            # made to alter it in the method call
            if lkey not in kwargs.keys():
                kwargs[lkey] = self.kwargs['load'][lkey]

        # Set options used by loading routine based upon user input
        if yr is not None and doy is not None:
            if doy < 1 or doy > 366:
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

            if end_yr is not None and end_doy is not None:
                if end_doy < 1 or end_doy > 366:
                    estr = ''.join(('Day of year (end_doy) is only valid ',
                                    'between and including 1-366.'))
                    raise ValueError(estr)
                end_date = dt.datetime.strptime(
                    "{:.0f} {:.0f}".format(end_yr, end_doy), "%Y %j")
                self.load_step = end_date - date
            elif end_yr is not None or end_doy is not None:
                estr = ''.join(('Both end_yr and end_doy must be set, ',
                                'or neither.'))
                raise ValueError(estr)
            else:
                # Increment end by a day if none supplied
                self.load_step = dt.timedelta(days=1)

            curr = self.date

        elif date is not None:
            # Verify arguments make sense, in context
            _check_load_arguments_none([fname, stop_fname, yr, doy, end_yr,
                                        end_doy], raise_error=True)

            # Ensure date portion from user is only year, month, day
            self._set_load_parameters(date=date, fid=None)
            date = pysat.utils.time.filter_datetime_input(date)

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
        loop_pad = self.pad if self.pad is not None else dt.timedelta(seconds=0)

        # Check for consistency between loading range and data padding, if any
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
                pysat.logger.warning(wstr)

        if (self.pad is not None) or self.multi_file_day:
            if self._empty(self._next_data) and self._empty(self._prev_data):
                # Data has not already been loaded for previous and next days.
                # Load data for all three.
                pysat.logger.debug('Initializing data cache.')

                # Using current date or fid
                self._prev_data, self._prev_meta = self._load_prev()
                self._curr_data, self._curr_meta = self._load_data(
                    date=self.date, fid=self._fid, inc=self.load_step,
                    load_kwargs=kwargs)
                self._next_data, self._next_meta = self._load_next()
            else:
                if self._next_data_track == curr:
                    pysat.logger.debug('Using data cache. Loading next.')
                    # Moving forward in time
                    del self._prev_data
                    self._prev_data = self._curr_data
                    self._prev_meta = self._curr_meta
                    self._curr_data = self._next_data
                    self._curr_meta = self._next_meta
                    self._next_data, self._next_meta = self._load_next()
                elif self._prev_data_track == curr:
                    pysat.logger.debug('Using data cache. Loading previous.')
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
                    pysat.logger.debug('Resetting data cache.')
                    del self._prev_data
                    del self._curr_data
                    del self._next_data
                    self._prev_data, self._prev_meta = self._load_prev()
                    self._curr_data, self._curr_meta = self._load_data(
                        date=self.date, fid=self._fid, inc=self.load_step,
                        load_kwargs=kwargs)
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
                # handled by __getitem__.
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

                # Pad data using access mechanisms that work for both pandas
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

        else:
            # If self.pad is False, load single day
            self.data, meta = self._load_data(date=self.date, fid=self._fid,
                                              inc=self.load_step,
                                              load_kwargs=kwargs)
            if not self.empty:
                # Data was returned. Assign returned metadata information.
                self.meta = meta
            else:
                estr = ''.join(('Metadata was not assigned as there was ',
                                'no data returned.'))
                pysat.logger.info(estr)

        if not self.empty:
            # Check for partial metadata, define the remaining variables.
            warn_missing_vars = []
            default_warn = "".join(["Metadata set to defaults, as they were ",
                                    "missing in the Instrument."])
            for var in self.vars_no_time:
                if var not in self.meta:
                    warn_missing_vars.append(var)
                    self.meta[var] = {self.meta.labels.name: var,
                                      self.meta.labels.notes: default_warn}

            if len(warn_missing_vars) > 0:
                default_warn = "".join(["Metadata for variables [{:s}] set to ",
                                        "defaults, as they were ",
                                        "missing in the Instrument."])
                default_warn = default_warn.format(', '.join(warn_missing_vars))
                warnings.warn(default_warn, stacklevel=2)

        # If loading by file and there is data, set the yr, doy, and date
        if not self._load_by_date and not self.empty:
            if self.pad is not None:
                temp = first_time
            else:
                temp = self.index[0]
            self.date = dt.datetime(temp.year, temp.month, temp.day)
            self.yr, self.doy = pysat.utils.time.getyrdoy(self.date)

        # Ensure data is unique and monotonic. Check occurs after all the data
        # padding loads, or individual load. Thus, it can potentially check
        # issues with padding or with raw data.
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

        # Apply custom functions via the nanokernel in `self.custom`
        if not self.empty:
            self.custom_apply_all()

        # Remove the excess data padding, if any applied
        if (self.pad is not None) & (not self.empty) & (not verifyPad):
            self.data = self[first_time: last_time]
            if not self.empty:
                if (self.index[-1] == last_time) & (not want_last_pad):
                    self.data = self[:-1]

        # Transfer any extra attributes in meta to the Instrument object.
        # TODO(#1020): Change the way this kwarg is handled
        if use_header or ('use_header' in self.kwargs['load']
                          and self.kwargs['load']['use_header']):
            self.meta.transfer_attributes_to_header()
        else:
            warnings.warn(''.join(['Meta now contains a class for global ',
                                   'metadata (MetaHeader). Default attachment ',
                                   'of global attributes to Instrument will ',
                                   'be Deprecated in pysat 3.2.0+. Set ',
                                   '`use_header=True` in this load call or ',
                                   'on Instrument instantiation to remove this',
                                   ' warning.']), DeprecationWarning,
                          stacklevel=2)
            self.meta.transfer_attributes_to_instrument(self)
        self.meta.mutable = False
        sys.stdout.flush()
        return

    def remote_file_list(self, start=None, stop=None, **kwargs):
        """Retrieve a time-series of remote files for chosen instrument.

        Parameters
        ----------
        start : dt.datetime or NoneType
            Starting time for file list. A None value will start with the first
            file found. (default=None)
        stop : dt.datetime or NoneType
            Ending time for the file list.  A None value will stop with the last
            file found. (default=None)
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments.
            The keyword arguments 'user' and 'password' are expected for remote
            databases requiring sign in or registration.

        Returns
        -------
        pds.Series
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
        """Determine first and last available dates for remote data.

        Parameters
        ----------
        start : dt.datetime or NoneType
            Starting time for file list. A None value will start with the first
            file found. (default=None)
        stop : dt.datetime or NoneType
            Ending time for the file list.  A None value will stop with the last
            file found. (default=None)
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments.
            The keyword arguments 'user' and 'password' are expected for remote
            databases requiring sign in or registration.

        Returns
        -------
        List
            First and last datetimes obtained from `remote_file_list`

        Note
        ----
        Default behaviour is to search all files.  User may additionally
        specify a given year, year/month, or year/month/day combination to
        return a subset of available files.

        """

        files = self.remote_file_list(start=start, stop=stop, **kwargs)
        return [files.index[0], files.index[-1]]

    def download_updated_files(self, **kwargs):
        """Download new files after comparing available remote and local files.

        Parameters
        ----------
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments

        Note
        ----
        Data will be downloaded to `self.files.data_path`

        If Instrument bounds are set to defaults they are updated
        after files are downloaded.

        If no remote file listing method is available, existing local files are
        assumed to be up-to-date and gaps are assumed to be missing files.

        If `start`, `stop`, or `date_array` are provided, only files at/between
        these times are considered for updating.  If no times are provided and
        a remote listing method is available, all new files will be downloaded.
        If no remote listing method is available, the current file limits are
        used as the starting and ending times.

        """

        # Get list of remote files
        remote_files = self.remote_file_list()
        if remote_files is not None and remote_files.empty:
            pysat.logger.warning(' '.join(('No remote files found. Unable to',
                                           'download latest data.')))
            return

        # Get current list of local files
        self.files.refresh()
        local_files = self.files.files

        # If there is no way to get a remote file list, get a date array
        # for the requested times that aren't available locally.  Otherwise,
        # compare the remote and local file lists.
        if remote_files is None:
            # Get an array of the desired dates
            if 'date_array' in kwargs.keys():
                new_dates = kwargs['date_array']
            elif 'start' in kwargs.keys():
                if 'stop' in kwargs.keys():
                    stop = kwargs['stop']
                else:
                    stop = kwargs['start'] + dt.timedelta(days=1)

                new_dates = pds.date_range(kwargs['start'], stop, freq='1D')
            else:
                new_dates = pds.date_range(local_files.index[0],
                                           local_files.index[-1], freq='1D')

            # Provide updating information
            pysat.logger.info(
                ' '.join(['No remote file listing method, looking for file',
                          'gaps between',
                          '{:} and'.format(new_dates[0].strftime('%d %b %Y')),
                          '{:}'.format(new_dates[-1].strftime('%d %b %Y')),
                          '(inclusive).']))

            # Determine which dates are missing
            missing_inds = [i for i, req_dates in enumerate(new_dates)
                            if req_dates not in local_files.index]

            # Extract only the missing dates
            new_dates = new_dates[missing_inds]
            pysat.logger.info(' '.join(('Found {:} days'.format(len(new_dates)),
                                        'with new files.')))
        else:
            # Compare local and remote files. First look for dates that are in
            # remote but not in local. Provide updating information.
            pysat.logger.info(' '.join(['A remote file listing method exists,',
                                        'looking for updated files and gaps at',
                                        'all times.']))

            new_dates = []
            for date in remote_files.index:
                if date not in local_files:
                    new_dates.append(date)

            # Now compare filenames between common dates as it may be a new
            # version or revision.  This will have a problem with filenames
            # that are faking daily data from monthly.
            for date in local_files.index:
                if date in remote_files.index:
                    if remote_files[date] != local_files[date]:
                        new_dates.append(date)
            new_dates = np.sort(new_dates)
            pysat.logger.info(' '.join(('Found {:} days'.format(len(new_dates)),
                                        'with new or updated files.')))

        if len(new_dates) > 0:
            # Update download kwargs to include new `date_array` value
            kwargs['date_array'] = new_dates

            # Download date for dates in new_dates (also includes new names)
            self.download(**kwargs)
        else:
            pysat.logger.info('Did not find any new or updated files.')

        return

    def download(self, start=None, stop=None, date_array=None,
                 **kwargs):
        """Download data for given Instrument object from start to stop.

        .. deprecated:: 3.2.0
           `freq`, which sets the step size for downloads, will be removed in
            the 3.2.0+ release.

        Parameters
        ----------
        start : pandas.datetime or NoneType
            Start date to download data, or yesterday if None is provided.
            (default=None)
        stop : pandas.datetime or NoneType
            Stop date (inclusive) to download data, or tomorrow if None is
            provided (default=None)
        date_array : list-like or NoneType
            Sequence of dates to download date for. Takes precedence over
            start and stop inputs (default=None)
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments.
            The keyword arguments 'user' and 'password' are expected for remote
            databases requiring sign in or registration. 'freq' temporarily
            ingested through this input option.

        Raises
        ------
        ValueError
            Raised if there is an issue creating `self.files.data_path`

        Note
        ----
        Data will be downloaded to `self.files.data_path`

        If Instrument bounds are set to defaults they are updated
        after files are downloaded.

        See Also
        --------
        pandas.DatetimeIndex

        """
        # Test for deprecated kwargs
        if 'freq' in kwargs.keys():
            warnings.warn("".join(["`pysat.Instrument.download` kwarg `freq` ",
                                   "has been deprecated and will be removed ",
                                   "in pysat 3.2.0+. Use `date_array` for ",
                                   "non-daily frequencies instead."]),
                          DeprecationWarning, stacklevel=2)
            freq = kwargs['freq']
            del kwargs['freq']
        else:
            freq = 'D'

        # Make sure directories are there, otherwise create them
        try:
            os.makedirs(self.files.data_path)
        except OSError as err:
            if err.errno != errno.EEXIST:
                # Ok if directories already exist, otherwise exit with an
                # error that includes the message from original error.
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
            pysat.logger.info(
                ' '.join(['Downloading the most recent data by',
                          'default (yesterday through tomorrow).']))
            start = self.yesterday()
            stop = self.tomorrow()
        elif stop is None and date_array is None:
            stop = start + dt.timedelta(days=1)

        pysat.logger.info(
            'Downloading data to: {:}'.format(self.files.data_path))

        if date_array is None:
            # Create range of dates for downloading data.  Make sure dates are
            # whole days.
            start = pysat.utils.time.filter_datetime_input(start)
            stop = pysat.utils.time.filter_datetime_input(stop)
            date_array = pysat.utils.time.create_date_range(start, stop,
                                                            freq=freq)

        # Add necessary kwargs to the optional kwargs
        kwargs['tag'] = self.tag
        kwargs['inst_id'] = self.inst_id
        kwargs['data_path'] = self.files.data_path
        for kwarg in self.kwargs['download']:
            if kwarg not in kwargs:
                kwargs[kwarg] = self.kwargs['download'][kwarg]

        # Download the data, if enough data is requested
        if len(date_array) > 0:
            self._download_rtn(date_array, **kwargs)

            # Get the current file date range
            first_date = self.files.start_date
            last_date = self.files.stop_date

            pysat.logger.info('Updating pysat file list')
            self.files.refresh()

            # If instrument object has default bounds, update them
            if len(self.bounds[0]) == 1:
                # Get current bounds
                curr_bound = self.bounds
                if self._iter_type == 'date':
                    if(curr_bound[0][0] == first_date
                       and curr_bound[1][0] == last_date):
                        pysat.logger.info(' '.join(('Updating instrument',
                                                    'object bounds by date')))
                        self.bounds = (self.files.start_date,
                                       self.files.stop_date, curr_bound[2],
                                       curr_bound[3])
                if self._iter_type == 'file':
                    # Account for the fact the file datetimes may not land
                    # exactly at start or end of a day.
                    dsel1 = slice(first_date, first_date
                                  + dt.timedelta(hours=23, minutes=59,
                                                 seconds=59))
                    dsel2 = slice(last_date, last_date
                                  + dt.timedelta(hours=23, minutes=59,
                                                 seconds=59))
                    if(curr_bound[0][0] == self.files[dsel1][0]
                       and curr_bound[1][0] == self.files[dsel2][-1]):
                        pysat.logger.info(' '.join(('Updating instrument',
                                                    'object bounds by file')))
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
        else:
            pysat.logger.warning('Requested download over an empty date range.')

        return

    def to_netcdf4(self, fname=None, base_instrument=None, epoch_name=None,
                   zlib=False, complevel=4, shuffle=True,
                   preserve_meta_case=False, export_nan=None,
                   unlimited_time=True, modify=False):
        """Store loaded data into a netCDF4 file.

        .. deprecated:: 3.0.2
            Changed `fname` from a kwarg to an arg of type str in the 3.2.0+
            release.

        Parameters
        ----------
        fname : str or NoneType
            Full path to save instrument object to (default=None)
        base_instrument : pysat.Instrument or NoneType
            Class used as a comparison, only attributes that are present with
            self and not on base_instrument are written to netCDF. Using None
            assigns an unmodified pysat.Instrument object. (default=None)
        epoch_name : str or NoneType
            Label in file for datetime index of Instrument object
            (default=None)
        zlib : bool
            Flag for engaging zlib compression (True - compression on)
            (default=False)
        complevel : int
            An integer flag between 1 and 9 describing the level of compression
            desired. Ignored if `zlib=False`. (default=4)
        shuffle : bool
            The HDF5 shuffle filter will be applied before compressing the data.
            This significantly improves compression. Ignored if `zlib=False`.
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
        modify : bool
             Flag specifying whether or not the changes made to the Instrument
             object needed to prepare it for writing should also be made to
             this object.  If False, the current Instrument object will remain
             unchanged. (default=False)

        Raises
        ------
        ValueError
            If required kwargs are not given values

        See Also
        --------
        pysat.utils.io.to_netcdf

        """
        if fname is None:
            warnings.warn("".join(["`fname` as a kwarg has been deprecated, ",
                                   "must supply a filename 3.2.0+"]),
                          DeprecationWarning, stacklevel=2)
            raise ValueError("Must supply an output filename")

        # Prepare the instrument object used to create the output file
        inst = self if modify else self.copy()

        # Write the output file
        pysat.utils.io.inst_to_netcdf(inst, fname=fname,
                                      base_instrument=base_instrument,
                                      epoch_name=epoch_name, zlib=zlib,
                                      complevel=complevel, shuffle=shuffle,
                                      preserve_meta_case=preserve_meta_case,
                                      export_nan=export_nan,
                                      unlimited_time=unlimited_time)

        return


# ----------------------------------------------------------------------------
#   Utilities and variables supporting the Instrument Object

# Hidden variable to store pysat reserved keywords. Defined here, since these
# values are used by both the Instrument class and a function defined below.
# In release 3.2.0+ `freq` will be removed.
_reserved_keywords = ['inst_id', 'tag', 'date_array', 'data_path', 'format_str',
                      'supported_tags', 'start', 'stop', 'freq', 'yr', 'doy',
                      'end_yr', 'end_doy', 'date', 'end_date', 'fname',
                      'fnames', 'stop_fname']


def _kwargs_keys_to_func_name(kwargs_key):
    """Convert from `self.kwargs` key name to the function or method name.

    Parameters
    ----------
    kwargs_key : str
        Key from `self.kwargs` dictionary

    Returns
    -------
    func_name : str
        Name of method or function associated with the input key

    """

    func_name = '_{:s}_rtn'.format(kwargs_key)
    return func_name


def _get_supported_keywords(local_func):
    """Get a dict of supported keywords.

    Parameters
    ----------
    local_func : function or method
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

    # Account for keywords that are treated by Instrument as args
    pre_kws = _reserved_keywords.copy()

    # Check if this is a partial function
    if isinstance(local_func, functools.partial):
        # Get keyword arguments already applied to function
        existing_kws = local_func.keywords

        # Pull out python function portion
        local_func = local_func.func
    else:
        existing_kws = {}

    # Account for keywords already set since input was a partial function
    pre_kws.extend(existing_kws.keys())

    # Get the lists of arguments and defaults. The args and kwargs are both
    # in the args list, and args are placed first.
    #
    # modified from code on
    # https://stackoverflow.com/questions/196960/
    # can-you-list-the-keyword-arguments-a-function-receives
    sig = inspect.getfullargspec(local_func)
    func_args = list(sig.args)

    # Recast the function defaults as a list instead of NoneType or tuple.
    # Inspect returns func_defaults=None when there are no defaults.
    if sig.defaults is None:
        func_defaults = []
    else:
        func_defaults = [dval for dval in sig.defaults]

    # Remove arguments from the start of the func_args list
    while len(func_args) > len(func_defaults):
        func_args.pop(0)

    # Remove pre-existing keywords from output. Start by identifying locations.
    pop_list = [i for i, arg in enumerate(func_args) if arg in pre_kws]

    # Remove pre-selected by cycling backwards through the list of indices
    for i in pop_list[::-1]:
        func_args.pop(i)
        func_defaults.pop(i)

    # Create the output dict
    out_dict = {akey: func_defaults[i] for i, akey in enumerate(func_args)}

    return out_dict


def _pass_func(*args, **kwargs):
    """Empty, default function for updatable Instrument methods."""
    pass


def _check_load_arguments_none(args, raise_error=False):
    """Ensure all arguments are None.

    Parameters
    ----------
    args : iterable object
        Variables that are to checked to ensure None
    raise_error : bool
        A flag that if True, will raise a ValueError if any one value in `args`
        is not None (default=False)

    Returns
    -------
    all_none : bool
        Flag that is True if all `args` values are None and False otherwise

    Raises
    ------
    ValueError
        If any one value in `args` is not None and `raise_error` is True

    Note
    ----
    Used to support `.load` method checks that arguments that should be
    None are None, while also keeping the `.load` method readable

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
