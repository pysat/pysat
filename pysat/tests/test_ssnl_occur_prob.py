"""
tests the pysat occur_prob object and code
"""

from nose.tools import raises

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
                                pysat.datetime(2008, 1, 31))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_occur_prob_daily_2D_w_bins(self):
        """Runs a basic probability routine daily 2D w/ bins"""
        ans = occur_prob.daily2D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', ['slt'], [12.],
                                 returnBins=True)
        assert abs(ans['slt']['prob'] - 1.0).max() < 1.0e-2
        assert (ans['slt']['prob']).shape == (3, 4)
        assert abs(ans['slt']['bin_x'] - [0, 90, 180, 270, 360]).max() < 1.0e-6
        assert abs(ans['slt']['bin_y'] - [-60, -20, 20, 60]).max() < 1.0e-6

    @raises(ValueError)
    def test_occur_prob_daily_2D_w_bad_data_label(self):
        """Catch a data_label that is not list-like"""
        ans = occur_prob.daily2D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', 'slt', [12.])

    @raises(ValueError)
    def test_occur_prob_daily_2D_w_bad_gate(self):
        """Catch a gate that is not list-like"""
        ans = occur_prob.daily2D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', ['slt'], 12.)

    @raises(ValueError)
    def test_occur_prob_daily_2D_w_mismatched_gate_and_data_label(self):
        """Catch a gate that does not match the data_label"""
        ans = occur_prob.daily2D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', ['slt'], [12., 18.])

    def test_occur_prob_by_orbit_2D_w_bins(self):
        """Runs a basic probability routine by orbit 2D"""
        ans = occur_prob.by_orbit2D(self.testInst, [0, 360, 4], 'longitude',
                                    [-60, 60, 3], 'latitude', ['slt'], [12.],
                                    returnBins=True)
        assert abs(ans['slt']['prob'] - 0.5).max() < 2.0e-2
        assert (ans['slt']['prob']).shape == (3, 4)
        assert abs(ans['slt']['bin_x'] - [0, 90, 180, 270, 360]).max() < 1.0e-6
        assert abs(ans['slt']['bin_y'] - [-60, -20, 20, 60]).max() < 1.0e-6

    def test_occur_prob_daily_3D_w_bins(self):
        """Runs a basic probability routine daily 3D"""
        ans = occur_prob.daily3D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', [0, 24, 2], 'slt',
                                 ['slt'], [12.], returnBins=True)
        assert abs(ans['slt']['prob'][0, :, :] - 0.0).max() < 1.0e-6
        assert abs(ans['slt']['prob'][-1, :, :] - 1.0).max() < 1.0e-6
        assert (ans['slt']['prob']).shape == (2, 3, 4)
        assert abs(ans['slt']['bin_x'] - [0, 90, 180, 270, 360]).max() < 1.0e-6
        assert abs(ans['slt']['bin_y'] - [-60, -20, 20, 60]).max() < 1.0e-6
        assert abs(ans['slt']['bin_z'] - [0, 12, 24]).max() < 1.0e-6

    @raises(ValueError)
    def test_occur_prob_daily_3D_w_bad_data_label(self):
        """Catch a data_label that is not list-like"""
        ans = occur_prob.daily3D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', [0, 24, 2], 'slt',
                                 'slt', [12.])

    @raises(ValueError)
    def test_occur_prob_daily_3D_w_bad_gate(self):
        """Catch a gate that is not list-like"""
        ans = occur_prob.daily3D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', [0, 24, 2], 'slt',
                                 ['slt'], 12.)

    @raises(ValueError)
    def test_occur_prob_daily_3D_w_mismatched_gate_and_data_label(self):
        """Catch a gate that does not match the data_label"""
        ans = occur_prob.daily3D(self.testInst, [0, 360, 4], 'longitude',
                                 [-60, 60, 3], 'latitude', [0, 24, 2], 'slt',
                                 ['slt'], [12., 18.])

    def test_occur_prob_by_orbit_3D_w_bins(self):
        """Runs a basic probability routine by orbit 3D"""
        ans = occur_prob.by_orbit3D(self.testInst, [0, 360, 4], 'longitude',
                                    [-60, 60, 3], 'latitude',
                                    [0, 24, 2], 'slt', ['slt'], [12.],
                                    returnBins=True)
        assert abs(ans['slt']['prob'][0, :, :] - 0.0).max() < 1.0e-6
        assert abs(ans['slt']['prob'][-1, :, :] - 1.0).max() < 1.0e-6
        assert (ans['slt']['prob']).shape == (2, 3, 4)
        assert abs(ans['slt']['bin_x'] - [0, 90, 180, 270, 360]).max() < 1.0e-6
        assert abs(ans['slt']['bin_y'] - [-60, -20, 20, 60]).max() < 1.0e-6
        assert abs(ans['slt']['bin_z'] - [0, 12, 24]).max() < 1.0e-6
