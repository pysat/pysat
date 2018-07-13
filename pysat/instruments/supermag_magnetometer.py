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
    Select  {'indices', None, 'all', 'stations'}

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
        'all':'magnetometer measurements and indices',
        'stations':'magnetometer stations'}
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
        'stations', and None (for just magnetometer measurements).
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
        'stations', and None (for just magnetometer measurements).
        (default=None)
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
                temp = load_csv_data(fname, tag)
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

def load_csv_data(fname, tag):
    """Load data from a comma separated SuperMAG file

    Parameters
    ------------
    fname : (str)
        CSV SuperMAG file name
    tag : (str)
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        'stations', and None (for just magnetometer measurements).

    Returns
    --------
    data : (pandas.DataFrame)
        Pandas DataFrame
    """
    if tag == "stations":
        # Because there may be multiple operators, the default pandas reader
        # cannot be used.
        ddict = dict()
        dkeys = list()

        # Open and read the file
        with open(fname, "r") as fopen:
            for fline in fopen.readlines():
                sline = fline.split(',')

                if len(ddict.keys()) == 0:
                    for kk in sline:
                        ddict[kk] = list()
                    dkeys = ddict.keys()
                else:
                    for i,ll in emunerate(sline):
                        if i >= 1 and i <= 4:
                            ddict[dkeys[i]].append(float(ll))
                        elif i == 6:
                            ddict[dkeys[i]].append(int(ll))
                        elif i < len(dkeys):
                            ddict[dkeys[i]].append(ll)
                        else:
                            ddict[dkeys[-1]][-1] += " {:s}".format(ll)
                            
        # Create a data frame for this file
        data = pds.DataFrame(ddict, index=ddict['IAGA'],
                             columns=ddict.keys())
    else:
        # Define the date parser
        def parse_smag_date(dd):                                               
            return pysat.datetime.strptime(dd, "%Y-%m-%d %H:%M:%S")

        # Load the file into a data frame
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
        'stations', and None (for just magnetometer measurements).
        (default=None)

    Returns
    --------
    data : (pandas.DataFrame)
        Pandas DataFrame
    baseline : (list)
        List of strings denoting the presence of a standard and file-specific
        baselines for each file.  None of not present or not applicable.
    """
    import re
    ndata = {"indices":2, None:4, 'date':7, "all":4, "stations":8}
    dkeys = {'stations':['IAGA', 'GEOLON', 'GEOLAT', 'AACGMLON', 'AACGMLAT',
                         'STATION-NAME', 'OPERATOR-NUM', 'OPERATORS'],
             None:['IAGA', 'N', 'E', 'Z']}
    skeys = 
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
        dflag = False if tag == "stations" else True  # date line
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
                        dkeys[None].extend(['MLT', 'MLAT'])
                    if fline.find("-sza") > 0:
                        ndata[None] += 1
                        dkeys[None].append('SZA')
                    if fline.find("-decl") > 0:
                        ndata[None] += 1
                        dkeys[None].append('IGRF_DECL')
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
                lsplit = re.split(r'\t+', fline)

                if dflag:
                    dflag = False # Unset the date flag
                    dstring = " ".join(lsplit[:6])
                    dtime = pysat.datetime.strptime(dstring,
                                                    "%Y %m %d %H %M %S")
                    snum = int(lsplit[6]) # Set the number of stations

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
                else:
                    if tag == "stations" and len(lsplit) >= ndata[tag]:
                        # Because stations can have multiple operators,
                        # ndata supplies the minimum number of columns
                        if len(ddict.keys()) < ndata[tag]:
                            for kk in dkeys[tag]:
                                ddict[kk] = list()
                        for i,ll in enumerate(lsplit):
                            if i >= 1 and i <= 4:
                                ddict[dkeys[tag][i]].append(float(ll))
                            elif i == 6:
                                ddict[dkeys[tag][i]].append(int(ll))
                            elif i < len(dkeys[tag]):
                                ddict[dkeys[tag][i]].append(ll)
                            else:
                                ddict[dkeys[tag][-1]][-1] += " {:s}".format(ll)
                    elif len(lsplit) == ndata[None]:
                        snum -= 1 # Mark the ingestion of a station
                        if tag != "indices":
                            if len(ddict.keys()) < ndata[None]:
                               for kk in dkeys[None]:
                                   ddict[kk] = list()
                            for i,kk in enumerate(dkeys[None]):
                                if i == 0:
                                    ddict[kk].append(lsplit[i])
                                else:
                                    ddict[kk].append(float(lsplit[i]))

                if tag != "stations" and snum == 0 and len(ddict.keys()) >= 2:
                    # The previous value was the last value, prepare for
                    # next block
                    dflag = True

        # Create a data frame for this file
        if tag == "stations":
            date_list = ddict['IAGA']
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
                  'SMU':'none', 'SML':'none', 'datetime':'YYYY-MM-DD HH:MM:SS',
                  'GEOLON':'degrees', 'GEOLAT':'degrees', 'AACGMLON':'degrees',
                  'AACGMLAT':'degrees', 'STATION-NAME':'none',
                  'OPERATOR-NUM':'none', 'OPERATOR':'none'}
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
                 ' degrees magnetic north.', 'datetime':'UT date and time',
                 'GEOLON':'geographic longitude',
                 'GEOLAT':'geographic latitude',
                 'AACGMLON':'Altitude-Adjusted Corrected Geomagnetic longitude',
                 'AACGMLAT':'Altitude-Adjusted Corrected Geomagnetic latitude',
                 'STATION-NAME':'Long form station name',
                 'OPERATOR-NUM':'Number of station operators',
                 'OPERATOR':'Station operator name(s)'}

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
    """ Data has been cleaned, but should be examined before use
    """
    return

def download(date_array, tag, sat_id='', data_path=None, user=None,
             password=None, baseline='all', delta='none', options='all',
             file_fmt='ascii'):
    """Routine to download SuperMAG data

    Parameters
    -----------
    date_array : np.array
        Array of datetime objects
    tag : string
        String denoting the type of file to load, accepted values are 'indices',
        'all', 'stations', and None (for only magnetometer data)
    sat_id : string
        Not used (default='')
    data_path : string or NoneType
        Data path to save downloaded files to (default=None)
    user : string or NoneType
        SuperMAG requires user registration (default=None)
    password : string or NoneType
        Not used; SuperMAG does not require a password (default=None)
    file_fmt : string
        File format options: 'ascii' and 'csv'. (default='ascii')
    baseline : string
        Baseline to remove from magnetometer data.  Options are 'all', 'yearly',
        and 'none'. (default='all')
    delta : string
        Remove a value from the magnetometer data.  Options are 'none', 'start',
        and 'median'.  (default='none')
    options : string or NoneType
        Additional parameter options for magnetometer data.  Includes 'mlt'
        (MLat and MLT), 'decl' (IGRF declination), 'sza' (Solar Zenith Angle),
        'all', and None. (default='all')
    """
    import sys
    import urllib2

    if user is None:
        raise ValueError('SuperMAG requires user registration')

    remoteaccess = {'method':'http', 'host':'supermag.jhuapl.edu',
                    'path':'mag/lib/services', 'user':'user={:s}'.format(user),
                    'service':'service=', 'options':'options='}
    remotefmt = "{method}//{host}/{path}/??{user}&{service}&{filefmt}&{start}"

    # Set the tag information
    if tag == "indices":
        tag = "all"

    if tag != "stations":
        remotefmt += "&{interval}&{stations}&{delta}&{baseline}&{options}"

    # Determine whether station or magnetometer data is requested
    remoteaccess['service'] += tag if tag == "stations" else "mag"

    # Add request for file type
    file_fmt = file_fmt.lower()
    if not file_fmt in ['ascii', 'csv']:
        estr = "unknown file format [{:s}], using 'ascii'".format(file_fmt)
        print("WARNING: {:s}".format(estr))
        file_fmt = 'ascii'
    remoteaccess['filefmt'] = 'fmt={:s}'format(file_fmt)

    # If indices are requested, add them now.
    if not tag in [None, 'stations']:
        remoteaccess['options'] += "+envelope"

    # Add other download options (for non-station files)
    if tag != "stations":
        if options is not None:
            options = options.lower()
            if options is 'all':
                remoteaccess['options'] += "+mlt+sza+decl"
            else:
                remoteaccess['options'] += "+{:s}".format(options)

        # Add requests for baseline substraction
        baseline = baseline.lower()
        if not baseline in ['all', 'yearly', 'none']:
            estr = "unknown baseline [{:s}], using 'all'".format(baseline)
            print("WARNING: {:s}".format(estr))
            baseline = 'all'
        remoteaccess['baseline'] = "baseline={:s}".format(baseline)

        delta = delta.lower()
        if not delta in ['none', 'median', 'start']:
            estr = "unknown delta [{:s}], using 'none'".format(delta)
            print("WARNING: {:s}".format(estr))
            delta = 'none'
        remoteaccess['delta'] = 'delta={:s}'format(delta)

        # Set the time information and format
        remoteaccess['interval'] = "interval=23%35A59"
        sfmt = "%Y-%m-%dT00:00:00.000"
        ffmt = "{:s}_{:s}_%Y%j.{:s}".format(platform, name, file_fmt)
        start_str = "start="
    else:
        # Set the time format
        sfmt = "%Y"
        ffmt = "{:s}_{:s}_%Y.{:s}".format(platform, name, file_fmt)
        start_str = "year="

    # Cycle through all of the dates, formatting them to achieve a unique set
    # of times to download data
    date_fmts = list(set([dd.strftime(sfmt) for dd in date_array]))
    name_fmts = list(set([dd.strftime(ffmt) for dd in date_array]))

    # Cycle through all of the unique dates.  Stations lists are yearly and
    # magnetometer data is daily
    istr = 'SuperMAG {:s}'.format(tag if tag == "stations" else "data")
    for i,date in enumerate(date_fmts):
        print("Downloading {:s} for {:s}".format(istr, date.split("T")[0]))
        sys.stdout.flush()

        # Add the start time and download period to query
        remoteaccess['start'] += "{:s}{:s}".format(start_str, date)

        if tag != "stations":
            # Get all of the stations for this time
            print("NEED TO LOAD STATION FILE")

            # Format a string of the station names
            print("NEED TO FORMAT THE STATION QUERY")
            remoteaccess['stations'] = "stations="

        # Format the query
        url = remotefmt.format(**remoteaccess)

        # Set up a request
        req = urllib2.Request(url)

        # Test the response
        try:
            # Establish a connection
            result = urllib2.urlopen(req)
        except:
            raise RuntimeError("unable to connect to [{:s}]".format(url))

        # Build the output file name
        if tag is None:
            fname = path.join(data_path, platform, name, name_fmts[i])
        else:
            fname = path.join(data_path, platform, name, tag, name_fmts[i])
        
        # Save the file data
        with open(fname, "w") as local_file:
            local_file.write(result.read())
            local_file.close()

        # Close the open connection
        result.close()
    return
