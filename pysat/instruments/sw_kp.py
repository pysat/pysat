# -*- coding: utf-8 -*-
"""Supports Kp index values. Downloads data from ftp.gfz-potsdam.de or SWPC.

Parameters
----------
platform
    'sw'
name
    'kp'
tag
    - '' : Standard Kp data
    - 'forecast' : Grab forecast data from SWPC (next 3 days)
    - 'recent' : Grab last 30 days of Kp data from SWPC

Note
----
Standard Kp files are stored by the first day of each month. When downloading
use kp.download(start, stop, freq='MS') to only download days that could
possibly have data.  'MS' gives a monthly start frequency.

The forecast data is stored by generation date, where each file contains the
forecast for the next three days. Forecast data downloads are only supported
for the current day. When loading forecast data, the date specified with the
load command is the date the forecast was generated. The data loaded will span
three days. To always ensure you are loading the most recent data, load
the data with tomorrow's date.
::

    kp = pysat.Instrument('sw', 'kp', tag='recent')
    kp.download()
    kp.load(date=kp.tomorrow())

Recent data is also stored by the generation date from the SWPC. Each file
contains 30 days of Kp measurements. The load date issued to pysat corresponds
to the generation date.

The recent and forecast data should not be used with the data padding option
available from pysat.Instrument objects.


Warnings
--------
The 'forecast' Kp data loads three days at a time. The data padding feature
and multi_file_day feature available from the pyast.Instrument object
is not appropriate for Kp 'forecast' data.


This material is based upon work supported by the
National Science Foundation under Grant Number 1259508.

Any opinions, findings, and conclusions or recommendations expressed in this
material are those of the author(s) and do not necessarily reflect the views
of the National Science Foundation.

Custom Functions
----------------
filter_geoquiet
    Filters pysat.Instrument data for given time after Kp drops below gate.

"""

import functools
import numpy as np
import os

import pandas as pds

import pysat

import logging
logger = logging.getLogger(__name__)


platform = 'sw'
name = 'kp'
tags = {'': '',
        'forecast': 'SWPC Forecast data next (3 days)',
        'recent': 'SWPC provided Kp for past 30 days'}
sat_ids = {'': ['', 'forecast', 'recent']}

# generate todays date to support loading forecast data
now = pysat.datetime.now()
today = pysat.datetime(now.year, now.month, now.day)
# set test dates
_test_dates = {'': {'': pysat.datetime(2009, 1, 1),
                    'forecast': today + pds.DateOffset(days=1)}}


def load(fnames, tag=None, sat_id=None):
    """Load Kp index files

    Parameters
    ------------
    fnames : pandas.Series
        Series of filenames
    tag : str or NoneType
        tag or None (default=None)
    sat_id : str or NoneType
        satellite id or None (default=None)

    Returns
    ---------
    data : pandas.DataFrame
        Object containing satellite data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    Notes
    -----
    Called by pysat. Not intended for direct use by user.


    """
    from pysat.utils.time import parse_date

    meta = pysat.Meta()
    if tag == '':
        # Kp data stored monthly, need to return data daily
        # the daily date is attached to filename
        # parse off the last date, load month of data, downselect to desired
        # day
        data = pds.DataFrame()
        # set up fixed width format for these files
        colspec = [(0, 2), (2, 4), (4, 6), (7, 10), (10, 13), (13, 16),
                   (16, 19), (19, 23), (23, 26), (26, 29), (29, 32), (32, 50)]
        for filename in fnames:
            # the daily date is attached to filename
            # parse off the last date, load month of data, downselect to the
            # desired day
            fname = filename[0:-11]
            date = pysat.datetime.strptime(filename[-10:], '%Y-%m-%d')

            temp = pds.read_fwf(fname, colspecs=colspec, skipfooter=4,
                                header=None, parse_dates=[[0, 1, 2]],
                                date_parser=parse_date, index_col='0_1_2')
            idx, = np.where((temp.index >= date) &
                            (temp.index < date + pds.DateOffset(days=1)))
            temp = temp.iloc[idx, :]
            data = pds.concat([data, temp], axis=0)

        # drop last column as it has data I don't care about
        data = data.iloc[:, 0:-1]

        # each column increments UT by three hours
        # produce a single data series that has Kp value monotonically
        # increasing in time with appropriate datetime indices
        s = pds.Series()
        for i in np.arange(8):
            temp = pds.Series(data.iloc[:, i].values,
                              index=data.index+pds.DateOffset(hours=int(3*i)))
            s = s.append(temp)
        s = s.sort_index()
        s.index.name = 'time'

        # now, Kp comes in non-user friendly values
        # 2-, 2o, and 2+ relate to 1.6, 2.0, 2.3
        # will convert for user friendliness
        first = np.array([float(x[0]) for x in s])
        flag = np.array([x[1] for x in s])

        ind, = np.where(flag == '+')
        first[ind] += 1.0 / 3.0
        ind, = np.where(flag == '-')
        first[ind] -= 1.0 / 3.0

        result = pds.DataFrame(first, columns=['Kp'], index=s.index)
        fill_val = np.nan
    elif tag == 'forecast':
        # load forecast data
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
        fill_val = -1
    elif tag == 'recent':
        # load recent Kp data
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
        fill_val = -1

    # Initalize the meta data
    for kk in result.keys():
        initialize_kp_metadata(meta, kk, fill_val)

    return result, meta


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : string or NoneType
        Denotes type of file to load.
        (default=None)
    sat_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : string or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    --------
    pysat.Files.from_os : pysat._files.Files
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
                out.loc[out.index[-1] + pds.DateOffset(months=1)
                        - pds.DateOffset(days=1)] = out.iloc[-1]
                out = out.asfreq('D', 'pad')
                out = out + '_' + out.index.strftime('%Y-%m-%d')
            return out
        elif tag == 'forecast':
            format_str = 'kp_forecast_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)
            # pad list of files data to include most recent file under tomorrow
            if not files.empty:
                pds_offset = pds.DateOffset(days=1)
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
            return files
        elif tag == 'recent':
            format_str = 'kp_recent_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)
            # pad list of files data to include most recent file under tomorrow
            if not files.empty:
                pds_offset = pds.DateOffset(days=1)
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
            return files

        else:
            raise ValueError('Unrecognized tag name for Space Weather Index ' +
                             'Kp')
    else:
        raise ValueError('A data_path must be passed to the loading routine ' +
                         'for Kp')


def download(date_array, tag, sat_id, data_path, user=None, password=None):
    """Routine to download Kp index data

    Parameters
    -----------
    tag : string or NoneType
        Denotes type of file to load.  Accepted types are '' and 'forecast'.
        (default=None)
    sat_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    Only able to download current forecast data, not archived forecasts.

    """

    # download standard Kp data
    if tag == '':
        import ftplib
        from ftplib import FTP
        import sys
        ftp = FTP('ftp.gfz-potsdam.de')   # connect to host, default port
        ftp.login()               # user anonymous, passwd anonymous@
        ftp.cwd('/pub/home/obs/kp-ap/tab')
        dnames = list()

        for date in date_array:
            fname = 'kp{year:02d}{month:02d}.tab'
            fname = fname.format(year=(date.year - date.year//100*100),
                                 month=date.month)
            local_fname = fname
            saved_fname = os.path.join(data_path, local_fname)
            if not fname in dnames:
                try:
                    logger.info('Downloading file for '+date.strftime('%b %Y'))
                    sys.stdout.flush()
                    ftp.retrbinary('RETR '+fname, open(saved_fname, 'wb').write)
                    dnames.append(fname)
                except ftplib.error_perm as exception:

                    if str(exception.args[0]).split(" ", 1)[0] != '550':
                        # leaving a bare raise below so that ftp errors
                        # are properly reported as coming from ftp
                        # and gives the correct line number.
                        # We aren't expecting any 'normal' ftp errors
                        # here, other than a 550 'no file' error, thus
                        # accurately raising FTP issues is the way to go
                        raise
                    else:
                        # file isn't actually there, just let people know
                        # then continue on
                        os.remove(saved_fname)
                        logger.info('File not available for '+date.strftime('%x'))

        ftp.close()

    elif tag == 'forecast':
        import requests
        logger.info('This routine can only download the current forecast, ' +
              'not archived forecasts')
        # download webpage
        furl = 'https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt'
        r = requests.get(furl)
        # parse text to get the date the prediction was generated
        date_str = r.text.split(':Issued: ')[-1].split(' UTC')[0]
        date = pysat.datetime.strptime(date_str, '%Y %b %d %H%M')
        # data is the forecast value for the next three days
        raw_data = r.text.split('NOAA Kp index forecast ')[-1]
        # get date of the forecasts
        date_str = raw_data[0:6] + ' ' + str(date.year)
        forecast_date = pysat.datetime.strptime(date_str, '%d %b %Y')
        # strings we will use to parse the downloaded text
        lines = ['00-03UT', '03-06UT', '06-09UT', '09-12UT', '12-15UT',
                 '15-18UT', '18-21UT', '21-00UT']
        # storage for daily forecasts
        # get values for each day, then combine together
        day1 = []
        day2 = []
        day3 = []
        for line in lines:
            raw = raw_data.split(line)[-1].split('\n')[0]
            day1.append(int(raw[0:10]))
            day2.append(int(raw[10:20]))
            day3.append(int(raw[20:]))
        times = pds.date_range(forecast_date, periods=24, freq='3H')
        day = []
        for dd in [day1, day2, day3]:
            day.extend(dd)
        # put data into nicer DataFrame
        data = pds.DataFrame(day, index=times, columns=['Kp'])
        # write out as a file
        data.to_csv(os.path.join(data_path, 'kp_forecast_' +
                                 date.strftime('%Y-%m-%d') + '.txt'),
                    header=True)

    elif tag == 'recent':
        import requests
        logger.info('This routine can only download the current webpage, not ' +
              'archived forecasts')
        # download webpage
        rurl = 'https://services.swpc.noaa.gov/text/' + \
            'daily-geomagnetic-indices.txt'
        r = requests.get(rurl)
        # parse text to get the date the prediction was generated
        date_str = r.text.split(':Issued: ')[-1].split('\n')[0]
        date = pysat.datetime.strptime(date_str, '%H%M UT %d %b %Y')
        # data is the forecast value for the next three days
        raw_data = r.text.split('#  Date ')[-1]
        # keep only the middle bits that matter
        raw_data = raw_data.split('\n')[1:-1]

        # hold times from the file
        kp_time = []
        # holds Kp value for each station
        sub_kps = [[], [], []]
        # iterate through file lines and parse out the info we want
        for line in raw_data:
            kp_time.append(pysat.datetime.strptime(line[0:10], '%Y %m %d'))
            # pick out Kp values for each of the three columns
            sub_lines = [line[17:33], line[40:56], line[63:]]
            for sub_line, sub_kp in zip(sub_lines, sub_kps):
                for i in np.arange(8):
                    sub_kp.append(int(sub_line[i*2:(i+1)*2]))
        # create times on 3 hour cadence
        times = pds.date_range(kp_time[0], periods=8*30, freq='3H')
        # put into DataFrame
        data = pds.DataFrame({'mid_lat_Kp': sub_kps[0],
                              'high_lat_Kp': sub_kps[1],
                              'Kp': sub_kps[2]}, index=times)
        # write out as a file
        data.to_csv(os.path.join(data_path, 'kp_recent_' +
                                 date.strftime('%Y-%m-%d') + '.txt'),
                    header=True)

    return


def filter_geoquiet(sat, maxKp=None, filterTime=None, kpData=None,
                    kp_inst=None):
    """Filters pysat.Instrument data for given time after Kp drops below gate.

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

    Notes
    -----
    Loads Kp data for the same timeframe covered by sat and sets sat.data to
    NaN for times when Kp > maxKp and for filterTime after Kp drops below
    maxKp.

    This routine is written for standard Kp data, not the forecast or recent
    data.

    """
    if kp_inst is not None:
        kp_inst.load(date=sat.date, verifyPad=True)
        kpData = kp_inst
    elif kpData is None:
        kp = pysat.Instrument('sw', 'Kp', pad=pds.DateOffset(days=1))
        kp.load(date=sat.date, verifyPad=True)
        kpData = kp

    if maxKp is None:
        maxKp = 3 + 1./3.

    if filterTime is None:
        filterTime = 24

    # now the defaults are ensured, let's do some filtering
    # date of satellite data
    date = sat.date
    selData = kpData[date-pds.DateOffset(days=1):date+pds.DateOffset(days=1)]
    ind, = np.where(selData['Kp'] >= maxKp)
    for lind in ind:
        sind = selData.index[lind]
        eind = sind + pds.DateOffset(hours=filterTime)
        sat.data[sind:eind] = np.NaN
        sat.data = sat.data.dropna(axis=0, how='all')

    return


def initialize_kp_metadata(meta, data_key, fill_val=-1):
    """ Initialize the Kp meta data using our knowledge of the index

    Parameters
    ----------
    meta : pysat._meta.Meta
        Pysat Metadata
    data_key : str
        String denoting the data key
    fill_val : int or float
        File-specific fill value (default=-1)

    """

    data_label = data_key.replace("_", " ")
    format_label = data_label[0].upper() + data_label[1:]

    meta[data_key] = {meta.units_label: '', meta.name_label: data_key,
                      meta.desc_label: "Planetary K-index",
                      meta.plot_label: format_label,
                      meta.axis_label: format_label,
                      meta.scale_label: 'linear', meta.min_label: 0,
                      meta.max_label: 9, meta.fill_label: fill_val}

    return


def convert_3hr_kp_to_ap(kp_inst):
    """ Calculate 3 hour ap from 3 hour Kp index

    Parameters
    ----------
    kp_inst : pysat.Instrument
        Pysat instrument containing Kp data

    Returns
    -------
    Void : Updates kp_inst with '3hr_ap'

    Notes
    -----
    Conversion between ap and Kp indices is described at:
    https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html

    """

    # Kp are keys, where n.3 = n+ and n.6 = (n+1)-. E.g., 0.6 = 1-
    kp_to_ap = {0: 0, 0.3: 2, 0.6: 3, 1: 4, 1.3: 5, 1.6: 6, 2: 7, 2.3: 9,
                2.6: 12, 3: 15, 3.3: 18, 3.6: 22, 4: 27, 4.3: 32, 4.6: 39,
                5: 48, 5.3: 56, 5.6: 67, 6: 80, 6.3: 94, 6.6: 111, 7: 132,
                7.3: 154, 7.6: 179, 8: 207, 8.3: 236, 8.6: 300, 9: 400}

    def ap(kk): return kp_to_ap[np.floor(kk*10.0) / 10.0] \
        if np.isfinite(kk) else np.nan

    # Test the input
    if 'Kp' not in kp_inst.data.columns:
        raise ValueError('unable to locate Kp data')

    # Convert from Kp to ap
    fill_val = kp_inst.meta['Kp'][kp_inst.meta.fill_label]
    ap_data = np.array([ap(kp) if kp != fill_val else fill_val
                        for kp in kp_inst['Kp']])

    # Append the output to the pysat instrument
    kp_inst['3hr_ap'] = pds.Series(ap_data, index=kp_inst.index)

    # Add metadata
    meta_dict = {kp_inst.meta.units_label: '',
                 kp_inst.meta.name_label: 'ap',
                 kp_inst.meta.desc_label: "3-hour ap (equivalent range) index",
                 kp_inst.meta.plot_label: "ap",
                 kp_inst.meta.axis_label: "ap",
                 kp_inst.meta.scale_label: 'linear',
                 kp_inst.meta.min_label: 0,
                 kp_inst.meta.max_label: 400,
                 kp_inst.meta.fill_label: fill_val,
                 kp_inst.meta.notes_label: 'ap converted from Kp as described '
                 'at: https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html'}

    kp_inst.meta.__setitem__('3hr_ap', meta_dict)
