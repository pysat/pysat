# -*- coding: utf-8 -*-
"""Supports the Ion Velocity Meter (IVM) 
onboard the Communication and Navigation Outage Forecasting
System (C/NOFS) satellite, part of the Coupled Ion Netural Dynamics 
Investigation (CINDI). Downloads data from the
NASA Coordinated Data Analysis Web (CDAWeb) in CDF format.

Parameters
----------
tag : string
    No tags supported

Warnings
--------
- The sampling rate of the instrument changes on July 29th, 2010.
  The rate is attached to the instrument object as .sample_rate.

- The cleaning parameters for the instrument are still under development.
       
"""
import sys
import os

import pandas as pds
import numpy as np

import pysat
from spacepy import pycdf

def list_files(tag=None, data_path=None):
    """Return a Pandas Series of every file for chosen satellite data"""

    if tag is not None:
        if tag == '':
            return pysat.Files.from_os(data_path=data_path, 
                format_str='cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf')
        else:
            raise ValueError('Unrecognized tag name for C/NOFS IVM')                  
    else:
        raise ValueError ('A tag name must be passed to the loading routine for C/NOFS')           
                
           
def load(fnames, tag=None):
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), pysat.Meta(None)
    else:
         cdf = pycdf.CDF(fnames[0])
         data = {}
         meta = pysat.Meta()
         for key in cdf.iterkeys():
             if key not in ['ECISC_matrix','ECISC_index', 'ECISC_index1',
                            'LVLHSC_matrix','LVLHSC_index', 'LVLHSC_index1']:
                data[key] = cdf[key][...]
                try:

                    meta[key] = {'units':cdf[key].attrs['UNITS'],
                                'long_name':cdf[key].attrs['LABLAXIS'], 
                                'description':cdf[key].attrs['CATDESC']} 
          
                except KeyError:
                    pass
         # matrices have storage issues (double split intwo two floats),
         # defer issue and drop for now
         epoch = data.pop('Epoch')
	 data = pysat.DataFrame(data, index=epoch)
	 cdf.close()
	 return data, meta

def default(ivm):

    ivm.sample_rate = 1.0 if ivm.date >= pysat.datetime(2010, 7, 29) else 2.0
   
            
def clean(self):

    # cleans cindi data
    if self.clean_level == 'clean':
        #choose areas below 550km
        #self.data = self.data[self.data.alt <= 550]
        idx, = np.where(self.data.altitude <= 550)
        self.data = self.data.iloc[idx,:]
    
    # make sure all -999999 values are NaN
    self.data.replace(-999999., np.nan, inplace=True)
    #idx, idy, = np.where(self.data == -999999.)
    #self.data.iloc[idx,idy] = np.nan

   
    if ((self.clean_level == 'clean') | (self.clean_level == 'dusty')):
	try:
	    #self.data = self.data[(abs(self.data.iv_mer) < 10000.)]
	    idx, = np.where(np.abs(self.data.ionVelmeridional) < 10000.)
	    self.data = self.data.iloc[idx,:]
        except AttributeError:
            pass
        #take out all values where RPA data quality is > 3
        #self.data = self.data[self.data.rpa_flag <= 3]
        idx, = np.where(self.data.RPAflag <= 3)
        self.data = self.data.iloc[idx,:]

        #enforce minimum RPA density if RPA flag eqal to 3
        o_dens = self.data.ionDensity*self.data.ion1fraction
        #self.data = self.data[-((o_dens < 3.E4) & (self.data.rpa_flag==3))]
        idx, = np.where(-((o_dens < 3.E4) & (self.data.RPAflag==3)))
        self.data = self.data.iloc[idx,:]
        
        #IDM quality flags
        self.data = self.data[ (self.data.driftMeterflag>= 90) & (self.data.driftMeterflag % 10 < 1) ]
        idx, = np.where((self.data.driftMeterflag>= 90) & (self.data.driftMeterflag % 10 < 1))
        self.data = self.data.iloc[idx,:]


    # basic quality check on drifts and don't let UTS go above 86400.
    #self.data = self.data[ (self.data.uts <= 86400.)]
    idx, = np.where(self.data.time <= 86400.)
    self.data = self.data.iloc[idx,:]
    
    #make sure MLT is between 0 and 24
    #self.data = self.data[(self['mlt'] >= 0.) & (self['mlt'] <= 24.)]
    idx, = np.where((self.data.mlt >= 0) & (self.data.mlt <= 24.))
    self.data = self.data.iloc[idx,:]


    return  
    
def download(date_array, tag, data_path, user=None, password=None):
    """
    download IVM data consistent with pysat

    """
    import ftplib
    from ftplib import FTP
    import sys
    ftp = FTP('cdaweb.gsfc.nasa.gov')   # connect to host, default port
    ftp.login()               # user anonymous, passwd anonymous@
    ftp.cwd('/pub/data/cnofs/cindi/ivm_500ms_cdf')


    for date in date_array:
        fname = '{year1:4d}/cnofs_cindi_ivm_500ms_{year2:4d}{month:02d}{day:02d}_v01.cdf'
        fname = fname.format(year1=date.year, year2=date.year, 
                                month=date.month, day=date.day)
        local_fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'.format(
                        year=date.year, month=date.month, day=date.day)
        saved_fname = os.path.join(data_path,local_fname) 
        try:
            print 'Downloading file for '+date.strftime('%D')
            sys.stdout.flush()
            ftp.retrbinary('RETR '+fname, open(saved_fname,'w').write)
        except ftplib.error_perm as exception:
            if exception[0][0:3] != '550':
                raise
            else:
                os.remove(saved_fname)
                print 'File not available for '+date.strftime('%D')


            
