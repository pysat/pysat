import datetime as dt
import numpy as np
import os

from nose.tools import assert_raises
from nose.plugins import skip
import pandas as pds

import pysat
from pysat.instruments import sw_kp, sw_f107
from pysat.instruments.methods import sw as sw_meth


class TestSWKp():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument
        self.testInst = pysat.Instrument()
        self.testInst.data = pds.DataFrame({'Kp': np.arange(0, 4, 1.0/3.0),
                                            'ap_nan': np.full(shape=12, \
                                                            fill_value=np.nan),
                                            'ap_inf': np.full(shape=12, \
                                                            fill_value=np.inf)},
                                           index=[pysat.datetime(2009, 1, 1)
                                                  + pds.DateOffset(hours=3*i)
                                                  for i in range(12)])
        self.testInst.meta = pysat.Meta()
        self.testInst.meta.__setitem__('Kp', {self.testInst.meta.fill_label:
                                              np.nan})
        self.testInst.meta.__setitem__('ap_nan', {self.testInst.meta.fill_label:
                                                  np.nan})
        self.testInst.meta.__setitem__('ap_inv', {self.testInst.meta.fill_label:
                                                  np.inf})

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
        fill_label = self.testInst.meta.fill_label
        self.testInst['Kp'][0] = self.testInst.meta['Kp'][fill_label]
        sw_kp.convert_3hr_kp_to_ap(self.testInst)

        # Test non-fill ap values
        assert '3hr_ap' in self.testInst.data.columns
        assert '3hr_ap' in self.testInst.meta.keys()
        assert(self.testInst['3hr_ap'][1:].min() >=
               self.testInst.meta['3hr_ap'][self.testInst.meta.min_label])
        assert(self.testInst['3hr_ap'][1:].max() <=
               self.testInst.meta['3hr_ap'][self.testInst.meta.max_label])

        # Test the fill value in the data and metadata
        assert np.isnan(self.testInst['3hr_ap'][0])
        assert np.isnan(self.testInst.meta['3hr_ap'][fill_label])

        del fill_label

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

    def test_convert_ap_to_kp(self):
        """ Test conversion of ap to Kp"""

        sw_kp.convert_3hr_kp_to_ap(self.testInst)
        kp_out, kp_meta = sw_meth.convert_ap_to_kp(self.testInst['3hr_ap'])

        # Assert original and coverted there and back Kp are equal
        assert all(abs(kp_out - self.testInst.data['Kp']) < 1.0e-4)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert(kp_meta['Kp'][kp_meta.fill_label] == -1)

        del kp_out, kp_meta

    def test_convert_ap_to_kp_middle(self):
        """ Test conversion of ap to Kp where ap is not an exact Kp value"""

        sw_kp.convert_3hr_kp_to_ap(self.testInst)
        self.testInst['3hr_ap'][8] += 1
        kp_out, kp_meta = sw_meth.convert_ap_to_kp(self.testInst['3hr_ap'])

        # Assert original and coverted there and back Kp are equal
        assert all(abs(kp_out - self.testInst.data['Kp']) < 1.0e-4)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert(kp_meta['Kp'][kp_meta.fill_label] == -1)

        del kp_out, kp_meta

    def test_convert_ap_to_kp_nan_input(self):
        """ Test conversion of ap to Kp where ap is NaN"""

        kp_out, kp_meta = sw_meth.convert_ap_to_kp(self.testInst['ap_nan'])

        # Assert original and coverted there and back Kp are equal
        assert all(kp_out == -1)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert(kp_meta['Kp'][kp_meta.fill_label] == -1)

        del kp_out, kp_meta

    def test_convert_ap_to_kp_inf_input(self):
        """ Test conversion of ap to Kp where ap is Inf"""

        kp_out, kp_meta = sw_meth.convert_ap_to_kp(self.testInst['ap_inf'])

        # Assert original and coverted there and back Kp are equal
        assert all(kp_out[1:] == -1)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert(kp_meta['Kp'][kp_meta.fill_label] == -1)

        del kp_out, kp_meta

    def test_convert_ap_to_kp_fill_val(self):
        """ Test conversion of ap to Kp with fill values"""

        # Set the first value to a fill value, then calculate ap
        fill_label = self.testInst.meta.fill_label
        self.testInst['Kp'][0] = self.testInst.meta['Kp'][fill_label]
        sw_kp.convert_3hr_kp_to_ap(self.testInst)
        kp_out, kp_meta = sw_meth.convert_ap_to_kp(self.testInst['3hr_ap'], \
                            fill_val=self.testInst.meta['Kp'][fill_label])

        # Test non-fill ap values
        assert all(abs(kp_out[1:] - self.testInst.data['Kp'][1:]) < 1.0e-4)

        # Test the fill value in the data and metadata
        assert np.isnan(kp_out[0])
        assert np.isnan(kp_meta['Kp'][fill_label])

        del fill_label, kp_out, kp_meta


class TestSwKpCombine():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Switch to test_data directory
        self.saved_path = pysat.data_dir
        pysat.utils.set_data_dir(pysat.test_data_path, store=False)

        # Set combination testing input
        self.test_day = pysat.datetime(2019, 3, 18)
        self.combine = {"standard_inst": pysat.Instrument("sw", "kp", ""),
                        "recent_inst": pysat.Instrument("sw", "kp", "recent"),
                        "forecast_inst":
                        pysat.Instrument("sw", "kp", "forecast"),
                        "start": self.test_day - dt.timedelta(days=30),
                        "stop": self.test_day + dt.timedelta(days=3),
                        "fill_val": -1}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.utils.set_data_dir(self.saved_path)
        del self.combine, self.test_day, self.saved_path

    def test_combine_kp_none(self):
        """ Test combine_kp failure when no input is provided"""

        assert_raises(ValueError, sw_meth.combine_kp)

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
        assert_raises(ValueError, sw_meth.combine_kp, combo_in)

        del combo_in, testInst

    def test_combine_kp_no_time(self):
        """Test combine_kp failure when no times are provided"""

        combo_in = {kk: self.combine[kk] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}

        assert_raises(ValueError, sw_meth.combine_kp, combo_in)

        del combo_in

    def test_combine_kp_no_data(self):
        """Test combine_kp when no data is present for specified times"""

        combo_in = {kk: self.combine['forecast_inst'] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}
        combo_in['start'] = pysat.datetime(2014, 2, 19)
        combo_in['stop'] = pysat.datetime(2014, 2, 24)
        kp_inst = sw_meth.combine_kp(**combo_in)

        assert kp_inst.data.isnull().all()["Kp"]

        del combo_in, kp_inst

    def test_combine_kp_inst_time(self):
        """Test combine_kp when times are provided through the instruments"""

        combo_in = {kk: self.combine[kk] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}

        combo_in['standard_inst'].load(date=self.combine['start'])
        combo_in['recent_inst'].load(date=self.test_day)
        combo_in['forecast_inst'].load(date=self.test_day)
        combo_in['stop'] = combo_in['forecast_inst'].index[-1]

        kp_inst = sw_meth.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        # kp_inst contains times up to 21:00:00, coombine['stop'] is midnight
        assert kp_inst.index[-1].date() <= self.combine['stop'].date()
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'

        assert np.isnan(kp_inst.meta['Kp'][kp_inst.meta.fill_label])
        assert len(kp_inst['Kp'][np.isnan(kp_inst['Kp'])]) == 0

        del combo_in, kp_inst

    def test_combine_kp_all(self):
        """Test combine_kp when all input is provided"""

        kp_inst = sw_meth.combine_kp(**self.combine)

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

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'forecast_inst'}
        kp_inst = sw_meth.combine_kp(**combo_in)

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

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'recent_inst'}
        kp_inst = sw_meth.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert (kp_inst.meta['Kp'][kp_inst.meta.fill_label] ==
                self.combine['fill_val'])
        assert len(kp_inst['Kp'][kp_inst['Kp']]
                   == self.combine['fill_val']) > 0

        del kp_inst, combo_in

    def test_combine_kp_no_standard(self):
        """Test combine_kp when standard data is not provided"""

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'standard_inst'}
        kp_inst = sw_meth.combine_kp(**combo_in)

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
        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200,
                                                                3840)},
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
        # Switch to test_data directory
        self.saved_path = pysat.data_dir
        pysat.utils.set_data_dir(pysat.test_data_path, store=False)

        # Set combination testing input
        self.test_day = pysat.datetime(2019, 3, 16)
        self.combineInst = {tag: pysat.Instrument("sw", "f107", tag)
                            for tag in sw_f107.tags.keys()}
        self.combineTimes = {"start": self.test_day - dt.timedelta(days=30),
                             "stop": self.test_day + dt.timedelta(days=3)}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.utils.set_data_dir(self.saved_path)
        del self.combineInst, self.test_day, self.combineTimes

    def test_combine_f107_none(self):
        """ Test combine_f107 failure when no input is provided"""

        assert_raises(TypeError, sw_meth.combine_f107)

    def test_combine_f107_no_time(self):
        """Test combine_f107 failure when no times are provided"""

        assert_raises(ValueError, sw_meth.combine_f107,
                      self.combineInst[''], self.combineInst['forecast'])

    def test_combine_f107_no_data(self):
        """Test combine_f107 when no data is present for specified times"""

        combo_in = {kk: self.combineInst['forecast'] for kk in
                    ['standard_inst', 'forecast_inst']}
        combo_in['start'] = pysat.datetime(2014, 2, 19)
        combo_in['stop'] = pysat.datetime(2014, 2, 24)
        f107_inst = sw_meth.combine_f107(**combo_in)

        assert f107_inst.data.isnull().all()["f107"]

        del combo_in, f107_inst

    def test_combine_f107_inst_time(self):
        """Test combine_f107 with times provided through datasets"""

        self.combineInst['all'].load(date=self.combineTimes['start'])
        self.combineInst['forecast'].load(date=self.test_day)

        f107_inst = sw_meth.combine_f107(self.combineInst['all'],
                                         self.combineInst['forecast'])

        assert f107_inst.index[0] == dt.datetime(1947, 2, 13)
        assert f107_inst.index[-1] <= self.combineTimes['stop']
        assert len(f107_inst.data.columns) == 1
        assert f107_inst.data.columns[0] == 'f107'

        del f107_inst

    def test_combine_f107_all(self):
        """Test combine_f107 when all input is provided with '' and '45day'"""

        f107_inst = sw_meth.combine_f107(self.combineInst[''],
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

        sw_meth.calc_daily_Ap(self.testInst)

        assert 'Ap' in self.testInst.data.columns
        assert 'Ap' in self.testInst.meta.keys()

        # Test unfilled values (full days)
        assert np.all(self.testInst['Ap'][:8].min() == 4.5)

        # Test fill values (partial days)
        assert np.all(np.isnan(self.testInst['Ap'][8:]))

    def test_calc_daily_Ap_bad_3hr(self):
        """ Test daily Ap calculation with bad input key"""

        assert_raises(ValueError, sw_meth.calc_daily_Ap, self.testInst,
                      "no")

    def test_calc_daily_Ap_bad_daily(self):
        """ Test daily Ap calculation with bad output key"""

        assert_raises(ValueError, sw_meth.calc_daily_Ap, self.testInst,
                      "3hr_ap", "3hr_ap")
