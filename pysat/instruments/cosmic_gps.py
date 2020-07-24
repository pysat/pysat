# -*- coding: utf-8 -*-
"""
Loads data from the COSMIC satellite.

The Constellation Observing System for Meteorology, Ionosphere, and Climate
(COSMIC) is comprised of six satellites in LEO with GPS receivers. The
occultation of GPS signals by the atmosphere provides a measurement of
atmospheric parameters. Data downloaded from the COSMIC Data Analaysis
and Archival Center.

Default behavior is to search for the 2013 re-processed data first, then the
post-processed data as recommended on
https://cdaac-www.cosmic.ucar.edu/cdaac/products.html

Properties
----------
platform
    'cosmic'
name
    'gps' for Radio Occultation profiles
tag
    Select profile type, or scintillation, one of:
    {'ionprf', 'sonprf', 'wetprf', 'atmprf', 'scnlv1'}
sat_id
    None supported
altitude_bin
    Number of kilometers to bin altitude profiles by when loading.
    Currently only supported for tag='ionprf'.

Note
----
- 'ionprf: 'ionPrf' ionosphere profiles
- 'sonprf': 'sonPrf' files
- 'wetprf': 'wetPrf' files
- 'atmprf': 'atmPrf' files
- 'scnlv1': 'scnLv1' files

Warnings
--------
- Routine was not produced by COSMIC team
- More recent versions of netCDF4 and numpy limit the casting of some variable
  types into others. This issue could prevent data loading for some variables
  such as 'MSL_Altitude' in the 'sonprf' and 'wetprf' files. The default
  UserWarning when this occurs is
    'UserWarning: WARNING: missing_value not used since it cannot be safely
    cast to variable data type'

"""

from __future__ import print_function
from __future__ import absolute_import
import logging
import numpy as np
import os
import requests
from requests.auth import HTTPBasicAuth
import shutil
import sys
import tarfile

import netCDF4
import pysat

logger = logging.getLogger(__name__)

platform = 'cosmic'
name = 'gps'
tags = {'ionprf': '',
        'sonprf': '',
        'wetprf': '',
        'atmprf': '',
        'scnlv1': ''}
sat_ids = {'': ['ionprf', 'sonprf', 'wetprf', 'atmprf', 'scnlv1']}
_test_dates = {'': {'ionprf': pysat.datetime(2008, 1, 1),
                    'sonprf': pysat.datetime(2008, 1, 1),
                    'wetprf': pysat.datetime(2008, 1, 1),
                    'atmprf': pysat.datetime(2008, 1, 1),
                    'scnlv1': pysat.datetime(2008, 1, 1)}}


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data.

    Parameters
    ----------
    tag : string or NoneType
        Denotes type of file to load.
        (default=None)
    sat_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : NoneType
        User specified file format not supported here. (default=None)

    Returns
    -------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    """
    estr = 'Building a list of COSMIC files, which can possibly take time. '
    logger.info('{:s}~1s per 100K files'.format(estr))
    sys.stdout.flush()

    # Note that Files.from_os() could be used here except for the fact
    # that there are multiple COSMIC files per given time
    # here, we follow from_os() except a fictional microsecond
    # is added to file times to help ensure there are no file collisions

    # overloading revision keyword below
    if format_str is None:
        # COSMIC file format string
        format_str = ''.join(('*.*/*.{year:04d}.{day:03d}',
                              '.{hour:02d}.{minute:02d}.*_nc'))

    # process format string to get string to search for
    search_dict = pysat._files.construct_searchstring_from_format(format_str)
    search_str = search_dict['search_string']
    # perform local file search
    files = pysat._files.search_local_system_formatted_filename(data_path,
                                                                search_str)
    # we have a list of files, now we need to extract the information
    # pull of data from the areas identified by format_str
    stored = pysat._files.parse_delimited_filenames(files, format_str,
                                                    delimiter='.')

    if len(stored['year']) > 0:
        year = np.array(stored['year'])
        day = np.array(stored['day'])
        hour = np.array(stored['hour'])
        minute = np.array(stored['minute'])
        uts = hour*3600. + minute*60.
        # do a pre-sort on uts to get files that may conflict with each other
        # due to multiple spacecraft and antennas
        # this ensures that we can make the times all unique for the file list
        idx = np.argsort(uts)
        # adding linearly increasing offsets less than 0.01 s
        shift_uts = np.mod(np.arange(len(year)), 1E3) * 1.E-5 + 1.E-5
        uts[idx] += shift_uts

        index = pysat.utils.time.create_datetime_index(year=year, day=day,
                                                       uts=uts)

        if not index.is_unique:
            raise ValueError(' '.join(('Generated non-unique datetimes for',
                                       'COSMIC within list_files.')))
        # store sorted file names with unique times in index
        file_list = np.array(stored['files'])
        file_list = pysat.Series(file_list, index=index)
        return file_list

    else:
        logger.info('Found no files, check your path or download them.')
        return pysat.Series(None)


def load(fnames, tag=None, sat_id=None, altitude_bin=None):
    """Load COSMIC GPS files.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames
    tag : str or NoneType
        tag or None (default=None)
    sat_id : str or NoneType
        satellite id or None (default=None)
    altitude_bin : integer
        Number of kilometers to bin altitude profiles by when loading.
        Currently only supported for tag='ionprf'. (default=None)

    Returns
    -------
    output : pandas.DataFrame
        Object containing satellite data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    """

    # input check
    if altitude_bin is not None:
        if tag != 'ionprf':
            estr = 'altitude_bin keyword only supported for "tag=ionprf"'
            raise ValueError(estr)

    num = len(fnames)
    # make sure there are files to read
    if num != 0:
        # call separate load_files routine, segmented for possible
        # multiprocessor load, not included and only benefits about 20%
        output = pysat.DataFrame(load_files(fnames, tag=tag, sat_id=sat_id,
                                            altitude_bin=altitude_bin))
        utsec = output.hour * 3600. + output.minute * 60. + output.second
        # make times unique by adding a unique amount of time less than a second
        # FIXME: need to switch to xarray so unique time stamps not needed
        if tag != 'scnlv1':
            # add 1E-6 seconds to time based upon occulting_sat_id
            # additional 1E-7 seconds added based upon cosmic ID
            # get cosmic satellite ID
            c_id = np.array([snip[3] for snip in output.fileStamp]).astype(int)
            # time offset
            utsec += output.occulting_sat_id*1.e-5 + c_id*1.e-6
        else:
            # construct time out of three different parameters
            # duration must be less than 10,000
            # prn_id is allowed two characters
            # antenna_id gets one
            # prn_id and antenna_id are not sufficient for a unique time
            utsec += output.prn_id*1.e-2 + output.duration.astype(int)*1.E-6
            utsec += output.antenna_id*1.E-7
        # move to Index
        output.index = \
            pysat.utils.time.create_datetime_index(year=output.year,
                                                   month=output.month,
                                                   day=output.day,
                                                   uts=utsec)
        if not output.index.is_unique:
            raise ValueError('Datetimes returned by load_files not unique.')
        # make sure UTS strictly increasing
        output.sort_index(inplace=True)
        # use the first available file to pick out meta information
        profile_meta = pysat.Meta()
        meta = pysat.Meta()
        ind = 0
        repeat = True
        while repeat:
            try:
                data = netCDF4.Dataset(fnames[ind])
                ncattrsList = data.ncattrs()
                for d in ncattrsList:
                    meta[d] = {'units': '', 'long_name': d}
                keys = data.variables.keys()
                for key in keys:
                    if 'units' in data.variables[key].ncattrs():
                        profile_meta[key] = {'units': data.variables[key].units,
                                             'long_name':
                                             data.variables[key].long_name}
                repeat = False
            except RuntimeError:
                # file was empty, try the next one by incrementing ind
                ind += 1

        meta['profiles'] = profile_meta
        return output, meta
    else:
        # no data
        return pysat.DataFrame(None), pysat.Meta()


def _process_lengths(lengths):
    """Prep lengths for parsing.

    Internal func used by load_files.
    """

    lengths = lengths.tolist()
    lengths.insert(0, 0)
    lengths = np.array(lengths)
    lengths2 = lengths.copy()
    lengths[-1] += 1
    return lengths, lengths2


# separate routine for doing actual loading. This was broken off from main load
# because I was playing around with multiprocessor loading
# yielded about 20% improvement in execution time
def load_files(files, tag=None, sat_id=None, altitude_bin=None):
    """Load COSMIC data files directly from a given list.

    May be directly called by user, but in general is called by load.  This is
    separate from the main load function for future support of multiprocessor
    loading.

    Parameters
    ----------
    files : pandas.Series
        Series of filenames
    tag : str or NoneType
        tag or None (default=None)
    sat_id : str or NoneType
        satellite id or None (default=None)
    altitude_bin : integer
        Number of kilometers to bin altitude profiles by when loading.
        Currently only supported for tag='ionprf'. (default=None)

    Returns
    -------
    output : list of dicts
        Object containing satellite data, one dict per file

    """

    output = [None] * len(files)
    drop_idx = []
    main_dict = {}
    main_dict_len = {}

    safe_keys = []
    for (i, fname) in enumerate(files):
        try:
            data = netCDF4.Dataset(fname)
            # build up dictionary will all ncattrs
            new = {}
            # get list of file attributes
            ncattrsList = data.ncattrs()
            # these include information about where the profile observed
            for d in ncattrsList:
                new[d] = data.getncattr(d)

            if i == 0:
                keys = data.variables.keys()
                for key in keys:
                    safe_keys.append(key)
                    main_dict[key] = []
                    main_dict_len[key] = []

            # load all of the variables in the netCDF
            for key in safe_keys:
                # grab data
                t_list = data.variables[key][:]
                # reverse byte order if needed
                if t_list.dtype.byteorder != '=':
                    main_dict[key].append(t_list.byteswap().newbyteorder())
                else:
                    main_dict[key].append(t_list)
                # store lengths
                main_dict_len[key].append(len(main_dict[key][-1]))

            output[i] = new
            data.close()
        except RuntimeError:
            # some of the files have zero bytes, which causes a read error
            # this stores the index of these zero byte files so I can drop
            # the Nones the gappy file leaves behind
            drop_idx.append(i)

    # drop anything that came from the zero byte files
    drop_idx.reverse()
    for i in drop_idx:
        del output[i]

    # combine different sub lists in main_dict into one
    for key in safe_keys:
        main_dict[key] = np.hstack(main_dict[key])
        main_dict_len[key] = np.cumsum(main_dict_len[key])

    if tag == 'atmprf':
        # this file has three groups of variable lengths
        # each goes into its own DataFrame
        # two are processed here, last is processed like other
        # file types
        # see code just after this if block for more
        # general explanation on lines just below
        p_keys = ['OL_vec2', 'OL_vec1', 'OL_vec3', 'OL_vec4']
        p_dict = {}
        # get indices needed to parse data
        plengths = main_dict_len['OL_vec1']
        max_p_length = np.max(plengths)
        plengths, plengths2 = _process_lengths(plengths)
        # collect data
        for key in p_keys:
            p_dict[key] = main_dict.pop(key)
            _ = main_dict_len.pop(key)
        psub_frame = pysat.DataFrame(p_dict)

        # change in variables in this file type
        # depending upon the processing applied at UCAR
        if 'ies' in main_dict.keys():
            q_keys = ['OL_ipar', 'OL_par', 'ies', 'hes', 'wes']
        else:
            q_keys = ['OL_ipar', 'OL_par']
        q_dict = {}
        # get indices needed to parse data
        qlengths = main_dict_len['OL_par']
        max_q_length = np.max(qlengths)
        qlengths, qlengths2 = _process_lengths(qlengths)
        # collect data
        for key in q_keys:
            q_dict[key] = main_dict.pop(key)
            _ = main_dict_len.pop(key)
        qsub_frame = pysat.DataFrame(q_dict)

        max_length = np.max([max_p_length, max_q_length])
        length_arr = np.arange(max_length)
        # small sub DataFrames
        for i in np.arange(len(output)):
            output[i]['OL_vecs'] = psub_frame.iloc[plengths[i]:plengths[i+1], :]
            output[i]['OL_vecs'].index = \
                length_arr[:plengths2[i+1]-plengths2[i]]
            output[i]['OL_pars'] = qsub_frame.iloc[qlengths[i]:qlengths[i+1], :]
            output[i]['OL_pars'].index = \
                length_arr[:qlengths2[i+1]-qlengths2[i]]

    # create a single data frame with all bits, then
    # break into smaller frames using views
    main_frame = pysat.DataFrame(main_dict)
    # get indices needed to parse data
    lengths = main_dict_len[list(main_dict.keys())[0]]
    # get largest length and create numpy array with it
    # used to speed up reindexing below
    max_length = np.max(lengths)
    length_arr = np.arange(max_length)
    # process lengths for ease of parsing
    lengths, lengths2 = _process_lengths(lengths)
    # break main profile data into each individual profile
    for i in np.arange(len(output)):
        output[i]['profiles'] = main_frame.iloc[lengths[i]:lengths[i+1], :]
        output[i]['profiles'].index = length_arr[:lengths2[i+1]-lengths2[i]]

    if tag == 'ionprf':
        if altitude_bin is not None:
            for out in output:
                rval = (out['profiles']['MSL_alt']/altitude_bin).round().values
                out['profiles'].index = rval * altitude_bin
                out['profiles'] = \
                    out['profiles'].groupby(out['profiles'].index.values).mean()
        else:
            for out in output:
                out['profiles'].index = out['profiles']['MSL_alt']

    return output


def download(date_array, tag, sat_id, data_path=None,
             user=None, password=None):
    """Download COSMIC GPS data.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    """

    if tag == 'ionprf':
        sub_dir = 'ionPrf'
    elif tag == 'sonprf':
        sub_dir = 'sonPrf'
    elif tag == 'wetprf':
        sub_dir = 'wetPrf'
    elif tag == 'atmprf':
        sub_dir = 'atmPrf'
    elif tag == 'scnlv1':
        sub_dir = 'scnLv1'
    else:
        raise ValueError('Unknown cosmic_gps tag')

    if (user is None) or (password is None):
        raise ValueError('CDAAC user account information must be provided.')

    for date in date_array:
        logger.info('Downloading COSMIC data for ' + date.strftime('%D'))
        sys.stdout.flush()
        yr, doy = pysat.utils.time.getyrdoy(date)
        yrdoystr = '{year:04d}.{doy:03d}'.format(year=yr, doy=doy)
        # Try re-processed data (preferred)
        try:
            dwnld = ''.join(("https://cdaac-www.cosmic.ucar.edu/cdaac/rest/",
                             "tarservice/data/cosmic2013/"))
            dwnld = dwnld + sub_dir + '/{year:04d}.{doy:03d}'.format(year=yr,
                                                                     doy=doy)
            top_dir = os.path.join(data_path, 'cosmic2013')
            req = requests.get(dwnld, auth=HTTPBasicAuth(user, password))
            req.raise_for_status()
        except requests.exceptions.HTTPError:
            # if response is negative, try post-processed data
            try:
                dwnld = ''.join(("https://cdaac-www.cosmic.ucar.edu/cdaac/",
                                 "rest/tarservice/data/cosmic/"))
                dwnld = dwnld + sub_dir + '/{year:04d}.{doy:03d}'
                dwnld = dwnld.format(year=yr, doy=doy)
                top_dir = os.path.join(data_path, 'cosmic')
                req = requests.get(dwnld, auth=HTTPBasicAuth(user, password))
                req.raise_for_status()
            except requests.exceptions.HTTPError as err:
                estr = ''.join((str(err), '\n', 'Data not found'))
                logger.info(estr)
        # Copy request info to tarball
        # If data does not exist, will copy info not readable as tar
        fname = os.path.join(data_path,
                             'cosmic_' + sub_dir + '_' + yrdoystr + '.tar')
        with open(fname, "wb") as local_file:
            local_file.write(req.content)
            local_file.close()
        try:
            # uncompress files and remove tarball
            tar = tarfile.open(fname)
            tar.extractall(path=data_path)
            tar.close()
            # move files
            source_dir = os.path.join(top_dir, sub_dir, yrdoystr)
            destination_dir = os.path.join(data_path, yrdoystr)
            if os.path.exists(destination_dir):
                shutil.rmtree(destination_dir)
            shutil.move(source_dir, destination_dir)
            # Get rid of empty directories from tar process
            shutil.rmtree(top_dir)
        except tarfile.ReadError:
            # If file cannot be read as a tarfile, then data does not exist
            # skip this day since no data to move
            pass
        # tar file must be removed (even if download fails)
        os.remove(fname)

    return


def clean(inst):
    """Return COSMIC GPS data cleaned to the specified level.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Notes
    -----
    Supports 'clean', 'dusty', 'dirty'

    """

    if inst.tag == 'ionprf':
        # ionosphere density profiles
        if inst.clean_level == 'clean':
            # try and make sure all data is good
            # filter out profiles where source provider processing doesn't
            # get max dens and max dens alt
            inst.data = inst.data[((inst['edmaxalt'] != -999.) &
                                   (inst['edmax'] != -999.))]
            # make sure edmaxalt in "reasonable" range
            inst.data = inst.data[(inst.data.edmaxalt >= 175.) &
                                  (inst.data.edmaxalt <= 475.)]
            # filter densities when negative
            for i, profile in enumerate(inst['profiles']):
                # take out all densities below the highest altitude negative
                # dens below 325
                idx, = np.where((profile.ELEC_dens < 0) &
                                (profile.index <= 325))
                if len(idx) > 0:
                    profile.iloc[0:idx[-1]+1] = np.nan
                # take out all densities above the lowest altitude negative
                # dens above 325
                idx, = np.where((profile.ELEC_dens < 0) &
                                (profile.index > 325))
                if len(idx) > 0:
                    profile.iloc[idx[0]:] = np.nan

                # do an altitude density gradient check to reduce number of
                # cycle slips
                densDiff = profile.ELEC_dens.diff()
                altDiff = profile.MSL_alt.diff()
                normGrad = (densDiff / (altDiff * profile.ELEC_dens)).abs()
                idx, = np.where((normGrad > 1.) & normGrad.notnull())
                if len(idx) > 0:
                    inst[i, 'edmaxalt'] = np.nan
                    inst[i, 'edmax'] = np.nan
                    inst[i, 'edmaxlat'] = np.nan
                    profile['ELEC_dens'] *= np.nan

        # filter out any measurements where things have been set to NaN
        inst.data = inst.data[inst.data.edmaxalt.notnull()]

    elif inst.tag == 'scnlv1':
        # scintillation files
        if inst.clean_level == 'clean':
            # try and make sure all data is good
            # filter out profiles where source provider processing doesn't
            # work
            inst.data = inst.data[((inst['alttp_s4max'] != -999.) &
                                   (inst['s4max9sec'] != -999.))]

    return
