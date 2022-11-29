"""Unit tests for the padding methods in `pysat.Instrument`."""

import datetime as dt
from importlib import reload
import numpy as np

import pandas as pds
import pytest

import pysat
import pysat.instruments.pysat_ndtesting
import pysat.instruments.pysat_testing
import pysat.instruments.pysat_testing2d
import pysat.instruments.pysat_testing_xarray
from pysat.utils import testing
from pysat.utils.time import filter_datetime_input


class TestDataPaddingbyFile(object):
    """Unit tests for pandas `pysat.Instrument` with data padding by file."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True,
                                         use_header=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')

        self.rawInst = pysat.Instrument(platform='pysat', name='testing',
                                        clean_level='clean',
                                        update_files=True,
                                        use_header=True)
        self.rawInst.bounds = self.testInst.bounds
        self.delta = dt.timedelta(seconds=0)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.rawInst, self.delta
        return

    def eval_index_start_end(self):
        """Evaluate the start and end of the test `index` attributes."""

        assert self.testInst.index[0] == (self.rawInst.index[0] - self.delta), \
            "failed to pad the start of the `testInst` object"
        assert (self.testInst.index[-1]
                == (self.rawInst.index[-1] + self.delta)), \
            "failed to pad the end of the `testInst` object"
        assert self.testInst.index.is_unique, "padded index has duplicate times"

        if self.delta > dt.timedelta(seconds=0):
            assert len(self.testInst.index) > len(self.rawInst.index), \
                "padded instrument does not have enough data"
        else:
            assert len(self.testInst.index) == len(self.rawInst.index), \
                "unpadded instrument has extra or is missing data"
        return

    @pytest.mark.parametrize("dmin,tind,ncycle", [
        (5, 1, 0), (5, 1, 1), (5, 1, 2), (5, 2, -1), (5, 10, -2)])
    def test_fname_data_padding(self, dmin, tind, ncycle):
        """Test data padding load by filename.

        Parameters
        ----------
        dmin : int
            Number of iteration cycles before performing padding test.
            Positive values move forward in time, negative values backward.
        tind : int
            File index to load data for
        ncycle : int
            Difference in data coverage times in number of minutes. Must
            be the same value as the `pad` keyword passed to `self.testInst`.

        """

        # Load the test data with padding
        self.testInst.load(fname=self.testInst.files[tind], verifyPad=True)

        rind = tind + ncycle
        if ncycle > 0:
            while ncycle > 1:
                self.testInst.next()
                ncycle -= 1
            self.testInst.next(verifyPad=True)
        elif ncycle < 0:
            while ncycle < -1:
                self.testInst.prev()
                ncycle += 1
            self.testInst.prev(verifyPad=True)

        # Load the comparison file without padding and set the padding time
        self.rawInst.load(fname=self.testInst.files[rind])
        self.delta = dt.timedelta(minutes=dmin)

        # Evaluate the test results
        self.eval_index_start_end()
        return

    def test_fname_data_padding_jump(self):
        """Test data padding by filename after loading non-consecutive file."""

        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.testInst.load(fname=self.testInst.files[10], verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[10])
        self.delta = dt.timedelta(minutes=5)
        self.eval_index_start_end()
        return

    def test_fname_data_padding_uniqueness(self):
        """Ensure uniqueness data padding when loading by file."""

        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        assert self.testInst.index.is_unique
        return

    def test_fname_data_padding_all_samples_present(self):
        """Ensure all samples present when padding and loading by file."""

        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.delta = pds.date_range(self.testInst.index[0],
                                    self.testInst.index[-1], freq='S')
        assert np.all(self.testInst.index == self.delta)
        return

    def test_fname_data_padding_removal(self):
        """Ensure padded samples nominally dropped, loading by file."""

        self.testInst.load(fname=self.testInst.files[1])
        self.rawInst.load(fname=self.testInst.files[1])
        self.eval_index_start_end()
        return


class TestDataPaddingbyFileXarray(TestDataPaddingbyFile):
    """Unit tests for xarray `pysat.Instrument` with data padding by file."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True,
                                         use_header=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')

        self.rawInst = pysat.Instrument(platform='pysat',
                                        name='testing_xarray',
                                        clean_level='clean',
                                        update_files=True,
                                        use_header=True)
        self.rawInst.bounds = self.testInst.bounds
        self.delta = dt.timedelta(seconds=0)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.rawInst, self.delta
        return


class TestOffsetRightFileDataPaddingBasics(TestDataPaddingbyFile):
    """Unit tests for pandas `pysat.Instrument` with right offset data pad."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5},
                                         use_header=True)
        self.rawInst = pysat.Instrument(platform='pysat', name='testing',
                                        tag='',
                                        clean_level='clean',
                                        update_files=True,
                                        sim_multi_file_right=True,
                                        use_header=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')
        self.rawInst.bounds = self.testInst.bounds
        self.delta = dt.timedelta(seconds=0)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.rawInst, self.delta
        return


class TestOffsetRightFileDataPaddingBasicsXarray(TestDataPaddingbyFile):
    """Unit tests for xarray `pysat.Instrument` with right offset data pad."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5},
                                         use_header=True)
        self.rawInst = pysat.Instrument(platform='pysat',
                                        name='testing_xarray',
                                        clean_level='clean',
                                        update_files=True,
                                        sim_multi_file_right=True,
                                        use_header=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')
        self.rawInst.bounds = self.testInst.bounds
        self.delta = dt.timedelta(seconds=0)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.rawInst, self.delta
        return


class TestOffsetLeftFileDataPaddingBasics(TestDataPaddingbyFile):
    """Unit tests for pandas `pysat.Instrument` with left offset data pad."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5},
                                         use_header=True)
        self.rawInst = pysat.Instrument(platform='pysat', name='testing',
                                        clean_level='clean',
                                        update_files=True,
                                        sim_multi_file_left=True,
                                        use_header=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')
        self.rawInst.bounds = self.testInst.bounds
        self.delta = dt.timedelta(seconds=0)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.rawInst, self.delta
        return


class TestDataPadding(object):
    """Unit tests for pandas `pysat.Instrument` with data padding."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True,
                                         use_header=True)
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2
        self.delta = dt.timedelta(minutes=5)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy, self.delta
        return

    def eval_index_start_end(self):
        """Evaluate the start and end of the test `index` attributes."""

        assert (self.testInst.index[0]
                == self.testInst.date - self.delta), \
            "failed to pad the start of the `testInst` object"
        assert (self.testInst.index[-1] == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + self.delta), \
            "failed to pad the end of the `testInst` object"
        return

    def test_data_padding(self):
        """Ensure that pad works at the instrument level."""

        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.eval_index_start_end()
        return

    @pytest.mark.parametrize('pad', [dt.timedelta(minutes=5),
                                     pds.DateOffset(minutes=5),
                                     {'minutes': 5}])
    def test_data_padding_offset_instantiation(self, pad):
        """Ensure pad can be used as datetime, pandas, or dict."""

        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad=pad,
                                         update_files=True,
                                         use_header=True)
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.eval_index_start_end()
        return

    def test_data_padding_bad_instantiation(self):
        """Ensure error when padding input type incorrect."""

        estr = ' '.join(('pad must be a dict, NoneType, datetime.timedelta,',
                         'or pandas.DateOffset instance.'))
        testing.eval_bad_input(pysat.Instrument, ValueError, estr,
                               input_kwargs={'platform': 'pysat',
                                             'name': 'testing',
                                             'clean_level': 'clean', 'pad': 2,
                                             'update_files': True})
        return

    def test_data_padding_bad_load(self):
        """Test that data padding when loading all data is not allowed."""

        if self.testInst.multi_file_day:
            estr = '`load()` is not supported with multi_file_day'
        else:
            estr = '`load()` is not supported with data padding'

        testing.eval_bad_input(self.testInst.load, ValueError, estr)
        return

    def test_padding_exceeds_load_window(self):
        """Ensure error is padding window larger than loading window."""

        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'days': 2},
                                         update_files=True,
                                         use_header=True)

        testing.eval_bad_input(self.testInst.load, ValueError,
                               'Data padding window must be shorter than ',
                               input_kwargs={'date': self.ref_time})
        return

    def test_yrdoy_data_padding_missing_earlier_days(self):
        """Test padding feature operates when there are missing prev days."""

        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.start_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] == self.testInst.date
        assert (self.testInst.index[-1]
                > self.testInst.date + dt.timedelta(days=1))

        self.testInst.load(yr, doy)
        assert self.testInst.index[0] == self.testInst.date
        assert (self.testInst.index[-1]
                < self.testInst.date + dt.timedelta(days=1))
        return

    def test_yrdoy_data_padding_missing_later_days(self):
        """Test padding feature operates when there are missing later days."""

        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.stop_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] < self.testInst.date
        assert (self.testInst.index[-1]
                < self.testInst.date + dt.timedelta(days=1))

        self.testInst.load(yr, doy)
        assert self.testInst.index[0] == self.testInst.date
        assert (self.testInst.index[-1]
                < self.testInst.date + dt.timedelta(days=1))
        return

    def test_yrdoy_data_padding_missing_earlier_and_later_days(self):
        """Test padding feature operates if missing earlier/later days."""

        # reduce available files
        self.testInst.files.files = self.testInst.files.files[0:1]
        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.start_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] == self.testInst.date
        assert (self.testInst.index[-1] < self.testInst.date
                + dt.timedelta(days=1))
        return

    def test_data_padding_next(self):
        """Test data padding with `.next()`."""

        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.next(verifyPad=True)
        self.eval_index_start_end()
        return

    def test_data_padding_multi_next(self):
        """Test data padding with multiple `.next()`."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        self.eval_index_start_end()
        return

    def test_data_padding_prev(self):
        """Test data padding with `.prev()`."""

        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.prev(verifyPad=True)
        self.eval_index_start_end()
        return

    def test_data_padding_multi_prev(self):
        """Test data padding with multiple `.prev()`."""

        self.ref_doy = 10
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        self.eval_index_start_end()
        return

    def test_data_padding_jump(self):
        """Test data padding if load is outside the cache window."""
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.load(self.ref_time.year, self.ref_doy + 10,
                           verifyPad=True)
        self.eval_index_start_end()
        return

    def test_data_padding_uniqueness(self):
        """Test index after data padding is unique."""

        self.ref_doy = 1
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        assert (self.testInst.index.is_unique)
        return

    def test_data_padding_all_samples_present(self):
        """Test data padding when all samples are present."""

        self.ref_doy = 1
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        test_index = pds.date_range(self.testInst.index[0],
                                    self.testInst.index[-1], freq='S')
        assert (np.all(self.testInst.index == test_index))
        return

    def test_data_padding_removal(self):
        """Test data padding removal."""

        self.ref_doy = 1
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.delta = dt.timedelta(seconds=0)
        self.eval_index_start_end()
        return


class TestDataPaddingXArray(TestDataPadding):
    """Unit tests for xarray `pysat.Instrument` with data padding."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True,
                                         use_header=True)
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2
        self.delta = dt.timedelta(minutes=5)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy, self.delta
        return


class TestMultiFileRightDataPaddingBasics(TestDataPadding):
    """Unit tests for pandas `pysat.Instrument` with right offset data pad."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5},
                                         use_header=True)
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2
        self.delta = dt.timedelta(minutes=5)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy, self.delta
        return


class TestMultiFileRightDataPaddingBasicsXarray(TestDataPadding):
    """Unit tests for xarray `pysat.Instrument` with right offset data pad."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5},
                                         use_header=True)
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2
        self.delta = dt.timedelta(minutes=5)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy, self.delta
        return


class TestMultiFileLeftDataPaddingBasics(TestDataPadding):
    """Unit tests for pandas `pysat.Instrument` with left offset data pad."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5},
                                         use_header=True)
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2
        self.delta = dt.timedelta(minutes=5)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy, self.delta
        return


class TestMultiFileLeftDataPaddingBasicsXarray(TestDataPadding):
    """Unit tests for xarray `pysat.Instrument` with left offset data pad."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5},
                                         use_header=True)
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2
        self.delta = dt.timedelta(minutes=5)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.ref_time, self.ref_doy, self.delta
        return
