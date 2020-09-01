"""
tests the registration of user-defined modules
"""

import numpy as np
import pytest
import sys

import pysat
from pysat import user_modules
from pysat.utils import registry
from pysat import Instrument
from pysat.instruments import pysat_testing
import importlib


def create_fake_module(full_module_name, platform, name):
    """Creates fake module and package from test instrument"""

    # use pysat_testing as base instrument
    file_path = pysat_testing.__file__.split('.py')[0] + '.py'

    package_name, module_name = full_module_name.split('.')

    # python 3.5+
    # implementation from https://stackoverflow.com/a/51575963
    # empty string to allow any file
    importlib.machinery.SOURCE_SUFFIXES.append('')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    instrument = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(instrument)

    # update the platform and name
    instrument.platform = platform
    instrument.name = name

    package_spec = importlib.util.spec_from_loader(package_name, None,
                                                   is_package=True)
    package = importlib.util.module_from_spec(package_spec)

    setattr(package, module_name, instrument)
    setattr(package, '__all__', [module_name])
    sys.modules[package_name] = package
    sys.modules['.'.join([package_name, module_name])] = instrument

    return


def create_and_verify_fake_modules(modules):
    """Create fake modules and verify instantiation
    via pysat.Instrument(inst_module=module)

    Parameters
    ----------
    modules : list
        List of tuples (module_string, platform, name)
        that will be checked against stored
        pysat.user_modules

    """

    # create modules
    for module_name, platform, name in modules:
        # create modules
        create_fake_module(module_name, platform, name)
        # import fake modules
        test_mod = importlib.import_module(module_name)
        # load module by keyword
        inst = Instrument(inst_module=test_mod)
        # ensure we have the correct one
        assert inst.platform == platform
        assert inst.name == name

    return


def verify_platform_name_instantiation(modules):
    """Verify that platform and name are sufficient
    for importing module.

    Parameters
    ----------
    modules : list
        List of tuples (module_string, platform, name)
        that will be checked against stored
        pysat.user_modules

    """

    # verify instantiation
    for module_name, platform, name in modules:
        # load by platform and name
        inst2 = Instrument(platform, name)
        # ensure we have the correct one
        assert inst2.platform == platform
        assert inst2.name == name

    return


def ensure_updated_stored_modules(modules):
    """Ensure stored pysat.user_modules updated
    to include modules

    Parameters
    ----------
    modules : list
        List of tuples (module_string, platform, name)
        that will be checked against stored
        pysat.user_modules

    """
    # make sure filesystem was updated
    saved_modules = registry.load_saved_modules()
    for module_name, platform, name in modules:
        assert platform in saved_modules
        assert name in saved_modules[platform]
        assert module_name in saved_modules[platform][name]


def ensure_live_registry_updated(modules):
    """Ensure current pysat.user_modules updated
    to include modules

    Parameters
    ----------
    modules : list
        List of tuples (module_string, platform, name)
        that will be checked against stored
        pysat.user_modules

    """

    for module_name, platform, name in modules:
        # check that global registry was updated
        assert platform in user_modules
        assert name in user_modules[platform]
        assert module_name in user_modules[platform][name]


def ensure_not_in_stored_modules(modules):
    """Ensure modules not in stored pysat.user_modules

    Parameters
    ----------
    modules : list
        List of tuples (module_string, platform, name)
        that will be checked against stored
        pysat.user_modules

    """
    # ensure input modules not in stored modules
    saved_modules = registry.load_saved_modules()
    for module_name, platform, name in modules:
        if platform in saved_modules:
            assert module_name not in saved_modules[platform]
        else:
            # platform not present, so not registered
            assert True
        with pytest.raises(KeyError):
            Instrument(platform, name)


class TestRegistration():
    def setup(self):
        self.modules = [
            ('package1.module1', 'platname1', 'name1'),
            ('package11.module2', 'platname1', 'name2'),
            ('package2.module2', 'platname2', 'name2')]

        self.module_names = [mod[0] for mod in self.modules]
        self.platforms = [mod[1] for mod in self.modules]
        self.platform_names = [mod[2] for mod in self.modules]

        # do pre-cleanup
        try:
            registry.remove(self.platforms, self.platform_names)
        except ValueError:
            pass

        # make sure instruments are not yet registered
        ensure_not_in_stored_modules(self.modules)
        # create modules
        create_and_verify_fake_modules(self.modules)

        return

    def teardown(self):
        # clean up
        try:
            # remove singly to ensure everything that could've been
            # registered has been removed
            for platform, name in zip(self.platforms, self.platform_names):
                registry.remove(platform, name)
        except ValueError:
            # ok if a module has already been removed
            pass
        # ensure things are clean, all have been removed
        ensure_not_in_stored_modules(self.modules)

        return

    def test_single_registration(self):
        """Test registering package one at a time"""

        # create modules
        for module_name, platform, name in self.modules:
            # register package
            registry.register(module_name)

        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # check that global registry was updated
        ensure_live_registry_updated(self.modules)
        # verify update
        ensure_updated_stored_modules(self.modules)

        return

    def test_single_registration_invalid_error(self):
        """Test registering bad package str"""

        # register packages again, this should error
        with pytest.raises(Exception):
            registry.register('made.up.name')

        return

    def test_duplicate_registration_error(self):
        """Test register error for duplicate package"""

        # register all modules at once
        registry.register(self.module_names)
        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # check that global registry was updated
        ensure_live_registry_updated(self.modules)
        # verify update
        ensure_updated_stored_modules(self.modules)

        # register packages again, this should error
        with pytest.raises(ValueError):
            registry.register(self.module_names)

        return

    def test_array_registration(self):
        """Test registering multiple instruments at once"""

        # register all modules at once
        registry.register(self.module_names)

        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # verify registration
        ensure_live_registry_updated(self.modules)
        # verify stored update
        ensure_updated_stored_modules(self.modules)

        return

    def test_platform_removal_array(self):
        """Test removing entire platform at once"""

        # register all modules at once
        registry.register(self.module_names)
        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # verify registration
        ensure_live_registry_updated(self.modules)
        # verify stored update
        ensure_updated_stored_modules(self.modules)
        # remove them using only platform
        registry.remove(np.unique(self.platforms))
        # test for removal performed by teardown
        return

    def test_platform_removal_single_string(self):
        """Test removing entire platform at once"""

        # register all modules at once
        registry.register(self.module_names)
        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # verify registration
        ensure_live_registry_updated(self.modules)
        # verify stored update
        ensure_updated_stored_modules(self.modules)
        # remove them using only platform
        for i, platform in enumerate(np.unique(self.platforms)):
            registry.remove(platform)

        # doing this one by one ensures more lines tested

        return

    def test_platform_name_removal_single_string(self):
        """Test removing single platform/name at a time"""

        # register all modules at once
        registry.register(self.module_names)
        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # verify registration
        ensure_live_registry_updated(self.modules)
        # verify stored update
        ensure_updated_stored_modules(self.modules)
        # remove them using only platform
        count = 0
        for platform, name in zip(self.platforms, self.platform_names):
            registry.remove(platform, name)
            # doing this one by one allows for test that all names
            # for a platform aren't removed
            ensure_not_in_stored_modules([self.modules[count]])
            # test other names still present
            if count < len(self.platforms) - 1:
                ensure_updated_stored_modules(self.modules[count + 1:])
            count += 1
        # test for full removal also performed by teardown

        return

    def test_platform_removal_error(self):
        """Test error raised when removing module not present"""

        # remove non-registered modules using only platform
        with pytest.raises(ValueError):
            registry.remove(['made_up_name'])

        return

    def test_platform_string_removal_error(self):
        """Test error raised when removing module not present"""

        # remove non-registered modules using only platform
        with pytest.raises(ValueError):
            registry.remove('made_up_name')

        return

    def test_platform_name_removal_error(self):
        """Test error raised when removing module not present"""

        # register all modules at once
        registry.register(self.module_names)

        # remove non-registered modules using platform and name
        with pytest.raises(ValueError):
            registry.remove(['made_up_name'], ['made_up_name'])

        # remove non-registered modules using good platform and bad name
        with pytest.raises(ValueError):
            registry.remove([self.platforms[0]], ['made_up_name'])

        return

    def test_module_registration_single(self):
        """Test registering a module containing an instrument"""

        # register package by module
        for module in self.modules:
            root = module[0].split('.')[0]
            registry.register_by_module(sys.modules[root])
        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # check that global registry was updated
        ensure_live_registry_updated(self.modules)
        # verify update
        ensure_updated_stored_modules(self.modules)

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
        self.platform_names = [snip.split('pysat')[-1][1:] for snip in
                               module_names]
        self.platforms = ['pysat'] * len(self.platform_names)
        module_strings = ['.'.join((pkg_name, name)) for name in
                           module_names]
        self.modules = [(mod, plat, nam) for mod, plat, nam in
                        zip(module_strings, self.platforms,
                            self.platform_names)]

        # remove any existing support which may be let over
        # errors if you try to remove a package that isn't
        # registered
        for plat_name in np.unique(self.platforms):
            try:
                registry.remove(plat_name)
            except ValueError:
                pass

        return

    def teardown(self):
        # clean up
        try:
            # remove singly to ensure everything that could've been
            # registered has been removed
            for platform, name in zip(self.platforms, self.platform_names):
                registry.remove(platform, name)
        except ValueError:
            # ok if a module has already been removed
            pass

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
