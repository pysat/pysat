# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 11:17:56 2013

@author: rstoneba
"""
import glob
import os
import netCDF4
import pandas as pds
import numpy as np
import pysat


def list_files(tag=None, data_dir = None):
    """Return a Pandas Series of every file for chosen satellite data"""
    #if tag == 'ionprf':
    #    # from_os constructor currently doesn't work because of the variable 
    #    # filename components at the end of each string.....
    #    #return pysat.Files.from_os(dir_path=os.path.join('cosmic', 'ionprf'),
    #        #format_str='*/ionPrf_*.{year:04d}.{day:03d}.{hour:02d}.{min:02d}*_nc')          

    # number of files may be large, written with this in mind
    cosmicDir = os.path.join(data_dir,'cosmic', tag)
    # only select file that are the cosmic data files and end with _nc
    cosmicFiles = glob.glob(os.path.join(cosmicDir, '*/*_nc'))
    # need to get date and time from filename to generate index
    print 'Building a list of COSMIC files, which can possibly take time. ~1s per 100K files'
    num = len(cosmicFiles) 
    print 'Estimated time:', num*1.E-5,'seconds'
    # preallocate lists
    year=[None]*num; days=[None]*num; hours=[None]*num; 
    minutes=[None]*num; microseconds=[None]*num;
    for i,f in enumerate(cosmicFiles):
        f2 = f.split('.')
        year[i]=f2[1]
        days[i]=f2[2]
        hours[i]=f2[3]
        minutes[i]=f2[4]
        microseconds[i]=i

    year=np.array(year).astype(int)
    days=np.array(days).astype(int)
    uts=np.array(hours).astype(int)*3600+np.array(minutes).astype(int)*60
    # adding microseconds to ensure each time is unique, not allowed to pass 1.E-3 s
    uts+=np.mod(np.array(microseconds).astype(int)*1.E-6, 1.E-3)
    index = pysat.utils.create_datetime_index(year=year, doy=days, uts=uts)
    file_list = pds.Series(cosmicFiles, index=index)
    return file_list
        

def load(cosmicFiles, tag=None):
    """
    cosmic data load routine, called by pysat
    """   
    num = len(cosmicFiles)
    # make sure there are files to read
    if num != 0:
        # call separate load_files routine, segemented for possible
        # multiprocessor load, not included and only benefits about 20%
        output = pds.DataFrame(load_files(cosmicFiles, tag=tag))
        output.index = pysat.utils.create_datetime_index(year=output.year, 
                month=output.month, doy=output.day, 
                uts=output.hour*3600.+output.minute*60.+output.second)
        # make sure UTS strictly increasing
	output.sort(inplace=True)	
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
        return pds.DataFrame(None), pysat.Meta()



# seperate routine for doing actual loading. This was broken off from main load
# becuase I was playing around with multiprocessor loading
# yielded about 20% improvement in execution time
def load_files(files, tag=None):
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
            new['profiles'] = pds.DataFrame(loadedVars)
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


    ## mean altitude profiles over bin size, make a pandas Series for each
    #altBin = 3
    #roundMSL_alt = np.round(loadedVars['MSL_alt']/altBin)*altBin
    #profiles = pds.DataFrame(loadedVars, index=roundMSL_alt)
    #profiles = profiles.groupby(profiles.index.values).mean()
    #del loadedVars 