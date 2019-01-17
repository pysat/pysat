# -*- coding: utf-8 -*-.
"""Provides default routines for solar wind and geospace indices

"""

from __future__ import print_function
from __future__ import absolute_import

import pandas as pds
import numpy as np
import pysat

def combine_kp(standard_inst=None, recent_inst=None, forecast_inst=None,
               start=None, stop=None):
    """ Combine the output from the different Kp sources for a range of dates

    Parameters
    ----------
    standard_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and '' tag or None to exclude (default=None)
    recent_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and 'recent' tag or None to exclude (default=None)
    forecast_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and 'forecast' tag or None to exclude (default=None)
    start : (dt.datetime or NoneType)
        Starting time for combining data, or None to use earliest loaded
        date from the pysat Instruments (default=None)
    stop : (dt.datetime)
        Ending time for combining data, or None to use the latest loaded date
        from the pysat Instruments (default=None)

    Returns
    -------
    kp_inst : (pysat.Instrument)
        Instrument object containing Kp observations for the desired period of
        time, merging the standard, recent, and forecasted values based on
        their reliability

    Notes
    -----
    Merging prioritizes the standard data, then the recent data, and finally
    the forecast data

    Will not attempt to download any missing data, but will load data

    """

    # Create an ordered list of the Instruments, excluding any that are None
    all_inst = list()
    tag = 'combined'
    inst_flag = None
    if standard_inst is not None:
        all_inst.append(standard_inst)
        tag += '_standard'
        if inst_flag is None:
            inst_flag = 'standard'

    if recent_inst is not None:
        all_inst.append(recent_inst)
        tag += '_recent'
        if inst_flag is None:
            inst_flag = 'recent'

    if forecast_inst is not None:
        all_inst.append(forecast_inst)
        tag += '_forecast'
        if inst_flag is None:
            inst_flag = 'forecast'

    if len(all_inst) < 2:
        raise ValueError("need at two Kp Instrument objects to combine them")

    # If the start or stop times are not defined, get them from the Instruments
    if start is None:
        stimes = [inst.index.min() for inst in all_inst if len(inst.index) > 0]
        start = min(stimes) if len(stimes) > 0 else None

    if stop is None:
        stimes = [inst.index.max() for inst in all_inst if len(inst.index) > 0]
        stop = max(stimes) if len(stimes) > 0 else None

    if start is None or stop is None:
        raise ValueError("must either load in Instrument objects or provide" +
                         " starting and ending times")

    print("TEST", start, stop, tag, inst_flag)

    # Initialize the output instrument
    kp_inst = pysat.Instrument()
    kp_inst.platform = all_inst[0].platform
    kp_inst.name = all_inst[0].name
    kp_inst.tag = tag
    kp_inst.date = start
    kp_inst.doy = int(start.strftime("%j"))
    kp_inst.meta = all_inst[0].meta['Kp']

    kp_times = list()
    kp_values = list()

    # Cycle through the desired time range
    itime = start
    while itime < stop and inst_flag is not None:
        print("TEST", itime, stop, inst_flag, len(kp_times), len(kp_values))
        
        # Load and save the standard data for as many times as possible
        if inst_flag == 'standard':
            standard_inst.load(date=itime)

            if len(standard_inst.index) == 0:
                inst_flag = 'forecast' if recent_inst is None else 'recent'
            else:
                kp_times.extend(list(standard_inst.index))
                kp_values.extend(list(standard_inst['Kp']))
                itime += pds.DateOffset(days=1)

        # Load and save the recent data for as many times as possible
        if inst_flag == 'recent':
            # Determine which files should be loaded
            if len(recent_inst.index) == 0:
                files = np.unique(recent_inst.files.files[itime:stop])
            else:
                files = [None] # No load needed, if already initialized

            # Cycle through all possible files of interest, saving relevant data
            for filename in files:
                if filename is not None:
                    recent_inst.load(fname=filename)

                # Determine which times to save
                fill_val = recent_inst.meta['Kp'].fill
                good_times = recent_inst.index >= itime
                good_vals = recent_inst['Kp'][good_times] != fill_val

                # Save output data and cycle time
                kp_times.extend(list(recent_inst.index[good_times][good_vals]))
                kp_values.extend(list(recent_inst['Kp'][good_times][good_vals]))
                itime = kp_times[-1].date() + pds.DateOffset(days=1)

            inst_flag = 'forecast' if forecast_inst is not None else None

        # Load and save the forecast data for as many times as possible
        if inst_flag == "forecast":
            # Determine which files should be loaded
            if len(forecast_inst.index) == 0:
                files = np.unique(forecast_inst.files.files[itime:stop])
            else:
                files = [None] # No load needed, if already initialized

            # Cycle through all possible files of interest, saving relevant data
            for filename in files:
                if filename is not None:
                    forecast_inst.load(fname=filename)

                # Determine which times to save
                fill_val = forecast_inst.meta['Kp'].fill
                good_times = forecast_inst.index >= itime
                good_vals = forecast_inst['Kp'][good_times] != fill_val

                # Save desired data and cycle time
                kp_times.extend(list(forecast_inst.index[good_times][good_vals]))
                kp_values.extend(list(forecast_inst['Kp'][good_times][good_vals]))
                itime = kp_times[-1].date() + pds.DateOffset(days=1)

            inst_flag = None

    # Determine if the beginning or end of the time series needs to be padded
    fill_val = kp_inst.meta['Kp'].fill
    del_time = (kp_times[1:] - kp_times[:-1]).min()
    freq = "{:.0f}S".format(del_time.total_seconds())
    date_range = pds.date_range(start=start, end=stop, freq=freq)

    if date_range[0] < kp_times[0]:
        # Extend the time and value arrays from their beginning with fill values
        itime = abs(date_range - kp_times[0]).argmin()
        kp_times.reverse()
        kp_values.reverse()
        extend_times = list(date_range[:itime])
        extend_times.reverse()
        kp_times.extend(extend_times)
        kp_values.extend([fill_val for kk in extend_times])
        kp_times.reverse()
        kp_values.reverse()

    if date_range[-1] > kp_times[-1]:
        # Extend the time and value arrays from their end with fill values
        itime = abs(date_range - kp_times[-1]).argmin() + 1
        extend_times = list(date_range[itime:])
        kp_times.extend(extend_times)
        kp_values.extend([fill_val for kk in extend_times])

    # Save output data
    kp_inst.data = pds.DataFrame(kp_values, columns=['Kp'], index=kp_times)

    # Resample the output data, filling missing values
    if(date_range.shape != kp_inst.index.shape or
       abs(date_range - kp_inst.index).max().total_seconds() > 0.0):
        kp_inst.data = kp_inst.data.resample(freq).fillna(value=fill_val)

    return kp_inst
