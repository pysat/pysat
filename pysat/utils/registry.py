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

or, alternatively, by instatiating an Instrument object using the 
inst_module keyword

    Instrument(inst_module = 'my.package.myInstrument')

Either way, the full module name "my.package.myInstrument" will be
registered in pysat_dir/user_modules.txt and is also listed in
pysat.user_modules.

Once registered, subsequent calls to Instrument may use the platform 
and name:

    Instrument('myplatform', 'myname')

pysat will search the instruments shipped with pysat before
checking the user_modules registry.
"""

import pysat
import os


def load_saved_modules():
    """get list of modules from user_modules.txt"""
    saved_modules = []
    with open(os.path.join(pysat.pysat_dir, 'user_modules.txt'), 'r') as f:
        for line in f:
            if line != '' and (line is not None):
                saved_modules.append(line.strip())
    return saved_modules


def store():
    """Rewrite user_modules.txt based on current listing"""
    with open(os.path.join(pysat.pysat_dir, 'user_modules.txt'), 'w') as f:
        for mod in pysat.user_modules:
            f.write(mod + '\n')

def register(module_name):
    """Registers a user module by name, returning the loaded module

    Parameters
    -----------
    module_name : string
        specify package name and instrument module
        examples:
            my.package.name.my_instrument
            my.pckage.name.myInstrument

    Returns
    --------
    Updates the user module registry specified in 
    pysat_dir/user_module.txt


    Notes
    ------
    Modules should be importable using
        from my.package.name import my_instrument
    
    Module names do not have to follow the pysat platform_name naming
    convection.

    Warning: Registering a module that contains code other than 
    pysat instrument files could result in unexpected consequences.

    Examples
    ---------
    from pysat import Instrument, user_modules
    from pysat.utils import registry

    registry.register('my.package.name.myInstrument')
    assert 'my.package.name.myInstrument' in user_modules



    testInst = Instrument()



    """
    import importlib
    inst_module = importlib.import_module(module_name)
    
    if module_name not in pysat.user_modules:
        print('registering user module {}'.format(module_name))
        pysat.user_modules.append(module_name)
        store()

    return inst_module

def remove(*module_names):
    """Removes module from registered user modules

    Parameters
    -----------
    module_names : str or multiple str
        full module package names to remove from registry

    Notes
    ------
    Current list of user modules can be retrieved from pysat.user_modules


    """
    for module_name in module_names:
        try:
            pysat.user_modules.remove(module_name)
            store()
        except ValueError:
            print('User module {} not found'.format(module_name))

