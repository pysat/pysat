"""
tests the registration of user-defined modules
"""
import pytest
import sys

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

    sys.modules[package_name] = package
    sys.modules['.'.join([package_name, module_name])] = instrument


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
        registry.remove(self.platforms, self.platform_names)
        # ensure things are clean
        ensure_not_in_stored_modules(self.modules)

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

    def test_multi_registration(self):
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
