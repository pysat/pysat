#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import importlib
import pytest
import sys

import pysat


class TestWithRegistration():
    """ Test class for unit/integration tests that need registered Instruments
    """

    def setup(self):
        """ Set up the environment by registering three Instruments
        """
        # Define the modules and platforms
        self.modules = [('package1.module1', 'platname1', 'name1'),
                        ('package11.module2', 'platname1', 'name2'),
                        ('package2.module2', 'platname2', 'name2')]

        self.module_names = [mod[0] for mod in self.modules]
        self.platforms = [mod[1] for mod in self.modules]
        self.names = [mod[2] for mod in self.modules]

        # Ensure a clean starting environment, as teardown may have failed
        pysat.utils.registry.remove(self.platforms, self.names)
        self.ensure_not_in_stored_modules()

        # Create modules
        self.create_and_verify_fake_modules()

        # Set common testing attributes
        self.module_name = None
        self.platform = None
        self.name = None

        return

    def teardown(self):
        """ Tear down the environment by removing the fake modules
        """
        pysat.utils.registry.remove(self.platforms, self.names)
        self.ensure_not_in_stored_modules()

        del self.modules, self.module_names, self.platforms, self.names
        del self.module_name, self.platform, self.name

        return

    def ensure_not_in_stored_modules(self):
        """Ensure modules not in stored pysat.user_modules

        Raises
        ------
        AssertionError
            If any of the supplied Instrument modules is registered

        """
        # Get the current Instruments in registry by module
        saved_modules = pysat.utils.registry.load_saved_modules()

        # Ensure the desired modules are not yet registered
        for self.module_name, self.platform, self.name in self.modules:
            if self.platform in saved_modules:
                assert self.module_name not in saved_modules[self.platform]
            else:
                # platform not present, so not registered
                assert True
            with pytest.raises(KeyError):
                pysat.Instrument(self.platform, self.name)

        return

    def create_and_verify_fake_modules(self):
        """Create fake modules and verify instantiation of Instrument modules

        Raises
        ------
        AssertionError
            If fake Instrument platform or name is incorrect

        """

        # Create modules based on supplied module, platform, and name
        for self.module_name, self.platform, self.name in self.modules:
            # Create a fake module
            self.create_fake_module()

            # Test fake module by importing and loading it
            self.module_name = importlib.import_module(self.module_name)
            self.verify_inst_instantiation()

        return

    def create_fake_module(self):
        """Creates fake module and package from pysat_testing test Instrument
        """

        # Use pysat_testing as base instrument
        file_path = pysat.instruments.pysat_testing.__file__
        fake_package, fake_module = self.module_name.split('.')

        # Python 3.5+ implementation from https://stackoverflow.com/a/51575963
        # empty string to allow any file
        importlib.machinery.SOURCE_SUFFIXES.append('')
        spec = importlib.util.spec_from_file_location(fake_module,
                                                      file_path)
        inst = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inst)

        # Update the platform and name
        inst.platform = self.platform
        inst.name = self.name

        package_spec = importlib.util.spec_from_loader(fake_package, None,
                                                       is_package=True)
        package = importlib.util.module_from_spec(package_spec)

        setattr(package, fake_module, inst)
        setattr(package, '__all__', [fake_module])
        sys.modules[fake_package] = package
        sys.modules['.'.join([fake_package, fake_module])] = inst

        return

    def verify_inst_instantiation(self):
        """Verify that information is sufficient for importing module

        Note
        ----
        Checks for presence in pysat.user_modules

        Raises
        ------
        AssertionError
            If fake Instrument module or platform/name combo is incorrect

        """

        if self.module_name is None:
            # Load Instrument by platform and name
            inst = pysat.Instrument(self.platform, self.name)
        else:
            # Load Instrument by module
            inst = pysat.Instrument(inst_module=self.module_name)

        # ensure we have the correct one
        assert inst.platform == self.platform
        assert inst.name == self.name

        return
