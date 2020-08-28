"""
tests the registration of user-defined modules
"""
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
        registry.remove(self.platforms)
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
        for platform in self.platforms:
            registry.remove(platform)
        # test for removal performed by teardown

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


class TestModuleRegistration():

    def test_module_registration(self):
        """Test registering a module containing multiple instruments"""

        # remove any existing support which may be let over
        # errors if you try to remove a package that isn't
        # registered
        try:
            registry.remove('pysat')
        except ValueError:
            pass

        # register package
        registry.register_by_module(pysat.instruments)
        # get a list of pysat instruments loaded
        platform_names = user_modules['pysat'].keys()
        platform = ['pysat'] * len(user_modules['pysat'])
        mods = ['pysat.instruments.pysat_' + name for name in platform_names]
        modules = []
        for plat, name, mod_str in zip(platform, platform_names, mods):
            modules.append((mod_str, plat, name))
        self.modules = modules
        # verify instantiation
        verify_platform_name_instantiation(self.modules)
        # check that global registry was updated
        ensure_live_registry_updated(self.modules)
        # verify update
        ensure_updated_stored_modules(self.modules)
        # remove modules
        registry.remove('pysat')
        # verifictaion not performed as functionality already tested
        # further, the verify method also checks that the module
        # can't be imported afterward. Since these are pysat modules,
        # they can be imported even when not in user_modules
        return
