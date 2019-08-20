import numpy as np
import sys

from nose.tools import assert_raises, raises
import pandas as pds

import pysat
from pysat import model_utils as mu


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing',
                                         clean_level='clean')
        self.start = pysat.datetime(2009, 1, 1)
        self.stop = pysat.datetime(2009, 1, 1)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.start, self.stop

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_date(self):
        """Try to run without start or stop dates"""
        match = mu.collect_inst_model_pairs(inst=self.testInst)

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_inst(self):
        """Try to run without an instrument"""
        match = mu.collect_inst_model_pairs(start=self.start, stop=self.stop)

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_model(self):
        """Try to run without a model"""
        match = mu.collect_inst_model_pairs(start=self.start, stop=self.stop,
                                            inst=self.testInst)
