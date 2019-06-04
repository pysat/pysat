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

Parameters
----------
altitude_bin : integer
    Number of kilometers to bin altitude profiles by when loading.
    Currently only supported for tag='ionprf'.
platform : string
    'cosmic'
name : string
    'gps' for Radio Occultation profiles
tag : string
    Select profile type, one of {'ionprf', 'sonprf', 'wetprf', 'atmprf'}
sat_id : string
    None supported

Note
----
- 'ionprf: 'ionPrf' ionosphere profiles
- 'sonprf': 'sonPrf' files
- 'wetprf': 'wetPrf' files
- 'atmPrf': 'atmPrf' files

Warnings
--------
- Routine was not produced by COSMIC team

"""

from __future__ import print_function
from __future__ import absolute_import
import glob
import numpy as np
import os
import pandas as pds
import sys

import netCDF4
import pysat

platform = 'cosmic'
name = 'gps'
tags = {'ionprf': '',
        'sonprf': '',
        'wetprf': '',
        'atmprf': ''}
sat_ids = {'': ['ionprf', 'sonprf', 'wetprf', 'atmprf']}
test_dates = {'': {'ionprf': pysat.datetime(2008, 1, 1),
                   'sonprf': pysat.datetime(2008, 1, 1),
                   'wetprf': pysat.datetime(2008, 1, 1),
                   'atmprf': pysat.datetime(2008, 1, 1)}}


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data.

    Parameters
    ----------
    tag : (string or NoneType)
        Denotes type of file to load.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : (NoneType)
        User specified file format not supported here. (default=None)

    Returns
    -------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    """
    estr = 'Building a list of COSMIC files, which can possibly take time. '
    print('{:s}~1s per 100K files'.format(estr))
    sys.stdout.flush()

    # number of files may be large, written with this in mind
    # only select file that are the cosmic data files and end with _nc
    fnames = glob.glob(os.path.join(data_path, '*/*_nc'))
    # need to get date and time from filename to generate index
    num = len(fnames)
    if num != 0:
        print('Estimated time:', num * 1.E-5, 'seconds')
        sys.stdout.flush()
        # preallocate lists
        year = [None] * num
        days = [None] * num
        hours = [None] * num
        minutes = [None] * num
        microseconds = [None] * num
        for i, f in enumerate(fnames):
            f2 = f.split('.')
            year[i] = f2[-6]
            days[i] = f2[-5]
            hours[i] = f2[-4]
            minutes[i] = f2[-3]
            microseconds[i] = i

        year = np.array(year).astype(int)
        days = np.array(days).astype(int)
        uts = (np.array(hours).astype(int) * 3600.
               + np.array(minutes).astype(int) * 60.)
        # adding microseconds to ensure each time is unique, not allowed to
        # pass 1.E-3 s
        uts += np.mod(np.array(microseconds).astype(int) * 4, 8000) * 1.E-5
        index = pysat.utils.time.create_datetime_index(year=year, day=days,
                                                       uts=uts)
        file_list = pysat.Series(fnames, index=index)
        return file_list
    else:
        print('Found no files, check your path or download them.')
        return pysat.Series(None)


def load(fnames, tag=None, sat_id=None):
    """Load COSMIC GPS files.

    Parameters
    ----------
    fnames : (pandas.Series)
        Series of filenames
    tag : (str or NoneType)
        tag or None (default=None)
    sat_id : (str or NoneType)
        satellite id or None (default=None)

    Returns
    -------
    output : (pandas.DataFrame)
        Object containing satellite data
    meta : (pysat.Meta)
        Object containing metadata such as column names and units

    """

    num = len(fnames)
    # make sure there are files to read
    if num != 0:
        # call separate load_files routine, segemented for possible
        # multiprocessor load, not included and only benefits about 20%
        output = pysat.DataFrame(load_files(fnames, tag=tag, sat_id=sat_id))
        utsec = output.hour * 3600. + output.minute * 60. + output.second
        output.index = \
            pysat.utils.time.create_datetime_index(year=output.year,
                                                   month=output.month,
                                                   day=output.day,
                                                   uts=utsec)
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


# seperate routine for doing actual loading. This was broken off from main load
# becuase I was playing around with multiprocessor loading
# yielded about 20% improvement in execution time
def load_files(files, tag=None, sat_id=None, altitude_bin=None):
    """Load COSMIC data files directly from a given list.

    May be directly called by user, but in general is called by load.  This is
    separate from the main load function for future support of multiprocessor
    loading.

    Parameters
    ----------
    files : (pandas.Series)
        Series of filenames
    tag : (str or NoneType)
        tag or None (default=None)
    sat_id : (str or NoneType)
        satellite id or None (default=None)
    altitude_bin : integer
        Number of kilometers to bin altitude profiles by when loading.
        Currently only supported for tag='ionprf'.

    Returns
    -------
    output : (list of dicts, one per file)
        Object containing satellite data

    """
    output = [None] * len(files)
    drop_idx = []
    for (i, file) in enumerate(files):
        try:
            data = netCDF4.Dataset(file)
            # build up dictionary will all ncattrs
            new = {}
            # get list of file attributes
            ncattrsList = data.ncattrs()
            for d in ncattrsList:
                new[d] = data.getncattr(d)
            # load all of the variables in the netCDF
            loadedVars = {}
            keys = data.variables.keys()
            for key in keys:
                if data.variables[key][:].dtype.byteorder != '=':
                    loadedVars[key] = \
                        data.variables[key][:].byteswap().newbyteorder()
                else:
                    loadedVars[key] = data.variables[key][:]

            new['profiles'] = pysat.DataFrame(loadedVars)

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
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Returns
    -------
    Void : (NoneType)
        data in inst is modified in-place.

    """
    import requests
    from requests.auth import HTTPBasicAuth
    import os
    import tarfile
    import shutil

    if tag == 'ionprf':
        sub_dir = 'ionPrf'
    elif tag == 'sonprf':
        sub_dir = 'sonPrf'
    elif tag == 'wetprf':
        sub_dir = 'wetPrf'
    elif tag == 'atmPrf':
        sub_dir = 'atmPrf'
    else:
        raise ValueError('Unknown cosmic_gps tag')

    if (user is None) or (password is None):
        raise ValueError('CDAAC user account information must be provided.')

    for date in date_array:
        print('Downloading COSMIC data for ' + date.strftime('%D'))
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
        # if repsonse is negative, try post-processed data
            try:
                dwnld = ''.join(("https://cdaac-www.cosmic.ucar.edu/cdaac/",
                                 "rest/tarservice/data/cosmic/"))
                dwnld = dwnld + sub_dir + '/{year:04d}.{doy:03d}'
                dwnld = dwnld.format(year=yr, doy=doy)
                top_dir = os.path.join(data_path, 'cosmic')
                req = requests.get(dwnld, auth=HTTPBasicAuth(user, password))
                req.raise_for_status()
            except requests.exceptions.HTTPError as err:
                estr = ''.join(str(err), '\n', 'Data not found')
                print(estr)
        fname = os.path.join(data_path,
                             'cosmic_' + sub_dir + '_' + yrdoystr + '.tar')
        with open(fname, "wb") as local_file:
            local_file.write(req.content)
            local_file.close()
        # uncompress files and remove tarball
        tar = tarfile.open(fname)
        tar.extractall(path=data_path)
        tar.close()
        os.remove(fname)
        # move files
        source_dir = os.path.join(top_dir, sub_dir, yrdoystr)
        destination_dir = os.path.join(data_path, yrdoystr)
        if os.path.exists(destination_dir):
            shutil.rmtree(destination_dir)
        shutil.move(source_dir, destination_dir)
        # Get rid of empty directories from tar process
        shutil.rmtree(top_dir)

    return


def clean(inst):
    """Return COSMIC GPS data cleaned to the specified level.

    Parameters
    ----------
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Returns
    -------
    Void : (NoneType)
        data in inst is modified in-place.

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

    elif inst.tag == 'scnlvl1':
        # scintillation files
        if inst.clean_level == 'clean':
            # try and make sure all data is good
            # filter out profiles where source provider processing doesn't
            # work
            inst.data = inst.data[((inst['alttp_s4max'] != -999.) &
                                   (inst['s4max9sec'] != -999.))]

    return
