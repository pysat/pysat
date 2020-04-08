# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str

import copy
import functools
import inspect
import os
import string
import sys
import warnings

import numpy as np
import pandas as pds
import xarray as xr

from . import _custom
from . import _files
from . import _orbits
from . import _meta
from . import utils
from pysat import DataFrame
from pysat import logger


# main class for users
class Instrument(object):
    """Download, load, manage, modify and analyze science data.

    Parameters
    ----------
    platform : string
        name of platform/satellite.
    name : string
        name of instrument.
    tag : string, optional
        identifies particular subset of instrument data.
    sat_id : string, optional
        identity within constellation
    clean_level : {'clean','dusty','dirty','none'}, optional
        level of data quality
    pad : pandas.DateOffset, or dictionary, optional
        Length of time to pad the begining and end of loaded data for
        time-series processing. Extra data is removed after applying all
        custom functions. Dictionary, if supplied, is simply passed to
        pandas DateOffset.
    orbit_info : dict
        Orbit information, {'index':index, 'kind':kind, 'period':period}.
        See pysat.Orbits for more information.
    inst_module : module, optional
        Provide instrument module directly.
        Takes precedence over platform/name.
    update_files : boolean, optional
        If True, immediately query filesystem for instrument files and store.
    temporary_file_list : boolean, optional
        If true, the list of Instrument files will not be written to disk.
        Prevents a race condition when running multiple pysat processes.
    strict_time_flag : boolean, option (False)
        If true, pysat will check data to ensure times are unique and
        monotonic. In future versions, this will be fixed to True.
    multi_file_day : boolean, optional
        Set to True if Instrument data files for a day are spread across
        multiple files and data for day n could be found in a file
        with a timestamp of day n-1 or n+1.
    manual_org : bool
        if True, then pysat will look directly in pysat data directory
        for data files and will not use default /platform/name/tag
    directory_format : str
        directory naming structure in string format. Variables such as
        platform, name, and tag will be filled in as needed using python
        string formatting. The default directory structure would be
        expressed as '{platform}/{name}/{tag}'
    file_format : str or NoneType
        File naming structure in string format.  Variables such as year,
        month, and sat_id will be filled in as needed using python string
        formatting.  The default file format structure is supplied in the
        instrument list_files routine.
    ignore_empty_files : boolean
        if True, the list of files found will be checked to
        ensure the filesizes are greater than zero. Empty files are
        removed from the stored list of files.
    units_label : str
        String used to label units in storage. Defaults to 'units'.
    name_label : str
        String used to label long_name in storage. Defaults to 'name'.
    notes_label : str
       label to use for notes in storage. Defaults to 'notes'
    desc_label : str
       label to use for variable descriptions in storage. Defaults to 'desc'
    plot_label : str
       label to use to label variables in plots. Defaults to 'label'
    axis_label : str
        label to use for axis on a plot. Defaults to 'axis'
    scale_label : str
       label to use for plot scaling type in storage. Defaults to 'scale'
    min_label : str
       label to use for typical variable value min limit in storage.
       Defaults to 'value_min'
    max_label : str
       label to use for typical variable value max limit in storage.
       Defaults to 'value_max'
    fill_label : str
        label to use for fill values. Defaults to 'fill' but some
        implementations will use 'FillVal'

    Attributes
    ----------
    data : pandas.DataFrame
        loaded science data
    date : pandas.datetime
        date for loaded data
    yr : int
        year for loaded data
    bounds : (datetime/filename/None, datetime/filename/None)
        bounds for loading data, supply array_like for a season with gaps.
        Users may provide as a tuple or tuple of lists, but the attribute is
        stored as a tuple of lists for consistency
    doy : int
        day of year for loaded data
    files : pysat.Files
        interface to instrument files
    meta : pysat.Meta
        interface to instrument metadata, similar to netCDF 1.6
    orbits : pysat.Orbits
        interface to extracting data orbit-by-orbit
    custom : pysat.Custom
        interface to instrument nano-kernel
    kwargs : dictionary
        keyword arguments passed to instrument loading routine

    Note
    ----
    Pysat attempts to load the module platform_name.py located in
    the pysat/instruments directory. This module provides the underlying
    functionality to download, load, and clean instrument data.
    Alternatively, the module may be supplied directly
    using keyword inst_module.

    Examples
    --------
    ::

        # 1-second mag field data
        vefi = pysat.Instrument(platform='cnofs',
                                name='vefi',
                                tag='dc_b',
                                clean_level='clean')
        start = pysat.datetime(2009,1,1)
        stop = pysat.datetime(2009,1,2)
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

        # Ionosphere profiles from GPS occultation
        cosmic = pysat.Instrument('cosmic',
                                    'gps',
                                    'ionprf',
                                    altitude_bin=3)
        # bins profile using 3 km step
        cosmic.download(start, stop, user=user, password=password)
        cosmic.load(date=start)

    """

    def __init__(self, platform=None, name=None, tag=None, sat_id=None,
                 clean_level='clean', update_files=None, pad=None,
                 orbit_info=None, inst_module=None, multi_file_day=None,
                 manual_org=None, directory_format=None, file_format=None,
                 temporary_file_list=False, strict_time_flag=False,
                 ignore_empty_files=False,
                 units_label='units', name_label='long_name',
                 notes_label='notes', desc_label='desc',
                 plot_label='label', axis_label='axis', scale_label='scale',
                 min_label='value_min', max_label='value_max',
                 fill_label='fill', *arg, **kwargs):

        if inst_module is None:
            # use strings to look up module name
            if isinstance(platform, str) and isinstance(name, str):
                self.platform = platform.lower()
                self.name = name.lower()
                # look to module for instrument functions and defaults
                self._assign_funcs(by_name=True)
            elif (platform is None) and (name is None):
                # creating "empty" Instrument object with this path
                self.name = ''
                self.platform = ''
                self._assign_funcs()
            else:
                raise ValueError('Inputs platform and name must both be ' +
                                 'strings, or both None.')
        else:
            # user has provided a module
            try:
                # platform and name are expected to be part of module
                self.name = inst_module.name.lower()
                self.platform = inst_module.platform.lower()
            except AttributeError as err:
                raise AttributeError(' '.join((str(err), '\n',
                                               'A name and platform attribute',
                                               'for the instrument is',
                                               'required if supplying routine',
                                               'module directly.')))
            # look to module for instrument functions and defaults
            self._assign_funcs(inst_module=inst_module)

        # more reasonable defaults for optional parameters
        self.tag = tag.lower() if tag is not None else ''
        self.sat_id = sat_id.lower() if sat_id is not None else ''
        self.clean_level = (clean_level.lower() if clean_level is not None
                            else 'none')

        # assign strict_time_flag
        self.strict_time_flag = strict_time_flag

        # assign directory format information, how pysat looks in
        # sub-directories for files
        # assign_func sets some instrument defaults, direct info rules all
        if directory_format is not None:
            self.directory_format = directory_format.lower()
        # value not provided by user, check if there is a value provided by
        # instrument module
        elif self.directory_format is not None:
            try:
                # check if it is a function
                self.directory_format = self.directory_format(tag, sat_id)
            except TypeError:
                pass
        # assign the file format string, if provided by user
        # enables user to temporarily put in a new string template for files
        # that may not match the standard names obtained from download routine
        if file_format is not None:
            self.file_format = file_format
        # check to make sure value is reasonable
        if self.file_format is not None:
            # check if it is an iterable string.  If it isn't formatted
            # properly, raise Error
            if (not isinstance(self.file_format, str) or
                    (self.file_format.find("{") < 0) or
                    (self.file_format.find("}") < 0)):
                estr = 'file format set to default, supplied string must be '
                estr = '{:s}iteratable [{:}]'.format(estr, self.file_format)
                raise ValueError(estr)

        # set up empty data and metadata
        # check if pandas or xarray format
        if self.pandas_format:
            self._null_data = DataFrame(None)
            self._data_library = DataFrame
        else:
            self._null_data = xr.Dataset(None)
            self._data_library = xr.Dataset
        # assign null data for user selected data type
        self.data = self._null_data.copy()

        # create Meta instance with appropriate labels
        self.units_label = units_label
        self.name_label = name_label
        self.notes_label = notes_label
        self.desc_label = desc_label
        self.plot_label = plot_label
        self.axis_label = axis_label
        self.scale_label = scale_label
        self.min_label = min_label
        self.max_label = max_label
        self.fill_label = fill_label
        self.meta = _meta.Meta(units_label=self.units_label,
                               name_label=self.name_label,
                               notes_label=self.notes_label,
                               desc_label=self.desc_label,
                               plot_label=self.plot_label,
                               axis_label=self.axis_label,
                               scale_label=self.scale_label,
                               min_label=self.min_label,
                               max_label=self.max_label,
                               fill_label=self.fill_label)

        # function processing class, processes data on load
        self.custom = _custom.Custom()
        # create arrays to store data around loaded day
        # enables padding across day breaks with minimal loads
        self._next_data = self._null_data.copy()
        self._next_data_track = []
        self._prev_data = self._null_data.copy()
        self._prev_data_track = []
        self._curr_data = self._null_data.copy()

        # multi file day, default set by assign_funcs
        if multi_file_day is not None:
            self.multi_file_day = multi_file_day

        # arguments for padding
        if isinstance(pad, pds.DateOffset):
            self.pad = pad
        elif isinstance(pad, dict):
            self.pad = pds.DateOffset(**pad)
        elif pad is None:
            self.pad = None
        else:
            estr = 'pad must be a dictionary or a pandas.DateOffset instance.'
            raise ValueError(estr)

        # instantiate Files class
        manual_org = False if manual_org is None else manual_org
        temporary_file_list = not temporary_file_list
        self.files = _files.Files(self, manual_org=manual_org,
                                  directory_format=self.directory_format,
                                  update_files=update_files,
                                  file_format=self.file_format,
                                  write_to_disk=temporary_file_list,
                                  ignore_empty_files=ignore_empty_files)

        # set bounds for iteration
        # self.bounds requires the Files class
        # setting (None,None) loads default bounds
        self.bounds = (None, None)
        self.date = None
        self._fid = None
        self.yr = None
        self.doy = None
        self._load_by_date = False

        # initialize orbit support
        if orbit_info is None:
            if self.orbit_info is None:
                # if default info not provided, set None as default
                orbit_info = {'index': None, 'kind': None, 'period': None}
            else:
                # default provided by instrument module
                orbit_info = self.orbit_info
        self.orbits = _orbits.Orbits(self, **orbit_info)

        # Create empty placeholder for meta translation table
        # gives information about how to label metadata for netcdf export
        # if None, pysat metadata labels will be used
        self._meta_translation_table = None

        # Create a placeholder for a post-processing function to be applied
        # to the metadata dictionary before export. If None, no post-processing
        # will occur
        self._export_meta_post_processing = None

        # store kwargs, passed to load routine
        # first, check if keywords are  valid
        _check_if_keywords_supported(self._load_rtn, **kwargs)
        # store
        self.kwargs = kwargs

        # run instrument init function, a basic pass function is used
        # if user doesn't supply the init function
        self._init_rtn(self)

        # store base attributes, used in particular by Meta class
        self._base_attr = dir(self)

        # warn about changes coming in the future
        if not self.strict_time_flag:
            warnings.warn('Strict times will eventually be enforced upon all'
                          ' instruments. (strict_time_flag)', DeprecationWarning,
                          stacklevel=2)


    def __getitem__(self, key):
        """
        Convenience notation for accessing data; inst['name'] is inst.data.name

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
            inst[datetime1:datetime1, 'name1':'name2']

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
                    try:
                        # Assume key[0] is integer (including list or slice)
                        return self.data.loc[self.data.index[key[0]], key[1]]
                    except ValueError as err:
                        estring = ' '.join((str(err), "\n",
                                            "Unable to sort out data.",
                                            "Instrument has data : ",
                                            str(not self.empty), "\n",
                                            "Requested key : ", str(key)))
                        raise ValueError(estring)
            else:
                try:
                    # integer based indexing
                    return self.data.iloc[key]
                except:
                    try:
                        return self.data[key]
                    except ValueError as err:
                        estring = ' '.join((str(err), "\n",
                                            "Unable to sort out data access.",
                                            "Instrument has data : ",
                                            str(not self.empty), "\n",
                                            "Requested key : ", str(key)))
                        raise ValueError(estring)
        else:
            return self.__getitem_xarray__(key)

    def __getitem_xarray__(self, key):
        """
        Convenience notation for accessing data; inst['name'] is inst.data.name

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
            inst[datetime1:datetime1, 'name1':'name2']

        """
        if 'time' not in self.data:
            return xr.Dataset(None)
        if isinstance(key, tuple):
            if len(key) == 2:
                # support slicing time, variable name
                try:
                    return self.data.isel(time=key[0])[key[1]]
                except:
                    try:
                        return self.data.sel(time=key[0])[key[1]]
                    except TypeError: # construct dataset from names
                        return self.data[self.variables[key[1]]]
            else:
                # multidimensional indexing
                indict = {}
                for i, dim in enumerate(self[key[-1]].dims):
                    indict[dim] = key[i]

                return self.data[key[-1]][indict]
        else:
            try:
                # grab a particular variable by name
                return self.data[key]
            except:
                # that didn't work
                try:
                    # get all data variables but for a subset of time
                    # using integer indexing
                    return self.data.isel(time=key)
                except:
                    # subset of time, using label based indexing
                    return self.data.sel(time=key)

    def __setitem__(self, key, new):
        """Convenience method for adding data to instrument.

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

        import numpy as np

        # add data to main pandas.DataFrame, depending upon the input
        # aka slice, and a name
        if self.pandas_format:
            if isinstance(key, tuple):
                try:
                    # Pass directly through to loc
                    self.data.loc[key[0], key[1]] = new
                except (KeyError, TypeError):
                    # TypeError for single integer
                    # KeyError for list, array, slice of integers
                    try:
                        # Assume key[0] is integer (including list or slice)
                        self.data.loc[self.data.index[key[0]], key[1]] = new
                    except ValueError as err:
                        estring = ' '.join((str(err), "\n",
                                            "Unable to sort out data access.",
                                            "Instrument has data : ",
                                            str(not self.empty), "\n",
                                            "Requested key : ", str(key)))
                        raise ValueError(estring)
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
                    # input is a list_like of frames
                    # this is higher order data
                    # this process ensures
                    if ('meta' not in new) and \
                            (key not in self.meta.keys_nD()):
                        # create an empty Meta instance but with variable names
                        # this will ensure the correct defaults for all
                        # subvariables.  Meta can filter out empty metadata as
                        # needed, the check above reduces the need to create
                        # Meta instances
                        ho_meta = _meta.Meta(units_label=self.units_label,
                                             name_label=self.name_label,
                                             notes_label=self.notes_label,
                                             desc_label=self.desc_label,
                                             plot_label=self.plot_label,
                                             axis_label=self.axis_label,
                                             scale_label=self.scale_label,
                                             fill_label=self.fill_label,
                                             min_label=self.min_label,
                                             max_label=self.max_label)
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
                    # if dim == 'time':
                    #     indict[dim] = self.index[key[i]]
                try:
                    self.data[key[-1]].loc[indict] = in_data
                except:
                    indict['time'] = self.index[indict['time']]
                    self.data[key[-1]].loc[indict] = in_data
                self.meta[key[-1]] = new
                return
            elif isinstance(key, basestring):
                # assigning basic variable

                # if xarray input, take as is
                if isinstance(in_data, xr.DataArray):
                    self.data[key] = in_data

                # ok, not an xarray input
                # but if we have an iterable input, then we
                # go through here
                elif len(np.shape(in_data)) == 1:
                    # looking at a 1D input here
                    if len(in_data) == len(self.index):
                        # 1D input has the correct length for storage along
                        # 'time'
                        self.data[key] = ('time', in_data)
                    elif len(in_data) == 1:
                        # only provided a single number in iterable, make that
                        # the input for all times
                        self.data[key] = ('time', [in_data[0]]*len(self.index))
                    elif len(in_data) == 0:
                        # provided an empty iterable
                        # make everything NaN
                        self.data[key] = ('time', [np.nan]*len(self.index))
                # not an iterable input
                elif len(np.shape(in_data)) == 0:
                    # not given an iterable at all, single number
                    # make that number the input for all times
                    self.data[key] = ('time', [in_data]*len(self.index))

                else:
                    # multidimensional input that is not an xarray
                    # user needs to provide what is required
                    if isinstance(in_data, tuple):
                        self.data[key] = in_data
                    else:
                        raise ValueError('Must provide dimensions for xarray' +
                                         ' multidimensional data using input' +
                                         ' tuple.')

            elif hasattr(key, '__iter__'):
                # multiple input strings (keys) are provided, but not in tuple
                # form recurse back into this function, setting each
                # input individually
                for keyname in key:
                    self.data[keyname] = in_data[keyname]

            # attach metadata
            self.meta[key] = new

    @property
    def empty(self):
        """Boolean flag reflecting lack of data.

        True if there is no Instrument data."""

        if self.pandas_format:
            return self.data.empty
        else:
            if 'time' in self.data.indexes:
                return len(self.data.indexes['time']) == 0
            else:
                return True

    def _empty(self, data=None):
        """Boolean flag reflecting lack of data.

        True if there is no Instrument data."""

        if data is None:
            data = self.data
        if self.pandas_format:
            return data.empty
        else:
            if 'time' in data.indexes:
                return len(data.indexes['time']) == 0
            else:
                return True
    @property
    def date(self):
        """Date for loaded data."""
        return self._date

    @date.setter
    def date(self, new):
        """Date for loaded data."""
        self._date = self._filter_datetime_input(new)

    @property
    def index(self):
        """Returns time index of loaded data."""
        return self._index()

    def _index(self, data=None):
        """Returns time index of loaded data."""
        if data is None:
            data = self.data

        if self.pandas_format:
            return data.index
        else:
            if 'time' in data.indexes:
                return data.indexes['time']
            else:
                return pds.Index([])

    @property
    def variables(self):
        """Returns list of variables within loaded data."""

        if self.pandas_format:
            return self.data.columns
        else:
            return list(self.data.variables.keys())

    def copy(self):
        """Deep copy of the entire Instrument object."""

        return copy.deepcopy(self)

    def concat_data(self, data, *args, **kwargs):
        """Concats data1 and data2 for xarray or pandas as needed

        Parameters
        ----------
        data : pandas or xarray
           Data to be appended to data already within the Instrument object

        Returns
        -------
        void
            Instrument.data modified in place.

        Notes
        -----
        For pandas, sort=False is passed along to the underlying
        pandas.concat method. If sort is supplied as a keyword, the
        user provided value is used instead.

        For xarray, dim='time' is passed along to xarray.concat
        except if the user includes a value for dim as a
        keyword argument.

        """

        if self.pandas_format:
            if 'sort' in kwargs:
                sort = kwargs['sort']
                _ = kwargs.pop('sort')
            else:
                sort = False
            return pds.concat(data, sort=sort, *args, **kwargs)
        else:
            if 'dim' in kwargs:
                dim = kwargs['dim']
                _ = kwargs.pop('dim')
            else:
                dim = 'time'
            return xr.concat(data, dim=dim, *args, **kwargs)

    def _pass_func(*args, **kwargs):
        pass

    def _assign_funcs(self, by_name=False, inst_module=None):
        """Assign all external science instrument methods to Instrument object.
        """

        import importlib
        # set defaults
        self._list_rtn = self._pass_func
        self._load_rtn = self._pass_func
        self._default_rtn = self._pass_func
        self._clean_rtn = self._pass_func
        self._init_rtn = self._pass_func
        self._download_rtn = self._pass_func
        self._list_remote_rtn = self._pass_func
        # default params
        self.directory_format = None
        self.file_format = None
        self.multi_file_day = False
        self.orbit_info = None
        self.pandas_format = True

        if by_name:
            # look for code with filename name, any errors passed up
            inst = importlib.import_module(''.join(('.', self.platform, '_',
                                           self.name)),
                                           package='pysat.instruments')
        elif inst_module is not None:
            # user supplied an object with relevant instrument routines
            inst = inst_module
        else:
            # no module or name info, default pass functions assigned
            return

        try:
            self._load_rtn = inst.load
            self._list_rtn = inst.list_files
            self._download_rtn = inst.download
        except AttributeError as err:
            estr = 'A load, file_list, and download routine are required for '
            raise AttributeError("\n".join((str(err),
                                            '{:s}every instrument.'.format(estr))))
        try:
            self._default_rtn = inst.default
        except AttributeError:
            pass
        try:
            self._init_rtn = inst.init
        except AttributeError:
            pass
        try:
            self._clean_rtn = inst.clean
        except AttributeError:
            pass
        try:
            self._list_remote_rtn = inst.list_remote_files
        except AttributeError:
            pass

        # look for instrument default parameters
        try:
            self.directory_format = inst.directory_format
        except AttributeError:
            pass
        try:
            self.multi_file_day = inst.multi_file_day
        except AttributeError:
            pass
        try:
            self.orbit_info = inst.orbit_info
        except AttributeError:
            pass
        try:
            self.pandas_format = inst.pandas_format
        except AttributeError:
            pass

        return

    def __str__(self):

        output_str = '\npysat Instrument object\n'
        output_str += '-----------------------\n'
        output_str += 'Platform: ' + self.platform + '\n'
        output_str += 'Name: ' + self.name + '\n'
        output_str += 'Tag: ' + self.tag + '\n'
        output_str += 'Satellite id: ' + self.sat_id + '\n'

        output_str += '\nData Processing\n'
        output_str += '---------------\n'
        output_str += 'Cleaning Level: ' + self.clean_level + '\n'
        output_str += 'Data Padding: ' + self.pad.__repr__() + '\n'
        output_str += 'Keyword Arguments Passed to load(): '
        output_str += self.kwargs.__repr__() + '\nCustom Functions : \n'
        if len(self.custom._functions) > 0:
            for func in self.custom._functions:
                output_str += '    ' + func.__repr__() + '\n'
        else:
            output_str += '    ' + 'No functions applied.\n'

        output_str += '\nOrbit Settings' + '\n'
        output_str += '--------------' + '\n'
        if self.orbit_info is None:
            output_str += 'Orbit properties not set.\n'
        else:
            output_str += 'Orbit Kind: ' + self.orbit_info['kind'] + '\n'
            output_str += 'Orbit Index: ' + self.orbit_info['index'] + '\n'
            output_str += 'Orbit Period: '
            output_str += self.orbit_info['period'].__str__() + '\n'
            output_str += 'Number of Orbits: {:d}\n'.format(self.orbits.num)
            output_str += 'Loaded Orbit Number: '
            if self.orbits.current is not None:
                output_str += '{:d}\n'.format(self.orbits.current)
            else:
                output_str += 'None\n'

        output_str += '\nLocal File Statistics' + '\n'
        output_str += '---------------------' + '\n'
        output_str += 'Number of files: ' + str(len(self.files.files)) + '\n'

        if len(self.files.files) > 0:
            output_str += 'Date Range: '
            output_str += self.files.files.index[0].strftime('%d %B %Y')
            output_str += ' --- '
            output_str += self.files.files.index[-1].strftime('%d %B %Y')

        output_str += '\n\nLoaded Data Statistics'+'\n'
        output_str += '----------------------'+'\n'
        if not self.empty:
            # if self._fid is not None:
            #     output_str += 'Filename: ' +
            output_str += 'Date: ' + self.date.strftime('%d %B %Y') + '\n'
            output_str += 'DOY: {:03d}'.format(self.doy) + '\n'
            output_str += 'Time range: '
            output_str += self.index[0].strftime('%d %B %Y %H:%M:%S')
            output_str += ' --- '
            output_str += self.index[-1].strftime('%d %B %Y %H:%M:%S')+'\n'
            output_str += 'Number of Times: ' + str(len(self.index)) + '\n'
            output_str += 'Number of variables: ' + str(len(self.variables))

            output_str += '\n\nVariable Names:'+'\n'
            num = len(self.variables)//3
            for i in np.arange(num):
                output_str += self.variables[3 * i].ljust(30)
                output_str += self.variables[3 * i + 1].ljust(30)
                output_str += self.variables[3 * i + 2].ljust(30)+'\n'
            for i in np.arange(len(self.variables) - 3 * num):
                output_str += self.variables[i+3*num].ljust(30)
            output_str += '\n'
        else:
            output_str += 'No loaded data.'+'\n'
        output_str += '\n'

        return output_str

    def _filter_datetime_input(self, date):
        """
        Returns datetime that only includes year, month, and day.

        Parameters
        ----------
        date : datetime (array_like or single input)

        Returns
        -------
        datetime (or list of datetimes)
            Only includes year, month, and day from original input

        """

        if date is None:
            return date
        else:
            if hasattr(date, '__iter__'):
                return [pds.datetime(da.year, da.month, da.day) for da in date]
            else:
                return pds.datetime(date.year, date.month, date.day)

    def today(self):
        """Returns today's date, with no hour, minute, second, etc.

        Parameters
        ----------
        None

        Returns
        -------
        datetime
            Today's date

        """

        return self._filter_datetime_input(pds.datetime.today())

    def tomorrow(self):
        """Returns tomorrow's date, with no hour, minute, second, etc.

        Parameters
        ----------
        None

        Returns
        -------
        datetime
            Tomorrow's date

        """

        return self.today() + pds.DateOffset(days=1)

    def yesterday(self):
        """Returns yesterday's date, with no hour, minute, second, etc.

        Parameters
        ----------
        None

        Returns
        -------
        datetime
            Yesterday's date

        """

        return self.today() - pds.DateOffset(days=1)

    def _load_data(self, date=None, fid=None):
        """
        Load data for an instrument on given date or fid, dependng upon input.

        Parameters
        ----------
        date : (dt.datetime.date object or NoneType)
            file date
        fid : (int or NoneType)
            filename index value

        Returns
        --------
        data : (pds.DataFrame or xr.Dataset)
            pysat data
        meta : (pysat.Meta)
            pysat meta data
        """

        date = self._filter_datetime_input(date)
        if fid is not None:
            # get filename based off of index value
            fname = self.files[fid:fid+1]
        elif date is not None:
            fname = self.files[date:date+pds.DateOffset(days=1)]
        else:
            raise ValueError('Must supply either a date or file id number.')

        if len(fname) > 0:
            load_fname = [os.path.join(self.files.data_path, f) for f in fname]
            try:
                data, mdata = self._load_rtn(load_fname, tag=self.tag,
                                             sat_id=self.sat_id, **self.kwargs)
                # ensure units and name are named consistently in new Meta
                # object as specified by user upon Instrument instantiation
                mdata.accept_default_labels(self)
                bad_datetime = False
            except pds.errors.OutOfBoundsDatetime:
                bad_datetime = True
                data = self._null_data.copy()
                mdata = _meta.Meta(units_label=self.units_label,
                                   name_label=self.name_label,
                                   notes_label=self.notes_label,
                                   desc_label=self.desc_label,
                                   plot_label=self.plot_label,
                                   axis_label=self.axis_label,
                                   scale_label=self.scale_label,
                                   min_label=self.min_label,
                                   max_label=self.max_label,
                                   fill_label=self.fill_label)

        else:
            bad_datetime = False
            data = self._null_data.copy()
            mdata = _meta.Meta(units_label=self.units_label,
                               name_label=self.name_label,
                               notes_label=self.notes_label,
                               desc_label=self.desc_label,
                               plot_label=self.plot_label,
                               axis_label=self.axis_label,
                               scale_label=self.scale_label,
                               min_label=self.min_label,
                               max_label=self.max_label,
                               fill_label=self.fill_label)

        output_str = '{platform} {name} {tag} {sat_id}'
        output_str = output_str.format(platform=self.platform,
                                       name=self.name, tag=self.tag,
                                       sat_id=self.sat_id)
        # check that data and metadata are the data types we expect
        if not isinstance(data, self._data_library):
            raise TypeError(' '.join(('Data returned by instrument load',
                            'routine must be a', self._data_library)))
        if not isinstance(mdata, _meta.Meta):
            raise TypeError('Metadata returned must be a pysat.Meta object')

        # let user know if data was returned or not
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

        # remove extra spaces, if any
        output_str = " ".join(output_str.split())
        logger.info(output_str)
        return data, mdata

    def _load_next(self):
        """Load the next days data (or file) without incrementing the date.
        Repeated calls will not advance date/file and will produce the same
        data.

        Uses info stored in object to either increment the date,
        or the file. Looks for self._load_by_date flag.

        """
        if self._load_by_date:
            next_date = self.date + pds.DateOffset(days=1)
            return self._load_data(date=next_date)
        else:
            return self._load_data(fid=self._fid+1)

    def _load_prev(self):
        """Load the next days data (or file) without decrementing the date.
        Repeated calls will not decrement date/file and will produce the same
        data

        Uses info stored in object to either decrement the date,
        or the file. Looks for self._load_by_date flag.

        """

        if self._load_by_date:
            prev_date = self.date - pds.DateOffset(days=1)
            return self._load_data(date=prev_date)
        else:
            return self._load_data(fid=self._fid-1)

    def _set_load_parameters(self, date=None, fid=None):
        # filter supplied data so that it is only year, month, and day
        # and then store as part of instrument object
        # filtering instrinsic to assignment
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

    def load(self, yr=None, doy=None, date=None, fname=None, fid=None,
             verifyPad=False):
        """Load instrument data into Instrument object .data.

        Parameters
        ----------
        yr : integer
            year for desired data
        doy : integer
            day of year
        date : datetime object
            date to load
        fname : 'string'
            filename to be loaded
        verifyPad : boolean
            if True, padding data not removed (debug purposes)

        Returns
        --------
        Void.  Data is added to self.data

        Note
        ----
        Loads data for a chosen instrument into .data. Any functions chosen
        by the user and added to the custom processing queue (.custom.add)
        are automatically applied to the data before it is available to
        user in .data.

        """
        # set options used by loading routine based upon user input
        if date is not None:
            # ensure date portion from user is only year, month, day
            self._set_load_parameters(date=date,
                                      fid=None)
            # increment
            inc = pds.DateOffset(days=1)
            curr = self._filter_datetime_input(date)
        elif (yr is not None) & (doy is not None):
            date = pds.datetime(yr, 1, 1) + pds.DateOffset(days=(doy-1))
            self._set_load_parameters(date=date, fid=None)
            # increment
            inc = pds.DateOffset(days=1)
            curr = self.date
        elif fname is not None:
            # date will have to be set later by looking at the data
            self._set_load_parameters(date=None,
                                      fid=self.files.get_index(fname))
            # increment one file at a time
            inc = 1
            curr = self._fid.copy()
        elif fid is not None:
            self._set_load_parameters(date=None, fid=fid)
            # increment one file at a time
            inc = 1
            curr = fid
        else:
            estr = 'Must supply a yr,doy pair, or datetime object, or filename'
            estr = '{:s} to load data from.'.format(estr)
            raise TypeError(estr)

        self.orbits._reset()
        # if pad  or multi_file_day is true, need to have a three day/file load
        loop_pad = self.pad if self.pad is not None \
            else pds.DateOffset(seconds=0)
        if (self.pad is not None) | self.multi_file_day:
            if self._empty(self._next_data) & self._empty(self._prev_data):
                # data has not already been loaded for previous and next days
                # load data for all three
                logger.info('Initializing three day/file window')
                # using current date or fid
                self._prev_data, self._prev_meta = self._load_prev()
                self._curr_data, self._curr_meta = \
                    self._load_data(date=self.date, fid=self._fid)
                self._next_data, self._next_meta = self._load_next()
            else:
                # moving forward in time
                if self._next_data_track == curr:
                    del self._prev_data
                    self._prev_data = self._curr_data
                    self._prev_meta = self._curr_meta
                    self._curr_data = self._next_data
                    self._curr_meta = self._next_meta
                    self._next_data, self._next_meta = self._load_next()
                # moving backward in time
                elif self._prev_data_track == curr:
                    del self._next_data
                    self._next_data = self._curr_data
                    self._next_meta = self._curr_meta
                    self._curr_data = self._prev_data
                    self._curr_meta = self._prev_meta
                    self._prev_data, self._prev_meta = self._load_prev()
                # jumped in time/or switched from filebased to date based
                # access
                else:
                    del self._prev_data
                    del self._curr_data
                    del self._next_data
                    self._prev_data, self._prev_meta = self._load_prev()
                    self._curr_data, self._curr_meta = \
                        self._load_data(date=self.date, fid=self._fid)
                    self._next_data, self._next_meta = self._load_next()

            # make sure datetime indices for all data is monotonic
            if not self._index(self._prev_data).is_monotonic_increasing:
                self._prev_data.sort_index(inplace=True)
            if not self._index(self._curr_data).is_monotonic_increasing:
                self._curr_data.sort_index(inplace=True)
            if not self._index(self._next_data).is_monotonic_increasing:
                self._next_data.sort_index(inplace=True)

            # make tracking indexes consistent with new loads
            self._next_data_track = curr + inc
            self._prev_data_track = curr - inc
            # attach data to object
            if not self._empty(self._curr_data):
                self.data = self._curr_data.copy()
                self.meta = self._curr_meta.copy()
            else:
                self.data = self._null_data.copy()
                # line below removed as it would delete previous meta, if any
                # if you end a seasonal analysis with a day with no data, then
                # no meta: self.meta = _meta.Meta()

            # multi file days can extend past a single day, only want data from
            # specific date if loading by day
            # set up times for the possible data padding coming up
            if self._load_by_date:
                first_time = self.date
                first_pad = self.date - loop_pad
                last_time = self.date + pds.DateOffset(days=1)
                last_pad = self.date + pds.DateOffset(days=1) + loop_pad
                want_last_pad = False
            # loading by file, can't be a multi_file-day flag situation
            elif (not self._load_by_date) and (not self.multi_file_day):
                first_time = self._index(self._curr_data)[0]
                first_pad = first_time - loop_pad
                last_time = self._index(self._curr_data)[-1]
                last_pad = last_time + loop_pad
                want_last_pad = True
            else:
                raise ValueError("multi_file_day and loading by date are " +
                                 "effectively equivalent.  Can't have " +
                                 "multi_file_day and load by file.")

            # pad data based upon passed parameter
            if (not self._empty(self._prev_data)) & (not self.empty):
                stored_data = self.data  # .copy()
                temp_time = copy.deepcopy(self.index[0])
                # pad data using access mechanisms that works
                # for both pandas and xarray
                self.data = self._prev_data.copy()
                # __getitem__ used below to get data
                # from instrument object. Details
                # for handling pandas and xarray are different
                # and handled by __getitem__
                self.data = self[first_pad:temp_time]
                if not self.empty:
                    if (self.index[-1] == temp_time):
                        self.data = self[:-1]
                    self.data = self.concat_data([self.data, stored_data])
                else:
                    self.data = stored_data

            if (not self._empty(self._next_data)) & (not self.empty):
                stored_data = self.data  # .copy()
                temp_time = copy.deepcopy(self.index[-1])
                # pad data using access mechanisms that work
                # for both pandas and xarray
                self.data = self._next_data.copy()
                self.data = self[temp_time:last_pad]
                if not self.empty:
                    if (self.index[0] == temp_time):
                        self.data = self[1:]
                    self.data = self.concat_data([stored_data, self.data])
                else:
                    self.data = stored_data

            self.data = self[first_pad:last_pad]
            # want exclusive end slicing behavior from above
            if not self.empty:
                if (self.index[-1] == last_pad) & (not want_last_pad):
                    self.data = self[:-1]

        # if self.pad is False, load single day
        else:
            self.data, meta = self._load_data(date=self.date, fid=self._fid)
            if not self.empty:
                self.meta = meta

        # check if load routine actually returns meta
        if self.meta.data.empty:
            self.meta[self.variables] = {self.name_label: self.variables,
                                         self.units_label: [''] *
                                         len(self.variables)}

        # if loading by file set the yr, doy, and date
        if not self._load_by_date:
            if self.pad is not None:
                temp = first_time
            else:
                temp = self.index[0]
            self.date = pds.datetime(temp.year, temp.month, temp.day)
            self.yr, self.doy = utils.time.getyrdoy(self.date)

        # ensure data is unique and monotonic
        # check occurs after all the data padding loads, or individual load
        # thus it can potentially check issues with padding or with raw data
        if self.strict_time_flag:
            if (not self.index.is_monotonic_increasing) or (not self.index.is_unique):
                raise ValueError('Loaded data is not unique (',not self.index.is_unique,
                                 ') or not monotonic increasing (',
                                 not self.index.is_monotonic_increasing,
                                 ')')

        # apply default instrument routine, if data present
        if not self.empty:
            self._default_rtn(self)

        # clean data, if data is present and cleaning requested
        if (not self.empty) & (self.clean_level != 'none'):
            self._clean_rtn(self)

        # apply custom functions via the nanokernel in self.custom
        if not self.empty:
            self.custom._apply_all(self)

        # remove the excess data padding, if any applied
        if (self.pad is not None) & (not self.empty) & (not verifyPad):
            self.data = self[first_time: last_time]
            if not self.empty:
                if (self.index[-1] == last_time) & (not want_last_pad):
                    self.data = self[:-1]

        # transfer any extra attributes in meta to the Instrument object
        self.meta.transfer_attributes_to_instrument(self)
        self.meta.mutable = False
        sys.stdout.flush()
        return

    def remote_file_list(self, year=None, month=None, day=None):
        """List remote files for chosen instrument.  Default behaviour is
        to return all files.  User may additionally specify a given year,
        year/month, or year/month/day combination to return a subset of
        available files.

        Keywords
        --------
        year : int or NoneType
            Selected year to return remote files.  A None value will return
            all available files.
            (default=None)
        month : int or NoneType
            Selected month to return remote files.  A year must be specified.
            A None value will return all available files for the year, if year
            is specified.
            (default=None)
        day : int or NoneType
            Selected day to return remote files.  A year and month must be
            specified. A None value will return all available files for the
            year or month, if keywords are specified.
            (default=None)

        Returns
        -------
        Series
            pandas Series of filenames indexed by date and time

        """

        return self._list_remote_rtn(self.tag, self.sat_id,
                                     year=year, month=month, day=day)

    def remote_date_range(self, year=None, month=None, day=None):
        """Returns fist and last date for remote data.  Default behaviour is
        to search all files.  User may additionally specify a given year,
        year/month, or year/month/day combination to return a subset of
        available files.

        Keywords
        --------
        year : int or NoneType
            Selected year to return remote files.  A None value will return
            all available files.
            (default=None)
        month : int or NoneType
            Selected month to return remote files.  A year must be specified.
            A None value will return all available files for the year, if year
            is specified.
            (default=None)
        day : int or NoneType
            Selected day to return remote files.  A year and month must be
            specified. A None value will return all available files for the
            year or month, if keywords are specified.
            (default=None)

        Returns
        -------
        List
            First and last datetimes obtained from remote_file_list

        """

        files = self.remote_file_list(year=year, month=month, day=day)
        return [files.index[0], files.index[-1]]

    def download_updated_files(self, user=None, password=None, **kwargs):
        """Grabs a list of remote files, compares to local, then downloads new
        files.

        Parameters
        ----------
        user : string
            username, if required by instrument data archive
        password : string
            password, if required by instrument data archive
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
            logger.warn('No remote files found. Unable to download latest data.')
            return

        # get current list of local files
        self.files.refresh()
        local_files = self.files.files
        # compare local and remote files

        # first look for dates that are in remote but not in local
        new_dates = []
        for date in remote_files.index:
            if date not in local_files:
                new_dates.append(date)

        # now compare filenames between common dates as it may
        # be a new version or revision
        # this will have a problem with filenames that are
        # faking daily data from monthly
        for date in local_files.index:
            if date in remote_files.index:
                if remote_files[date] != local_files[date]:
                    new_dates.append(date)
        logger.info('Found {} files that are new or updated.'.format(len(new_dates)))
        # download date for dates in new_dates (also includes new names)
        self.download(user=user, password=password, date_array=new_dates,
                      **kwargs)

    def download(self, start=None, stop=None, freq='D', user=None,
                 password=None, date_array=None, **kwargs):
        """Download data for given Instrument object from start to stop.

        Parameters
        ----------
        start : pandas.datetime (yesterday)
            start date to download data
        stop : pandas.datetime (tomorrow)
            stop date to download data
        freq : string
            Stepsize between dates for season, 'D' for daily, 'M' monthly
            (see pandas)
        user : string
            username, if required by instrument data archive
        password : string
            password, if required by instrument data archive
        date_array : list-like
            Sequence of dates to download date for. Takes precendence over
            start and stop inputs
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments

        Note
        ----
        Data will be downloaded to pysat_data_dir/patform/name/tag

        If Instrument bounds are set to defaults they are updated
        after files are downloaded.

        """
        import errno
        # make sure directories are there, otherwise create them
        try:
            os.makedirs(self.files.data_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        if ((start is None) or (stop is None)) and (date_array is None):
            # defaults for downloads are set here rather than
            # in the method signature since method defaults are
            # only set once! If an Instrument object persists
            # longer than a day then the download defaults would
            # no longer be correct. Dates are always correct in this
            # setup.
            logger.info('Downloading the most recent data by default ' +
                  '(yesterday through tomorrow).')
            start = self.yesterday()
            stop = self.tomorrow()
        logger.info('Downloading data to: {}'.format(self.files.data_path))

        if date_array is None:
            # create range of dates to download data for
            # make sure dates are whole days
            start = self._filter_datetime_input(start)
            stop = self._filter_datetime_input(stop)
            date_array = utils.time.create_date_range(start, stop, freq=freq)

        if user is None:
            self._download_rtn(date_array,
                               tag=self.tag,
                               sat_id=self.sat_id,
                               data_path=self.files.data_path,
                               **kwargs)
        else:
            self._download_rtn(date_array,
                               tag=self.tag,
                               sat_id=self.sat_id,
                               data_path=self.files.data_path,
                               user=user,
                               password=password, **kwargs)
        # get current file date range
        first_date = self.files.start_date
        last_date = self.files.stop_date

        logger.info('Updating pysat file list')
        self.files.refresh()

        # if instrument object has default bounds, update them
        if len(self.bounds[0]) == 1:
            if(self.bounds[0][0] == first_date and
               self.bounds[1][0] == last_date):
                logger.info('Updating instrument object bounds.')
                self.bounds = None

    @property
    def bounds(self):
        """Boundaries for iterating over instrument object by date or file.

        Parameters
        ----------
        start : datetime object, filename, or None (default)
            start of iteration, if None uses first data date.
            list-like collection also accepted
        end :  datetime object, filename, or None (default)
            end of iteration, inclusive. If None uses last data date.
            list-like collection also accepted

        Note
        ----
        Both start and stop must be the same type (date, or filename) or None.
        Only the year, month, and day are used for date inputs.

        Examples
        --------
        ::

            inst = pysat.Instrument(platform=platform,
                                    name=name,
                                    tag=tag)
            start = pysat.datetime(2009,1,1)
            stop = pysat.datetime(2009,1,31)
            inst.bounds = (start,stop)

            start2 = pysat.datetetime(2010,1,1)
            stop2 = pysat.datetime(2010,2,14)
            inst.bounds = ([start, start2], [stop, stop2])

        """
        return self._iter_start, self._iter_stop

    @bounds.setter
    def bounds(self, value=None):
        if value is None:
            value = (None, None)
        if len(value) < 2:
            raise ValueError('Must supply both a start and end date/file' +
                             'Supply None if you want the first/last possible')

        start = value[0]
        end = value[1]
        # get the frequency, or step size, of season
        if len(value) == 3:
            step = value[2]
        else:
            # default to daily
            step = 'D'

        if (start is None) and (end is None):
            # set default
            self._iter_start = [self.files.start_date]
            self._iter_stop = [self.files.stop_date]
            self._iter_type = 'date'
            if self._iter_start[0] is not None:
                # check here in case Instrument is initialized with no input
                self._iter_list = \
                    utils.time.create_date_range(self._iter_start,
                                                 self._iter_stop,
                                                 freq=step)

        elif((hasattr(start, '__iter__') and not isinstance(start, str)) and
             (hasattr(end, '__iter__') and not isinstance(end, str))):
            base = type(start[0])
            for s, t in zip(start, end):
                if (type(s) != type(t)) or (type(s) != base):
                    raise ValueError(' '.join(('Start and end items must all',
                                               'be of the same type')))
            if isinstance(start[0], str):
                self._iter_type = 'file'
                self._iter_list = self.files.get_file_array(start, end)
            elif isinstance(start[0], pds.datetime):
                self._iter_type = 'date'
                start = self._filter_datetime_input(start)
                end = self._filter_datetime_input(end)
                self._iter_list = utils.time.create_date_range(start, end, freq=step)
            else:
                raise ValueError('Input is not a known type, string or ' +
                                 'datetime')
            self._iter_start = start
            self._iter_stop = end

        elif((hasattr(start, '__iter__') and not isinstance(start, str)) or
             (hasattr(end, '__iter__') and not isinstance(end, str))):
            raise ValueError('Both start and end must be iterable if one ' +
                             'bound is iterable')

        elif isinstance(start, str) or isinstance(end, str):
            if isinstance(start, pds.datetime) or \
                    isinstance(end, pds.datetime):
                raise ValueError('Not allowed to mix file and date bounds')
            if start is None:
                start = self.files[0]
            if end is None:
                end = self.files.files[-1]
            self._iter_start = [start]
            self._iter_stop = [end]
            self._iter_list = self.files.get_file_array(self._iter_start,
                                                        self._iter_stop)
            self._iter_type = 'file'

        elif isinstance(start, pds.datetime) or isinstance(end, pds.datetime):
            if start is None:
                start = self.files.start_date
            if end is None:
                end = self.files.stop_date
            self._iter_start = [self._filter_datetime_input(start)]
            self._iter_stop = [self._filter_datetime_input(end)]
            self._iter_list = utils.time.create_date_range(self._iter_start,
                                                           self._iter_stop,
                                                           freq=step)
            self._iter_type = 'date'
        else:
            raise ValueError(''.join(('Provided an invalid combination of',
                                      ' bounds. if specifying by file, both',
                                      ' bounds must be by file. Other ',
                                      'combinations of datetime objects ',
                                      'and None are allowed.')))

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

            inst = pysat.Instrument(platform=platform,
                                    name=name,
                                    tag=tag)
            start = pysat.datetime(2009,1,1)
            stop = pysat.datetime(2009,1,31)
            inst.bounds = (start,stop)
            for inst in inst:
                print('Another day loaded', inst.date)

        """

        if self._iter_type == 'file':
            for fname in self._iter_list:
                self.load(fname=fname)
                yield self

        elif self._iter_type == 'date':
            for date in self._iter_list:
                self.load(date=date)
                yield self

    def next(self, verifyPad=False):
        """Manually iterate through the data loaded in Instrument object.

        Bounds of iteration and iteration type (day/file) are set by
        `bounds` attribute.

        Note
        ----
        If there were no previous calls to load then the
        first day(default)/file will be loaded.

        """

        if self._iter_type == 'date':
            if self.date is not None:
                idx, = np.where(self._iter_list == self.date)
                if (len(idx) == 0):
                    raise StopIteration(''.join(('File list is empty. ',
                                                 'Nothing to be done.')))
                elif idx[-1] + 1 >= len(self._iter_list):
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    idx += 1
                    self.load(date=self._iter_list[idx[0]],
                              verifyPad=verifyPad)
            else:
                self.load(date=self._iter_list[0], verifyPad=verifyPad)

        elif self._iter_type == 'file':
            if self._fid is not None:
                first = self.files.get_index(self._iter_list[0])
                last = self.files.get_index(self._iter_list[-1])
                if (self._fid < first) | (self._fid+1 > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    self.load(fname=self._iter_list[self._fid + 1 - first],
                              verifyPad=verifyPad)
            else:
                self.load(fname=self._iter_list[0], verifyPad=verifyPad)

    def prev(self, verifyPad=False):
        """Manually iterate backwards through the data in Instrument object.

        Bounds of iteration and iteration type (day/file)
        are set by `bounds` attribute.

        Note
        ----
        If there were no previous calls to load then the
        first day(default)/file will be loaded.

        """

        if self._iter_type == 'date':
            if self.date is not None:
                idx, = np.where(self._iter_list == self.date)
                if len(idx) == 0:
                    raise StopIteration(''.join(('File list is empty. ',
                                                 'Nothing to be done.')))
                elif idx[0] == 0:
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    idx -= 1
                    self.load(date=self._iter_list[idx[0]],
                              verifyPad=verifyPad)
            else:
                self.load(date=self._iter_list[-1], verifyPad=verifyPad)

        elif self._iter_type == 'file':
            if self._fid is not None:
                first = self.files.get_index(self._iter_list[0])
                last = self.files.get_index(self._iter_list[-1])
                if (self._fid-1 < first) | (self._fid > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    self.load(fname=self._iter_list[self._fid-1-first],
                              verifyPad=verifyPad)
            else:
                self.load(fname=self._iter_list[-1], verifyPad=verifyPad)

    def _get_var_type_code(self, coltype):
        '''Determines the two-character type code for a given variable type

        Parameters
        ----------
        coltype : type or np.dtype
            The type of the variable

        Returns
        -------
        str
            The variable type code for the given type'''

        if type(coltype) is np.dtype:
            var_type = coltype.kind + str(coltype.itemsize)
            return var_type
        else:
            if coltype is np.int64:
                return 'i8'
            elif coltype is np.int32:
                return 'i4'
            elif coltype is np.int16:
                return 'i2'
            elif coltype is np.int8:
                return 'i1'
            elif coltype is np.uint64:
                return 'u8'
            elif coltype is np.uint32:
                return 'u4'
            elif coltype is np.uint16:
                return 'u2'
            elif coltype is np.uint8:
                return 'u1'
            elif coltype is np.float64:
                return 'f8'
            elif coltype is np.float32:
                return 'f4'
            elif issubclass(coltype, basestring):
                return 'S1'
            else:
                raise TypeError('Unknown Variable Type' + str(coltype))

    def _get_data_info(self, data, file_format):
        """Support file writing by determining data type and other options

        Parameters
        ----------
        data : pandas object
            Data to be written
        file_format : basestring
            String indicating netCDF3 or netCDF4

        Returns
        -------
        data_flag, datetime_flag, old_format
        """
        # get type of data
        data_type = data.dtype
        # check if older file_format
        # if file_format[:7] == 'NETCDF3':
        if file_format != 'NETCDF4':
            old_format = True
        else:
            old_format = False
        # check for object type
        if data_type != np.dtype('O'):
            # simple data, not an object

            # no 64bit ints in netCDF3
            if (data_type == np.int64) & old_format:
                data = data.astype(np.int32)
                data_type = np.int32

            if data_type == np.dtype('<M8[ns]'):
                if not old_format:
                    data_type = np.int64
                else:
                    data_type = np.float
                datetime_flag = True
            else:
                datetime_flag = False
        else:
            # dealing with a more complicated object
            # iterate over elements until we hit something that is something,
            # and not NaN
            data_type = type(data.iloc[0])
            for i in np.arange(len(data)):
                if len(data.iloc[i]) > 0:
                    data_type = type(data.iloc[i])
                    if not isinstance(data_type, np.float):
                        break
            datetime_flag = False

        return data, data_type, datetime_flag

    def _filter_netcdf4_metadata(self, mdata_dict, coltype, remove=False):
        """Filter metadata properties to be consistent with netCDF4.

        Notes
        -----
        removed forced to True if coltype consistent with a string type

        Parameters
        ----------
        mdata_dict : dict
            Dictionary equivalent to Meta object info
        coltype : type
            Type provided by _get_data_info
        remove : boolean (False)
            Removes FillValue and associated parameters disallowed for strings

        Returns
        -------
        dict
            Modified as needed for netCDf4

        """
        # Coerce boolean types to integers
        for key in mdata_dict:
            if type(mdata_dict[key]) == bool:
                mdata_dict[key] = int(mdata_dict[key])
        # Should use isinstance here
        if (coltype == type(' ')) or (coltype == type(u' ')):
            # if isinstance(coltype, str):
            remove = True
            warnings.warn('FillValue is not an acceptable '
                          'parameter for strings it will be removed')
        
        # print('coltype', coltype, remove, type(coltype), )
        if u'_FillValue' in mdata_dict.keys():
            # make sure _FillValue is the same type as the data
            if remove:
                mdata_dict.pop('_FillValue')
            else:
                if not np.can_cast(mdata_dict['_FillValue'], coltype):
                    if 'FieldNam' in mdata_dict:
                         warnings.warn('FillValue for %s (%s) cannot be safely '
                                      'casted to %s Casting anyways. '
                                      'This may result in unexpected behavior'
                                      % (mdata_dict['FieldNam'],
                                         str(mdata_dict['_FillValue']),
                                         coltype))
                    else:
                        warnings.warn('FillValue %s cannot be safely '
                                      'casted to %s. Casting anyways. '
                                      'This may result in unexpected behavior'
                                      % (str(mdata_dict['_FillValue']),
                                         coltype))
                mdata_dict['_FillValue'] = \
                    np.array(mdata_dict['_FillValue']).astype(coltype)
        if u'FillVal' in mdata_dict.keys():
            # make sure _FillValue is the same type as the data
            if remove:
                mdata_dict.pop('FillVal')
            else:
                mdata_dict['FillVal'] = \
                    np.array(mdata_dict['FillVal']).astype(coltype)
        return mdata_dict

    def generic_meta_translator(self, meta_to_translate):
        '''Translates the metadate contained in an object into a dictionary
        suitable for export.

        Parameters
        ----------
        meta_to_translate : Meta
            The metadata object to translate

        Returns
        -------
        dict
            A dictionary of the metadata for each variable of an output file
            e.g. netcdf4'''
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
        for key in meta_to_translate.data.index:
            if translation_table is None:
                export_dict[key] = meta_to_translate.data.loc[key].to_dict()
            else:
                # Translate each key if a translation is provided
                export_dict[key] = {}
                meta_dict = meta_to_translate.data.loc[key].to_dict()
                for original_key in meta_dict:
                    if original_key in translation_table:
                        for translated_key in translation_table[original_key]:
                            export_dict[key][translated_key] = \
                                meta_dict[original_key]
                    else:
                        export_dict[key][original_key] = \
                            meta_dict[original_key]

        # Higher Order Data
        for key in meta_to_translate.ho_data:
            if key not in export_dict:
                export_dict[key] = {}
            for ho_key in meta_to_translate.ho_data[key].data.index:
                if translation_table is None:
                    export_dict[key+'_'+ho_key] = \
                        meta_to_translate.ho_data[key].data.loc[ho_key].to_dict()
                else:
                    # Translate each key if a translation is provided
                    export_dict[key+'_'+ho_key] = {}
                    meta_dict = \
                        meta_to_translate.ho_data[key].data.loc[ho_key].to_dict()
                    for original_key in meta_dict:
                        if original_key in translation_table:
                            for translated_key in translation_table[original_key]:
                                export_dict[key+'_'+ho_key][translated_key] = \
                                    meta_dict[original_key]
                        else:
                            export_dict[key+'_'+ho_key][original_key] = \
                                meta_dict[original_key]
        return export_dict

    def to_netcdf4(self, fname=None, base_instrument=None, epoch_name='Epoch',
                   zlib=False, complevel=4, shuffle=True, preserve_meta_case=False):
        """Stores loaded data into a netCDF4 file.

        Parameters
        ----------
        fname : string
            full path to save instrument object to
        base_instrument : pysat.Instrument
            used as a comparison, only attributes that are present with
            self and not on base_instrument are written to netCDF
        epoch_name : str
            Label in file for datetime index of Instrument object
        zlib : boolean
            Flag for engaging zlib compression (True - compression on)
        complevel : int
            an integer between 1 and 9 describing the level of compression
            desired (default 4). Ignored if zlib=False
        shuffle : boolean
            the HDF5 shuffle filter will be applied before compressing the data
            (default True). This significantly improves compression. Default is
            True. Ignored if zlib=False.
        preserve_meta_case : bool (False)
            if True, then the variable strings within the MetaData object, which
            preserves case, are used to name variables in the written netCDF file.
            If False, then the variable strings used to access data from the
            Instrument object are used instead. By default, the variable strings
            on both the data and metadata side are the same, though this relationship
            may be altered by a user.

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
        'Generation_Date', and 'Logical_File_ID'. These are defined within to_netCDF
        at the time the file is written, as per the adopted standard,
        SPDF ISTP/IACG Modified for NetCDF. Atrributes 'Conventions' and
        'Text_Supplement' are given default values if not present.

        """

        import netCDF4
        import pysat

        file_format = 'NETCDF4'
        # base_instrument used to define the standard attributes attached
        # to the instrument object. Any additional attributes added
        # to the main input Instrument will be written to the netCDF4
        base_instrument = Instrument() if base_instrument is None \
            else base_instrument

        # begin processing metadata for writing to the file
        # look to see if user supplied a list of export keys
        # corresponding to internally tracked metadata within pysat
        export_meta = self.generic_meta_translator(self.meta)
        if self._meta_translation_table is None:
            # didn't find a translation table, using the strings
            # attached to the supplied pysat.Instrument object
            export_name_labels = [self.name_label]
            export_units_labels = [self.units_label]
            export_desc_labels = [self.desc_label]
            export_notes_labels = [self.notes_label]
        else:
            # user supplied labels in translation table
            export_name_labels = self._meta_translation_table['name_label']
            export_units_labels = self._meta_translation_table['units_label']
            export_desc_labels = self._meta_translation_table['desc_label']
            export_notes_labels = self._meta_translation_table['notes_label']
            logger.info('Using Metadata Translation Table: ' +
                  str(self._meta_translation_table))
        # Apply instrument specific post-processing to the export_meta
        if hasattr(self._export_meta_post_processing, '__call__'):
            export_meta = self._export_meta_post_processing(export_meta)

        # check if there are multiple variables with same characters
        # but with different case
        lower_variables = [var.lower() for var in self.variables]
        unique_lower_variables = np.unique(lower_variables)
        if len(unique_lower_variables) != len(lower_variables):
            raise ValueError('There are multiple variables with the same ' +
                             'name but different case which results in a ' +
                             'loss of metadata. Please make the names unique.')

        # general process for writing data is this
        # first, take care of the EPOCH information
        # second, iterate over the variable colums in Instrument.data
        # check the type of data
        # if 1D column, do simple write (type is not an object)
        # if it is an object, then check if writing strings, if not strings,
        # then if column is a Series of Frames, write as 2D variables
        # metadata must be filtered before writing to netCDF4, string variables
        # can't have a fill value
        with netCDF4.Dataset(fname, mode='w', format=file_format) as out_data:
            # number of items, yeah
            num = len(self.index)
            # write out the datetime index
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
            new_dict = self._filter_netcdf4_metadata(new_dict, np.int64)
            # attach metadata
            cdfkey.setncatts(new_dict)

            # attach data
            cdfkey[:] = (self.index.values.astype(np.int64) *
                         1.E-6).astype(np.int64)

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
                data, coltype, datetime_flag = self._get_data_info(self[key],
                                                                   file_format)
                # operate on data based upon type
                if self[key].dtype != np.dtype('O'):
                    # not an object, normal basic 1D data
                    # print(key, coltype, file_format)

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
                        new_dict = self._filter_netcdf4_metadata(new_dict,
                                                                 coltype)
                        cdfkey.setncatts(new_dict)
                    except KeyError as err:
                        logger.info(' '.join((str(err), '\n',
                                        ', '.join(('Unable to find MetaData for',
                                                   key)))))
                    # assign data
                    if datetime_flag:
                        # datetime is in nanoseconds, storing milliseconds
                        cdfkey[:] = (data.values.astype(coltype)
                                     * 1.E-6).astype(coltype)
                    else:
                        # not datetime data, just store as is
                        cdfkey[:] = data.values.astype(coltype)

                # back to main check on type of data to write
                else:
                    # it is a Series of objects, need to figure out
                    # what the actual objects are, then act as needed

                    # use info in coltype to get real datatype of object
                    # isinstance isn't working here because of something with
                    # coltype

                    if (coltype == type(' ')) or (coltype == type(u' ')):
                        # dealing with a string
                        cdfkey = out_data.createVariable(case_key,
                                                         coltype,
                                                         dimensions=(epoch_name),
                                                         zlib=zlib,
                                                         complevel=complevel,
                                                         shuffle=shuffle)
                        # attach any meta data
                        try:
                            # attach dimension metadata
                            new_dict = export_meta[case_key]
                            new_dict['Depend_0'] = epoch_name
                            new_dict['Display_Type'] = 'Time Series'
                            new_dict['Format'] = \
                                self._get_var_type_code(coltype)
                            new_dict['Var_Type'] = 'data'
                            # no FillValue or FillVal allowed for strings
                            new_dict = self._filter_netcdf4_metadata(new_dict,
                                                                     coltype,
                                                                     remove=True)
                            # really attach metadata now
                            cdfkey.setncatts(new_dict)
                        except KeyError:
                            logger.info(', '.join(('Unable to find MetaData for',
                                             key)))

                        # time to actually write the data now
                        cdfkey[:] = data.values

                    # still dealing with an object, not just a series
                    # of strings
                    # maps to if check on coltypes being stringbased
                    else:
                        # presuming a series with a dataframe or series in each
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
                                data, coltype, _ = \
                                    self._get_data_info(idx, file_format)
                                cdfkey = \
                                    out_data.createVariable(case_key + '_' + col,
                                                            coltype,
                                                            dimensions=var_dim,
                                                            zlib=zlib,
                                                            complevel=complevel,
                                                            shuffle=shuffle)
                                # attach any meta data
                                try:
                                    new_dict = export_meta[case_key + '_' + col]
                                    new_dict['Depend_0'] = epoch_name
                                    new_dict['Depend_1'] = obj_dim_names[-1]
                                    new_dict['Display_Type'] = 'Spectrogram'
                                    new_dict['Format'] = \
                                        self._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    new_dict = \
                                        self._filter_netcdf4_metadata(new_dict,
                                                                      coltype)
                                    cdfkey.setncatts(new_dict)
                                except KeyError as err:
                                    logger.info(' '.join((str(err), '\n',
                                                    'Unable to find MetaData',
                                                    'for', ', '.join((key,
                                                                      col)))))
                                # attach data
                                # it may be slow to repeatedly call the store
                                # method as well astype method below collect
                                # data into a numpy array, then write the full
                                # array in one go
                                temp_cdf_data = \
                                    np.zeros((num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = \
                                        self[key].iloc[i][col].values
                                # write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                            else:
                                # we are dealing with a Series
                                # get information about information within
                                # series
                                idx = self[key].iloc[good_data_loc]
                                data, coltype, _ = \
                                    self._get_data_info(idx, file_format)
                                cdfkey = \
                                    out_data.createVariable(case_key + '_data',
                                                            coltype,
                                                            dimensions=var_dim,
                                                            zlib=zlib,
                                                            complevel=complevel,
                                                            shuffle=shuffle)
                                # attach any meta data
                                try:
                                    new_dict = export_meta[case_key]
                                    new_dict['Depend_0'] = epoch_name
                                    new_dict['Depend_1'] = obj_dim_names[-1]
                                    new_dict['Display_Type'] = 'Spectrogram'
                                    new_dict['Format'] = \
                                        self._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    new_dict = \
                                        self._filter_netcdf4_metadata(new_dict,
                                                                      coltype)
                                    # really attach metadata now
                                    cdfkey.setncatts(new_dict)
                                except KeyError as err:
                                    logger.info(' '.join((str(err), '\n',
                                                    'Unable to find MetaData',
                                                    'for,', key)))
                                # attach data
                                temp_cdf_data = \
                                    np.zeros((num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = self[i, key].values
                                # write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                        # we are done storing the actual data for the given
                        # higher order variable, now we need to store the index
                        # for all of that fancy data

                        # get index information
                        idx = good_data_loc
                        data, coltype, datetime_flag = \
                            self._get_data_info(self[key].iloc[idx].index,
                                                file_format)
                        # create dimension variable for to store index in
                        # netCDF4
                        cdfkey = out_data.createVariable(case_key, coltype,
                                                         dimensions=var_dim,
                                                         zlib=zlib,
                                                         complevel=complevel,
                                                         shuffle=shuffle)
                        # work with metadata
                        new_dict = export_meta[case_key]
                        new_dict['Depend_0'] = epoch_name
                        new_dict['Depend_1'] = obj_dim_names[-1]
                        new_dict['Display_Type'] = 'Time Series'
                        new_dict['Format'] = self._get_var_type_code(coltype)
                        new_dict['Var_Type'] = 'data'

                        if datetime_flag:
                            # print('datetime flag')
                            for export_name_label in export_name_labels:
                                new_dict[export_name_label] = epoch_name
                            for export_units_label in export_units_labels:
                                new_dict[export_units_label] = \
                                    'Milliseconds since 1970-1-1 00:00:00'
                            new_dict = self._filter_netcdf4_metadata(new_dict,
                                                                     coltype)
                            # set metadata dict
                            cdfkey.setncatts(new_dict)
                            # set data
                            temp_cdf_data = np.zeros((num,
                                                      dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = self[i, key].index.values
                            cdfkey[:, :] = (temp_cdf_data.astype(coltype) *
                                            1.E-6).astype(coltype)

                        else:
                            if self[key].iloc[data_loc].index.name is not None:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = \
                                        self[key].iloc[data_loc].index.name
                            else:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = key
                            new_dict = self._filter_netcdf4_metadata(new_dict,
                                                                     coltype)
                            # assign metadata dict
                            cdfkey.setncatts(new_dict)
                            # set data
                            temp_cdf_data = \
                                np.zeros((num, dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = \
                                    self[key].iloc[i].index.to_native_types()
                            cdfkey[:, :] = temp_cdf_data.astype(coltype)

            # store any non standard attributes
            # compare this Instrument's attributes to base object
            base_attrb = dir(base_instrument)
            this_attrb = dir(self)
            # filter out any 'private' attributes
            # those that start with a _
            adict = {}
            for key in this_attrb:
                if key not in base_attrb:
                    if key[0] != '_':
                        adict[key] = self.__getattribute__(key)
            # store any non-standard attributes attached to meta
            base_attrb = dir(base_instrument.meta)
            this_attrb = dir(self.meta)
            for key in this_attrb:
                if key not in base_attrb:
                    if key[0] != '_':
                        adict[key] = self.meta.__getattribute__(key)
            # Add additional metadata to conform to standards
            adict['pysat_version'] = pysat.__version__
            if 'Conventions' not in adict:
                adict['Conventions'] = 'SPDF ISTP/IACG Modified for NetCDF'
            if 'Text_Supplement' not in adict:
                adict['Text_Supplement'] = ''
            # remove any attributes with the names below
            # pysat is responible for including them in the file.
            items = ['Date_End', 'Date_Start', 'File', 'File_Date',
                     'Generation_Date', 'Logical_File_ID']
            for item in items:
                if item in adict:
                    _ = adict.pop(item)

            adict['Date_End'] = \
                pysat.datetime.strftime(self.index[-1],
                                        '%a, %d %b %Y,  ' +
                                        '%Y-%m-%dT%H:%M:%S.%f')
            adict['Date_End'] = adict['Date_End'][:-3] + ' UTC'

            adict['Date_Start'] = \
                pysat.datetime.strftime(self.index[0],
                                        '%a, %d %b %Y,  ' +
                                        '%Y-%m-%dT%H:%M:%S.%f')
            adict['Date_Start'] = adict['Date_Start'][:-3] + ' UTC'
            adict['File'] = os.path.split(fname)
            adict['File_Date'] = \
                self.index[-1].strftime('%a, %d %b %Y,  ' +
                                        '%Y-%m-%dT%H:%M:%S.%f')
            adict['File_Date'] = adict['File_Date'][:-3] + ' UTC'
            adict['Generation_Date'] = \
                pysat.datetime.utcnow().strftime('%Y%m%d')
            adict['Logical_File_ID'] = os.path.split(fname)[-1].split('.')[:-1]

            # check for binary types, convert when found
            for key in adict.keys():
                if isinstance(adict[key], bool):
                    adict[key] = int(adict[key])
            # attach attributes
            out_data.setncatts(adict)
        return

#
# ----------------------------------------------
#   Utilities supporting the Instrument Object
# ----------------------------------------------
#


def _get_supported_keywords(load_func):
    """Return a list of supported keywords

    Intended to be used on the supporting instrument
    functions that enable the general Instrument object
    to load and work with a particular data set.

    Parameters
    ----------
    load_func: Python method or functools.partial
        Method used to load data within pysat

    Returns
    -------
    list
        list of keyword argument strings


    Notes
    -----
        If the input is a partial function then the
        list of keywords returned only includes keywords
        that have not already been set as part of
        the functools.partial instantiation.

    """

    # check if partial function
    if isinstance(load_func, functools.partial):
        # get keyword arguments already applied to function
        existing_kws = load_func.keywords
        # pull out python function portion
        load_func = load_func.func
    else:
        existing_kws = None

    # modified from code on
    # https://stackoverflow.com/questions/196960/can-you-list-the-keyword-arguments-a-function-receives
    if sys.version_info.major == 2:
        args, varargs, varkw, defaults = inspect.getargspec(load_func)
    else:
        sig = inspect.getfullargspec(load_func)
        # args are first
        args = sig.args

    pop_list = []
    # account for keywords that exist for every load function
    pre_kws = ['fnames', 'sat_id', 'tag']
    # account for keywords already set since input was a partial function
    if existing_kws is not None:
        pre_kws.extend(existing_kws.keys())
    # remove pre-existing keywords from output
    # first identify locations
    for i, arg in enumerate(args):
        if arg in pre_kws:
            pop_list.append(i)
    # remove identified locations
    # go backwards so we don't mess with the location of data we
    # are trying to remove
    if len(pop_list) > 0:
        for pop in pop_list[::-1]:
            args.pop(pop)

    # *args and **kwargs are not required, so ignore them.
    return args


def _check_if_keywords_supported(func, **kwargs):
    """Checks if keywords supported by function

    Parameters
    ----------
    func: method
        Method to be checked against
    **kwargs : keyword args
        keyword arguments dictionary

    Returns
    -------
    bool
        If true, all keywords supported

    """

    # get list of supported keywords
    supp = _get_supported_keywords(func)
    # check if kwargs are in list
    for name in kwargs.keys():
        if name not in supp:
            estr = ' '.join((name, 'is not a supported keyword by pysat or',
                             'by the underlying supporting load routine.',
                             'Please double check the keyword inputs.'))
            raise ValueError(estr)
    return True
