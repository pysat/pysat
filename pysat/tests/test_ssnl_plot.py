"""
tests the pysat averaging code
"""
import numpy as np
import sys

from nose.tools import assert_raises, raises
import pandas as pds

import pysat
from pysat.ssnl import plot


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean')
        self.testInst.bounds = (pysat.datetime(2008, 1, 1),
                                pysat.datetime(2008, 1, 1))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_scatterplot(self):
        """Check if scatterplot generates"""
        figs = plot.scatterplot(self.testInst, 'longitude', 'latitude',
                                'slt', [0.0, 24.0])

        axes = figs[0].get_axes()
        assert len(figs) == 1
        assert len(axes) == 3

    def test_multiple_scatterplots(self):
        """Check if multiple scatterplots generate"""
        figs = plot.scatterplot(self.testInst, 'longitude', 'latitude',
                                ['slt', 'mlt'], [0.0, 24.0])

        axes = figs[0].get_axes()
        axes2 = figs[1].get_axes()
        assert len(figs) == 2
        assert len(axes) == 3
        assert len(axes2) == 3
