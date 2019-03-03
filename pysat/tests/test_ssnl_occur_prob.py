"""
tests the pysat occur_prob object and code
"""

import numpy as np
import sys

from nose.tools import assert_raises, raises
import pandas as pds
import tempfile

import pysat
from pysat.ssnl import occur_prob


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

    def test_occur_prob_daily_2D(self):
        """Runs a basic probability routine daily 2D"""
        ans = occur_prob.daily2D(self.testInst, [0, 360, 3], 'longitude',
                                 [-30, 30, 3], 'latitude', ['slt'], [12.])
        assert abs(ans['slt']['prob'] - 1.0).max() < 1.0e-2
        assert (ans['slt']['prob']).shape == (3, 3)

    def test_occur_prob_by_orbit_2D(self):
        """Runs a basic probability routine by orbit 2D"""
        ans = occur_prob.by_orbit2D(self.testInst, [0, 360, 3], 'longitude',
                                    [-30, 30, 3], 'latitude', ['slt'], [12.])
        assert abs(ans['slt']['prob'] - 0.5).max() < 1.0e-2
        assert (ans['slt']['prob']).shape == (3, 3)

    def test_occur_prob_daily_3D(self):
        """Runs a basic probability routine daily 3D"""
        ans = occur_prob.daily3D(self.testInst, [0, 360, 3], 'longitude',
                                 [-30, 30, 3], 'latitude', [0, 24, 3], ['slt'],
                                 ['dummy1'], [12.])
        assert abs(ans['seconds']['prob'] - 1.0).max() < 1.0e-2
        assert (ans['seconds']['prob']).shape == (3, 3, 3)

    def test_occur_prob_by_orbit_3D(self):
        """Runs a basic probability routine by orbit 3D"""
        ans = occur_prob.by_orbit3D(self.testInst, [0, 360, 3], 'longitude',
                                    [-30, 30, 3], 'latitude',
                                    [0, 24, 3], ['slt'], ['dummy1'], [12.])
        assert abs(ans['seconds']['prob'] - 0.5).max() < 1.0e-2
        assert (ans['seconds']['prob']).shape == (3, 3, 3)
