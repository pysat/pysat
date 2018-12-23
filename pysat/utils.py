"""
pysat.utils - utilities for running pysat
=========================================

pysat.utils contains a number of functions used
throughout the pysat package.  This includes conversion
of formats, loading of files, and user-supplied info
for the pysat data directory structure.
"""

from __future__ import print_function
from __future__ import absolute_import

import pandas as pds
import numpy as np
import copy
# python 2/3 compatibility
try:
    basestring
except NameError:
    # print ('setting basestring')
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
        dslice = Panel.from_dict(dict([(i, data.iloc[i])
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


def load_netcdf4(fnames=None, strict_meta=False, file_format=None,
                 epoch_name='Epoch', units_label='units',
                 name_label='long_name', notes_label='notes',
                 desc_label='desc', plot_label='label', axis_label='axis',
                 scale_label='scale', min_label='value_min',
                 max_label='value_max', fill_label='fill'):
    # unix_time=False, **kwargs):
    """Load netCDF-3/4 file produced by pysat.

    Parameters
    ----------
    fnames : string or array_like of strings (None)
        filenames to load
    strict_meta : boolean (False)
        check if metadata across fnames is the same
    file_format : string (None)
        file_format keyword passed to netCDF4 routine
        NETCDF3_CLASSIC, NETCDF3_64BIT, NETCDF4_CLASSIC, and NETCDF4
    epoch_name : string ('Epoch')
    units_label : string ('units')
        keyword for unit information
    name_label : string ('long_name')
        keyword for informative name label
    notes_label : string ('notes')
        keyword for file notes
    desc_label : string ('desc')
        keyword for data descriptions
    plot_label : string ('label')
        keyword for name to use on plot labels
    axis_label : string ('axis')
        keyword for axis labels
    scale_label : string ('scale')
        keyword for plot scaling
    min_label : string ('value_min')
        keyword for minimum in allowable value range
    max_label : string ('value_max')
        keyword for maximum in allowable value range
    fill_label : string ('fill')
        keyword for fill values

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
    running_store = []
    two_d_keys = []
    two_d_dims = []
    three_d_keys = []
    three_d_dims = []

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
                        meta_dict[nc_key] = \
                                data.variables[key].getncattr(nc_key)
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
                    clean_var_keys.append(
                            two_d_keys[i].split(obj_key_name + '_')[-1])

                # figure out how to index this data, it could provide its own
                # index - or we may have to create simple integer based
                # DataFrame access. If the dimension is stored as its own
                # variable then use that info for index
                if obj_key_name in obj_var_keys:
                    # string used to indentify dimension also in data.variables
                    # will be used as an index
                    index_key_name = obj_key_name
                    # if the object index uses UNIX time, process into datetime
                    # index
                    if data.variables[obj_key_name].getncattr(name_label) == \
                            epoch_name:
                        # name to be used in DataFrame index
                        index_name = epoch_name
                        time_index_flag = True
                    else:
                        time_index_flag = False
                        # label to be used in DataFrame index
                        index_name = \
                            data.variables[obj_key_name].getncattr(name_label)
                else:
                    # dimension is not itself a variable
                    index_key_name = None

                # iterate over the variables and grab metadata
                dim_meta_data = pysat.Meta(units_label=units_label,
                                           name_label=name_label,
                                           notes_label=notes_label,
                                           desc_label=desc_label,
                                           plot_label=plot_label,
                                           axis_label=axis_label,
                                           scale_label=scale_label,
                                           min_label=min_label,
                                           max_label=max_label,
                                           fill_label=fill_label)

                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    # store attributes in metadata, exept for dim name
                    meta_dict = {}
                    for nc_key in data.variables[key].ncattrs():
                        meta_dict[nc_key] = \
                            data.variables[key].getncattr(nc_key)
                    dim_meta_data[clean_key] = meta_dict

                # print (dim_meta_data)
                dim_meta_dict = {'meta': dim_meta_data}
                if index_key_name is not None:
                    # add top level meta
                    for nc_key in data.variables[obj_key_name].ncattrs():
                        dim_meta_dict[nc_key] = \
                            data.variables[obj_key_name].getncattr(nc_key)
                    mdata[obj_key_name] = dim_meta_dict

                # iterate over all variables with this dimension and store data
                # data storage, whole shebang
                loop_dict = {}
                # list holds a series of slices, parsed from dict above
                loop_list = []
                for key, clean_key in zip(obj_var_keys, clean_var_keys):
                    # data
                    loop_dict[clean_key] = \
                        data.variables[key][:, :].flatten(order='C')
                # number of values in time
                loop_lim = data.variables[obj_var_keys[0]].shape[0]
                # number of values per time
                step_size = len(data.variables[obj_var_keys[0]][0, :])
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
                    new_index = np.arange(loop_lim*step_size,
                                          dtype=int) % step_size
                    new_index_name = 'index'
                # load all data into frame
                if len(loop_dict.keys()) > 1:
                    loop_frame = pds.DataFrame(loop_dict,
                                               columns=clean_var_keys)
                    if obj_key_name in loop_frame:
                        del loop_frame[obj_key_name]
                    # break massive frame into bunch of smaller frames
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:
                                                         step_size*(i+1), :])
                        loop_list[-1].index = new_index[step_size*i:
                                                        step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name
                else:
                    loop_frame = pds.Series(loop_dict[clean_var_keys[0]],
                                            name=obj_var_keys[0])
                    # break massive series into bunch of smaller series
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:
                                                         step_size*(i+1)])
                        loop_list[-1].index = new_index[step_size*i:
                                                        step_size*(i+1)]
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
                    loop_dict[obj_key_name] = data.variables[obj_key_name][:, :, :]
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
                        new_index = np.arange(loop_lim*step_size,
                                              dtype=int) % step_size
                        new_index_name = 'index'
                    # load all data into frame
                    loop_frame = pds.DataFrame(loop_dict[obj_key_name])
                    # del loop_frame['dimension_1']
                    # break massive frame into bunch of smaller frames
                    for i in np.arange(loop_lim, dtype=int):
                        loop_list.append(loop_frame.iloc[step_size*i:
                                                         step_size*(i+1), :])
                        loop_list[-1].index = new_index[step_size*i:
                                                        step_size*(i+1)]
                        loop_list[-1].index.name = new_index_name

                    # add 2D object data, all based on a unique dimension
                    # within netCDF, to loaded data dictionary
                    loadedVars[obj_key_name] = loop_list
                    del loop_list

            # prepare dataframe index for this netcdf file
            time_var = loadedVars.pop(epoch_name)

            # convert from GPS seconds to seconds used in pandas (unix time,
            # no leap)
            # time_var = convert_gps_to_unix_seconds(time_var)
            if file_format == 'NETCDF4':
                loadedVars[epoch_name] = pds.to_datetime((1E6 *
                                                          time_var).astype(int))
            else:
                loadedVars[epoch_name] = pds.to_datetime((time_var *
                                                          1E6).astype(int))
            # loadedVars[epoch_name] = pds.to_datetime((time_var*1E6).astype(int))
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
    """Return a tuple of year, day of year for a supplied datetime object.

    Parameters
    ----------
    date : datetime.datetime
        Datetime object

    Returns
    -------
    year : int
        Integer year
    doy : int
        Integer day of year

    """

    try:
        doy = date.toordinal() - datetime(date.year, 1, 1).toordinal() + 1
    except AttributeError:
        raise AttributeError("Must supply a pandas datetime object or " +
                             "equivalent")
    else:
        return date.year, doy


def parse_date(str_yr, str_mo, str_day, str_hr='0', str_min='0', str_sec='0',
               century=2000):
    """ Basic date parser for file reading

    Parameters
    ----------
    str_yr : string
        String containing the year (2 or 4 digits)
    str_mo : string
        String containing month digits
    str_day : string
        String containing day of month digits
    str_hr : string ('0')
        String containing the hour of day
    str_min : string ('0')
        String containing the minutes of hour
    str_sec : string ('0')
        String containing the seconds of minute
    century : int (2000)
        Century, only used if str_yr is a 2-digit year

    Returns
    -------
    out_date : pds.datetime
        Pandas datetime object

    """

    yr = int(str_yr) + century if len(str_yr) == 2 else int(str_yr)
    out_date = pds.datetime(yr, int(str_mo), int(str_day), int(str_hr),
                            int(str_min), int(str_sec))

    return out_date


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
        for (sta, stp) in zip(start[1:], stop[1:]):
            season = season.append(pds.date_range(sta, stp, freq=freq))
    else:
        season = pds.date_range(start, stop, freq=freq)
    return season


# determine the median in 1 dimension
def median1D(self, bin_params, bin_label, data_label):

    bins = np.arange(bin_params[0], bin_params[1] + bin_params[2],
                     bin_params[2])
    ans = 0.*bins[0:-1]
    ind = np.digitize(self.data[bin_label], bins)

    for i in xrange(bins.size-1):
        index, = np.where(ind == (i + 1))
        if len(index) > 0:
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

    # get list of unique year, and month
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
    _, idx = np.unique(year*100.+month, return_index=True)
    # create another index array for faster algorithm below
    idx2 = np.hstack((idx, len(year) + 1))
    # computes UTC seconds offset for each unique set of year and month
    for _idx, _idx2 in zip(idx[1:], idx2[2:]):
        temp = (datetime(year[_idx], month[_idx], 1) -
                datetime(year[0], month[0], 1))
        uts_del[_idx:_idx2] += temp.total_seconds()

    # add in UTC seconds for days, ignores existence of leap seconds
    uts_del += (day-1)*86400
    # add in seconds since unix epoch to first day
    uts_del += (datetime(year[0], month[0], 1) -
                datetime(1970, 1, 1)).total_seconds()
    # going to use routine that defaults to nanseconds for epoch
    uts_del *= 1E9
    return pds.to_datetime(uts_del)


def nan_circmean(samples, high=2.0*np.pi, low=0.0, axis=None):
    """NaN insensitive version of scipy's circular mean routine

    Parameters
    -----------
    samples : array_like
        Input array
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
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
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
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


def adjust_cyclic_data(samples, high=2.0*np.pi, low=0.0):
    """Adjust cyclic values such as longitude to a different scale

    Parameters
    -----------
    samples : array_like
        Input array
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
    axis : int or NoneType
        Axis along which standard deviations are computed.  The default is to
        compute the standard deviation of the flattened array

    Returns
    --------
    out_samples : float
        Circular standard deviation

    """

    out_samples = np.asarray(samples)
    sample_range = high - low
    out_samples[out_samples >= high] -= sample_range
    out_samples[out_samples < low] += sample_range

    return out_samples


def update_longitude(inst, lon_name=None, high=180.0, low=-180.0):
    """ Update longitude to the desired range

    Parameters
    ------------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data
    high : float
        Highest allowed longitude value (default=180.0)
    low : float
        Lowest allowed longitude value (default=-180.0)

    Returns
    ---------
    updates instrument data in column 'lon_name'

    """
    from pysat.utils import adjust_cyclic_data

    if lon_name not in inst.data.keys():
        raise ValueError('uknown longitude variable name')

    new_lon = adjust_cyclic_data(inst[lon_name], high=high, low=low)

    # Update based on data type
    if inst.pandas_format:
        inst[lon_name] = new_lon
    else:
        inst[lon_name].data = new_lon

    return


def calc_solar_local_time(inst, lon_name=None, slt_name='slt'):
    """ Append solar local time to an instrument object

    Parameters
    ------------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data key (assumes data are in degrees)
    slt_name : string
        name of the output solar local time data key (default='slt')

    Returns
    ---------
    updates instrument data in column specified by slt_name

    """
    import datetime as dt

    if lon_name not in inst.data.keys():
        raise ValueError('uknown longitude variable name')

    # Convert from numpy epoch nanoseconds to UT seconds of day
    utsec = list()
    for nptime in inst.index.values.astype(int):
        # Numpy times come out in nanoseconds and timestamp converts
        # from seconds
        dtime = dt.datetime.fromtimestamp(nptime * 1.0e-9)
        utsec.append((dtime.hour * 3600.0 + dtime.minute * 60.0 +
                      dtime.second + dtime.microsecond * 1.0e-6) / 3600.0)

    # Calculate solar local time
    slt = np.array([t + inst[lon_name][i] / 15.0 for i, t in enumerate(utsec)])

    # Ensure that solar local time falls between 0 and 24 hours
    slt[slt >= 24.0] -= 24.0
    slt[slt < 0.0] += 24.0

    # Add the solar local time to the instrument
    if inst.pandas_format:
        inst[slt_name] = pds.Series(slt, index=inst.data.index)
    else:
        data = inst.data.assign(pysat_slt=(inst.data.coords.keys(), slt))
        data.rename({"pysat_slt": slt_name}, inplace=True)
        inst.data = data
    return


def scale_units(out_unit, in_unit):
    """ Determine the scaling factor between two units

    Parameters
    -------------
    out_unit : str
        Desired unit after scaling
    in_unit : str
        Unit to be scaled

    Returns
    -----------
    unit_scale : float
        Scaling factor that will convert from in_units to out_units

    Notes
    -------
    Accepted units include degrees ('deg', 'degree', 'degrees'),
    radians ('rad', 'radian', 'radians'),
    hours ('h', 'hr', 'hrs', 'hour', 'hours'), and lengths ('m', 'km', 'cm').
    Can convert between degrees, radians, and hours or different lengths.

    Example
    -----------
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
                      'm/s': ['m/s', 'cm/s', 'km/s']}

    scales = {'deg': 180.0, 'rad': np.pi, 'h': 12.0,
              'm': 1.0, 'km': 0.001, 'cm': 100.0,
              'm/s': 1.0, 'cm/s': 100.0, 'km/s': 0.001}

    # Test input and determine transformation type
    out_key = None
    in_key = None
    for kk in accepted_units.keys():
        if out_unit.lower() in accepted_units[kk]:
            out_key = kk
        if in_unit.lower() in accepted_units[kk]:
            in_key = kk

    if out_key is None:
        raise ValueError('Unknown output unit {:}'.format(out_unit))

    if in_key is None:
        raise ValueError('Unknown input unit {:}'.format(in_unit))

    if out_key == 'm' or out_key == 'm/s' or in_key == 'm' or in_key == 'm/s':
        if in_key != out_key:
            raise ValueError('Cannot scale {:s} and {:s}'.format(out_unit,
                                                                 in_unit))
        # Recast units as keys for the scales dictionary
        out_key = out_unit
        in_key = in_unit

    unit_scale = scales[out_key.lower()] / scales[in_key.lower()]

    return unit_scale


def geodetic_to_geocentric(lat_in, lon_in=None, inverse=False):
    """Converts position from geodetic to geocentric or vice-versa.

    Parameters
    ----------
    lat_in : float
        latitude in degrees.
    lon_in : float or NoneType
        longitude in degrees.  Remains unchanged, so does not need to be
        included. (default=None)
    inverse : bool
        False for geodetic to geocentric, True for geocentric to geodetic.
        (default=False)

    Returns
    -------
    lat_out : float
        latitude [degree] (geocentric/detic if inverse=False/True)
    lon_out : float or NoneType
        longitude [degree] (geocentric/detic if inverse=False/True)
    rad_earth : float
        Earth radius [km] (geocentric/detic if inverse=False/True)

    Notes
    -----
    Uses WGS-84 values

    References
    ----------
    Based on J.M. Ruohoniemi's geopack and R.J. Barnes radar.pro

    """
    rad_eq = 6378.1370  # WGS-84 semi-major axis
    flat = 1.0 / 298.257223563  # WGS-84 flattening
    rad_pol = rad_eq * (1.0 - flat)  # WGS-84 semi-minor axis

    # The ratio between the semi-major and minor axis is used several times
    rad_ratio_sq = (rad_eq / rad_pol)**2

    # Calculate the square of the second eccentricity (e')
    eprime_sq = rad_ratio_sq - 1.0

    # Calculate the tangent of the input latitude
    tan_in = np.tan(np.radians(lat_in))

    # If converting from geodetic to geocentric, take the inverse of the
    # radius ratio
    rad_ratio_sq = 1.0 / rad_ratio_sq

    # Calculate the output latitude
    lat_out = np.degrees(np.arctan(rad_ratio_sq * tan_in))

    # Calculate the Earth radius at this latitude
    rad_earth = rad_eq / np.sqrt(1.0 + eprime_sq *
                                 np.sin(np.radians(lat_out))**2)

    # longitude remains unchanged
    lon_out = lon_in

    return lat_out, lon_out, rad_earth


def geodetic_to_geocentric_horizontal(lat_in, lon_in, az_in, el_in,
                                      inverse=False):
    """Converts from local horizontal coordinates in a geodetic system to local
    horizontal coordinates in a geocentric system

    Parameters
    ----------
    lat_in : float
        latitude in degrees of the local horizontal coordinate system center
    lon_in : float
        longitude in degrees of the local horizontal coordinate system center
    az_in : float
        azimuth in degrees within the local horizontal coordinate system
    el_in : float
        elevation in degrees within the local horizontal coordinate system
    inverse : bool
        False for geodetic to geocentric, True for inverse (default=False)

    Returns
    -------
    lat_out : float
        latitude in degrees of the converted horizontal coordinate system
        center
    lon_out : float
        longitude in degrees of the converted horizontal coordinate system
        center
    rad_earth : float
        Earth radius in km at the geocentric/detic (False/True) location
    az_out : float
        azimuth in degrees of the converted horizontal coordinate system
    el_out : float
        elevation in degrees of the converted horizontal coordinate system

    References
    ----------
    Based on J.M. Ruohoniemi's geopack and R.J. Barnes radar.pro

    """
    az = np.radians(az_in)
    el = np.radians(el_in)

    # Transform the location of the local horizontal coordinate system center
    lat_out, lon_out, rad_earth = geodetic_to_geocentric(lat_in, lon_in,
                                                         inverse=inverse)

    # Calcualte the deviation from vertical in radians
    dev_vert = np.radians(lat_in - lat_out)

    # Calculate cartesian coordinated in local system
    x_local = np.cos(el) * np.sin(az)
    y_local = np.cos(el) * np.cos(az)
    z_local = np.sin(el)

    # Now rotate system about the x axis to align local vertical vector
    # with Earth radial vector
    x_out = x_local
    y_out = y_local * np.cos(dev_vert) + z_local * np.sin(dev_vert)
    z_out = -y_local * np.sin(dev_vert) + z_local * np.cos(dev_vert)

    # Transform the azimuth and elevation angles
    az_out = np.degrees(np.arctan2(x_out, y_out))
    el_out = np.degrees(np.arctan(z_out / np.sqrt(x_out**2 + y_out**2)))

    return lat_out, lon_out, rad_earth, az_out, el_out


def spherical_to_cartesian(az_in, el_in, r_in, inverse=False):
    """Convert a position from spherical to cartesian, or vice-versa

    Parameters
    ----------
    az_in : float
        azimuth/longitude in degrees or cartesian x in km (inverse=False/True)
    el_in : float
        elevation/latitude in degrees or cartesian y in km (inverse=False/True)
    r_in : float
        distance from origin in km or cartesian z in km (inverse=False/True)
    inverse : boolian
        False to go from spherical to cartesian and True for the inverse

    Returns
    -------
    x_out : float
        cartesian x in km or azimuth/longitude in degrees (inverse=False/True)
    y_out : float
        cartesian y in km or elevation/latitude in degrees (inverse=False/True)
    z_out : float
        cartesian z in km or distance from origin in km (inverse=False/True)

    Notes
    ------
    This transform is the same for local or global spherical/cartesian
    transformations

    """

    if inverse:
        # Cartesian to Spherical
        xy_sq = az_in**2 + el_in**2
        z_out = np.sqrt(xy_sq + r_in**2)  # This is r
        x_out = np.degrees(np.arctan2(np.sqrt(xy_sq), r_in))  # This is azimuth
        y_out = np.degrees(np.arctan2(el_in, az_in))  # This is elevation
    else:
        # Spherical to Cartesian
        x_out = r_in * np.cos(np.radians(az_in)) * np.sin(np.radians(el_in))
        y_out = r_in * np.cos(np.radians(az_in)) * np.cos(np.radians(el_in))
        z_out = r_in * np.sin(np.radians(az_in))

    return x_out, y_out, z_out


def global_to_local_cartesian(x_in, y_in, z_in, lat_cent, lon_cent, rad_cent,
                              inverse=False):
    """Converts a position from global to local cartesian or vice-versa

    Parameters
    ----------
    x_in : float
        global or local cartesian x in km (inverse=False/True)
    y_in : float
        global or local cartesian y in km (inverse=False/True)
    z_in : float
        global or local cartesian z in km (inverse=False/True)
    lat_cent : float
        geocentric latitude in degrees of local cartesian system origin
    lon_cent : float
        geocentric longitude in degrees of local cartesian system origin
    rad_cent : float
        distance from center of the Earth in km of local cartesian system
        origin
    inverse : bool
        False to convert from global to local cartesian coodiantes, and True
        for the inverse (default=False)

    Returns
    -------
    x_out : float
        local or global cartesian x in km (inverse=False/True)
    y_out : float
        local or global cartesian y in km (inverse=False/True)
    z_out : float
        local or global cartesian z in km (inverse=False/True)

    Notes
    -------
    The global cartesian coordinate system has its origin at the center of the
    Earth, while the local system has its origin specified by the input
    latitude, longitude, and radius.  The global system has x intersecting
    the equatorial plane and the prime meridian, z pointing North along the
    rotational axis, and y completing the right-handed coodinate system.
    The local system has z pointing up, y pointing North, and x pointing East.

    """

    # Get the global cartesian coordinates of local origin
    x_cent, y_cent, z_cent = spherical_to_cartesian(lat_cent, lon_cent,
                                                    rad_cent)

    # Get the amount of rotation needed to align the x-axis with the
    # Earth's rotational axis
    ax_rot = np.radians(90.0 - lat_cent)

    # Get the amount of rotation needed to align the global x-axis with the
    # prime meridian
    mer_rot = np.radians(lon_cent - 90.0)

    if inverse:
        # Rotate about the x-axis to align the z-axis with the Earth's
        # rotational axis
        xrot = x_in
        yrot = y_in * np.cos(ax_rot) - z_in * np.sin(ax_rot)
        zrot = y_in * np.sin(ax_rot) + z_in * np.cos(ax_rot)

        # Rotate about the global z-axis to get the global x-axis aligned
        # with the prime meridian and translate the local center to the
        # global origin
        x_out = xrot * np.cos(mer_rot) - yrot * np.sin(mer_rot) + x_cent
        y_out = xrot * np.sin(mer_rot) - yrot * np.cos(mer_rot) + y_cent
        z_out = zrot + z_cent
    else:
        # Translate global origin to the local origin
        xtrans = x_in - x_cent
        ytrans = y_in - y_cent
        ztrans = z_in - z_cent

        # Rotate about the global z-axis to get the local x-axis pointing East
        xrot = xtrans * np.cos(-mer_rot) - ytrans * np.sin(-mer_rot)
        yrot = xtrans * np.sin(-mer_rot) + ytrans * np.cos(-mer_rot)
        zrot = ztrans

        # Rotate about the x-axis to get the z-axis pointing up
        x_out = xrot
        y_out = yrot * np.cos(-ax_rot) - zrot * np.sin(-ax_rot)
        z_out = yrot * np.sin(-ax_rot) + zrot * np.cos(-ax_rot)

    return x_out, y_out, z_out


def local_horizontal_to_global_geo(az, el, dist, lat_orig, lon_orig, alt_orig,
                                   geodetic=True):
    """ Convert from local horizontal coordinates to geodetic or geocentric
    coordinates

    Parameters
    ----------
    az : float
        Azimuth (angle from North) of point in degrees
    el : float
        Elevation (angle from ground) of point in degrees
    dist : float
        Distance from origin to point in km
    lat_orig : float
        Latitude of origin in degrees
    lon_orig : float
        Longitude of origin in degrees
    alt_orig : float
        Altitude of origin in km from the surface of the Earth
    geodetic : bool
        True if origin coordinates are geodetic, False if they are geocentric.
        Will return coordinates in the same system as the origin input.
        (default=True)

    Returns
    -------
    lat_pnt : float
        Latitude of point in degrees
    lon_pnt : float
        Longitude of point in degrees
    rad_pnt : float
        Distance to the point from the centre of the Earth in km

    References
    ----------
    Based on J.M. Ruohoniemi's geopack and R.J. Barnes radar.pro

    """

    # If the data are in geodetic coordiantes, convert to geocentric
    if geodetic:
        (glat, glon, rearth, gaz, gel) = \
            geodetic_to_geocentric_horizontal(lat_orig, lon_orig, az, el,
                                              inverse=False)
        grad = rearth + alt_orig
    else:
        glat = lat_orig
        glon = lon_orig
        grad = alt_orig + 6371.0  # Add the mean earth radius in km
        gaz = az
        gel = el

    # Convert from local horizontal to local cartesian coordiantes
    x_loc, y_loc, z_loc = spherical_to_cartesian(az, el, dist, inverse=False)

    # Convert from local to global cartesian coordiantes
    x_glob, y_glob, z_glob = global_to_local_cartesian(x_loc, y_loc, z_loc,
                                                       glat, glon, grad,
                                                       inverse=True)

    # Convert from global cartesian to geocentric coordinates
    lon_pnt, lat_pnt, rad_pnt = spherical_to_cartesian(x_glob, y_glob, z_glob,
                                                       inverse=True)

    # Convert from geocentric to geodetic, if desired
    if geodetic:
        lat_pnt, lon_pnt, rearth = geodetic_to_geocentric(lat_pnt, lon_pnt,
                                                          inverse=True)
        rad_pnt = rearth + rad_pnt - 6371.0

    return lat_pnt, lon_pnt, rad_pnt
