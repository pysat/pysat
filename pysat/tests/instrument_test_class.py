"""
Standardized class and functions to test instruments for pysat libraries.  Not
directly called by pytest, but imported as part of test_instruments.py.  Can
be imported directly for external instrument libraries of pysat instruments.
"""
import datetime as dt
from importlib import import_module
import os
import tempfile
import warnings

import pytest

import pysat

# dict, keyed by pysat instrument, with a list of usernames and passwords
user_download_dict = {'supermag_magnetometer': {'user': 'rstoneback',
                                                'password': 'None'}}


def remove_files(inst):
    """Remove any files downloaded as part of the unit tests.

    Parameters
    ----------
    inst : pysat.Instrument
        The instrument object that is being tested

    """
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


def generate_instrument_list(package=None):
    """Iterate through and create all of the test Instruments needed.


    Parameters
    ----------
    package : python module
        The instrument library package to test, eg, 'pysat.instruments'

    Note
    ----
    Only want to do this once per instrument library being tested.

    """

    if package is None:
        package = pysat.instruments

    instrument_names = package.__all__
    instrument_download = []
    instrument_no_download = []

    # create temporary directory
    dir_name = tempfile.mkdtemp()
    saved_path = pysat.data_dir
    pysat.utils.set_data_dir(dir_name, store=False)

    for name in instrument_names:
        try:
            module = import_module(''.join(('.', name)),
                                   package=package.__name__)
        except ImportError:
            print(' '.join(["Couldn't import", name]))
            pass
        else:
            # try to grab basic information about the module so we
            # can iterate over all of the options
            try:
                info = module._test_dates
            except AttributeError:
                info = {}
                info[''] = {'': dt.datetime(2009, 1, 1)}
                module._test_dates = info
            for sat_id in info.keys():
                for tag in info[sat_id].keys():
                    inst = pysat.Instrument(inst_module=module,
                                            tag=tag,
                                            sat_id=sat_id,
                                            temporary_file_list=True)
                    inst._test_dates = module._test_dates
                    travis_skip = ((os.environ.get('TRAVIS') == 'true')
                                   and not inst._test_download_travis)
                    if inst._test_download:
                        if not travis_skip:
                            instrument_download.append(inst)
                    elif not inst._password_req:
                        # we don't want to test download for this combo
                        # But we do want to test the download warnings
                        # for instruments without a password requirement
                        instrument_no_download.append(inst)
    pysat.utils.set_data_dir(saved_path, store=False)

    output = {'names': instrument_names,
              'download': instrument_download,
              'no_download': instrument_no_download}

    return output


class InstTestClass():
    """Provides standardized tests for pysat instrument libraries.
    """
    module_attrs = ['platform', 'name', 'tags', 'sat_ids',
                    'load', 'list_files', 'download']
    inst_attrs = ['tag', 'sat_id', 'acknowledgements', 'references']
    inst_callable = ['load', 'list_files', 'download', 'clean', 'default']
    attr_types = {'platform': str, 'name': str, 'tags': dict,
                  'sat_ids': dict, 'tag': str, 'sat_id': str,
                  'acknowledgements': str, 'references': str}

    @pytest.mark.all_inst
    def test_modules_standard(self, name):
        """Checks that modules are importable and have standard properties.
        """
        # ensure that each module is at minimum importable
        module = import_module(''.join(('.', name)),
                               package=self.package.__name__)
        # Check for presence of basic instrument module attributes
        for mattr in self.module_attrs:
            assert hasattr(module, mattr)
            if mattr in self.attr_types.keys():
                assert isinstance(getattr(module, mattr),
                                  self.attr_types[mattr])

        # Check for presence of required instrument attributes
        for sat_id in module.sat_ids.keys():
            for tag in module.sat_ids[sat_id]:
                inst = pysat.Instrument(inst_module=module, tag=tag,
                                        sat_id=sat_id)

                # Test to see that the class parameters were passed in
                assert isinstance(inst, pysat.Instrument)
                assert inst.platform == module.platform
                assert inst.name == module.name
                assert inst.sat_id == sat_id
                assert inst.tag == tag

                # Test the required class attributes
                for iattr in self.inst_attrs:
                    assert hasattr(inst, iattr)
                    assert isinstance(getattr(inst, iattr),
                                      self.attr_types[iattr])

    @pytest.mark.all_inst
    def test_standard_function_presence(self, name):
        """Check if each function is callable and all required functions exist
        """
        module = import_module(''.join(('.', name)),
                               package=self.package.__name__)

        # Test for presence of all standard module functions
        for mcall in self.inst_callable:
            if hasattr(module, mcall):
                # If present, must be a callable function
                assert callable(getattr(module, mcall))
            else:
                # If absent, must not be a required function
                assert mcall not in self.module_attrs

    @pytest.mark.all_inst
    def test_instrument_test_dates(self, name):
        """Check that module has structured test dates correctly."""
        module = import_module(''.join(('.', name)),
                               package=self.package.__name__)
        info = module._test_dates
        for sat_id in info.keys():
            for tag in info[sat_id].keys():
                assert isinstance(info[sat_id][tag], dt.datetime)

    @pytest.mark.first
    @pytest.mark.download
    def test_download(self, inst):
        """Check that instruments are downloadable."""
        try:
            start = inst._test_dates[inst.sat_id][inst.tag]
            # check for username
            inst_name = '_'.join((inst.platform, inst.name))
            dl_dict = user_download_dict[inst_name] if inst_name in \
                user_download_dict.keys() else {}
            inst.download(start, start, **dl_dict)
            assert len(inst.files.files) > 0
        except Exception as merr:
            # Let users know which instrument is failing, since instrument
            # list is opaque
            raise type(merr)(' '.join((str(merr),
                                       '\nProblem with downloading:',
                                       inst.platform,
                                       inst.name,
                                       inst.tag,
                                       inst.sat_id)))

    @pytest.mark.second
    @pytest.mark.download
    @pytest.mark.parametrize("clean_level", ['none', 'dirty', 'dusty', 'clean'])
    def test_load(self, clean_level, inst):
        """Check that instruments load at each cleaning level."""
        # make sure download was successful
        if len(inst.files.files) > 0:
            try:
                # Set Clean Level
                inst.clean_level = clean_level
                target = 'Fake Data to be cleared'
                inst.data = [target]
                start = inst._test_dates[inst.sat_id][inst.tag]
                try:
                    inst.load(date=start)
                except ValueError as verr:
                    # Check if instrument is failing due to strict time flag
                    if str(verr).find('Loaded data') > 0:
                        inst.strict_time_flag = False
                        with warnings.catch_warnings(record=True) as war:
                            inst.load(date=start)
                        assert len(war) >= 1
                        categories = [war[j].category for j in range(0,
                                                                     len(war))]
                        assert UserWarning in categories
                    else:
                        # If error message does not match, raise error anyway
                        raise(verr)

                # Make sure fake data is cleared
                assert target not in inst.data
                # If cleaning not used, something should be in the file
                # Not used for clean levels since cleaning may remove all data
                if clean_level == "none":
                    assert not inst.empty
                # For last parametrized clean_level, remove files
                if clean_level == "clean":
                    remove_files(inst)
            except Exception as merr:
                # Let users know which instrument is failing, since instrument
                # list is opaque
                raise type(merr)(' '.join((str(merr),
                                           '\nProblem with loading:',
                                           inst.platform,
                                           inst.name,
                                           inst.tag,
                                           inst.sat_id)))
        else:
            pytest.skip("Download data not available")

    @pytest.mark.download
    def test_remote_file_list(self, inst):
        """Check if optional list_remote_files routine exists and is callable.
        """
        try:
            name = '_'.join((inst.platform, inst.name))
            if hasattr(getattr(self.package, name), 'list_remote_files'):
                assert callable(inst.remote_file_list)
                date = inst._test_dates[inst.sat_id][inst.tag]
                files = inst.remote_file_list(start=date, stop=date)
                # If test date is correctly chosen, files should exist
                assert len(files) > 0
            else:
                pytest.skip("remote_file_list not available")
        except Exception as merr:
            # Let users know which instrument is failing, since instrument
            # list is opaque
            raise type(merr)(' '.join((str(merr), '\nProblem with checking:',
                                       inst.platform, inst.name, inst.tag,
                                       inst.sat_id)))

    @pytest.mark.no_download
    def test_download_warning(self, inst):
        """Check that instruments without download support have a warning."""
        start = inst._test_dates[inst.sat_id][inst.tag]
        try:
            with warnings.catch_warnings(record=True) as war:
                inst.download(start, start)
            assert len(war) >= 1
            categories = [war[j].category for j in range(0, len(war))]
            assert UserWarning in categories
        except Exception as merr:
            # Let users know which instrument is failing, since instrument
            # list is opaque
            raise type(merr)(' '.join((str(merr), '\nProblem with checking:',
                                       inst.platform, inst.name, inst.tag,
                                       inst.sat_id)))
