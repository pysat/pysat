from __future__ import print_function
from __future__ import absolute_import

import pandas as pds
import numpy as np
import copy
# python 2/3 compatibility
try:
    basestring
except NameError:
    #print ('setting basestring')
    basestring = str

from pysat import DataFrame, Series, datetime, Panel

def computational_form(data):
    """
    Input Series of numbers, Series, or DataFrames repackaged
    for calculation.
    
    Parameters
    ----------
    data : pandas.Series
        Series of numbers, Series, DataFrames

    Returns
    -------
    pandas.Series, DataFrame, or Panel
        repacked data, aligned by indices, ready for calculation
        
    """

    if isinstance(data.iloc[0], DataFrame):
        dslice = Panel.from_dict(dict([(i,data.iloc[i]) for i in xrange(len(data))]))
    elif isinstance(data.iloc[0], Series):
        dslice = DataFrame(data.tolist())
        dslice.index = data.index
    else:
        dslice = data
    return dslice

def set_data_dir(path=None, store=None):
    """
    Set the top level directory pysat uses to look for data and reload.
    
    Parameters
    ----------
    path : string
        valid path to directory pysat uses to look for data
    store : bool
        if True, store data directory for future runs
        
        
    """
    import sys
    import os
    import pysat
    if sys.version_info[0] >= 3:
        if sys.version_info[1] < 4:
            import imp
            re_load = imp.reload
        else:
            import importlib
            re_load = importlib.reload
    else:
        re_load = reload
    if store is None:
        store = True    
    if os.path.isdir(path):
        if store:
            with open(os.path.join(os.getenv('HOME'), '.pysat', 'data_path.txt'), 'w') as f:
                f.write(path)
        pysat.data_dir = path
        pysat._files = re_load(pysat._files)
        pysat._instrument = re_load(pysat._instrument)
    else:
        raise ValueError('Path does not lead to a valid directory.')
        

def load_netcdf4(fnames=None, strict_meta=False, format=None): #, index_label=None,
                    # unix_time=False, **kwargs):
    """Load netCDF-3/4 file produced by pysat.
    
    Parameters
    ----------
    fnames : string or array_like of strings
        filenames to load
    strict_meta : boolean
        check if metadata across fnames is the same
    format : string
        format keyword passed to netCDF4 routine
        NETCDF3_CLASSIC, NETCDF3_64BIT, NETCDF4_CLASSIC, and NETCDF4
     
    """
                    
    import netCDF4
    import string
    import pysat

    if fnames is None:
        raise ValueError("Must supply a filename/list of filenames")
    if isinstance(fnames, basestring): 
        fnames = [fnames]

    if format is None:
        format = 'NETCDF3_64BIT'
    else:
        format = format.upper()

    saved_mdata = None
    running_idx = 0
    running_store=[]
    two_d_keys = []; two_d_dims = [];
    for fname in fnames:
        with netCDF4.Dataset(fname, mode='r', format=format) as data:
            # build up dictionary with all ncattrs
            # and add those attributes to a pysat meta object
            ncattrsList = data.ncattrs()
            mdata = pysat.Meta()
            for d in ncattrsList:
                if hasattr(mdata, d):
                    mdata.__setattr__(d+'_', data.getncattr(d))
                else:
                    mdata.__setattr__(d, data.getncattr(d))
               
            # loadup all of the variables in the netCDF
            loadedVars = {}
            for key in data.variables.keys():
                # load up metadata
                # from here group unique dimensions and act accordingly, 1D, 2D, 3D  
                if len(data.variables[key].dimensions) == 1:
                    # assuming basic time dimension
                    loadedVars[key] = data.variables[key][:] 
                    if key != 'time':
                        mdata[key] = {'long_name':data.variables[key].long_name,
                                      'units':data.variables[key].units}
                              # 'nc_dimensions':data.variables[key].dimensions}

                if len(data.variables[key].dimensions) == 2:
                    # part of dataframe within dataframe
                    two_d_keys.append(key)
                    two_d_dims.append(data.variables[key].dimensions)
                    
            # we now have a list of keys that need to go into a dataframe,
            # could be more than one, collect unique dimensions for 2D keys
            for dim in set(two_d_dims):
                
                # get the name of the final data column
                # dimension naming follows name_dim_number, 
                # pull out name by finding last _ and tracking back
                obj_key_name = dim[1][ : -string.find(dim[1][::-1], '_')-5]
                # collect variable names associated with object
                obj_var_keys = []
                for tkey, tdim in zip(two_d_keys, two_d_dims):
                    if tdim == dim:
                        obj_var_keys.append(tkey)
                        
                # loop over first object dimension
                # preallocate dataframes to hold objects because it is faster
                init_frame = DataFrame(None)
                loop_list = [init_frame]*data.variables[obj_var_keys[0]].shape[0]
                for i, loop_frame in enumerate(loop_list):
                    loop_frame = init_frame.copy()
                    for key in obj_var_keys:
                        loop_frame[key[len(obj_key_name)+1:]] = data.variables[key][i, :]
                        
                    # if the object index uses unix time, process into datetime index    
                    if data.variables[obj_key_name+'_dim_1'].long_name == 'UNIX time':
                        # nanosecond resolution from datetime64 can't be stored in netcdf3
                        # no 64-bit integers
                        # it is stored as a float, need to undo processing 
                        # due to precision loss, resolution limited to the microsecond
                        loop_frame.index = pds.to_datetime((1E6*loop_frame['dim_1']).astype(int)*1000)
                        loop_frame.index.name = 'time'
                    else:
                        loop_frame.index = loop_frame['dim_1']
                        loop_frame.index.name = data.variables[obj_key_name+'_dim_1'].long_name


                    del loop_frame['dim_1']
                    loop_list[i] = loop_frame
                    #print (loop_list[i] )
                    #loop_list.append(loop_frame)
                # add object data to loaded data dictionary
                loadedVars[obj_key_name] = loop_list
                del loop_list
                
            # prepare dataframe index for this netcdf file
            loadedVars['time'] = pds.to_datetime((loadedVars.pop('time')*1E6).astype(int)*1000)
            running_store.append(loadedVars)
            running_idx += len(loadedVars['time'])
            # if index_label is not None:
            #     if unix_time:
            #         loadedVars['_index'] = pds.to_datetime((loadedVars.pop(index_label)*1E6).astype(int)*1000)
            #     else:
            #         loadedVars['_index'] = loadedVars.pop(index_label)
            #     running_store.append(loadedVars)
            #     running_idx += len(loadedVars['_index'])
            # else:
            #     # keep a running integer index if none provided
            #     num = len(loadedVars[loadedVars.keys()[0]])
            #     # this only guaranteed to work if all variables share the same
            #     # first dimension
            #     loadedVars['_index'] = np.arange(num) + running_idx
            #     running_store.append(loadedVars)
            #     running_idx += num

            if strict_meta:
                if saved_mdata is None:
                    saved_mdata = copy.deepcopy(mdata)
                elif (mdata != saved_mdata):
                    raise ValueError('Metadata across filenames is not the same.')
                    
    # combine all of the data loaded across files together
    # currently doesn't work if list of dicts of lists is provided
    # in other words, only one file at a time
    out = DataFrame.from_records(running_store[0], index='time')
         
    return out, mdata        


def getyrdoy(date):
    """Return a tuple of year, day of year for a supplied datetime object."""
    #if date is not None:
    try:
        doy = date.toordinal()-datetime(date.year,1,1).toordinal()+1
    except AttributeError:
        raise AttributeError("Must supply a pandas datetime object or equivalent")
    else:
        return (date.year, doy)


def season_date_range(start, stop, freq='D'):
    """
    Return array of datetime objects using input frequency from start to stop
    
    Supports single datetime object or list, tuple, ndarray of start and 
    stop dates.
    
    freq codes correspond to pandas date_range codes, D daily, M monthly, S secondly
    """
    
    if hasattr(start, '__iter__'):  
        #missing check for datetime
        season = pds.date_range(start[0], stop[0], freq=freq)
        for (sta,stp) in zip(start[1:], stop[1:]):
            season = season.append(pds.date_range(sta, stp, freq=freq))
    else:
        season = pds.date_range(start, stop, freq=freq)
    return season

#determine the median in 1 dimension
def median1D(self, bin_params, bin_label,data_label):

    bins = np.arange(bin_params[0],bin_params[1]+bin_params[2],bin_params[2])
    ans = 0.*bins[0:-1]
    ind = np.digitize(self.data[bin_label], bins)

    for i in xrange(bins.size-1):
        index, = np.where(ind==(i+1))
        if len(index)>0:
            ans[i] = self.data.ix[index, data_label].median()

    return ans


def create_datetime_index(year=None, month=None, day=None, uts=None):
    """Create a timeseries index using supplied year, month, day, and ut in
    seconds.

    Parameters
    ----------
        year : array_like of ints 
        month : array_like of ints or None
        day : array_like of ints
            for day (default) or day of year (use month=None)
        uts : array_like of floats

    Returns
    -------
        Pandas timeseries index.
        
    Note
    ----
    Leap seconds have no meaning here.
        
    """
    # need a timeseries index for storing satellite data in pandas but
    # creating a datetime object for everything is too slow
    # so I calculate the number of nanoseconds elapsed since first sample, 
    # and create timeseries index from that. 
    # Factor of 20 improvement compared to previous method,
    # which itself was an order of magnitude faster than datetime.
 
    #get list of unique year, and month
    if not hasattr(year, '__iter__'):
        raise ValueError('Must provide an iterable for all inputs.')
    if len(year) == 0:
        raise ValueError('Length of array must be larger than 0.')
    year = year.astype(int)
    if month is None:
        month = np.ones(len(year), dtype=int)
    else:
        month = month.astype(int)
        
    if uts is None:
        uts = np.zeros(len(year))
    if day is None:
        day = np.ones(len(year))
    day = day.astype(int)
    # track changes in seconds
    uts_del = uts.copy().astype(float)
    # determine where there are changes in year and month that need to be 
    # accounted for    
    _,idx = np.unique(year*100.+month, return_index=True)
    # create another index array for faster algorithm below
    idx2 = np.hstack((idx,len(year)+1))   
    # computes UTC seconds offset for each unique set of year and month
    for _idx,_idx2 in zip(idx[1:],idx2[2:]):
        temp = (datetime(year[_idx],month[_idx],1) - datetime(year[0],month[0],1))
        uts_del[_idx:_idx2] += temp.total_seconds()

    # add in UTC seconds for days, ignores existence of leap seconds
    uts_del += (day-1)*86400
    # add in seconds since unix epoch to first day
    uts_del += (datetime(year[0],month[0],1)-datetime(1970,1,1) ).total_seconds()
    # going to use routine that defaults to nanseconds for epoch
    uts_del *= 1E9
    return pds.to_datetime(uts_del)
    
                                                
#def create_datetime_index_slow(year=None, doy=None, uts=None):
#    """
#    Create a Date Index for storing satellite date in pandas array.
#
#    scientific data will be loaded into a subclass of numpy called pandas
#    ,designed for time series.
#
#    Keywords:
#        yrdoy - array of yr*1000 + (Day of Year)
#        uts - array of ut seconds.
#    Output:
#        Pandas timearray containing satellite data.
#    """
#    #Need to create a time label for each of the measurements in time
#    #time labels use the python pandas.datetime functionality
#    #designed to work on a single day
#
#    #create datetime object with start date
#    #start_date = pds.datetime(yrs[0],1,1)+timedelta(days=(doys[0]-1),seconds=uts[0])
#    #create array of seconds since start time
#    
#    yr_offset = year - year[0]
#    if (year[0] % 4 == 0) & (year[0] % 100 != 0):
#        #leap year
#        uts_del = uts + (yr_offset*366. + doy)*86400.
#    else:
#        #non-leap year
#        uts_del = uts + (yr_offset*365. + doy)*86400.
#
#    uts_del -= uts_del[0]
#    #uts_del = array([(pds.datetime(year,1,1)+timedelta(days=(days-1),seconds=secs) - start_date).total_seconds() for (year,days,secs) in zip(yrs,doys,uts)])
#    #create an array of datetime seconds, then multiply by change in uts
#
#    #turns out this is super slow
##        timeIndex = pds.datetime(yrs[0],1,1) + pds.DateOffset(days=doys[0]-1, microseconds=uts[0]*1000000)
##        temp = pds.DateOffset(seconds=1)
##        timeIndex += uts_del*temp
##        return timeIndex
#
#    #create pandas.datetime object for first sample
#    #doesn't like inputs less than 1 second
#    start = pds.datetime(year[0],1,1)+pds.DateOffset(days=doy[0]-1,microseconds=uts[0]*1000000)
#    end = pds.datetime(year[-1],1,1)+pds.DateOffset(days=doy[-1]-1,microseconds=uts[-1]*1000000)
#
#    #create all times in between at a constant cadence
#    #creating pandas.datetime object for each time individually too slow
#    #thus I create a constant samplrate array
#    #and I find the satellite times closest to constant samplerate times
#    freq=1
#    timeIndex = pds.date_range(start, end, freq='%iL'%freq)
#
#    #create an index array that connects each satellite measurement time
#    #to a pandas.datetime object
#
#    #number of samples at freq samplerate to get to uts_del seconds
#    uts_del /= (freq/1000.)
#    #pick the closest integer
#    uts_del = np.floor(uts_del).astype('int64')
#    #this is now the index into the pandas.datetime array
#    #return the pandas.datetime array nearest each measurement to the
#    #closest 1 milisecond. Fails if instrument samplerate is close
#    #to this
#    return timeIndex[uts_del]

#def load_netcdf3_simple(fnames=None, strict_meta=False, **kwargs):
#    
#    import netCDF4
#
#    if fnames is None:
#        raise ValueError("Must supply a list of filenames")
#    if not hasattr(fnames, '__iter__'):
#        fnames = [fnames]    
#            
#    saved_mdata = None
#    idx = 0
#    temp_store=[]
#    for file in fnames:
#        with netCDF4.Dataset(file, mode='r', format='NETCDF3_64BIT') as data:
#            # build up dictionary will all ncattrs
#            # and add those attributes to a pysat meta object
#            ncattrsList = data.ncattrs()
#            mdata = meta.Meta()
#            for d in ncattrsList:
#                if hasattr(mdata, d):
#                    mdata.__setattr__(d+'_', data.getncattr(d))
#                else:
#                    mdata.__setattr__(d, data.getncattr(d))
#               
#            #loadup all of the variables in the netCDF
#            loadedVars={}
#            keys = data.variables.keys()
#            for key in keys:
#                # load up metadata
#                mdata[key] = {'long_name':data.variables[key].long_name,
#                                'units':data.variables[key].units,
#                                'dimensions':data.variables[key].dimensions}
#                # from here group unique dimensions and act accordingly, 1D, 2D, 3D 
#                # cheating at the moment  
#                loadedVars[key] = data.variables[key][:] 
#            num = len(loadedVars[keys()[0]])                               
#            temp_store.append(pds.DataFrame.from_dict(loadedVars,
#                                index=np.arange(num) + idx ))     
#            idx += num   
#
#            if strict_meta:
#                if saved_mdata is None:
#                    saved_mdata = copy.deepcopy(mdata)
#                elif (mdata != saved_mdata):
#                    raise ValueError('Metadata across filenames is not the same.')
#                    
#    return pds.DataFrame(temp_store), mdata        
        #out_data.close()
