"""
tests the pysat - pyglow operations
"""
import pysat

from nose.tools import assert_raises, raises
import nose.tools


def test_import_pyglow():
    """Can we load pyglow?"""

    import pyglow
