#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import copy
from importlib import reload
import os
import pytest
import shutil

import pysat


class TravisCICleanSetup():
    """ Tests where local settings are altered.

    These only run in CI environments such as Travis and Appveyor to avoid
    breaking an end user's setup

    """

    def setup(self):
        """Runs before every method to create a clean testing setup."""

        self.ci_env = (os.environ.get('TRAVIS') == 'true')

        reload(pysat)
        # Store directory paths
        self.saved_path = copy.deepcopy(pysat.params['data_dirs'])

        if not self.ci_env:
            pytest.skip("Skipping local tests to avoid breaking user setup")
        else:
            # Move settings directory to simulate first load after install
            self.root = os.path.join(os.getenv('HOME'), '.pysat')
            self.new_root = os.path.join(os.getenv('HOME'), '.saved_pysat')
            try:
                # Ensure new_root is clean
                shutil.rmtree(self.new_root)
            except FileNotFoundError:
                pass
            shutil.move(self.root, self.new_root)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        if self.ci_env:
            # Move settings back
            shutil.rmtree(self.root)
            shutil.move(self.new_root, self.root)

            # Restore pysat and directory paths
            reload(pysat)
            pysat.params.restore_defaults()
            pysat.params['data_dirs'] = self.saved_path

        del self.ci_env, self.saved_path
