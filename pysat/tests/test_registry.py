#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""
tests the registration of user-defined modules
"""

import copy
import numpy as np
import pytest
import sys

import pysat
from pysat.utils import registry
from pysat.tests.registration_test_class import TestWithRegistration


def ensure_updated_stored_modules(modules):
    """Ensure stored pysat.params['user_modules'] updated
    to include modules

    Parameters
    ----------
    modules : list
        List of tuples (module_string, platform, name)
        that will be checked against stored
        pysat.params['user_modules']

    """
    # make sure filesystem was updated
    saved_modules = registry.load_saved_modules()
    for module_name, platform, name in modules:
        assert platform in saved_modules
        assert name in saved_modules[platform]
        assert module_name in saved_modules[platform][name]


def ensure_live_registry_updated(modules):
    """Ensure current pysat.params['user_modules'] updated
    to include modules

    Parameters
    ----------
    modules : list
        List of tuples (module_string, platform, name)
        that will be checked against stored
        pysat.params['user_modules']

    """

    for module_name, platform, name in modules:
        # check that global registry was updated
        assert platform in pysat.params['user_modules']
        assert name in pysat.params['user_modules'][platform]
        assert module_name in pysat.params['user_modules'][platform][name]


class TestRegistration(TestWithRegistration):

    # Set setup/teardown to the class defaults
    setup = TestWithRegistration.setup
    teardown = TestWithRegistration.teardown

    def test_duplicate_registration_error(self):
        """Test register error for duplicate package"""

        # Register all modules at once
        registry.register(self.module_names)

        # Verify instantiation by platform/name combo
        for self.module_name, self.platform, self.name in self.modules:
            self.module_name = None  # Must be None to use platform/name combo
            self.verify_inst_instantiation()

        # Check that global registry was updated
        ensure_live_registry_updated(self.modules)

        # Verify update
        ensure_updated_stored_modules(self.modules)

        # Create a new package, the same as an existing one but with a
        # different module name
        mod_name = self.module_names[0]
        sys.modules['pysat_error.test_faux_module'] = sys.modules[mod_name]

        # register packages again, this should error
        with pytest.raises(ValueError):
            registry.register(['pysat_error.test_faux_module'])

        return

    def test_duplicate_registration_overwrite(self):
        """Test register error for duplicate package"""

        # Register all modules at once
        registry.register(self.module_names)

        # Verify instantiation by by platform/name combo
        for self.module_name, self.platform, self.name in self.modules:
            self.module_name = None  # Must be None to use platform/name combo
            self.verify_inst_instantiation()

        # Check that global registry was updated
        ensure_live_registry_updated(self.modules)

        # Verify update
        ensure_updated_stored_modules(self.modules)

        # Create a new package, the same as an existing one, but with a
        # different module name
        mod_name = self.module_names[0]
        sys.modules['pysat_error.test_faux_module'] = sys.modules[mod_name]

        # Register packages again
        registry.register(['pysat_error.test_faux_module'], overwrite=True)
        self.modules[0] = ('pysat_error.test_faux_module', 'platname1', 'name1')

        # Check that global registry was updated
        ensure_live_registry_updated(self.modules)

        # Verify update
        ensure_updated_stored_modules(self.modules)

        return

    def test_registration(self):
        """Test registering multiple instruments at once"""

        # Register all modules at once
        registry.register(self.module_names)

        # Verify instantiation by by platform/name combo
        for self.module_name, self.platform, self.name in self.modules:
            self.module_name = None  # Must be None to use platform/name combo
            self.verify_inst_instantiation()

        # Verify registration
        ensure_live_registry_updated(self.modules)

        # Verify stored update
        ensure_updated_stored_modules(self.modules)

        return

    def test_platform_removal(self):
        """Test removing entire platform at once"""

        # register all modules at once
        registry.register(self.module_names)

        # Verify instantiation by by platform/name combo
        for self.module_name, self.platform, self.name in self.modules:
            self.module_name = None  # Must be None to use platform/name combo
            self.verify_inst_instantiation()

        # verify registration
        ensure_live_registry_updated(self.modules)

        # verify stored update
        ensure_updated_stored_modules(self.modules)

        # remove them using only platform
        uplatforms = np.unique(self.platforms)
        registry.remove(uplatforms, [None] * len(uplatforms))

        return

    def test_platform_removal_single(self):
        """Test removing single platform at a time"""

        # Register all modules at once
        registry.register(self.module_names)

        # Verify instantiation by by platform/name combo
        for self.module_name, self.platform, self.name in self.modules:
            self.module_name = None  # Must be None to use platform/name combo
            self.verify_inst_instantiation()

        # Verify registration
        ensure_live_registry_updated(self.modules)

        # Verify stored update
        ensure_updated_stored_modules(self.modules)

        # Remove modules using only the platform. Doing this one by one ensures
        # more lines are tested  and other registered packages are still
        # present until their removal is performed.
        uplatforms, idx = np.unique(self.platforms, return_index=True)
        umodules = np.asarray(self.modules)[idx]
        for i, self.platform in enumerate(uplatforms):
            # Remove all Instruments on this platform and verify absence
            registry.remove([self.platform], [None])
            self.modules = [umodules[i]]
            self.ensure_not_in_stored_modules()

            # Test that other names still present
            if i < len(self.platforms) - 1:
                ensure_updated_stored_modules(umodules[i + 1:])

        return

    def test_platform_name_removal_single(self):
        """Test removing single platform/name at a time"""

        # Register all modules at once
        registry.register(self.module_names)

        # Verify instantiation by by platform/name combo
        for self.module_name, self.platform, self.name in self.modules:
            self.module_name = None  # Must be None to use platform/name combo
            self.verify_inst_instantiation()

        # Verify registration
        ensure_live_registry_updated(self.modules)

        # Verify stored update
        ensure_updated_stored_modules(self.modules)

        # Remove them using platform and name
        all_modules = list(self.modules)
        for i, self.platform in enumerate(self.platforms):
            # Set the name and module for removal
            self.name = self.names[i]
            self.modules = [all_modules[i]]

            # Remove by platform and name, verifying results
            registry.remove([self.platform], [self.name])
            self.ensure_not_in_stored_modules()

            # Ensure other names and platforms are still present
            if i < len(self.platforms) - 1:
                ensure_updated_stored_modules(self.modules[i + 1:])

        return

    def test_platform_removal_not_present(self):
        """Test error raised when removing module not present"""

        # Try to remove non-registered modules using only platform
        stored_modules = copy.deepcopy(pysat.params['user_modules'])
        registry.remove(['made_up_name'], [None])

        # Make sure nothing changed
        assert stored_modules == pysat.params['user_modules']

        return

    @pytest.mark.parametrize("par_plat, par_name",
                             [(['made_up_name', 'second'], ['made_up_name']),
                              (['made_up_name'], ['made_up_name', 'second']),
                              ([], ['made_up_name', 'second']),
                              ([], ['made_up_name'])])
    def test_platform_name_length_removal_error(self, par_plat, par_name):
        """Test error raised when platforms and names unequal lengths"""

        # Register all modules at once
        registry.register(self.module_names)

        # Raise error when removing non-existent Instruments
        with pytest.raises(ValueError):
            registry.remove(par_plat, par_name)

        return

    def test_module_registration_single(self):
        """Test registering a module containing an instrument"""

        # Register and verify package by module
        for self.module_name, self.platform, self.name in self.modules:
            root = self.module_name.split('.')[0]
            registry.register_by_module(sys.modules[root])
            self.module_name = None  # Test only works here by platform/name
            self.verify_inst_instantiation()

        # Check that global registry was updated
        ensure_live_registry_updated(self.modules)

        # Verify update
        ensure_updated_stored_modules(self.modules)

        return

    def test_module_registration_non_importable(self):
        """Test registering a non-existent module"""

        with pytest.raises(Exception):
            registry.register(['made.up.module'])

        return


class TestModuleRegistration():
    def setup(self):

        self.inst_module = pysat.instruments
        # package name
        pkg_name = self.inst_module.__name__

        # construct inputs similar to TestRegistration
        # to enable use of existing methods
        # almost fully general
        module_names = self.inst_module.__all__
        self.names = [snip.split('pysat')[-1][1:] for snip in module_names]
        self.platforms = ['pysat'] * len(self.names)
        module_strings = ['.'.join((pkg_name, name)) for name in
                          module_names]
        self.modules = [(mod, plat, nam) for mod, plat, nam in
                        zip(module_strings, self.platforms, self.names)]

        # remove any existing support which may be let over
        registry.remove(self.platforms, [None] * len(self.platforms))

        return

    def teardown(self):
        # clean up
        registry.remove(self.platforms, self.names)

        return

    def test_module_registration_multiple(self):
        """Test registering a module containing multiple instruments"""

        # register package by module
        registry.register_by_module(self.inst_module)
        # check that global registry was updated
        ensure_live_registry_updated(self.modules)
        # verify update on disk
        ensure_updated_stored_modules(self.modules)

        return
