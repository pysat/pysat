import pysat
import pandas as pds
import numpy as np
from nose.tools import assert_raises, raises
import nose.tools
import datetime as dt
import pysat.instruments.icon_ivm as icivm

class TestICONIVMCustom:
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing', tag='12',
                                         clean_level='clean')
        self.testInst.load(2009,1)


    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


    def test_remove_names_tag_level(self):
        self.testInst.tag = 'level_2'
        self.testInst.sat_id = 'a'
        
        self.testInst['ICON_L2_IVM_A_Blurp'] = self.testInst['dummy1']
        icivm.remove_icon_names(self.testInst)
        # check prepended text removed
        assert (len(self.testInst['blurp']) > 0)
        # check other names untouched
        assert (len(self.testInst['dummy1']) > 0)

    def test_remove_names_target(self):
        self.testInst.tag = 'level_2'
        self.testInst.sat_id = 'a'
        
        self.testInst['ICON_L2_IVM_A_Blurp'] = self.testInst['dummy1']
        icivm.remove_icon_names(self.testInst, target='ICON_L2_IVM')
        # check prepended text removed
        assert (len(self.testInst['_a_blurp']) > 0)
        # check other names untouched
        assert (len(self.testInst['dummy1']) > 0)
