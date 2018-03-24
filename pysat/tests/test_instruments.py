"""
tests the pysat meta object and code
"""
import pysat
import pandas as pds
from nose.tools import assert_raises, raises
import nose.tools
from functools import partial
import tempfile


import pysat.instruments.pysat_testing
# import pysat.instruments as instruments
import numpy as np
# import os


import sys
import importlib

exclude_list = ['champ_star', 'superdarn_grdex', 'cosmic_gps', 'cosmic2013_gps', 
                'icon_euv', 'icon_ivm']

def safe_data_dir():
    saved_path = pysat.data_dir
    if saved_path is '':
        saved_path = '.'
    return saved_path

class TestInstrumentQualifier:
    
    def __init__(self):
        """Iterate through and create all of the test Instruments needed"""

        # names of all the instrument modules
        instrument_names = pysat.instruments.__all__
        temp = []
        for name in instrument_names:
            if name not in exclude_list:
                temp.append(name)
        instrument_names = temp
        self.instruments = []
        self.instrument_modules = []

        # create temporary directory  
        dir_name = tempfile.gettempdir()
        saved_path = safe_data_dir()
        pysat.utils.set_data_dir(dir_name, store=False)    
            
        for name in instrument_names:
            try:
                module = importlib.import_module(''.join(('.', name)), package='pysat.instruments')
            except ImportError:
                print ("Couldn't import instrument module")
                pass
            else:
                # try and grab basic information about the module so we
                # can iterate over all of the options
                try:
                    info = module.test_dates
                except AttributeError:
                    info = {}
                    info[''] = {'':pysat.datetime(2009,1,1)}
                    module.test_dates = info            
                for sat_id in info.keys() :  
                    for tag in info[sat_id].keys():
                        try:
                            inst = pysat.Instrument(inst_module=module, 
                                                                    tag=tag, 
                                                                    sat_id=sat_id,
                                                                    temporary_file_list=True) 
                            inst.test_dates = module.test_dates
                            self.instruments.append(inst)
                            self.instrument_modules.append(module)
                        except:
                            pass
        pysat.utils.set_data_dir(saved_path, store=False) 
        
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        pass

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pass

    def check_module_loadable(self, module, tag, sat_id):
        a = pysat.Instrument(inst_module=module, tag=tag, sat_id=sat_id)
        assert True
        
    def check_module_importable(self, name):
        module = importlib.import_module(''.join(('.', name)), package='pysat.instruments')
        assert True
        
    def check_module_info(self, module):
        platform = module.platform
        name = module.name
        tags = module.tags
        sat_ids = module.sat_ids
        check = []
        # check tags is a dict
        check.append(isinstance(tags, dict))
        # that contains strings
        # check sat_ids is a dict
        check.append(isinstance(sat_ids, dict))
        # that contains lists
        assert np.all(check)
    
    def test_modules_loadable(self):
        instrument_names = pysat.instruments.__all__
        self.instruments = []
    
        for name in instrument_names:
            f = partial(self.check_module_importable, name)
            f.description = ' '.join(('Checking importability for module:', name))
            yield (f,)
            
            try:
                module = importlib.import_module(''.join(('.', name)), package='pysat.instruments')
            except ImportError:
                pass
            else:
                # try and grab basic information about the module so we
                # can iterate over all of the options
                f = partial(self.check_module_info, module)
                f.description = ' '.join(('Checking module has platform, name, tags, sat_ids. Testing module:', name))
                yield (f,)

                try:
                    info = module.test_dates
                except AttributeError:
                    info = {}
                    info[''] = {'':'failsafe'}            
                for sat_id in info.keys() :  
                    for tag in info[sat_id].keys():
                        f = partial(self.check_module_loadable, module, tag, sat_id)
                        f.description = ' '.join(('Checking pysat.Instrument instantiation for module:', name, 'tag:', tag, 'sat id:', sat_id))
                        yield (f, )


    def check_load_presence(self, inst):
        _ = inst.load
        assert True
                
    def test_load_presence(self):
        for module in self.instrument_modules:
            f = partial(self.check_load_presence, module)
            f.description = ' '.join(('Checking for load routine for module: ', module.platform, module.name))
            yield (f,)
            
    def check_list_files_presence(self, module):
        _ = module.list_files
        assert True
                
    def test_list_files_presence(self):
        for module in self.instrument_modules:
            f = partial(self.check_list_files_presence, module)
            f.description = ' '.join(('Checking for list_files routine for module: ', module.platform, module.name))
            yield (f,)
            
    def check_download_presence(self, inst):
        _ = inst.download
        assert True
                
    def test_download_presence(self):
        for module in self.instrument_modules:
            yield (self.check_download_presence, module)

    def check_module_tdates(self, module):
        info = module.test_dates
        check = []        
        for sat_id in info.keys():
            for tag in info[sat_id].keys():
                check.append(isinstance(info[sat_id][tag], pysat.datetime))             
        assert np.all(check)

    def check_download(self, inst):
        from unittest.case import SkipTest
        import os
        
        start = inst.test_dates[inst.sat_id][inst.tag]
        # print (start)
        try:
            inst.download(start, start)
        except Exception as e:
            # couldn't run download, try to find test data instead
            print("Couldn't download data, trying to find test data.")
            saved_path = safe_data_dir()

            new_path = os.path.join(pysat.__path__[0],'tests', 'test_data')
            pysat.utils.set_data_dir(new_path, store=False)
            test_dates = inst.test_dates
            inst = pysat.Instrument(platform=inst.platform,
                                    name=inst.name,
                                    tag=inst.tag,
                                    sat_id=inst.sat_id,
                                    temporary_file_list=True)
            inst.test_dates = test_dates
            pysat.utils.set_data_dir(saved_path, store=False)
            if len(inst.files.files) > 0:
                print("Found test data.")
                raise SkipTest
            else:
                print("No test data found.")
                raise e
        assert True

    def check_load(self, inst):
        start = inst.test_dates[inst.sat_id][inst.tag]
        inst.load(date=start)
        assert not inst.data.empty

    def test_download_and_load(self):
        for inst in self.instruments:
            f = partial(self.check_module_tdates, inst)
            f.description = ' '.join(('Checking for test_dates information attached to module: ', inst.platform, inst.name, inst.tag, inst.sat_id))
            yield (f,)
            
            f = partial(self.check_download, inst)
            f.description = ' '.join(('Checking download routine functionality for module: ', inst.platform, inst.name, inst.tag, inst.sat_id))
            yield (f,)
            
            f = partial(self.check_load, inst)
            f.description = ' '.join(('Checking load routine functionality for module: ', inst.platform, inst.name, inst.tag, inst.sat_id))
            yield (f,)
            
            inst.clean_level = 'none'
            f = partial(self.check_load, inst)
            f.description = ' '.join(('Checking load routine functionality for module with clean level "none": ', inst.platform, inst.name, inst.tag, inst.sat_id))
            yield (f,)

            inst.clean_level = 'dirty'
            f = partial(self.check_load, inst)
            f.description = ' '.join(('Checking load routine functionality for module with clean level "dirty": ', inst.platform, inst.name, inst.tag, inst.sat_id))
            yield (f,)
            
            inst.clean_level = 'dusty'
            f = partial(self.check_load, inst)
            f.description = ' '.join(('Checking load routine functionality for module with clean level "dusty": ', inst.platform, inst.name, inst.tag, inst.sat_id))
            yield (f,)

            inst.clean_level = 'clean'
            f = partial(self.check_load, inst)
            f.description = ' '.join(('Checking load routine functionality for module with clean level "clean": ', inst.platform, inst.name, inst.tag, inst.sat_id))
            yield (f,)


    # Optional support
    
    # directory_format string
    
    # multiple file days
    
    # orbit information
    
        # self.directory_format = None
        # self.file_format = None
        # self.multi_file_day = False
        # self.orbit_info = None                
    
    
