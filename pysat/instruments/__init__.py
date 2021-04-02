# -*- coding: utf-8 -*-
"""
pysat.instruments is a pysat module that provides
the interface for pysat to download, load, manage,
modify and analyze science data.  Each instrument
is contained within a subpackage of this set.
"""

__all__ = ['pysat_testing', 'pysat_testing_xarray', 'pysat_testing2d',
           'pysat_testing2d_xarray', 'pysat_testmodel']

for inst in __all__:
    exec("from pysat.instruments import {x}".format(x=inst))
