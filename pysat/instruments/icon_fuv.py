# -*- coding: utf-8 -*-
"""Supports the Far Ultraviolet (FUV) imager onboard the Ionospheric
CONnection Explorer (ICON) satellite.  Accesses local data in
netCDF format.

Parameters
----------
platform : string
    'icon'
name : string
    'fuv'
tag : string
    None supported

Warnings
--------
- The cleaning parameters for the instrument are still under development.
- Only supports level-2 data.

Example
-------
    import pysat
    fuv = pysat.Instrument('icon', 'fuv', clean_level='clean')
    fuv.download(dt.datetime(2019, 1, 30), dt.datetime(2019, 12, 31))
    fuv.load(2017,363)

Authors
---------
Originated from EUV support.
Jeff Klenzing, Mar 17, 2018, Goddard Space Flight Center
Russell Stoneback, Mar 23, 2018, University of Texas at Dallas
Conversion to FUV, Oct 8th, 2028, University of Texas at Dallas

"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import functools
import pandas as pds
import warnings

import pysat
from pysat.instruments.methods import general as mm_gen
from pysat.instruments.icon_euv import icon_ssl_download
import logging
logger = logging.getLogger(__name__)


platform = 'icon'
name = 'fuv'
tags = {'day': 'Level 2 daytime O/N2',
        'night': 'Level 2 nighttime O profile'}
sat_ids = {'': ['day', 'night']}
_test_dates = {'': {kk: dt.datetime(2020, 1, 1) for kk in tags.keys()}}
_test_download_travis = {'': {kk: False for kk in tags.keys()}}
pandas_format = False

fname24 = 'ICON_L2-4_FUV_Day_{year:04d}-{month:02d}-{day:02d}_v03r001.NC'
fname25 = 'ICON_L2-5_FUV_Night_{year:04d}-{month:02d}-{day:02d}_v03r000.NC'
supported_tags = {'': {'day': fname24,
                       'night': fname25}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# support download routine
basic_tag24 = {'dir': '/pub/LEVEL.2/FUV',
               'remote_fname': '{year:4d}/{doy:03d}/' + fname24,
               'local_fname': fname24}
basic_tag25 = {'dir': '/pub/LEVEL.2/FUV',
               'remote_fname': '{year:4d}/{doy:03d}/' + fname25,
               'local_fname': fname25}

download_tags = {'': {'day': basic_tag24,
                      'night': basic_tag25}}

download = functools.partial(icon_ssl_download, supported_tags=download_tags,
                             ftp_dir='/pub/LEVEL.2/FUV')


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    Returns
    --------
    Void : (NoneType)
        modified in-place, as desired.

    """

    logger.info(''.join(( 'This is a data product from the NASA Ionospheric '
                          'Connection Explorer mission, an Explorer launched '
                          'at 21:59:45 EDT on October 10, 2019.\n\nGuidelines '
                          'for the use of this product are described in the '
                          'ICON Rules of the Road  '
                          '(https://http://icon.ssl.berkeley.edu/Data).'
                          '\n\nResponsibility for the mission science '
                          'falls to the Principal Investigator, Dr. '
                          'Thomas Immel at UC Berkeley:\nImmel, T.J., '
                          'England, S.L., Mende, S.B. et al. Space Sci Rev '
                          '(2018) 214: 13. '
                          'https://doi.org/10.1007/s11214-017-0449-2\n\n'
                          'Responsibility for the validation of the L1 data '
                          'products falls to the instrument lead investigators/'
                          'scientists.\n* EUV: Dr. Eric Korpela :  '
                          'https://doi.org/10.1007/s11214-017-0384-2\n * FUV: '
                          'Dr. Harald Frey : https://doi.org/10.1007/s11214-017-0386-0\n* '
                          'MIGHTI: Dr. Christoph Englert : https://doi.org/10.10'
                          '07/s11214-017-0358-4, and https://doi.org/10.1007/s11'
                          '214-017-0374-4\n* IVM: Dr. Roderick Heelis : '
                          'https://doi.org/10.1007/s11214-017-0383-3\n\n '
                          'Responsibility for the validation of the L2 data '
                          'products falls to those scientists responsible for '
                          'those products.\n * Daytime O and N2 profiles: Dr. '
                          'Andrew Stephan : '
                          'https://doi.org/10.1007/s11214-018-0477-6\n* Daytime '
                          '(EUV) O+ profiles: Dr. Andrew Stephan : '
                          'https://doi.org/10.1007/s11214-017-0385-1\n* '
                          'Nighttime (FUV) O+ profiles: Dr. Farzad Kamalabadi : '
                          'https://doi.org/10.1007/s11214-018-0502-9\n* Neutral'
                          ' Wind profiles: Dr. Jonathan Makela :'
                          ' https://doi.org/10.1007/s11214-017-0359-3\n* '
                          'Neutral Temperature profiles: Dr. Christoph Englert '
                          ': https://doi.org/10.1007/s11214-017-0434-9\n* Ion '
                          'Velocity Measurements : Dr. Russell Stoneback : '
                          'https://doi.org/10.1007/s11214-017-0383-3\n\n'
                          'Responsibility for Level 4 products falls to those '
                          'scientists responsible for those products.\n*'
                          ' Hough Modes : Dr. Chihoko Yamashita :  '
                          'https://doi.org/10.1007/s11214-017-0401-5\n* TIEGCM : '
                          'Dr. Astrid Maute : '
                          'https://doi.org/10.1007/s11214-017-0330-3\n* '
                          'SAMI3 : Dr. Joseph Huba : '
                          'https://doi.org/10.1007/s11214-017-0415-z\n\n'
                          'Pre-production versions of all above papers are '
                          'available on the ICON website.\n\nOverall validation '
                          'of the products is overseen by the ICON Project '
                          'Scientist, Dr. Scott England.\n\nNASA oversight for '
                          'all products is provided by the Mission Scientist, '
                          'Dr. Jeffrey Klenzing.\n\nUsers of these data should '
                          'contact and acknowledge the Principal Investigator '
                          'Dr. Immel and the party directly responsible for the '
                          'data product (noted above) and acknowledge NASA '
                          'funding for the collection of the data used in the '
                          'research with the following statement : "ICON is '
                          'supported by NASA’s Explorers Program through '
                          'contracts NNG12FA45C and NNG12FA42I".\n\nThese data '
                          'are openly available as described in the ICON Data '
                          'Management Plan available on the ICON website '
                          '(http://icon.ssl.berkeley.edu/Data).')))

    pass


def default(inst):
    """Default routine to be applied when loading data.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    Note
    ----
        Removes ICON preamble on variable names.

    """

    # Use datetime instead of timestamp for Epoch
    inst.data['Epoch'] = pds.to_datetime([dt.datetime.utcfromtimestamp(x/1000)
                                          for x in inst.data['Epoch']])
    target = {'day': 'ICON_L24_',
              'night': 'ICON_L25_'}
    mm_gen.remove_leading_text(inst, target=target[inst.tag])


def load(fnames, tag=None, sat_id=None):
    """Loads ICON FUV data using pysat into pandas.

    This routine is called as needed by pysat. It is not intended
    for direct user interaction.

    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : string
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    sat_id : string
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself.
    **kwargs : extra keywords
        Passthrough for additional keyword arguments specified when
        instantiating an Instrument object. These additional keywords
        are passed through to this routine by pysat.

    Returns
    -------
    data, metadata
        Data and Metadata are formatted for pysat. Data is a pandas
        DataFrame while metadata is a pysat.Meta instance.

    Note
    ----
    Any additional keyword arguments passed to pysat.Instrument
    upon instantiation are passed along to this routine.

    Examples
    --------
    ::
        inst = pysat.Instrument('icon', 'fuv')
        inst.load(2019,1)

    """

    return pysat.utils.load_netcdf4(fnames, epoch_name='Epoch',
                                    units_label='Units',
                                    name_label='Long_Name',
                                    notes_label='Var_Notes',
                                    desc_label='CatDesc',
                                    plot_label='FieldNam',
                                    axis_label='LablAxis',
                                    scale_label='ScaleTyp',
                                    min_label='ValidMin',
                                    max_label='ValidMax',
                                    fill_label='FillVal',
                                    pandas_format=pandas_format)


def clean(inst, clean_level=None):
    """Provides data cleaning based upon clean_level.

    clean_level is set upon Instrument instantiation to
    one of the following:

    'Clean'
    'Dusty'
    'Dirty'
    'None'

    Routine is called by pysat, and not by the end user directly.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Returns
    --------
    Void : (NoneType)
        data in inst is modified in-place.

    Note
    ----
        Supports 'clean', 'dusty', 'dirty', 'none'

    """

    if clean_level != 'none':
        warnings.warn("Cleaning actions for ICON FUV are not yet defined.")
    return
