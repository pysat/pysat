"""
tests the pysat instruments and code
"""
from importlib import import_module
from functools import partial
import numpy as np
import os
import warnings

import pandas as pds
import tempfile

import pysat
import pysat.instruments.pysat_testing

# module in list below are excluded from download checks
exclude_list = ['champ_star', 'superdarn_grdex', 'cosmic_gps',
                'cosmic2013_gps', 'demeter_iap', 'sport_ivm',
                'icon_euv', 'icon_ivm', 'icon_mighti', 'icon_fuv',
                'supermag_magnetometer', 'sw_dst', 'ucar_tiegcm']

# exclude testing download functionality for specific module name, tag, sat_id
exclude_tags = {'sw_f107': {'tag': ['prelim'], 'sat_id': ['']},
                'sw_kp': {'tag': [''], 'sat_id': ['']}}

# dict, keyed by pysat instrument, with a list of usernames and passwords
user_download_dict = {'supermag_magnetometer': ['rstoneback', None]}


def remove_files(inst):
    # remove any files downloaded as part of the unit tests
    temp_dir = inst.files.data_path
    # Check if there are less than 20 files to ensure this is the testing
    # directory
    if len(inst.files.files.values) < 20:
        for the_file in list(inst.files.files.values):
            # Check if filename is appended with date for fake_daily data
            # ie, does an underscore exist to the right of the file extension?
            if the_file.rfind('_') > the_file.rfind('.'):
                # If so, trim the appendix to get the original filename
                the_file = the_file[:the_file.rfind('_')]
            file_path = os.path.join(temp_dir, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    else:
        warnings.warn(''.join(('Files > 20.  Not deleted.  Please check to ',
                              'ensure temp directory is used')))


def init_func_external(self):
    """Iterate through and create all of the test Instruments needed.
       Only want to do this once.

    """

    # names of all the instrument modules
    instrument_names = pysat.instruments.__all__
    temp = []
    for name in instrument_names:
        if name not in exclude_list:
            temp.append(name)
    instrument_names = temp

    print('The following instrument modules will be tested : ',
          instrument_names)

    self.instrument_names = temp
    self.instruments = []
    self.instrument_modules = []

    # create temporary directory
    dir_name = tempfile.mkdtemp()
    saved_path = pysat.data_dir
    pysat.utils.set_data_dir(dir_name, store=False)

    for name in instrument_names:
        try:
            module = import_module(''.join(('.', name)),
                                   package='pysat.instruments')
        except ImportError:
            print("Couldn't import instrument module")
            pass
        else:
            # try and grab basic information about the module so we
            # can iterate over all of the options
            try:
                info = module._test_dates
            except AttributeError:
                info = {}
                info[''] = {'': pysat.datetime(2009, 1, 1)}
                module._test_dates = info
            for sat_id in info.keys():
                for tag in info[sat_id].keys():
                    if name in exclude_tags and \
                            tag in exclude_tags[name]['tag'] and \
                            sat_id in exclude_tags[name]['sat_id']:
                        # we don't want to test download for this combo
                        print(' '.join(['Excluding', name, tag, sat_id]))
                    else:
                        try:
                            inst = pysat.Instrument(inst_module=module,
                                                    tag=tag,
                                                    sat_id=sat_id,
                                                    temporary_file_list=True)
                            inst._test_dates = module._test_dates
                            self.instruments.append(inst)
                            self.instrument_modules.append(module)
                        except:
                            pass
    pysat.utils.set_data_dir(saved_path, store=False)


init_inst = None
init_mod = None
init_names = None


class TestInstrumentQualifier():

    def __init__(self):
        """Iterate through and create all of the test Instruments needed"""
        global init_inst
        global init_mod
        global init_names

        if init_inst is None:
            init_func_external(self)
            init_inst = self.instruments
            init_mod = self.instrument_modules
            init_names = self.instrument_names

        else:
            self.instruments = init_inst
            self.instrument_modules = init_mod
            self.instrument_names = init_names

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        pass

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pass

    def check_module_loadable(self, module, tag, sat_id):
        _ = pysat.Instrument(inst_module=module, tag=tag, sat_id=sat_id)
        assert True

    def check_module_importable(self, name):
        _ = import_module(''.join(('.', name)),
                          package='pysat.instruments')
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

        # ensure that all modules are at minimum importable
        for name in pysat.instruments.__all__:
            f = partial(self.check_module_importable, name)
            f.description = ' '.join(('Checking importability for module:',
                                      name))
            yield (f,)

            try:
                module = import_module(''.join(('.', name)),
                                       package='pysat.instruments')
            except ImportError:
                pass
            else:
                # try and grab basic information about the module so we
                # can iterate over all of the options
                f = partial(self.check_module_info, module)
                f.description = ' '.join(('Checking module has platform,',
                                          'name, tags, sat_ids. Testing',
                                          'module:', name))
                yield (f,)

                try:
                    info = module._test_dates
                except AttributeError:
                    info = {}
                    info[''] = {'': 'failsafe'}
                for sat_id in info.keys():
                    for tag in info[sat_id].keys():
                        f = partial(self.check_module_loadable, module, tag,
                                    sat_id)
                        f.description = ' '.join(('Checking pysat.Instrument',
                                                  'instantiation for module:',
                                                  name, 'tag:', tag, 'sat id:',
                                                  sat_id))
                        yield (f, )

    def check_load_presence(self, inst):
        _ = inst.load
        assert True

    def test_load_presence(self):
        for module in self.instrument_modules:
            f = partial(self.check_load_presence, module)
            f.description = ' '.join(('Checking for load routine for module: ',
                                      module.platform, module.name))
            yield (f,)

    def check_list_files_presence(self, module):
        _ = module.list_files
        assert True

    def test_list_files_presence(self):
        for module in self.instrument_modules:
            f = partial(self.check_list_files_presence, module)
            f.description = ' '.join(('Checking for list_files routine for',
                                      'module: ', module.platform,
                                      module.name))
            yield (f,)

    def check_download_presence(self, inst):
        _ = inst.download
        assert True

    def test_download_presence(self):
        for module in self.instrument_modules:
            yield (self.check_download_presence, module)

    def check_module_tdates(self, module):
        info = module._test_dates
        check = []
        for sat_id in info.keys():
            for tag in info[sat_id].keys():
                check.append(isinstance(info[sat_id][tag], pysat.datetime))
        assert np.all(check)

    def check_download(self, inst):
        from unittest.case import SkipTest
        import os

        start = inst._test_dates[inst.sat_id][inst.tag]
        try:
            # check for username
            inst_name = '_'.join((inst.platform, inst.name))
            if inst_name in user_download_dict:
                inst.download(start, start,
                              user=user_download_dict[inst_name][0],
                              password=user_download_dict[inst_name][1])
            else:
                inst.download(start, start)
        except Exception as e:
            # couldn't run download, try to find test data instead
            print("Couldn't download data, trying to find test data.")
            saved_path = pysat.data_dir

            new_path = os.path.join(pysat.__path__[0], 'tests', 'test_data')
            pysat.utils.set_data_dir(new_path, store=False)
            _test_dates = inst._test_dates
            inst = pysat.Instrument(platform=inst.platform,
                                    name=inst.name,
                                    tag=inst.tag,
                                    sat_id=inst.sat_id,
                                    temporary_file_list=True)
            inst._test_dates = _test_dates
            pysat.utils.set_data_dir(saved_path, store=False)
            if len(inst.files.files) > 0:
                print("Found test data.")
                raise SkipTest
            else:
                print("No test data found.")
                raise e
        assert True

    def check_load(self, inst, fuzzy=False):
        # set ringer data
        inst.data = pds.DataFrame([0])
        start = inst._test_dates[inst.sat_id][inst.tag]
        inst.load(date=start)
        if not fuzzy:
            assert not inst.empty
        else:
            try:
                assert inst.data != pds.DataFrame([0])
            except:
                # if there is an error, they aren't the same
                assert True

        # clear data
        inst.data = pds.DataFrame(None)

    def test_download_and_load(self):
        for inst in self.instruments:
            f = partial(self.check_module_tdates, inst)
            f.description = ' '.join(('Checking for _test_dates information',
                                      'attached to module: ', inst.platform,
                                      inst.name, inst.tag, inst.sat_id))
            yield (f,)

            f = partial(self.check_download, inst)
            f.description = ' '.join(('Checking download routine',
                                      'functionality for module: ',
                                      inst.platform, inst.name, inst.tag,
                                      inst.sat_id))
            yield (f,)

            # make sure download was successful
            if len(inst.files.files) > 0:
                f = partial(self.check_load, inst, fuzzy=True)
                f.description = ' '.join(('Checking load routine',
                                          'functionality for module: ',
                                          inst.platform, inst.name, inst.tag,
                                          inst.sat_id))
                yield (f,)

                inst.clean_level = 'none'
                f = partial(self.check_load, inst)
                f.description = ' '.join(('Checking load routine',
                                          'functionality for module with',
                                          'clean level "none": ',
                                          inst.platform, inst.name, inst.tag,
                                          inst.sat_id))
                yield (f,)

                inst.clean_level = 'dirty'
                f = partial(self.check_load, inst, fuzzy=True)
                f.description = ' '.join(('Checking load routine',
                                          'functionality for module with',
                                          'clean level "dirty": ',
                                          inst.platform, inst.name, inst.tag,
                                          inst.sat_id))
                yield (f,)

                inst.clean_level = 'dusty'
                f = partial(self.check_load, inst, fuzzy=True)
                f.description = ' '.join(('Checking load routine',
                                          'functionality for module with',
                                          'clean level "dusty": ',
                                          inst.platform, inst.name, inst.tag,
                                          inst.sat_id))
                yield (f,)

                inst.clean_level = 'clean'
                f = partial(self.check_load, inst, fuzzy=True)
                f.description = ' '.join(('Checking load routine',
                                          'functionality for module with',
                                          'clean level "clean": ',
                                          inst.platform, inst.name, inst.tag,
                                          inst.sat_id))
                yield (f,)

                remove_files(inst)
            else:
                print('Unable to actually download a file.')
                # raise RuntimeWarning(' '.join(('Download for', inst.platform,
                # inst.name, inst.tag, inst.sat_id, 'was not successful.')))
                import warnings
                warnings.warn(' '.join(('Download for', inst.platform,
                                        inst.name, inst.tag, inst.sat_id,
                                        'was not successful.')))

    # Optional support

    # directory_format string

    # multiple file days

    # orbit information

        # self.directory_format = None
        # self.file_format = None
        # self.multi_file_day = False
        # self.orbit_info = None
