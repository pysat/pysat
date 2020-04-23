"""
tests the registration of user-defined modules
"""
import pytest

from pysat import user_modules
from pysat.utils import registry
from pysat import Instrument
from pysat.instruments import pysat_testing
import importlib


def create_fake_module(full_module_name,  platform, name):
    """Creates fake module and package from test instrument"""

    # use pysat_testing as base instrument
    file_path = pysat_testing.__file__.split('.py')[0] + '.py'

    package_name, module_name = full_module_name.split('.')

    try:
        # python 3.5+
        # implementation from https://stackoverflow.com/a/51575963
        importlib.machinery.SOURCE_SUFFIXES.append('')  # empty string to allow any file
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        instrument = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(instrument)

        # update the platform and name
        instrument.platform = platform
        instrument.name = name

        package_spec = importlib.util.spec_from_loader(package_name, None,
                                                       is_package=True)
        package = importlib.util.module_from_spec(package_spec)

    except AttributeError:
        import imp
        # python 2.7
        instrument = imp.load_source(module_name, file_path)

        # update the platform and name
        instrument.platform = platform
        instrument.name = name

        package = imp.new_module(package_name)

    setattr(package, module_name, instrument)

    import sys
    sys.modules[package_name] = package
    sys.modules['.'.join([package_name, module_name])] = instrument


def test_multi_registration():
    modules = [
        ('package1.module1', 'platname1', 'name1'),
        ('package2.module2', 'platname2', 'name2')]

    module_names = [mod[0] for mod in modules]

    registry.remove(*module_names)

    # make sure modules are not yet created
    for module_name in module_names:
        with pytest.raises(ImportError):
            importlib.import_module(module_name)

    # make sure instruments are not yet registered
    saved_modules = registry.load_saved_modules()
    for module_name, platform, name in modules:
        assert module_name not in saved_modules
        with pytest.raises(ImportError):
            Instrument(platform, name)

    # create modules
    for module_name, platform, name in modules:

        create_fake_module(module_name, platform, name)

        test_mod = importlib.import_module(module_name)

        # load module by keyword
        Instrument(inst_module=test_mod)

        # load by platform and name
        registry.register(module_name)
        Instrument(platform, name)

        # check that global registry was updated
        assert module_name in user_modules

    # make sure user_modules.txt was updated
    saved_modules = registry.load_saved_modules()
    for module_name in module_names:
        assert module_name in saved_modules

    # clean up
    registry.remove(*module_names)

    saved_modules = registry.load_saved_modules()
    for module_name in module_names:
        assert module_name not in user_modules
        assert module_name not in saved_modules
