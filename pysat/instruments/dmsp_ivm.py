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

import sys
import functools

import pandas as pds
import numpy as np

import pysat

from . import nasa_cdaweb_methods as cdw

platform = 'dmsp'
name = 'ivm'
tags = {'utd':'UTDallas DMSP data processing'}
sat_ids = {'f11':['utd'], 'f12':['utd'], 'f13':['utd'], 'f14':['utd'], 'f15':['utd']}
test_dates = {'f11':{'utd':pysat.datetime(1998,1,2)},
              'f12':{'utd':pysat.datetime(1998,1,2)},
              'f13':{'utd':pysat.datetime(1998,1,2)},
              'f14':{'utd':pysat.datetime(1998,1,2)},
              'f15':{'utd':pysat.datetime(2017,12,30)}}


# support list files routine
# use the default CDAWeb method
dmsp_fname1 = 'dms_ut_{year:4d}{month:02d}{day:02d}_'
dmsp_fname2 = '.{version:03d}.hdf5'
supported_tags = {'f11':{'utd':dmsp_fname1 + '11' + dmsp_fname2},
                  'f12':{'utd':dmsp_fname1 + '12' + dmsp_fname2},
                  'f13':{'utd':dmsp_fname1 + '13' + dmsp_fname2},
                  'f14':{'utd':dmsp_fname1 + '14' + dmsp_fname2},
                  'f15':{'utd':dmsp_fname1 + '15' + dmsp_fname2},}
list_files = functools.partial(cdw.list_files, 
                               supported_tags=supported_tags)
                               
# madrigal tags
madrigal_tag = {'f11':10241,
                'f12':10242,
                'f13':10243,
                'f14':10244,
                'f15':10245,}
                
# let pysat know that data is spread across more than one file
# multi_file_day=True
                               
# support load routine
def load(fnames, tag=None, sat_id=None):
    
    import h5py
    
    filed = h5py.File(fnames[0], 'r')
    # data
    file_data = filed['Data']['Table Layout']
    # metadata
    file_meta = filed['Metadata']['Data Parameters']
    # load up what is offered into pysat.Meta
    meta = pysat.Meta()
    labels = []
    for item in file_meta:
        # handle difference in string output between python 2 and 3
        name_string = item[0]
        unit_string = item[3]
        desc_string = item[1]
        if sys.version_info[0] >= 3:
            name_string = name_string.decode('UTF-8')
            unit_string = unit_string.decode('UTF-8')
            desc_string = desc_string.decode('UTF-8')
        labels.append(name_string)
        meta[name_string] = {'long_name':name_string,
                             'units':unit_string,
                             'desc':desc_string}
    # add additional metadata notes
    # custom attributes attached to meta are attached to
    # corresponding Instrument object when pysat receives
    # data and meta from this routine
    for key in filed['Metadata']:
        if key != 'Data Parameters':
            setattr(meta, key.replace(' ', '_'), filed['Metadata'][key][:])
    # data into frame, with labels from metadata
    data = pds.DataFrame.from_records(file_data, columns=labels)
    # lowercase variable names
    data.columns = [item.lower() for item in data.columns]
    # datetime index from times
    time = pysat.utils.create_datetime_index(year=data.loc[:,'year'], month=data.loc[:,'month'],
                                             uts=3600.*data.loc[:,'hour']+60.*data.loc[:,'min']+data.loc[:,'sec'])
    # set index
    data.index = time
    return data, meta


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    """Downloads data from Madrigal.
    
    The user's names should be provided in field user. John Malkovich should be 
    entered as John+Malkovich 
    
    The password field should be the user's email address. These parameters
    are passed to Madrigal when downloading.
    
    The affiliation field is set to pysat to enable tracking of pysat downloads.
    
    Parameters
    ----------
    
    
    """
    import subprocess
    
    # currently passes things along if no user and password supplied
    # need to do this for testing
    # TODO, implement user and password values in test code
    # specific to DMSP
    if user is None:
        print ('No user information supplied for download.')
        user = 'pysat_testing'
    if password is None:
        print ('Please provide email address in password field.')
        password = 'pysat_testing@not_real_email.org'

    a = subprocess.check_output(["globalDownload.py", "--verbose", 
                    "--url=http://cedar.openmadrigal.org",
                    '--outputDir='+data_path,
                    '--user_fullname='+user,
                    '--user_email='+password,
                    '--user_affiliation=pysat',
                    '--format=hdf5',
                    '--startDate='+date_array[0].strftime('%m/%d/%Y'),
                    '--endDate='+date_array[-1].strftime('%m/%d/%Y'),
                    '--inst=8100',
                    '--kindat='+str(madrigal_tag[sat_id])])
    print ('Feedback from openMadrigal ', a)
    
    
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
    
    if self.clean_level == 'clean':
        idx, = np.where((self['rpa_flag_ut'] <= 1) & (self['idm_flag_ut'] <= 1))
    elif self.clean_level == 'dusty':
        idx, = np.where((self['rpa_flag_ut'] <= 2) & (self['idm_flag_ut'] <= 2))
    elif self.clean_level == 'dirty':
        idx, = np.where((self['rpa_flag_ut'] <= 3) & (self['idm_flag_ut'] <= 3))
    else:
        idx = []
        
    # downselect data based upon cleaning conditions above
    self.data = self[idx]
        
    return
