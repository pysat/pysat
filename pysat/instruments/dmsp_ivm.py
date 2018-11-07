# -*- coding: utf-8 -*-
"""Supports the Ion Velocity Meter (IVM) 
onboard the Defense Meteorological Satellite Program (DMSP). 

The IVM is comprised of the Retarding Potential Analyzer (RPA) and
Drift Meter (DM). The RPA measures the energy of plasma along the 
direction of satellite motion. By fitting these measurements
to a theoretical description of plasma the number density, plasma
composition, plasma temperature, and plasma motion may be determined. 
The DM directly measures the arrival angle of plasma. Using the reported 
motion of the satellite the angle is converted into ion motion along
two orthogonal directions, perpendicular to the satellite track.

Downloads data from the National Science Foundation Madrigal Database.
The routine is configured to utilize data files with instrument
performance flags generated at the Center for Space Sciences at the
University of Texas at Dallas.

Parameters
----------
platform : string
    'dmsp'
name : string
    'ivm'
tag : string
    'utd'

Example
-------
    import pysat
    dmsp = pysat.Instrument('dmsp', 'ivm', 'utd', 'f15', clean_level='clean')
    dmsp.download(pysat.datetime(2017, 12, 30), pysat.datetime(2017, 12, 31), 
                  user='Firstname+Lastname', password='email@address.com')
    dmsp.load(2017,363)

Note
----
    Please provide name and email when downloading data with this routine.
    
Code development supported by NSF grant 1259508

"""

from __future__ import print_function
from __future__ import absolute_import

import functools
import pysat
from . import madrigal_methods as mad_meth
from . import nasa_cdaweb_methods as cdw

platform = 'dmsp'
name = 'ivm'
tags = {'utd':'UTDallas DMSP data processing', '':'Level 1 data processing'}
sat_ids = {'f11':['utd', ''], 'f12':['utd', ''], 'f13':['utd', ''],
           'f14':['utd', ''], 'f15':['utd', ''], 'f16':[''], 'f17':[''],
           'f18':['']}
test_dates = {'f11':{'utd':pysat.datetime(1998,1,2)},
              'f12':{'utd':pysat.datetime(1998,1,2)},
              'f13':{'utd':pysat.datetime(1998,1,2)},
              'f14':{'utd':pysat.datetime(1998,1,2)},
              'f15':{'utd':pysat.datetime(2017,12,30)}}


# support list files routine
# use the default CDAWeb method
dmsp_fname1 = {'utd':'dms_ut_{year:4d}{month:02d}{day:02d}_',
               '':'dms_{year:4d}{month:02d}{day:02d}_'}
dmsp_fname2 = {'utd':'.{version:03d}.hdf5', '':'s?.{version:03d}.hdf5'}
supported_tags = {ss:{kk:dmsp_fname1[kk] + ss[1:] + dmsp_fname2[kk]
                      for kk in sat_ids[ss]} for ss in sat_ids.keys()}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)
                               
# madrigal tags
madrigal_inst_tag = 8100
madrigal_tag = {'f11':{'utd':10241, '':10111},
                'f12':{'utd':10242, '':10112},
                'f13':{'utd':10243, '':10113},
                'f14':{'utd':10244, '':10114},
                'f15':{'utd':10245, '':10115},
                'f16':{'':10116},
                'f17':{'':10117},
                'f18':{'':10118},}
                
# let pysat know that data is spread across more than one file
# multi_file_day=True
        
# Set to False to specify using xarray (not using pandas)
# Set to True if data will be returned via a pandas DataFrame
pandas_format = True

# support load routine
load = mad_meth.load

def init(self):
    """Initializes the Instrument object with values specific to DMSP IVM
    
    Runs once upon instantiation.
    
    Parameters
    ----------
    self : pysat.Instrument
        This object

    Returns
    --------
    Void : (NoneType)
        Object modified in place.
    
    
    """

    print(mad_meth.cedar_rules())
    return

def download(date_array, tag='', sat_id='', data_path=None, user=None,
             password=None):
    """Downloads data from Madrigal.
    
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
        pysat. If an account
        is required for dowloads this routine here must error if user not
        supplied.
    password : string (None)
        Password for data download.

    Returns
    --------
    Void : (NoneType)
        Downloads data to disk.
    
    Notes
    -----
    The user's names should be provided in field user. Ritu Karidhal should
    be entered as Ritu+Karidhal

    The password field should be the user's email address. These parameters
    are passed to Madrigal when downloading.
    
    The affiliation field is set to pysat to enable tracking of pysat downloads.
    
    """
    mad_meth.download(date_array, inst_code=str(madrigal_inst_code),
                      kindat=str(madrigal_tag[sat_id][tag]),
                      data_path=data_path, user=user, password=password)


def default(ivm):
    pass
   
        
def clean(self):
    """Routine to return DMSP IVM data cleaned to the specified level

    'Clean' enforces that both RPA and DM flags are <= 1
    'Dusty' <= 2
    'Dirty' <= 3
    'None' None
    
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

    Notes
    --------
    Supports 'clean', 'dusty', 'dirty'
    
    """

    if self.tag == 'utd':
        if self.clean_level == 'clean':
            idx, = np.where((self['rpa_flag_ut'] <= 1) &
                            (self['idm_flag_ut'] <= 1))
        elif self.clean_level == 'dusty':
            idx, = np.where((self['rpa_flag_ut'] <= 2) &
                            (self['idm_flag_ut'] <= 2))
        elif self.clean_level == 'dirty':
            idx, = np.where((self['rpa_flag_ut'] <= 3) &
                            (self['idm_flag_ut'] <= 3))
        else:
            idx = []
    else:
        if self.clean_level in ['clean', 'dusty', 'dirty']:
            print('WARNING: this level 1 data has no quality flags')
        idx = []

    # downselect data based upon cleaning conditions above
    self.data = self[idx]
        
    return

def smooth_ram_drifts(self, rpa_flag_key=None, rpa_vel_key='ion_v_sat_for'):
    """ Smooth the ram drifts using a rolling mean

    Parameters
    -----------
    rpa_flag_key : string or NoneType
        RPA flag key, if None will not select any data. The UTD RPA flag key
        is 'rpa_flag_ut' (default=None)
    rpa_vel_key : string
        RPA velocity data key (default='ion_v_sat_for')

    Returns
    ---------
     RPA data in instrument object

    """

    if rpa_flag_key in list(self.data.keys()):
        rpa_idx, = np.where(inst[rpa_flag_key] == 1)
    else:
        rpa_idx = list()

    self[rpa_idx,rpa_vel_key] = self[rpa_idx,rpa_vel_key].rolling(15, 5).mean()
    return

def update_DMSP_ephemeris(self, ephem=None):
    """Updates DMSP instrument data with DMSP ephemeris

    Parameters
    ----------
    ephem : pysat.Instrument or NoneType
        dmsp_ivm_ephem instrument object

    Returns
    ---------
    Updates 'mlt' and 'mlat'

    """

    # Ensure the right ephemera is loaded
    if ephem is None:
        print('No ephemera provided for {:}'.format(self.date))
        self.data = pds.DataFrame(None)
        return

    if ephem.sat_id != dmsp.sat_id:
        raise ValueError('ephemera provided for the wrong satellite')
    
    if ephem.date != self.date:
        ephem.load(date=self.date, verifyPad=True)

        if ephem.data.empty:
            print('unable to load ephemera for {:}'.format(date))
            self.data = pds.DataFrame(None)
            return

    # Reindex the ephemeris data
    ephem.data = ephem.data.reindex(index=self.data.index, method='pad')
    ephem.data = ephem.data.interpolate('time')

    # Update the DMSP instrument
    self['mlt'] = ephem['SC_AACGM_LTIME']
    self['mlat'] = ephem['SC_AACGM_LAT']

    return

def add_drift_unit_vectors(self):
    """ Add unit vectors for the satellite velocity

    Returns
    ---------
    Adds unit vectors in cartesian and polar coordinates for RAM and cross-track
    directions
        - 'unit_ram_x', 'unit_ram_y', 'unit_ram_r', 'unit_ram_theta'
        - 'unit_cross_x', 'unit_cross_y', 'unit_cross_r', 'unit_cross_theta'

    Notes
    ---------
    Assumes that the RAM vector is pointed perfectly forward

    """
    # Calculate theta and R in radians from MLT and MLat, respectively
    theta = self['mlt'] * (np.pi / 12.0) - np.pi * 0.5
    r = np.radians(90.0 - dmsp['mlat'].abs())

    # Determine the positions in cartesian coordinates
    pos_x = r * np.cos(theta)
    pos_y = r * np.sin(theta)
    diff_x = pos_x.diff()
    diff_y = pos_y.diff()
    norm = np.sqrt(diff_x**2 + diff_y**2)

    # Calculate the RAM and cross-track unit vectors in cartesian and polar
    # coordinates.
    # x points along MLT = 6, y points along MLT = 12
    self['unit_ram_x'] = diff_x / norm
    self['unit_ram_y'] = diff_y / norm
    self['unit_cross_x'] = -diff_y / norm
    self['unit_cross_y'] = diff_x / norm
    idx, = np.where(self['mlat'] < 0)
    self.data.ix[idx, 'unit_cross_x'] *= -1.0
    self.data.ix[idx, 'unit_cross_y'] *= -1.0
        
    self['unit_ram_r'] = self['unit_ram_x'] * np.cos(theta) + \
        self['unit_ram_y'] * np.sin(theta)
    self['unit_ram_theta'] = -self['unit_ram_x'] * np.sin(theta) + \
        self['unit_ram_y'] * np.cos(theta)

    self['unit_cross_r'] = self['unit_cross_x'] * np.cos(theta) + \
        self['unit_cross_y'] * np.sin(theta)
    self['unit_cross_theta'] = -self['unit_cross_x'] * np.sin(theta) + \
        self['unit_cross_y'] * np.cos(theta)
    return 

def add_drifts_polar_cap_x_y(self, rpa_flag_key=None,
                             rpa_vel_key='ion_v_sat_for',
                             cross_vel_key='ion_v_sat_left'):
    """ Add polar cap drifts in cartesian coordinates

    Parameters
    ------------
    rpa_flag_key : string or NoneType
        RPA flag key, if None will not select any data. The UTD RPA flag key
        is 'rpa_flag_ut' (default=None)
    rpa_vel_key : string
        RPA velocity data key (default='ion_v_sat_for')
    cross_vel_key : string
        Cross-track velocity data key (default='ion_v_sat_left')

    Returns
    ----------
    Adds 'ion_vel_pc_x', 'ion_vel_pc_y', and 'partial'.  The last data key
    indicates whether RPA data was available (False) or not (True).

    Notes
    -------
    Polar cap drifts assume there is no vertical component to the X-Y velocities
    """

    # Get the good RPA data, if available
    if rpa_flag_key in list(self.data.keys()):
        rpa_idx, = np.where(inst[rpa_flag_key] != 1)
    else:
        rpa_idx = []

    # Use the cartesian unit vectors to calculate the desired velocities
    iv_x = inst[rpa_vel_key].copy()
    iv_x[rpa_idx] = 0.0

    # Check to see if unit vectors have been created
    if not 'unit_ram_y' in list(self.data.keys()):
        add_drift_unit_vectors(self)

    # Calculate the velocities
    self['ion_vel_pc_x'] = iv_x * self['unit_ram_x'] + \
        self[cross_vel_key] * self['unit_cross_x']
    self['ion_vel_pc_y'] = iv_x * self['unit_ram_y'] + \
        self[cross_vel_key] * self['unit_cross_y']

    # Flag the velocities as full (False) or partial (True)
    self['partial'] = False
    self[rpa_idx, 'partial'] = True

    return
