"""
pysat.constellations is a pysat module that provides
the interface for pysat to manage and analyze data
from multiple pysat instrument.  Each instrument
is contained within a subpackage of the pysat.instruments
package.
"""

__all__ = ['testing', 'testing_empty', 'single_test', 'test_add_opposite',
           'test_add_similar', 'test_diff_same', 'test_diff_similar']

for const in __all__:
    exec("from pysat.constellations import {:}".format(const))
    
