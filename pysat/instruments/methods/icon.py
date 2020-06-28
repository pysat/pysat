# -*- coding: utf-8 -*-
"""Provides non-instrument routines for DEMETER microsatellite data"""

from __future__ import absolute_import, division, print_function

import ftplib
from ftplib import FTP
import os

import pysat

import logging
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


def ssl_download(date_array, tag, sat_id, data_path=None,
                 user=None, password=None, supported_tags=None,
                 ftp_dir=None):
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

    # connect to CDAWeb default port
    ftp = FTP('icon-science.ssl.berkeley.edu')

    # user anonymous, passwd anonymous@
    ftp.login()

    try:
        ftp_dict = supported_tags[sat_id][tag]
    except KeyError:
        raise ValueError('sat_id/tag name unknown.')

    # path to relevant file on CDAWeb
    ftp.cwd(ftp_dict['dir'])

    # naming scheme for files on the CDAWeb server
    remote_fname = ftp_dict['remote_fname']

    # naming scheme for local files, should be closely related
    # to CDAWeb scheme, though directory structures may be reduced
    # if desired
    local_fname = ftp_dict['local_fname']

    for date in date_array:
        # format files for specific dates and download location
        yr, doy = pysat.utils.time.getyrdoy(date)
        formatted_remote_fname = remote_fname.format(year=yr,
                                                     doy=doy,
                                                     month=date.month,
                                                     day=date.day)
        formatted_local_fname = local_fname.format(year=yr,
                                                   doy=doy,
                                                   month=date.month,
                                                   day=date.day)
        saved_local_fname = os.path.join(data_path, formatted_local_fname)

        # perform download
        try:
            logger.info(' '.join(('Attempting to download file for',
                                  date.strftime('%x'))))
            logger.info(formatted_remote_fname)
            ftp.retrbinary('RETR ' + formatted_remote_fname,
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
