"""Interface for pysat to manage and analyze multiple pysat instruments.

Each instrument is contained within a subpackage of the pysat.instruments
package.
"""

__all__ = ['testing', 'testing_empty', 'testing_partial', 'single_test']

for const in __all__:
    exec("from pysat.constellations import {:}".format(const))

del const
