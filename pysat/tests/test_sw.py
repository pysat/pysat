import datetime as dt
import numpy as np
import os

from nose.tools import assert_raises
from nose.plugins import skip
import pandas as pds
import tempfile

import pysat
from pysat.instruments import sw_kp, sw_f107, sw_methods


def remove_files(inst):
    # remove any files downloaded as part of the unit tests
    temp_dir = inst.files.data_path
    for the_file in list(inst.files.files.values):
        if the_file.rfind('_') > the_file.rfind('.'):
            the_file = the_file[:the_file.rfind('_')]
        file_path = os.path.join(temp_dir, the_file)
        if os.path.isfile(file_path):
            os.unlink(file_path)


class TestSWKp():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument
        self.testInst = pysat.Instrument()
        self.testInst.data = pds.DataFrame({'Kp': np.arange(0, 4, 1.0/3.0)},
                                           index=[pysat.datetime(2009, 1, 1)
                                                  + pds.DateOffset(hours=3*i)
                                                  for i in range(12)])
        self.testInst.meta = pysat.Meta()
        self.testInst.meta.__setitem__('Kp', {self.testInst.meta.fill_label:
                                              np.nan})

        # Load a test Metadata
        self.testMeta = pysat.Meta()

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.testMeta

    def test_convert_kp_to_ap(self):
        """ Test conversion of Kp to ap"""

        sw_kp.convert_3hr_kp_to_ap(self.testInst)

        assert '3hr_ap' in self.testInst.data.columns
        assert '3hr_ap' in self.testInst.meta.keys()
        assert(self.testInst['3hr_ap'].min() >=
               self.testInst.meta['3hr_ap'][self.testInst.meta.min_label])
        assert(self.testInst['3hr_ap'].max() <=
               self.testInst.meta['3hr_ap'][self.testInst.meta.max_label])

    def test_convert_kp_to_ap_fill_val(self):
        """ Test conversion of Kp to ap with fill values"""

        # Set the first value to a fill value, then calculate ap
        self.testInst['Kp'][0] = \
            self.testInst.meta['Kp'][self.testInst.meta.fill_label]
        sw_kp.convert_3hr_kp_to_ap(self.testInst)

        # Test non-fill ap values
        assert '3hr_ap' in self.testInst.data.columns
        assert '3hr_ap' in self.testInst.meta.keys()
        assert(self.testInst['3hr_ap'][1:].min() >=
               self.testInst.meta['3hr_ap'][self.testInst.meta.min_label])
        assert(self.testInst['3hr_ap'][1:].max() <=
               self.testInst.meta['3hr_ap'][self.testInst.meta.max_label])

        # Test the fill value in the data and metadata
        if np.isnan(self.testInst['Kp'][0]):
            assert np.isnan(self.testInst['3hr_ap'][0])
            assert np.isnan( \
                self.testInst.meta['3hr_ap'][self.testInst.meta.fill_label])
        else:
            assert self.testInst['Kp'][0] == self.testInst['3hr_ap'][0]
            assert(self.testInst.meta['3hr_ap'][self.testInst.meta.fill_label]
                   == self.testInst.meta['Kp'][self.testInst.meta.fill_label])

    def test_convert_kp_to_ap_bad_input(self):
        """ Test conversion of Kp to ap with bad input"""

        self.testInst.data.rename(columns={"Kp": "bad"}, inplace=True)

        assert_raises(ValueError, sw_kp.convert_3hr_kp_to_ap, self.testInst)

    def test_initialize_kp_metadata(self):
        """Test default Kp metadata initialization"""
        sw_kp.initialize_kp_metadata(self.testInst.meta, 'Kp')

        assert self.testInst.meta['Kp'][self.testInst.meta.units_label] == ''
        assert self.testInst.meta['Kp'][self.testInst.meta.name_label] == 'Kp'
        assert(self.testInst.meta['Kp'][self.testInst.meta.desc_label] ==
               'Planetary K-index')
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
        assert(self.testMeta['Kp'][self.testMeta.desc_label] ==
               'Planetary K-index')
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
        dkey = 'high_lat_Kp'
        sw_kp.initialize_kp_metadata(self.testInst.meta, dkey)

        assert self.testInst.meta[dkey][self.testInst.meta.name_label] == dkey
        assert(self.testInst.meta[dkey][self.testInst.meta.desc_label] ==
               'Planetary K-index')
        assert(self.testInst.meta[dkey][self.testInst.meta.plot_label] ==
               'High lat Kp')
        assert(self.testInst.meta[dkey][self.testInst.meta.axis_label] ==
               'High lat Kp')
        del dkey


class TestSwKpCombine():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # create temporary directory
        dir_name = tempfile.mkdtemp()
        self.saved_path = pysat.data_dir
        pysat.utils.set_data_dir(dir_name, store=False)

        # Set combination testing input
        self.today = dt.datetime.today().replace(hour=0, minute=0, second=0,
                                                 microsecond=0)
        self.combine = {"standard_inst": pysat.Instrument("sw", "kp", ""),
                        "recent_inst": pysat.Instrument("sw", "kp", "recent"),
                        "forecast_inst":
                        pysat.Instrument("sw", "kp", "forecast"),
                        "start": self.today - dt.timedelta(days=30),
                        "stop": self.today + dt.timedelta(days=3),
                        "fill_val": -1}

        # Download combination testing input
        self.download = True
        # Load the instrument objects
        for kk in ['standard_inst', 'recent_inst', 'forecast_inst']:
            try:
                self.combine[kk].download(start=self.combine['start'],
                                          stop=self.combine['stop'])
            except:
                self.download = False
                pass

            if len(self.combine[kk].files.files) == 0:
                self.download = False

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        for kk in ['standard_inst', 'recent_inst', 'forecast_inst']:
            remove_files(self.combine[kk])
        pysat.utils.set_data_dir(self.saved_path)
        del self.combine, self.download, self.today, self.saved_path

    def test_combine_kp_none(self):
        """ Test combine_kp failure when no input is provided"""

        assert_raises(ValueError, sw_methods.combine_kp)

    def test_combine_kp_one(self):
        """ Test combine_kp failure when only one instrument is provided"""

        # Load a test instrument
        testInst = pysat.Instrument()
        testInst.data = pds.DataFrame({'Kp': np.arange(0, 4, 1.0/3.0)},
                                      index=[pysat.datetime(2009, 1, 1)
                                             + pds.DateOffset(hours=3*i)
                                             for i in range(12)])
        testInst.meta = pysat.Meta()
        testInst.meta['Kp'] = {testInst.meta.fill_label: np.nan}

        combo_in = {"standard_inst": testInst}
        assert_raises(ValueError, sw_methods.combine_kp, combo_in)

        del combo_in, testInst

    def test_combine_kp_no_time(self):
        """Test combine_kp failure when no times are provided"""

        combo_in = {kk: self.combine[kk] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}

        assert_raises(ValueError, sw_methods.combine_kp, combo_in)

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
        combo_in['stop'] = combo_in['forecast_inst'].index[-1]

        kp_inst = sw_methods.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] <= self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'

        fill_val = combo_in['standard_inst'].meta['Kp'][kp_inst.meta.fill_label]

        if np.isnan(fill_val):
            assert np.isnan(kp_inst.meta['Kp'][kp_inst.meta.fill_label])
            assert len(kp_inst['Kp'][np.isnan(kp_inst['Kp'])]) == 0
        else:
            assert kp_inst.meta['Kp'][kp_inst.meta.fill_label] == fill_val
            assert len(kp_inst['Kp'][kp_inst['Kp'] == fill_val]) == 0

        del combo_in, kp_inst, fill_val

    def test_combine_kp_all(self):
        """Test combine_kp when all input is provided"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        kp_inst = sw_methods.combine_kp(**self.combine)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'

        # Fill value is defined by combine
        assert(kp_inst.meta['Kp'][kp_inst.meta.fill_label] ==
               self.combine['fill_val'])
        assert (kp_inst['Kp'] != self.combine['fill_val']).all()

        del kp_inst

    def test_combine_kp_no_forecast(self):
        """Test combine_kp when forecasted data is not provided"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'forecast_inst'}
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

    def test_combine_kp_no_recent(self):
        """Test combine_kp when recent data is not provided"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
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

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'standard_inst'}
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


class TestSWF107():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument
        self.testInst = pysat.Instrument()
        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200, 160)},
                                           index=[pysat.datetime(2009, 1, 1)
                                                  + pds.DateOffset(days=i)
                                                  for i in range(160)])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_calc_f107a_bad_inname(self):
        """ Test the calc_f107a with a bad input name """

        assert_raises(ValueError, sw_f107.calc_f107a, self.testInst, 'bad')

    def test_calc_f107a_bad_outname(self):
        """ Test the calc_f107a with a bad output name """

        assert_raises(ValueError, sw_f107.calc_f107a, self.testInst, 'f107',
                      'f107')

    def test_calc_f107a_daily(self):
        """ Test the calc_f107a routine with daily data"""

        sw_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the values are finite and realistic means
        assert np.all(np.isfinite(self.testInst['f107a']))
        assert self.testInst['f107a'].min() > self.testInst['f107'].min()
        assert self.testInst['f107a'].max() < self.testInst['f107'].max()

    def test_calc_f107a_high_rate(self):
        """ Test the calc_f107a routine with sub-daily data"""
        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200, 3840)},
                                           index=[pysat.datetime(2009, 1, 1)
                                                  + pds.DateOffset(hours=i)
                                                  for i in range(3840)])
        sw_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the values are finite and realistic means
        assert np.all(np.isfinite(self.testInst['f107a']))
        assert self.testInst['f107a'].min() > self.testInst['f107'].min()
        assert self.testInst['f107a'].max() < self.testInst['f107'].max()

        # Assert the same mean value is used for a day
        assert len(np.unique(self.testInst['f107a'][:24])) == 1

    def test_calc_f107a_daily_missing(self):
        """ Test the calc_f107a routine with some daily data missing"""

        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200, 160)},
                                           index=[pysat.datetime(2009, 1, 1)
                                                  + pds.DateOffset(days=2*i+1)
                                                  for i in range(160)])
        sw_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the finite values have realistic means
        assert(np.nanmin(self.testInst['f107a'])
               > np.nanmin(self.testInst['f107']))
        assert(np.nanmax(self.testInst['f107a'])
               < np.nanmax(self.testInst['f107']))

        # Assert the expected number of fill values
        assert(len(self.testInst['f107a'][np.isnan(self.testInst['f107a'])])
               == 40)


class TestSWF107Combine():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # create temporary directory
        dir_name = tempfile.mkdtemp()
        self.saved_path = pysat.data_dir
        pysat.utils.set_data_dir(dir_name, store=False)

        # Set combination testing input
        self.today = dt.datetime.today().replace(hour=0, minute=0, second=0,
                                                 microsecond=0)
        self.combineInst = {tag: pysat.Instrument("sw", "f107", tag)
                            for tag in sw_f107.tags.keys()}
        self.combineTimes = {"start": self.today - dt.timedelta(days=30),
                             "stop": self.today + dt.timedelta(days=3)}

        # Download combination testing input
        self.download = True
        # Load the instrument objects
        for kk in self.combineInst.keys():
            try:
                if kk == '':
                    self.combineInst[kk].download(self.combineTimes['start'],
                                                  freq='MS')
                else:
                    self.combineInst[kk].download(**self.combineTimes)
            except:
                pass

            if len(self.combineInst[kk].files.files) == 0:
                self.download = False

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        for kk in self.combineInst.keys():
            remove_files(self.combineInst[kk])
        pysat.utils.set_data_dir(self.saved_path)
        del self.combineInst, self.download, self.today, self.combineTimes

    def test_combine_f107_none(self):
        """ Test combine_f107 failure when no input is provided"""

        assert_raises(TypeError, sw_methods.combine_f107)

    def test_combine_f107_no_time(self):
        """Test combine_f107 failure when no times are provided"""

        assert_raises(ValueError, sw_methods.combine_f107,
                      self.combineInst[''], self.combineInst['forecast'])

    def test_combine_f107_inst_time(self):
        """Test combine_f107 with times provided through 'all' and 'forecast'"""

        if not self.download:
            raise skip.SkipTest("test needs downloaded data")

        self.combineInst['all'].load(date=self.combineTimes['start'])
        self.combineInst['forecast'].load(date=self.today)

        f107_inst = sw_methods.combine_f107(self.combineInst['all'],
                                            self.combineInst['forecast'])

        assert f107_inst.index[0] == dt.datetime(1947, 2, 13)
        assert f107_inst.index[-1] <= self.combineTimes['stop']
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


class TestSWAp():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument with 3hr ap data
        self.testInst = pysat.Instrument()
        self.testInst.data = pds.DataFrame({'3hr_ap': [0, 2, 3, 4, 5, 6, 7, 9,
                                                       12, 15]},
                                           index=[pysat.datetime(2009, 1, 1)
                                                  + pds.DateOffset(hours=3*i)
                                                  for i in range(10)])
        self.testInst.meta = pysat.Meta()
        self.meta_dict = {self.testInst.meta.units_label: '',
                          self.testInst.meta.name_label: 'ap',
                          self.testInst.meta.desc_label:
                          "3-hour ap (equivalent range) index",
                          self.testInst.meta.plot_label: "ap",
                          self.testInst.meta.axis_label: "ap",
                          self.testInst.meta.scale_label: 'linear',
                          self.testInst.meta.min_label: 0,
                          self.testInst.meta.max_label: 400,
                          self.testInst.meta.fill_label: np.nan,
                          self.testInst.meta.notes_label: 'test ap'}
        self.testInst.meta.__setitem__('3hr_ap', self.meta_dict)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.meta_dict

    def test_calc_daily_Ap(self):
        """ Test daily Ap calculation"""

        sw_methods.calc_daily_Ap(self.testInst)

        assert 'Ap' in self.testInst.data.columns
        assert 'Ap' in self.testInst.meta.keys()

        # Test unfilled values (full days)
        assert np.all(self.testInst['Ap'][:8].min() == 4.5)

        # Test fill values (partial days)
        assert np.all(np.isnan(self.testInst['Ap'][8:]))

    def test_calc_daily_Ap_bad_3hr(self):
        """ Test daily Ap calculation with bad input key"""

        assert_raises(ValueError, sw_methods.calc_daily_Ap, self.testInst,
                      "no")

    def test_calc_daily_Ap_bad_daily(self):
        """ Test daily Ap calculation with bad output key"""

        assert_raises(ValueError, sw_methods.calc_daily_Ap, self.testInst,
                      "3hr_ap", "3hr_ap")
