# -*- coding: utf-8 -*-
"""Supports Dst values. Downloads data from NGDC.

Properties
----------
platform
    'sw'
name
    'dst'
tag
    None supported

Note
----
Will only work until 2057.

Download method should be invoked on a yearly frequency,
dst.download(date1, date2, freq='AS')

This material is based upon work supported by the
National Science Foundation under Grant Number 1259508.

Any opinions, findings, and conclusions or recommendations expressed in this
material are those of the author(s) and do not necessarily reflect the views
of the National Science Foundation.

"""

import os
import pandas as pds
import numpy as np

import pysat

import logging
logger = logging.getLogger(__name__)

platform = 'sw'
name = 'dst'
tags = {'': ''}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(2007, 1, 1)}}


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

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    data = pds.DataFrame()

    for filename in fnames:
        # need to remove date appended to dst filename
        fname = filename[0:-11]
        # f = open(fname)
        with open(fname) as f:
            lines = f.readlines()
            idx = 0
            # check if all lines are good
            max_lines = 0
            for line in lines:
                if len(line) > 1:
                    max_lines += 1
            yr = np.zeros(max_lines * 24, dtype=int)
            mo = np.zeros(max_lines * 24, dtype=int)
            day = np.zeros(max_lines * 24, dtype=int)
            ut = np.zeros(max_lines * 24, dtype=int)
            dst = np.zeros(max_lines * 24, dtype=int)
            for line in lines:
                if len(line) > 1:
                    temp_year = int(line[14:16] + line[3:5])
                    if temp_year > 57:
                        temp_year += 1900
                    else:
                        temp_year += 2000

                    yr[idx:idx + 24] = temp_year
                    mo[idx:idx + 24] = int(line[5:7])
                    day[idx:idx + 24] = int(line[8:10])
                    ut[idx:idx + 24] = np.arange(24)
                    temp = line.strip()[20:-4]
                    temp2 = [temp[4 * i:4 * (i + 1)] for i in np.arange(24)]
                    dst[idx:idx + 24] = temp2
                    idx += 24

            # f.close()

            start = pds.datetime(yr[0], mo[0], day[0], ut[0])
            stop = pds.datetime(yr[-1], mo[-1], day[-1], ut[-1])
            dates = pds.date_range(start, stop, freq='H')

            new_data = pds.DataFrame(dst, index=dates, columns=['dst'])
            # pull out specific day
            new_date = pysat.datetime.strptime(filename[-10:], '%Y-%m-%d')
            idx, = np.where((new_data.index >= new_date) &
                            (new_data.index < new_date+pds.DateOffset(days=1)))
            new_data = new_data.iloc[idx, :]
            # add specific day to all data loaded for filenames
            data = pds.concat([data, new_data], sort=True, axis=0)

    return data, pysat.Meta()


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : string or NoneType
        Denotes type of file to load.  Accepted types are '1min' and '5min'.
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
            # files are by year, going to add date to yearly filename for
            # each day of the month. The load routine will load a month of
            # data and use the appended date to select out appropriate data.
            if format_str is None:
                format_str = 'dst{year:4d}.txt'
            out = pysat.Files.from_os(data_path=data_path,
                                      format_str=format_str)
            if not out.empty:
                out.loc[out.index[-1] + pds.DateOffset(years=1)
                        - pds.DateOffset(days=1)] = out.iloc[-1]
                out = out.asfreq('D', 'pad')
                out = out + '_' + out.index.strftime('%Y-%m-%d')
            return out
        else:
            raise ValueError(''.join(('Unrecognized tag name for Space ',
                                      'Weather Dst Index')))
    else:
        raise ValueError(''.join(('A data_path must be passed to the loading ',
                                  'routine for Dst')))


def download(date_array, tag, sat_id, data_path, user=None, password=None):
    """Routine to download Dst index data

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

    Notes
    -----
    Called by pysat. Not intended for direct use by user.

    """

    import ftplib
    from ftplib import FTP
    import sys
    ftp = FTP('ftp.ngdc.noaa.gov')   # connect to host, default port
    ftp.login()               # user anonymous, passwd anonymous@
    ftp.cwd('/STP/GEOMAGNETIC_DATA/INDICES/DST')

    for date in date_array:
        fname = 'dst{year:02d}.txt'
        fname = fname.format(year=date.year)
        local_fname = fname
        saved_fname = os.path.join(data_path, local_fname)
        try:
            logger.info('Downloading file for '+date.strftime('%D'))
            sys.stdout.flush()
            ftp.retrbinary('RETR ' + fname, open(saved_fname, 'wb').write)
        except ftplib.error_perm as exception:
            # if exception[0][0:3] != '550':
            if str(exception.args[0]).split(" ", 1)[0] != '550':
                raise
            else:
                os.remove(saved_fname)
                logger.info('File not available for ' + date.strftime('%D'))

    ftp.close()
    return
