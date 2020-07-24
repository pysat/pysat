# -*- coding: utf-8 -*-
"""Supports the Michelson Interferometer for Global High-resolution
Thermospheric Imaging (MIGHTI) instrument onboard the Ionospheric
CONnection Explorer (ICON) satellite.  Accesses local data in
netCDF format.

Properties
----------
platform
    'icon'
name
    'mighti'
tag
    Supports 'los_wind_green', 'los_wind_red', 'vector_wind_green',
    'vector_wind_red', 'temperature'.  Note that not every data product
    available for every sat_id
sat_id
    '', 'a', or 'b'


Warnings
--------
- The cleaning parameters for the instrument are still under development.
- Only supports level-2 data.


Example
-------
::

    import pysat
    mighti = pysat.Instrument('icon', 'mighti', 'vector_wind_green',
                              clean_level='clean')
    mighti.download(dt.datetime(2020, 1, 30), dt.datetime(2020, 1, 31))
    mighti.load(2020, 2)

By default, pysat removes the ICON level tags from variable names, ie,
ICON_L27_Ion_Density becomes Ion_Density.  To retain the original names, use
::

    mighti = pysat.Instrument(platform='icon', name='mighti',
                              tag='vector_wind_green', clean_level='clean',
                              keep_original_names=True)


Authors
---------
Originated from EUV support.
Jeff Klenzing, Mar 17, 2018, Goddard Space Flight Center
Russell Stoneback, Mar 23, 2018, University of Texas at Dallas
Conversion to MIGHTI, Oct 8th, 2028, University of Texas at Dallas

"""

from __future__ import print_function
from __future__ import absolute_import

import datetime as dt
import functools
import logging

import pysat
from pysat.instruments.methods import general as mm_gen
from pysat.instruments.methods import icon as mm_icon


logger = logging.getLogger(__name__)

platform = 'icon'
name = 'mighti'
tags = {'los_wind_green': 'Line of sight wind data -- Green Line',
        'los_wind_red': 'Line of sight wind data -- Red Line',
        'vector_wind_green': 'Vector wind data -- Green Line',
        'vector_wind_red': 'Vector wind data -- Red Line',
        'temperature': 'Neutral temperature data'}
sat_ids = {'': ['vector_wind_green', 'vector_wind_red'],
           'a': ['los_wind_green', 'los_wind_red', 'temperature'],
           'b': ['los_wind_green', 'los_wind_red', 'temperature']}
_test_dates = {jj: {kk: dt.datetime(2020, 1, 2) for kk in sat_ids[jj]}
               for jj in sat_ids.keys()}
_test_download_travis = {jj: {kk: False for kk in sat_ids[jj]}
                         for jj in sat_ids.keys()}
pandas_format = False

datestr = '{year:04d}-{month:02d}-{day:02d}_v{version:02d}r{revision:03d}'
fname1 = 'ICON_L2-1_MIGHTI-{id:s}_LOS-Wind-{color:s}_{date:s}.NC'
fname2 = 'ICON_L2-2_MIGHTI_Vector-Wind-{color:s}_{date:s}.NC'
fname3 = 'ICON_L2-3_MIGHTI-{id:s}_Temperature_{date:s}.NC'
supported_tags = {'': {'vector_wind_green': fname2.format(color='Green',
                                                          date=datestr),
                       'vector_wind_red': fname2.format(color='Red',
                                                        date=datestr)},
                  'a': {'los_wind_green': fname1.format(id='A', color='Green',
                                                        date=datestr),
                        'los_wind_red': fname1.format(id='A', color='Red',
                                                      date=datestr),
                        'temperature': fname3.format(id='A', date=datestr)},
                  'b': {'los_wind_green': fname1.format(id='B', color='Green',
                                                        date=datestr),
                        'los_wind_red': fname1.format(id='B', color='Red',
                                                      date=datestr),
                        'temperature': fname3.format(id='B', date=datestr)}}

# use the CDAWeb methods list files routine
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# support download routine
dirstr = '/pub/LEVEL.2/MIGHTI{id:s}'
dirdatestr = '{year:4d}/{doy:03d}/'
ids = {'': '',
       'a': '-A',
       'b': '-B'}
products = {'vector_wind_green': 'Vector-Winds/',
            'vector_wind_red': 'Vector-Winds/',
            'los_wind_green': 'LOS-Winds/',
            'los_wind_red': 'LOS-Winds/',
            'temperature': 'Temperature/'}
datestr = '{year:04d}-{month:02d}-{day:02d}'

download_tags = {}
for skey in supported_tags.keys():
    download_tags[skey] = {}
    for tkey in supported_tags[skey].keys():
        fname = supported_tags[skey][tkey]

        download_tags[skey][tkey] = {'dir': dirstr.format(id=ids[skey]),
                                     'remote_fname': ''.join((products[tkey],
                                                              fname))}

download = functools.partial(mm_icon.ssl_download, supported_tags=download_tags)

# support listing files on SSL
list_remote_files = functools.partial(mm_icon.list_remote_files,
                                      supported_tags=download_tags)


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    -----------
    inst : (pysat.Instrument)
        Instrument class object

    """

    logger.info(mm_icon.ackn_str)
    self.meta.acknowledgements = mm_icon.ackn_str
    self.meta.references = ''.join((mm_icon.refs['mission'],
                                    mm_icon.refs['mighti']))

    pass


def default(inst):
    """Default routine to be applied when loading data.  Adjusts epoch timestamps
    to datetimes and removes variable preambles.

    """

    mm_gen.convert_timestamp_to_datetime(inst, sec_mult=1.0e-3)
    if not inst.kwargs['keep_original_names']:
        remove_preamble(inst)


def remove_preamble(inst):
    """Removes preambles in variable names"""

    target = {'los_wind_green': 'ICON_L21_',
              'los_wind_red': 'ICON_L21_',
              'vector_wind_green': 'ICON_L22_',
              'vector_wind_red': 'ICON_L22_',
              'temperature': ['ICON_L1_MIGHTI_{}_'.format(inst.sat_id.upper()),
                              'ICON_L23_MIGHTI_{}_'.format(inst.sat_id.upper()),
                              'ICON_L23_']}
    mm_gen.remove_leading_text(inst, target=target[inst.tag])

    return


def load(fnames, tag=None, sat_id=None, keep_original_names=False):
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
    keep_original_names : boolean
        if True then the names as given in the netCDF ICON file
        will be used as is. If False, a preamble is removed.

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
        inst.load(2020, 1)

    """

    data, mdata = pysat.utils.load_netcdf4(fnames, epoch_name='Epoch',
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
    # xarray can't merge if variable and dim names are the same
    if 'Altitude' in data.dims:
        data = data.rename({'Altitude': 'Alt'})
    return data, mdata


def clean(inst):
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

    Note
    ----
        Supports 'clean', 'dusty', 'dirty', 'none'

    """

    if inst.tag.find('los') >= 0:
        # dealing with LOS winds
        wind_flag = 'Wind_Quality'
        ver_flag = 'VER_Quality'
        wind_vars = ['Line_of_Sight_Wind', 'Line_of_Sight_Wind_Error']
        ver_vars = ['Fringe_Amplitude', 'Fringe_Amplitude_Error',
                    'Relative_VER', 'Relative_VER_Error']
        if wind_flag not in inst.variables:
            wind_flag = '_'.join(('ICON_L21', wind_flag))
            ver_flag = '_'.join(('ICON_L21', ver_flag))
            wind_vars = ['ICON_L21_' + var for var in wind_vars]
            ver_vars = ['ICON_L21_' + var for var in ver_vars]
        min_val = {'clean': 1.0,
                   'dusty': 0.5}
        if inst.clean_level in ['clean', 'dusty']:
            # find location with any of the flags set
            for var in wind_vars:
                inst[var] = inst[var].where(inst[wind_flag]
                                            >= min_val[inst.clean_level])
            for var in ver_vars:
                inst[var] = inst[var].where(inst[ver_flag]
                                            >= min_val[inst.clean_level])
        else:
            # dirty and worse lets everything through
            pass

    elif inst.tag.find('vector') >= 0:
        # vector winds area
        wind_flag = 'Wind_Quality'
        ver_flag = 'VER_Quality'
        wind_vars = ['Zonal_Wind', 'Zonal_Wind_Error',
                     'Meridional_Wind', 'Meridional_Wind_Error']
        ver_vars = ['Fringe_Amplitude', 'Fringe_Amplitude_Error',
                    'Relative_VER', 'Relative_VER_Error']
        if wind_flag not in inst.variables:
            wind_flag = '_'.join(('ICON_L22', wind_flag))
            ver_flag = '_'.join(('ICON_L22', ver_flag))
            wind_vars = ['ICON_L22_' + var for var in wind_vars]
            ver_vars = ['ICON_L22_' + var for var in ver_vars]
        min_val = {'clean': 1.0,
                   'dusty': 0.5}
        if inst.clean_level in ['clean', 'dusty']:
            # find location with any of the flags set
            for var in wind_vars:
                inst[var] = inst[var].where(inst[wind_flag]
                                            >= min_val[inst.clean_level])
            for var in ver_vars:
                inst[var] = inst[var].where(inst[ver_flag]
                                            >= min_val[inst.clean_level])
        else:
            # dirty lets everything through
            pass

    elif inst.tag.find('temp') >= 0:
        # neutral temperatures
        var = 'Temperature'
        saa_flag = 'Quality_Flag_South_Atlantic_Anomaly'
        cal_flag = 'Quality_Flag_Bad_Calibration'
        if saa_flag not in inst.variables:
            saa_flag = '_'.join(('ICON_L1_MIGHTI', inst.sat_id.upper(),
                                 saa_flag))
            cal_flag = '_'.join(('ICON_L1_MIGHTI', inst.sat_id.upper(),
                                 cal_flag))
            var = '_'.join(('ICON_L23_MIGHTI', inst.sat_id.upper(), var))
        if inst.clean_level in ['clean', 'dusty']:
            # filter out areas with bad calibration data
            # as well as data marked in the SAA
            inst[var] = inst[var].where((inst[saa_flag] == 0)
                                        & (inst[cal_flag] == 0))
            # filter out negative temperatures
            inst[var] = inst[var].where(inst[var] > 0)
        else:
            # dirty and worse lets everything through
            pass

    return
