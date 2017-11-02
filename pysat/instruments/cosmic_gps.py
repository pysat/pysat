# -*- coding: utf-8 -*-
"""
Loads and downloads data from the COSMIC satellite.

The Constellation Observing System for Meteorology, Ionosphere, and Climate
(COSMIC) is comprised of six satellites in LEO with GPS receivers. The occultation
of GPS signals by the atmosphere provides a measurement of atmospheric
parameters. Data downloaded from the COSMIC Data Analaysis and
Archival Center.

Parameters
----------
platform : string
    'cosmic'
name : string
    'gps' for Radio Occultation profiles
tag : string
    Select profile type, one of {'ionprf', 'sonprf', 'wetprf', 'atmprf'}

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
import os
import pandas as pds
import numpy as np
import pysat

platform = 'cosmic'
name = 'gps'
tags = {'ionprf':'', 
        'sonprf':'', 
        'wetprf':'',
        'atmprf':''}
sat_ids = {'':['ionprf', 'sonprf', 'wetprf', 'atmprf']}
test_dates = {'':{'ionprf':pysat.datetime(2008,1,1),
                    'sonprf':pysat.datetime(2008,1,1),
                    'wetprf':pysat.datetime(2008,1,1),
                    'atmprf':pysat.datetime(2008,1,1)}}


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : (string or NoneType)
        Denotes type of file to load, not supported by this routine.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : (string or NoneType)
        User specified file format, not supported here. (default=None)

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files
    """
    import sys
    #if tag == 'ionprf':
    #    # from_os constructor currently doesn't work because of the variable 
    #    # filename components at the end of each string.....
    #    ion_fmt = '*/ionPrf_*.{year:04d}.{day:03d}.{hour:02d}.{min:02d}*_nc'
    #    return pysat.Files.from_os(dir_path=os.path.join('cosmic', 'ionprf'),
    #                               format_str=ion_fmt)
    estr = 'Building a list of COSMIC files, which can possibly take time. '
    print('{:s}~1s per 100K files'.format(estr))
    sys.stdout.flush()

    # number of files may be large, written with this in mind
    # only select file that are the cosmic data files and end with _nc
    cosmicFiles = glob.glob(os.path.join(data_path, '*/*_nc'))
    # need to get date and time from filename to generate index
    num = len(cosmicFiles) 
    if num != 0:
        print('Estimated time:', num*1.E-5,'seconds')
        sys.stdout.flush()
        # preallocate lists
        year=[None]*num; days=[None]*num; hours=[None]*num; 
        minutes=[None]*num; microseconds=[None]*num;
        for i,f in enumerate(cosmicFiles):
            f2 = f.split('.')
            year[i]=f2[-6]
            days[i]=f2[-5]
            hours[i]=f2[-4]
            minutes[i]=f2[-3]
            microseconds[i]=i
    
        year=np.array(year).astype(int)
        days=np.array(days).astype(int)
        uts=np.array(hours).astype(int)*3600+np.array(minutes).astype(int)*60
        # adding microseconds to ensure each time is unique, not allowed to
        # pass 1.E-3 s
        uts+=np.mod(np.array(microseconds).astype(int)*1.E-6, 1.E-3)
        index = pysat.utils.create_datetime_index(year=year, day=days, uts=uts)
        file_list = pysat.Series(cosmicFiles, index=index)
        return file_list
    else:
        print('Found no files, check your path or download them.')
        return pysat.Series(None)
        

def load(cosmicFiles, tag=None, sat_id=None):
    """
    cosmic data load routine, called by pysat
    """   
    import netCDF4

    num = len(cosmicFiles)
    # make sure there are files to read
    if num != 0:
        # call separate load_files routine, segemented for possible
        # multiprocessor load, not included and only benefits about 20%
        output = pysat.DataFrame(load_files(cosmicFiles, tag=tag, sat_id=sat_id))
        output.index = pysat.utils.create_datetime_index(year=output.year, 
                month=output.month, day=output.day, 
                uts=output.hour*3600.+output.minute*60.+output.second)
        # make sure UTS strictly increasing
        output.sort_index(inplace=True)
        # use the first available file to pick out meta information
        meta = pysat.Meta()
        ind = 0
        repeat = True
        while repeat:
            try:
                data = netCDF4.Dataset(cosmicFiles[ind]) 
                ncattrsList = data.ncattrs()
                for d in ncattrsList:
                    meta[d] = {'units':'', 'long_name':d}
                keys = data.variables.keys()
                for key in keys:
                    meta[key] = {'units':data.variables[key].units, 
                                'long_name':data.variables[key].long_name}  
                repeat = False                  
            except RuntimeError:
                # file was empty, try the next one by incrementing ind
                ind+=1
                                    
        return output, meta
    else:
        # no data
        return pysat.DataFrame(None), pysat.Meta()



# seperate routine for doing actual loading. This was broken off from main load
# becuase I was playing around with multiprocessor loading
# yielded about 20% improvement in execution time
def load_files(files, tag=None, sat_id=None):
    '''Loads a list of COSMIC data files, supplied by user.
    
    Returns a list of dicts, a dict for each file.
    '''
       
    output = [None]*len(files)
    drop_idx = []
    for (i,file) in enumerate(files):
        try:
            data = netCDF4.Dataset(file)    
            # build up dictionary will all ncattrs
            new = {} 
            # get list of file attributes
            ncattrsList = data.ncattrs()
            for d in ncattrsList:
                new[d] = data.getncattr(d)            
            # load all of the variables in the netCDF
            loadedVars={}
            keys = data.variables.keys()
            for key in keys:
                loadedVars[key] = data.variables[key][:]               
            new['profiles'] = pysat.DataFrame(loadedVars)
            if tag == 'ionprf':
                new['profiles'].index = new['profiles']['MSL_alt']
            output[i] = new   
            data.close()
        except RuntimeError:
            # some of the S4 files have zero bytes, which causes a read error
            # this stores the index of these zero byte files so I can drop 
            # the Nones the gappy file leaves behind
            drop_idx.append(i)

    # drop anything that came from the zero byte files
    drop_idx.reverse()
    for i in drop_idx:
        del output[i]
    return output


def clean(self):
    
    if self.tag == 'ionprf':
        # ionosphere density profiles
        if self.clean_level == 'clean':
            # try and make sure all data is good
            # filter out profiles where source provider processing doesn't get max dens and max dens alt
            self.data = self.data[( (self['edmaxalt'] != -999.) & (self['edmax'] != -999.) )]
            # make sure edmaxalt in "reasonable" range
            self.data = self.data[(self.data.edmaxalt >= 175.) & (self.data.edmaxalt <= 475.)]
            # filter densities when negative
            for i, profile in enumerate(self['profiles']):
                # take out all densities below the highest altitude negative dens below 325
                idx, = np.where((profile.ELEC_dens < 0) & (profile.index <= 325))	
                if len(idx) > 0:
                    profile.iloc[0:idx[-1]+1] = np.nan
                # take out all densities above the lowest altitude negative dens above 325
                idx, = np.where((profile.ELEC_dens < 0) & (profile.index > 325))	
                if len(idx) > 0:
                    profile.iloc[idx[0]:] = np.nan
                                    
                # do an altitude density gradient check to reduce number of cycle slips 
                densDiff = profile.ELEC_dens.diff()
                altDiff = profile.MSL_alt.diff()
                normGrad = ( densDiff/(altDiff*profile.ELEC_dens) ).abs()
                idx, = np.where((normGrad > 1.) & normGrad.notnull())
                if len(idx) > 0:
                    self[i,'edmaxalt'] = np.nan
                    self[i,'edmax'] = np.nan
                    self[i,'edmaxlat'] = np.nan
                    profile['ELEC_dens'] *= np.nan
                    #self.data['profiles'][i]['ELEC_dens'] *= np.nan

        # filter out any measurements where things have been set to NaN
        self.data = self.data[self.data.edmaxalt.notnull()]

    elif self.tag == 'scnlvl1':
        # scintillation files
        if self.clean_level == 'clean':
            # try and make sure all data is good       
            # filter out profiles where source provider processing doesn't 
            # work 
            self.data = self.data[( (self['alttp_s4max'] != -999.) & (self['s4max9sec'] != -999.) )]

    return

def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    import ftplib
    import urllib2
    import base64
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
   
    for date in date_array:
        print('Downloading COSMIC data for '+date.strftime('%D'))
        yr,doy = pysat.utils.getyrdoy(date)
        yrdoystr = '{year:04d}.{doy:03d}'.format(year=yr, doy=doy)
        dwnld="http://cdaac-www.cosmic.ucar.edu/cdaac/rest/tarservice/data/cosmic2013/"
        dwnld = dwnld+sub_dir+'/{year:04d}.{doy:03d}'.format(year=yr, doy=doy)
        req=urllib2.Request(dwnld)
        base64str=base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64str)   
        result=urllib2.urlopen(req)
        fname=os.path.join(data_path,'cosmic_'+sub_dir+'_'+ yrdoystr+'.tar' )
        with open(fname, "wb") as local_file:
            local_file.write(result.read())
            local_file.close()
            # uncompress files
            tar = tarfile.open(fname)
            tar.extractall(path=data_path)
            tar.close()
            # move files
            ext_dir = os.path.join(data_path,'cosmic2013',sub_dir,yrdoystr) 
            shutil.move(ext_dir, os.path.join(data_path,yrdoystr))

    return

    
    
    
    
    ## mean altitude profiles over bin size, make a pandas Series for each
    #altBin = 3
    #roundMSL_alt = np.round(loadedVars['MSL_alt']/altBin)*altBin
    #profiles = pds.DataFrame(loadedVars, index=roundMSL_alt)
    #profiles = profiles.groupby(profiles.index.values).mean()
    #del loadedVars 
