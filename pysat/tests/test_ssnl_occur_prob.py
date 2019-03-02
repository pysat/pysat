"""
tests the pysat occur_prob object and code
"""

import numpy as np
import sys

import nose.tools
import pandas as pds
import tempfile

import pysat


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        orbit_info = {'index': 'longitude', 'kind': 'longitude'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=orbit_info)
        self.testInst.bounds = (pysat.datetime(2008, 1, 1),
                                pysat.datetime(2008, 12, 31))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_basic_thing(self):
        """Runs a basic probability routine by orbit 2D"""
        ans = pysat.ssnl.occur_prob.by_orbit2D(self.testInst,
                                               [0, 360, 3], 'longitude',
                                               [-30, 30, 3], 'latitude',
                                               ['slt'], [12.],
                                               returnBins=True)
        assert abs(ans['slt']['prob'] - 0.5).max() < 1.0e-3
        assert (ans['slt']['prob']).shape() = (3, 3)
