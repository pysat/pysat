"""
pysat.utils.registry - user module registry operations in pysat
===============================================================

Instantiating a pysat.Instrument object for a particular data set
requires a module for each instrument with routines that download,
load, and clean the respective data. Instructions for adding support
for external modules may be found here
https://pysat.readthedocs.io/en/latest/new_instrument.html

This module enables pysat to provide the same user experience for
external or custom instrument modules, as for those shipped
with pysat, by maintaining information about these outside
instrument files.

Instrument support modules must be registered before use. For
example, assume there is an implementation for myInstrument in the
module my.package.myInstrument with platform and name attributes
'myplatform' and 'myname'. Such an instrument may be registered with
::

    registry.register('my.package.myInstrument')

The full module name "my.package.myInstrument" will be
registered in pysat_dir/user_modules.txt and is also listed in
::

    pysat.user_modules
which is stored as a dict of dicts keyed by platform and name.

Once registered, subsequent calls to Instrument may use the platform
and name string identifiers.
::

    Instrument('myplatform', 'myname')

"""

import importlib
import logging
import os

import pysat
import pysat.tests.instrument_test_class as itc
logger = logging.getLogger(__name__)


def load_saved_modules():
    """Load registered pysat.Instrument modules

    Returns
    -------
    dict of dicts
        instrument module strings are keyed by
        platform then name

    """

    saved_modules = {}
    user_modules_file = os.path.join(pysat.pysat_dir, 'user_modules.txt')
    with pysat.utils.NetworkLock(user_modules_file, 'r') as fopen:
        for line in fopen:
            if line != '' and (line is not None):
                # remove trailing whitespace
                line = line.strip()
                # stored as platform, name, module string
                platform, name, inst_module = line.split(' ')
                # dict of dicts, keyed by platform then name
                if platform not in saved_modules:
                    saved_modules[platform] = {}
                # store instrument module string
                saved_modules[platform][name] = inst_module

    return saved_modules


def store():
    """Rewrite user_modules.txt based on current listing"""

    with open(os.path.join(pysat.pysat_dir, 'user_modules.txt'), 'w') as fopen:
        for platform in pysat.user_modules:
            for name in pysat.user_modules[platform]:
                # instrument module string
                inst_mod = pysat.user_modules[platform][name]
                # format for storage
                # platform, name, instrument module
                out = ' '.join((platform, name, inst_mod, '\n'))
                # store
                fopen.write(out)

        # in case of network file system
        fopen.flush()
        os.fsync(fopen.fileno())


def register(module_names, overwrite=False):
    """Registers a user pysat.Instrument module by name

    Enables instantiation of a third-party Instrument
    module using
    ::

        inst = pysat.Instrument(platform, name, tag=tag, inst_id=inst_id)

    Parameters
    ----------
    module_names : list-like of str
        specify package name and instrument modules
    overwrite : bool
        If True, an existing registration will be updated
        with the new module information.

    Raises
    ------
    ValueError
        If a new module is input with a platform and name that is already
        associated with a registered module and the overwrite flag is set to
        False.

    Warnings
    --------
    Registering a module that contains code other than pysat instrument
    files could result in unexpected consequences.

    Note
    ----
    Modules should be importable using
    ::

        from my.package.name import my_instrument

    Module names do not have to follow the pysat platform_name naming
    convection.

    Current registered modules bay be found at
    ::

        pysat.user_modules

    which is stored as a dict of dicts keyed by platform and name.

    Examples
    --------
    ::

        from pysat import Instrument, user_modules
        from pysat.utils import registry

        registry.register('my.package.name.myInstrument')

        testInst = Instrument(platform, name)

    """

    for module_name in module_names:
        # first, ensure module string directs to something importable
        try:
            inst_module = importlib.import_module(module_name)
        except Exception:
            # log then preserve trace and propagate error
            estr = ' '.join(('There was a problem trying to import',
                             module_name))
            logger.error(estr)
            raise

        # second, check that module is itself pysat compatible
        validate = itc.InstTestClass()
        # work with test code, create dummy structure to make things work

        class Foo(object):
            pass
        validate.inst_loc = Foo()
        # parse string to get package part and instrument module part
        parse = module_name.split('.')
        # module name without package
        mod_part = parse[-1]
        # the package preamble
        pack_part = parse[:-1]
        # assign package info to Test class
        validate.inst_loc.__name__ = '.'.join(pack_part)
        # run tests
        validate.test_modules_standard(mod_part)
        validate.test_standard_function_presence(mod_part)

        # registry is a dict of dicts
        # platform, name, module string
        # get platform and name identifiers from imported module
        platform = inst_module.platform
        name = inst_module.name
        # only register module if not already present
        # multiple names allowed for a single platform
        if platform not in pysat.user_modules:
            # setup `of dict` part of dict of dicts
            pysat.user_modules[platform] = {}
        # only register name if not present under platform
        if name not in pysat.user_modules[platform]:
            logger.info('Registering user module {}'.format(module_name))
            # add to current user modules structure
            pysat.user_modules[platform][name] = module_name
            # store user modules to disk
            store()
        else:
            # platform/name combination already registered
            # check if this is a new package or just a redundant assignment
            if module_name != pysat.user_modules[platform][name]:
                # new assignment, check for overwrite flag
                if not overwrite:
                    estr = ' '.join(('An instrument has already been ',
                                     'registered for platform:', platform,
                                     'and name:', name,
                                     'which maps to:', module_name, 'To assign',
                                     'a new module the overwrite flag',
                                     'must be enabled.'))
                    raise ValueError(estr)
                else:
                    # overwrite with new module information
                    pysat.user_modules[platform][name] = module_name
                    # store
                    store()

    return


def register_by_module(module):
    """Register all sub-modules attached to input module

    Enables instantiation of a third-party Instrument
    module using
    ::
        inst = pysat.Instrument(platform, name)

    Parameters
    ----------
    module : Python module
        Module with one or more pysat.Instrument support modules
        attached as sub-modules to the input `module`

    Raises
    ------
    ValueError
        If platform and name associated with a module are already registered

    Note
    ----
    Gets a list of sub-modules by using the __all__ attribute,
    defined in the module's __init__.py

    Examples
    --------
    ::

        import pysat
        import pysatModels
        pysat.utils.registry.register_by_module(pysatModels.models)

        import pysatSpaceWeather
        pysat.utils.registry.register_by_module(pysatSpaceWeather.instruments)

    """

    # get a list of all user specified modules attached to module
    module_names = module.__all__
    # add in package preamble
    module_names = [module.__name__ + '.' + mod for mod in module_names]
    # register all of them
    register(module_names)

    return


def remove(platforms, names):
    """Removes module from registered user modules

    Parameters
    ----------
    platforms : list-like of str
        Platform identifiers to remove
    names : list-like of str
        Name identifiers, paired with platforms, to remove.
        If the names element paired with the platform element is None,
        then all instruments under the specified platform will be
        removed. Should be the same type as `platforms`.

    Raises
    ------
    ValueError
        If platform and/or name are not currently registered

    Note
    ----
    Current registered user modules available at pysat.user_modules

    Examples
    --------
    ::

        platforms = ['platform1', 'platform2']
        names = ['name1', 'name2']

        # remove all instruments with platform=='platform1'
        registry.remove(['platform1'], [None])
        # remove all instruments with platform 'platform1' or 'platform2'
        registry.remove(platforms, [None, None])
        # remove all instruments with 'platform1', and individual instrument
        # for 'platform2', 'name2'
        registry.remove(platforms, [None, 'name2']
        # remove 'platform1', 'name1', as well as 'platform2', 'name2'
        registry.remove(platforms, names)

    """

    # ensure equal number of inputs
    if len(names) != len(platforms):
        estr = "".join(("The number of 'platforms' and 'names' must be the ",
                        "same, or names must be None, which removes all ",
                        "instruments under each platform."))
        raise ValueError(estr)

    # iterate over inputs and remove modules
    for platform, name in zip(platforms, names):
        if platform in pysat.user_modules:
            if name is None:
                # remove platform entirely
                pysat.user_modules.pop(platform)
                # store
                store()
            else:
                # name supplied, remove single module
                if name in pysat.user_modules[platform]:
                    # remove module
                    pysat.user_modules[platform].pop(name)
                else:
                    # name not in platform
                    estr = ''.join((platform, ', ', name, ': not a registered ',
                                    'instrument module.'))
                    logger.info(estr)
                # remove platform if no remaining instruments
                if len(pysat.user_modules[platform]) == 0:
                    pysat.user_modules.pop(platform)
                # store
                store()
        else:
            # info string if module not registered
            estr = ''.join((platform, ': is not a registered ',
                            'instrument platform.'))
            # platform not in registered modules
            logger.info(estr)

    return
