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
        dslice = Panel.from_dict(dict([(i,data.iloc[i])
                                       for i in xrange(len(data))]))
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
            with open(os.path.join(os.path.expanduser('~'), '.pysat',
                                   'data_path.txt'), 'w') as f:
                f.write(path)
        pysat.data_dir = path
        pysat._files = re_load(pysat._files)
        pysat._instrument = re_load(pysat._instrument)
    else:
        raise ValueError('Path %s does not lead to a valid directory.' % path)

def load_netcdf4(fnames=None, strict_meta=False, file_format=None, epoch_name='Epoch',
                 units_label='units', name_label='long_name', 
                 notes_label='notes', desc_label='desc',
                 plot_label='label', axis_label='axis', 
                 scale_label='scale',
                 min_label='value_min', max_label='value_max',
                 fill_label='fill'):
                    # unix_time=False, **kwargs):
    """Load netCDF-3/4 file produced by pysat.

    Parameters
    ----------
    fnames : string or array_like of strings
        filenames to load
    strict_meta : boolean
        check if metadata across fnames is the same
    file_format : string
        file_format keyword passed to netCDF4 routine
        NETCDF3_CLASSIC, NETCDF3_64BIT, NETCDF4_CLASSIC, and NETCDF4

    Returns
    --------
    out : pandas.core.frame.DataFrame
        DataFrame output
    mdata : pysat._meta.Meta
        Meta data
    """
    import netCDF4
    import string
    import pysat

    if fnames is None:
        raise ValueError("Must supply a filename/list of filenames")
    if isinstance(fnames, basestring): 
        fnames = [fnames]

    if file_format is None:
        file_format = 'NETCDF4'
    else:
        file_format = file_format.upper()

    saved_mdata = None
    running_idx = 0
    running_store=[]
    two_d_keys = []; two_d_dims = []; three_d_keys = []; three_d_dims = [];
    for fname in fnames:
        with netCDF4.Dataset(fname, mode='r', format=file_format) as data:
            # build up dictionary with all global ncattrs
            # and add those attributes to a pysat meta object
            ncattrsList = data.ncattrs()
            mdata = pysat.Meta(units_label=units_label, name_label=name_label,
                               notes_label=notes_label, desc_label=desc_label,
                               plot_label=plot_label, axis_label=axis_label,
                               scale_label=scale_label,
                               min_label=min_label, max_label=max_label,
                               fill_label=fill_label)
            for d in ncattrsList:
                if hasattr(mdata, d):
                    mdata.__setattr__(d+'_', data.getncattr(d))
                else:
                    mdata.__setattr__(d, data.getncattr(d))

            # loadup all of the variables in the netCDF
            loadedVars = {}
            for key in data.variables.keys():
                # load up metadata.  From here group unique 
                # dimensions and act accordingly, 1D, 2D, 3D  
                if len(data.variables[key].dimensions) == 1:
                    # load 1D data variable
                    # assuming basic time dimension
                    loadedVars[key] = data.variables[key][:] 
                    # if key != epoch_name:
                    # load up metadata
                    meta_dict = {}
                    for nc_key in data.variables[key].ncattrs():
                        meta_dict[nc_key] = data.variables[key].getncattr(nc_key)
                    mdata[key] = meta_dict
                if len(data.variables[key].dimensions) == 2:
                    # part of dataframe within dataframe
                    two_d_keys.append(key)
                    two_d_dims.append(data.variables[key].dimensions)

                if len(data.variables[key].dimensions) == 3:
                    # part of full/dedicated dataframe within dataframe
                    three_d_keys.append(key)
                    three_d_dims.append(data.variables[key].dimensions)

            # we now have a list of keys that need to go into a dataframe,
            # could be more than one, collect unique dimensions for 2D keys
            for dim in set(two_d_dims):
                # first dimension should be epoch
                # second dimension name used as variable name
                obj_key_name = dim[1]
                # collect variable names associated with dimension
                idx_bool = [dim == i for i in two_d_dims]
                idx, = np.where(np.array(idx_bool))
                obj_var_keys = []
                clean_var_keys = []
                for i in idx:
                    obj_var_keys.append(two_d_keys[i])
                    clean_var_keys.append(two_d_keys[i].split(obj_key_name+'_')[-1])

                # figure out how to index this data, it could provide its own
                # index - or we may have to create simple integer based DataFrame access
                # if the dimension is stored as its own variable then use that info for index
                if obj_key_name in obj_var_keys:
                    # string used to indentify dimension also in data.variables 
                    # will be used as an index 
                    index_key_name = obj_key_name 
                    # if the object index uses UNIX time, process into datetime index  
                    if data.variables[obj_key_name].getncattr(name_label) == epoch_name:
                        # name to be used in DataFrame index
                        index_name = epoch_name
                        time_index_flag = True
                    else:
                        time_index_flag = False
                        # label to be used in DataFrame index
                        index_name = data.variables[obj_key_name].getncattr(name_label)
                else:
                    # dimension is not itself a variable
                    index_key_name  = None                

                # iterate over the variables and grab metadata
                dim_meta_data = pysat.Meta(units_label=units_label, name_label=name_label,
                                           notes_label=notes_label, desc_label=desc_label,
                                           plot_label=plot_label, axis_label=axis_label,
                                           scale_label=scale_label,
                                           min_label=min_label, max_label=max_label,
                                           fill_label=fill_label)
                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    # store attributes in metadata, exept for dim name
                    meta_dict = {}
                    for nc_key in data.variables[key].ncattrs():
                        meta_dict[nc_key] = data.variables[key].getncattr(nc_key)
                    dim_meta_data[clean_key] = meta_dict

                # print (dim_meta_data)
                dim_meta_dict = {'meta':dim_meta_data}
                if index_key_name is not None:
                    # add top level meta
                    for nc_key in data.variables[obj_key_name].ncattrs():
                        dim_meta_dict[nc_key] = data.variables[obj_key_name].getncattr(nc_key)
                    mdata[obj_key_name] = dim_meta_dict
                
                # iterate over all variables with this dimension and store data
                # data storage, whole shebang
                loop_dict = {}
                # list holds a series of slices, parsed from dict above
                loop_list = []
                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    # data
                    loop_dict[clean_key] = data.variables[key][:,:].flatten(order='C')                
                # number of values in time
                loop_lim = data.variables[obj_var_keys[0]].shape[0]
                # number of values per time
                step_size = len(data.variables[obj_var_keys[0]][0,:])
                # check if there is an index we should use
                if not (index_key_name is None):
                    # an index was found
                    time_var = loop_dict.pop(index_key_name)
                    if time_index_flag:
                        # create datetime index from data
                        if file_format == 'NETCDF4':
                            time_var = pds.to_datetime(1E6*time_var)
                        else:
                            time_var = pds.to_datetime(1E6*time_var)
                    new_index = time_var
                    new_index_name = index_name
                else:
                    # using integer indexing
                    new_index = np.arange(loop_lim*step_size, dtype=int) % step_size
                    new_index_name = 'index'
                # load all data into frame
                if len(loop_dict.keys()) > 1:
                    loop_frame = pds.DataFrame(loop_dict, columns=clean_var_keys)
                    if obj_key_name in loop_frame:
                        del loop_frame[obj_key_name]
                    # break massive frame into bunch of smaller frames
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:step_size*(i+1),:])
                        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name             
                else:
                    loop_frame = pds.Series(loop_dict[clean_var_keys[0]], name=obj_var_keys[0])
                    # break massive series into bunch of smaller series
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:step_size*(i+1)])
                        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name
                # print (loop_frame.columns)
                        
                # add 2D object data, all based on a unique dimension within
                # netCDF, to loaded data dictionary
                loadedVars[obj_key_name] = loop_list
                del loop_list

            # we now have a list of keys that need to go into a dataframe,
            # could be more than one, collect unique dimensions for 2D keys
            for dim in set(three_d_dims):
                # collect variable names associated with dimension
                idx_bool = [dim == i for i in three_d_dims]
                idx, = np.where(np.array(idx_bool))
                obj_var_keys = []
                for i in idx:
                    obj_var_keys.append(three_d_keys[i])
                    
                for obj_key_name in obj_var_keys:
                    # store attributes in metadata
                    meta_dict = {}
                    for nc_key in data.variables[obj_key_name].ncattrs():
                        meta_dict[nc_key] = data.variables[obj_key_name].getncattr(nc_key)
                    mdata[obj_key_name] = meta_dict
                    
                    # iterate over all variables with this dimension and store data
                    # data storage, whole shebang
                    loop_dict = {}
                    # list holds a series of slices, parsed from dict above
                    loop_list = []
                    loop_dict[obj_key_name] = data.variables[obj_key_name][:,:,:]                
                    # number of values in time
                    loop_lim = data.variables[obj_key_name].shape[0]
                    # number of values per time
                    step_size_x = len(data.variables[obj_key_name][0, :, 0])
                    step_size_y = len(data.variables[obj_key_name][0, 0, :])
                    step_size = step_size_x
                    loop_dict[obj_key_name] = loop_dict[obj_key_name].reshape((loop_lim*step_size_x, step_size_y))
                    # check if there is an index we should use
                    if not (index_key_name is None):
                        # an index was found
                        time_var = loop_dict.pop(index_key_name)
                        if time_index_flag:
                            # create datetime index from data
                            if file_format == 'NETCDF4':
                                time_var = pds.to_datetime(1E6*time_var)
                            else:
                                time_var = pds.to_datetime(1E6*time_var)
                        new_index = time_var
                        new_index_name = index_name
                    else:
                        # using integer indexing
                        new_index = np.arange(loop_lim*step_size, dtype=int) % step_size
                        new_index_name = 'index'
                    # load all data into frame
                    loop_frame = pds.DataFrame(loop_dict[obj_key_name])
                    # del loop_frame['dimension_1']
                    # break massive frame into bunch of smaller frames
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:step_size*(i+1),:])
                        loop_list[-1].index = new_index[step_size*i:step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name                                 
                            
                    # add 2D object data, all based on a unique dimension within netCDF,
                    # to loaded data dictionary
                    loadedVars[obj_key_name] = loop_list
                    del loop_list
                                                                
            # prepare dataframe index for this netcdf file
            time_var = loadedVars.pop(epoch_name)

            # convert from GPS seconds to seconds used in pandas (unix time,
            # no leap)
            #time_var = convert_gps_to_unix_seconds(time_var)
            if file_format == 'NETCDF4':
                loadedVars[epoch_name] = pds.to_datetime((1E6 *
                                                          time_var).astype(int))
            else:
                loadedVars[epoch_name] = pds.to_datetime((time_var *
                                                          1E6).astype(int))
            #loadedVars[epoch_name] = pds.to_datetime((time_var*1E6).astype(int))
            running_store.append(loadedVars)
            running_idx += len(loadedVars[epoch_name])

            if strict_meta:
                if saved_mdata is None:
                    saved_mdata = copy.deepcopy(mdata)
                elif (mdata != saved_mdata):
                    raise ValueError('Metadata across filenames is not the ' +
                                     'same.')

    # combine all of the data loaded across files together
    out = []
    for item in running_store:
        out.append(pds.DataFrame.from_records(item, index=epoch_name))
    out = pds.concat(out, axis=0)
    return out, mdata        


def getyrdoy(date):
    """Return a tuple of year, day of year for a supplied datetime object."""

    try:
        doy = date.toordinal()-datetime(date.year,1,1).toordinal()+1
    except AttributeError:
        raise AttributeError("Must supply a pandas datetime object or " +
                             "equivalent")
    else:
        return date.year, doy


def season_date_range(start, stop, freq='D'):
    """
    Return array of datetime objects using input frequency from start to stop

    Supports single datetime object or list, tuple, ndarray of start and 
    stop dates.

    freq codes correspond to pandas date_range codes, D daily, M monthly,
    S secondly
    """

    if hasattr(start, '__iter__'):  
        # missing check for datetime
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
        temp = (datetime(year[_idx],month[_idx],1)
                - datetime(year[0],month[0],1))
        uts_del[_idx:_idx2] += temp.total_seconds()

    # add in UTC seconds for days, ignores existence of leap seconds
    uts_del += (day-1)*86400
    # add in seconds since unix epoch to first day
    uts_del += (datetime(year[0],month[0],1)-datetime(1970,1,1)).total_seconds()
    # going to use routine that defaults to nanseconds for epoch
    uts_del *= 1E9
    return pds.to_datetime(uts_del)


def nan_circmean(samples, high=2.0*np.pi, low=0.0, axis=None):
    """NaN insensitive version of scipy's circular mean routine

    Parameters
    -----------
    samples : array_like
        Input array
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    axis : int or NoneType
        Axis along which standard deviations are computed.  The default is to
        compute the standard deviation of the flattened array

    Returns
    --------
    circmean : float
        Circular mean
    """

    samples = np.asarray(samples)
    samples = samples[~np.isnan(samples)]
    if samples.size == 0:
        return np.nan

    # Ensure the samples are in radians
    ang = (samples - low) * 2.0 * np.pi / (high - low)

    # Calculate the means of the sine and cosine, as well as the length
    # of their unit vector
    ssum = np.sin(ang).sum(axis=axis)
    csum = np.cos(ang).sum(axis=axis)
    res = np.arctan2(ssum, csum)

    # Bring the range of the result between 0 and 2 pi
    mask = res < 0.0

    if mask.ndim > 0:
        res[mask] += 2.0 * np.pi
    elif mask:
        res += 2.0 * np.pi

    # Calculate the circular standard deviation
    circmean = res * (high - low) / (2.0 * np.pi) + low
    return circmean


def nan_circstd(samples, high=2.0*np.pi, low=0.0, axis=None):
    """NaN insensitive version of scipy's circular standard deviation routine

    Parameters
    -----------
    samples : array_like
        Input array
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    axis : int or NoneType
        Axis along which standard deviations are computed.  The default is to
        compute the standard deviation of the flattened array

    Returns
    --------
    circstd : float
        Circular standard deviation
    """

    samples = np.asarray(samples)
    samples = samples[~np.isnan(samples)]
    if samples.size == 0:
        return np.nan

    # Ensure the samples are in radians
    ang = (samples - low) * 2.0 * np.pi / (high - low)

    # Calculate the means of the sine and cosine, as well as the length
    # of their unit vector
    smean = np.sin(ang).mean(axis=axis)
    cmean = np.cos(ang).mean(axis=axis)
    rmean = np.sqrt(smean**2 + cmean**2)

    # Calculate the circular standard deviation
    circstd = (high - low) * np.sqrt(-2.0 * np.log(rmean)) / (2.0 * np.pi)
    return circstd
