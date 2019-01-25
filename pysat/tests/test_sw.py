import pysat
from pysat.instruments import sw_kp, sw_f107, sw_methods
import pandas as pds
import numpy as np
from nose.tools import assert_raises, raises
import nose.tools
from nose.plugins import skip
import datetime as dt

class TestSWKp():
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

        # Set combination testing input
        self.today = dt.datetime.today().date()
        self.combine = {"standard_inst": pysat.Instrument("sw", "kp", ""),
                        "recent_inst": pysat.Instrument("sw", "kp", "recent"),
                        "forecast_inst":
                        pysat.Instrument("sw", "kp", "forecast"),
                        "start": self.today - dt.timedelta(days=30),
                        "stop": self.today + dt.timedelta(days=3),
                        "fill_val": -1}

        # Download combination testing input
        self.downloaded = True
        # Load the instrument objects
        for kk in ['standard_inst', 'recent_inst', 'forecast_inst']:
            self.combine[kk].download(start=self.combine['start'],
                                      stop=self.combine['stop'])
            if len(self.combine[kk].files.files) == 0:
                self.download = False

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.testMeta, self.combine, self.download
        del self.today

    def test_initialize_kp_metadata(self):
        """Test default Kp metadata initialization"""
        sw_kp.initialize_kp_metadata(self.testInst.meta, 'Kp')

        assert self.testInst.meta['Kp'][self.testInst.meta.units_label] == ''
        assert self.testInst.meta['Kp'][self.testInst.meta.name_label] == 'Kp'
        assert self.testInst.meta['Kp'][self.testInst.meta.desc_label] == 'Kp'
        assert self.testInst.meta['Kp'][self.testInst.meta.plot_label] == 'Kp'
        assert self.testInst.meta['Kp'][self.testInst.meta.axis_label] == 'Kp'
        assert(self.testInst.meta['Kp'][self.testInst.meta.scale_label] ==
               'linear')
        assert self.testInst.meta['Kp'][self.testInst.meta.min_label] == 0
        assert self.testInst.meta['Kp'][self.testInst.meta.max_label] == 9
        assert self.testInst.meta['Kp'][self.testInst.meta.fill_label] == -1

    def test_uninit_kp_metadata(self):
        """Test Kp metadata initialization with uninitialized Metadata"""
        sw_kp.initialize_kp_metadata(self.testMeta, 'Kp')

        assert self.testMeta['Kp'][self.testMeta.units_label] == ''
        assert self.testMeta['Kp'][self.testMeta.name_label] == 'Kp'
        assert self.testMeta['Kp'][self.testMeta.desc_label] == 'Kp'
        assert self.testMeta['Kp'][self.testMeta.plot_label] == 'Kp'
        assert self.testMeta['Kp'][self.testMeta.axis_label] == 'Kp'
        assert self.testMeta['Kp'][self.testMeta.scale_label] == 'linear'
        assert self.testMeta['Kp'][self.testMeta.min_label] == 0
        assert self.testMeta['Kp'][self.testMeta.max_label] == 9
        assert self.testMeta['Kp'][self.testMeta.fill_label] == -1

    def test_fill_kp_metadata(self):
        """Test Kp metadata initialization with user-specified fill value"""
        sw_kp.initialize_kp_metadata(self.testInst.meta, 'Kp', fill_val=666)

        assert self.testInst.meta['Kp'][self.testInst.meta.fill_label] == 666

    def test_long_name_kp_metadata(self):
        """Test Kp metadata initialization with a long name"""
        sw_kp.initialize_kp_metadata(self.testInst.meta, 'high_lat_Kp')

        assert(self.testInst.meta['Kp'][self.testInst.meta.name_label] ==
               'high_lat_Kp')
        assert(self.testInst.meta['Kp'][self.testInst.meta.desc_label] ==
               'high lat Kp')
        assert(self.testInst.meta['Kp'][self.testInst.meta.plot_label] ==
               'High lat Kp')
        assert(self.testInst.meta['Kp'][self.testInst.meta.axis_label] ==
               'High lat Kp')

    def test_combine_kp_none(self):
        """ Test combine_kp failure when no input is provided"""
        
        assert_raises(ValueError, sw_methods.combine_kp)

    def test_combine_kp_one(self):
        """ Test combine_kp failure when only one instrument is provided"""

        combo_in = {"standard_inst": self.testInst}
        assert_raises(ValueError, sw_methods.combine_kp, **combo_in)

        del combo_in

    def test_combine_kp_no_time(self):
        """Test combine_kp failure when no times are provided"""

        combo_in = {kk: self.combine[kk] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}

        assert_raises(ValueError, sw_methods.combine_kp, **combo_in)

        del combo_in

    def test_combine_kp_inst_time(self):
        """Test combine_kp when times are provided through the instruments"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        combo_in = {kk: self.combine[kk] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}

        combo_in['standard_inst'].load(date=self.combine['start'])
        combo_in['recent_inst'].load(date=self.today)
        combo_in['forecast_inst'].load(date=self.today)

        kp_inst = sw_methods.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert(kp_inst.meta['Kp'][kp_inst.meta.fill_label] ==
               self.combine['fill_val'])
        assert len(kp_inst['Kp'][kp_inst['Kp']] ==
                   self.combine['fill_val']) == 0

        del combo_in, kp_inst

    def test_combine_kp_all(self):
        """Test combine_kp when all input is provided"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        kp_inst = sw_methods.combine_kp(**self.combine)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert(kp_inst.meta['Kp'][kp_inst.meta.fill_label] ==
               self.combine['fill_val'])
        assert len(kp_inst['Kp'][kp_inst['Kp']] ==
                   self.combine['fill_val']) == 0

        del kp_inst

    def test_combine_kp_no_forecast(self):
        """Test combine_kp when forecasted data is not provided"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        combo_in = {kk: self.combine for kk in self.combine.keys()
                    if kk != 'forecast_inst'}
        kp_inst = sw_methods.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['recent_inst'].index[-1]
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert(kp_inst.meta['Kp'][kp_inst.meta.fill_label] ==
               self.combine['fill_val'])
        assert len(kp_inst['Kp'][kp_inst['Kp']]
                   == self.combine['fill_val']) > 0

        del kp_inst, combo_in

    def test_combine_kp_no_recent(self):
        """Test combine_kp when recent data is not provided"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        combo_in = {kk: self.combine for kk in self.combine.keys()
                    if kk != 'recent_inst'}
        kp_inst = sw_methods.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert(kp_inst.meta['Kp'][kp_inst.meta.fill_label] ==
               self.combine['fill_val'])
        assert len(kp_inst['Kp'][kp_inst['Kp']]
                   == self.combine['fill_val']) > 0

        del kp_inst, combo_in

    def test_combine_kp_no_standard(self):
        """Test combine_kp when standard data is not provided"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        combo_in = {kk: self.combine for kk in self.combine.keys()
                    if kk != 'standard_inst'}
        kp_inst = sw_methods.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['recent_inst'].index[0]
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert(kp_inst.meta['Kp'][kp_inst.meta.fill_label] ==
               self.combine['fill_val'])
        assert len(kp_inst['Kp'][kp_inst['Kp']]
                   == self.combine['fill_val']) > 0

        del kp_inst, combo_in

class TestSWF107():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing', tag='12',
                                         clean_level='clean')
        self.testInst.load(2009,1)

        # Add Kp data
        self.testInst['f107'] = pds.Series(np.arange(72, 84, 1.0),
                                           index=self.testInst.data.index)

        # Load a test Metadata
        self.testMeta = pysat.Meta()

        # Set combination testing input
        self.today = dt.datetime.today().date()
        self.combineInst = {tag: pysat.Instrument("sw", "f107", tag)
                            for tag in sw_f107.tags.keys()}
        self.combineTimes = {"start": self.today - dt.timedelta(days=30),
                             "stop": self.today + dt.timedelta(days=3)}

        # Download combination testing input
        self.downloaded = True
        # Load the instrument objects
        for kk in self.combineInst.keys():
            self.combineInst[kk].download(**self.combineTimes)
            if len(self.combine[kk].files.files) == 0:
                self.download = False

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.testMeta, self.combineInst, self.download
        del self.today, self.combineTimes

    def test_combine_f107_none(self):
        """ Test combine_f107 failure when no input is provided"""
        
        assert_raises(TypeError, sw_methods.combine_f107)

    def test_combine_f107_no_time(self):
        """Test combine_f107 failure when no times are provided"""

        assert_raises(ValueError, sw_methods.combine_f107, self.combineInst[''],
                      self.combineInst['forecast'])

    def test_combine_f107_inst_time(self):
        """Test combine_f107 with times provided through 'all' and 'forecast'"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        self.combineInst['all'].load(date=self.combineTimes['start'])
        self.combineInst['forecast'].load(date=self.today)

        f107_inst = sw_methods.combine_f107(self.combineInst['all'],
                                            self.combineInst['forecast'])

        assert f107_inst.index[0] >= self.combineTimes['start']
        assert f107_inst.index[-1] < self.combineTimes['stop']
        assert len(f107_inst.data.columns) == 1
        assert f107_inst.data.columns[0] == 'f107'

        del f107_inst

    def test_combine_f107_all(self):
        """Test combine_f107 when all input is provided with '' and '45day'"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        f107_inst = sw_methods.combine_f107(self.combineInst[''],
                                            self.combineInst['45day'],
                                            **self.combineTimes)

        assert f107_inst.index[0] >= self.combineTimes['start']
        assert f107_inst.index[-1] < self.combineTimes['stop']
        assert len(f107_inst.data.columns) == 1
        assert f107_inst.data.columns[0] == 'f107'

        del f107_inst
