# -*- coding: utf-8 -*-
"""Supports Kp index values. Downloads data from ftp.gfz-potsdam.de.

Parameters
----------
platform : string
    'sw'
name : string
    'kp'
tag : string
    None supported

Note
----
Files are stored by the first day of each month. When downloading use
kp.download(start, stop, freq='MS') to only download days that could possibly
have data.  'MS' gives a monthly start frequency.

This material is based upon work supported by the 
National Science Foundation under Grant Number 1259508. 

Any opinions, findings, and conclusions or recommendations expressed in this 
material are those of the author(s) and do not necessarily reflect the views 
of the National Science Foundation.
       
"""

import os
import functools

import pandas as pds
import numpy as np

import pysat
from . import nasa_cdaweb_methods as cdw

platform = 'sw'
name = 'kp'
tags = {'':''}
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}


# create a basic parser to deal with date format of the Kp file
def _parse(yr, mo, day):
    """
    Basic parser to deal with date format of the Kp file.
    """
    
    yr = '20'+yr
    yr = int(yr)
    mo = int(mo)
    day = int(day)
    return pds.datetime(yr, mo, day)


def load(fnames, tag=None, sat_id=None):
    """Load Kp index files

    Parameters
    ------------
    fnames : (pandas.Series)
        Series of filenames
    tag : (str or NoneType)
        tag or None (default=None)
    sat_id : (str or NoneType)
        satellite id or None (default=None)

    Returns
    ---------
    data : (pandas.DataFrame)
        Object containing satellite data
    meta : (pysat.Meta)
        Object containing metadata such as column names and units

    Notes
    -----
    Called by pysat. Not intended for direct use by user.
    
    """

    # Kp data stored monthly, need to return data daily
    # the daily date is attached to filename
    # parse off the last date, load month of data, downselect to desired day
    data = pds.DataFrame()
    #set up fixed width format for these files
    colspec = [(0,2),(2,4),(4,6),(7,10),(10,13),(13,16),(16,19),(19,23),(23,26),(26,29),(29,32),(32,50)]
    for filename in fnames:
        # the daily date is attached to filename
        # parse off the last date, load month of data, downselect to desired day
        fname = filename[0:-11]
        date = pysat.datetime.strptime(filename[-10:], '%Y-%m-%d')

        temp = pds.read_fwf(fname, colspecs=colspec, skipfooter=4,header=None, 
                            parse_dates=[[0,1,2]], date_parser=_parse, 
                            index_col='0_1_2')
        idx, = np.where((temp.index >= date) & (temp.index < date+pds.DateOffset(days=1)))
        temp = temp.iloc[idx,:]
        data = pds.concat([data,temp], axis=0)
        
    # drop last column as it has data I don't care about
    data = data.iloc[:,0:-1]
    
    # each column increments UT by three hours
    # produce a single data series that has Kp value monotonically increasing in time
    # with appropriate datetime indices
    s = pds.Series()
    for i in np.arange(8):
        temp = pds.Series(data.iloc[:,i].values, 
                          index=data.index+pds.DateOffset(hours=int(3*i))  )
        #print temp
        s = s.append(temp) 
    s = s.sort_index()
    s.index.name = 'time'
    
    # now, Kp comes in non-user friendly values
    # 2-, 2o, and 2+ relate to 1.6, 2.0, 2.3
    # will convert for user friendliness
    first = np.array([float(x[0]) for x in s])
    flag = np.array([x[1] for x in s])

    ind, = np.where(flag == '+')
    first[ind] += 1./3.
    ind, = np.where(flag == '-')
    first[ind] -= 1./3.
    
    result = pds.DataFrame(first, columns=['kp'], index=s.index)
        
    return result, pysat.Meta()
    
def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are '1min' and '5min'.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : (string or NoneType)
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    Notes
    -----
    Called by pysat. Not intended for direct use by user.    
    
    """

    if data_path is not None:
        if tag == '':
            # files are by month, going to add date to monthly filename for
            # each day of the month. The load routine will load a month of
            # data and use the appended date to select out appropriate data.
            if format_str is None:
                format_str = 'kp{year:2d}{month:02d}.tab'
            out = pysat.Files.from_os(data_path=data_path, 
                format_str=format_str,
                two_digit_year_break=94)
            if not out.empty:
                out.ix[out.index[-1]+pds.DateOffset(months=1)-
                         pds.DateOffset(days=1)] = out.iloc[-1]  
                out = out.asfreq('D', 'pad')
                out = out + '_' + out.index.strftime('%Y-%m-%d')  
            return out
        else:
            raise ValueError('Unrecognized tag name for Space Weather Index Kp')                  
    else:
        raise ValueError ('A data_path must be passed to the loading routine for Kp')  



def download(date_array, tag, sat_id, data_path, user=None, password=None):
    """Routine to download Kp index data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are '1min' and '5min'.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)

    Returns
    --------
    Void : (NoneType)
        data downloaded to disk, if available.
    
    Notes
    -----
    Called by pysat. Not intended for direct use by user.

    """

    import ftplib
    from ftplib import FTP
    import sys
    ftp = FTP('ftp.gfz-potsdam.de')   # connect to host, default port
    ftp.login()               # user anonymous, passwd anonymous@
    ftp.cwd('/pub/home/obs/kp-ap/tab')

    for date in date_array:
        fname = 'kp{year:02d}{month:02d}.tab'
        fname = fname.format(year=(date.year - date.year//100*100), month=date.month)
        local_fname = fname
        saved_fname = os.path.join(data_path,local_fname) 
        try:
            print('Downloading file for '+date.strftime('%D'))
            sys.stdout.flush()
            ftp.retrbinary('RETR '+fname, open(saved_fname,'wb').write)
        except ftplib.error_perm as exception:
            # if exception[0][0:3] != '550':
            if str(exception.args[0]).split(" ", 1)[0] != '550':
                raise
            else:
                os.remove(saved_fname)
                print('File not available for '+date.strftime('%D'))
    
    ftp.close()
    return        
    
def filter_geoquiet(sat, maxKp=None, filterTime=None, kpData=None, kp_inst=None):
    """Filters pysat.Instrument data for given time after Kp drops below gate.
    
    Loads Kp data for the same timeframe covered by sat and sets sat.data to
    NaN for times when Kp > maxKp and for filterTime after Kp drops below maxKp.
    
    Parameters
    ----------
    sat : pysat.Instrument
        Instrument to be filtered
    maxKp : float
        Maximum Kp value allowed. Kp values above this trigger
        sat.data filtering.
    filterTime : int
        Number of hours to filter data after Kp drops below maxKp
    kpData : pysat.Instrument (optional)
        Kp pysat.Instrument object with data already loaded
    kp_inst : pysat.Instrument (optional)
        Kp pysat.Instrument object ready to load Kp data.Overrides kpData.
        
    Returns
    -------
    None : NoneType
        sat Instrument object modified in place
        
    """
    if kp_inst is not None:
        kp_inst.load(date=sat.date, verifyPad=True)
        kpData = kp_inst
    elif kpData is None:
        kp = pysat.Instrument('sw', 'kp', pad=pds.DateOffset(days=1))
        kp.load(date=sat.date, verifyPad=True)
        kpData = kp
        
    
    if maxKp is None:
        maxKp = 3+ 1./3.
        
    if filterTime is None:
        filterTime = 24
        
    # now the defaults are ensured, let's do some filtering
    # date of satellite data
    date = sat.date
    selData = kpData[date-pds.DateOffset(days=1):date+pds.DateOffset(days=1)]
    ind, = np.where(selData['kp'] >= maxKp)
    for lind in ind:
        sat.data[selData.index[lind]:(selData.index[lind]+pds.DateOffset(hours=filterTime) )] = np.NaN
        sat.data = sat.data.dropna(axis=0, how='all')

    return
    
    
