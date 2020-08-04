# -*- coding: utf-8 -*-
# Test some of the basic _core functions
import datetime as dt
from importlib import reload as re_load
import logging
import numpy as np

import pandas as pds
import pytest

import pysat
import pysat.instruments.pysat_testing
import pysat.instruments.pysat_testing_xarray
import pysat.instruments.pysat_testing2d

xarray_epoch_name = 'time'


# ------------------------------------------------------------------------------
#
# Test Instrument object basics
#
# ------------------------------------------------------------------------------
class TestBasics():
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         sat_id='10',
                                         clean_level='clean',
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    # --------------------------------------------------------------------------
    #
    # Test basic loads, by date, filename, file id, as well as prev/next
    #
    # --------------------------------------------------------------------------
    def test_basic_instrument_load(self):
        """Test if the correct day is being loaded (checking object date and
        data)."""
        self.testInst.load(2009, 1)
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2009, 1, 1))
        assert (test_date == self.testInst.date)

    def test_basic_instrument_bad_keyword(self):
        """Checks for error when instantiating with bad load_rtn keywords"""
        with pytest.raises(ValueError):
            pysat.Instrument(platform=self.testInst.platform,
                             name=self.testInst.name, sat_id='10',
                             clean_level='clean',
                             unsupported_keyword_yeah=True)

    def test_basic_instrument_load_yr_no_doy(self):
        with pytest.raises(TypeError):
            self.testInst.load(2009)

    def test_basic_instrument_load_no_input(self):
        with pytest.raises(TypeError):
            self.testInst.load()

    def test_basic_instrument_load_by_file_and_multifile(self):
        testInst = pysat.Instrument(platform=self.testInst.platform,
                                    name=self.testInst.name,
                                    sat_id='10',
                                    clean_level='clean',
                                    update_files=True,
                                    multi_file_day=True)
        with pytest.raises(ValueError):
            testInst.load(fname=testInst.files[0])

    def test_basic_instrument_load_by_date(self):
        date = dt.datetime(2009, 1, 1)
        self.testInst.load(date=date)
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2009, 1, 1))
        assert (test_date == self.testInst.date)

    def test_basic_instrument_load_by_date_with_extra_time(self):
        # put in a date that has more than year, month, day
        date = dt.datetime(2009, 1, 1, 1, 1, 1)
        self.testInst.load(date=date)
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2009, 1, 1))
        assert (test_date == self.testInst.date)

    def test_basic_instrument_load_data(self):
        """Test if the correct day is being loaded (checking data down to the
        second)."""
        self.testInst.load(2009, 1)
        assert self.testInst.index[0] == dt.datetime(2009, 1, 1, 0, 0, 0)

    def test_basic_instrument_load_leap_year(self):
        """Test if the correct day is being loaded (Leap-Year)."""
        self.testInst.load(2008, 366)
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2008, 12, 31))
        assert (test_date == self.testInst.date)

    def test_next_load_default(self):
        """Test if first day is loaded by default when first invoking .next."""
        self.testInst.next()
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert test_date == dt.datetime(2008, 1, 1)

    def test_prev_load_default(self):
        """Test if last day is loaded by default when first invoking .prev."""
        self.testInst.prev()
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert test_date == dt.datetime(2010, 12, 31)

    def test_basic_fid_instrument_load(self):
        """Test if first day is loaded by default when first invoking .next."""
        self.testInst.load(fid=0)
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2008, 1, 1))
        assert (test_date == self.testInst.date)

    def test_next_fid_load_default(self):
        """Test next day is being loaded (checking object date)."""
        self.testInst.load(fid=0)
        self.testInst.next()
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2008, 1, 2))
        assert (test_date == self.testInst.date)

    def test_prev_fid_load_default(self):
        """Test prev day is loaded when invoking .prev."""
        self.testInst.load(fid=3)
        self.testInst.prev()
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2008, 1, 3))
        assert (test_date == self.testInst.date)

    def test_filename_load(self):
        """Test if file is loadable by filename, relative to
        top_data_dir/platform/name/tag"""
        self.testInst.load(fname='2010-12-31.nofile')
        assert self.testInst.index[0] == dt.datetime(2010, 12, 31)

    def test_next_filename_load_default(self):
        """Test next day is being loaded (checking object date)."""
        self.testInst.load(fname='2010-12-30.nofile')
        self.testInst.next()
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2010, 12, 31))
        assert (test_date == self.testInst.date)

    def test_prev_filename_load_default(self):
        """Test prev day is loaded when invoking .prev."""
        self.testInst.load(fname='2009-01-04.nofile')
        self.testInst.prev()
        test_date = self.testInst.index[0]
        test_date = dt.datetime(test_date.year, test_date.month,
                                test_date.day)
        assert (test_date == dt.datetime(2009, 1, 3))
        assert (test_date == self.testInst.date)

    def test_list_files(self):
        files = self.testInst.files.files
        assert isinstance(files, pds.Series)

    def test_remote_file_list(self):
        files = self.testInst.remote_file_list(start=dt.datetime(2009, 1, 1),
                                               stop=dt.datetime(2009, 1, 31))
        assert files.index[0] == dt.datetime(2009, 1, 1)
        assert files.index[-1] == dt.datetime(2009, 1, 31)

    def test_remote_date_range(self):
        files = self.testInst.remote_date_range(start=dt.datetime(2009, 1, 1),
                                                stop=dt.datetime(2009, 1, 31))
        assert len(files) == 2
        assert files[0] == dt.datetime(2009, 1, 1)
        assert files[-1] == dt.datetime(2009, 1, 31)

    def test_download_updated_files(self, caplog):
        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download_updated_files()
        # Perform a local search
        assert "files locally" in caplog.text
        # New files are found
        assert "that are new or updated" in caplog.text
        # download new files
        assert "Downloading data to" in caplog.text
        # Update local file list
        assert "Updating pysat file list" in caplog.text

    def test_download_recent_data(self, caplog):
        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download()
        # Tells user that recent data will be downloaded
        assert "most recent data by default" in caplog.text
        # download new files
        assert "Downloading data to" in caplog.text
        # Update local file list
        assert "Updating pysat file list" in caplog.text

    # --------------------------------------------------------------------------
    #
    # Test date helpers
    #
    # --------------------------------------------------------------------------
    def test_today_yesterday_and_tomorrow(self):
        now = dt.datetime.now()
        today = dt.datetime(now.year, now.month, now.day)
        assert today == self.testInst.today()
        assert today - pds.DateOffset(days=1) == self.testInst.yesterday()
        assert today + pds.DateOffset(days=1) == self.testInst.tomorrow()

    def test_filter_datetime(self):
        now = dt.datetime.now()
        today = dt.datetime(now.year, now.month, now.day)
        assert today == self.testInst._filter_datetime_input(now)

    def test_filtered_date_attribute(self):
        now = dt.datetime.now()
        today = dt.datetime(now.year, now.month, now.day)
        self.testInst.date = now
        assert today == self.testInst.date

    # -------------------------------------------------------------------------
    #
    # Test concat_data method
    #
    # --------------------------------------------------------------------------

    def test_concat_data(self):
        # data set #2
        self.testInst.load(2009, 2)
        data2 = self.testInst.data
        len2 = len(self.testInst.index)
        self.testInst.load(2009, 1)
        # data set #1
        data1 = self.testInst.data
        len1 = len(self.testInst.index)

        # concat together
        self.testInst.data = self.testInst.concat_data([data1, data2])
        # basic test for concatenation
        len3 = len(self.testInst.index)
        assert (len3 == len1 + len2)

        if self.testInst.pandas_format:
            # test concat from above
            assert (self.testInst[0:len1, :] == data1.values[:, :]).all().all()
            assert (self.testInst[len1:, :] == data2.values[:, :]).all().all()
            # concat together with sort=True
            # pandas only feature
            self.testInst.data = self.testInst.concat_data([data1, data2],
                                                           sort=True)
            # test for concatenation
            len3 = len(self.testInst.index)
            assert (len3 == len1 + len2)
            assert np.all(self.testInst[0:len1, data1.columns] == data1.values)
            assert np.all(self.testInst[len1:, data2.columns] == data2.values)
        else:

            # first, check for concat just before if else
            assert np.all(self.testInst[0:len1, :] == data1.to_array()[:, :])
            assert np.all(self.testInst[len1:, :] == data2.to_array()[:, :])

            # concat together while also specifying a different concatentation
            # dimension
            # xarray specific functionality
            # change name of main dim to support test for dim keyword
            data1 = data1.rename({xarray_epoch_name: 'Epoch2'})
            data2 = data2.rename({xarray_epoch_name: 'Epoch2'})

            # concat together
            self.testInst.data = self.testInst.concat_data(
                [data1, data2], dim='Epoch2').rename({'Epoch2':
                                                      xarray_epoch_name})
            # test for concatenation
            # Instrument.data must have a 'Epoch' index
            len3 = len(self.testInst.index)
            assert (len3 == len1 + len2)
            assert (self.testInst[0:len1, :]
                    == data1.to_array()[:, :]).all().all()
            assert (self.testInst[len1:, :]
                    == data2.to_array()[:, :]).all().all()

    # --------------------------------------------------------------------------
    #
    # Test empty property flags, if True, no data
    #
    # --------------------------------------------------------------------------
    def test_empty_flag_data_empty(self):
        assert self.testInst.empty

    def test_empty_flag_data_not_empty(self):
        self.testInst.load(2009, 1)
        assert not self.testInst.empty

    # --------------------------------------------------------------------------
    #
    # Test index attribute, should always be a datetime index
    #
    # --------------------------------------------------------------------------
    def test_index_attribute(self):
        # empty Instrument test
        assert isinstance(self.testInst.index, pds.Index)
        # now repeat the same test but with data loaded
        self.testInst.load(2009, 1)
        assert isinstance(self.testInst.index, pds.Index)

    def test_index_return(self):
        # load data
        self.testInst.load(2009, 1)
        # ensure we get the index back
        if self.testInst.pandas_format:
            assert np.all(self.testInst.index == self.testInst.data.index)
        else:
            assert np.all(self.testInst.index ==
                          self.testInst.data.indexes[xarray_epoch_name])

    # #--------------------------------------------------------------------------
    # #
    # # Test custom attributes
    # #
    # #--------------------------------------------------------------------------
    def test_retrieve_bad_attribute(self):
        with pytest.raises(AttributeError):
            self.testInst.bad_attr

    def test_base_attr(self):
        self.testInst._base_attr
        assert '_base_attr' in dir(self.testInst)

    # --------------------------------------------------------------------------
    #
    # test textual representations
    #
    # --------------------------------------------------------------------------
    def test_basic_repr(self):
        """Check for lines from each decision point in repr"""
        output = self.testInst.__str__()
        assert isinstance(output, str)
        assert output.find('pysat Instrument object') > 0
        # No custom functions
        assert output.find('No functions applied') > 0
        # No orbital info
        assert output.find('Orbit properties not set') > 0
        # Files exist for test inst
        assert output.find('Date Range:') > 0
        # No loaded data
        assert output.find('No loaded data') > 0
        assert output.find('Number of variables:') < 0
        assert output.find('uts') < 0

    def test_repr_w_orbit(self):
        re_load(pysat.instruments.pysat_testing)
        orbit_info = {'index': 'mlt',
                      'kind': 'local time',
                      'period': np.timedelta64(97, 'm')}
        testInst = pysat.Instrument(platform='pysat', name='testing',
                                    sat_id='10',
                                    clean_level='clean',
                                    update_files=True,
                                    orbit_info=orbit_info)

        output = testInst.__str__()
        # Check that orbit info is passed through
        assert output.find('Orbit properties not set') < 0
        assert output.find('Orbit Kind:') > 0
        assert output.find('Loaded Orbit Number: None') > 0
        # Activate orbits, check that message has changed
        testInst.load(2009, 1)
        testInst.orbits.next()
        output = testInst.__str__()
        assert output.find('Loaded Orbit Number: None') < 0
        assert output.find('Loaded Orbit Number: ') > 0

    def test_repr_w_padding(self):
        self.testInst.pad = pds.DateOffset(minutes=5)
        output = self.testInst.__str__()
        assert output.find('DateOffset: minutes=5') > 0

    def test_repr_w_custom_func(self):
        def testfunc(self):
            pass
        self.testInst.custom.attach(testfunc, 'modify')
        output = self.testInst.__str__()
        assert output.find('testfunc') > 0

    def test_repr_w_load_data(self):
        self.testInst.load(2009, 1)
        output = self.testInst.__str__()
        assert output.find('No loaded data') < 0
        assert output.find('Number of variables:') > 0
        assert output.find('uts') > 0

    # --------------------------------------------------------------------------
    #
    # test instrument initialization functions
    #
    # --------------------------------------------------------------------------
    def test_instrument_init(self):
        """Test if init function supplied by instrument can modify object"""
        assert self.testInst.new_thing

    def test_custom_instrument_load(self):
        """
        Test if the correct day is being loaded (End-to-End),
        with no instrument file but routines are passed.
        """
        import pysat.instruments.pysat_testing as test
        testInst = pysat.Instrument(inst_module=test, tag='',
                                    clean_level='clean')
        testInst.load(2009, 32)
        assert testInst.date == dt.datetime(2009, 2, 1)

    def test_custom_instrument_load_2(self):
        """
        Test if an exception is thrown correctly if there is no
        instrument file and supplied routines are incomplete.
        """
        import pysat.instruments.pysat_testing as test
        del test.list_files

        with pytest.raises(AttributeError):
            pysat.Instrument(inst_module=test, tag='',
                             clean_level='clean')

    def test_custom_instrument_load_3(self):
        """
        Test if an exception is thrown correctly if there is no
        instrument file and supplied routines are incomplete.
        """
        import pysat.instruments.pysat_testing as test
        del test.load

        with pytest.raises(AttributeError):
            pysat.Instrument(inst_module=test, tag='',
                             clean_level='clean')

    # --------------------------------------------------------------------------
    #
    # Test basic data access features, both getting and setting data
    #
    # --------------------------------------------------------------------------
    def test_basic_data_access_by_name(self):
        self.testInst.load(2009, 1)
        assert np.all(self.testInst['uts'] == self.testInst.data['uts'])

    def test_data_access_by_row_slicing_and_name(self):
        self.testInst.load(2009, 1)
        assert np.all(self.testInst[0:10, 'uts'] ==
                      self.testInst.data['uts'].values[0:10])

    def test_data_access_by_row_slicing_and_name_slicing(self):
        self.testInst.load(2009, 1)
        result = self.testInst[0:10, :]
        for variable, array in result.items():
            assert len(array) == len(self.testInst.data[variable].values[0:10])
            assert np.all(array == self.testInst.data[variable].values[0:10])

    def test_data_access_by_row_slicing_w_ndarray_and_name(self):
        self.testInst.load(2009, 1)
        assert np.all(self.testInst[np.arange(0, 10), 'uts'] ==
                      self.testInst.data['uts'].values[0:10])

    def test_data_access_by_row_and_name(self):
        self.testInst.load(2009, 1)
        assert np.all(self.testInst[0, 'uts'] ==
                      self.testInst.data['uts'].values[0])

    def test_data_access_by_row_index(self):
        self.testInst.load(2009, 1)
        idx = np.arange(10)
        assert np.all(self.testInst[idx]['uts'] ==
                      self.testInst.data['uts'].values[idx])

    def test_data_access_by_datetime_and_name(self):
        self.testInst.load(2009, 1)
        ind = dt.datetime(2009, 1, 1, 0, 0, 0)
        assert np.all(self.testInst[ind, 'uts'] ==
                      self.testInst.data['uts'].values[0])

    def test_data_access_by_datetime_slicing_and_name(self):
        self.testInst.load(2009, 1)
        time_step = (self.testInst.index[1]
                     - self.testInst.index[0]).value / 1.E9
        offset = pds.DateOffset(seconds=(10 * time_step))
        start = dt.datetime(2009, 1, 1, 0, 0, 0)
        stop = start + offset
        assert np.all(self.testInst[start:stop, 'uts']
                      == self.testInst.data['uts'].values[0:11])

    def test_setting_data_by_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])

    def test_setting_series_data_by_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2.*pds.Series(self.testInst['mlt'].values,
                                                   index=self.testInst.index)
        assert np.all(self.testInst['doubleMLT'] == 2.*self.testInst['mlt'])

        self.testInst['blankMLT'] = pds.Series(None, dtype='float64')
        assert np.all(np.isnan(self.testInst['blankMLT']))

    def test_setting_pandas_dataframe_by_names(self):
        self.testInst.load(2009, 1)
        self.testInst[['doubleMLT', 'tripleMLT']] = \
            pds.DataFrame({'doubleMLT': 2.*self.testInst['mlt'].values,
                           'tripleMLT': 3.*self.testInst['mlt'].values},
                          index=self.testInst.index)
        assert np.all(self.testInst['doubleMLT'] == 2.*self.testInst['mlt'])
        assert np.all(self.testInst['tripleMLT'] == 3.*self.testInst['mlt'])

    def test_setting_data_by_name_single_element(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2.
        assert np.all(self.testInst['doubleMLT'] == 2.)

        self.testInst['nanMLT'] = np.nan
        assert np.all(np.isnan(self.testInst['nanMLT']))

    def test_setting_data_by_name_with_meta(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = {'data': 2.*self.testInst['mlt'],
                                      'units': 'hours',
                                      'long_name': 'double trouble'}
        assert np.all(self.testInst['doubleMLT'] == 2.*self.testInst['mlt'])
        assert self.testInst.meta['doubleMLT'].units == 'hours'
        assert self.testInst.meta['doubleMLT'].long_name == 'double trouble'

    def test_setting_partial_data(self):
        self.testInst.load(2009, 1)
        cloneInst = self.testInst
        if self.testInst.pandas_format:
            self.testInst[0:3] = 0
            assert np.all(self.testInst[3:] == cloneInst[3:])
            assert np.all(self.testInst[0:3] == 0)
        else:
            # This command does not work for xarray
            assert True

    def test_setting_partial_data_by_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[0, 'doubleMLT'] = 0
        assert np.all(self.testInst[1:, 'doubleMLT'] ==
                      2. * self.testInst[1:, 'mlt'])
        assert self.testInst[0, 'doubleMLT'] == 0

    def test_setting_partial_data_by_integer_and_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2.*self.testInst['mlt']
        self.testInst[[0, 1, 2, 3], 'doubleMLT'] = 0
        assert np.all(self.testInst[4:, 'doubleMLT'] ==
                      2. * self.testInst[4:, 'mlt'])
        assert np.all(self.testInst[[0, 1, 2, 3], 'doubleMLT'] == 0)

    def test_setting_partial_data_by_slice_and_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[0:10, 'doubleMLT'] = 0
        assert np.all(self.testInst[10:, 'doubleMLT'] ==
                      2. * self.testInst[10:, 'mlt'])
        assert np.all(self.testInst[0:10, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_index_and_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[self.testInst.index[0:10], 'doubleMLT'] = 0
        assert np.all(self.testInst[10:, 'doubleMLT'] ==
                      2. * self.testInst[10:, 'mlt'])
        assert np.all(self.testInst[0:10, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_numpy_array_and_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[np.array([0, 1, 2, 3]), 'doubleMLT'] = 0
        assert np.all(self.testInst[4:, 'doubleMLT'] ==
                      2. * self.testInst[4:, 'mlt'])
        assert np.all(self.testInst[0:4, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_datetime_and_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[dt.datetime(2009, 1, 1, 0, 0, 0), 'doubleMLT'] = 0
        assert np.all(self.testInst[0, 'doubleMLT'] ==
                      2. * self.testInst[0, 'mlt'])
        assert np.all(self.testInst[0, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_datetime_slicing_and_name(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        time_step = (self.testInst.index[1]
                     - self.testInst.index[0]).value / 1.E9
        offset = pds.DateOffset(seconds=(10 * time_step))
        start = dt.datetime(2009, 1, 1, 0, 0, 0)
        stop = start + offset
        self.testInst[start:stop, 'doubleMLT'] = 0
        assert np.all(self.testInst[11:, 'doubleMLT']
                      == 2. * self.testInst[11:, 'mlt'])
        assert np.all(self.testInst[0:11, 'doubleMLT'] == 0)

    def test_modifying_data_inplace(self):
        self.testInst.load(2009, 1)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst['doubleMLT'] += 100
        assert np.all(self.testInst['doubleMLT']
                      == 2.*self.testInst['mlt'] + 100)

    def test_getting_all_data_by_index(self):
        self.testInst.load(2009, 1)
        a = self.testInst[[0, 1, 2, 3, 4]]
        if self.testInst.pandas_format:
            assert len(a) == 5
        else:
            assert a.sizes[xarray_epoch_name] == 5

    def test_getting_all_data_by_numpy_array_of_int(self):
        self.testInst.load(2009, 1)
        a = self.testInst[np.array([0, 1, 2, 3, 4])]
        if self.testInst.pandas_format:
            assert len(a) == 5
        else:
            assert a.sizes[xarray_epoch_name] == 5

    # --------------------------------------------------------------------------
    #
    # Test variable renaming
    #
    # --------------------------------------------------------------------------

    @pytest.mark.parametrize("values", [{'uts': 'uts1'},
                                        {'uts': 'uts2',
                                         'mlt': 'mlt2'},
                                        {'uts': 'long change with spaces'}])
    def test_basic_variable_renaming(self, values):
        # test single variable
        self.testInst.load(2009, 1)
        self.testInst.rename(values)
        for key in values:
            # check for new name
            assert values[key] in self.testInst.data
            assert values[key] in self.testInst.meta
            # ensure old name not present
            assert key not in self.testInst.data
            assert key not in self.testInst.meta

    @pytest.mark.parametrize("values", [{'help': 'I need somebody'},
                                        {'UTS': 'litte_uts'},
                                        {'utS': 'uts1'},
                                        {'utS': 'uts'}])
    def test_unknown_variable_error_renaming(self, values):
        # check for error for unknown variable name
        self.testInst.load(2009, 1)
        with pytest.raises(ValueError):
            self.testInst.rename(values)

    @pytest.mark.parametrize("values", [{'uts': 'UTS1'},
                                        {'uts': 'UTs2',
                                         'mlt': 'Mlt2'},
                                        {'uts': 'Long Change with spaces'}])
    def test_basic_variable_renaming_lowercase(self, values):
        # test single variable
        self.testInst.load(2009, 1)
        self.testInst.rename(values, lowercase_data_labels=True)
        for key in values:
            # check for new name
            assert values[key].lower() in self.testInst.data
            assert values[key].lower() in self.testInst.meta
            # ensure case retained in meta
            assert values[key] == self.testInst.meta[values[key]].name
            # ensure old name not present
            assert key not in self.testInst.data
            assert key not in self.testInst.meta

    @pytest.mark.parametrize("values", [{'profiles': {'density': 'ionization'}},
                                        {'profiles': {'density': 'mass'},
                                         'alt_profiles':
                                             {'density': 'volume'}}])
    def test_ho_pandas_variable_renaming(self, values):
        # check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(2009, 1)
                self.testInst.rename(values)
                for key in values:
                    for ikey in values[key]:
                        # check column name unchanged
                        assert key in self.testInst.data
                        assert key in self.testInst.meta
                        # check for new name in HO data
                        assert values[key][ikey] in self.testInst[0, key]
                        check_var = self.testInst.meta[key]['children']
                        assert values[key][ikey] in check_var
                        # ensure old name not present
                        assert ikey not in self.testInst[0, key]
                        check_var = self.testInst.meta[key]['children']
                        assert ikey not in check_var

    @pytest.mark.parametrize("values", [{'profiles':
                                        {'help': 'I need somebody'}},
                                        {'fake_profi':
                                        {'help': 'Not just anybody'}},
                                        {'wrong_profile':
                                        {'help': 'You know I need someone'},
                                         'fake_profiles':
                                        {'Beatles': 'help!'},
                                         'profiles':
                                        {'density': 'valid_change'}},
                                        {'fake_profile':
                                        {'density': 'valid HO change'}},
                                        {'Nope_profiles':
                                        {'density': 'valid_HO_change'}}])
    def test_ho_pandas_unknown_variable_error_renaming(self, values):
        # check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(2009, 1)
                # check for error for unknown column or HO variable name
                with pytest.raises(ValueError):
                    self.testInst.rename(values)

    @pytest.mark.parametrize("values", [{'profiles': {'density': 'Ionization'}},
                                        {'profiles': {'density': 'MASa'},
                                         'alt_profiles':
                                             {'density': 'VoLuMe'}}])
    def test_ho_pandas_variable_renaming_lowercase(self, values):
        # check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(2009, 1)
                self.testInst.rename(values)
                for key in values:
                    for ikey in values[key]:
                        # check column name unchanged
                        assert key in self.testInst.data
                        assert key in self.testInst.meta
                        # check for new name in HO data
                        test_val = values[key][ikey]
                        assert test_val in self.testInst[0, key]
                        check_var = self.testInst.meta[key]['children']
                        # case insensitive check
                        assert values[key][ikey] in check_var
                        # ensure new case in there
                        check_var = check_var[values[key][ikey]].name
                        assert values[key][ikey] == check_var
                        # ensure old name not present
                        assert ikey not in self.testInst[0, key]
                        check_var = self.testInst.meta[key]['children']
                        assert ikey not in check_var

    # --------------------------------------------------------------------------
    #
    # Test iteration behaviors
    #
    # --------------------------------------------------------------------------
    def test_left_bounds_with_prev(self):
        """Test if passing bounds raises StopIteration."""
        # load first data
        self.testInst.next()
        with pytest.raises(StopIteration):
            # go back to no data
            self.testInst.prev()

    def test_right_bounds_with_next(self):
        """Test if passing bounds raises StopIteration."""
        # load last data
        self.testInst.prev()
        with pytest.raises(StopIteration):
            # move on to future data that doesn't exist
            self.testInst.next()

    def test_set_bounds_with_frequency(self):
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2010, 1, 15)
        self.testInst.bounds = (start, stop, 'M')
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='M').tolist())

    def test_set_bounds_too_few(self):
        start = dt.datetime(2009, 1, 1)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start]

    def test_set_bounds_mixed(self):
        start = dt.datetime(2009, 1, 1)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, '2009-01-01.nofile']

    def test_set_bounds_wrong_type(self):
        start = dt.datetime(2009, 1, 1)
        with pytest.raises(AttributeError):
            self.testInst.bounds = [start, 1]

    def test_set_bounds_mixed_iterable(self):
        start = [dt.datetime(2009, 1, 1)]*2
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, '2009-01-01.nofile']

    def test_set_bounds_mixed_iterabless(self):
        start = [dt.datetime(2009, 1, 1)]*2
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, [dt.datetime(2009, 1, 1),
                                            '2009-01-01.nofile']]

    def test_set_bounds_string_default_start(self):
        self.testInst.bounds = [None, '2009-01-01.nofile']
        assert self.testInst.bounds[0][0] == self.testInst.files[0]

    def test_set_bounds_string_default_end(self):
        self.testInst.bounds = ['2009-01-01.nofile', None]
        assert self.testInst.bounds[1][0] == self.testInst.files[-1]

    def test_set_bounds_too_many(self):
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2009, 1, 1)
        huh = dt.datetime(2009, 1, 1)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, stop, huh]

    def test_set_bounds_by_date(self):
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list ==
                      pds.date_range(start, stop).tolist())

    def test_set_bounds_by_default(self):
        start = self.testInst.files.start_date
        stop = self.testInst.files.stop_date
        self.testInst.bounds = (None, None)
        assert np.all(self.testInst._iter_list ==
                      pds.date_range(start, stop).tolist())
        self.testInst.bounds = None
        assert np.all(self.testInst._iter_list ==
                      pds.date_range(start, stop).tolist())
        self.testInst.bounds = (start, None)
        assert np.all(self.testInst._iter_list ==
                      pds.date_range(start, stop).tolist())
        self.testInst.bounds = (None, stop)
        assert np.all(self.testInst._iter_list ==
                      pds.date_range(start, stop).tolist())

    def test_set_bounds_by_date_extra_time(self):
        start = dt.datetime(2009, 1, 1, 1, 10)
        stop = dt.datetime(2009, 1, 15, 1, 10)
        self.testInst.bounds = (start, stop)
        start = self.testInst._filter_datetime_input(start)
        stop = self.testInst._filter_datetime_input(stop)
        assert np.all(self.testInst._iter_list ==
                      pds.date_range(start, stop).tolist())

    def test_iterate_over_bounds_set_by_date(self):
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start, stop).tolist()
        assert np.all(dates == out)

    def test_iterate_over_bounds_set_by_date2(self):
        start = dt.datetime(2008, 1, 1)
        stop = dt.datetime(2010, 12, 31)
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start, stop).tolist()
        assert np.all(dates == out)

    def test_iterate_over_default_bounds(self):
        start = self.testInst.files.start_date
        stop = self.testInst.files.stop_date
        self.testInst.bounds = (None, None)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start, stop).tolist()
        assert np.all(dates == out)

    def test_set_bounds_by_date_season(self):
        start = [dt.datetime(2009, 1, 1), dt.datetime(2009, 2, 1)]
        stop = [dt.datetime(2009, 1, 15), dt.datetime(2009, 2, 15)]
        self.testInst.bounds = (start, stop)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(self.testInst._iter_list == out)

    def test_set_bounds_by_date_season_extra_time(self):
        start = [dt.datetime(2009, 1, 1, 1, 10),
                 dt.datetime(2009, 2, 1, 1, 10)]
        stop = [dt.datetime(2009, 1, 15, 1, 10),
                dt.datetime(2009, 2, 15, 1, 10)]
        self.testInst.bounds = (start, stop)
        start = self.testInst._filter_datetime_input(start)
        stop = self.testInst._filter_datetime_input(stop)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(self.testInst._iter_list == out)

    def test_iterate_over_bounds_set_by_date_season(self):
        start = [dt.datetime(2009, 1, 1), dt.datetime(2009, 2, 1)]
        stop = [dt.datetime(2009, 1, 15), dt.datetime(2009, 2, 15)]
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(dates == out)

    def test_iterate_over_bounds_set_by_date_season_extra_time(self):
        start = [dt.datetime(2009, 1, 1, 1, 10),
                 dt.datetime(2009, 2, 1, 1, 10)]
        stop = [dt.datetime(2009, 1, 15, 1, 10),
                dt.datetime(2009, 2, 15, 1, 10)]
        self.testInst.bounds = (start, stop)
        # filter
        start = self.testInst._filter_datetime_input(start)
        stop = self.testInst._filter_datetime_input(stop)
        # iterate
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(dates == out)

    def test_set_bounds_by_fname(self):
        start = '2009-01-01.nofile'
        stop = '2009-01-03.nofile'
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list ==
                      ['2009-01-01.nofile', '2009-01-02.nofile',
                       '2009-01-03.nofile'])

    def test_iterate_over_bounds_set_by_fname(self):
        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1)
        stop_d = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start_d, stop_d).tolist()
        assert np.all(dates == out)

    def test_iterate_over_bounds_set_by_fname_via_next(self):
        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1)
        stop_d = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        dates = []
        loop_next = True
        while loop_next:
            try:
                self.testInst.next()
                dates.append(self.testInst.date)
            except StopIteration:
                loop_next = False
        out = pds.date_range(start_d, stop_d).tolist()
        assert np.all(dates == out)

    def test_iterate_over_bounds_set_by_fname_via_prev(self):
        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1)
        stop_d = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        dates = []
        loop = True
        while loop:
            try:
                self.testInst.prev()
                dates.append(self.testInst.date)
            except StopIteration:
                loop = False
        out = pds.date_range(start_d, stop_d).tolist()
        assert np.all(dates == out[::-1])

    def test_set_bounds_by_fname_season(self):
        start = ['2009-01-01.nofile', '2009-02-01.nofile']
        stop = ['2009-01-03.nofile', '2009-02-03.nofile']
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list ==
                      ['2009-01-01.nofile', '2009-01-02.nofile',
                       '2009-01-03.nofile', '2009-02-01.nofile',
                       '2009-02-02.nofile', '2009-02-03.nofile'])

    def test_iterate_over_bounds_set_by_fname_season(self):
        start = ['2009-01-01.nofile', '2009-02-01.nofile']
        stop = ['2009-01-15.nofile', '2009-02-15.nofile']
        start_d = [dt.datetime(2009, 1, 1), dt.datetime(2009, 2, 1)]
        stop_d = [dt.datetime(2009, 1, 15), dt.datetime(2009, 2, 15)]
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start_d[0], stop_d[0]).tolist()
        out.extend(pds.date_range(start_d[1], stop_d[1]).tolist())
        assert np.all(dates == out)

    def test_creating_empty_instrument_object(self):
        null = pysat.Instrument()

        assert isinstance(null, pysat.Instrument)

    def test_incorrect_creation_empty_instrument_object(self):
        with pytest.raises(ValueError):
            # both name and platform should be empty
            _ = pysat.Instrument(platform='cnofs')

    def test_supplying_instrument_module_requires_name_and_platform(self):
        class Dummy:
            pass
        Dummy.name = 'help'

        with pytest.raises(AttributeError):
            _ = pysat.Instrument(inst_module=Dummy)


# ------------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# ------------------------------------------------------------------------------
class TestBasicsXarray(TestBasics):
    def setup(self):
        re_load(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         sat_id='10',
                                         clean_level='clean',
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


# ------------------------------------------------------------------------------
#
# Repeat tests above with 2d data
#
# ------------------------------------------------------------------------------
class TestBasics2D(TestBasics):
    def setup(self):
        re_load(pysat.instruments.pysat_testing2d)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing2d',
                                         sat_id='50',
                                         clean_level='clean',
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


# ------------------------------------------------------------------------------
#
# Repeat TestBasics above with shifted file dates
#
# ------------------------------------------------------------------------------

class TestBasicsShiftedFileDates(TestBasics):
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         sat_id='10',
                                         clean_level='clean',
                                         update_files=True,
                                         mangle_file_dates=True,
                                         strict_time_flag=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


# ------------------------------------------------------------------------------
#
# Test Instrument with a non-unique and non-monotonic index
#
# ------------------------------------------------------------------------------


class TestMalformedIndex():
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         sat_id='10',
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    # --------------------------------------------------------------------------
    #
    # Test checks on time uniqueness and monotonicity
    #
    # --------------------------------------------------------------------------
    def test_ensure_unique_index(self):
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)


# ------------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# ------------------------------------------------------------------------------

class TestMalformedIndexXarray(TestMalformedIndex):
    def setup(self):
        re_load(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         sat_id='10',
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


# ------------------------------------------------------------------------------
#
# Test data padding, loading by file
#
# ------------------------------------------------------------------------------
class TestDataPaddingbyFile():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        re_load(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')

        self.rawInst = pysat.Instrument(platform='pysat', name='testing',
                                        clean_level='clean',
                                        update_files=True)
        self.rawInst.bounds = self.testInst.bounds

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
        del self.rawInst

    def test_fid_data_padding(self):
        self.testInst.load(fid=1, verifyPad=True)
        self.rawInst.load(fid=1)
        delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + delta)

    def test_fid_data_padding_next(self):
        self.testInst.load(fid=1, verifyPad=True)
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fid=2)
        delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + delta)

    def test_fid_data_padding_multi_next(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(fid=1)
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fid=3)
        delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + delta)

    def test_fid_data_padding_prev(self):
        self.testInst.load(fid=2, verifyPad=True)
        self.testInst.prev(verifyPad=True)
        self.rawInst.load(fid=1)
        delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + delta)

    def test_fid_data_padding_multi_prev(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(fid=10)
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        self.rawInst.load(fid=8)
        delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + delta)

    def test_fid_data_padding_jump(self):
        self.testInst.load(fid=1, verifyPad=True)
        self.testInst.load(fid=10, verifyPad=True)
        self.rawInst.load(fid=10)
        delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + delta)

    def test_fid_data_padding_uniqueness(self):
        self.testInst.load(fid=1, verifyPad=True)
        assert (self.testInst.index.is_unique)

    def test_fid_data_padding_all_samples_present(self):
        self.testInst.load(fid=1, verifyPad=True)
        test_index = pds.date_range(self.testInst.index[0],
                                    self.testInst.index[-1], freq='S')
        assert (np.all(self.testInst.index == test_index))

    def test_fid_data_padding_removal(self):
        self.testInst.load(fid=1)
        self.rawInst.load(fid=1)
        assert self.testInst.index[0] == self.rawInst.index[0]
        assert self.testInst.index[-1] == self.rawInst.index[-1]
        assert len(self.rawInst.data) == len(self.testInst.data)


# ------------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# ------------------------------------------------------------------------------

class TestDataPaddingbyFileXarray(TestDataPaddingbyFile):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        re_load(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')

        self.rawInst = pysat.Instrument(platform='pysat',
                                        name='testing_xarray',
                                        clean_level='clean',
                                        update_files=True)
        self.rawInst.bounds = self.testInst.bounds

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
        del self.rawInst


class TestOffsetRightFileDataPaddingBasics(TestDataPaddingbyFile):
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5})
        self.rawInst = pysat.Instrument(platform='pysat', name='testing',
                                        tag='',
                                        clean_level='clean',
                                        update_files=True,
                                        sim_multi_file_right=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')
        self.rawInst.bounds = self.testInst.bounds


class TestOffsetRightFileDataPaddingBasicsXarray(TestDataPaddingbyFile):
    def setup(self):
        re_load(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5})
        self.rawInst = pysat.Instrument(platform='pysat',
                                        name='testing_xarray',
                                        clean_level='clean',
                                        update_files=True,
                                        sim_multi_file_right=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')
        self.rawInst.bounds = self.testInst.bounds


class TestOffsetLeftFileDataPaddingBasics(TestDataPaddingbyFile):
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5})
        self.rawInst = pysat.Instrument(platform='pysat', name='testing',
                                        clean_level='clean',
                                        update_files=True,
                                        sim_multi_file_left=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')
        self.rawInst.bounds = self.testInst.bounds


class TestDataPadding():
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_data_padding(self):
        self.testInst.load(2009, 2, verifyPad=True)
        assert (self.testInst.index[0] ==
                self.testInst.date - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date +
                pds.DateOffset(hours=23, minutes=59, seconds=59) +
                pds.DateOffset(minutes=5))

    def test_data_padding_offset_instantiation(self):
        testInst = pysat.Instrument(platform='pysat', name='testing',
                                    clean_level='clean',
                                    pad=pds.DateOffset(minutes=5),
                                    update_files=True)
        testInst.load(2009, 2, verifyPad=True)
        assert (testInst.index[0] ==
                testInst.date - pds.DateOffset(minutes=5))
        assert (testInst.index[-1] == testInst.date +
                pds.DateOffset(hours=23, minutes=59, seconds=59) +
                pds.DateOffset(minutes=5))

    def test_data_padding_bad_instantiation(self):
        with pytest.raises(ValueError):
            pysat.Instrument(platform='pysat', name='testing',
                             clean_level='clean',
                             pad=2,
                             update_files=True)

    def test_yrdoy_data_padding_missing_days(self):
        self.testInst.load(2008, 1)
        # test load
        self.testInst.load(2008, 0)
        # reset buffer data
        self.testInst.load(2008, -5)
        # test load, prev day empty, current and next has data
        self.testInst.load(2008, 1)
        # reset
        self.testInst.load(2008, -4)
        # etc
        self.testInst.load(2008, 2)
        self.testInst.load(2008, -3)
        self.testInst.load(2008, 3)
        # switch to missing data on the right
        self.testInst.load(2010, 365)
        self.testInst.load(2010, 360)
        self.testInst.load(2010, 366)
        self.testInst.load(2010, 360)
        self.testInst.load(2010, 367)
        assert True

    def test_data_padding_next(self):
        self.testInst.load(2009, 2, verifyPad=True)
        self.testInst.next(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_multi_next(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(2009, 2)
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_prev(self):
        self.testInst.load(2009, 2, verifyPad=True)
        self.testInst.prev(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_multi_prev(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(2009, 10)
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date -
                pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date +
                pds.DateOffset(hours=23, minutes=59, seconds=59) +
                pds.DateOffset(minutes=5))

    def test_data_padding_jump(self):
        self.testInst.load(2009, 2, verifyPad=True)
        self.testInst.load(2009, 11, verifyPad=True)
        assert (self.testInst.index[0] ==
                self.testInst.date - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] ==
                self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_uniqueness(self):
        self.testInst.load(2009, 1, verifyPad=True)
        assert (self.testInst.index.is_unique)

    def test_data_padding_all_samples_present(self):
        self.testInst.load(2009, 1, verifyPad=True)
        test_index = pds.date_range(self.testInst.index[0],
                                    self.testInst.index[-1], freq='S')
        assert (np.all(self.testInst.index == test_index))

    def test_data_padding_removal(self):
        self.testInst.load(2009, 1)
        assert (self.testInst.index[0] == self.testInst.date)
        assert (self.testInst.index[-1] == self.testInst.date +
                pds.DateOffset(hour=23, minutes=59, seconds=59))


class TestDataPaddingXarray(TestDataPadding):
    def setup(self):
        re_load(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)


class TestMultiFileRightDataPaddingBasics(TestDataPadding):
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5},
                                         multi_file_day=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestMultiFileRightDataPaddingBasicsXarray(TestDataPadding):
    def setup(self):
        re_load(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5},
                                         multi_file_day=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestMultiFileLeftDataPaddingBasics(TestDataPadding):
    def setup(self):
        re_load(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5},
                                         multi_file_day=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestMultiFileLeftDataPaddingBasicsXarray(TestDataPadding):
    def setup(self):
        re_load(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5},
                                         multi_file_day=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
