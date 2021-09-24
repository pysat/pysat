# -*- coding: utf-8 -*-
"""Collection of test instruments for the core pysat routines.

Each instrument is contained within a subpackage of this set.
"""

__all__ = ['pysat_testing', 'pysat_testing_xarray', 'pysat_testing2d',
           'pysat_testing2d_xarray', 'pysat_testmodel', 'pysat_testmodel2']

for inst in __all__:
    exec("from pysat.instruments import {x}".format(x=inst))
