# -*- coding: utf-8 -*-
"""
pysat.utils - utilities for running pysat
=========================================

pysat.utils contains a number of functions used
throughout the pysat package.  This includes conversion
of formats, loading of files, and user-supplied info
for the pysat data directory structure.
"""

from . import coords, misc, stats, time

def set_data_dir(path=None, store=None):
    """
    Set the top level directory pysat uses to look for data and reload.

    Parameters
    ----------
    path : string
        valid path to directory pysat uses to look for data
    store : bool
        if True, store data directory for future runs
    """
    import sys
    import os
    import pysat
    if sys.version_info[0] >= 3:
        if sys.version_info[1] < 4:
            import imp
            re_load = imp.reload
        else:
            import importlib
            re_load = importlib.reload
    else:
        re_load = reload
    if store is None:
        store = True
    if os.path.isdir(path):
        if store:
            with open(os.path.join(os.path.expanduser('~'), '.pysat',
                                   'data_path.txt'), 'w') as f:
                f.write(path)
        pysat.data_dir = path
        pysat._files = re_load(pysat._files)
        pysat._instrument = re_load(pysat._instrument)
    else:
        raise ValueError('Path %s does not lead to a valid directory.' % path)
