"""
tests the pysat instruments and code
"""
from importlib import import_module
import numpy as np
import os
import warnings

import pandas as pds
import pytest
import tempfile

import pysat

# module in list below are excluded from download checks
exclude_list = ['champ_star', 'superdarn_grdex', 'cosmic_gps',
                'demeter_iap', 'sport_ivm',
                'icon_euv', 'icon_ivm', 'icon_mighti', 'icon_fuv',
                'supermag_magnetometer', 'sw_dst']

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


def init_func_external():
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

    instruments = []
    instrument_modules = []

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
                            instruments.append(inst)
                            instrument_modules.append(module)
                        except:
                            pass
    pysat.utils.set_data_dir(saved_path, store=False)

    output = {'list': instruments,
              'names': instrument_names,
              'modules': instrument_modules}

    return output

instruments = init_func_external()


class TestInstrumentQualifier():

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

    @pytest.mark.parametrize("name", pysat.instruments.__all__)
    def test_modules_loadable(self, name):

        # ensure that all modules are at minimum importable
        print(' '.join(('\nChecking importability for module:', name)))
        self.check_module_importable(name)

        try:
            module = import_module(''.join(('.', name)),
                                   package='pysat.instruments')
        except ImportError:
            pass
        else:
            # try and grab basic information about the module so we
            # can iterate over all of the options
            print(' '.join(('Checking module has platform,',
                                      'name, tags, sat_ids. Testing',
                                      'module:', name)))
            self.check_module_info(module)

            try:
                info = module._test_dates
            except AttributeError:
                info = {}
                info[''] = {'': 'failsafe'}
            for sat_id in info.keys():
                for tag in info[sat_id].keys():
                    print(' '.join(('Checking pysat.Instrument',
                                    'instantiation for module:', name,
                                    'tag:', tag, 'sat id:', sat_id)))
                    self.check_module_loadable(module, tag, sat_id)

    @pytest.mark.parametrize("module", pysat.instruments.__all__)
    def test_load_presence(self, module):
        print(' '.join(('\nChecking for load routine for module: ',
                        module.platform, module.name)))
        _ = module.load
        assert True

    @pytest.mark.parametrize("module", pysat.instruments.__all__)
    def test_list_files_presence(self, module):
        print(' '.join(('\nChecking for list_files routine for',
                        'module: ', module.platform, module.name)))
        _ = module.list_files
        assert True

    @pytest.mark.parametrize("module", pysat.instruments.__all__)
    def test_download_presence(self, module):
        print(' '.join(('\nChecking for download routine for',
                        'module: ', module.platform, module.name)))
        _ = module.download
        assert True

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

    @pytest.mark.parametrize("inst", instruments['list'])
    def test_download_and_load(self, inst):
        print(' '.join(('Checking for _test_dates information attached to'
                        'module: ', inst.platform, inst.name, inst.tag,
                        inst.sat_id)))
        self.check_module_tdates(inst)

        print(' '.join(('Checking download routine functionality for module: ',
                        inst.platform, inst.name, inst.tag, inst.sat_id)))
        self.check_download(inst)

        # make sure download was successful
        if len(inst.files.files) > 0:
            print(' '.join(('Checking load routine functionality for module: ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            inst.clean_level = 'none'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "none": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst)

            inst.clean_level = 'dirty'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "dirty": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            inst.clean_level = 'dusty'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "dusty": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            inst.clean_level = 'clean'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "clean": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            remove_files(inst)
        else:
            print('Unable to actually download a file.')
            # raise RuntimeWarning(' '.join(('Download for', inst.platform,
            # inst.name, inst.tag, inst.sat_id, 'was not successful.')))
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
