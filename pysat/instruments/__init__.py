# -*- coding: utf-8 -*-
"""Collection of test instruments for the core pysat routines.

Each instrument is contained within a subpackage of this set.
"""

__all__ = ['pysat_ndtesting', 'pysat_netcdf', 'pysat_testing',
           'pysat_testmodel', 'pysat_testing_xarray',
           'pysat_testing2d', 'pysat_testing2d_xarray']

for inst in __all__:
    exec("from pysat.instruments import {x}".format(x=inst))

del inst
