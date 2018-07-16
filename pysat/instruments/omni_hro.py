# -*- coding: utf-8 -*-
"""Supports OMNI Combined, Definitive, IMF and Plasma Data, and Energetic
Proton Fluxes, Time-Shifted to the Nose of the Earth's Bow Shock, plus Solar
and Magnetic Indices. Downloads data from the NASA Coordinated Data Analysis
Web (CDAWeb). Supports both 5 and 1 minute files.

Parameters
----------
platform : string
    'omni'
name : string
    'hro'
tag : string
    Select time between samples, one of {'1min', '5min'}

Note
----
Files are stored by the first day of each month. When downloading use
omni.download(start, stop, freq='MS') to only download days that could possibly
have data.  'MS' gives a monthly start frequency.

This material is based upon work supported by the 
National Science Foundation under Grant Number 1259508. 

Any opinions, findings, and conclusions or recommendations expressed in this 
material are those of the author(s) and do not necessarily reflect the views 
of the National Science Foundation.


Warnings
--------
- Currently no cleaning routine. Though the CDAWEB description indicates that
  these level-2 products are expected to be ok.
- Module not written by OMNI team.

Custom Functions
-----------------
time_shift_to_magnetic_poles : Shift time from bowshock to intersection with
                               one of the magnetic poles
calculate_clock_angle : Calculate the clock angle and IMF mag in the YZ plane
calculate_imf_steadiness : Calculate the IMF steadiness using clock angle and
                           magnitude in the YZ plane
calculate_dayside_reconnection : Calculate the dayside reconnection rate
"""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import functools

import pandas as pds
import numpy as np

import pysat

platform = 'omni'
name = 'hro'
tags = {'1min':'1-minute time averaged data',
        '5min':'5-minute time averaged data'}
sat_ids = {'':['1min', '5min']}
test_dates = {'':{'1min':pysat.datetime(2009,1,1),
                  '5min':pysat.datetime(2009,1,1)}}


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
    """
    if format_str is None and data_path is not None:
        if (tag == '1min') | (tag == '5min'):
            min_fmt = ''.join(['omni_hro_', tag,
                               '{year:4d}{month:02d}{day:02d}_v01.cdf'])
            files = pysat.Files.from_os(data_path=data_path, format_str=min_fmt)
            # files are by month, just add date to monthly filename for
            # each day of the month. load routine will use date to select out
            # appropriate data
            if not files.empty:
                files.ix[files.index[-1] + pds.DateOffset(months=1) -
                         pds.DateOffset(days=1)] = files.iloc[-1]
                files = files.asfreq('D', 'pad')
                # add the date to the filename
                files = files + '_' + files.index.strftime('%Y-%m-%d')
            return files
        else:
            raise ValueError('Unknown tag')
    elif format_str is None:
        estr = 'A directory must be passed to the loading routine for OMNI HRO'
        raise ValueError (estr)
    else:
        return pysat.Files.from_os(data_path=data_path, format_str=format_str)
            

def load(fnames, tag=None, sat_id=None):
    import pysatCDF
    
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), None
    else:
        # pull out date appended to filename
        fname = fnames[0][0:-11]
        date = pysat.datetime.strptime(fnames[0][-10:], '%Y-%m-%d')
        with pysatCDF.CDF(fname) as cdf:
            data, meta = cdf.to_pysat()
            # pick out data for date
            data = data.ix[date:date+pds.DateOffset(days=1) -
                           pds.DateOffset(microseconds=1)] 
            return data, meta

def clean(omni):
    for fill_attr in ["fillval", "fill"]:
        # case insensitive check for attribute name
        if omni.meta.has_attr(fill_attr):
            # get real name
            fill_attr = omni.meta.attr_case_name(fill_attr)
            for key in omni.data.columns:
                if key != 'Epoch':    
                    idx, = np.where(omni[key] == omni.meta[key, fill_attr])
                    omni[idx, key] = np.nan
    return

def time_shift_to_magnetic_poles(inst):
    """ OMNI data is time-shifted to bow shock. Time shifted again
    to intersections with magnetic pole.

    Parameters
    -----------
    inst : Instrument class object
        Instrument with OMNI HRO data

    Notes
    ---------
    Time shift calculated using distance to bow shock nose (BSN)
    and velocity of solar wind along x-direction.
    
    Warnings
    --------
    Use at own risk.
    
    """
    
    # need to fill in Vx to get an estimate of what is going on
    inst['Vx'] = inst['Vx'].interpolate('nearest')
    inst['Vx'] = inst['Vx'].fillna(method='backfill')
    inst['Vx'] = inst['Vx'].fillna(method='pad')

    inst['BSN_x'] = inst['BSN_x'].interpolate('nearest')
    inst['BSN_x'] = inst['BSN_x'].fillna(method='backfill')
    inst['BSN_x'] = inst['BSN_x'].fillna(method='pad')

    # make sure there are no gaps larger than a minute
    inst.data = inst.data.resample('1T').interpolate('time')

    time_x = inst['BSN_x']*6371.2/-inst['Vx']
    idx, = np.where(np.isnan(time_x))
    if len(idx) > 0:
        print (time_x[idx])
        print (time_x)
    time_x_offset = [pds.DateOffset(seconds = time)
                     for time in time_x.astype(int)]
    new_index=[]
    for i, time in enumerate(time_x_offset):
        new_index.append(inst.data.index[i] + time)
    inst.data.index = new_index
    inst.data = inst.data.sort_index()    
    
    return

def download(date_array, tag, sat_id='', data_path=None, user=None,
             password=None):
    """ download OMNI data, layout consistent with pysat

    Parameters
    -----------
    data_array : np.array
    tag : string
        String denoting the type of file to load, accepted values are '1min' and
       '5min'
    sat_id : string
        Not used (default='')
    data_path : string or NoneType
        Data path to save downloaded files to (default=None)
    user : string or NoneType
        Not used, CDAWeb allows anonymous users (default=None)
    password : string or NoneType
        Not used, CDAWeb provides password (default=None)
    """
    import os
    import ftplib

    ftp = ftplib.FTP('cdaweb.gsfc.nasa.gov')   # connect to host, default port
    ftp.login()               # user anonymous, passwd anonymous@
    
    if (tag == '1min') | (tag == '5min'):
        ftp.cwd('/pub/data/omni/omni_cdaweb/hro_'+tag)
    
        for date in date_array:
            fname = '{year1:4d}/omni_hro_' + tag + \
                    '_{year2:4d}{month:02d}{day:02d}_v01.cdf'
            fname = fname.format(year1=date.year, year2=date.year,
                                 month=date.month, day=date.day)
            local_fname = ''.join(['omni_hro_', tag, \
            '_{year:4d}{month:02d}{day:02d}_v01.cdf']).format(year=date.year, \
                                                month=date.month, day=date.day)
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
                    print('File not available for '+ date.strftime('%D'))
    ftp.close()
    # ftp.quit()
    return

def calculate_clock_angle(inst):
    """ Calculate IMF clock angle and magnitude of IMF in GSM Y-Z plane

    Parameters
    -----------
    inst : pysat.Instrument
        Instrument with OMNI HRO data
    """
    
    # Calculate clock angle in degrees
    clock_angle = np.degrees(np.arctan2(inst['BY_GSM'], inst['BZ_GSM']))
    clock_angle[clock_angle < 0.0] += 360.0
    inst['clock_angle'] = pds.Series(clock_angle, index=inst.data.index)

    # Calculate magnitude of IMF in Y-Z plane
    inst['BYZ_GSM'] = pds.Series(np.sqrt(inst['BY_GSM']**2 +
                                         inst['BZ_GSM']**2),
                                       index=inst.data.index)

    return

def calculate_imf_steadiness(inst, steady_window=15, min_window_frac=0.75,
                             max_clock_angle_std=90.0/np.pi, max_bmag_cv=0.5):
    """ Calculate IMF steadiness using clock angle standard deviation and
    the coefficient of variation of the IMF magnitude in the GSM Y-Z plane

    Parameters
    -----------
    inst : pysat.Instrument
        Instrument with OMNI HRO data
    steady_window : int
        Window for calculating running statistical moments in min (default=15)
    min_window_frac : float
        Minimum fraction of points in a window for steadiness to be calculated
        (default=0.75)
    max_clock_angle_std : float
        Maximum standard deviation of the clock angle in degrees (default=22.5)
    max_bmag_cv : float
        Maximum coefficient of variation of the IMF magnitude in the GSM
        Y-Z plane (default=0.5)
    """

    # We are not going to interpolate through missing values
    sample_rate = int(inst.tag[0])
    max_wnum = np.floor(steady_window / sample_rate)
    if max_wnum != steady_window / sample_rate:
        steady_window = max_wnum * sample_rate
        print("WARNING: sample rate is not a factor of the statistical window")
        print("new statistical window is {:.1f}".format(steady_window))

    min_wnum = int(np.ceil(max_wnum * min_window_frac))

    # Calculate the running coefficient of variation of the BYZ magnitude
    byz_mean = inst['BYZ_GSM'].rolling(min_periods=min_wnum, center=True,
                                       window=steady_window).mean()
    byz_std = inst['BYZ_GSM'].rolling(min_periods=min_wnum, center=True,
                                      window=steady_window).std()
    inst['BYZ_CV'] = pds.Series(byz_std / byz_mean, index=inst.data.index)

    # Calculate the running circular standard deviation of the clock angle
    circ_kwargs = {'high':360.0, 'low':0.0}
    ca = inst['clock_angle'][~np.isnan(inst['clock_angle'])]
    ca_std = inst['clock_angle'].rolling(min_periods=min_wnum,
                                         window=steady_window, \
                center=True).apply(pysat.utils.nan_circstd, kwargs=circ_kwargs)
    inst['clock_angle_std'] = pds.Series(ca_std, index=inst.data.index)

    # Determine how long the clock angle and IMF magnitude are steady
    imf_steady = np.zeros(shape=inst.data.index.shape)

    steady = False
    for i,cv in enumerate(inst.data['BYZ_CV']):
        if steady:
            del_min = int((inst.data.index[i] -
                           inst.data.index[i-1]).total_seconds() / 60.0)
            if np.isnan(cv) or np.isnan(ca_std[i]) or del_min > sample_rate:
                # Reset the steadiness flag if fill values are encountered, or
                # if an entry is missing
                steady = False

        if cv <= max_bmag_cv and ca_std[i] <= max_clock_angle_std:
            # Steadiness conditions have been met
            if steady:
                imf_steady[i] = imf_steady[i-1]

            imf_steady[i] += sample_rate
            steady = True

    inst['IMF_Steady'] = pds.Series(imf_steady, index=inst.data.index)
    return

def calculate_dayside_reconnection(inst):
    """ Calculate the dayside reconnection rate (Milan et al. 2014)

    Parameters
    -----------
    inst : pysat.Instrument
        Instrument with OMNI HRO data, requires BYZ_GSM and clock_angle

    Notes
    --------
    recon_day = 3.8 Re (Vx / 4e5 m/s)^1/3 Vx B_yz (sin(theta/2))^9/2
    """
    rearth = 6371008.8
    sin_htheta = np.power(np.sin(np.radians(0.5 * inst['clock_angle'])), 4.5)
    byz = inst['BYZ_GSM'] * 1.0e-9
    vx = inst['flow_speed'] * 1000.0
    
    recon_day = 3.8 * rearth * vx * byz * sin_htheta * np.power((vx / 4.0e5),
                                                                1.0/3.0)
    inst['recon_day'] = pds.Series(recon_day, index=inst.data.index)
    return

