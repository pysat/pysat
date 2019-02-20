import datetime as dt
import numpy as np

from nose.tools import assert_raises

import pysat
from pysat.ssnl import avg

class TestSSNLAvg():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean', update_files=True)
        self.testInst.bounds = [dt.datetime(2008, 1, 1),
                                dt.datetime(2008, 1, 31)]
        self.test_bins = [0, 24, 24]
        self.test_label = 'slt'
        self.test_data = ['dummy1', 'dummy2']
        self.out_keys = ['count', 'avg_abs_dev', 'median', 'bin_x', 'bin_y']
        self.out_data = {'dummy1':
                         {'count': [111780., 111320., 111780., 111320., 111780.,
                                    111320., 111780., 111320., 111780., 111320.,
                                    111780., 111320., 111780., 111320., 111918.,
                                    111562., 112023., 111562., 112023., 111412.,
                                    111780., 111320., 111780., 111320.],
                          'avg_abs_dev': np.zeros(shape=24),
                          'median': np.linspace(0.0, 23.0, 24.0)},
                         'dummy2':
                         {'count': [111780., 111320., 111780., 111320., 111780.,
                                    111320., 111780., 111320., 111780., 111320.,
                                    111780., 111320., 111780., 111320., 111918.,
                                    111562., 112023., 111562., 112023., 111412.,
                                    111780., 111320., 111780., 111320.],
                          'avg_abs_dev': np.zeros(shape=24) + 6.0,
                          'median': [11., 12., 11., 11., 12., 11., 12., 11.,
                                     12., 12., 11., 12., 11., 12., 11., 11.,
                                     12., 11., 12., 11., 11., 11., 11., 12.]}}

    def teardown(self):
        """Runs after every method to clean up previous testing"""
        del self.testInst, self.test_bins, self.test_label, self.test_data
        del self.out_keys, self.out_data

    def test_median1D_default(self):
        """Test success of median1D with default options"""

        med_dict = avg.median1D(self.testInst, self.test_bins, self.test_label,
                                self.test_data)

        # Test output type
        assert isinstance(med_dict, dict)
        assert len(med_dict.keys()) == len(self.test_data)

        # Test output keys
        for kk in med_dict.keys():
            assert kk in self.test_data
            assert np.all([jj in self.out_keys[:-1]
                           for jj in med_dict[kk].keys()])

            # Test output values
            for jj in self.out_keys[:-2]:
                assert len(med_dict[kk][jj]) == self.test_bins[-1]
                assert np.all(med_dict[kk][jj] == self.out_data[kk][jj])

            jj = self.out_keys[-2]
            assert len(med_dict[kk][jj]) == self.test_bins[-1]+1
            assert np.all(med_dict[kk][jj] == np.linspace(self.test_bins[0],
                                                          self.test_bins[1],
                                                          self.test_bins[2]+1))
        del med_dict, kk, jj

    def test_median1D_bad_data(self):
        """Test failure of median1D with string data instead of list"""

        assert_raises(KeyError, avg.median1D, self.testInst, self.test_bins,
                      self.test_label, self.test_data[0])

    def test_median1D_bad_label(self):
        """Test failure of median1D with unknown label"""

        assert_raises(KeyError, avg.median1D, self.testInst, self.test_bins,
                      "bad_label", self.test_data)
