# -*- coding: utf-8 -*-
import string
import pandas as pds
import numpy as np
import os
#from types import ModuleType
import copy
import sys


import _custom
import _files
import _orbits
import _meta
import utils
from pysat import data_dir #import pysat.data_dir as data_dir

# main class for users
class Instrument(object):


    def __init__(self, platform=None, name=None, tag=None, clean_level='clean', 
                query_files=False, pad=False,
                orbit_index=None, orbit_type=None, orbit_period=None,  
                inst_module=None, *arg, **kwargs):
        '''
        Class for analyzing, modifying, and managing satellite data.
        
        platform: String for instrument platform/satellite.
	name : String indicating name of instrument. 
	tag : String identifying particular aspect of the instrument.
	   pysat attempts to load corresponding instrument module platform_name.
	inst_module : Provide instrument module directly (takes precedence over name)
	clean_level : String passed to clean function indicating level of quality.
	pad : Boolean indicating whether padding should be added (using instrument data) to begining and end of data
	       for time-series processing. Extra data is removed after applying all custom functions. Pad=True requires
                length of time for padding (seconds or minutes or hours). Maximum of 1-day.
	orbit_index : String indicating which data will be used to determine breaks in orbit, if requested.
	orbit_type : String indicating type of orbit, equatorial (default) or polar.
	orbit_period : datetime.timedelta object containing length of orbital period.
	query_files: Boolean indicating whether the filesystem should be queried
	               or if the stored list of files is sufficient. (set True if new files)
	
	'''

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

        self.data = pds.DataFrame(None)
        self.meta = _meta.Meta()
        # function processing class, processes data on load
        self.custom = _custom.custom()
        # create arrays to store data around loaded day
        # enables padding across day breaks with minimal loads
        self._next_data = pds.DataFrame(None)
	self._next_data_track = []
        self._prev_data = pds.DataFrame(None)
        self._prev_data_track = []
        self._curr_data = pds.DataFrame(None)
        # arguments for padding
        self.pad = pad
        self.padkws = kwargs	

        # load file list function, which returns dict of files
        # as well as data start and end dates
        self.files = _files.Files(self)
        if query_files:
            self.files.refresh()
        # set bounds for iteration based upon data properties
        self.bounds = (None, None)
        self.date = None
        self._fid = None
        self.yr = None
        self.doy = None
        self._load_by_date = False
        # attach seasonal methods for convenience        
        #self.ssnl = ssnl
        # initiliaze orbit support
        self.orbits = _orbits.orbits(self, index=orbit_index, kind=orbit_type,
                                    period=orbit_period)
        # run instrument init function, a basic pass function is used
        # if user doesn't supply the init function
        self._init_rtn(self)
        
                
    def __getitem__(self, key): 
        """
        Convenience notation for accessing data in inst.data.name using
        inst['name'].
        
        Slicing is also allowed inst['name', a:b].
        """

        if isinstance(key, tuple):
	    # support slicing	
            return self.data.ix[key[0], key[1]]
	else:
	    return self.data[key]

    def __setitem__(self,key,new):
        """Add data to inst.data dataFrame. inst['name'] = newData."""
        if isinstance(new, dict):
            # metadata should be included in dict
            self.data[key] = new.pop('data')
            # pass the rest to meta
            self.meta[key] = new
        else:
            if isinstance(key, tuple):
                self.data.ix[key[0],key[1]] = new
                if key[1] not in self.meta.data.index:
                    self.meta[key[1]] = {'long_name':key, 'units':''}
            elif isinstance(key, str):
                self.data[key] = new  
                if key not in self.meta.data.index:   
                    # add in default metadata because none was supplied
                    self.meta[key] = {'long_name':key, 'units':''} 
            elif isinstance(new, pds.DataFrame):
                self.data[key] = new[key]
                for ke in key:
                    if ke not in self.meta.data.index:   
                        # add in default metadata because none was supplied
                        self.meta[ke] = {'long_name':ke, 'units':''}                 
            else:
                raise ValueError("No support for supplied input key")           
    
    def copy(self):
        """Deep copy of the entire satellite object."""
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
            inst = importlib.import_module(''.join(('.',self.platform,'_',
                        self.name)),  package='pysat.instruments')
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
	    fname = self.files.files.iloc[fid]
	elif date is not None:
	    fname = self.files[date : date+pds.DateOffset(days=1)]
	else:
	    raise ValueError('Must supply either a date or file id number.')
   
        if len(fname) > 0:    
            load_fname = [os.path.join(self.files.data_path, f) for f in fname]
            data, mdata = self._load_rtn(load_fname, tag = self.tag) 
        else:
            data = pds.DataFrame(None)
            mdata = _meta.Meta()

        if not data.empty: 
            if not isinstance(data, pds.DataFrame):
                raise TypeError(string.join(('Data returned by instrument load',
                                'routine must be a pandas.DataFrame')))
            if not isinstance(mdata, _meta.Meta):
                raise TypeError('Metadata returned must be a pysat.Meta object')
            if date is not None:
                print string.join(('Returning',self.platform,self.name,self.tag,'data for', 
                              date.strftime('%D')))
            else:
                if len(fname) == 1:
                    # this check was zero
                    print string.join(('Returning',self.platform,self.name,self.tag,
                                        'data from',fname[0]))
                else:
                    print string.join(('Returning',self.platform,self.name,self.tag,
                            'data from',fname[0], ' :: ',fname[-1]))
        else:
            # no data signal
            print string.join(('No',self.platform,self.name,self.tag,'data for', 
                                date.strftime('%D')))
    
        return data, mdata
        
    def _load_next(self):
        '''Load the next days data (or file) without incrementing the date.
        Repeated calls will not advance date/file and will produce the same data
        
        Uses info stored in object to either increment the date, 
        or the file. Looks for self._load_by_date flag.  
	'''
	if self._load_by_date:
	    next_date = self.date + pds.DateOffset(days=1)
       	    return self._load_data(date=next_date)
       	else:
       	    return self._load_data(fid = self._fid+1)

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
	    return self._load_data(fid = self._fid-1)

    def load(self, yr=None, doy=None, date=None, fname=None, fid=None, 
                verifyPad=False, *arg, **kwargs):
        """
        Load instrument data into satellite object as .data

        Keywords:
            yr: year
            doy: day of year
            date: datetime object for date
            fname: filename to be loaded
            verifyPad: boolean to verify data padding is being applied (debug purposes)
        Summary:
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
            self.date = (pds.datetime(yr,1,1) ) + pds.DateOffset(days=(doy-1))
            self.yr = yr
            self.doy = doy
            self._fid = None
            self._load_by_date = True
            inc = pds.DateOffset(days=1)
            curr = self.date
        elif fname != None:
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
	elif fid != None:
            self._load_by_date = False	    
	    self._fid = fid
	    self.date = None
            self.yr = None
            self.doy = None
	    inc = 1
	    curr = fid
        else:
            raise TypeError('Must supply a yr,doy pair, or datetime object, '+ 
				'or filename to load data from.')
				
        self.orbits._reset()        
        # if pad is true, need to have a three day/file load
        if self.pad:
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
	        self.data = pds.DataFrame(None)	
	        self.meta = _meta.Meta()
            # pad data based upon passed parameter
            offs = pds.DateOffset( **(self.padkws) )
            if (not self._prev_data.empty) & (not self.data.empty) :
                padLeft = self._prev_data[(self._curr_data.index[0]-offs):self._curr_data.index[0]]
                self.data = pds.concat([padLeft[0:-1], self.data])
            if  (not self._next_data.empty) & (not self.data.empty) :
                padRight = self._next_data[self._curr_data.index[-1]:(self._curr_data.index[-1]+offs)]
                self.data = pds.concat([self.data, padRight[1:]])
        # if self.pad is False, load single day
        else:
            self.data, self.meta  = self._load_data(date=self.date, fid=self._fid)       
        # check if load routine actually returns meta
        if self.meta.data.empty:
            self.meta[self.data.columns] = {'long_name':self.data.columns,
                                            'units':['']*len(self.data.columns)}
        if not self.data.empty:
            self._default_rtn(self)
	# clean
        if  (not self.data.empty) & (self.clean_level != 'none') :
            self._clean_rtn(self)   
        # apply custom functions
        if not self.data.empty:
            self.custom._apply_all(self)
        # remove the excess padding, if any applied
        if self.pad & (not self.data.empty) & (not verifyPad) :
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
        '''Download data for given Instrument object.'''
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
        date_array = utils.season_date_range(start,stop)
        if user is None:
            self._download_rtn(date_array, tag=self.tag, 
                    data_path=self.files.data_path)
        else:
            self._download_rtn(date_array, tag=self.tag, 
                    data_path=self.files.data_path,user=user, password=password)	
        print 'Updating pysat file list'
        self.files.refresh(store=True)
        
    @property
    def bounds(self):
	"""
	Boundaries for iterating over instrument object by date or file.
	
	input: 
	   start: datetime object, filename, or None (default)
		  Defines start of iteration, if None uses first data date.
	   end:  datetime object, filename, or None (default)
		 Defines end of iteration, inclusive. If None uses last
		 data date. 	
        """
        return (self._iter_start, self._iter_stop)
    
    @bounds.setter        
    def bounds(self, value=None):
        #start=None, end=None):
	"""
	Set boundaries for iterating over instrument object by date or file.
	
	input: 
	   start: datetime object, filename, or None (default)
		  Defines start of iteration, if None uses first data date.
	   end:  datetime object, filename, or None (default)
		 Defines end of iteration, inclusive. If None uses last
		 data date. 	
        """
        if value is None:
            value = (None,None)
        if len(value) < 2:
            raise ValueError('Must supply both a start and end date/file'+
                  'Supply None if you want the first/last possible')

        start = value[0]
        end = value[1]

        if (start is None) and (end is None):
	    #set default
	    self._iter_start = [self.files.start_date]
	    self._iter_stop = [self.files.stop_date]
            self._iter_type = 'date'
            if self._iter_start[0] is not None:
                # check here in case Instrument is initialized with no input
                self._iter_list = utils.season_date_range(self._iter_start, self._iter_stop)

	elif hasattr(start, '__iter__') and hasattr(end, '__iter__'):
            base = type(start[0])
	    for s,t in zip(start, end):
	        if (type(s) != type(t)) or (type(s) != base):
	            raise ValueError('Start and end items must all be of the same type')
	    if isinstance(start[0], str):
                self._iter_type = 'file'
		self._iter_list = self.files.get_file_array(start, end)	        
            elif isinstance(start[0], pds.datetime):
                self._iter_type = 'date'
                self._iter_list = utils.season_date_range(start, end)
            else:
                raise ValueError ('Input is not a known type, string or datetime')
            self._iter_start = start
            self._iter_stop = end

        elif hasattr(start, '__iter__') or hasattr(end, '__iter__'):
            raise ValueError('Both start and end must be iterable if one bound is iterable')

        elif isinstance(start, str) or isinstance(end, str):
            if isinstance(start, pds.datetime) or isinstance(end, pds.datetime):
                raise ValueError('Not allowed to mix file and date bounds')
	    if start is None:
	        start = self.files.files[0]
	    if end is None:
	        end = self.file.files[-1]	
            self._iter_start = [start]
            self._iter_stop = [end]
            self._iter_list = self.files.get_file_array(self._iter_start,self._iter_stop)
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
	    raise ValueError('Provided an invalid combination of bounds. '+
	    'if specifying by file, both bounds must be by file. Other '+
	    'combinations of datetime objects and None are allowed.')


    def __iter__(self):
        """
        Iterates by loading subsequent days or files as appropriate.
        	
	Limits of iteration set by calling setBounds method.	
        """
        if self._iter_type == 'file':
            for fid in self._iter_list:
                self.load(fid=fid)
                yield self       
 
	elif self._iter_type == 'date': 
            for date in self._iter_list:
                self.load(date=date)
                yield self            
                
    def next(self):
        """
        Manually iterate through the data loaded in satellite object.
        
        Bounds of iteration and iteration type (day/file) are set by setBounds
        If there were no previous calls to load then the first
        day (default)/file will be loaded.
        """
        
	if self._iter_type == 'date':
       	    if self.date is not None:
       	        idx, = np.where(self._iter_list == self.date )
       	        if (len(idx)==0) | (idx+1 >= len(self._iter_list) ):
       	            raise StopIteration('Outside the set date boundaries.')
       	        else:
       	            idx += 1
       	            self.load(date = self._iter_list[idx[0]])
            else:
                self.load(date = self._iter_list[0])
                
        elif self._iter_type == 'file':
            if self._fid is not None:
       	        idx, = np.where(self._iter_list == self._fid )
       	        if (len(idx)==0) | (idx+1 >= len(self._iter_list) ):
       	            raise StopIteration('Outside the set file boundaries.')
       	        else:
       	            idx += 1
       	            self.load(fid = self._iter_list[idx[0]])
            else:
                self.load(fid = self._iter_list[0])

    def prev(self):
        """
        Manually iterate backwards through the data loaded in satellite object.
        
        Bounds of iteration and iteration type (day/file) are set by setBounds
        If there were no previous calls to load then the last
        day (default)/file will be loaded.
        """
        
	if self._iter_type == 'date':
       	    if self.date is not None:
       	        idx, = np.where(self._iter_list == self.date )
       	        if (len(idx)==0) | (idx-1 < 0 ):
       	            raise StopIteration('Outside the set date boundaries.')
       	        else:
       	            idx -= 1
       	            self.load(date = self._iter_list[idx[0]])
            else:
                self.load(date = self._iter_list[-1])
                
        elif self._iter_type == 'file':
            if self._fid is not None:
       	        idx, = np.where(self._iter_list == self._fid )
       	        if (len(idx)==0) | (idx-1 < 0 ):
       	            raise StopIteration('Outside the set file boundaries.')
       	        else:
       	            idx -= 1
       	            self.load(fid = self._iter_list[idx[0]])
            else:
                #last file by default
                self.load(fid = self._iter_list[-1])


    def to_netcdf3(self, fname=None):
        """
        Stores loaded data into a netCDF3 64-bit file.
        
        Stores 1-D data along dimension 'time' - the date time index.
        Stores object data (dataframes within dataframe) separately:
            The name of the object data is used to prepend extra variable
              dimensions within netCDF, key_2, key_3, first dimension time
            The index organizing the data stored as key_sample_index
            from_netcdf3 uses this naming scheme to reconstruct data structure
        The datetime index is stored as 'UNIX time'. netCDF-3 doesn't support
          64-bit integers so it is stored as a 64-bit float. This results in a
          loss of datetime precision when converted back to datetime index
          up to hundreds of nanoseconds. Use netCDF4 if this is a problem.
          
        All attributes attached to instrument meta are written to netCDF attrs.
        
        """
        
        import netCDF4
        
        with netCDF4.Dataset('/Users/rstoneba/Desktop/test.nc', 
                            mode='w', format='NETCDF3_64BIT') as out_data:
        
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
                    cdfkey = out_data.createVariable(key, self[key].dtype, dimensions=('time'), )
                    cdfkey.units = self.meta[key].units
                    cdfkey.long_name = self.meta[key].long_name
                    cdfkey[:] = self[key].values
                else:
                    # we are dealing with a more complicated object
                    # presuming a series with a dataframe in each location
                    dims = np.shape(self[key].iloc[0])
                    obj_dim_names=[]
                    # don't need to recreate last dimension, 
                    # it covers number of columns
                    for i,dim in enumerate(dims[:-1]):
                        obj_dim_names.append(key+'_dim_%i' % (i+1))
                        out_data.createDimension(obj_dim_names[-1], dim)
                    var_dim = tuple(['time']+obj_dim_names)
                    
                    # iterate over columns and store
                    for col in self[key].iloc[0].columns:
                        coltype = self[key].iloc[0][col].dtype
                        if coltype == np.int64 :
                            coltype = np.int32
                        cdfkey = out_data.createVariable(col, coltype, dimensions=var_dim)
                        cdfkey.long_name = col
                        cdfkey.units = ''
                        for i in xrange(num):
                            cdfkey[i,:] = self[key].iloc[i][col].values.astype(coltype)
                            
                    # store the dataframe index for each time of main dataframe
                    datetime_flag = False
                    coltype = self[key].iloc[0].index.dtype
                    # check for datetime index
                    if coltype == np.dtype('<M8[ns]'):
                        coltype = 'f8' #self[key].iloc[0].index.to_native_types()[0].dtype
                        datetime_flag = True
                    
                    cdfkey = out_data.createVariable(key+'_sample_index', 
                                        coltype, dimensions=var_dim)
                    if datetime_flag:
                        cdfkey.units='s'
                        cdfkey.long_name = 'UNIX time'
                        for i in xrange(num):
                            cdfkey[i,:] = self[key].iloc[i].index.astype(int)*1.E-9
                    else:
                        cdfkey.units=''
                        cdfkey.long_name = key
                        for i in xrange(num):
                            cdfkey[i,:] = self[key].iloc[i].index.to_native_types()

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


