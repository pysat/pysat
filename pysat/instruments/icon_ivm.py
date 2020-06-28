# -*- coding: utf-8 -*-

"""Supports the Ion Velocity Meter (IVM)
onboard the Ionospheric Connections (ICON) Explorer.

Parameters
----------
platform : string
    'icon'
name : string
    'ivm'
tag : string
    None supported
sat_id : string
    'a' or 'b'

Warnings
--------
- No download routine as ICON has not yet been launched
- Data not yet publicly available

Example
-------
    import pysat
    ivm = pysat.Instrument('icon', 'ivm', sat_id='a', clean_level='clean')
    ivm.download(dt.datetime(2020, 1, 1), dt.datetime(2020, 1, 31))
    ivm.load(2020, 1)

Author
------
R. A. Stoneback

"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import functools
import numpy as np
import warnings

import pysat
from pysat.instruments.methods import general as mm_gen
from pysat.instruments.icon_euv import icon_ssl_download

import logging
logger = logging.getLogger(__name__)


platform = 'icon'
name = 'ivm'
tags = {'': 'Level 2 public geophysical data'}
# dictionary of sat_ids ad tags supported by each
sat_ids = {'a': [''],
           'b': ['']}
# Note for developers: IVM-A and IVM-B face in opposite directions, and only
# one is expected to have geophysical data at a given time depedning on ram
# direction.  IVM-B data is not available as of Jun 26 2020, as this mode has
# not yet been engaged.  Bypassing tests and warning checks via the password_req
# flag
_test_dates = {'a': {'': dt.datetime(2020, 1, 1)},
               'b': {'': dt.datetime(2020, 1, 1)}}  # IVM-B not yet engaged
_test_download_travis = {'a': {kk: False for kk in tags.keys()}}
_test_download = {'b': {kk: False for kk in tags.keys()}}
_password_req = {'b': {kk: True for kk in tags.keys()}}

aname = 'ICON_L2-7_IVM-A_{year:04d}-{month:02d}-{day:02d}_v02r002.NC'
bname = 'ICON_L2-7_IVM-B_{year:04d}-{month:02d}-{day:02d}_v02r002.NC'
supported_tags = {'a': {'': aname},
                  'b': {'': bname}}

# use the general methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# support download routine
basic_tag_a = {'dir': '/pub/LEVEL.2/IVM-A',
               'remote_fname': '{year:4d}/{doy:03d}/Data/' + aname,
               'local_fname': aname}
basic_tag_b = {'dir': '/pub/LEVEL.2/IVM-B',
               'remote_fname': '{year:4d}/{doy:03d}/Data/' + aname,
               'local_fname': aname}

download_tags = {'a': {'': basic_tag_a},
                 'b': {'': basic_tag_b}}
download = functools.partial(icon_ssl_download, supported_tags=download_tags)


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

    mm_gen.remove_leading_text(inst, target='ICON_L27_')


def load(fnames, tag=None, sat_id=None):
    """Loads ICON IVM data using pysat into pandas.

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
        inst = pysat.Instrument('icon', 'ivm', sat_id='a', tag='')
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
                                    fill_label='FillVal')


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
        # IVM variable groupings
        drift_variables = ['Ion_Velocity_X', 'Ion_Velocity_Zonal',
                           'Ion_Velocity_Meridional', 'Ion_Velocity_Field_Aligned']
        cross_drift_variables = ['Ion_Velocity_Z', 'Ion_Velocity_Y']
        rpa_variables = ['Ion_Temperature', 'Ion_Density', 'Fractional_Ion_Density_H',
                         'Fractional_Ion_Density_O']

        if clean_level == 'clean' or (clean_level == 'dusty'):
            # remove drift values impacted by RPA
            idx, = np.where(inst['RPA_Flag'] >= 1)
            for var in drift_variables:
                inst[idx, var] = np.nan
            # DM values
            idx, = np.where(inst['DM_Flag'] >= 1)
            for var in cross_drift_variables:
                inst[idx, var] = np.nan

        if clean_level == 'clean':
            # other RPA parameters
            idx, = np.where(inst['RPA_Flag'] >= 2)
            for var in rpa_variables:
                inst[idx, var] = np.nan

    return
