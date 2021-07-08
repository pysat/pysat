#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""
pysat user module registry utilities

This module allows pysat to provide direct access to external or custom
instrument modules by maintaining information about these instrument modules.

Examples
--------
Instrument support modules must be registered before use. This may be done
individually or for a collection of Instruments at once. For example, assume
there is an implementation for `myInstrument` in the module
`my.package.myInstrument` with platform and name attributes 'myplatform' and
'myname'. Such an instrument may be registered with
::

    registry.register(['my.package.myInstrument'])

The full module name "my.package.myInstrument" will be registered in
pysat.params['user_modules'] and stored as a dict of dicts keyed by platform
and name.

Once registered, subsequent calls to Instrument may use the platform and name
string identifiers.
::

    Instrument('myplatform', 'myname')

A full suite of instrument support modules may be registered at once using
::

    # General form where my.package contains a collection of
    # submodules to support Instrument data sets.
    registry.register_by_module(my.package)

    # Register published packages from pysat team
    import pysatSpaceWeather
    registry.register_by_module(pysatSpaceWeather.instruments)

    import pysatNASA
    registry.register_by_module(pysatNASA.instruments)

    import pysatModels
    registry.register_by_module(pysatModels.models)

"""

import importlib
import logging

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

    return pysat.params['user_modules']


def store():
    """Store current registry onto disk"""

    pysat.params.store()

    return


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

        pysat.params['user_modules']

    which is stored as a dict of dicts keyed by platform and name.

    Examples
    --------
    ::

        from pysat import Instrument
        from pysat.utils import registry

        registry.register(['my.package.name.myInstrument'])

        testInst = Instrument(platform, name)

    """

    for mod_name in module_names:
        # First, ensure module string directs to something importable
        try:
            inst_module = importlib.import_module(mod_name)
        except Exception:
            # Log then preserve trace and propagate error
            estr = ' '.join(('There was a problem trying to import', mod_name))
            logger.error(estr)
            raise

        # Second, check that module is itself pysat compatible
        validate = itc.InstTestClass()

        # Work with test code, create dummy structure to make things work
        class Foo(object):
            pass
        validate.inst_loc = Foo()

        # Parse string to get package part and instrument module part
        parse = mod_name.split('.')

        # Module name without package
        mod_part = parse[-1]

        # The package preamble
        pack_part = parse[:-1]

        # Assign package info to Test class
        validate.inst_loc.__name__ = '.'.join(pack_part)

        # Run tests
        validate.test_modules_standard(mod_part)
        validate.test_standard_function_presence(mod_part)

        # Registry is a dict of dicts with platform, name, and module string.
        # Get the platform and name identifiers from imported module
        platform = inst_module.platform
        name = inst_module.name

        # Only register module if not already present. Multiple names are
        # allowed for a single platform
        if platform not in pysat.params['user_modules']:
            # setup `of dict` part of dict of dicts
            pysat.params.data['user_modules'][platform] = {}

        # Only register name if it is not present under platform
        if name not in pysat.params['user_modules'][platform]:
            logger.info('Registering user module {}'.format(mod_name))
            # Add to current user modules structure and store it to disk
            pysat.params.data['user_modules'][platform][name] = mod_name
            store()
        else:
            # Platform/name combination already registered. Check to see if
            # this is a new package or just a redundant assignment
            if mod_name != pysat.params['user_modules'][platform][name]:
                # New assignment, check for overwrite flag
                if not overwrite:
                    estr = ' '.join(('An instrument has already been ',
                                     'registered for platform:', platform,
                                     'and name:', name,
                                     'which maps to:', mod_name, 'To assign',
                                     'a new module the overwrite flag',
                                     'must be enabled.'))
                    raise ValueError(estr)
                else:
                    # Overwrite with new module information
                    pysat.params.data['user_modules'][platform][name] = mod_name
                    store()

    return


def register_by_module(module):
    """Register all sub-modules attached to input module

    Enables instantiation of a third-party Instrument module using
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
    Gets a list of sub-modules by using the `__all__` attribute,
    defined in the module's `__init__.py`

    Examples
    --------
    ::

        import pysat
        import pysatModels
        pysat.utils.registry.register_by_module(pysatModels.models)

    """

    # Get a list of all user specified modules attached to module
    module_names = module.__all__

    # Add in package preamble
    module_names = [module.__name__ + '.' + mod for mod in module_names]

    # Register all of the sub-modules
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
    Current registered user modules available at pysat.params['user_modules']

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
        if platform in pysat.params['user_modules']:
            if name is None:
                # remove platform entirely
                pysat.params['user_modules'].pop(platform)
                # store
                store()
            else:
                # name supplied, remove single module
                if name in pysat.params['user_modules'][platform]:
                    # remove module
                    pysat.params['user_modules'][platform].pop(name)
                else:
                    # name not in platform
                    estr = ''.join((platform, ', ', name, ': not a registered ',
                                    'instrument module.'))
                    logger.info(estr)
                # remove platform if no remaining instruments
                if len(pysat.params['user_modules'][platform]) == 0:
                    pysat.params['user_modules'].pop(platform)
                # store
                store()
        else:
            # info string if module not registered
            estr = ''.join((platform, ': is not a registered ',
                            'instrument platform.'))
            # platform not in registered modules
            logger.info(estr)

    return
