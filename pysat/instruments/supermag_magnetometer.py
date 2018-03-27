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

from __future__ import print_function, absolute_import
import pandas as pds
import numpy as np
from os import path

import pysat

platform = 'supermag'
name = 'magnetometer'
tags = {'indices':'SMU and SML indices',
        None:'magnetometer measurements',
        'all':'magnetometer measurements and indices'}
sat_ids = {'':tags.keys()}
test_dates = {'':{kk:pysat.datetime(2009,1,1) for kk in tags.keys()}}

def init(self):
    """
    """

    return

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
        file_base = 'supermag_magnetometer'
        if tag == "indices" or tag == "all":
            file_base += '_all' # Can't just download indices

            if tag == "indices":
                psplit = path.split(data_path[:-1])
                data_path = path.join(psplit[0], "all", "")

        min_fmt = '_'.join([file_base, '{year:4d}{month:02d}{day:02d}.???'])
        files = pysat.Files.from_os(data_path=data_path, format_str=min_fmt)
        # files may consist of an arbitraty amount of time, specify the starting
        # date for now.  Currently assumes 1 month of data.
        if not files.empty:
            files.ix[files.index[-1] + pds.DateOffset(months=1) -
                     pds.DateOffset(days=1)] = files.iloc[-1]
            files = files.asfreq('D', 'pad')
            # add the date to the filename
            files = files + '_' + files.index.strftime('%Y-%m-%d')
        return files
    elif format_str is None:
        estr = 'A directory must be passed to the loading routine for SuperMAG'
        raise ValueError (estr)
    else:
        return pysat.Files.from_os(data_path=data_path, format_str=format_str)
            

def load(fnames, tag=None, sat_id=None):
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

    Returns
    --------
    data : (pandas.DataFrame)
        Object containing satellite data
    meta : (pysat.Meta)
        Object containing metadata such as column names and units
    """
    # Ensure that there are files to load
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), pysat.Meta(None)

    # Ensure that the files are in a list
    if isinstance(fnames, basestring):
        fnames = [fnames]

    # Initialise the output data
    data = pds.DataFrame()
    baseline = list()

    # Cycle through the files
    for fname in fnames:
        fname = fname[:-11] # Remove date index from end of filename
        file_type = path.splitext(fname)[1].lower()

        # Open and load the files for each file type
        if file_type == ".csv":
            if tag != "indices":
                temp = load_csv_data(fname)
        else:
            temp, bline = load_ascii_data(fname, tag)

            if bline is not None:
                baseline.append(bline)

        # Save the loaded data in the output data structure
        if len(temp.columns) > 0:
            data = pds.concat([data, temp], axis=0)
        del temp

    # If data was loaded, update the meta data
    if len(data.columns) > 0:
        meta = pysat.Meta()
        for cc in data.columns:
            meta[cc] = update_smag_metadata(cc)

        meta.info = {'baseline':format_baseline_list(baseline)}
    else:
        meta = pysat.Meta(None)

    return data, meta

def load_csv_data(fname):
    """Load data from a comma separated SuperMAG file

    Parameters
    ------------
    fname : (str)
        CSV SuperMAG file name

    Returns
    --------
    data : (pandas.DataFrame)
        Pandas DataFrame
    """
    # Define the date parser
    def parse_smag_date(dd):                                               
        return pysat.datetime.strptime(dd, "%Y-%m-%d %H:%M:%S")

    # Cycle through the files and load them into a data frame
    data = pds.read_csv(fname, parse_dates={'datetime':[0]},
                        date_parser=parse_smag_date, index_col='datetime')

    return data
            
def load_ascii_data(fname, tag):
    """Load data from a self-documenting ASCII SuperMAG file

    Parameters
    ------------
    fname : (str)
        ASCII SuperMAG filename
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
    ndata = {"indices":2, None:4, 'date':7, "all":4}
    dkeys = [ 'IAGA', 'N', 'E', 'Z']
    data = pds.DataFrame(None)
    baseline = None

    # Ensure that the tag indicates a type of data we know how to load
    if not tag in ndata.keys():
        return data, baseline

    # Read in the text data, processing the header, indices, and
    # magnetometer data (as desired)
    with open(fname, "r") as fopen:
        # Set the processing flags
        hflag = True  # header lines
        pflag = False # parameter line
        dflag = True  # date line
        snum = 0      # number of magnetometer stations
        ddict = dict()
        date_list = list()

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
                    baseline = " ".join([lsplit[ibase], lsplit[idelta],
                                         lsplit[isd], lsplit[ist], lsplit[iex]])

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
                    dtime = pysat.datetime.strptime(dstring,
                                                    "%Y %m %d %H %M %S")
                    snum = int(lsplit[6])

                    # Load the times
                    if tag == "indices":
                        date_list.append(dtime)
                    else:
                        date_list.extend([dtime for i in range(snum)])
                elif len(lsplit) == ndata['indices']:
                    if tag is not None:
                        if lsplit[0] not in ddict.keys():
                            ddict[lsplit[0]] = list()

                        if tag == "indices":
                            ddict[lsplit[0]].append(int(lsplit[1]))
                        else:
                            # This works because indices occur before
                            # magnetometer measurements
                            ddict[lsplit[0]].extend([int(lsplit[1])
                                                     for i in range(snum)])
                elif len(lsplit) == ndata[None]:
                    snum -= 1
                    if tag != "indices":
                        if len(ddict.keys()) < 4:
                            for kk in dkeys:
                                ddict[kk] = list()
                        for i,kk in enumerate(dkeys):
                            if i == 0:
                                ddict[kk].append(lsplit[i])
                            else:
                                ddict[kk].append(float(lsplit[i]))

                if snum == 0 and len(ddict.keys()) >= 2:
                    # The previous value was the last value, prepare for
                    # next block
                    dflag = True

        # Create a data frame for this file
        data = pds.DataFrame(ddict, index=date_list,
                             columns=ddict.keys())

        fopen.close()

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
                  'SMU':'none', 'SML':'none', 'datetime':'YYYY-MM-DD HH:MM:SS'}
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
                 ' degrees magnetic north.', 'datetime':'UT date and time'}

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
        uniq_delta[bsplit[1]] += "{:s}, ".format(bdate)

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
        else:
            base_string += "unknown"

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
        else:
            base_string += "unknown"

    return base_string

def clean(supermag):
    """ Data is not supplied when it isn't clean
    """
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
