# -*- coding: utf-8 -*-
"""Supports the Michelson Interferometer for Global High-resolution
Thermospheric Imaging (MIGHTI) instrument onboard the Ionospheric
CONnection Explorer (ICON) satellite.  Accesses local data in
netCDF format.

.. deprecated:: 2.3.0
  This Instrument module has been removed from pysat in the 3.0.0 release and
  can now be found in pysatNASA (https://github.com/pysat/pysatNASA).  Note that
  the ICON files are retrieved from different servers here and in pysatNASA,
  resulting in a difference in local file names. Please see the migration guide
  there for more details.

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
import warnings

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw
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
pandas_format = False

# Set the list_files routine
datestr = '{year:04d}{month:02d}{day:02d}'
fname1 = 'icon_l2-1_mighti-{id:s}_los-wind-{color:s}_{date:s}_v04r001.nc'
fname2 = 'icon_l2-2_mighti_vector-wind-{color:s}_{date:s}_v04r000.nc'
fname3 = 'icon_l2-3_mighti-{id:s}_temperature_{date:s}_v04r000.nc'
supported_tags = {'': {'vector_wind_green': fname2.format(color='green',
                                                          date=datestr),
                       'vector_wind_red': fname2.format(color='red',
                                                        date=datestr)},
                  'a': {'los_wind_green': fname1.format(id='a', color='green',
                                                        date=datestr),
                        'los_wind_red': fname1.format(id='a', color='red',
                                                      date=datestr),
                        'temperature': fname3.format(id='a', date=datestr)},
                  'b': {'los_wind_green': fname1.format(id='b', color='green',
                                                        date=datestr),
                        'los_wind_red': fname1.format(id='b', color='red',
                                                      date=datestr),
                        'temperature': fname3.format(id='b', date=datestr)}}

list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags)

# Set the download routine
dirstr1 = '/pub/data/icon/l2/l2-1_mighti-{{id:s}}_los-wind-{color:s}/'
dirstr2 = '/pub/data/icon/l2/l2-2_mighti_vector-wind-{color:s}/'
dirstr3 = '/pub/data/icon/l2/l2-3_mighti-{id:s}_temperature/'
dirnames = {'los_wind_green': dirstr1.format(color='green'),
            'los_wind_red': dirstr1.format(color='red'),
            'vector_wind_green': dirstr2.format(color='green'),
            'vector_wind_red': dirstr2.format(color='red'),
            'temperature': dirstr3}

download_tags = {}
for inst_id in supported_tags.keys():
    download_tags[inst_id] = {}
    for tag in supported_tags[inst_id].keys():
        fname = supported_tags[inst_id][tag]

        download_tags[inst_id][tag] = \
            {'dir': dirnames[tag].format(id=inst_id),
             'remote_fname': '{year:04d}/' + fname,
             'local_fname': fname}

download = functools.partial(cdw.download, download_tags)

# Set the list_remote_files routine
list_remote_files = functools.partial(cdw.list_remote_files,
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

    warnings.warn(" ".join(["_".join([self.platform, self.name]),
                            "has been removed from the pysat-managed",
                            "Instruments in pysat 3.0.0, and now resides in",
                            "pysatNASA:",
                            "https://github.com/pysat/pysatNASA",
                            "Note that the ICON files are retrieved from",
                            "different servers here and in pysatNASA, resulting",
                            "in a difference in local file names. Please see",
                            "the migration guide there for more details."]),
                  DeprecationWarning, stacklevel=2)
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


def clean(self):
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

    if self.tag.find('los') >= 0:
        # dealing with LOS winds
        wind_flag = 'Wind_Quality'
        ver_flag = 'VER_Quality'
        wind_vars = ['Line_of_Sight_Wind', 'Line_of_Sight_Wind_Error']
        ver_vars = ['Fringe_Amplitude', 'Fringe_Amplitude_Error',
                    'Relative_VER', 'Relative_VER_Error']
        if wind_flag not in self.variables:
            wind_flag = '_'.join(('ICON_L21', wind_flag))
            ver_flag = '_'.join(('ICON_L21', ver_flag))
            wind_vars = ['ICON_L21_' + var for var in wind_vars]
            ver_vars = ['ICON_L21_' + var for var in ver_vars]
        min_val = {'clean': 1.0,
                   'dusty': 0.5}
        if self.clean_level in ['clean', 'dusty']:
            # find location with any of the flags set
            for var in wind_vars:
                self[var] = self[var].where(self[wind_flag]
                                            >= min_val[self.clean_level])
            for var in ver_vars:
                self[var] = self[var].where(self[ver_flag]
                                            >= min_val[self.clean_level])

    elif self.tag.find('vector') >= 0:
        # vector winds area
        wind_flag = 'Wind_Quality'
        ver_flag = 'VER_Quality'
        wind_vars = ['Zonal_Wind', 'Zonal_Wind_Error',
                     'Meridional_Wind', 'Meridional_Wind_Error']
        ver_vars = ['Fringe_Amplitude', 'Fringe_Amplitude_Error',
                    'Relative_VER', 'Relative_VER_Error']
        if wind_flag not in self.variables:
            wind_flag = '_'.join(('ICON_L22', wind_flag))
            ver_flag = '_'.join(('ICON_L22', ver_flag))
            wind_vars = ['ICON_L22_' + var for var in wind_vars]
            ver_vars = ['ICON_L22_' + var for var in ver_vars]
        min_val = {'clean': 1.0,
                   'dusty': 0.5}
        if self.clean_level in ['clean', 'dusty']:
            # find location with any of the flags set
            for var in wind_vars:
                self[var] = self[var].where(self[wind_flag]
                                            >= min_val[self.clean_level])
            for var in ver_vars:
                self[var] = self[var].where(self[ver_flag]
                                            >= min_val[self.clean_level])

    elif self.tag.find('temp') >= 0:
        # neutral temperatures
        var = 'Temperature'
        saa_flag = 'Quality_Flag_South_Atlantic_Anomaly'
        cal_flag = 'Quality_Flag_Bad_Calibration'
        if saa_flag not in self.variables:
            id_str = self.inst_id.upper()
            saa_flag = '_'.join(('ICON_L1_MIGHTI', id_str, saa_flag))
            cal_flag = '_'.join(('ICON_L1_MIGHTI', id_str, cal_flag))
            var = '_'.join(('ICON_L23_MIGHTI', id_str, var))
        if self.clean_level in ['clean', 'dusty']:
            # filter out areas with bad calibration data
            # as well as data marked in the SAA
            self[var] = self[var].where((self[saa_flag] == 0)
                                        & (self[cal_flag] == 0))
            # filter out negative temperatures
            self[var] = self[var].where(self[var] > 0)

    return
