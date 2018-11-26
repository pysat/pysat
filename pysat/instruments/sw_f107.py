# -*- coding: utf-8 -*-
"""Supports F10.7 index values. Downloads data from LASP and the SWPC.

Parameters
----------
platform : string
    'sw'
name : string
    'f107'
tag : string
    '' Standard F10.7 data (single day at a time)
    'all' All F10.7
    'forecast' Grab forecast data from SWPC (next 3 days)
    '45day' 45-Day Forecast data from the Air Force

Note
----
The forecast data is stored by generation date, where each file contains the
forecast for the next three days. Forecast data downloads are only supported
for the current day. When loading forecast data, the date specified with the
load command is the date the forecast was generated. The data loaded will span
three days. To always ensure you are loading the most recent data, load
the data with tomorrow's date.

    f107 = pysat.Instrument('sw', 'f107', tag='forecast')
    f107.download()
    f107.load(date=f107.tomorrow())



The forecast data should not be used with the data padding option available
from pysat.Instrument objects. The 'all' tag shouldn't be used either, no
other data available to pad with.

Warnings
--------
The 'forecast' F10.7 data loads three days at a time. The data padding feature
and multi_file_day feature available from the pyast.Instrument object
is not appropriate for 'forecast' data.

       
"""

import os
import functools

import pandas as pds
import numpy as np

import pysat

platform = 'sw'
name = 'f107'
tags = {'':'Daily value of F10.7',
        'all':'All F10.7 values',
        'forecast':'SWPC Forecast F107 data next (3 days)',
        '45day':'Air Force 45-day Forecast'}
# dict keyed by sat_id that lists supported tags for each sat_id
sat_ids = {'':['', 'all', 'forecast', '45day']}
# dict keyed by sat_id that lists supported tags and a good day of test data
# generate todays date to support loading forecast data
now = pysat.datetime.now()
today = pysat.datetime(now.year, now.month, now.day)
tomorrow = today + pds.DateOffset(days=1)
# set test dates
test_dates = {'':{'':pysat.datetime(2009,1,1), 
                  'all':pysat.datetime(2009,1,1),
                  'forecast':tomorrow,
                  '45day':tomorrow}}


def load(fnames, tag=None, sat_id=None):
    """Load F10.7 index files

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


    if tag == '':
        # f107 data stored monthly, need to return data daily
        # the daily date is attached to filename
        # parse off the last date, load month of data, downselect to desired day
        date = pysat.datetime.strptime(fnames[0][-10:], '%Y-%m-%d')
        data = pds.read_csv(fnames[0][0:-11], index_col=0, parse_dates=True) 
        idx, = np.where((data.index >= date) &
                        (data.index < date+pds.DateOffset(days=1)))
        result = data.iloc[idx,:]      
    elif tag == 'all':
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
    elif tag == 'forecast':
        # load forecast data
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
    elif tag == '45day':
        # load forecast data
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
    
    meta = pysat.Meta()
    meta['f107'] = {'units':'SFU',
                    'long_name':'F10.7 cm solar index',
                    'desc':'F10.7 cm radio flux in Solar Flux Units (SFU)'}
                    
    return result, meta
    
def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for F10.7 data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.
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
                format_str = 'f107_monthly_{year:04d}-{month:02d}.txt'
            out = pysat.Files.from_os(data_path=data_path, 
                                      format_str=format_str)
            if not out.empty:
                out.ix[out.index[-1]+pds.DateOffset(months=1)-
                         pds.DateOffset(days=1)] = out.iloc[-1]  
                out = out.asfreq('D', 'pad')
                out = out + '_' + out.index.strftime('%Y-%m-%d')  
            return out
            
        elif tag == 'all':
            # files are by year
            if format_str is None:
                format_str = 'f107_1947_to_{year:04d}-{month:02d}-{day:02d}.txt'
            out = pysat.Files.from_os(data_path=data_path, 
                                    format_str=format_str)
            # load the same data (all), regardless of which day a user selects
            # resample file list to provide the same filename for every day
            # of f107 data
            if not out.empty:
                # only want to use the most recent file
                out = out.iloc[-1:]
                # first day of data is 2-14, ensure same file for first and
                # most recent day
                out.ix[pysat.datetime(1947, 2, 13)] = out.iloc[0]
                # make sure things are in order and copy latest filename for
                # all days, thus no matter which day with data the user loads
                # they get the most recent F10.7 file
                out = out.sort_index()                
                out = out.asfreq('D', 'pad')

            return out

        elif tag == 'forecast':
            format_str = 'f107_forecast_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                       format_str=format_str)
            # pad list of files data to include most recent file under tomorrow
            if not files.empty:
                files.ix[files.index[-1]+pds.DateOffset(days=1)] = files.values[-1]
                files.ix[files.index[-1]+pds.DateOffset(days=1)] = files.values[-1]
            return files
        elif tag == '45day':
            format_str = 'f107_45day_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                       format_str=format_str)
            # pad list of files data to include most recent file under tomorrow
            if not files.empty:
                files.ix[files.index[-1]+pds.DateOffset(days=1)] = files.values[-1]
                files.ix[files.index[-1]+pds.DateOffset(days=1)] = files.values[-1]
            return files
        else:
            raise ValueError('Unrecognized tag name for Space Weather Index ' +
                             'F107')                  
    else:
        raise ValueError ('A data_path must be passed to the loading routine ' +
                          'for F107')  



def download(date_array, tag, sat_id, data_path, user=None, password=None):
    """Routine to download F107 index data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are '' and 'forecast'.
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
    
    Note
    ----
    Called by pysat. Not intended for direct use by user.
    
    Warnings
    --------
    Only able to download current forecast data, not archived forecasts.

    """


    # download standard F107 data
    if tag == '':    
        # download from LASP, by month
        import requests
        import json
                    
        for date in date_array:
            # modify date to be the start of the month
            if date.day != 1:
                raise ValueError('The Download routine must be invoked with ' +
                                 'a freq="MS" option.')
            # download webpage
            dstr = 'http://lasp.colorado.edu/lisird/latis/'
            dstr += 'noaa_radio_flux.json?time%3E=' 
            dstr += date.strftime('%Y-%m-%d')
            dstr += 'T00:00:00.000Z&time%3C=' 
            dstr += (date + pds.DateOffset(months=1) -
                     pds.DateOffset(days=1)).strftime('%Y-%m-%d')
            dstr += 'T00:00:00.000Z'
            # data returned as json
            r = requests.get(dstr)
            # process
            raw_dict = json.loads(r.text)['noaa_radio_flux']
            data = pds.DataFrame.from_dict(raw_dict['samples'])
            times = [pysat.datetime.strptime(time, '%Y %m %d')
                     for time in data.pop('time')]
            data.index = times
            # replace fill with NaNs
            idx, = np.where(data['f107'] == -99999.0)
            data.iloc[idx,:] = np.nan
            # create file
            data.to_csv(os.path.join(data_path, 'f107_monthly_' +
                                     date.strftime('%Y-%m') + '.txt'))

    elif tag == 'all':    
        # download from LASP, by year
        import requests
        import json
                    
        # download webpage
        dstr = 'http://lasp.colorado.edu/lisird/latis/'
        dstr += 'noaa_radio_flux.json?time%3E=' 
        dstr += pysat.datetime(1947, 2, 13).strftime('%Y-%m-%d')
        dstr += 'T00:00:00.000Z&time%3C='
        now = pysat.datetime.utcnow() 
        dstr += now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        # data returned as json
        r = requests.get(dstr)
        # process
        raw_dict = json.loads(r.text)['noaa_radio_flux']
        data = pds.DataFrame.from_dict(raw_dict['samples'])
        times = [pysat.datetime.strptime(time, '%Y %m %d')
                 for time in data.pop('time')]
        data.index = times
        # replace fill with NaNs
        idx, = np.where(data['f107'] == -99999.0)
        data.iloc[idx,:] = np.nan
        # create file
        data.to_csv(os.path.join(data_path, 'f107_1947_to_' +
                                 now.strftime('%Y-%m-%d') + '.txt'))
            
        
    elif tag == 'forecast':
        import requests
        print('This routine can only download the current forecast, not ' +
              'archived forecasts')
        # download webpage
        furl = 'https://services.swpc.noaa.gov/text/' + \
            '3-day-solar-geomag-predictions.txt'
        r = requests.get(furl)
        # parse text to get the date the prediction was generated
        date_str = r.text.split(':Issued: ')[-1].split(' UTC')[0]
        date = pysat.datetime.strptime(date_str, '%Y %b %d %H%M')
        # get starting date of the forecasts
        raw_data = r.text.split(':Prediction_dates:')[-1]
        forecast_date = pysat.datetime.strptime(raw_data[3:14], '%Y %b %d')
        # times for output data
        times = pds.date_range(forecast_date, periods=3, freq='1D')
        # string data is the forecast value for the next three days
        raw_data = r.text.split('10cm_flux:')[-1]
        raw_data = raw_data.split('\n')[1]
        val1 = int(raw_data[24:27])
        val2 = int(raw_data[38:41])
        val3 = int(raw_data[52:])
        
        # put data into nicer DataFrame
        data = pds.DataFrame([val1, val2, val3], index=times, columns=['f107'])
        # write out as a file
        data.to_csv(os.path.join(data_path, 'f107_forecast_' +
                                 date.strftime('%Y-%m-%d') + '.txt'))

    elif tag == '45day':
        import requests
        print('This routine can only download the current forecast, not ' +
              'archived forecasts')
        # download webpage
        furl = 'https://services.swpc.noaa.gov/text/45-day-ap-forecast.txt'
        r = requests.get(furl)
        # parse text to get the date the prediction was generated
        date_str = r.text.split(':Issued: ')[-1].split(' UTC')[0]
        date = pysat.datetime.strptime(date_str, '%Y %b %d %H%M')
        # get to the forecast data
        raw_data = r.text.split('45-DAY AP FORECAST')[-1]
        # grab AP part
        raw_ap = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[0]
        # clean up
        raw_ap = raw_ap.split('\n')[1:-1]
        # f107
        raw_f107 = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[-1]
        # clean up
        raw_f107 = raw_f107.split('\n')[1:-4]
        
        # parse the AP data
        ap_times = []
        ap = []
        for line in raw_ap:
            for i in np.arange(5):
                ap_times.append(pysat.datetime.strptime(line[0:7], '%d%b%y'))
                ap.append(int(line[8:11]))
        
        f107 = []
        f107_times = []
        for line in raw_f107:
            for i in np.arange(5):
                f107_times.append(pysat.datetime.strptime(line[0:7], '%d%b%y'))
                f107.append(int(line[8:11]))
        
        # collect into DataFrame
        data = pds.DataFrame(f107, index=f107_times, columns=['f107'])
        data['ap'] = ap
        # write out as a file
        data.to_csv(os.path.join(data_path, 'f107_45day_' +
                                 date.strftime('%Y-%m-%d') + '.txt'))

    return        
