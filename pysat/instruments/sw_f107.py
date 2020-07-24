# -*- coding: utf-8 -*-
"""Supports F10.7 index values. Downloads data from LASP and the SWPC.

Properties
----------
platform
    'sw'
name
    'f107'
tag
    - '' : LASP F10.7 data (downloads by month, loads by day)
    - 'all' : All LASP standard F10.7
    - 'prelim' : Preliminary SWPC daily solar indices
    - 'daily' : Daily SWPC solar indices (contains last 30 days)
    - 'forecast' : Grab forecast data from SWPC (next 3 days)
    - '45day' : 45-Day Forecast data from the Air Force

Note
----
The forecast data is stored by generation date, where each file contains the
forecast for the next three days. Forecast data downloads are only supported
for the current day. When loading forecast data, the date specified with the
load command is the date the forecast was generated. The data loaded will span
three days. To always ensure you are loading the most recent data, load
the data with tomorrow's date.
::

    f107 = pysat.Instrument('sw', 'f107', tag='forecast')
    f107.download()
    f107.load(date=f107.tomorrow())



The forecast or prelim data should not be used with the data padding option
available from pysat.Instrument objects. The 'all' tag shouldn't be used either,
no other data available to pad with.


Warnings
--------
The 'forecast' F10.7 data loads three days at a time. The data padding feature
and multi_file_day feature available from the pyast.Instrument object
is not appropriate for 'forecast' data.

"""

import os
import warnings

import numpy as np
import pandas as pds

import pysat

import logging
logger = logging.getLogger(__name__)

platform = 'sw'
name = 'f107'
tags = {'': 'Daily LASP value of F10.7',
        'all': 'All LASP F10.7 values',
        'prelim': 'Preliminary SWPC daily solar indices',
        'daily': 'Daily SWPC solar indices (contains last 30 days)',
        'forecast': 'SWPC Forecast F107 data next (3 days)',
        '45day': 'Air Force 45-day Forecast'}
# dict keyed by sat_id that lists supported tags for each sat_id
sat_ids = {'': ['', 'all', 'prelim', 'daily', 'forecast', '45day']}
# dict keyed by sat_id that lists supported tags and a good day of test data
# generate todays date to support loading forecast data
now = pysat.datetime.now()
today = pysat.datetime(now.year, now.month, now.day)
tomorrow = today + pds.DateOffset(days=1)
# set test dates
_test_dates = {'': {'': pysat.datetime(2009, 1, 1),
                    'all': pysat.datetime(2009, 1, 1),
                    'prelim': pysat.datetime(2009, 1, 1),
                    'daily': tomorrow,
                    'forecast': tomorrow,
                    '45day': tomorrow}}


def load(fnames, tag=None, sat_id=None):
    """Load F10.7 index files

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

    if tag == '':
        # f107 data stored monthly, need to return data daily
        # the daily date is attached to filename
        # parse off the last date, load month of data, downselect to desired
        # day
        date = pysat.datetime.strptime(fnames[0][-10:], '%Y-%m-%d')
        data = pds.read_csv(fnames[0][0:-11], index_col=0, parse_dates=True)
        idx, = np.where((data.index >= date) &
                        (data.index < date + pds.DateOffset(days=1)))
        result = data.iloc[idx, :]
    elif tag == 'all':
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
    elif tag == 'daily' or tag == 'prelim':
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
    elif tag == 'forecast':
        # load forecast data
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)
    elif tag == '45day':
        # load forecast data
        result = pds.read_csv(fnames[0], index_col=0, parse_dates=True)

    meta = pysat.Meta()
    meta['f107'] = {meta.units_label: 'SFU',
                    meta.name_label: 'F10.7 cm solar index',
                    meta.desc_label:
                    'F10.7 cm radio flux in Solar Flux Units (SFU)'}

    if tag == '45day':
        meta['ap'] = {meta.name_label: 'Daily Ap index',
                      meta.desc_label: 'Daily average of 3-h ap indices'}
    elif tag == 'daily' or tag == 'prelim':
        meta['ssn'] = {meta.name_label: 'Sunspot Number',
                       meta.desc_label: 'SESC Sunspot Number',
                       meta.fill_label: -999}
        meta['ss_area'] = {meta.name_label: 'Sunspot Area',
                           meta.desc_label: 'Sunspot Area 10$^6$ Hemisphere',
                           meta.fill_label: -999}
        meta['new_reg'] = {meta.name_label: 'New Regions',
                           meta.desc_label: 'New active solar regions',
                           meta.fill_label: -999}
        meta['smf'] = {meta.name_label: 'Solar Mean Field',
                       meta.desc_label: 'Standford Solar Mean Field',
                       meta.fill_label: -999}
        meta['goes_bgd_flux'] = {meta.name_label: 'X-ray Background Flux',
                                 meta.desc_label:
                                 'GOES15 X-ray Background Flux',
                                 meta.fill_label: '*'}
        meta['c_flare'] = {meta.name_label: 'C X-Ray Flares',
                           meta.desc_label: 'C-class X-Ray Flares',
                           meta.fill_label: -1}
        meta['m_flare'] = {meta.name_label: 'M X-Ray Flares',
                           meta.desc_label: 'M-class X-Ray Flares',
                           meta.fill_label: -1}
        meta['x_flare'] = {meta.name_label: 'X X-Ray Flares',
                           meta.desc_label: 'X-class X-Ray Flares',
                           meta.fill_label: -1}
        meta['o1_flare'] = {meta.name_label: '1 Optical Flares',
                            meta.desc_label: '1-class Optical Flares',
                            meta.fill_label: -1}
        meta['o2_flare'] = {meta.name_label: '2 Optical Flares',
                            meta.desc_label: '2-class Optical Flares',
                            meta.fill_label: -1}
        meta['o3_flare'] = {meta.name_label: '3 Optical Flares',
                            meta.desc_label: '3-class Optical Flares',
                            meta.fill_label: -1}

    return result, meta


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for F10.7 data

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
                format_str = 'f107_monthly_{year:04d}-{month:02d}.txt'
            out = pysat.Files.from_os(data_path=data_path,
                                      format_str=format_str)
            if not out.empty:
                out.loc[out.index[-1] + pds.DateOffset(months=1)
                        - pds.DateOffset(days=1)] = out.iloc[-1]
                out = out.asfreq('D', 'pad')
                out = out + '_' + out.index.strftime('%Y-%m-%d')
            return out

        elif tag == 'all':
            # files are by year
            if format_str is None:
                format_str = ''.join(('f107_1947_to_{year:04d}-{month:02d}-',
                                      '{day:02d}.txt'))
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
                out.loc[pysat.datetime(1947, 2, 13)] = out.iloc[0]
                # make sure things are in order and copy latest filename for
                # all days, thus no matter which day with data the user loads
                # they get the most recent F10.7 file
                out = out.sort_index()
                out = out.asfreq('D', 'pad')

            return out

        elif tag == 'prelim':
            # files are by year (and quarter). The load routine will load a
            # year of data
            if format_str is None:
                format_str = \
                    'f107_prelim_{year:04d}_{month:02d}_v{version:01d}.txt'
            out = pysat.Files.from_os(data_path=data_path,
                                      format_str=format_str)

            if not out.empty:
                # Set each file's valid length at a 1-day resolution
                orig_files = out.sort_index().copy()
                new_files = list()

                for orig in orig_files.iteritems():
                    # Version determines each file's valid length
                    version = int(orig[1].split("_v")[1][0])
                    doff = pds.DateOffset(years=1) if version == 2 \
                        else pds.DateOffset(months=3)
                    istart = orig[0]
                    iend = istart + doff - pds.DateOffset(days=1)

                    # Ensure the end time does not extend past the number of
                    # possible days included based on the file's download time
                    fname = os.path.join(data_path, orig[1])
                    dend = pds.datetime.utcfromtimestamp(os.path.getctime(fname))
                    dend = dend - pds.DateOffset(days=1)
                    if dend < iend:
                        iend = dend

                    # Pad the original file index
                    out.loc[iend] = orig[1]
                    out = out.sort_index()

                    # Save the files at a daily cadence over the desired period
                    new_files.append(out.loc[istart: iend].asfreq('D', 'pad'))
                # Add the newly indexed files to the file output
                out = pds.concat(new_files, sort=True)
                out = out.dropna()
                out = out.sort_index()

            return out

        elif tag == 'daily':
            format_str = 'f107_daily_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)

            # pad list of files data to include most recent file under tomorrow
            if not files.empty:
                pds_off = pds.DateOffset(days=1)
                files.loc[files.index[-1] + pds_off] = files.values[-1]
                files.loc[files.index[-1] + pds_off] = files.values[-1]
            return files

        elif tag == 'forecast':
            format_str = 'f107_forecast_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)
            # pad list of files data to include most recent file under tomorrow
            if not files.empty:
                pds_off = pds.DateOffset(days=1)
                files.loc[files.index[-1] + pds_off] = files.values[-1]
                files.loc[files.index[-1] + pds_off] = files.values[-1]
            return files

        elif tag == '45day':
            format_str = 'f107_45day_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)

            # pad list of files data to include most recent file under tomorrow
            if not files.empty:
                pds_off = pds.DateOffset(days=1)
                files.loc[files.index[-1] + pds_off] = files.values[-1]
                files.loc[files.index[-1] + pds_off] = files.values[-1]
            return files

        else:
            raise ValueError('Unrecognized tag name for Space Weather Index ' +
                             'F107')
    else:
        raise ValueError('A data_path must be passed to the loading routine ' +
                         'for F107')


def download(date_array, tag, sat_id, data_path, user=None, password=None):
    """Routine to download F107 index data

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
            dstr = 'http://lasp.colorado.edu/lisird/latis/dap/'
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
            if data.empty:
                warnings.warn("no data for {:}".format(date), UserWarning)
            else:
                times = [pysat.datetime.strptime(time, '%Y%m%d')
                         for time in data.pop('time')]
                data.index = times
                # replace fill with NaNs
                idx, = np.where(data['f107'] == -99999.0)
                data.iloc[idx, :] = np.nan
                # create file
                data.to_csv(os.path.join(data_path, 'f107_monthly_' +
                                         date.strftime('%Y-%m') + '.txt'),
                            header=True)

    elif tag == 'all':
        # download from LASP, by year
        import requests
        import json

        # download webpage
        dstr = 'http://lasp.colorado.edu/lisird/latis/dap/'
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
        try:
            # This is the new data format
            times = [pysat.datetime.strptime(time, '%Y%m%d')
                     for time in data.pop('time')]
        except ValueError:
            # Accepts old file formats
            times = [pysat.datetime.strptime(time, '%Y %m %d')
                     for time in data.pop('time')]
        data.index = times
        # replace fill with NaNs
        idx, = np.where(data['f107'] == -99999.0)
        data.iloc[idx, :] = np.nan
        # create file
        data.to_csv(os.path.join(data_path, 'f107_1947_to_' +
                                 now.strftime('%Y-%m-%d') + '.txt'),
                    header=True)

    elif tag == 'prelim':
        import ftplib
        from ftplib import FTP
        import sys
        ftp = FTP('ftp.swpc.noaa.gov')  # connect to host, default port
        ftp.login()  # user anonymous, passwd anonymous@
        ftp.cwd('/pub/indices/old_indices')

        bad_fname = list()

        # Get the local files, to ensure that the version 1 files are
        # downloaded again if more data has been added
        local_files = list_files(tag, sat_id, data_path)

        # To avoid downloading multiple files, cycle dates based on file length
        date = date_array[0]
        while date <= date_array[-1]:
            # The file name changes, depending on how recent the requested
            # data is
            qnum = (date.month-1) // 3 + 1  # Integer floor division
            qmonth = (qnum-1) * 3 + 1
            quar = 'Q{:d}_'.format(qnum)
            fnames = ['{:04d}{:s}DSD.txt'.format(date.year, ss)
                      for ss in ['_', quar]]
            versions = ["01_v2", "{:02d}_v1".format(qmonth)]
            vend = [pysat.datetime(date.year, 12, 31),
                    pysat.datetime(date.year, qmonth, 1)
                    + pds.DateOffset(months=3) - pds.DateOffset(days=1)]
            downloaded = False
            rewritten = False

            # Attempt the download(s)
            for iname, fname in enumerate(fnames):
                # Test to see if we already tried this filename
                if fname in bad_fname:
                    continue

                local_fname = fname
                saved_fname = os.path.join(data_path, local_fname)
                ofile = '_'.join(['f107', 'prelim', '{:04d}'.format(date.year),
                                  '{:s}.txt'.format(versions[iname])])
                outfile = os.path.join(data_path, ofile)

                if os.path.isfile(outfile):
                    downloaded = True

                    # Check the date to see if this should be rewritten
                    checkfile = os.path.split(outfile)[-1]
                    has_file = local_files == checkfile
                    if np.any(has_file):
                        if has_file[has_file].index[-1] < vend[iname]:
                            # This file will be updated again, but only attempt
                            # to do so if enough time has passed from the
                            # last time it was downloaded
                            yesterday = today - pds.DateOffset(days=1)
                            if has_file[has_file].index[-1] < yesterday:
                                rewritten = True
                else:
                    # The file does not exist, if it can be downloaded, it
                    # should be 'rewritten'
                    rewritten = True

                # Attempt to download if the file does not exist or if the
                # file has been updated
                if rewritten or not downloaded:
                    try:
                        sys.stdout.flush()
                        ftp.retrbinary('RETR ' + fname,
                                       open(saved_fname, 'wb').write)
                        downloaded = True
                        logger.info('Downloaded file for ' + date.strftime('%x'))

                    except ftplib.error_perm as exception:
                        # Could not fetch, so cannot rewrite
                        rewritten = False

                        # Test for an error
                        if str(exception.args[0]).split(" ", 1)[0] != '550':
                            raise RuntimeError(exception)
                        else:
                            # file isn't actually there, try the next name
                            os.remove(saved_fname)

                            # Save this so we don't try again
                            # Because there are two possible filenames for
                            # each time, it's ok if one isn't there.  We just
                            # don't want to keep looking for it.
                            bad_fname.append(fname)

                # If the first file worked, don't try again
                if downloaded:
                    break

            if not downloaded:
                logger.info('File not available for {:}'.format(date.strftime('%x')))
            elif rewritten:
                with open(saved_fname, 'r') as fprelim:
                    lines = fprelim.read()

                rewrite_daily_file(date.year, outfile, lines)
                os.remove(saved_fname)

            # Cycle to the next date
            date = vend[iname] + pds.DateOffset(days=1)

        # Close connection after downloading all dates
        ftp.close()

    elif tag == 'daily':
        import requests
        logger.info('This routine can only download the latest 30 day file')

        # download webpage
        furl = 'https://services.swpc.noaa.gov/text/daily-solar-indices.txt'
        r = requests.get(furl)

        # Save the output
        outfile = os.path.join(data_path, 'f107_daily_' +
                               today.strftime('%Y-%m-%d') + '.txt')
        rewrite_daily_file(today.year, outfile, r.text)

    elif tag == 'forecast':
        import requests
        logger.info('This routine can only download the current forecast, not ' +
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
                                 date.strftime('%Y-%m-%d') + '.txt'),
                    header=True)

    elif tag == '45day':
        import requests
        logger.info('This routine can only download the current forecast, not ' +
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
        ap_times, ap = parse_45day_block(raw_ap)

        # parse the F10.7 data
        f107_times, f107 = parse_45day_block(raw_f107)

        # collect into DataFrame
        data = pds.DataFrame(f107, index=f107_times, columns=['f107'])
        data['ap'] = ap
        # write out as a file
        data.to_csv(os.path.join(data_path, 'f107_45day_' +
                                 date.strftime('%Y-%m-%d') + '.txt'),
                    header=True)

    return


def parse_45day_block(block_lines):
    """ Parse the data blocks used in the 45-day Ap and F10.7 Flux Forecast
    file

    Parameters
    ----------
    block_lines : list
        List of lines containing data in this data block

    Returns
    -------
    dates : list
        List of dates for each date/data pair in this block
    values : list
        List of values for each date/data pair in this block

    """

    # Initialize the output
    dates = list()
    values = list()

    # Cycle through each line in this block
    for line in block_lines:
        # Split the line on whitespace
        split_line = line.split()

        # Format the dates
        dates.extend([pysat.datetime.strptime(tt, "%d%b%y")
                      for tt in split_line[::2]])

        # Format the data values
        values.extend([int(vv) for vv in split_line[1::2]])

    return dates, values


def rewrite_daily_file(year, outfile, lines):
    """ Rewrite the SWPC Daily Solar Data files

    Parameters
    ----------
    year : int
        Year of data file (format changes based on date)
    outfile : str
        Output filename
    lines : str
        String containing all output data (result of 'read')

    """

    # get to the solar index data
    if year > 2000:
        raw_data = lines.split('#---------------------------------')[-1]
        raw_data = raw_data.split('\n')[1:-1]
        optical = True
    else:
        raw_data = lines.split('# ')[-1]
        raw_data = raw_data.split('\n')
        optical = False if raw_data[0].find('Not Available') or year == 1994 \
            else True
        istart = 7 if year < 2000 else 1
        raw_data = raw_data[istart:-1]

    # parse the data
    solar_times, data_dict = parse_daily_solar_data(raw_data, year, optical)

    # collect into DataFrame
    data = pds.DataFrame(data_dict, index=solar_times,
                         columns=data_dict.keys())

    # write out as a file
    data.to_csv(outfile, header=True)

    return


def parse_daily_solar_data(data_lines, year, optical):
    """ Parse the data in the SWPC daily solar index file

    Parameters
    ----------
    data_lines : list
        List of lines containing data
    year : list
        Year of file
    optical : boolean
        Flag denoting whether or not optical data is available

    Returns
    -------
    dates : list
        List of dates for each date/data pair in this block
    values : dict
        Dict of lists of values, where each key is the value name

    """

    # Initialize the output
    dates = list()
    val_keys = ['f107', 'ssn', 'ss_area', 'new_reg', 'smf', 'goes_bgd_flux',
                'c_flare', 'm_flare', 'x_flare', 'o1_flare', 'o2_flare',
                'o3_flare']
    optical_keys = ['o1_flare', 'o2_flare', 'o3_flare']
    xray_keys = ['c_flare', 'm_flare', 'x_flare']
    values = {kk: list() for kk in val_keys}

    # Cycle through each line in this file
    for line in data_lines:
        # Split the line on whitespace
        split_line = line.split()

        # Format the date
        dfmt = "%Y %m %d" if year > 1996 else "%d %b %y"
        dates.append(pysat.datetime.strptime(" ".join(split_line[0:3]), dfmt))

        # Format the data values
        j = 0
        for i, kk in enumerate(val_keys):
            if year == 1994 and kk == 'new_reg':
                # New regions only in files after 1994
                val = -999
            elif((year == 1994 and kk in xray_keys) or
                 (not optical and kk in optical_keys)):
                # X-ray flares in files after 1994, optical flares come later
                val = -1
            else:
                val = split_line[j + 3]
                j += 1

            if kk != 'goes_bgd_flux':
                if val == "*":
                    val = -999 if i < 5 else -1
                else:
                    val = int(val)
            values[kk].append(val)

    return dates, values


def calc_f107a(f107_inst, f107_name='f107', f107a_name='f107a', min_pnts=41):
    """ Calculate the 81 day mean F10.7

    Parameters
    ----------
    f107_inst : pysat.Instrument
        pysat Instrument holding the F10.7 data
    f107_name : str
        Data column name for the F10.7 data (default='f107')
    f107a_name : str
        Data column name for the F10.7a data (default='f107a')
    min_pnts : int
        Minimum number of points required to calculate an average (default=41)

    Returns
    -------
    Void : Updates f107_inst with F10.7a data

    Notes
    -----
    Will not pad data on its own

    """

    # Test to see that the input data is present
    if f107_name not in f107_inst.data.columns:
        raise ValueError("unknown input data column: " + f107_name)

    # Test to see that the output data does not already exist
    if f107a_name in f107_inst.data.columns:
        raise ValueError("output data column already exists: " + f107a_name)

    if f107_name in f107_inst.meta:
        fill_val = f107_inst.meta[f107_name][f107_inst.fill_label]
    else:
        fill_val = np.nan

    # Calculate the rolling mean.  Since these values are centered but rolling
    # function doesn't allow temporal windows to be calculated this way, create
    # a hack for this.
    #
    # Ensure the data are evenly sampled at a daily frequency, since this is
    # how often F10.7 is calculated.
    f107_fill = f107_inst.data.resample('1D').fillna(method=None)

    # Replace the time index with an ordinal
    time_ind = f107_fill.index
    f107_fill['ord'] = pds.Series([tt.toordinal() for tt in time_ind],
                                  index=time_ind)
    f107_fill.set_index('ord', inplace=True)

    # Calculate the mean
    f107_fill[f107a_name] = f107_fill[f107_name].rolling(window=81,
                                                         min_periods=min_pnts,
                                                         center=True).mean()

    # Replace the ordinal index with the time
    f107_fill['time'] = pds.Series(time_ind, index=f107_fill.index)
    f107_fill.set_index('time', inplace=True)

    # Resample to the original frequency, if it is not equal to 1 day
    freq = pysat.utils.time.calc_freq(f107_inst.index)
    if freq != "86400S":
        # Resample to the desired frequency
        f107_fill = f107_fill.resample(freq).pad()

        # Save the output in a list
        f107a = list(f107_fill[f107a_name])

        # Fill any dates that fall
        time_ind = pds.date_range(f107_fill.index[0], f107_inst.index[-1],
                                  freq=freq)
        for itime in time_ind[f107_fill.index.shape[0]:]:
            if (itime - f107_fill.index[-1]).total_seconds() < 86400.0:
                f107a.append(f107a[-1])
            else:
                f107a.append(fill_val)

        # Redefine the Series
        f107_fill = pds.DataFrame({f107a_name: f107a}, index=time_ind)

    # There may be missing days in the output data, remove these
    if f107_inst.index.shape < f107_fill.index.shape:
        f107_fill = f107_fill.loc[f107_inst.index]

    # Save the data
    f107_inst[f107a_name] = f107_fill[f107a_name]

    # Update the metadata
    meta_dict = {f107_inst.units_label: 'SFU',
                 f107_inst.name_label: 'F10.7a',
                 f107_inst.desc_label: "81-day centered average of F10.7",
                 f107_inst.plot_label: "F$_{10.7a}$",
                 f107_inst.axis_label: "F$_{10.7a}$",
                 f107_inst.scale_label: 'linear',
                 f107_inst.min_label: 0.0,
                 f107_inst.max_label: np.nan,
                 f107_inst.fill_label: fill_val,
                 f107_inst.notes_label: 'Calculated using data between ' +
                 '{:} and {:}'.format(f107_inst.index[0], f107_inst.index[-1])}

    f107_inst.meta[f107a_name] = meta_dict

    return
