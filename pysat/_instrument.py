# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

import string
import os
import copy
import sys
import pandas as pds
import numpy as np

from . import _custom
from . import _files
from . import _orbits
from . import _meta
from . import utils
from pysat import data_dir
from pysat import DataFrame, Series


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
    units_label : str
        label to use for units. Defaults to 'units' but some implementations
        will use mixed case 'Units'
    name_label : str
        label to use for long name. Defaults to 'long_name' but some implementations
        will use 'Long_Name'
    file_format : str or NoneType
        File naming structure in string format.  Variables such as year,
        month, and sat_id will be filled in as needed using python string
        formatting.  The default file format structure is supplied in the
        instrument list_files routine.
               
    Attributes
    ----------
    data : pandas.DataFrame
        loaded science data 
    date : pandas.datetime
        date for loaded data
    yr : int
        year for loaded data
    bounds : (datetime/filename/None, datetime/filename/None)
        bounds for loading data, supply array_like for a season with gaps
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
        cosmic = pysat.Instrument('cosmic2013', 
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
                 temporary_file_list=False, units_label='units', name_label='long_name',  
                 *arg, **kwargs):

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
                raise ValueError('Inputs platform and name must both be strings, or both None.')                        
        else:
            # user has provided a module
            try:
                # platform and name are expected to be part of module
                self.name = inst_module.name.lower()
                self.platform = inst_module.platform.lower()
            except AttributeError:
                raise AttributeError(string.join(('A name and platform attribute for the ',
                                     'instrument is required if supplying routine module directly.')))
            # look to module for instrument functions and defaults
            self._assign_funcs(inst_module=inst_module)
            
        # more reasonable defaults for optional parameters
        self.tag = tag.lower() if tag is not None else ''
        self.sat_id = sat_id.lower() if sat_id is not None else ''
        self.clean_level = (clean_level.lower() if clean_level is not None
                            else 'none')

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
        self.data = DataFrame(None)
        self.units_label = units_label
        self.name_label = name_label
        self.meta = _meta.Meta(units_label=self.units_label, name_label=self.name_label)
        
        # function processing class, processes data on load
        self.custom = _custom.Custom()
        # create arrays to store data around loaded day
        # enables padding across day breaks with minimal loads
        self._next_data = DataFrame(None)
        self._next_data_track = []
        self._prev_data = DataFrame(None)
        self._prev_data_track = []
        self._curr_data = DataFrame(None)

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
                                  write_to_disk=temporary_file_list)

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

        # store kwargs, passed to load routine
        self.kwargs = kwargs        

        # run instrument init function, a basic pass function is used
        # if user doesn't supply the init function
        self._init_rtn(self)

        # store base attributes, used in particular by Meta class
        self._base_attr = dir(self)

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

        if isinstance(key, tuple):
            # support slicing
            return self.data.ix[key[0], key[1]]
        else:
            return self.data[key]

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
        if isinstance(new, dict):
            # metadata should be included in dict
            self.data[key] = new.pop('data')
            # pass the rest to meta
            self.meta[key] = new
        else:
            if isinstance(key, tuple):
                self.data.ix[key[0], key[1]] = new
                self.meta[key[1]] = {}
            elif isinstance(key, str):
                self.data[key] = new  
                self.meta[key] = {}
            elif isinstance(new, DataFrame):
                self.data[key] = new[key]
                for ke in key:
                    self.meta[ke] = {}
            else:
                raise ValueError("No support for supplied input key")

    @property
    def empty(self):
        """Boolean flag reflecting lack of data.
        
        True if there is no Instrument data."""
        return self.data.empty

    def copy(self):
        """Deep copy of the entire Instrument object."""
        return copy.deepcopy(self)
    
    def _pass_func(*args, **kwargs):
        pass     

    def _assign_funcs(self, by_name=False, inst_module=None):        
        """Assign all external science instrument methods to Instrument object."""
        import importlib
        # set defaults
        self._list_rtn = self._pass_func
        self._load_rtn = self._pass_func
        self._default_rtn = self._pass_func
        self._clean_rtn = self._pass_func
        self._init_rtn = self._pass_func
        self._download_rtn = self._pass_func
        # default params
        self.directory_format = None
        self.file_format = None
        self.multi_file_day = False
        self.orbit_info = None
                        
        if by_name: 
            # look for code with filename name, any errors passed up
            inst = importlib.import_module(''.join(('.', self.platform, '_',
                                           self.name)), package='pysat.instruments')
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
        except AttributeError:
            estr = 'A load, file_list, and download routine are required for '
            raise AttributeError('{:s}every instrument.'.format(estr))
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

        # look for instrument default parameters
        try:
            self.directory_format = inst.directory_format
        except AttributeError:
            pass
        try:
            self.multi_file_day = inst.self.multi_file_day
        except AttributeError:
            pass
        try:
            self.orbit_info = inst.orbit_info
        except AttributeError:
            pass

        return

    def __repr__(self):

        output_str = '\npysat Instrument object\n'
        output_str += '-----------------------\n'
        output_str += 'Platform: '+self.platform+'\n'
        output_str += 'Name: '+self.name+'\n'
        output_str += 'Tag: '+self.tag+'\n'
        output_str += 'Satellite id: '+self.sat_id+'\n'

        output_str += '\nData Processing\n'
        output_str += '---------------\n'
        output_str += 'Cleaning Level: ' + self.clean_level + '\n'
        output_str += 'Data Padding: ' + self.pad.__repr__() + '\n'
        output_str += 'Keyword Arguments Passed to load(): ' + self.kwargs.__repr__() +'\n'
        output_str += 'Custom Functions : \n'
        if len(self.custom._functions) > 0:
            for func in self.custom._functions:
                output_str += '    ' + func.__repr__()
        else:
            output_str += '    ' + 'No functions applied.\n'

        output_str += '\nOrbit Settings' + '\n'
        output_str += '--------------' + '\n'
        if self.orbit_info is None:
            output_str += 'Orbit properties not set.\n'
        else:
            output_str += 'Orbit Kind: ' + self.orbit_info['kind'] + '\n'
            output_str += 'Orbit Index: ' + self.orbit_info['index'] + '\n'
            output_str += 'Orbit Period: ' + self.orbit_info['period'].__str__() + '\n'
            output_str += 'Number of Orbits: {:d}'.format(self.orbits.num) + '\n'
            output_str += 'Loaded Orbit Number: {:d}'.format(self.orbits.current) + '\n'

        output_str += '\nLocal File Statistics' + '\n'
        output_str += '---------------------' + '\n'
        output_str += 'Number of files: ' + str(len(self.files.files)) + '\n'
        output_str += 'Date Range: '+self.files.files.index[0].strftime('%m/%d/%Y')
        output_str += ' --- ' + self.files.files.index[-1].strftime('%m/%d/%Y') + '\n'

        output_str += '\nLoaded Data Statistics'+'\n'
        output_str += '----------------------'+'\n'
        if not self.empty:
            # if self._fid is not None:
            #     output_str += 'Filename: ' +
            output_str += 'Date: ' + self.date.strftime('%m/%d/%Y') + '\n'
            output_str += 'DOY: {:03d}'.format(self.doy) + '\n'
            output_str += 'Time range: ' + self.data.index[0].strftime('%m/%d/%Y %H:%M:%S') + ' --- '
            output_str += self.data.index[-1].strftime('%m/%d/%Y %H:%M:%S')+'\n'
            output_str += 'Number of Times: ' + str(len(self.data.index)) + '\n'
            output_str += 'Number of variables: ' + str(len(self.data.columns)) + '\n'

            output_str += '\nVariable Names:'+'\n'
            num = len(self.data.columns)//3
            for i in np.arange(num):
                output_str += self.data.columns[3 * i].ljust(30)
                output_str += self.data.columns[3 * i + 1].ljust(30)
                output_str += self.data.columns[3 * i + 2].ljust(30)+'\n'
            for i in np.arange(len(self.data.columns) - 3 * num):
                output_str += self.data.columns[i+3*num].ljust(30)
            output_str += '\n'
        else:
            output_str += 'No loaded data.'+'\n'
        output_str += '\n'

        return output_str

    def _load_data(self, date=None, fid=None):
        """
        Load data for an instrument on given date or fid, dependng upon input.
        
        """

        if fid is not None:
            # get filename based off of index value
            fname = self.files[fid:fid+1]
        elif date is not None:
            fname = self.files[date: date+pds.DateOffset(days=1)]
        else:
            raise ValueError('Must supply either a date or file id number.')
   
        if len(fname) > 0:    
            load_fname = [os.path.join(self.files.data_path, f) for f in fname]
            data, mdata = self._load_rtn(load_fname, tag=self.tag,
                                         sat_id=self.sat_id, **self.kwargs)
        else:
            data = DataFrame(None)
            mdata = _meta.Meta(units_label=self.units_label, name_label=self.name_label)

        output_str = '{platform} {name} {tag} {sat_id}'
        output_str = output_str.format(platform=self.platform,
                                       name=self.name, tag=self.tag, 
                                       sat_id=self.sat_id)
        if not data.empty: 
            if not isinstance(data, DataFrame):
                raise TypeError(' '.join(('Data returned by instrument load',
                                'routine must be a pandas.DataFrame')))
            if not isinstance(mdata, _meta.Meta):
                raise TypeError('Metadata returned must be a pysat.Meta object')
            if date is not None:
                output_str = ' '.join(('Returning', output_str, 'data for', date.strftime('%D')))
            else:
                if len(fname) == 1:
                    # this check was zero
                    output_str = ' '.join(('Returning', output_str, 'data from', fname[0]))
                else:
                    output_str = ' '.join(('Returning', output_str, 'data from', fname[0], '::', fname[-1]))
        else:
            # no data signal
            output_str = ' '.join(('No', output_str, 'data for', date.strftime('%D')))
        # remove extra spaces, if any
        output_str = " ".join(output_str.split())
        print (output_str)                
        return data, mdata
        
    def _load_next(self):
        """Load the next days data (or file) without incrementing the date.
        Repeated calls will not advance date/file and will produce the same data
        
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
        Repeated calls will not decrement date/file and will produce the same data
        
        Uses info stored in object to either decrement the date, 
        or the file. Looks for self._load_by_date flag.  
        
        """

        if self._load_by_date:
            prev_date = self.date - pds.DateOffset(days=1)
            return self._load_data(date=prev_date)
        else:
            return self._load_data(fid=self._fid-1)

    def _set_load_parameters(self, date=None, fid=None):
        self.date = date
        self._fid = fid
        if date is not None:
            year, doy = utils.getyrdoy(date)
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
            self._set_load_parameters(date=date, fid=None)
            # increment 
            inc = pds.DateOffset(days=1)
            curr = date
        elif (yr is not None) & (doy is not None):
            date = pds.datetime(yr, 1, 1) + pds.DateOffset(days=(doy-1))
            self._set_load_parameters(date=date, fid=None)
            # increment 
            inc = pds.DateOffset(days=1)
            curr = self.date
        elif fname is not None:
            # date will have to be set later by looking at the data
            self._set_load_parameters(date=None, fid=self.files.get_index(fname))
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
        loop_pad = self.pad if self.pad is not None else pds.DateOffset(seconds=0)   
        if (self.pad is not None) | self.multi_file_day:
            if self._next_data.empty & self._prev_data.empty:
                # data has not already been loaded for previous and next days
                # load data for all three
                print('Initializing three day/file window')
                # using current date or fid
                self._prev_data, self._prev_meta = self._load_prev()
                self._curr_data, self._curr_meta = \
                    self._load_data(date=self.date, fid=self._fid)
                self._next_data, self._next_meta = self._load_next()
            else:
                # moving forward in time
                if self._next_data_track == curr:
                    self._prev_data = self._curr_data
                    self._prev_meta = self._curr_meta
                    self._curr_data = self._next_data
                    self._curr_meta = self._next_meta
                    self._next_data, self._next_meta = self._load_next()
                # moving backward in time
                elif self._prev_data_track == curr:
                    self._next_data = self._curr_data
                    self._next_meta = self._curr_meta
                    self._curr_data = self._prev_data
                    self._curr_meta = self._prev_meta
                    self._prev_data, self._prev_meta = self._load_prev()
                # jumped in time/or switched from filebased to date based access
                else:
                    self._prev_data, self._prev_meta = self._load_prev()
                    self._curr_data, self._curr_meta = \
                                self._load_data(date=self.date, fid=self._fid)
                    self._next_data, self._next_meta = self._load_next()

            # make sure datetime indices for all data is monotonic
            if not self._prev_data.index.is_monotonic_increasing:
                self._prev_data.sort_index(inplace=True)
            if not self._curr_data.index.is_monotonic_increasing:
                self._curr_data.sort_index(inplace=True)
            if not self._next_data.index.is_monotonic_increasing:
                self._next_data.sort_index(inplace=True)
                
            # make tracking indexes consistent with new loads
            self._next_data_track = curr + inc
            self._prev_data_track = curr - inc
            # attach data to object
            if not self._curr_data.empty:
                self.data = self._curr_data.copy()
                self.meta = self._curr_meta.copy()
            else:
                self.data = DataFrame(None)
                # line below removed as it would delete previous meta, if any
                # if you end a seasonal analysis with a day with no data, then
                # no meta: self.meta = _meta.Meta()
            
            # multi file days can extend past a single day, only want data from 
            # specific date if loading by day
            # set up times for the possible data padding coming up
            if self._load_by_date:
                #print ('double trouble')
                first_time = self.date 
                first_pad = self.date - loop_pad
                last_time = self.date + pds.DateOffset(days=1) 
                last_pad = self.date + pds.DateOffset(days=1) + loop_pad
                want_last_pad = False
            # loading by file, can't be a multi_file-day flag situation
            elif (not self._load_by_date) and (not self.multi_file_day):
                #print ('single trouble')
                first_time = self._curr_data.index[0]
                first_pad = first_time - loop_pad
                last_time = self._curr_data.index[-1]
                last_pad = last_time + loop_pad
                want_last_pad = True
            else:
                raise ValueError("multi_file_day and loading by date are effectively equivalent."+ 
                                "Can't have multi_file_day and load by file.")
            #print (first_pad, first_time, last_time, last_pad)

            # pad data based upon passed parameter
            if (not self._prev_data.empty) & (not self.data.empty):
                padLeft = self._prev_data.loc[first_pad : self.data.index[0]]
                if len(padLeft) > 0:
                    if (padLeft.index[-1] == self.data.index[0]) :
                        padLeft = padLeft.iloc[:-1, :]
                    self.data = pds.concat([padLeft, self.data])

            if (not self._next_data.empty) & (not self.data.empty):
                padRight = self._next_data.loc[self.data.index[-1] : last_pad]
                if len(padRight) > 0:
                    if (padRight.index[0] == self.data.index[-1]) :
                        padRight = padRight.iloc[1:, :]
                    self.data = pds.concat([self.data, padRight])
                    
            self.data = self.data.ix[first_pad : last_pad]
            # want exclusive end slicing behavior from above
            if not self.empty:
                if (self.data.index[-1] == last_pad) & (not want_last_pad):
                    self.data = self.data.iloc[:-1, :]
   
            ## drop any possible duplicate index times
            ##self.data.drop_duplicates(inplace=True)
            #self.data = self.data[~self.data.index.duplicated()]
            
        # if self.pad is False, load single day
        else:
            self.data, meta = self._load_data(date=self.date, fid=self._fid) 
            if not self.data.empty:
                self.meta = meta   
               
        # check if load routine actually returns meta
        if self.meta.data.empty:
            self.meta[self.data.columns] = {self.name_label: self.data.columns,
                                            self.units_label: ['']*len(self.data.columns)}
        # if loading by file set the yr, doy, and date
        if not self._load_by_date:
            if self.pad is not None:
                temp = first_time
            else:
                temp = self.data.index[0]
            self.date = pds.datetime(temp.year, temp.month, temp.day)
            self.yr, self.doy = utils.getyrdoy(self.date)

        if not self.data.empty:
            self._default_rtn(self)
        # clean
        if (not self.data.empty) & (self.clean_level != 'none'):
            self._clean_rtn(self)   
        # apply custom functions
        if not self.data.empty:
            self.custom._apply_all(self)
            
        # remove the excess padding, if any applied
        if (self.pad is not None) & (not self.data.empty) & (not verifyPad):
            self.data = self.data[first_time : last_time]
            if (self.data.index[-1] == last_time) & (not want_last_pad):
                self.data = self.data.iloc[:-1, :]

        # transfer any extra attributes in meta to the Instrument object
        self.meta.transfer_attributes_to_instrument(self)
        sys.stdout.flush()
        return

    def download(self, start, stop, freq='D', user=None, password=None):
        """Download data for given Instrument object from start to stop.
        
        Parameters
        ----------
        start : pandas.datetime
            start date to download data
        stop : pandas.datetime
            stop date to download data
        freq : string
            Stepsize between dates for season, 'D' for daily, 'M' monthly 
            (see pandas)
        user : string
            username, if required by instrument data archive
        password : string
            password, if required by instrument data archive
            
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
        print('Downloading data to: ', self.files.data_path)
        date_array = utils.season_date_range(start, stop, freq=freq)
        if user is None:
            self._download_rtn(date_array,
                               tag=self.tag,
                               sat_id=self.sat_id,
                               data_path=self.files.data_path)
        else:
            self._download_rtn(date_array,
                               tag=self.tag,
                               sat_id=self.sat_id,
                               data_path=self.files.data_path,
                               user=user,
                               password=password)
        # get current file date range
        first_date = self.files.start_date
        last_date = self.files.stop_date
            
        print('Updating pysat file list')
        self.files.refresh()

        # if instrument object has default bounds, update them
        if len(self.bounds[0]) == 1:
            if(self.bounds[0][0] == first_date and
               self.bounds[1][0] == last_date):
                print('Updating instrument object bounds.')
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
        Both start and stop must be the same type (date, or filename) or None

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
            # default do daily
            step = 'D'

        if (start is None) and (end is None):
            # set default
            self._iter_start = [self.files.start_date]
            self._iter_stop = [self.files.stop_date]
            self._iter_type = 'date'
            if self._iter_start[0] is not None:
                # check here in case Instrument is initialized with no input
                self._iter_list = utils.season_date_range(self._iter_start, self._iter_stop, freq=step)
                
        elif (hasattr(start, '__iter__') and not isinstance(start,str)) and (hasattr(end, '__iter__') and not isinstance(end,str)):
            base = type(start[0])
            for s, t in zip(start, end):
                if (type(s) != type(t)) or (type(s) != base):
                    raise ValueError('Start and end items must all be of the same type')
            if isinstance(start[0], str):
                self._iter_type = 'file'
                self._iter_list = self.files.get_file_array(start, end)
            elif isinstance(start[0], pds.datetime):
                self._iter_type = 'date'
                self._iter_list = utils.season_date_range(start, end, freq=step)
            else:
                raise ValueError('Input is not a known type, string or datetime')
            self._iter_start = start
            self._iter_stop = end
            
        elif (hasattr(start, '__iter__') and not isinstance(start,str)) or (hasattr(end, '__iter__') and not isinstance(end,str)):
            raise ValueError('Both start and end must be iterable if one bound is iterable')

        elif isinstance(start, str) or isinstance(end, str):
            if isinstance(start, pds.datetime) or isinstance(end, pds.datetime):
                raise ValueError('Not allowed to mix file and date bounds')
            if start is None:
                start = self.files[0]
            if end is None:
                end = self.files.files[-1]
            self._iter_start = [start]
            self._iter_stop = [end]
            self._iter_list = self.files.get_file_array(self._iter_start, self._iter_stop)
            self._iter_type = 'file'

        elif isinstance(start, pds.datetime) or isinstance(end, pds.datetime):
            if start is None:
                start = self.files.start_date
            if end is None:
                end = self.files.stop_date
            self._iter_start = [start]
            self._iter_stop = [end]
            self._iter_list = utils.season_date_range(start, end, freq=step)
            self._iter_type = 'date'
        else:
            raise ValueError('Provided an invalid combination of bounds. ' +
                             'if specifying by file, both bounds must be by file. Other ' +
                             'combinations of datetime objects and None are allowed.')

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
                if (len(idx) == 0) | (idx+1 >= len(self._iter_list)):
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    idx += 1
                    self.load(date=self._iter_list[idx[0]], verifyPad=verifyPad)
            else:
                self.load(date=self._iter_list[0], verifyPad=verifyPad)

        elif self._iter_type == 'file':
            if self._fid is not None:
                first = self.files.get_index(self._iter_list[0])
                last = self.files.get_index(self._iter_list[-1])
                if (self._fid < first) | (self._fid+1 > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    self.load(fname=self._iter_list[self._fid+1-first], verifyPad=verifyPad)
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
                if (len(idx) == 0) | (idx-1 < 0):
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    idx -= 1
                    self.load(date=self._iter_list[idx[0]], verifyPad=verifyPad)
            else:
                self.load(date=self._iter_list[-1], verifyPad=verifyPad)

        elif self._iter_type == 'file':
            if self._fid is not None:
                first = self.files.get_index(self._iter_list[0])
                last = self.files.get_index(self._iter_list[-1])
                if (self._fid-1 < first) | (self._fid > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    self.load(fname=self._iter_list[self._fid-1-first], verifyPad=verifyPad)
            else:
                self.load(fname=self._iter_list[-1], verifyPad=verifyPad)

    def _get_data_info(self, data, file_format):
        """Support file writing by determiniing data type and other options

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
            # iterate over elements until we hit something that is something, and not NaN
            data_type = type(data.iloc[0])
            for i in np.arange(len(data)):
                if len(data.iloc[i]) > 0:
                    data_type = type(data.iloc[i])
                    if not isinstance(data_type, np.float):
                        break
            datetime_flag = False
            
                
        
        return data, data_type, datetime_flag

    def to_netcdf4(self, fname=None, base_instrument=None, epoch_name='epoch', zlib=False):
        """Stores loaded data into a netCDF3/4 file.
        
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
        
        Note
        ----

        Stores 1-D data along dimension 'epoch' - the date time index.
        
        Stores object data (e.g. dataframes within series) separately
                    
         - The name of the series is used to prepend extra variable
           dimensions within netCDF, key_2, key_3; first dimension time
         - The index organizing the data stored as key_sample_index
         - from_netcdf3 uses this naming scheme to reconstruct data structure
            
        The datetime index is stored as 'UNIX time'. netCDF-3 doesn't support
        64-bit integers so it is stored as a 64-bit float. This results in a
        loss of datetime precision when converted back to datetime index
        up to hundreds of nanoseconds. Use netCDF4 if this is a problem.
          
        All attributes attached to instrument meta are written to netCDF attrs.
        
        """
        
        import netCDF4
        import pysat

        file_format = 'NETCDF4'

        base_instrument = Instrument() if base_instrument is None else base_instrument
        with netCDF4.Dataset(fname, mode='w', format=file_format) as out_data:

            num = len(self.data.index)
            out_data.createDimension(epoch_name, num)
            
            # write out the datetime index
            if file_format == 'NETCDF4':
                cdfkey = out_data.createVariable(epoch_name, 'i8', dimensions=(epoch_name),
                                                 zlib=zlib) #, chunksizes=1)
                cdfkey.units = 'Milliseconds since 1970-1-1 00:00:00'
                cdfkey[:] = (self.data.index.values.astype(np.int64)*1.E-6).astype(np.int64)
            else:
                # can't store full time resolution
                cdfkey = out_data.createVariable(epoch_name, 'f8', dimensions=(epoch_name),
                                                 zlib=zlib) #, chunksizes=1)
                cdfkey.units = 'Milliseconds since 1970-1-1 00:00:00'
                cdfkey[:] = (self.data.index.values.astype(int)*1.E-6).astype(np.float)
    
            cdfkey.long_name = 'UNIX time'
            cdfkey.calendar = 'standard'
                            
            # store all of the data in dataframe columns
            for key in self.data.columns:
                # get information on data
                data, coltype, datetime_flag = self._get_data_info(self[key], file_format)
                # operate on data based upon type
                if self[key].dtype != np.dtype('O'):
                    # not an object, normal basic data
                    # print(key, coltype, file_format)
                    cdfkey = out_data.createVariable(key,
                                                     coltype,
                                                     dimensions=(epoch_name),
                                                     zlib=zlib) #, chunksizes=1)
                    # attach any meta data
                    try:
                        new_dict = self.meta[key].to_dict()
                        if u'_FillValue' in new_dict.keys():
                            # make sure _FillValue is the same type as the data
                            new_dict['_FillValue'] = np.array(new_dict['_FillValue']).astype(coltype)
                        if u'FillVal' in new_dict.keys():
                            # make sure _FillValue is the same type as the data
                            new_dict['FillVal'] = np.array(new_dict['FillVal']).astype(coltype)
                        # really attach metadata now
                        cdfkey.setncatts(new_dict)
                    except KeyError:
                        print(', '.join(('Unable to find MetaData for', key)))
                    # assign data
                    if datetime_flag:
                        if file_format == 'NETCDF4':
                            cdfkey[:] = (data.values.astype(coltype) * 1.E-6).astype(coltype)
                        else:
                            cdfkey[:] = (data.values.astype(coltype) * 1.E-6).astype(coltype)
                    else:
                        cdfkey[:] = data.values.astype(coltype)
                else:
                    # it is an object
                    # use info in coltype to get real datatype
                    if (coltype == type(' ')) or (coltype == type(u' ')):
                        # dealing with a string
                        cdfkey = out_data.createVariable(key,
                                                         coltype,
                                                         dimensions=(epoch_name),
                                                         zlib=zlib) #, chunksizes=1)
                        # attach any meta data
                        try:
                            new_dict = self.meta[key].to_dict()
                            # no FillValue or FillVal allowed for strings
                            if u'_FillValue' in new_dict.keys():
                                new_dict.pop(u'_FillValue')
                            if u'FillVal' in new_dict.keys():
                                new_dict.pop(u'FillVal')
                            # really attach metadata now
                            cdfkey.setncatts(new_dict)
                        except KeyError:
                            print(', '.join(('Unable to find MetaData for', key)))
                        cdfkey[:] = data.values

                    else:
                        # we are dealing with a more complicated object
                        # presuming a series with a dataframe in each location
                        dims = np.shape(self[key].iloc[0])
                        obj_dim_names = []

                        for i, dim in enumerate(dims[:-1]):
                            # don't need to go over last dimension value,
                            # it covers number of columns
                            obj_dim_names.append(key+'_dimension_%i' % (i+1))
                            out_data.createDimension(obj_dim_names[-1], dim)
                        # total dimensions stored for object are epoch plus ones just above
                        var_dim = tuple([epoch_name]+obj_dim_names)
                        # iterate over columns and store
                        try:
                            iterable = self[key].iloc[0].columns
                            is_frame = True
                        except AttributeError:
                            # looking at a series, which doesn't have columns
                            iterable = self[key].iloc[0].name
                            is_frame = False

                        # find location that has data
                        data_loc = 0
                        for jjj in np.arange(len(self.data)):
                            if len(self.data[key].iloc[0]) > 0:
                                data_loc = jjj
                                break

                        for col in iterable:
                            if is_frame:
                                data, coltype, _ = self._get_data_info(self[key].iloc[data_loc][col], file_format)
                            else:
                                data, coltype, _ = self._get_data_info(self[key].iloc[data_loc], file_format)
                            cdfkey = out_data.createVariable(key + '_' + col,
                                                             coltype,
                                                             dimensions=var_dim,
                                                             zlib=zlib) #, chunksizes=1)
                            if is_frame:
                                # attach any meta data
                                try:
                                    # print('Frame Writing ', key, col, self.meta[key][col])
                                    new_dict = self.meta[key][col].to_dict()
                                    if u'_FillValue' in new_dict.keys():
                                        # make sure _FillValue is the same type as the data
                                        new_dict['_FillValue'] = np.array(new_dict['_FillValue']).astype(coltype)
                                    if u'FillVal' in new_dict.keys():
                                        # make sure _FillValue is the same type as the data
                                        new_dict['FillVal'] = np.array(new_dict['FillVal']).astype(coltype)
                                    cdfkey.setncatts(new_dict)

                                except KeyError:
                                    print(', '.join(('Unable to find MetaData for', key, col)) )
                                # attach data
                                # it may be slow to repeatedly call the store method as well astype method below
                                # collect data into a numpy array, then write the full array in one go
                                # print(coltype, dims)
                                temp_cdf_data = np.zeros((num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = self[key].iloc[i][col].values
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)
                                # for i in range(num):
                                #     cdfkey[i, :] = self[key].iloc[i][col].values.astype(coltype)
                            else:
                                # attach any meta data
                                try:
                                    new_dict = self.meta[key].to_dict()
                                    if u'_FillValue' in new_dict.keys():
                                        # make sure _FillValue is the same type as the data
                                        new_dict['_FillValue'] = np.array(new_dict['_FillValue']).astype(coltype)
                                    if u'FillVal' in new_dict.keys():
                                        # make sure _FillValue is the same type as the data
                                        new_dict['FillVal'] = np.array(new_dict['FillVal']).astype(coltype)
                                    # really attach metadata now
                                    cdfkey.setncatts(new_dict)
                                except KeyError:
                                    print(', '.join(('Unable to find MetaData for', key)))
                                # cdfkey.setncatts(self.meta[key].to_dict())

                                # # attach data
                                # for i in range(num):
                                #     cdfkey[i, :] = self[key].iloc[i].values.astype(coltype)
                                temp_cdf_data = np.zeros((num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = self[key].iloc[i].values#.astype(coltype)
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)
                        # store the dataframe index for each time of main dataframe
                        data, coltype, datetime_flag = self._get_data_info(self[key].iloc[data_loc].index, file_format)
                        cdfkey = out_data.createVariable(key+'_dimension_1',
                                                         coltype, dimensions=var_dim,
                                                         zlib=zlib) #, chunksizes=1)
                        if datetime_flag:
                            #print('datetime flag')
                            if file_format == 'NETCDF4':
                                cdfkey.units = 'Milliseconds since 1970-1-1 00:00:00'
                                for i in range(num):
                                    cdfkey[i, :] = (self[key].iloc[i].index.values.astype(coltype)*1.E-6).astype(coltype)
                            else:
                                cdfkey.units = 'Milliseconds since 1970-1-1 00:00:00'
                                for i in range(num):
                                    cdfkey[i, :] = (self[key].iloc[i].index.values.astype(coltype)*1.E-6).astype(coltype)

                            cdfkey.long_name = 'UNIX time'
                        else:
                            #cdfkey.units = ''
                            if self[key].iloc[data_loc].index.name is not None:
                                cdfkey.long_name = self[key].iloc[data_loc].index.name
                            else:
                                cdfkey.long_name = key
                            for i in range(num):
                                cdfkey[i, :] = self[key].iloc[i].index.to_native_types()

            # store any non standard attributes
            base_attrb = dir(base_instrument)
            this_attrb = dir(self)
            
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
            adict['pysat_version'] = pysat.__version__
            adict['Conventions'] = 'CF-1.6'

            # check for binary types
            for key in adict.keys():
                if isinstance(adict[key], bool):
                    adict[key] = int(adict[key])
            # print('adict', adict)

            out_data.setncatts(adict)
        return
