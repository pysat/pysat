# -*- coding: utf-8 -*-
"""Supports SuperMAG ground magnetometer measurements and SML/SMU indices.
Downloading is supported; please follow their rules of the road:
http://supermag.jhuapl.edu/info/?page=rulesoftheroad

Parameters
----------
platform : string
    'supermag'
name : string
    'magnetometer'
tag : string
    Select  {'indices', '', 'all', 'stations'}

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
    - Currently no cleaning routine, though the SuperMAG description indicates
      that these products are expected to be good.  More information about the
      processing is available
    - Module not written by the SuperMAG team.

"""

from __future__ import print_function, absolute_import
import pandas as pds
import numpy as np
from os import path
import functools
import warnings

import pysat

platform = 'supermag'
name = 'magnetometer'
tags = {'indices': 'SMU and SML indices',
        '': 'magnetometer measurements',
        'all': 'magnetometer measurements and indices',
        'stations': 'magnetometer stations'}
sat_ids = {'': tags.keys()}
_test_dates = {'': {kk: pysat.datetime(2009, 1, 1) for kk in tags.keys()}}


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    # if the tag is 'indices', update data_path to reflect this
    # both 'indices' and 'all' are stored under 'all'
    if self.tag == "indices":
        psplit = path.split(self.files.data_path[:-1])
        self.files.data_path = path.join(psplit[0], "all", "")

    # reset the list_remote_files routine to include the data path
    # now conveniently included with instrument object
    self._list_remote_rtn = \
        functools.partial(list_remote_files,
                          data_path=self.files.data_path,
                          format_str=self.files.file_format)
    return


def list_remote_files(tag='', sat_id=None, data_path=None, format_str=None,
                      year=None, month=None, Day=None):
    """Lists remote files available for SuperMAG.

    Note
    ----
    Given the setup of the SuperMAG system, files aren't directly
    available as the requested data is put into files as requested.
    To enable the functionality of keeping SuperMAG up to date, we
    fake the files here such that data from 1970 through the present
    is downloaded.

    Parameters
    ----------
    tag : string
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        'stations', and '' (for just magnetometer measurements).
        (default='')
    sat_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : string or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)
    year : int or NoneType
        Selects a given year to return remote files for.  None returns all
        years.
        (default=None)
    month : int or NoneType
        Selects a given month to return remote files for.  None returns all
        months.  Requires year to be defined.
        (default=None)
    day : int or NoneType
        Selects a given day to return remote files for.  None returns all
        days.  Requires year and month to be defined.
        (default=None)

    Returns
    -------
    pandas.Series
        Series indexed by date that stores the filename for each date.

    """

    # given the function of SuperMAG, create a fake list of files
    # starting 01 Jan 1970, through today
    now = pysat.datetime.now()
    now = pysat.datetime(now.year, now.month, now.day)
    if tag == 'stations':
        # yearly
        freq = 'Y'
    else:
        # daily
        freq = 'D'
    # create a list of dates with appropriate frequency
    index = pds.period_range(pysat.datetime(1970, 1, 1), now, freq=freq)
    # pre fill in blank strings
    remote_files = pds.Series([''] * len(index), index=index)

    # pysat compares both dates and filenames when determining
    # which files it needs to download
    # so we need to ensure that filename for dates that overlap
    # are the same or data that is already present will be redownloaded

    # need to get a list of the current files attached to
    # the Instrument object. In this case, the object hasn't
    # been passed in.....
    #   that is ok, we can just call list_files right here
    #   except we don't have the data path
    # the init function above is used to reset the
    # lost_remote_files method with one where the
    # data path and format_str are set
    # iterating directly since pandas is complaining about periods
    # between different between indexes
    local_files = list_files(tag, sat_id, data_path, format_str)
    for time, fname in local_files.iteritems():
        remote_files.loc[time] = fname
    return remote_files


def list_files(tag='', sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen SuperMAG data

    Parameters
    -----------
    tag : string
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        'stations', and '' (for just magnetometer measurements). (default='')
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
    pysat.Files.from_os : (pysat._files.Files)
        A pandas Series containing the verified available files

    """
    if format_str is None and data_path is not None:
        file_base = 'supermag_magnetometer'
        if tag == "indices" or tag == "all":
            file_base += '_all'  # Can't just download indices

            if tag == "indices":
                psplit = path.split(data_path[:-1])
                data_path = path.join(psplit[0], "all", "")

        if tag == "stations":
            file_base += '_stations'
            min_fmt = '_'.join([file_base, '{year:4d}.???'])
            doff = pds.DateOffset(years=1)
        else:
            min_fmt = '_'.join([file_base,
                                '{year:4d}{month:02d}{day:02d}.???'])
            doff = pds.DateOffset(days=1)

        files = pysat.Files.from_os(data_path=data_path, format_str=min_fmt)

        # station files are once per year but we need to
        # create the illusion there is a file per year
        if not files.empty:
            files = files.sort_index()

            if tag == "stations":
                orig_files = files.copy()
                new_files = []
                # Assigns the validity of each station file to be 1 year
                for orig in orig_files.iteritems():
                    files.loc[orig[0] + doff - pds.DateOffset(days=1)] = orig[1]
                    files = files.sort_index()
                    new_files.append(files.loc[orig[0]: orig[0] + doff - \
                            pds.DateOffset(days=1)].asfreq('D', method='pad'))
                files = pds.concat(new_files, sort = True)

                files = files.dropna()
                files = files.sort_index()
            # add the date to the filename
            files = files + '_' + files.index.strftime('%Y-%m-%d')
        return files
    elif format_str is None:
        estr = 'A directory must be passed to the loading routine for SuperMAG'
        raise ValueError(estr)
    else:
        return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def load(fnames, tag='', sat_id=None):
    """ Load the SuperMAG files

    Parameters
    -----------
    fnames : list
        List of filenames
    tag : str
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        'stations', and '' (for just magnetometer measurements). (default='')
    sat_id : str or NoneType
        Satellite ID for constellations, not used. (default=None)

    Returns
    --------
    data : pandas.DataFrame
        Object containing satellite data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    """

    # Ensure that there are files to load
    if len(fnames) <= 0:
        return pysat.DataFrame(None), pysat.Meta(None)

    # Ensure that the files are in a list
    if isinstance(fnames, str):
        fnames = [fnames]

    # Initialise the output data
    data = pds.DataFrame()
    baseline = list()

    # Cycle through the files
    for fname in fnames:
        fname = fname[:-11]  # Remove date index from end of filename
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
            data = pds.concat([data, temp], sort=True, axis=0)
        del temp

    # If data was loaded, update the meta data
    if len(data.columns) > 0:
        meta = pysat.Meta()
        for cc in data.columns:
            meta[cc] = update_smag_metadata(cc)

        meta.info = {'baseline': format_baseline_list(baseline)}
    else:
        meta = pysat.Meta(None)

    return data, meta


def load_csv_data(fname, tag):
    """Load data from a comma separated SuperMAG file

    Parameters
    ------------
    fname : str
        CSV SuperMAG file name
    tag : str
        Denotes type of file to load.  Accepted types are 'indices', 'all',
        'stations', and '' (for just magnetometer measurements).

    Returns
    --------
    data : pandas.DataFrame
        Pandas DataFrame

    """
    import re

    if tag == "stations":
        # Because there may be multiple operators, the default pandas reader
        # cannot be used.
        ddict = dict()
        dkeys = list()
        date_list = list()

        # Open and read the file
        with open(fname, "r") as fopen:
            dtime = pds.datetime.strptime(fname.split("_")[-1].split(".")[0],
                                          "%Y")

            for fline in fopen.readlines():
                sline = [ll for ll in re.split(r'[,\n]+', fline)
                         if len(ll) > 0]

                if len(ddict.items()) == 0:
                    for kk in sline:
                        kk = re.sub("-", "_", kk)
                        ddict[kk] = list()
                        dkeys.append(kk)
                else:
                    date_list.append(dtime)
                    for i, ll in enumerate(sline):
                        if i >= 1 and i <= 4:
                            ddict[dkeys[i]].append(float(ll))
                        elif i == 6:
                            ddict[dkeys[i]].append(int(ll))
                        elif i < len(dkeys):
                            ddict[dkeys[i]].append(ll)
                        else:
                            ddict[dkeys[-1]][-1] += " {:s}".format(ll)

        # Create a data frame for this file
        data = pds.DataFrame(ddict, index=date_list, columns=ddict.keys())
    else:
        # Define the date parser
        def parse_smag_date(dd):
            return pysat.datetime.strptime(dd, "%Y-%m-%d %H:%M:%S")

        # Load the file into a data frame
        data = pds.read_csv(fname, parse_dates={'datetime': [0]},
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
        'stations', and '' (for just magnetometer measurements).

    Returns
    --------
    data : (pandas.DataFrame)
        Pandas DataFrame
    baseline : (list)
        List of strings denoting the presence of a standard and file-specific
        baselines for each file.  None of not present or not applicable.

    """
    import re
    ndata = {"indices": 2, "": 4, "all": 4, "stations": 8}
    dkeys = {'stations': list(), '': ['IAGA', 'N', 'E', 'Z']}
    data = pds.DataFrame(None)
    baseline = None

    # Ensure that the tag indicates a type of data we know how to load
    if tag not in ndata.keys():
        return data, baseline

    # Read in the text data, processing the header, indices, and
    # magnetometer data (as desired)
    with open(fname, "r") as fopen:
        # Set the processing flags
        hflag = True  # header lines
        pflag = False  # parameter line
        dflag = False if tag == "stations" else True  # date line
        snum = 0      # number of magnetometer stations
        ddict = dict()
        date_list = list()

        if tag == "stations":
            dtime = pds.datetime.strptime(fname.split("_")[-1].split(".")[0],
                                          "%Y")

        for fline in fopen.readlines():
            # Cycle past the header
            line_len = len(fline)

            if hflag:
                if pflag:
                    pflag = False  # Unset the flag
                    if fline.find("-mlt") > 0:
                        ndata[''] += 2
                        dkeys[''].extend(['MLT', 'MLAT'])
                    if fline.find("-sza") > 0:
                        ndata[''] += 1
                        dkeys[''].append('SZA')
                    if fline.find("-decl") > 0:
                        ndata[''] += 1
                        dkeys[''].append('IGRF_DECL')
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
                                         lsplit[isd], lsplit[ist],
                                         lsplit[iex]])

                if fline.find("Selected parameters:") >= 0:
                    pflag = True
                if fline.count("=") == line_len - 1 and line_len > 2:
                    hflag = False
            else:
                # Load the desired data
                lsplit = [ll for ll in re.split(r'[\t\n]+', fline)
                          if len(ll) > 0]

                if dflag:
                    dflag = False  # Unset the date flag
                    dstring = " ".join(lsplit[:6])
                    dtime = pysat.datetime.strptime(dstring,
                                                    "%Y %m %d %H %M %S")
                    snum = int(lsplit[6])  # Set the number of stations

                    # Load the times
                    if tag == "indices":
                        date_list.append(dtime)
                    else:
                        date_list.extend([dtime for i in range(snum)])
                elif len(lsplit) == ndata['indices']:
                    if tag is not '':
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
                        if len(dkeys[tag]) == 0:
                            # Station files include column names and data files
                            # do not.  Read in the column names here
                            for ll in lsplit:
                                ll = re.sub("-", "_", ll)
                                dkeys[tag].append(ll)
                                ddict[ll] = list()
                        else:
                            # Because stations can have multiple operators,
                            # ndata supplies the minimum number of columns
                            date_list.append(dtime)
                            for i, ll in enumerate(lsplit):
                                if i >= 1 and i <= 4:
                                    ddict[dkeys[tag][i]].append(float(ll))
                                elif i == 6:
                                    ddict[dkeys[tag][i]].append(int(ll))
                                elif i < len(dkeys[tag]):
                                    ddict[dkeys[tag][i]].append(ll)
                                else:
                                    ddict[dkeys[tag][-1]][-1] += \
                                                            " {:s}".format(ll)
                    elif len(lsplit) == ndata['']:
                        snum -= 1  # Mark the ingestion of a station
                        if tag != "indices":
                            if len(ddict.keys()) < ndata['']:
                                for kk in dkeys['']:
                                    ddict[kk] = list()
                            for i, kk in enumerate(dkeys['']):
                                if i == 0:
                                    ddict[kk].append(lsplit[i])
                                else:
                                    ddict[kk].append(float(lsplit[i]))

                if tag != "stations" and snum == 0 and len(ddict.items()) >= 2:
                    # The previous value was the last value, prepare for
                    # next block
                    dflag = True

        # Create a data frame for this file
        data = pds.DataFrame(ddict, index=date_list, columns=ddict.keys())

        fopen.close()

    return data, baseline


def update_smag_metadata(col_name):
    """Update SuperMAG metadata

    Parameters
    -----------
    col_name : str
        Data column name

    Returns
    --------
    col_dict : dict
       Dictionary of strings detailing the units and long-form name of the data

    """

    smag_units = {'IAGA': 'none', 'N': 'nT', 'E': 'nT', 'Z': 'nT',
                  'MLT': 'hours', 'MLAT': 'degrees', 'SZA': 'degrees',
                  'IGRF_DECL': 'degrees', 'SMU': 'none', 'SML': 'none',
                  'datetime': 'YYYY-MM-DD HH:MM:SS',
                  'GEOLON': 'degrees', 'GEOLAT': 'degrees',
                  'AACGMLON': 'degrees', 'AACGMLAT': 'degrees',
                  'STATION_NAME': 'none',
                  'OPERATOR_NUM': 'none', 'OPERATORS': 'none'}
    smag_name = {'IAGA': 'Station Code',
                 'N': 'B along local magnetic North',
                 'E': 'B along local magnetic East',
                 'Z': 'B vertically downward',
                 'MLT': 'Magnetic Local Time',
                 'MLAT': 'Magnetic Latitude',
                 'SZA': 'Solar Zenith Angle',
                 'IGRF_DECL': 'IGRF magnetic declination',
                 'SMU': ' '.join(['Maximum eastward auroral electrojets',
                                  'strength.\nUpper envelope of N-component',
                                  'for stations between 40 and 80 degrees'
                                  'magnetic north.']),
                 'SML': ' '.join(['Maximum westward auroral electrojets',
                                  'strength.\nLower envelope of N-component',
                                  'for stations between 40 and 80 degrees',
                                  'magnetic north.']),
                 'datetime': 'UT date and time',
                 'GEOLON': 'geographic longitude',
                 'GEOLAT': 'geographic latitude',
                 'AACGMLON': ' '.join(['Altitude-Adjusted Corrected',
                                       'Geomagnetic longitude']),
                 'AACGMLAT': ' '.join(['Altitude-Adjusted Corrected',
                                       'Geomagnetic latitude']),
                 'STATION_NAME': 'Long form station name',
                 'OPERATOR_NUM': 'Number of station operators',
                 'OPERATORS': 'Station operator name(s)', }

    ackn = "When using this data please include the following reference:\n"
    ackn += "Gjerloev, J. W., The SuperMAG data processing technique, "
    ackn += "Geophys. Res., 117, A09213, doi:10.1029/2012JA017683, 2012\n\n"
    ackn += "For publications and presentations, please include the following"
    ackn += "acknowledgement:\nFor the ground magnetometer data we gratefully "
    ackn += "acknowledge: Intermagnet; USGS, Jeffrey J. Love; CARISMA, PI Ian "
    ackn += "Mann; CANMOS; The S-RAMP Database, PI K. Yumoto and Dr. K. "
    ackn += "Shiokawa; The SPIDR database; AARI, PI Oleg Troshichev; The "
    ackn += "MACCS program, PI M. Engebretson, Geomagnetism Unit of the "
    ackn += "Geological Survey of Canada; GIMA; MEASURE, UCLA IGPP and Florida"
    ackn += " Institute of Technology; SAMBA, PI Eftyhia Zesta; 210 Chain, PI "
    ackn += "K. Yumoto; SAMNET, PI Farideh Honary; The institutes who maintain"
    ackn += " the IMAGE magnetometer array, PI Eija Tanskanen; PENGUIN; "
    ackn += "AUTUMN, PI Martin Connors; DTU Space, PI Dr. Rico Behlke; South "
    ackn += "Pole and McMurdo Magnetometer, PI's Louis J. Lanzarotti and Alan "
    ackn += "T. Weatherwax; ICESTAR; RAPIDMAG; PENGUIn; British Artarctic "
    ackn += "Survey; McMac, PI Dr. Peter Chi; BGS, PI Dr. Susan Macmillan; "
    ackn += "Pushkov Institute of Terrestrial Magnetism, Ionosphere and Radio "
    ackn += "Wave Propagation (IZMIRAN); GFZ, PI Dr. Juergen Matzka; MFGI, PI "
    ackn += "B. Heilig; IGFPAS, PI J. Reda; University of L’Aquila, PI M. "
    ackn += "Vellante; BCMT, V. Lesur and A. Chambodut; Data obtained in "
    ackn += "cooperation with Geoscience Australia, PI Marina Costelloe; "
    ackn += "SuperMAG, PI Jesper W. Gjerloev."

    col_dict = {'units': smag_units[col_name],
                'long_name': smag_name[col_name],
                'acknowledgements': ackn}

    return col_dict


def format_baseline_list(baseline_list):
    """Format the list of baseline information from the loaded files into a
    cohesive, informative string

    Parameters
    ------------
    baseline_list : list
        List of strings specifying the baseline information for each
        SuperMAG file

    Returns
    ---------
    base_string : str
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

    if len(uniq_base.items()) == 1:
        base_string = "Baseline {:s}".format(list(uniq_base.keys())[0])
    else:
        base_string = "Baseline "

        for i, kk in enumerate(uniq_base.keys()):
            if i == 1:
                base_string += "{:s}: {:s}".format(kk, uniq_base[kk][:-2])
            else:
                base_string += "         {:s}: {:s}".format(kk,
                                                            uniq_base[kk][:-2])
        else:
            base_string += "unknown"

    if len(uniq_delta.items()) == 1:
        base_string += "\nDelta    {:s}".format(list(uniq_delta.keys())[0])
    else:
        base_string += "\nDelta    "

        for i, kk in enumerate(uniq_delta.keys()):
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


def download(date_array):
    """Routine to download SuperMAG data

    Parameters
    -----------
    date_array : np.array
        Array of datetime objects

    """
    warnings.warn(' '.join(("Downloads not currently supported in pysat.",
                            "Please visit http://supermag.jhuapl.edu/")))
    return None


def append_data(file_strings, file_fmt, tag):
    """ Load the SuperMAG files

    Parameters
    -----------
    file_strings : array-like
        Lists or arrays of strings, where each string contains one file of data
    file_fmt : str
        String denoting file type (ascii or csv)
    tag : string
        String denoting the type of file to load, accepted values are
        'indices', 'all', 'stations', and '' (for only magnetometer data)

    Returns
    -------
    out_string : string
        String with all data, ready for output to a file

    """
    # Determine the right appending routine for the file type
    if file_fmt.lower() == "csv":
        return append_csv_data(file_strings)
    else:
        return append_ascii_data(file_strings, tag)


def append_ascii_data(file_strings, tag):
    """ Append data from multiple files for the same time period

    Parameters
    -----------
    file_strings : array-like
        Lists or arrays of strings, where each string contains one file of data
    tag : string
        String denoting the type of file to load, accepted values are
        'indices', 'all', 'stations', and None (for only magnetometer data)

    Returns
    -------
    out_string : string
        String with all data, ready for output to a file

    """
    import re

    # Start with data from the first list element
    out_lines = file_strings[0].split('\n')
    iparam = -1  # Index for the parameter line
    ihead = -1  # Index for the last header line
    idates = list()  # Indices for the date lines
    date_list = list()  # List of dates
    num_stations = list()  # Number of stations for each date line
    ind_num = 2 if tag in ['all', 'indices'] else 0
    # ind_num = 2 if tag == '' else ind_num

    # Find the index information for the data
    for i, line in enumerate(out_lines):
        if line == "Selected parameters:":
            iparam = i + 1
        elif line.count("=") == len(line) and len(line) > 2:
            ihead = i
            break

    # Find the time indices and number of stations for each date line
    i = ihead + 1
    while i < len(out_lines) - 1:
        idates.append(i)
        lsplit = re.split('\t+', out_lines[i])
        dtime = pds.datetime.strptime(" ".join(lsplit[0:-1]),
                                      "%Y %m %d %H %M %S")
        date_list.append(dtime)
        num_stations.append(int(lsplit[-1]))
        i += num_stations[-1] + 1 + ind_num
    idates = np.array(idates)

    # Initialize a list of station names
    station_names = list()

    # Cycle through each additional set of file strings
    for ff in range(len(file_strings) - 1):
        file_lines = file_strings[ff + 1].split('\n')

        # Find the index information for the data
        head = True
        snum = 0
        for i, line in enumerate(file_lines):
            if head:
                if line.count("=") == len(line) and len(line) > 2:
                    head = False
            elif len(line) > 0:
                lsplit = re.split('\t+', line)
                if snum == 0:
                    dtime = pds.datetime.strptime(" ".join(lsplit[0:-1]),
                                                  "%Y %m %d %H %M %S")
                    try:
                        idate = date_list.index(dtime)
                    except:
                        # SuperMAG outputs date lines regardless of the
                        # number of stations.  These files shouldn't be
                        # appended together.
                        raise ValueError("Unexpected date ", dtime)

                    snum = int(lsplit[-1])
                    onum = num_stations[idate]
                    inum = ind_num

                    # Adjust reference data for new number of station lines
                    idates[idate+1:] += snum
                    num_stations[idate] += snum

                    # Adjust date line for new number of station lines
                    oline = "{:s}\t{:d}".format( \
                                    dtime.strftime("%Y\t%m\t%d\t%H\t%M\t%S"),
                                    num_stations[idate])
                    out_lines[idates[idate]] = oline
                else:
                    if inum > 0:
                        inum -= 1
                    else:
                        # Insert the station line to the end of the date
                        # section
                        onum += 1
                        snum -= 1
                        out_lines.insert(idates[idate]+onum, line)

                        # Save the station name to update the parameter line
                        if not lsplit[0] in station_names:
                            station_names.append(lsplit[0])

    # Update the parameter line
    out_lines[iparam] += "," + ",".join(station_names)

    # Join the output lines into a single string
    out_string = "\n".join(out_lines)

    return out_string


def append_csv_data(file_strings):
    """ Append data from multiple csv files for the same time period

    Parameters
    -----------
    file_strings : array-like
        Lists or arrays of strings, where each string contains one file of data

    Returns
    -------
    out_string : string
        String with all data, ready for output to a file

    """
    # Start with data from the first list element
    out_lines = list()
    head_line = None

    # Cycle through the lists of file strings, creating a list of line strings
    for fstrings in file_strings:
        file_lines = fstrings.split('\n')

        # Remove and save the header line
        head_line = file_lines.pop(0)

        # Save the data lines
        out_lines.extend(file_lines)

    # Sort the output lines by date and station (first two columns) in place
    out_lines.sort()

    # Remove all zero-length lines from front, add one to back, and add header
    i = 0
    while len(out_lines[i]) == 0:
        out_lines.pop(i)

    out_lines.insert(0, head_line)
    out_lines.append('')

    # Join the output lines into a single string
    out_string = "\n".join(out_lines)

    return out_string
