"""
pysat.utils.user_module - user module registry operations in pysat
=========================================

pysat.user_module contains a number of module registry
functions used throughout the pysat package.
"""
import pysat
import os


def load_saved_modules():
    """get list of modules from user_modules.txt"""
    saved_modules = []
    with open(os.path.join(pysat.pysat_dir, 'user_modules.txt'), 'r') as f:
        for _ in f:
            if _ != '' and (_ is not None):
                saved_modules.append(_.strip())
    return saved_modules


def refresh():
    """Rewrite user_modules.txt based on current listing"""
    with open(os.path.join(pysat.pysat_dir, 'user_modules.txt'), 'w') as f:
        for mod in pysat.user_modules:
            f.write(mod + '\n')

def register(module_name):
    """Registers a user module by name, returning the loaded module"""
    import importlib
    inst_module = importlib.import_module(module_name)
    
    if module_name not in pysat.user_modules:
        print('registering user module {}'.format(module_name))
        pysat.user_modules.append(module_name)
        refresh()

    return inst_module

def remove(*module_names):
    """Removes module from registered user modules"""
    for module_name in module_names:
        try:
            pysat.user_modules.remove(module_name)
            # del sys.modules[module_name]
            refresh()
        except ValueError:
            print('User module {} not found'.format(module_name))

