# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str

import string
import os
import copy
import sys
import pandas as pds
import numpy as np

from . import _custom
from . import _files
from . import _orbits
from . import _meta
from . import utils
from pysat import data_dir
from pysat import DataFrame, Series


# main class for users
class Instrument(object):
    """Download, load, manage, modify and analyze science data.
    
    Parameters
    ----------    
    platform : string
        name of platform/satellite.
    name : string
        name of instrument. 
    tag : string, optional
        identifies particular subset of instrument data.
    sat_id : string, optional
        identity within constellation
    clean_level : {'clean','dusty','dirty','none'}, optional
        level of data quality
    pad : pandas.DateOffset, or dictionary, optional
        Length of time to pad the begining and end of loaded data for 
        time-series processing. Extra data is removed after applying all 
        custom functions. Dictionary, if supplied, is simply passed to 
        pandas DateOffset.
    orbit_info : dict    
        Orbit information, {'index':index, 'kind':kind, 'period':period}.
        See pysat.Orbits for more information.            
    inst_module : module, optional
        Provide instrument module directly. 
        Takes precedence over platform/name.
    update_files : boolean, optional
        If True, immediately query filesystem for instrument files and store.
    temporary_file_list : boolean, optional
        If true, the list of Instrument files will not be written to disk.
        Prevents a race condition when running multiple pysat processes.
    multi_file_day : boolean, optional 
        Set to True if Instrument data files for a day are spread across
        multiple files and data for day n could be found in a file
        with a timestamp of day n-1 or n+1.
    manual_org : bool
        if True, then pysat will look directly in pysat data directory
        for data files and will not use default /platform/name/tag
    directory_format : str
        directory naming structure in string format. Variables such as
        platform, name, and tag will be filled in as needed using python
        string formatting. The default directory structure would be 
        expressed as '{platform}/{name}/{tag}'
    file_format : str or NoneType
        File naming structure in string format.  Variables such as year,
        month, and sat_id will be filled in as needed using python string
        formatting.  The default file format structure is supplied in the
        instrument list_files routine.
    units_label : str
        String used to label units in storage. Defaults to 'units'. 
    name_label : str
        String used to label long_name in storage. Defaults to 'name'.
    notes_label : str
       label to use for notes in storage. Defaults to 'notes'
    desc_label : str
       label to use for variable descriptions in storage. Defaults to 'desc'
    plot_label : str
       label to use to label variables in plots. Defaults to 'label'
    axis_label : str
        label to use for axis on a plot. Defaults to 'axis'
    scale_label : str
       label to use for plot scaling type in storage. Defaults to 'scale'
    min_label : str
       label to use for typical variable value min limit in storage.
       Defaults to 'value_min'
    max_label : str
       label to use for typical variable value max limit in storage.
       Defaults to 'value_max'
    fill_label : str
        label to use for fill values. Defaults to 'fill' but some implementations
        will use 'FillVal'
               
    Attributes
    ----------
    data : pandas.DataFrame
        loaded science data 
    date : pandas.datetime
        date for loaded data
    yr : int
        year for loaded data
    bounds : (datetime/filename/None, datetime/filename/None)
        bounds for loading data, supply array_like for a season with gaps
    doy : int
        day of year for loaded data
    files : pysat.Files
        interface to instrument files
    meta : pysat.Meta
        interface to instrument metadata, similar to netCDF 1.6
    orbits : pysat.Orbits
        interface to extracting data orbit-by-orbit
    custom : pysat.Custom
        interface to instrument nano-kernel
    kwargs : dictionary
        keyword arguments passed to instrument loading routine
    
    Note
    ----
    Pysat attempts to load the module platform_name.py located in
    the pysat/instruments directory. This module provides the underlying 
    functionality to download, load, and clean instrument data. 
    Alternatively, the module may be supplied directly
    using keyword inst_module.
    
    Examples
    --------     
    :: 
           
        # 1-second mag field data
        vefi = pysat.Instrument(platform='cnofs', 
                                name='vefi', 
                                tag='dc_b', 
                                clean_level='clean')
        start = pysat.datetime(2009,1,1)
        stop = pysat.datetime(2009,1,2)
        vefi.download(start, stop)
        vefi.load(date=start)
        print(vefi['dB_mer'])
        print(vefi.meta['db_mer'])
    
        # 1-second thermal plasma parameters
        ivm = pysat.Instrument(platform='cnofs', 
                                name='ivm', 
                                tag='', 
                                clean_level='clean')
        ivm.download(start,stop)
        ivm.load(2009,1)
        print(ivm['ionVelmeridional'])
        
        # Ionosphere profiles from GPS occultation
        cosmic = pysat.Instrument('cosmic2013', 
                                    'gps', 
                                    'ionprf', 
                                    altitude_bin=3)
        # bins profile using 3 km step
        cosmic.download(start, stop, user=user, password=password)
        cosmic.load(date=start)

    """

    def __init__(self, platform=None, name=None, tag=None, sat_id=None,
                 clean_level='clean', update_files=None, pad=None,
                 orbit_info=None, inst_module=None, multi_file_day=None,
                 manual_org=None, directory_format=None, file_format=None,
                 temporary_file_list=False, units_label='units',
                 name_label='long_name', notes_label='notes', desc_label='desc',
                 plot_label='label', axis_label='axis', scale_label='scale',
                 min_label='value_min', max_label='value_max',
                 fill_label = 'fill', *arg, **kwargs):

        if inst_module is None:
            # use strings to look up module name
            if isinstance(platform, str) and isinstance(name, str):
                self.platform = platform.lower() 
                self.name = name.lower() 
                # look to module for instrument functions and defaults
                self._assign_funcs(by_name=True)
            elif (platform is None) and (name is None):
                # creating "empty" Instrument object with this path
                self.name = ''
                self.platform = ''
                self._assign_funcs()                
            else:
                raise ValueError('Inputs platform and name must both be ' +
                                 'strings, or both None.')
        else:
            # user has provided a module
            try:
                # platform and name are expected to be part of module
                self.name = inst_module.name.lower()
                self.platform = inst_module.platform.lower()
            except AttributeError:
                raise AttributeError(string.join(('A name and platform ',
                                                  'attribute for the ',
                                                  'instrument is required if ',
                                                  'supplying routine module ',
                                                  'directly.')))
            # look to module for instrument functions and defaults
            self._assign_funcs(inst_module=inst_module)
            
        # more reasonable defaults for optional parameters
        self.tag = tag.lower() if tag is not None else ''
        self.sat_id = sat_id.lower() if sat_id is not None else ''
        self.clean_level = (clean_level.lower() if clean_level is not None
                            else 'none')


        # assign_func sets some instrument defaults, direct info rules all
        if directory_format is not None:
            self.directory_format = directory_format.lower()
        # value not provided by user, check if there is a value provided by
        # instrument module
        elif self.directory_format is not None:
            try:
                # check if it is a function
                self.directory_format = self.directory_format(tag, sat_id)
            except TypeError:
                pass

        if file_format is not None:
            self.file_format = file_format
        # check to make sure value is reasonable
        if self.file_format is not None:
            # check if it is an iterable string.  If it isn't formatted
            # properly, raise Error
            if (not isinstance(self.file_format, str) or
                    (self.file_format.find("{") < 0) or
                    (self.file_format.find("}") < 0)):
                estr = 'file format set to default, supplied string must be '
                estr = '{:s}iteratable [{:}]'.format(estr, self.file_format)
                raise ValueError(estr)

        # set up empty data and metadata
        self.data = DataFrame(None)
        self.units_label = units_label
        self.name_label = name_label
        self.notes_label = notes_label
        self.desc_label = desc_label
        self.plot_label = plot_label
        self.axis_label = axis_label
        self.scale_label = scale_label
        self.min_label = min_label
        self.max_label = max_label
        self.fill_label = fill_label
        self.meta = _meta.Meta(units_label=self.units_label, name_label=self.name_label,
                               notes_label=self.notes_label, desc_label=self.desc_label,
                               plot_label=self.plot_label, axis_label=self.axis_label,
                               scale_label=self.scale_label, min_label=self.min_label,
                               max_label=self.max_label, fill_label=self.fill_label)

        # function processing class, processes data on load
        self.custom = _custom.Custom()
        # create arrays to store data around loaded day
        # enables padding across day breaks with minimal loads
        self._next_data = DataFrame(None)
        self._next_data_track = []
        self._prev_data = DataFrame(None)
        self._prev_data_track = []
        self._curr_data = DataFrame(None)

        # multi file day, default set by assign_funcs
        if multi_file_day is not None:
            self.multi_file_day = multi_file_day
                    
        # arguments for padding
        if isinstance(pad, pds.DateOffset):
            self.pad = pad
        elif isinstance(pad, dict):
            self.pad = pds.DateOffset(**pad)
        elif pad is None:
            self.pad = None
        else:
            estr = 'pad must be a dictionary or a pandas.DateOffset instance.'
            raise ValueError(estr)

        # instantiate Files class
        manual_org = False if manual_org is None else manual_org
        temporary_file_list = not temporary_file_list
        self.files = _files.Files(self, manual_org=manual_org, 
                                  directory_format=self.directory_format,
                                  update_files=update_files,
                                  file_format=self.file_format,
                                  write_to_disk=temporary_file_list)

        # set bounds for iteration
        # self.bounds requires the Files class
        # setting (None,None) loads default bounds
        self.bounds = (None, None)
        self.date = None
        self._fid = None
        self.yr = None
        self.doy = None
        self._load_by_date = False

        # initialize orbit support
        if orbit_info is None:
            if self.orbit_info is None:
                # if default info not provided, set None as default
                orbit_info = {'index': None, 'kind': None, 'period': None}
            else:
                # default provided by instrument module
                orbit_info = self.orbit_info
        self.orbits = _orbits.Orbits(self, **orbit_info)

        # Create empty placeholder for meta translation table
        # gives information about how to label metadata for netcdf export
        # if None, pysat metadata labels will be used
        self._meta_translation_table = None

        # Create a placeholder for a post-processing function to be applied
        # to the metadata dictionary before export. If None, no post-processing
        # will occur
        self._export_meta_post_processing = None

        # store kwargs, passed to load routine
        self.kwargs = kwargs

        # run instrument init function, a basic pass function is used
        # if user doesn't supply the init function
        self._init_rtn(self)

        # store base attributes, used in particular by Meta class
        self._base_attr = dir(self)

    def __getitem__(self, key): 
        """
        Convenience notation for accessing data; inst['name'] is inst.data.name
        
        Examples
        --------
        ::
        
            # By name
            inst['name']
            # By position  
            inst[row_index, 'name']  
            # Slicing by row 
            inst[row1:row2, 'name']            
            # By Date  
            inst[datetime, 'name']
            # Slicing by date, inclusive
            inst[datetime1:datetime2, 'name']
            # Slicing by name and row/date  
            inst[datetime1:datetime1, 'name1':'name2']
            
        """

        if isinstance(key, tuple):
            # support slicing
            return self.data.ix[key[0], key[1]]
        else:
            try:
                return self.data.iloc[key]
            except:
                try:
                    return self.data[key]
                except:
                    estring = '\n'.join(("Unable to sort out data access.",
                                         "Instrument has data : " + str(not self.empty),
                                         "Requested key : ", key))
                    raise ValueError(estring)

    def __setitem__(self, key, new):
        """Convenience method for adding data to instrument.
        
        Examples
        --------
        ::
        
            # Simple Assignment, default metadata assigned
            # 'long_name' = 'name'
            # 'units' = ''
            inst['name'] = newData
            # Assignment with Metadata 
            inst['name'] = {'data':new_data, 
                            'long_name':long_name, 
                            'units':units}
        
        Note
        ----
        If no metadata provided and if metadata for 'name' not already stored 
        then default meta information is also added, 
        long_name = 'name', and units = ''.
        
        """
        
        # add data to main pandas.DataFrame, depending upon the input
        # aka slice, and a name
        if isinstance(key, tuple):
            self.data.ix[key[0], key[1]] = new
            self.meta[key[1]] = {}
            return 
        elif not isinstance(new, dict):
            # make it a dict to simplify downstream processing
            new = {'data': new}
            
        # input dict must have data in 'data', 
        # the rest of the keys are presumed to be metadata
        try:
            in_data = new.pop('data')
        except:
            raise ValueError(' '.join(("Data for the variable must be passed under key 'data'",
                                       "when passing a dictionary.",
                                       "If you wish to set metadata individually, please",
                                       "use the access mechanisms under the .meta "
                                       "attached to the pysat.Instrument object.") ))
        if hasattr(in_data, '__iter__'):
            if isinstance(in_data, pds.DataFrame):
                pass
                # filter for elif
            elif isinstance(next(iter(in_data), None), pds.DataFrame):
                # input is a list_like of frames
                # this is higher order data
                # this process ensures
                if ('meta' not in new) and (key not in self.meta.keys_nD()):
                    # create an empty Meta instance but with variable names
                    # this will ensure the correct defaults for all subvariables
                    # meta can filter out empty metadata as needed, the check above reduces
                    # the need to create Meta instances
                    ho_meta = _meta.Meta(units_label=self.units_label, name_label=self.name_label,
                                        notes_label=self.notes_label, desc_label=self.desc_label,
                                        plot_label=self.plot_label, axis_label=self.axis_label,
                                        scale_label=self.scale_label, fill_label=self.fill_label,
                                        min_label=self.min_label, max_label=self.max_label)
                    ho_meta[in_data[0].columns] = {}
                    self.meta[key] = ho_meta
        
        # assign data and any extra metadata
        self.data[key] = in_data
        self.meta[key] = new

                        
    @property
    def empty(self):
        """Boolean flag reflecting lack of data.
        
        True if there is no Instrument data."""
        return self.data.empty

    def copy(self):
        """Deep copy of the entire Instrument object."""
        return copy.deepcopy(self)
    
    def _pass_func(*args, **kwargs):
        pass     

    def _assign_funcs(self, by_name=False, inst_module=None):        
        """Assign all external science instrument methods to Instrument object.
        """
        import importlib
        # set defaults
        self._list_rtn = self._pass_func
        self._load_rtn = self._pass_func
        self._default_rtn = self._pass_func
        self._clean_rtn = self._pass_func
        self._init_rtn = self._pass_func
        self._download_rtn = self._pass_func
        # default params
        self.directory_format = None
        self.file_format = None
        self.multi_file_day = False
        self.orbit_info = None
                        
        if by_name: 
            # look for code with filename name, any errors passed up
            inst = importlib.import_module(''.join(('.', self.platform, '_',
                                           self.name)),
                                           package='pysat.instruments')
        elif inst_module is not None:
            # user supplied an object with relevant instrument routines
            inst = inst_module
        else:
            # no module or name info, default pass functions assigned
            return

        try:
            self._load_rtn = inst.load
            self._list_rtn = inst.list_files
            self._download_rtn = inst.download
        except AttributeError:
            estr = 'A load, file_list, and download routine are required for '
            raise AttributeError('{:s}every instrument.'.format(estr))
        try:
            self._default_rtn = inst.default
        except AttributeError:
            pass
        try:
            self._init_rtn = inst.init
        except AttributeError:
            pass   
        try:
            self._clean_rtn = inst.clean
        except AttributeError:
            pass

        # look for instrument default parameters
        try:
            self.directory_format = inst.directory_format
        except AttributeError:
            pass
        try:
            self.multi_file_day = inst.multi_file_day
        except AttributeError:
            pass
        try:
            self.orbit_info = inst.orbit_info
        except AttributeError:
            pass

        return

    def __str__(self):

        output_str = '\npysat Instrument object\n'
        output_str += '-----------------------\n'
        output_str += 'Platform: '+self.platform+'\n'
        output_str += 'Name: '+self.name+'\n'
        output_str += 'Tag: '+self.tag+'\n'
        output_str += 'Satellite id: '+self.sat_id+'\n'

        output_str += '\nData Processing\n'
        output_str += '---------------\n'
        output_str += 'Cleaning Level: ' + self.clean_level + '\n'
        output_str += 'Data Padding: ' + self.pad.__repr__() + '\n'
        output_str += 'Keyword Arguments Passed to load(): '
        output_str += self.kwargs.__repr__() +'\nCustom Functions : \n'
        if len(self.custom._functions) > 0:
            for func in self.custom._functions:
                output_str += '    ' + func.__repr__() + '\n'
        else:
            output_str += '    ' + 'No functions applied.\n'

        output_str += '\nOrbit Settings' + '\n'
        output_str += '--------------' + '\n'
        if self.orbit_info is None:
            output_str += 'Orbit properties not set.\n'
        else:
            output_str += 'Orbit Kind: ' + self.orbit_info['kind'] + '\n'
            output_str += 'Orbit Index: ' + self.orbit_info['index'] + '\n'
            output_str += 'Orbit Period: '
            output_str += self.orbit_info['period'].__str__() + '\n'
            output_str += 'Number of Orbits: {:d}\n'.format(self.orbits.num)
            output_str += 'Loaded Orbit Number: '
            if self.orbits.current is not None:
                output_str += '{:d}\n'.format(self.orbits.current)
            else:
                output_str += 'None\n'

        output_str += '\nLocal File Statistics' + '\n'
        output_str += '---------------------' + '\n'
        output_str += 'Number of files: ' + str(len(self.files.files)) + '\n'

        if len(self.files.files) > 0:
            output_str += 'Date Range: '
            output_str += self.files.files.index[0].strftime('%m/%d/%Y')
            output_str += ' --- ' + self.files.files.index[-1].strftime('%m/%d/%Y')

        output_str += '\n\nLoaded Data Statistics'+'\n'
        output_str += '----------------------'+'\n'
        if not self.empty:
            # if self._fid is not None:
            #     output_str += 'Filename: ' +
            output_str += 'Date: ' + self.date.strftime('%m/%d/%Y') + '\n'
            output_str += 'DOY: {:03d}'.format(self.doy) + '\n'
            output_str += 'Time range: '
            output_str += self.data.index[0].strftime('%m/%d/%Y %H:%M:%S')
            output_str += ' --- '
            output_str += self.data.index[-1].strftime('%m/%d/%Y %H:%M:%S')+'\n'
            output_str += 'Number of Times: ' + str(len(self.data.index)) + '\n'
            output_str += 'Number of variables: ' + str(len(self.data.columns))

            output_str += '\n\nVariable Names:'+'\n'
            num = len(self.data.columns)//3
            for i in np.arange(num):
                output_str += self.data.columns[3 * i].ljust(30)
                output_str += '  ' + self.data.columns[3 * i + 1].ljust(30)
                output_str += '  ' + self.data.columns[3 * i + 2].ljust(30)+'\n'
            for i in np.arange(len(self.data.columns) - 3 * num):
                output_str += self.data.columns[i+3*num].ljust(30) + '  '
            output_str += '\n'
        else:
            output_str += 'No loaded data.'+'\n'
        output_str += '\n'

        return output_str

    def _load_data(self, date=None, fid=None):
        """
        Load data for an instrument on given date or fid, dependng upon input.

        Parameters
        ------------
        date : (dt.datetime.date object or NoneType)
            file date
        fid : (int or NoneType)
            filename index value

        Returns
        --------
        data : (pds.DataFrame)
            pysat data
        meta : (pysat.Meta)
            pysat meta data
        """

        if fid is not None:
            # get filename based off of index value
            fname = self.files[fid:fid+1]
        elif date is not None:
            fname = self.files[date: date+pds.DateOffset(days=1)]
        else:
            raise ValueError('Must supply either a date or file id number.')
   
        if len(fname) > 0:    
            load_fname = [os.path.join(self.files.data_path, f) for f in fname]
            data, mdata = self._load_rtn(load_fname, tag=self.tag,
                                         sat_id=self.sat_id, **self.kwargs)

            # ensure units and name are named consistently in new Meta
            # object as specified by user upon Instrument instantiation
            mdata.accept_default_labels(self)

        else:
            data = DataFrame(None)
            mdata = _meta.Meta(units_label=self.units_label, name_label=self.name_label,
                        notes_label = self.notes_label, desc_label = self.desc_label,
                        plot_label = self.plot_label, axis_label = self.axis_label,
                        scale_label = self.scale_label, min_label = self.min_label,
                        max_label = self.max_label, fill_label=self.fill_label)

        output_str = '{platform} {name} {tag} {sat_id}'
        output_str = output_str.format(platform=self.platform,
                                       name=self.name, tag=self.tag, 
                                       sat_id=self.sat_id)
        if not data.empty: 
            if not isinstance(data, DataFrame):
                raise TypeError(' '.join(('Data returned by instrument load',
                                'routine must be a pandas.DataFrame')))
            if not isinstance(mdata, _meta.Meta):
                raise TypeError('Metadata returned must be a pysat.Meta object')
            if date is not None:
                output_str = ' '.join(('Returning', output_str, 'data for',
                                       date.strftime('%x')))
            else:
                if len(fname) == 1:
                    # this check was zero
                    output_str = ' '.join(('Returning', output_str, 'data from',
                                           fname[0]))
                else:
                    output_str = ' '.join(('Returning', output_str, 'data from',
                                           fname[0], '::', fname[-1]))
        else:
            # no data signal
            output_str = ' '.join(('No', output_str, 'data for',
                                   date.strftime('%m/%d/%y')))
        # remove extra spaces, if any
        output_str = " ".join(output_str.split())
        print (output_str)                
        return data, mdata
        
    def _load_next(self):
        """Load the next days data (or file) without incrementing the date.
        Repeated calls will not advance date/file and will produce the same data
        
        Uses info stored in object to either increment the date, 
        or the file. Looks for self._load_by_date flag. 
         
        """
        if self._load_by_date:
            next_date = self.date + pds.DateOffset(days=1)
            return self._load_data(date=next_date)
        else:
            return self._load_data(fid=self._fid+1)

    def _load_prev(self):
        """Load the next days data (or file) without decrementing the date.
        Repeated calls will not decrement date/file and will produce the same
        data
        
        Uses info stored in object to either decrement the date, 
        or the file. Looks for self._load_by_date flag.  
        
        """

        if self._load_by_date:
            prev_date = self.date - pds.DateOffset(days=1)
            return self._load_data(date=prev_date)
        else:
            return self._load_data(fid=self._fid-1)

    def _set_load_parameters(self, date=None, fid=None):
        self.date = date
        self._fid = fid
        if date is not None:
            year, doy = utils.getyrdoy(date)
            self.yr = year 
            self.doy = doy 
            self._load_by_date = True
        else:
            self.yr = None 
            self.doy = None 
            self._load_by_date = False        

    def load(self, yr=None, doy=None, date=None, fname=None, fid=None, 
             verifyPad=False):
        """Load instrument data into Instrument object .data.

        Parameters
        ----------
        yr : integer
            year for desired data
        doy : integer
            day of year
        date : datetime object
            date to load
        fname : 'string'
            filename to be loaded
        verifyPad : boolean 
            if True, padding data not removed (debug purposes)

        Returns
        --------
        Void.  Data is added to self.data

        Note
        ----
        Loads data for a chosen instrument into .data. Any functions chosen
        by the user and added to the custom processing queue (.custom.add)
        are automatically applied to the data before it is available to 
        user in .data.
        
        """
        # set options used by loading routine based upon user input
        if date is not None:
            self._set_load_parameters(date=date, fid=None)
            # increment 
            inc = pds.DateOffset(days=1)
            curr = date
        elif (yr is not None) & (doy is not None):
            date = pds.datetime(yr, 1, 1) + pds.DateOffset(days=(doy-1))
            self._set_load_parameters(date=date, fid=None)
            # increment 
            inc = pds.DateOffset(days=1)
            curr = self.date
        elif fname is not None:
            # date will have to be set later by looking at the data
            self._set_load_parameters(date=None,
                                      fid=self.files.get_index(fname))
            # increment one file at a time
            inc = 1
            curr = self._fid.copy()
        elif fid is not None:
            self._set_load_parameters(date=None, fid=fid)
            # increment one file at a time
            inc = 1
            curr = fid
        else:
            estr = 'Must supply a yr,doy pair, or datetime object, or filename'
            estr = '{:s} to load data from.'.format(estr)
            raise TypeError(estr)

        self.orbits._reset()
        # if pad  or multi_file_day is true, need to have a three day/file load
        loop_pad = self.pad if self.pad is not None else pds.DateOffset(seconds=0)   
        if (self.pad is not None) | self.multi_file_day:
            if self._next_data.empty & self._prev_data.empty:
                # data has not already been loaded for previous and next days
                # load data for all three
                print('Initializing three day/file window')
                # using current date or fid
                self._prev_data, self._prev_meta = self._load_prev()
                self._curr_data, self._curr_meta = \
                    self._load_data(date=self.date, fid=self._fid)
                self._next_data, self._next_meta = self._load_next()
            else:
                # moving forward in time
                if self._next_data_track == curr:
                    del self._prev_data
                    self._prev_data = self._curr_data
                    self._prev_meta = self._curr_meta
                    self._curr_data = self._next_data
                    self._curr_meta = self._next_meta
                    self._next_data, self._next_meta = self._load_next()
                # moving backward in time
                elif self._prev_data_track == curr:
                    del self._next_data
                    self._next_data = self._curr_data
                    self._next_meta = self._curr_meta
                    self._curr_data = self._prev_data
                    self._curr_meta = self._prev_meta
                    self._prev_data, self._prev_meta = self._load_prev()
                # jumped in time/or switched from filebased to date based access
                else:
                    del self._prev_data
                    del self._curr_data
                    del self._next_data
                    self._prev_data, self._prev_meta = self._load_prev()
                    self._curr_data, self._curr_meta = \
                                self._load_data(date=self.date, fid=self._fid)
                    self._next_data, self._next_meta = self._load_next()

            # make sure datetime indices for all data is monotonic
            if not self._prev_data.index.is_monotonic_increasing:
                self._prev_data.sort_index(inplace=True)
            if not self._curr_data.index.is_monotonic_increasing:
                self._curr_data.sort_index(inplace=True)
            if not self._next_data.index.is_monotonic_increasing:
                self._next_data.sort_index(inplace=True)
                
            # make tracking indexes consistent with new loads
            self._next_data_track = curr + inc
            self._prev_data_track = curr - inc
            # attach data to object
            if not self._curr_data.empty:
                self.data = self._curr_data.copy()
                self.meta = self._curr_meta.copy()
            else:
                self.data = DataFrame(None)
                # line below removed as it would delete previous meta, if any
                # if you end a seasonal analysis with a day with no data, then
                # no meta: self.meta = _meta.Meta()
            
            # multi file days can extend past a single day, only want data from 
            # specific date if loading by day
            # set up times for the possible data padding coming up
            if self._load_by_date:
                #print ('double trouble')
                first_time = self.date 
                first_pad = self.date - loop_pad
                last_time = self.date + pds.DateOffset(days=1) 
                last_pad = self.date + pds.DateOffset(days=1) + loop_pad
                want_last_pad = False
            # loading by file, can't be a multi_file-day flag situation
            elif (not self._load_by_date) and (not self.multi_file_day):
                #print ('single trouble')
                first_time = self._curr_data.index[0]
                first_pad = first_time - loop_pad
                last_time = self._curr_data.index[-1]
                last_pad = last_time + loop_pad
                want_last_pad = True
            else:
                raise ValueError("multi_file_day and loading by date are " + 
                                 "effectively equivalent.  Can't have " +
                                 "multi_file_day and load by file.")
            #print (first_pad, first_time, last_time, last_pad)

            # pad data based upon passed parameter
            if (not self._prev_data.empty) & (not self.data.empty):
                padLeft = self._prev_data.loc[first_pad : self.data.index[0]]
                if len(padLeft) > 0:
                    if (padLeft.index[-1] == self.data.index[0]) :
                        padLeft = padLeft.iloc[:-1, :]
                    self.data = pds.concat([padLeft, self.data])

            if (not self._next_data.empty) & (not self.data.empty):
                padRight = self._next_data.loc[self.data.index[-1] : last_pad]
                if len(padRight) > 0:
                    if (padRight.index[0] == self.data.index[-1]) :
                        padRight = padRight.iloc[1:, :]
                    self.data = pds.concat([self.data, padRight])
                    
            self.data = self.data.ix[first_pad : last_pad]
            # want exclusive end slicing behavior from above
            if not self.empty:
                if (self.data.index[-1] == last_pad) & (not want_last_pad):
                    self.data = self.data.iloc[:-1, :]
   
            ## drop any possible duplicate index times
            ##self.data.drop_duplicates(inplace=True)
            #self.data = self.data[~self.data.index.duplicated()]
            
        # if self.pad is False, load single day
        else:
            self.data, meta = self._load_data(date=self.date, fid=self._fid) 
            if not self.data.empty:
                self.meta = meta   
               
        # check if load routine actually returns meta
        if self.meta.data.empty:
            self.meta[self.data.columns] = {self.name_label: self.data.columns,
                                            self.units_label: [''] *
                                            len(self.data.columns)}
        # if loading by file set the yr, doy, and date
        if not self._load_by_date:
            if self.pad is not None:
                temp = first_time
            else:
                temp = self.data.index[0]
            self.date = pds.datetime(temp.year, temp.month, temp.day)
            self.yr, self.doy = utils.getyrdoy(self.date)

        if not self.data.empty:
            self._default_rtn(self)
        # clean
        if (not self.data.empty) & (self.clean_level != 'none'):
            self._clean_rtn(self)   
        # apply custom functions
        if not self.data.empty:
            self.custom._apply_all(self)
            
        # remove the excess padding, if any applied
        if (self.pad is not None) & (not self.data.empty) & (not verifyPad):
            self.data = self.data[first_time: last_time]
            if not self.empty:
                if (self.data.index[-1] == last_time) & (not want_last_pad):
                    self.data = self.data.iloc[:-1, :]

        # transfer any extra attributes in meta to the Instrument object
        self.meta.transfer_attributes_to_instrument(self)
        sys.stdout.flush()
        return

    def download(self, start, stop, freq='D', user=None, password=None,
                 **kwargs):
        """Download data for given Instrument object from start to stop.
        
        Parameters
        ----------
        start : pandas.datetime
            start date to download data
        stop : pandas.datetime
            stop date to download data
        freq : string
            Stepsize between dates for season, 'D' for daily, 'M' monthly 
            (see pandas)
        user : string
            username, if required by instrument data archive
        password : string
            password, if required by instrument data archive
        **kwargs : dict
            Dictionary of keywords that may be options for specific instruments
            
        Note
        ----
        Data will be downloaded to pysat_data_dir/patform/name/tag
        
        If Instrument bounds are set to defaults they are updated
        after files are downloaded.
        
        """
        import errno
        # make sure directories are there, otherwise create them
        try:
            os.makedirs(self.files.data_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        print('Downloading data to: ', self.files.data_path)
        date_array = utils.season_date_range(start, stop, freq=freq)
        if user is None:
            self._download_rtn(date_array,
                               tag=self.tag,
                               sat_id=self.sat_id,
                               data_path=self.files.data_path,
                               **kwargs)
        else:
            self._download_rtn(date_array,
                               tag=self.tag,
                               sat_id=self.sat_id,
                               data_path=self.files.data_path,
                               user=user,
                               password=password, **kwargs)
        # get current file date range
        first_date = self.files.start_date
        last_date = self.files.stop_date
            
        print('Updating pysat file list')
        self.files.refresh()

        # if instrument object has default bounds, update them
        if len(self.bounds[0]) == 1:
            if(self.bounds[0][0] == first_date and
               self.bounds[1][0] == last_date):
                print('Updating instrument object bounds.')
                self.bounds = None

    @property
    def bounds(self):
        """Boundaries for iterating over instrument object by date or file.

        Parameters
        ----------
        start : datetime object, filename, or None (default)
            start of iteration, if None uses first data date.
            list-like collection also accepted
        end :  datetime object, filename, or None (default)
                end of iteration, inclusive. If None uses last data date.
                list-like collection also accepted

        Note
        ----
        Both start and stop must be the same type (date, or filename) or None

        Examples
        --------
        ::

            inst = pysat.Instrument(platform=platform,
                                    name=name,
                                    tag=tag)
            start = pysat.datetime(2009,1,1)
            stop = pysat.datetime(2009,1,31)
            inst.bounds = (start,stop)

            start2 = pysat.datetetime(2010,1,1)
            stop2 = pysat.datetime(2010,2,14)
            inst.bounds = ([start, start2], [stop, stop2])

        """
        return self._iter_start, self._iter_stop
    
    @bounds.setter        
    def bounds(self, value=None):
        if value is None:
            value = (None, None)
        if len(value) < 2:
            raise ValueError('Must supply both a start and end date/file' +
                             'Supply None if you want the first/last possible')

        start = value[0]
        end = value[1]
        # get the frequency, or step size, of season
        if len(value) == 3:
            step = value[2]
        else:
            # default do daily
            step = 'D'

        if (start is None) and (end is None):
            # set default
            self._iter_start = [self.files.start_date]
            self._iter_stop = [self.files.stop_date]
            self._iter_type = 'date'
            if self._iter_start[0] is not None:
                # check here in case Instrument is initialized with no input
                self._iter_list = utils.season_date_range(self._iter_start,
                                                          self._iter_stop,
                                                          freq=step)
                
        elif((hasattr(start, '__iter__') and not isinstance(start,str)) and
             (hasattr(end, '__iter__') and not isinstance(end,str))):
            base = type(start[0])
            for s, t in zip(start, end):
                if (type(s) != type(t)) or (type(s) != base):
                    raise ValueError('Start and end items must all be of the ' +
                                     'same type')
            if isinstance(start[0], str):
                self._iter_type = 'file'
                self._iter_list = self.files.get_file_array(start, end)
            elif isinstance(start[0], pds.datetime):
                self._iter_type = 'date'
                self._iter_list = utils.season_date_range(start, end, freq=step)
            else:
                raise ValueError('Input is not a known type, string or ' +
                                 'datetime')
            self._iter_start = start
            self._iter_stop = end
            
        elif((hasattr(start, '__iter__') and not isinstance(start,str)) or
             (hasattr(end, '__iter__') and not isinstance(end,str))):
            raise ValueError('Both start and end must be iterable if one ' +
                             'bound is iterable')

        elif isinstance(start, str) or isinstance(end, str):
            if isinstance(start, pds.datetime) or isinstance(end, pds.datetime):
                raise ValueError('Not allowed to mix file and date bounds')
            if start is None:
                start = self.files[0]
            if end is None:
                end = self.files.files[-1]
            self._iter_start = [start]
            self._iter_stop = [end]
            self._iter_list = self.files.get_file_array(self._iter_start,
                                                        self._iter_stop)
            self._iter_type = 'file'

        elif isinstance(start, pds.datetime) or isinstance(end, pds.datetime):
            if start is None:
                start = self.files.start_date
            if end is None:
                end = self.files.stop_date
            self._iter_start = [start]
            self._iter_stop = [end]
            self._iter_list = utils.season_date_range(start, end, freq=step)
            self._iter_type = 'date'
        else:
            raise ValueError('Provided an invalid combination of bounds. ' +
                             'if specifying by file, both bounds must be by ' +
                             'file. Other combinations of datetime objects ' +
                             'and None are allowed.')

    def __iter__(self):
        """Iterates instrument object by loading subsequent days or files.

        Note
        ----
        Limits of iteration, and iteration type (date/file)
        set by `bounds` attribute.

        Default bounds are the first and last dates from files on local system.

        Examples
        --------
        ::

            inst = pysat.Instrument(platform=platform,
                                    name=name,
                                    tag=tag)
            start = pysat.datetime(2009,1,1)
            stop = pysat.datetime(2009,1,31)
            inst.bounds = (start,stop)
            for inst in inst:
                print('Another day loaded', inst.date)

        """

        if self._iter_type == 'file':
            for fname in self._iter_list:
                self.load(fname=fname)
                yield self       
 
        elif self._iter_type == 'date':
            for date in self._iter_list:
                self.load(date=date)
                yield self            
                
    def next(self, verifyPad=False):
        """Manually iterate through the data loaded in Instrument object.
        
        Bounds of iteration and iteration type (day/file) are set by 
        `bounds` attribute.
        
        Note
        ----
        If there were no previous calls to load then the 
        first day(default)/file will be loaded.
         
        """
        
        if self._iter_type == 'date':
            if self.date is not None:
                idx, = np.where(self._iter_list == self.date)
                if (len(idx) == 0):
                    raise StopIteration('File list is empty. Nothing to be done.')
                elif idx[-1]+1 >= len(self._iter_list):
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    idx += 1
                    self.load(date=self._iter_list[idx[0]], verifyPad=verifyPad)
            else:
                self.load(date=self._iter_list[0], verifyPad=verifyPad)

        elif self._iter_type == 'file':
            if self._fid is not None:
                first = self.files.get_index(self._iter_list[0])
                last = self.files.get_index(self._iter_list[-1])
                if (self._fid < first) | (self._fid+1 > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    self.load(fname=self._iter_list[self._fid+1-first],
                              verifyPad=verifyPad)
            else:
                self.load(fname=self._iter_list[0], verifyPad=verifyPad)

    def prev(self, verifyPad=False):
        """Manually iterate backwards through the data in Instrument object.
        
        Bounds of iteration and iteration type (day/file) 
        are set by `bounds` attribute.
        
        Note
        ----
        If there were no previous calls to load then the 
        first day(default)/file will be loaded.
            
        """
        
        if self._iter_type == 'date':
            if self.date is not None:
                idx, = np.where(self._iter_list == self.date)
                if len(idx) == 0:
                    raise StopIteration('File list is empty. Nothing to be done.')
                elif idx[0] == 0:
                    raise StopIteration('Outside the set date boundaries.')
                else:
                    idx -= 1
                    self.load(date=self._iter_list[idx[0]], verifyPad=verifyPad)
            else:
                self.load(date=self._iter_list[-1], verifyPad=verifyPad)

        elif self._iter_type == 'file':
            if self._fid is not None:
                first = self.files.get_index(self._iter_list[0])
                last = self.files.get_index(self._iter_list[-1])
                if (self._fid-1 < first) | (self._fid > last):
                    raise StopIteration('Outside the set file boundaries.')
                else:
                    self.load(fname=self._iter_list[self._fid-1-first],
                              verifyPad=verifyPad)
            else:
                self.load(fname=self._iter_list[-1], verifyPad=verifyPad)

    def _get_var_type_code(self, coltype):
        '''Determines the two-character type code for a given variable type

        Parameters
        ----------
        coltype : type or np.dtype
            The type of the variable

        Returns
        -------
        str
            The variable type code for the given type'''

        if type(coltype) is np.dtype:
            var_type = coltype.kind + str(coltype.itemsize)
            return var_type
        else:
            if coltype is np.int64:
                return 'i8'
            elif coltype is np.int32:
                return 'i4'
            elif coltype is np.int16:
                return 'i2'
            elif coltype is np.int8:
                return 'i1'
            elif coltype is np.uint64:
                return 'u8'
            elif coltype is np.uint32:
                return 'u4'
            elif coltype is np.uint16:
                return 'u2'
            elif coltype is np.uint8:
                return 'u1'
            elif coltype is np.float64:
                return 'f8'
            elif coltype is np.float32:
                return 'f4'
            elif issubclass(coltype, basestring):
                return 'S1'
            else:
                raise TypeError('Unknown Variable Type' + str(coltype))



    def _get_data_info(self, data, file_format):
        """Support file writing by determiniing data type and other options

        Parameters
        ----------
        data : pandas object
            Data to be written
        file_format : basestring
            String indicating netCDF3 or netCDF4

        Returns
        -------
        data_flag, datetime_flag, old_format
        """
        # get type of data
        data_type = data.dtype
        # check if older file_format
        # if file_format[:7] == 'NETCDF3':
        if file_format != 'NETCDF4':
            old_format = True
        else:
            old_format = False
        # check for object type
        if data_type != np.dtype('O'):
            # simple data, not an object
            
            # no 64bit ints in netCDF3
            if (data_type == np.int64) & old_format:
                data = data.astype(np.int32)
                data_type = np.int32
                   
            if data_type == np.dtype('<M8[ns]'):
                if not old_format:
                    data_type = np.int64
                else:
                    data_type = np.float
                datetime_flag = True
            else:
                datetime_flag = False
        else:
            # dealing with a more complicated object
            # iterate over elements until we hit something that is something,
            # and not NaN
            data_type = type(data.iloc[0])
            for i in np.arange(len(data)):
                if len(data.iloc[i]) > 0:
                    data_type = type(data.iloc[i])
                    if not isinstance(data_type, np.float):
                        break
            datetime_flag = False
            
        return data, data_type, datetime_flag
        
    def _filter_netcdf4_metadata(self, mdata_dict, coltype, remove=False):
        """Filter metadata properties to be consistent with netCDF4.
        
        Notes
        -----
        removed forced to True if coltype consistent with a string type
        
        Parameters
        ----------
        mdata_dict : dict
            Dictionary equivalent to Meta object info
        coltype : type
            Type provided by _get_data_info
        remove : boolean (False)
            Removes FillValue and associated parameters disallowed for strings
            
        Returns
        -------
        dict
            Modified as needed for netCDf4
        
        """
        # Coerce boolean types to integers
        for key in mdata_dict:
            if type(mdata_dict[key]) == bool:
                mdata_dict[key] = int(mdata_dict[key])
        if (coltype == type(' ')) or (coltype == type(u' ')):
            remove = True
        # print ('coltype', coltype, remove, type(coltype), )
        if u'_FillValue' in mdata_dict.keys():
            # make sure _FillValue is the same type as the data
            if remove:
                mdata_dict.pop('_FillValue')
            else:
                mdata_dict['_FillValue'] = np.array(mdata_dict['_FillValue']).astype(coltype)
        if u'FillVal' in mdata_dict.keys():
            # make sure _FillValue is the same type as the data
            if remove:
                mdata_dict.pop('FillVal')
            else:
                mdata_dict['FillVal'] = np.array(mdata_dict['FillVal']).astype(coltype)
        return mdata_dict

    def generic_meta_translator(self, meta_to_translate):
        '''Translates the metadate contained in an object into a dictionary
        suitable for export.

        Parameters
        ----------
        meta_to_translate : Meta
            The metadata object to translate

        Returns
        -------
        dict
            A dictionary of the metadata for each variable of an output file
            e.g. netcdf4'''
        export_dict = {}
        if self._meta_translation_table is not None:
            # Create a translation table for the actual values of the meta labels.
            # The instrument specific translation table only stores the names of the
            # attributes that hold the various meta labels
            translation_table = {}
            for key in self._meta_translation_table:
                translation_table[getattr(self, key)] = self._meta_translation_table[key]
        else:
            translation_table = None
        #First Order Data
        for key in meta_to_translate.data.index:
            if translation_table is None:
                export_dict[key] = meta_to_translate.data.loc[key].to_dict()
            else:
                # Translate each key if a translation is provided
                export_dict[key] = {}
                meta_dict = meta_to_translate.data.loc[key].to_dict()
                for original_key in meta_dict:
                    if original_key in translation_table:
                        for translated_key in translation_table[original_key]:
                            export_dict[key][translated_key] = meta_dict[original_key]
                    else:
                        export_dict[key][original_key] = meta_dict[original_key]


        #Higher Order Data
        for key in meta_to_translate.ho_data:
            if key not in export_dict:
                export_dict[key] = {}
            for ho_key in meta_to_translate.ho_data[key].data.index:
                if translation_table is None:
                    export_dict[key+'_'+ho_key] = meta_to_translate.ho_data[key].data.loc[ho_key].to_dict()
                else:
                    #Translate each key if a translation is provided
                    export_dict[key+'_'+ho_key] = {}
                    meta_dict = meta_to_translate.ho_data[key].data.loc[ho_key].to_dict()
                    for original_key in meta_dict:
                        if original_key in translation_table:
                            for translated_key in translation_table[original_key]:
                                export_dict[key+'_'+ho_key][translated_key] = meta_dict[original_key]
                        else:
                            export_dict[key+'_'+ho_key][original_key] = meta_dict[original_key]

        return export_dict

 
    def to_netcdf4(self, fname=None, base_instrument=None, epoch_name='Epoch',
                   zlib=False, complevel=4, shuffle=True):
        """Stores loaded data into a netCDF4 file.
        
        Parameters
        ----------
        fname : string
            full path to save instrument object to
        base_instrument : pysat.Instrument
            used as a comparison, only attributes that are present with
            self and not on base_instrument are written to netCDF
        epoch_name : str
            Label in file for datetime index of Instrument object
        zlib : boolean
            Flag for engaging zlib compression (True - compression on)
        complevel : int
            an integer between 1 and 9 describing the level of compression
            desired (default 4). Ignored if zlib=False
        shuffle : boolean
            the HDF5 shuffle filter will be applied before compressing the data (default True).
            This significantly improves compression. Default is True. Ignored if zlib=False.

        Note
        ----

        Stores 1-D data along dimension 'epoch' - the date time index.
        
        Stores higher order data (e.g. dataframes within series) separately
                    
         - The name of the main variable column is used to prepend subvariable
           names within netCDF, var_subvar_sub
         - A netCDF4 dimension is created for each main variable column
           with higher order data; first dimension Epoch
         - The index organizing the data stored as a dimension variable 
         - from_netcdf4 uses the variable dimensions to reconstruct data structure
            
        
        All attributes attached to instrument meta are written to netCDF attrs.
        
        """
        
        import netCDF4
        import pysat

        file_format = 'NETCDF4'
        # base_instrument used to define the standard attributes attached
        # to the instrument object. Any additional attributes added
        # to the main input Instrument will be written to the netCDF4
        base_instrument = Instrument() if base_instrument is None else base_instrument
        
        # begin processing metadata for writing to the file
        # look to see if user supplied a list of export keys
        # corresponding to internally tracked metadata within pysat
        export_meta = self.generic_meta_translator(self.meta)
        if self._meta_translation_table is None:
            # didn't find a translation table, using the strings
            # attached to the supplied pysat.Instrument object
            export_name_labels = [self.name_label]
            export_units_labels = [self.units_label]
            export_desc_labels = [self.desc_label]
            export_notes_labels = [self.notes_label]
        else:
            # user supplied labels in translation table
            export_name_labels = self._meta_translation_table['name_label']
            export_units_labels = self._meta_translation_table['units_label']
            export_desc_labels = self._meta_translation_table['desc_label']
            export_notes_labels = self._meta_translation_table['notes_label']
            print('Using Metadata Translation Table: ', self._meta_translation_table)
        # Apply instrument specific post-processing to the export_meta
        if hasattr(self._export_meta_post_processing, '__call__'):
            export_meta = self._export_meta_post_processing(export_meta)


        # general process for writing data is this
        # first, take care of the EPOCH information
        # second, iterate over the variable colums in Instrument.data
        # check the type of data
        # if 1D column, do simple write (type is not an object)
        # if it is an object, then check if writing strings, if not strings, then
        # if column is a Series of Frames, write as 2D variables
        # metadata must be filtered before writing to netCDF4, string variables 
        # can't have a fill value
        with netCDF4.Dataset(fname, mode='w', format=file_format) as out_data:
            # number of items, yeah
            num = len(self.data.index)
            # write out the datetime index
            out_data.createDimension(epoch_name, num)
            cdfkey = out_data.createVariable(epoch_name, 'i8',
                                             dimensions=(epoch_name),
                                             zlib=zlib,
                                             complevel=complevel,
                                             shuffle=shuffle) 
            # grab existing metadata for Epoch or create suitable info
            if epoch_name in self.meta:
                new_dict = export_meta[self.meta.var_case_name(epoch_name)]
            else:
                # create empty shell
                new_dict = {}
                
            # update required and basic information if not present
            for export_name_label in export_name_labels:
                if export_name_label not in new_dict:
                    new_dict[export_name_label] = epoch_name
            for export_units_label in export_units_labels:
                if export_units_label not in new_dict:
                    new_dict[export_units_label] = 'Milliseconds since 1970-1-1 00:00:00'
            for export_desc_label in export_desc_labels:
                if export_desc_label not in new_dict:
                    new_dict[export_desc_label] = 'Milliseconds since 1970-1-1 00:00:00'
            for export_notes_label in export_notes_labels:
                if export_notes_label not in new_dict:
                    new_dict[export_notes_label] = ''
            new_dict['calendar'] = 'standard'
            new_dict['Format'] = 'i8'
            new_dict['Var_Type'] = 'data'
            if self.data.index.is_monotonic_increasing:
                new_dict['MonoTon'] = 'increase'
            elif self.data.index.is_monotonic_decreasing:
                new_dict['MonoTon'] = 'decrease' 
            new_dict['Time_Base'] = 'Milliseconds since 1970-1-1 00:00:00'
            new_dict['Time_Scale'] = 'UTC'
            new_dict = self._filter_netcdf4_metadata(new_dict, np.int64)
            # attach metadata
            cdfkey.setncatts(new_dict)

            # attach data
            cdfkey[:] = (self.data.index.values.astype(np.int64) *
                         1.E-6).astype(np.int64)
                            
            # iterate over all of the columns in the Instrument dataframe
            # check what kind of data we are dealing with, then store
            for key in self.data.columns:
                # print (key)
                # get information on type data we are dealing with
                # data is data in proer type( multiformat support)
                # coltype is the direct type, np.int64
                # and datetime_flag lets you know if the data is full of time
                # information
                data, coltype, datetime_flag = self._get_data_info(self[key],
                                                                   file_format)
                # operate on data based upon type
                if self[key].dtype != np.dtype('O'):
                    # not an object, normal basic 1D data
                    # print(key, coltype, file_format)
                    cdfkey = out_data.createVariable(key,
                                                     coltype,
                                                     dimensions=(epoch_name),
                                                     zlib=zlib,
                                                     complevel=complevel,
                                                     shuffle=shuffle) #, chunksizes=1)
                    # attach any meta data, after filtering for standards
                    try:
                        # attach dimension metadata
                        new_dict = export_meta[key]
                        new_dict['Depend_0'] = epoch_name
                        new_dict['Display_Type'] = 'Time Series'
                        new_dict['Format'] = self._get_var_type_code(coltype)
                        new_dict['Var_Type'] = 'data'
                        new_dict = self._filter_netcdf4_metadata(new_dict,
                                                                 coltype)
                        cdfkey.setncatts(new_dict)
                    except KeyError:
                        print(', '.join(('Unable to find MetaData for', key)))
                    # assign data
                    if datetime_flag:
                        # datetime is in nanoseconds, storing milliseconds
                        cdfkey[:] = (data.values.astype(coltype)
                                     * 1.E-6).astype(coltype)
                    else:
                        # not datetime data, just store as is
                        cdfkey[:] = data.values.astype(coltype)
                        
                # back to main check on type of data to write
                else:
                    # it is a Series of objects, need to figure out
                    # what the actual objects are, then act as needed
                    
                    # use info in coltype to get real datatype of object
                    # isinstance isn't working here because of something with coltype
                    if (coltype == type(' ')) or (coltype == type(u' ')):
                        # dealing with a string
                        cdfkey = out_data.createVariable(key, coltype, \
                                            dimensions=(epoch_name), zlib=zlib, \
                                            complevel=complevel, shuffle=shuffle) 
                        # attach any meta data
                        try:
                            # attach dimension metadata
                            new_dict = export_meta[key]
                            new_dict['Depend_0'] = epoch_name
                            new_dict['Display_Type'] = 'Time Series'
                            new_dict['Format'] = self._get_var_type_code(coltype)
                            new_dict['Var_Type'] = 'data'
                            # no FillValue or FillVal allowed for strings
                            new_dict = self._filter_netcdf4_metadata(new_dict, \
                                                        coltype, remove=True)
                            # really attach metadata now
                            cdfkey.setncatts(new_dict)
                        except KeyError:
                            print(', '.join(('Unable to find MetaData for',
                                             key)))

                        # time to actually write the data now
                        cdfkey[:] = data.values
                        
                    # still dealing with an object, not just a series
                    # of strings
                    # maps to if check on coltypes being stringbased
                    else:
                        # presuming a series with a dataframe or series in each location
                        # start by collecting some basic info on dimensions
                        # sizes, names, then create corresponding netCDF4 dimensions
                        # total dimensions stored for object are epoch plus ones
                        # created below
                        dims = np.shape(self[key].iloc[0])
                        obj_dim_names = []
                        if len(dims) == 1:
                            # generally working with higher dimensional data
                            # pad dimensions so that the rest of the code works
                            # for either a Series or a Frame
                            dims = (dims[0], 0)
                        for i, dim in enumerate(dims[:-1]):
                            # don't need to go over last dimension value,
                            # it covers number of columns (if a frame)
                            obj_dim_names.append(key)
                            out_data.createDimension(obj_dim_names[-1], dim)                            
                        # create simple tuple with information needed to create
                        # the right dimensions for variables that will
                        # be written to file
                        var_dim = tuple([epoch_name] + obj_dim_names)
                        
                        # We need to do different things if a series or dataframe
                        # stored
                        try:
                            # start by assuming it is a dataframe
                            # get list of subvariables
                            iterable = self[key].iloc[0].columns
                            # store our newfound knowledge, we are dealing with
                            # a series of DataFrames
                            is_frame = True
                        except AttributeError:
                            # turns out data is Series of Series 
                            # which doesn't have columns
                            iterable = [self[key].iloc[0].name]
                            is_frame = False

                        # find location within main variable
                        # that actually has subvariable data (not just empty frame/series)
                        # so we can determine what the real underlying data types are
                        good_data_loc = 0
                        for jjj in np.arange(len(self.data)):
                            if len(self.data[key].iloc[0]) > 0:
                                data_loc = jjj
                                break
                        # found a place with data, if there is one
                        # now iterate over the subvariables, get data info
                        # create netCDF4 variables and store the data 
                        # stored name is variable_subvariable
                        for col in iterable:
                            if is_frame:
                                # we are working with a dataframe
                                # so multiple subvariables stored under a single
                                # main variable heading
                                data, coltype, _ = self._get_data_info(self[key].iloc[good_data_loc][col], file_format)
                                cdfkey = out_data.createVariable(key + '_' + col,
                                                                 coltype,
                                                                 dimensions=var_dim,
                                                                 zlib=zlib,
                                                                 complevel=complevel,
                                                                 shuffle=shuffle)
                                # attach any meta data
                                try:
                                    new_dict = export_meta[key+'_'+col]
                                    new_dict['Depend_0'] = epoch_name
                                    new_dict['Depend_1'] = obj_dim_names[-1]
                                    new_dict['Display_Type'] = 'Spectrogram'            
                                    new_dict['Format'] = self._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    # print('Frame Writing ', key, col, export_meta[key].children[col])
                                    new_dict = self._filter_netcdf4_metadata(new_dict, coltype)
                                    # print ('mid2 ', new_dict)
                                    cdfkey.setncatts(new_dict)
                                except KeyError:
                                    print(', '.join(('Unable to find MetaData for', key, col)) )
                                # attach data
                                # it may be slow to repeatedly call the store
                                # method as well astype method below collect
                                # data into a numpy array, then write the full
                                # array in one go
                                # print(coltype, dims)
                                temp_cdf_data = np.zeros((num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = self[key].iloc[i][col].values
                                # write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                            else:
                                # we are dealing with a Series
                                # get information about information within series
                                data, coltype, _ = self._get_data_info(self[key].iloc[good_data_loc], file_format)
                                cdfkey = out_data.createVariable(key + '_data',
                                                                coltype,
                                                                dimensions=var_dim,
                                                                zlib=zlib,
                                                                complevel=complevel,
                                                                shuffle=shuffle) #, chunksizes=1)
                                # attach any meta data
                                try:
                                    new_dict = export_meta[key]
                                    new_dict['Depend_0'] = epoch_name
                                    new_dict['Depend_1'] =  obj_dim_names[-1]
                                    new_dict['Display_Type'] = 'Spectrogram' 
                                    new_dict['Format'] = self._get_var_type_code(coltype)
                                    new_dict['Var_Type'] = 'data'
                                    new_dict = self._filter_netcdf4_metadata(new_dict, coltype)
                                    # really attach metadata now
                                    # print ('mid3 ', new_dict)
                                    cdfkey.setncatts(new_dict)
                                except KeyError:
                                    print(', '.join(('Unable to find MetaData for', key)))
                                # attach data
                                temp_cdf_data = np.zeros((num, dims[0])).astype(coltype)
                                for i in range(num):
                                    temp_cdf_data[i, :] = self[i, key].values
                                # write data
                                cdfkey[:, :] = temp_cdf_data.astype(coltype)

                        # we are done storing the actual data for the given higher
                        # order variable, now we need to store the index for all
                        # of that fancy data
                        
                        # get index information
                        data, coltype, datetime_flag = self._get_data_info(self[key].iloc[good_data_loc].index, file_format)
                        # create dimension variable for to store index in netCDF4
                        cdfkey = out_data.createVariable(key,
                                                         coltype, dimensions=var_dim,
                                                         zlib=zlib,
                                                         complevel=complevel,
                                                         shuffle=shuffle)
                        # work with metadata
                        new_dict = export_meta[key]
                        new_dict['Depend_0'] = epoch_name
                        new_dict['Depend_1'] =  obj_dim_names[-1]  
                        new_dict['Display_Type'] = 'Time Series'  
                        new_dict['Format'] = self._get_var_type_code(coltype)
                        new_dict['Var_Type'] = 'data'
                        
                        if datetime_flag:
                            #print('datetime flag')                            
                            for export_name_label in export_name_labels:
                                new_dict[export_name_label] = epoch_name
                            for export_units_label in export_units_labels:
                                new_dict[export_units_label] = 'Milliseconds since 1970-1-1 00:00:00'
                            new_dict = self._filter_netcdf4_metadata(new_dict, coltype)
                            # set metadata dict
                            cdfkey.setncatts(new_dict)
                            # set data
                            temp_cdf_data = np.zeros((num,
                                                      dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = self[i, key].index.values
                            cdfkey[:, :] = (temp_cdf_data.astype(coltype) *
                                            1.E-6).astype(coltype)
 
                        else:
                            if self[key].iloc[data_loc].index.name is not None:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = self[key].iloc[data_loc].index.name
                            else:
                                for export_name_label in export_name_labels:
                                    new_dict[export_name_label] = key
                            new_dict = self._filter_netcdf4_metadata(new_dict, coltype)
                            # assign metadata dict
                            cdfkey.setncatts(new_dict)
                            # set data
                            temp_cdf_data = np.zeros((num, dims[0])).astype(coltype)
                            for i in range(num):
                                temp_cdf_data[i, :] = self[key].iloc[i].index.to_native_types()
                            cdfkey[:, :] = temp_cdf_data.astype(coltype)
                            
            # store any non standard attributes
            # compare this Instrument's attributes to base object
            base_attrb = dir(base_instrument)
            this_attrb = dir(self)
            # filter out any 'private' attributes
            # those that start with a _
            adict = {}
            for key in this_attrb:
                if key not in base_attrb:
                    if key[0] != '_':
                        adict[key] = self.__getattribute__(key)
            # store any non-standard attributes attached to meta
            base_attrb = dir(base_instrument.meta)
            this_attrb = dir(self.meta)
            for key in this_attrb:
                if key not in base_attrb:
                    if key[0] != '_':
                        adict[key] = self.meta.__getattribute__(key)
            adict['pysat_version'] = pysat.__version__
            if 'Conventions' not in adict:
                adict['Conventions'] = 'SPDF ISTP/IACG Modified for NetCDF'
            if 'Text_Supplement' not in adict:
                adict['Text_Supplement'] = ''

            adict['Date_Start'] = pysat.datetime.strftime(self.data.index[0], '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f UTC')
            adict['Date_End'] = pysat.datetime.strftime(self.data.index[-1], '%a, %d %b %Y,  %Y-%m-%dT%H:%M:%S.%f UTC')
            adict['File'] = os.path.split(fname)
            adict['Generation_Date'] = pysat.datetime.utcnow().strftime('%Y%m%d')
            adict['Logical_File_ID'] = os.path.split(fname)[-1].split('.')[:-1]
            # check for binary types
            for key in adict.keys():
                if isinstance(adict[key], bool):
                    adict[key] = int(adict[key])
            # print('adict', adict)
            out_data.setncatts(adict)
        return
