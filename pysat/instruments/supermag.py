# -*- coding: utf-8 -*-
"""Supports SuperMAG ground magnetometer measurements and SML/SMU indices.
Downloading is not currently supported; please use the SuperMAG interface:
    http://supermag.jhuapl.edu/mag/
and follow their rules of the road:
    http://supermag.jhuapl.edu/info/?page=rulesoftheroad

Parameters
----------
platform : string
    'supermag'
name : string
    'magnetometer'
tag : string
    Select  {'indices', None}

Note
----
Files must be downloaded from the website, and is freely available after
registration.

This material is based upon work supported by the 
National Science Foundation under Grant Number 1259508. 

Any opinions, findings, and conclusions or recommendations expressed in this 
material are those of the author(s) and do not necessarily reflect the views 
of the National Science Foundation.


Warnings
--------
- Currently no cleaning routine, though the SuperMAG description indicates that
  these products are expected to be good.  More information about the processing
  is available 
- Module not written by the SuperMAG team.

Custom Functions
-----------------
                           
"""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import functools

import pandas as pds
import numpy as np

import pysat

platform = 'supermag'
name = 'magnetometer'
tags = {'indices':'SMU and SML indices',
        None:'magnetometer measurements',
        'all':'magnetometer measurements and indices'}
sat_ids = {'':tags.keys()}
test_dates = {'':{kk:pysat.datetime(2009,1,1) for kk in tags.keys()}}


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen SuperMAG data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        and None (for just magnetometer measurements). (default=None)
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
        if (tag == 'indices') | (tag is None) | (tag == 'all'):
            min_fmt = ''.join(['????????-??-??-supermag.txt'])
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
        estr = 'A directory must be passed to the loading routine for SuperMAG'
        raise ValueError (estr)
    else:
        return pysat.Files.from_os(data_path=data_path, format_str=format_str)
            

def load(fnames, tag=None, sat_id=None, file_type="ascii"):
    """ Load the SuperMAG files

    Parameters
    -----------
    fnames : (list)
        List of filenames
    tag : (str or NoneType)
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        and None (for just magnetometer measurements). (default=None)
    sat_id : (str or NoneType)
        Satellite ID for constellations, not used. (default=None)
    file_type : (str)
        Specifies if file is ascii or csv (default='ascii')

    Returns
    --------
    data : (pandas.DataFrame)
        Object containing satellite data
    meta : (pysat.Meta)
        Object containing metadata such as column names and units
    """
    baseline = list()

    # Ensure that there are files to load
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), pysat.Meta(None)

    # Open and load the files for each file type
    if file_type.lower() == "csv":
        if tag == "indices":
            return pysat.DataFrame(None), pysat.Meta(None)
        else:
            data = load_csv_data(fnames)
    else:
        data, baseline = load_ascii_data(fnames, tags)

    # If data was loaded, update the meta data
    if len(data.columns) > 0:
        meta = pysat.Meta()
        for cc in data.columns:
            meta[cc] = update_smag_metadata(cc)

        meta['baseline'] = format_baseline_list(baseline)
    else:
        meta = pysat.Meta(None)

    return data, meta

def load_csv_data(fnames):
    """Load data from comma separated SuperMAG files

    Parameters
    ------------
    fnames : (list)
        List of CSV SuperMAG files

    Returns
    --------
    data : (pandas.DataFrame)
        Pandas DataFrame
    """
    # Define the date parser
    def parse_smag_date(dd):                                               
        return dt.datetime.strptime(dd, "%Y-%m-%d %H:%M:%S")

    # Ensure that the files are in a list
    if isinstance(fnames, basestring):
        fnames = [fnames]

    # Cycle through the files and load them into a data frame
    data = pds.DataFrame()
    for fname in fnames:
        temp = pds.read_csv(fname, parse_dates={'datetime':[0]},
                            date_parser=parse_smag_date, index_col='datetime')
        data = pds.concat([data, temp], axis=0)

    return data
            
def load_ascii_data(fnames, tag):
    """Load data from comma separated SuperMAG files

    Parameters
    ------------
    fnames : (list)
        List of CSV SuperMAG files
    tag : (str)
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        and None (for just magnetometer measurements). (default=None)

    Returns
    --------
    data : (pandas.DataFrame)
        Pandas DataFrame
    baseline : (list)
        List of strings denoting the presence of a standard and file-specific
        baselines for each file
    """
    ndata = {"indices":2, None:4, 'date':7}
    dkeys = [ 'IAGA', 'N', 'E', 'Z']

    # Ensure that the tag indicates a type of data we know how to load
    if not tag in ndata.keys():
        return pysat.DataFrame(None)

    # Ensure that the files are in a list
    if isinstance(fnames, basestring):
        fnames = [fnames]

    # Initialise the output data
    data = pds.DataFrame()
    baseline = list()

    # Cycle through the files and load them
    for fname in fnames:
        # Read in the text data, processing the header, indices, and
        # magnetometer data (as desired)
        try:
            fopen = open(fname, "r")

            # Set the processing flags
            hflag = True  # header lines
            pflag = False # parameter line
            dflag = True  # date line
            snum = 0      # number of magnetometer stations
            ddict = dict()

            for fline in fopen.readlines():
                # Cycle past the header
                line_len = len(fline)
                if hflag:
                    if pflag:
                        pflag = False # Unset the flag
                        if fline.find("-mlt") > 0:
                            ndata[None] += 2
                            dkeys.extend(['MLT', 'MLAT'])
                        if fline.find("-sza") > 0:
                            ndata[None] += 1
                            dkeys.append('SZA')
                        if fline.find("-decl") > 0:
                            ndata[None] += 1
                            dkeys.append('IGRF_DECL')
                        if tag == "indices" and fline.find("-envelope") < 0:
                            # Indices not included in this file
                            break

                        # Save the baseline information
                        lsplit = fline.split()
                        idelta = lsplit.index('-delta') + 1
                        ibase = lsplit.index('-baseline') + 1
                        isd = lsplit.index('-sd') + 1
                        ist = lsplit.index('-st') + 1
                        iex = lsplit.index('-ex') + 1
                        bline = " ".join([lsplit[ibase], lsplit[idelta],
                                          lsplit[isd], lsplit[ist],
                                          lsplit[iex]])
                        baseline.append(bline)
                    if fline.find("Selected parameters:") >= 0:
                        pflag = True
                    if fline.count("=") == line_len - 1 and line_len > 2:
                        hflag = False
                else:
                    # Load the desired data
                    lsplit = fline.split()

                    if dflag:
                        dflag = False # Unset the date flag
                        dstring = " ".join(lsplit[:6])
                        dtime = dt.datetime.strptime(dstring,
                                                     "%Y %m %d %H %M %S")
                        snum = int(lsplit[6])
                    elif lsplit == ndata['indices']:
                        if tag is not None:
                            if lsplit[0] not in ddict.keys():
                                ddict[lsplit[0]] = list()
                            ddict[lsplit[0]].append(int(lsplit[1]))
                    elif lsplit == ndata[None]:
                        snum -= 1
                        if len(ddict.keys()) < 4:
                            for kk in dkeys:
                                ddict[kk] = list()
                        for i,kk in enumerate(dkeys):
                            if i == 0:
                                ddict[kk].append(lsplit[i])
                            else:
                                ddict[kk].append(float(lsplit[i]))

                    if snum == 0 and len(ddict.keys()) >= 2 > :
                        # The previous value was the last value, prepare for
                        # next block
                        if 'datetime' not in ddict.keys():
                            ddict['datetime'] = list()
                        ddict['datetime'].extend([dtime
                                                  for i in ddict.values()[0]])
                        dflag = True

            # Close the file
            fopen.close()

            # Create a data frame for this file
            temp = pds.DataFrame(ddict, index=ddict['datetime'],
                                 columns=ddict.keys())

            # Save the data in a DataFrame for all files
            data = pds.concat([data, temp], axis=0)
            del temp, ddict
        except:
            print("Unable to load file [{:s}]".format(fname))

    return data, baseline

def update_smag_metadata(col_name):
    """Update SuperMAG metadata

    Parameters
    -----------
    col_name : (str)
        Data column name

    Returns
    --------
    col_dict : (dict)
       Dictionary of strings detailing the units and long-form name of the data
    """

    smag_units = {'IAGA':'none', 'N':'nT', 'E':'nT', 'Z':'nT', 'MLT':'hours',
                  'MLAT':'degrees', 'SZA':'degrees', 'IGRF_DECL':'degrees',
                  'SMU':'none', 'SML':'none'}
    smag_name = {'IAGA':'Station Code', 'N':'B along local magnetic North',
                 'E':'B along local magnetic East', 'Z':'B vertically downward',
                 'MLT':'Magnetic Local Time', 'MLAT':'Magnetic Latitude',
                 'SZA':'Solar Zenith Angle',
                 'IGRF_DECL':'IGRF magnetic declination',
                 'SMU': 'Maximum eastward auroral electrojets strength.\n'
                 'Upper envelope of N-component for stations between 40 and '
                 '80 degrees magnetic north.',
                 'SML':'Maximum westward auroral electrojets strength.\n'
                 'Lower envelope of N-component for stations between 40 and 80'
                 ' degrees magnetic north.'}

    col_dict = {'units':smag_units[col_name], 'long_name':smag_name[col_name]}

    return col_dict

def format_baseline_list(baseline_list):
    """Format the list of baseline information from the loaded files into a
    cohesive, informative string

    Parameters
    ------------
    baseline_list : (list)
        List of strings specifying the baseline information for each
        SuperMAG file

    Returns
    ---------
    base_string : (str)
        Single string containing the relevent data
    """

    uniq_base = dict()
    uniq_delta = dict()

    for bline in baseline_list:
        bsplit = bline.split()
        bdate = " ".join(bsplit[2:])
        if bsplit[0] not in uniq_base.keys():
            uniq_base[bsplit[0]] = ""
        if bsplit[1] not in uniq_delta.keys():
            uniq_delta[bsplit[1]] = ""

        uniq_base[bsplit[0]] += "{:s}, ".format(bdate)
        uniq_base[bsplit[1]] += "{:s}, ".format(bdate)

    if len(uniq_base.keys()) == 1:
        base_string = "Baseline {:s}".format(uniq_base.keys()[0])
    else:
        base_string = "Baseline "

        for i,kk in enumerate(uniq_base.keys()):
            if i == 1:
                base_string += "{:s}: {:s}".format(kk, uniq_base[kk][:-2])
            else:
                base_string += "         {:s}: {:s}".format(kk,
                                                            uniq_base[kk][:-2])

    if len(uniq_delta.keys()) == 1:
        base_string += "\nDelta    {:s}".format(uniq_delta.keys()[0])
    else:
        base_string += "\nDelta    "

        for i,kk in enumerate(uniq_delta.keys()):
            if i == 1:
                base_string += "{:s}: {:s}".format(kk, uniq_delta[kk][:-2])
            else:
                base_string += "         {:s}: {:s}".format(kk,
                                                            uniq_delta[kk][:-2])
    return base_string

def clean(supermag):
    for key in supermag.data.columns:
        if key != 'Epoch':
            fill_attr = "fillval"
            if not hasattr(supermag.meta[key], fill_attr):
                if hasattr(supermag.meta[key], fill_attr.upper()):
                    fill_attr = fill_attr.upper()
                else:
                    raise "unknown attribute {:s} or {:s}".format(fill_attr, \
                                                            fill_attr.upper())

            idx, = np.where(supermag[key] == getattr(supermag.meta[key],
                                                     fill_attr))
            supermag[idx, key] = np.nan
    return

def download(date_array, tag, sat_id='', data_path=None, user=None,
             password=None):
    """NOT AVAILABLE.  Would contain routine to download SuperMAG data

    Parameters
    -----------
    date_array : np.array
        Array of datetime objects
    tag : string
        String denoting the type of file to load, accepted values are 'indices',
        'all' and None
    sat_id : string
        Not used (default='')
    data_path : string or NoneType
        Data path to save downloaded files to (default=None)
    user : string or NoneType
        Not used (default=None)
    password : string or NoneType
        Not used (default=None)
    """

    return
