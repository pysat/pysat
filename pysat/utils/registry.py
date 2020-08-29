"""
pysat.utils.registry - user module registry operations in pysat
=========================================

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
module my.package.myInstrument having  platform and name attributes
'myplatform' and 'myname'. Such an instrument may be registered with

    registry.register('my.package.myInstrument')


The full module name "my.package.myInstrument" will be
registered in pysat_dir/user_modules.txt and is also listed in
pysat.user_modules.

Once registered, subsequent calls to Instrument may use the platform
and name:

    Instrument('myplatform', 'myname')

pysat will search the instruments shipped with pysat before
checking the user_modules registry.
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
    fpath = os.path.join(pysat.pysat_dir, 'user_modules.txt')
    with open(fpath, 'r') as fopen:
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
    """Store registered pysat.Instrument modules to disk"""

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


def register(module_names):
    """Registers a user pysat.Instrument module by name

    Enables instantiation of a third-party Instrument
    module using
    ::
        inst = pysat.Instrument(platform, name)

    Parameters
    -----------
    module_names : str or list-like of str
        specify package name and instrument modules

    Note
    ----
    Modules should be importable using
        from my.package.name import my_instrument

    Module names do not have to follow the pysat platform_name naming
    convection.

    Warning: Registering a module that contains code other than
    pysat instrument files could result in unexpected consequences.

    Examples
    --------
    ::
        from pysat import Instrument, user_modules
        from pysat.utils import registry

        registry.register('my.package.name.myInstrument')
        assert 'my.package.name.myInstrument' in user_modules

        testInst = Instrument(platform, name)

    """

    if isinstance(module_names, str):
        module_names = [module_names]

    for module_name in module_names:
        # first, ensure module string directs to something importable
        try:
            inst_module = importlib.import_module(module_name)
        except Exception as error:
            # log error and then preserve trace and propagate error
            logger.error(error)
            raise

        # second, check that module is itself pysat compatible
        validate = itc.InstTestClass()
        validate.test_modules_standard('', inst_module)
        validate.test_standard_function_presence('', inst_module)

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
            estr = ' '.join(('An instrument has already been registered using',
                             'platform:', platform, 'and name:', name,
                             'which maps to:', module_name))
            raise ValueError(estr)

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

    Note
    ----
    Gets a list of sub-modules by using the __all__ attribute,
    defined in the module's __init__.py

    """

    # get a list of all user specified modules attached to module
    try:
        module_names = module.__all__
        # add in package preamble
        module_names = [module.__name__ + '.' + mod for mod in module_names]
        # register all of them
        register(module_names)
    except Exception as error:
        logger.error(error)
        raise

    return


def remove(platforms, names=None):
    """Removes module from registered user modules

    Parameters
    ----------
    platforms : str of list-like of str
        One or more platform identifiers to remove
    names : str of list-like of str
        Name identifiers, paired with platforms, to remove.
        If names is None, then all instruments under
        `platforms` will be removed. Supports a mixed
        combination of name labels and None. (default=None)

    Note
    ----
    Current registered user modules available at pysat.user_modules

    """

    # support input of both string and list-like of strings
    if isinstance(platforms, str):
        platforms = [platforms]
    if isinstance(names, str):
        names = [names]

    # ensure names is as long as platforms under default input
    if names is None:
        names = [None] * len(platforms)

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
                    # error string if module not registered
                    estr = ''.join((platform, ', ', name, ': not a registered ',
                                    'instrument module.'))
                    raise ValueError(estr)
                # remove platform if no remaining instruments
                if len(pysat.user_modules[platform]) == 0:
                    pysat.user_modules.pop(platform)
                # store
                store()
        else:
            # error string if module not registered
            estr = ''.join((platform, ': is not a registered ',
                            'instrument platform.'))

            # platform not in registered modules
            raise ValueError(estr)

    return
