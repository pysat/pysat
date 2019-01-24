import pysat
import pysat.instruments.sw_kp as pysat_kp
import pandas as pds
import numpy as np
from nose.tools import assert_raises, raises
import nose.tools
import datetime as dt

class TestSWKpCustom():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing', tag='12',
                                         clean_level='clean')
        self.testInst.load(2009,1)

        # Add Kp data
        self.testInst['Kp'] = pds.Series(np.arange(0, 4, 1.0/3.0),
                                         index=self.testInst.data.index)

        # Load a test Metadata
        self.testMeta = pysat.Meta()

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.testMeta

    def test_initialize_kp_metadata(self):
        """Test default Kp metadata initialization"""
        pysat_kp.initialize_kp_metadata(testInst.meta, 'Kp')

        assert testInst.meta['Kp'][meta.units_label] == ''
        assert testInst.meta['Kp'][meta.name_label] == 'Kp'
        assert testInst.meta['Kp'][meta.desc_label] == 'Kp'
        assert testInst.meta['Kp'][meta.plot_label] == 'Kp'
        assert testInst.meta['Kp'][meta.axis_label] == 'Kp'
        assert testInst.meta['Kp'][meta.scale_label] == 'linear'
        assert testInst.meta['Kp'][meta.min_label] == 0
        assert testInst.meta['Kp'][meta.max_label] == 9
        assert testInst.meta['Kp'][meta.fill_label] == -1

    def test_uninit_kp_metadata(self):
        """Test Kp metadata initialization with uninitialized Metadata"""
        pysat_kp.initialize_kp_metadata(self.testMeta, 'Kp')

        assert self.testMeta['Kp'][meta.units_label] == ''
        assert self.testMeta['Kp'][meta.name_label] == 'Kp'
        assert self.testMeta['Kp'][meta.desc_label] == 'Kp'
        assert self.testMeta['Kp'][meta.plot_label] == 'Kp'
        assert self.testMeta['Kp'][meta.axis_label] == 'Kp'
        assert self.testMeta['Kp'][meta.scale_label] == 'linear'
        assert self.testMeta['Kp'][meta.min_label] == 0
        assert self.testMeta['Kp'][meta.max_label] == 9
        assert self.testMeta['Kp'][meta.fill_label] == -1

    def test_fill_kp_metadata(self):
        """Test Kp metadata initialization with user-specified fill value"""
        pysat_kp.initialize_kp_metadata(testInst.meta, 'Kp', fill_val=666)

        assert testInst.meta['Kp'][meta.fill_label] == 666

    def test_long_name_kp_metadata(self):
        """Test Kp metadata initialization with a long name"""
        pysat_kp.initialize_kp_metadata(testInst.meta, 'high_lat_Kp')

        assert testInst.meta['Kp'][meta.name_label] == 'high_lat_Kp'
        assert testInst.meta['Kp'][meta.desc_label] == 'high lat Kp'
        assert testInst.meta['Kp'][meta.plot_label] == 'High lat Kp'
        assert testInst.meta['Kp'][meta.axis_label] == 'High lat Kp'
