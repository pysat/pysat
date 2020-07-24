# -*- coding: utf-8 -*-
"""Provides non-instrument specific routines for ICON data"""

from __future__ import absolute_import, division, print_function

import fnmatch
import ftplib
import logging
import numpy as np
import os

import pysat
import pysat._files as pfiles


logger = logging.getLogger(__name__)

ackn_str = ''.join(('This is a data product from the NASA Ionospheric ',
                    'Connection Explorer mission, an Explorer launched ',
                    'at 21:59:45 EDT on October 10, 2019.\n\nGuidelines ',
                    'for the use of this product are described in the ',
                    'ICON Rules of the Road  ',
                    '(https://http://icon.ssl.berkeley.edu/Data).',
                    '\n\nResponsibility for the mission science ',
                    'falls to the Principal Investigator, Dr. ',
                    'Thomas Immel at UC Berkeley:\nImmel, T.J., ',
                    'England, S.L., Mende, S.B. et al. Space Sci Rev ',
                    '(2018) 214: 13. ',
                    'https://doi.org/10.1007/s11214-017-0449-2\n\n',
                    'Responsibility for the validation of the L1 data ',
                    'products falls to the instrument lead investigators/',
                    'scientists.\n* EUV: Dr. Eric Korpela :  https://',
                    'doi.org/10.1007/s11214-017-0384-2\n * FUV: Dr. Harald ',
                    'Frey : https://doi.org/10.1007/s11214-017-0386-0\n* ',
                    'MIGHTI: Dr. Christoph Englert : https://doi.org/10.10',
                    '07/s11214-017-0358-4, and https://doi.org/10.1007/s11',
                    '214-017-0374-4\n* IVM: Dr. Roderick Heelis : ',
                    'https://doi.org/10.1007/s11214-017-0383-3\n\n ',
                    'Responsibility for the validation of the L2 data ',
                    'products falls to those scientists responsible for ',
                    'those products.\n * Daytime O and N2 profiles: Dr. ',
                    'Andrew Stephan : ',
                    'https://doi.org/10.1007/s11214-018-0477-6\n* Daytime ',
                    '(EUV) O+ profiles: Dr. Andrew Stephan : ',
                    'https://doi.org/10.1007/s11214-017-0385-1\n* ',
                    'Nighttime (FUV) O+ profiles: Dr. Farzad Kamalabadi : ',
                    'https://doi.org/10.1007/s11214-018-0502-9\n* Neutral',
                    ' Wind profiles: Dr. Jonathan Makela :',
                    ' https://doi.org/10.1007/s11214-017-0359-3\n* ',
                    'Neutral Temperature profiles: Dr. Christoph Englert ',
                    ': https://doi.org/10.1007/s11214-017-0434-9\n* Ion ',
                    'Velocity Measurements : Dr. Russell Stoneback : ',
                    'https://doi.org/10.1007/s11214-017-0383-3\n\n',
                    'Responsibility for Level 4 products falls to those ',
                    'scientists responsible for those products.\n*',
                    ' Hough Modes : Dr. Chihoko Yamashita :  ',
                    'https://doi.org/10.1007/s11214-017-0401-5\n* TIEGCM : ',
                    'Dr. Astrid Maute : ',
                    'https://doi.org/10.1007/s11214-017-0330-3\n* ',
                    'SAMI3 : Dr. Joseph Huba : ',
                    'https://doi.org/10.1007/s11214-017-0415-z\n\n',
                    'Pre-production versions of all above papers are ',
                    'available on the ICON website.\n\nOverall validation ',
                    'of the products is overseen by the ICON Project ',
                    'Scientist, Dr. Scott England.\n\nNASA oversight for ',
                    'all products is provided by the Mission Scientist, ',
                    'Dr. Jeffrey Klenzing.\n\nUsers of these data should ',
                    'contact and acknowledge the Principal Investigator ',
                    'Dr. Immel and the party directly responsible for the ',
                    'data product (noted above) and acknowledge NASA ',
                    'funding for the collection of the data used in the ',
                    'research with the following statement : "ICON is ',
                    'supported by NASA’s Explorers Program through ',
                    'contracts NNG12FA45C and NNG12FA42I".\n\nThese data ',
                    'are openly available as described in the ICON Data ',
                    'Management Plan available on the ICON website ',
                    '(http://icon.ssl.berkeley.edu/Data).'))

refs = {'euv': ' '.join(('Stephan, A.W., Meier, R.R., England, S.L. et al.',
                         'Daytime O/N2 Retrieval Algorithm for the Ionospheric',
                         'Connection Explorer (ICON). Space Sci Rev 214, 42',
                         '(2018). https://doi.org/10.1007/s11214-018-0477-6\n',
                         'Stephan, A.W., Korpela, E.J., Sirk, M.M. et al.',
                         'Daytime Ionosphere Retrieval Algorithm for the',
                         'Ionospheric Connection Explorer (ICON). Space Sci',
                         'Rev 212, 645–654 (2017).',
                         'https://doi.org/10.1007/s11214-017-0385-1')),
        'fuv': ' '.join(('Kamalabadi, F., Qin, J., Harding, B.J. et al.',
                         'Inferring Nighttime Ionospheric Parameters with the',
                         'Far Ultraviolet Imager Onboard the Ionospheric',
                         'Connection Explorer. Space Sci Rev 214, 70 (2018).',
                         'https://doi.org/10.1007/s11214-018-0502-9')),
        'ivm': ' '.join(('Heelis, R.A., Stoneback, R.A., Perdue, M.D. et al.',
                         'Ion Velocity Measurements for the Ionospheric',
                         'Connections Explorer. Space Sci Rev 212, 615–629',
                         '(2017). https://doi.org/10.1007/s11214-017-0383-3')),
        'mighti': ' '.join(('Harding, B.J., Makela, J.J., Englert, C.R. et al.',
                            'The MIGHTI Wind Retrieval Algorithm: Description',
                            'and Verification. Space Sci Rev 212, 585–600',
                            '(2017).',
                            'https://doi.org/10.1007/s11214-017-0359-3\n',
                            'Stevens, M.H., Englert, C.R., Harlander, J.M. et',
                            'al. Retrieval of Lower Thermospheric Temperatures',
                            'from O2 A Band Emission: The MIGHTI Experiment on',
                            'ICON. Space Sci Rev 214, 4 (2018).',
                            'https://doi.org/10.1007/s11214-017-0434-9')),
        'mission': ' '.join(('Immel, T.J., England, S.L., Mende, S.B. et al.',
                             'The Ionospheric Connection Explorer Mission:',
                             'Mission Goals and Design. Space Sci Rev 214, 13',
                             '(2018).',
                             'https://doi.org/10.1007/s11214-017-0449-2\n'))}


def list_remote_files(tag, sat_id, user=None, password=None,
                      supported_tags=None,
                      year=None, month=None, day=None,
                      start=None, stop=None):
    """Return a Pandas Series of every file for chosen remote data.

    This routine is intended to be used by pysat instrument modules supporting
    a particular UC-Berkeley SSL dataset related to ICON.

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    user : (string or NoneType)
        Username to be passed along to resource with relevant data.
        (default=None)
    password : (string or NoneType)
        User password to be passed along to resource with relevant data.
        (default=None)
    start : (dt.datetime or NoneType)
        Starting time for file list. A None value will start with the first
        file found.
        (default=None)
    stop : (dt.datetime or NoneType)
        Ending time for the file list.  A None value will stop with the last
        file found.
        (default=None)

    Returns
    --------
    pandas.Series
        A Series formatted for the Files class (pysat._files.Files)
        containing filenames and indexed by date and time

    """

    if (user is not None) or (password is not None):
        raise ValueError('User account information must not be provided.')

    # connect to CDAWeb default port
    ftp = ftplib.FTP('icon-science.ssl.berkeley.edu')
    # user anonymous, passwd anonymous@
    ftp.login()

    try:
        ftp_dict = supported_tags[sat_id][tag]
    except KeyError:
        raise ValueError('sat_id/tag name unknown.')

    # naming scheme for files on the CDAWeb server
    remote_fname = ftp_dict['remote_fname']

    # will hold paths to remote locations
    remote_years = []
    remote_days = []
    temp_dirs = []

    # values of years and days with data
    years = []
    days = []
    yrdoys = []

    # path to highest directory, below which is custom structure
    # and files
    # change directory
    ftp.cwd(ftp_dict['dir'])
    # get directory contents
    ftp.dir(temp_dirs.append)
    # need to parse output to obtain list of paths to years
    for item in temp_dirs:
        # parse raw string
        parsed = item.split(' ')
        # print(parsed[-1])
        remote_years.append(ftp_dict['dir'] + '/' + parsed[-1])
        years.append(parsed[-1])

    # get files under each year, first identify day directories
    for year, year_int in zip(remote_years, years):
        ftp.cwd(year)
        # get list of days
        temp_dirs = []
        ftp.dir(temp_dirs.append)
        for item in temp_dirs:
            # parse raw string
            parsed = item.split(' ')
            # print(parsed[-1])
            remote_days.append(year + '/' + parsed[-1])
            days.append(parsed[-1])
            yrdoys.append(int(year_int) * 1000 + int(parsed[-1]))

    # potentially filter here for years and days that are out of bounds
    yrdoys = np.array(yrdoys)

    # use user supplied date limits or use min and max from observed files
    if start is None:
        syrdoy = np.min(yrdoys)
    else:
        syr, sdoy = pysat.utils.time.getyrdoy(start)
        syrdoy = syr * 1000 + sdoy

    if stop is None:
        eyrdoy = np.max(yrdoys)
    else:
        eyr, edoy = pysat.utils.time.getyrdoy(stop)
        eyrdoy = eyr * 1000 + edoy
    # apply date filter
    idx, = np.where((yrdoys >= syrdoy) & (yrdoys <= eyrdoy))
    remote_days = np.array(remote_days)[idx].tolist()

    # leading path, get any directory elements between the year/doy
    # and the start of actual files on SSL server
    leading_dirs = remote_fname.split('/')
    leading_dirs = leading_dirs[:-1]
    leading_dirs = '/'.join(leading_dirs)
    if leading_dirs != '':
        leading_dirs += '/'

    # get a list of files now that all leading portions determined
    day_file_list = []
    for remote_day in remote_days:
        temp_dirs = []
        ftp.cwd(remote_day + '/' + leading_dirs)
        ftp.dir(temp_dirs.append)
        for item in temp_dirs:
            # parse raw string
            parsed = item.split(' ')
            day_file_list.append(remote_day + '/' + leading_dirs + parsed[-1])

    # we now have a list of all files in the instrument data directories
    # need to whittle list down to the versions and revisions most appropriate
    search_dict = pysat._files.construct_searchstring_from_format(remote_fname)
    search_str = '*/' + search_dict['search_string']
    remote_files = fnmatch.filter(day_file_list, search_str)

    # pull out date information from the files
    stored = pfiles.parse_fixed_width_filenames(remote_files, remote_fname)
    output = pfiles.process_parsed_filenames(stored)
    # return information, limited to start and stop dates
    return output[start:stop]


def ssl_download(date_array, tag, sat_id, data_path=None,
                 user=None, password=None, supported_tags=None):
    """Download ICON data from public area of SSL ftp server

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : string ('')
        Tag identifier used for particular dataset. This input is provided by
        pysat.
    sat_id : string  ('')
        Satellite ID string identifier used for particular dataset. This input
        is provided by pysat.
    data_path : string (None)
        Path to directory to download data to.
    user : string (None)
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for downloads this routine here must
        error if user not supplied.
    password : string (None)
        Password for data download.
    **kwargs : dict
        Additional keywords supplied by user when invoking the download
        routine attached to a pysat.Instrument object are passed to this
        routine via kwargs.

    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.

    """

    # get a list of remote files
    remote_files = list_remote_files(tag, sat_id, supported_tags=supported_tags,
                                     start=date_array[0], stop=date_array[-1])

    # connect to CDAWeb default port
    ftp = ftplib.FTP('icon-science.ssl.berkeley.edu')

    # user anonymous, passwd anonymous@
    ftp.login()
    for date in date_array:
        if date in remote_files:
            fname = remote_files[date]
            # format files for specific dates and download location
            # yr, doy = pysat.utils.time.getyrdoy(date)
            saved_local_fname = os.path.join(data_path, fname.split('/')[-1])

            # perform download
            try:
                logger.info(' '.join(('Attempting to download file for',
                                      date.strftime('%x'))))
                logger.info(fname)
                ftp.retrbinary('RETR ' + fname,
                               open(saved_local_fname, 'wb').write)
                logger.info('Finished.')
            except ftplib.error_perm as exception:
                if str(exception.args[0]).split(" ", 1)[0] != '550':
                    raise
                else:
                    os.remove(saved_local_fname)
                    logger.info('File not available for ' + date.strftime('%x'))
    ftp.close()
    return
