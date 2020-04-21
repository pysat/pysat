"""
tests the pysat instruments and code
"""
from importlib import import_module
import os
import tempfile
import warnings

import pandas as pds
import pytest

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
user_download_dict = {'supermag_magnetometer': {'user': 'rstoneback',
                                                'password': 'None'}}

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


def generate_instrument_list(exclude_list, exclude_tags):
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
                        pass
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

instruments = generate_instrument_list(exclude_list, exclude_tags)

class TestInstrumentsAll():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.package = 'pysat.instruments'

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.package

    @pytest.mark.parametrize("name", pysat.instruments.__all__)
    def test_modules_loadable(self, name):

        # ensure that each module is at minimum importable
        module = import_module(''.join(('.', name)),
                               package=self.package)
        # Check for presence of basic platform / name / tags / sat_id
        assert isinstance(module.platform, str)
        assert isinstance(module.name, str)
        assert isinstance(module.tags, dict)
        assert isinstance(module.sat_ids, dict)

        for sat_id in module.sat_ids.keys():
            for tag in module.sat_ids[sat_id]:
                inst = pysat.Instrument(inst_module=module, tag=tag,
                                        sat_id=sat_id)
                assert isinstance(inst, pysat.Instrument)
                assert inst.platform == module.platform
                assert inst.name == module.name
                assert inst.sat_id == sat_id
                assert inst.tag == tag

    @pytest.mark.parametrize("name", pysat.instruments.__all__)
    def test_required_function_presence(self, name):
        """Check if each required function is present and callable"""
        module = import_module(''.join(('.', name)),
                               package=self.package)
        assert hasattr(module, 'load') & callable(module.load)
        assert hasattr(module, 'list_files') & callable(module.list_files)
        assert hasattr(module, 'download') & callable(module.download)

    @pytest.mark.parametrize("name", pysat.instruments.__all__)
    def test_instrument_tdates(self, name):
        module = import_module(''.join(('.', name)),
                               package=self.package)
        info = module._test_dates
        for sat_id in info.keys():
            for tag in info[sat_id].keys():
                assert isinstance(info[sat_id][tag], pds.datetime)

class TestInstrumentsDownload():

    @pytest.mark.first
    @pytest.mark.parametrize("inst", instruments['list'])
    def test_download(self, inst):
        try:
            start = inst._test_dates[inst.sat_id][inst.tag]
            # check for username
            inst_name = '_'.join((inst.platform, inst.name))
            dl_dict = user_download_dict[inst_name] if inst_name in \
                user_download_dict.keys() else {}
            inst.download(start, start, **dl_dict)
            assert len(inst.files.files) > 0
        except Error as merr:
            # Let users know which instrument is failing, as instrument
            # list is opaque
            print(' '.join(('\nProblem with downloading:', inst.platform,
                            inst.name, inst.tag, inst.sat_id)))
            raise merr


    @pytest.mark.second
    @pytest.mark.parametrize("inst", instruments['list'])
    @pytest.mark.parametrize("clean_level", ['none', 'dirty', 'dusty',
                                             'clean'])
    def test_load(self, inst, clean_level):
        # make sure download was successful
        if len(inst.files.files) > 0:
            try:
                inst.clean_level = clean_level
                target = 'Fake Data to be cleared'
                inst.data = [target]
                start = inst._test_dates[inst.sat_id][inst.tag]
                inst.load(date=start)
                # Make sure fake data is cleared
                assert target not in inst.data
                # If cleaning not used, something should be in the file
                # Not used for clean levels since cleaning may remove all data
                if clean_level == "none":
                    assert not inst.empty
                # For last parametrized clean_level, remove files
                if clean_level == "clean":
                    remove_files(inst)
            except Error as merr:
                # Let users know which instrument is failing, as instrument
                # list is opaque
                print(' '.join(('\nProblem with loading:', inst.platform,
                                inst.name, inst.tag, inst.sat_id)))
                raise merr
        else:
            pytest.skip("Download data not available")
