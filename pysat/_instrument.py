# -*- coding: utf-8 -*-
import string
import os
import copy
import sys
import pandas as pds
import numpy as np

import _custom
import _files
import _orbits
import _meta
import utils
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
    inst_module : module, optional
        Provide instrument module directly. 
        Takes precedence over platform/name.
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
    update_files : boolean, optional
        If True, query filesystem for instrument files and store. 
        files.get_new() will return no files after this call until 
        additional files are added.
    multi_file_day : boolean, optional (False by default)
        Set to True if Instrument data files for a day are spread across
        multiple files and data for day n could be found in a file
        with a timestamp of day n-1 or n+1.
        
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
        print vefi['dB_mer']
        print vefi.meta['db_mer']
    
        # 1-second thermal plasma parameters
        ivm = pysat.Instrument(platform='cnofs', 
                                name='ivm', 
                                tag='', 
                                clean_level='clean')
        ivm.download(start,stop)
        ivm.load(2009,1)
        print ivm['ionVelmeridional'] 
        
        # Ionosphere profiles from GPS occultation
        cosmic = pysat.Instrument('cosmic2013', 
                                    'gps', 
                                    'ionprf', 
                                    altitude_bin=3)
        # bins profile using 3 km step
        cosmic.download(start, stop, user=user, password=password)
        cosmic.load(date=start)

    """

    def __init__(self, platform=None, name=None, tag=None, clean_level='clean',
                 update_files=False, pad=None, orbit_info=None,
                 inst_module=None, multi_file_day=False, *arg, **kwargs):

        if inst_module is None:
            if isinstance(platform, str) and isinstance(name, str):              
                self.platform = platform.lower() 
                self.name = name.lower() 
                self._assign_funcs(by_name=True)
            elif (platform is None) and (name is None):
                # creating "empty" Instrument object with this path
                self.name = ''
                self.platform = ''
                self._assign_funcs()                
            else:
                raise ValueError('Inputs platform and name must both be strings, or both None.')                        
        else:
            # user expected to have provided module
            try:
                self.name = inst_module.name.lower()
                self.platform = inst_module.platform.lower()
            except AttributeError:
                raise AttributeError(string.join(('A name and platform attribute for the ',
                                     'instrument is required if supplying routine module directly.')))
            self._assign_funcs(inst_module=inst_module)
            
        self.tag = tag.lower() if tag is not None else ''    
        self.clean_level = clean_level.lower() if clean_level is not None else 'none'

        self.data = DataFrame(None)
        self.meta = _meta.Meta()
        # function processing class, processes data on load
        self.custom = _custom.Custom()
        # create arrays to store data around loaded day
        # enables padding across day breaks with minimal loads
        self._next_data = DataFrame(None)
        self._next_data_track = []
        self._prev_data = DataFrame(None)
        self._prev_data_track = []
        self._curr_data = DataFrame(None)
        
        # arguments for padding
        if isinstance(pad, pds.DateOffset):
            self.pad = pad
        elif isinstance(pad, dict):
            self.pad = pds.DateOffset(**pad)
        elif pad is None:
            self.pad = None
        else:
            raise ValueError('pad must be a dictionary or a pandas.DateOffset instance.')

        # multi file day
        self.multi_file_day = multi_file_day

        self.kwargs = kwargs

        # load file list function, which returns dict of files
        # as well as data start and end dates
        self.files = _files.Files(self)
        if update_files:
            self.files.refresh(store=True)
        # set bounds for iteration based upon data properties
        # setting (None,None) loads default bounds
        self.bounds = (None, None)
        self.date = None
        self._fid = None
        self.yr = None
        self.doy = None
        self._load_by_date = False

        # initialize orbit support
        if orbit_info is None:
            orbit_info = {'index': None, 'kind': None, 'period': None}
        self.orbits = _orbits.Orbits(self, **orbit_info)
        # run instrument init function, a basic pass function is used
        # if user doesn't supply the init function
        self._init_rtn(self)

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
                if key[1] not in self.meta.data.index:
                    self.meta[key[1]] = {'long_name': key, 'units': ''}
            elif isinstance(key, str):
                self.data[key] = new  
                if key not in self.meta.data.index:   
                    # add in default metadata because none was supplied
                    self.meta[key] = {'long_name': key, 'units': ''}
            elif isinstance(new, DataFrame):
                self.data[key] = new[key]
                for ke in key:
                    if ke not in self.meta.data.index:   
                        # add in default metadata because none was supplied
                        self.meta[ke] = {'long_name': ke, 'units': ''}
            else:
                raise ValueError("No support for supplied input key")           
    
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
            raise AttributeError(string.join(('A load, file_list, and download routine',
                                 'are required for every instrument.')))
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

        return

    def _load_data(self, date=None, fid=None):
        """
        Load data for an instrument on given date or fid, dependng upon input.
        
        """

        if fid is not None:
            # get filename based off of index value
            # remove direct access of data
            fname = self.files[fid]
        elif date is not None:
            fname = self.files[date: date+pds.DateOffset(days=1)]
        else:
            raise ValueError('Must supply either a date or file id number.')
   
        if len(fname) > 0:    
            load_fname = [os.path.join(self.files.data_path, f) for f in fname]
            data, mdata = self._load_rtn(load_fname, tag=self.tag, **self.kwargs)
        else:
            data = DataFrame(None)
            mdata = _meta.Meta()

        if not data.empty: 
            if not isinstance(data, DataFrame):
                raise TypeError(string.join(('Data returned by instrument load',
                                'routine must be a pandas.DataFrame')))
            if not isinstance(mdata, _meta.Meta):
                raise TypeError('Metadata returned must be a pysat.Meta object')
            if date is not None:
                print string.join(('Returning', self.platform, self.name, self.tag, 'data for',
                                   date.strftime('%D')))
            else:
                if len(fname) == 1:
                    # this check was zero
                    print string.join(('Returning', self.platform, self.name, self.tag,
                                       'data from', fname[0]))
                else:
                    print string.join(('Returning', self.platform, self.name, self.tag,
                                       'data from', fname[0], '::', fname[-1]))
        else:
            # no data signal
            print string.join(('No', self.platform, self.name, self.tag, 'data for',
                               date.strftime('%D')))
    
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

        Note
        ----
        Loads data for a chosen instrument into .data. Any functions chosen
        by the user and added to the custom processing queue (.custom.add)
        are automatically applied to the data before it is available to 
        user in .data.
        
        """

        if date is not None:
            # date supplied getyrdoy checks if it is datetime
            year, doy = utils.getyrdoy(date)
            self.yr = year 
            self.doy = doy 
            self.date = date
            self._fid = None
            self._load_by_date = True
            inc = pds.DateOffset(days=1)
            curr = date
        elif (yr is not None) & (doy is not None):
            # if date not defined but both yr and doy are
            self.date = pds.datetime(yr,1,1) + pds.DateOffset(days=(doy-1))
            self.yr = yr
            self.doy = doy
            self._fid = None
            self._load_by_date = True
            inc = pds.DateOffset(days=1)
            curr = self.date
        elif fname is not None:
            # date will have to be set later by looking at the data
            self.date = None
            self.yr = None
            self.doy = None
            self._load_by_date = False
            # if no index, called func tries to find file in instrument dir,
            # throws IOError if it fails
            self._fid = self.files.get_index(fname)
            inc = 1
            curr = self._fid.copy()
        elif fid is not None:
            self._load_by_date = False	    
            self._fid = fid
            self.date = None
            self.yr = None
            self.doy = None
            inc = 1
            curr = fid
        else:
            raise TypeError('Must supply a yr,doy pair, or datetime object, ' +
                            'or filename to load data from.')

        self.orbits._reset()
        # if pad is true, need to have a three day/file load
        if (self.pad is not None) | self.multi_file_day:
            if self._next_data.empty & self._prev_data.empty:
                # data has not already been loaded for previous and next days
                # load data for all three
                print 'Initializing three day/file window'
                # using current date or fid
                self._prev_data, self._prev_meta = self._load_prev()
                self._curr_data, self._curr_meta = self._load_data(date=self.date, fid=self._fid)
                self._next_data, self._next_meta = self._load_next()
            else:
                # moving forward in time
                if self._next_data_track == curr:
                    self._prev_data, self._prev_meta = self._curr_data, self._curr_meta
                    self._curr_data, self._curr_meta = self._next_data, self._next_meta
                    self._next_data, self._next_meta = self._load_next()
                # moving backward in time
                elif self._prev_data_track == curr:
                    self._next_data, self._next_meta = self._curr_data, self._curr_meta
                    self._curr_data, self._curr_meta = self._prev_data, self._prev_meta
                    self._prev_data, self._prev_meta = self._load_prev()
                # jumped in time/or switched from filebased to date based access
                else:
                    self._prev_data, self._prev_meta = self._load_prev()
                    self._curr_data, self._curr_meta = self._load_data(date=self.date, fid=self._fid)   
                    self._next_data, self._next_meta = self._load_next()

            # make tracking indexes consistent with new loads
            self._next_data_track = curr + inc
            self._prev_data_track = curr - inc
            # attach data to object
            if not self._curr_data.empty :
                self.data = self._curr_data.copy()
                self.meta = self._curr_meta.copy()
            else:
                self.data = DataFrame(None)
                # line below removed as it would delete previous meta, if any
                # if you end a seasonal analysis with a day with no data, then no meta
                # self.meta = _meta.Meta()

            if self.multi_file_day:
                self.data = self.data[self.date : self.date+pds.DateOffset(hours=23, minutes=59, seconds=59, nanoseconds=99999999)]
            # pad data based upon passed parameter

            if (not self._prev_data.empty) & (not self.data.empty):
                if self.multi_file_day and self._load_by_date:
                    padLeft = self._prev_data[(self.date):self._curr_data.index[0]]
                else:
                    padLeft = self._prev_data[(self._curr_data.index[0]-self.pad):self._curr_data.index[0]]
                self.data = pds.concat([padLeft[0:-1], self.data])

            if (not self._next_data.empty) & (not self.data.empty):

                if self.multi_file_day and self._load_by_date:
                    padRight = self._next_data[self.date : (self.date+pds.DateOffset(hours=23, minutes=59, seconds=59, nanoseconds=99999999))]
                else:
                    padRight = self._next_data[self._curr_data.index[-1]:(self._curr_data.index[-1]+self.pad)]
                self.data = pds.concat([self.data, padRight[1:]])
                
        # if self.pad is False, load single day
        else:
            self.data, meta = self._load_data(date=self.date, fid=self._fid) 
            if not self.data.empty:
                self.meta = meta   
               
        # check if load routine actually returns meta
        if self.meta.data.empty:
            self.meta[self.data.columns] = {'long_name': self.data.columns,
                                            'units': ['']*len(self.data.columns)}
        if not self.data.empty:
            self._default_rtn(self)
        # clean
        if (not self.data.empty) & (self.clean_level != 'none'):
            self._clean_rtn(self)   
        # apply custom functions
        if not self.data.empty:
            self.custom._apply_all(self)
        # remove the excess padding, if any applied
        if (self.pad is not None)& (not self.data.empty) & (not verifyPad) :
            self.data = self.data[self._curr_data.index[0]:self._curr_data.index[-1]]
        # if loading by file set the yr, doy, and date
        if not self._load_by_date:
            temp = self.data.index[0]
            temp = pds.datetime(temp.year, temp.month, temp.day)
            self.date = temp
            self.yr, self.doy = utils.getyrdoy(self.date)

        sys.stdout.flush()
        return

    def download(self, start, stop, user=None, password=None):
        """Download data for given Instrument object from start to stop.
        
        Parameters
        ----------
        start : pandas.datetime
            start date to download data
        stop : pandas.datetime
            stop date to download data
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
            os.mkdir(os.path.join(data_dir, self.platform))
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise    
        try:
            os.mkdir(os.path.join(data_dir, self.platform, self.name))
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise    
        try:
            os.mkdir(self.files.data_path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        date_array = utils.season_date_range(start, stop)
        if user is None:
            self._download_rtn(date_array,
                               tag=self.tag,
                               data_path=self.files.data_path)
        else:
            self._download_rtn(date_array,
                               tag=self.tag,
                               data_path=self.files.data_path,
                               user=user,
                               password=password)
        # get current file date range
        first_date = self.files.start_date
        last_date = self.files.stop_date
            
        print('Updating pysat file list')
        self.files.refresh(store=True)

        # if instrument object has default bounds, update them
        if len(self.bounds[0]) == 1:
            if (self.bounds[0][0] == first_date) and (self.bounds[1][0] == last_date):
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

        if (start is None) and (end is None):
            # set default
            self._iter_start = [self.files.start_date]
            self._iter_stop = [self.files.stop_date]
            self._iter_type = 'date'
            if self._iter_start[0] is not None:
                # check here in case Instrument is initialized with no input
                self._iter_list = utils.season_date_range(self._iter_start, self._iter_stop)

        elif hasattr(start, '__iter__') and hasattr(end, '__iter__'):
            base = type(start[0])
            for s, t in zip(start, end):
                if (type(s) != type(t)) or (type(s) != base):
                    raise ValueError('Start and end items must all be of the same type')
            if isinstance(start[0], str):
                self._iter_type = 'file'
                self._iter_list = self.files.get_file_array(start, end)
            elif isinstance(start[0], pds.datetime):
                self._iter_type = 'date'
                self._iter_list = utils.season_date_range(start, end)
            else:
                raise ValueError('Input is not a known type, string or datetime')
            self._iter_start = start
            self._iter_stop = end

        elif hasattr(start, '__iter__') or hasattr(end, '__iter__'):
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
            self._iter_list = utils.season_date_range(start, end)
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
                
    def next(self):
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
                    self.load(date=self._iter_list[idx[0]])
            else:
                self.load(date=self._iter_list[0])

        elif self._iter_type == 'file':
            if self._fid is not None:
                idx, = np.where(self._iter_list == self._fid)
                if (len(idx) == 0) | (idx+1 >= len(self._iter_list)):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    idx += 1
                    self.load(fid=self._iter_list[idx[0]])
            else:
                self.load(fid=self._iter_list[0])

    def prev(self):
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
                    self.load(date=self._iter_list[idx[0]])
            else:
                self.load(date=self._iter_list[-1])

        elif self._iter_type == 'file':
            if self._fid is not None:
                idx, = np.where(self._iter_list == self._fid)
                if (len(idx) == 0) | (idx-1 < 0):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    idx -= 1
                    self.load(fid=self._iter_list[idx[0]])
            else:
                # last file by default
                self.load(fid=self._iter_list[-1])

    def to_netcdf3(self, fname=None):
        """Stores loaded data into a netCDF3 64-bit file.
        
        Parameters
        ----------
        fname : string
            full path to save instrument object to
        
        Note
        ----
        Stores 1-D data along dimension 'time' - the date time index.
        
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
        
        with netCDF4.Dataset(fname, mode='w', format='NETCDF3_64BIT') as out_data:
        
            num = len(self.data.index)
            out_data.createDimension('time', num)
            
            # write out the datetime index
            cdfkey = out_data.createVariable('unix_time', 'f8', dimensions=('time'),)
            cdfkey.units = 's'
            cdfkey.long_name = 'UNIX time'
            cdfkey.calendar = 'noleap'
            cdfkey[:] = self.data.index.astype(int)*1.E-9
            # store all of the data names in meta            
            for key in self.meta.data.index:
                if self[key].dtype != np.dtype('O'):
                    # not an object, simple column of data, write it out
                    cdfkey = out_data.createVariable(key, 
                                                     self[key].dtype,
                                                     dimensions=('time'), )
                    cdfkey.units = self.meta[key].units
                    cdfkey.long_name = self.meta[key].long_name
                    cdfkey[:] = self[key].values
                else:
                    # we are dealing with a more complicated object
                    # presuming a series with a dataframe in each location
                    dims = np.shape(self[key].iloc[0])
                    obj_dim_names = []
                    # don't need to recreate last dimension, 
                    # it covers number of columns
                    for i, dim in enumerate(dims[:-1]):
                        obj_dim_names.append(key+'_dim_%i' % (i+1))
                        out_data.createDimension(obj_dim_names[-1], dim)
                    var_dim = tuple(['time']+obj_dim_names)
                    
                    # iterate over columns and store
                    for col in self[key].iloc[0].columns:
                        coltype = self[key].iloc[0][col].dtype
                        if coltype == np.int64:
                            coltype = np.int32
                        cdfkey = out_data.createVariable(col, 
                                                         coltype,
                                                         dimensions=var_dim)
                        cdfkey.long_name = col
                        cdfkey.units = ''
                        for i in xrange(num):
                            cdfkey[i, :] = self[key].iloc[i][col].values.astype(coltype)
                            
                    # store the dataframe index for each time of main dataframe
                    datetime_flag = False
                    coltype = self[key].iloc[0].index.dtype
                    # check for datetime index
                    if coltype == np.dtype('<M8[ns]'):
                        coltype = 'f8'
                        datetime_flag = True
                    
                    cdfkey = out_data.createVariable(key+'_sample_index', 
                                                     coltype, dimensions=var_dim)
                    if datetime_flag:
                        cdfkey.units = 's'
                        cdfkey.long_name = 'UNIX time'
                        for i in xrange(num):
                            cdfkey[i, :] = self[key].iloc[i].index.astype(int)*1.E-9
                    else:
                        cdfkey.units = ''
                        cdfkey.long_name = key
                        for i in xrange(num):
                            cdfkey[i, :] = self[key].iloc[i].index.to_native_types()

                    if self[key].iloc[0].index.name is not None:
                        cdfkey.long_name = self[key].iloc[0].index.name
                    
            # store any non standard attributes
            base_attrb = dir(Instrument())
            this_attrb = dir(self)
            
            adict = {}
            for key in this_attrb:
                if key not in base_attrb:
                    if key[0] != '_':
                        adict[key] = self.__getattribute__(key)
            # store any non-standard attributes attached to meta
            base_attrb = dir(_meta.Meta())
            this_attrb = dir(self.meta)
            for key in this_attrb:
                if key not in base_attrb:
                    if key[0] != '_':
                        adict[key] = self.__getattribute__(key)
            adict['pysat_version'] = 1.0
            adict['Conventions'] = 'CF-1.6'
            out_data.setncatts(adict)
