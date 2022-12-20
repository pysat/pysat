#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat parameters storage area."""

import copy
from importlib import reload
import os
import pytest
import shutil
import tempfile

import pysat  # Required for reimporting pysat
from pysat._params import Parameters  # Required for eval statements
from pysat.tests.classes.cls_ci import CICleanSetup
from pysat.utils import testing


class TestBasics(object):
    """Unit tests for accessing and changing `pysat._params`."""

    def setup_method(self):
        """Set up the unit test environment for each method."""
        # Store current pysat directory
        self.stored_params = copy.deepcopy(pysat.params)

        # Set up default values
        pysat.params.restore_defaults()

        # Get a temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        self.wd = os.getcwd()

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        pysat.params = copy.deepcopy(self.stored_params)
        pysat.params.store()
        reload(pysat)
        os.chdir(self.wd)
        self.tempdir.cleanup()

    @pytest.mark.parametrize("paths, check",
                             [('.', ['.']),
                              (os.path.join('.', 'hi'),
                               [os.path.join('.', 'hi')]),
                              (os.path.join('.', 'hi', ''),
                               [os.path.join('.', 'hi')]),
                              (os.path.join('.', ''), ['.']),
                              (['.', '.'], None)])
    def test_set_data_dirs(self, paths, check):
        """Test update of pysat directory via params."""
        if check is None:
            check = paths

        # Switch working directory to temp directory
        os.chdir(self.tempdir.name)

        # Assign path
        pysat.params['data_dirs'] = paths
        assert pysat.params['data_dirs'] == check

        # Check if next load of pysat remembers the change
        reload(pysat)
        assert pysat.params['data_dirs'] == check
        return

    @pytest.mark.parametrize("path", ['no_path', 'not_a_directory'])
    def test_set_data_dir_bad_directory(self, path):
        """Ensure you can't set data_dirs to a bad path.

        Parameters
        ----------
        path : str
            Bad path to a directory

        """
        with pytest.raises(ValueError) as verr:
            pysat.params['data_dirs'] = path

        assert str(verr).find("Invalid path") >= 0
        return

    def test_repr(self):
        """Test __repr__ method."""
        out = pysat.params.__repr__()
        assert out.find('Parameters(path=') >= 0
        return

    def test_str(self):
        """Ensure str method works."""

        # Include a user parameter
        pysat.params['pysat_user_test_str'] = 'We are here.'

        out = str(pysat.params)
        # Confirm start of str
        assert out.find('pysat Parameters object') >= 0

        # Confirm that default, non-default, and user values present
        assert out.find('pysat settings') > 0
        assert out.find('Standard parameters:') > 0

        assert out.find('settings (non-default)') > 0
        assert out.find('Standard parameters (no defaults):') > 0

        assert out.find('user values') > 0
        assert out.find('User parameters:') > 0
        return

    def test_restore_defaults(self):
        """Test restore_defaults works as intended."""

        # Get default value, as per setup
        default_val = pysat.params['update_files']

        # Change value to non-default
        pysat.params['update_files'] = not default_val

        # Restore defaults
        pysat.params.restore_defaults()

        # Ensure new value is the default
        assert pysat.params['update_files'] == default_val

        # Make sure that non-default values left as is
        assert pysat.params['data_dirs'] != []
        return

    def test_update_standard_value(self):
        """Test that update of a pre-existing standard value is stored."""

        # Get default value, as per setup
        default_val = pysat.params['update_files']

        # Change value to non-default
        pysat.params['update_files'] = not pysat.params['update_files']

        # Ensure it is in memory
        assert pysat.params['update_files'] is not default_val

        # Get a new parameters instance and verify information is retained.
        # Using eval to ensure all settings with current pysat.params retained.
        new_params = eval(pysat.params.__repr__())
        assert new_params['update_files'] == pysat.params['update_files']
        return

    def test_no_update_user_modules(self):
        """Ensure user_modules not modifiable via params."""

        # Attempt to change value
        with pytest.raises(ValueError) as err:
            pysat.params['user_modules'] = {}
        assert str(err).find('The pysat.utils.registry ') >= 0
        return

    def test_add_user_parameter(self):
        """Add custom parameter and ensure present."""

        pysat.params['hi_there'] = 'hello there!'
        assert pysat.params['hi_there'] == 'hello there!'

        # Get a new parameters instance and verify information is retained
        # Using eval to ensure all settings with current pysat.params retained.
        new_params = eval(pysat.params.__repr__())
        assert new_params['hi_there'] == pysat.params['hi_there']
        return

    def test_clear_and_restart(self):
        """Verify clear_and_restart method impacts all values."""

        pysat.params.clear_and_restart()

        # Check default value
        assert pysat.params['user_modules'] == {}

        # Check value without working default
        assert pysat.params['data_dirs'] == []

        return

    def test_bad_path_instantiation(self):
        """Ensure you can't use bad path when loading Parameters."""
        testing.eval_bad_input(Parameters, OSError,
                               "Supplied path does not exist",
                               input_kwargs={"path": './made_up_name'})

        return


class TestCIonly(CICleanSetup):
    """Tests where we mess with local settings.

    Note
    ----
    These only run in CI environments to avoid breaking an end user's setup

    """

    def test_settings_file_must_be_present(self, capsys):
        """Ensure pysat_settings.json is present."""

        reload(pysat)

        captured = capsys.readouterr()
        # Ensure pysat is running in 'first-time' mode
        assert captured.out.find("Hi there!") >= 0

        # Remove pysat settings file
        shutil.move(os.path.join(self.root, 'pysat_settings.json'),
                    os.path.join(self.root, 'pysat_settings_moved.json'))

        # Ensure we can't create a parameters file without valid .json
        testing.eval_bad_input(Parameters, OSError,
                               'pysat is unable to locate a user settings')

        shutil.move(os.path.join(self.root, 'pysat_settings_moved.json'),
                    os.path.join(self.root, 'pysat_settings.json'))
        return

    def test_settings_file_cwd(self, capsys):
        """Test Parameters works when settings file in current working dir."""

        reload(pysat)

        captured = capsys.readouterr()
        # Ensure pysat is running in 'first-time' mode
        assert captured.out.find("Hi there!") >= 0

        # Move pysat settings file to cwd
        shutil.move(os.path.join(self.root, 'pysat_settings.json'),
                    os.path.join('.', 'pysat_settings.json'))

        # Try loading by supplying a specific path
        test_params = Parameters(path='.')

        # Supplying no path should yield the same result
        test_params2 = Parameters()

        # Confirm data is the same for both
        assert test_params.data == test_params2.data

        # Confirm path is the same for both
        assert test_params.file_path == test_params2.file_path

        # Ensure we didn't load a file in .pysat
        assert not os.path.isfile(os.path.join(self.root,
                                               'pysat_settings.json'))

        # Move pysat settings file back to original
        shutil.move(os.path.join('.', 'pysat_settings.json'),
                    os.path.join(self.root, 'pysat_settings.json'))

        return
