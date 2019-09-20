"""
pysat.utils.user_module - user module registry operations in pysat
=========================================

pysat.user_module contains a number of module registry
functions used throughout the pysat package.
"""




def modules():
    """Return current list of registerd user modules"""
    from pysat import user_modules
    return user_modules


def refresh():
    """Rewrite user_modules.txt based on current listing"""
    from pysat import pysat_dir
    import os
    user_modules = modules()

    with open(os.path.join(pysat_dir, 'user_modules.txt'), 'w') as f:
        for mod in user_modules:
            f.write(mod + '\n')

def register(module_name):
    """Registers a user module by name, returning the loaded module"""
    import importlib
    inst_module = importlib.import_module(module_name)
    
    user_modules = modules()
    if module_name not in user_modules:
        print('registering user module {}'.format(module_name))
        user_modules.append(module_name)
        refresh()

    return inst_module

def remove(module_name):
    """Removes module from registered user modules"""
    user_modules = modules()
    try:
        user_modules.remove(module_name)
        refresh()
    except ValueError:
        print('User module {} not found'.format(module_name))

