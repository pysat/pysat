# -*- coding: utf-8 -*-
"""SuperDARN data support (Alpha Level!)

"""
import sys
import os

import pandas as pds
import numpy as np

import pysat
import pydarn

def list_files(tag=None, data_path=None):
    """Return a Pandas Series of every file for chosen satellite data"""

    if tag is not None:
        if tag == 'north':
            return pysat.Files.from_os(data_path=data_path, 
                format_str='{year:4d}{month:02d}{day:02d}.north.grdex.bz2')
        else:
            raise ValueError('Unrecognized tag name for SuperDARN, north or south.')                  
    else:
        raise ValueError ('A tag name must be passed to SuperDARN.')           
                
           
def load(fnames, tag=None):
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), pysat.Meta(None)
    elif len(fnames)==1:
        b = pydarn.sdio.sdDataOpen(pysat.datetime(1980,1,1), 
                                    src='local', 
                                    eTime=pysat.datetime(2050,1,1),
                                    fileName=fnames[0])
                                    
        data_list = pydarn.sdio.sdDataReadAll(b)
        sys.stdout.flush()
        in_dict = []
        for info in data_list:
            arr = np.arange(len(info.stid))
            drift_frame = pds.DataFrame(info.vector.__dict__, 
                                    #index=[info.vector.mlon, info.vector.mlat])
                                    index=info.vector.index)
            drift_frame.index.name = 'index'
            drift_frame.sort(inplace=True)
            #drift_frame.index.names=['mlon', 'mlat']
            for i in arr:
                nvec = info.nvec[i]
                in_frame = drift_frame.iloc[0:nvec]
                drift_frame = drift_frame.iloc[nvec:]
                in_dict.append({'stid':info.stid[i],
                            'channel':info.channel[i],
                            'noisemean':info.noisemean[i],
                            'noisesd':info.noisesd[i],
                            'gsct':info.gsct[i],
                            'nvec':info.nvec[i],
                            'pmax':info.pmax[i],
                            'vector':in_frame,
                            'start_time':info.sTime,
                            'end_time':info.eTime,
                            'vemax':info.vemax[i],
                            'vemin':info.vemin[i],
                            'pmin':info.pmin[i],
                            'programid':info.programid[i],
                            'wmax':info.wmax[i],
                            'wmin':info.wmin[i],
                            'freq':info.freq[i]})
        output = pds.DataFrame(in_dict)
        output.index = output.start_time
        output.drop('start_time', axis=1, inplace=True)
        return output, pysat.Meta()
    else:
        raise ValueError('Only one filename currently supported.')

                                        
#def default(ivm):
#
#    return
            
def clean(self):
    # remove data when there are no vectors
    idx, = np.where(self['nvec'] > 0)
    self.data = self.data.iloc[idx]

    return  
    
def download(date_array, tag, data_path, user=None, password=None):
    """
    download IVM data consistent with pysat

    """

    import sys
    import os
    import pysftp
    
    if user is None:
        user = os.environ['DBREADUSER']
    if password is None:
        password = os.environ['DBREADPASS']
        
    with pysftp.Connection(
            os.environ['VTDB'], 
            username=user,
            password=password) as sftp:
            
        for date in date_array:
            myDir = '/data/'+date.strftime("%Y")+'/grdex/'+tag+'/'
            fname = date.strftime("%Y%m%d")+'.north.grdex.bz2'
            local_fname = fname
            saved_fname = os.path.join(data_path,local_fname) 
            try:
                print 'Downloading file for '+date.strftime('%D')
                sys.stdout.flush()
                sftp.get(myDir+fname, saved_fname)
            except IOError:
                print 'File not available for '+date.strftime('%D')


#def test():
#    b = pydarn.sdio.sdDataOpen(pysat.datetime(1980,1,1), 
#                                src='local', 
#                                eTime=pysat.datetime(2050,1,1),
#                                fileName=fnames[0])
#                                
#    data_list = pydarn.sdio.sdDataReadAll(b)
#    print 'building dataframe'
#    sys.stdout.flush()
#    output = pds.DataFrame()
#    for info in data_list:
#        in_frame = []
#        drift_frame = pds.DataFrame(info.vector.__dict__, 
#                                index=[info.vector.mlon, info.vector.mlat])
#        drift_frame.index.names=['mlon', 'mlat']
#        in_dict = {'stid':info.stid,
#                        'channel':info.channel,
#                        'noisemean':info.noisemean,
#                        'noisesd':info.noisesd,
#                        'gsct':info.gsct,
#                        'nvec':info.nvec,
#                        'pmax':info.pmax,
#                        'vector':in_frame,
#                        'start_time':[info.sTime]*len(info.stid),
#                        'end_time':[info.eTime]*len(info.stid),
#                        'vemax':info.vemax,
#                        'vemin':info.vemin,
#                        'pmin':info.pmin,
#                        'programid':info.programid,
#                        'w_max':info.wmax,
#                        'wmin':info.wmin,
#                        'freq':info.freq}
#        for nvec in info.nvec:
#            in_frame.append(drift_frame.iloc[0:nvec])
#            drift_frame = drift_frame.iloc[nvec:]
#        in_dict['vector'] = in_frame
#        frame = pds.DataFrame(in_dict)
#        frame.index = frame.start_time
#        frame.drop('start_time', axis=1, inplace=True)
#        output.append(frame)
#
#def test2():
#    b = pydarn.sdio.sdDataOpen(pysat.datetime(1980,1,1), 
#                                src='local', 
#                                eTime=pysat.datetime(2050,1,1),
#                                fileName=fnames[0])
#                                
#    data_list = pydarn.sdio.sdDataReadAll(b)
#    print 'building dataframe'
#    sys.stdout.flush()
#    in_dict = []
#    for info in data_list:
#        arr = np.arange(len(info.stid))
#        drift_frame = pds.DataFrame(info.vector.__dict__, 
#                                index=[info.vector.mlon, info.vector.mlat])
#        drift_frame.index.names=['mlon', 'mlat']
#        for i in arr:
#            nvec = info.nvec[i]
#            in_frame = drift_frame.iloc[0:nvec]
#            drift_frame = drift_frame.iloc[nvec:]
#            in_dict.append({'stid':info.stid[i],
#                        'channel':info.channel[i],
#                        'noisemean':info.noisemean[i],
#                        'noisesd':info.noisesd[i],
#                        'gsct':info.gsct[i],
#                        'nvec':info.nvec[i],
#                        'pmax':info.pmax[i],
#                        'vector':in_frame,
#                        'start_time':info.sTime,
#                        'end_time':info.eTime,
#                        'vemax':info.vemax[i],
#                        'vemin':info.vemin[i],
#                        'pmin':info.pmin[i],
#                        'programid':info.programid[i],
#                        'w_max':info.wmax[i],
#                        'wmin':info.wmin[i],
#                        'freq':info.freq[i]})
#    output = pds.DataFrame(in_dict)
#    output.index = output.start_time
#    output.drop('start_time', axis=1, inplace=True)            
#
#
#def test3():
#    b = pydarn.sdio.sdDataOpen(pysat.datetime(1980,1,1), 
#                                src='local', 
#                                eTime=pysat.datetime(2050,1,1),
#                                fileName=fnames[0])
#                                
#    data_list = pydarn.sdio.sdDataReadAll(b)
#    print 'building dataframe'
#    sys.stdout.flush()
#    in_frame=[]
#    names=['stid','channel','noisemean','noisesd','gsct','nvec','pmax','vector',
#            'start_time','end_time','vemax','vemin','pmin','programid',
#            'wmax','wmin','freq']
#    
#    in_dict={}    
#    for name in names:
#        in_dict[name]=[]
#
#    for info in data_list:
#
#        drift_frame = pds.DataFrame(info.vector.__dict__, 
#                                index=[info.vector.mlon, info.vector.mlat])
#        drift_frame.index.names=['mlon', 'mlat']
#        in_dict['stid'].extend(info.stid)
#        in_dict['channel'].extend(info.channel)
#        in_dict['noisemean'].extend(info.noisemean)
#        in_dict['noisesd'].extend(info.noisesd)
#        in_dict['gsct'].extend(info.gsct)
#        in_dict['nvec'].extend(info.nvec)
#        in_dict['pmax'].extend(info.pmax)
#        in_dict['start_time'].extend([info.sTime]*len(info.stid))
#        in_dict['end_time'].extend([info.eTime]*len(info.stid))
#        in_dict['vemax'].extend(info.vemax)
#        in_dict['vemin'].extend(info.vemin)
#        in_dict['pmin'].extend(info.pmin)
#        in_dict['programid'].extend(info.programid)
#        in_dict['wmax'].extend(info.wmax)
#        in_dict['wmin'].extend(info.wmin)
#        in_dict['freq'].extend(info.freq)
#        for nvec in info.nvec:
#            in_frame.append(drift_frame.iloc[0:nvec])
#            drift_frame = drift_frame.iloc[nvec:]
#    in_dict['vector'] = in_frame
#    output = pds.DataFrame(in_dict)
#    output.index = output.start_time
#    output.drop('start_time', axis=1, inplace=True) 