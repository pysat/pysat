# -*- coding: utf-8 -*-
"""Tests the pysat Instrument object and methods."""

import datetime as dt
from importlib import reload
import logging
import numpy as np
import warnings

import pandas as pds
import pytest
import xarray as xr

import pysat
import pysat.instruments.pysat_testing
import pysat.instruments.pysat_testing2d
import pysat.instruments.pysat_testing2d_xarray
import pysat.instruments.pysat_testing_xarray
from pysat.utils import generate_instrument_list
from pysat.utils.time import filter_datetime_input

xarray_epoch_name = 'time'


# -----------------------------------------------------------------------------
#
# Test Instrument object basics
#
# -----------------------------------------------------------------------------
class TestBasics(object):
    """Unit tests for pysat.Instrument object."""

    def setup_class(self):
        """Set up class-level variables once before all methods."""

        self.testing_kwargs = {'test_init_kwarg': True,
                               'test_clean_kwarg': False,
                               'test_preprocess_kwarg': 'test_phrase',
                               'test_load_kwarg': 'bright_light',
                               'test_list_files_kwarg': 'sleep_tight',
                               'test_list_remote_kwarg': 'one_eye_open',
                               'test_download_kwarg': 'exit_night'}
        return

    def teardown_class(self):
        """Clean up class-level variables once after all methods."""

        del self.testing_kwargs
        return

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return

    def generate_fname(self, date):
        """Generate a filename for support of testing iterations."""

        fname = '{year:04d}-{month:02d}-{day:02d}.nofile'
        return fname.format(year=date.year, month=date.month, day=date.day)

    def support_iter_evaluations(self, values, for_loop=False, reverse=False,
                                 by_date=True):
        """Support testing of .next/.prev via dates/files.

        Parameters
        ----------
        values : list of four inputs
            [starts, stops, step, width]
        for_loop : bool
            If True, iterate via for loop.  If False, iterate via while.
            (default=False)
        reverse : bool
            Direction of iteration.  If True, use `.prev()`. If False, use
            `.next()`.  (default=False)
        by_date : bool
            If True, set bounds by date.  If False, set bounds by filename.
            (default=False)
        """

        # Extract specific values from input.
        starts = values[0]
        stops = values[1]
        step = values[2]
        width = values[3]

        # Ensure dates are lists for consistency of later code.
        starts = np.asarray([starts])
        stops = np.asarray([stops])
        if len(starts.shape) > 1:
            starts = starts.squeeze().tolist()
            stops = stops.squeeze().tolist()
        else:
            starts = starts.tolist()
            stops = stops.tolist()

        if by_date:
            # Convert step and width to string and timedelta.
            step = '{:}D'.format(step)
            width = dt.timedelta(days=width)
            self.testInst.bounds = (starts, stops, step, width)
        else:
            # Convert start and stop to filenames.
            start_files = [self.generate_fname(date) for date in starts]
            stop_files = [self.generate_fname(date) for date in stops]
            self.testInst.bounds = (start_files, stop_files, step, width)

        # iterate until we run out of bounds
        dates = []
        time_range = []
        if for_loop:
            # iterate via for loop option
            for inst in self.testInst:
                dates.append(inst.date)
                time_range.append((inst.index[0],
                                   inst.index[-1]))
        else:
            # .next/.prev iterations
            if reverse:
                iterator = self.testInst.prev
            else:
                iterator = self.testInst.next
            try:
                while True:
                    iterator()
                    dates.append(self.testInst.date)
                    time_range.append((self.testInst.index[0],
                                       self.testInst.index[-1]))
            except StopIteration:
                # reached the end
                pass

        # Deal with file or date iteration, make file inputs same as date for
        # verification purposes.
        if isinstance(step, int):
            step = str(step) + 'D'
        if isinstance(width, int):
            width = dt.timedelta(days=width)

        out = []
        for start, stop in zip(starts, stops):
            tdate = stop - width + dt.timedelta(days=1)
            out.extend(pds.date_range(start, tdate, freq=step).tolist())
        if reverse:
            # Ensure time order is consistent for verify methods.
            out = out[::-1]
        pysat.utils.testing.assert_lists_equal(dates, out)

        output = {}
        output['expected_times'] = out
        output['observed_times'] = time_range
        output['starts'] = starts
        output['stops'] = stops
        output['width'] = width
        output['step'] = step
        return output

    # -------------------------------------------------------------------------
    #
    # Test basic loads, by date, filename, file id, as well as prev/next
    #
    # -------------------------------------------------------------------------
    def eval_successful_load(self, end_date=None):
        """Evaluate successful loading of `self.testInst`.

        Parameters
        ----------
        end_date : dt.datetime or NoneType
            End date for loading data.  If None, assumes self.ref_time + 1 day.
            (default=None)

        """
        # Test that the first loaded time matches the first requested time
        assert self.testInst.index[0] == self.ref_time, \
            "First loaded time is incorrect"

        # Test that the Instrument date is set to the requested start date
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day)
        assert self.testInst.date == self.out, \
            "Incorrect Instrument date attribute"

        # Test that the end of the loaded data matches the requested end date
        if end_date is None:
            end_date = self.ref_time + dt.timedelta(days=1)
        assert self.testInst.index[-1] > self.ref_time, \
            "Last loaded time is not greater than the start time"
        assert self.testInst.index[-1] <= end_date, \
            "Last loaded time is greater than the requested end date"

        return

    def eval_iter_list(self, start, stop, dates=False, freq=None):
        """Evaluate successful generation of iter_list for `self.testInst`.

        Parameters
        ----------
        start : dt.datetime or list of dt.datetime
            Start date for generating iter_list.
        stop : dt.datetime or list of dt.datetime
            start date for generating iter_list.
        dates : bool
            If True, checks each date.  If False, checks against the _iter_list
            (default=False)
        freq : int or NoneType
            Frequency in days.  If None, use pandas default. (default=None)

        """

        kwargs = {'freq': '{:}D'.format(freq)} if freq else {}

        if isinstance(start, dt.datetime):
            out = pds.date_range(start, stop, **kwargs).tolist()
        else:
            out = list()
            for (istart, istop) in zip(start, stop):
                out.extend(pds.date_range(istart, istop, **kwargs).tolist())
        if dates:
            dates = []
            for inst in self.testInst:
                dates.append(inst.date)
            pysat.utils.testing.assert_lists_equal(dates, out)
        else:
            pysat.utils.testing.assert_lists_equal(self.testInst._iter_list,
                                                   out)
        return

    @pytest.mark.parametrize("kwargs", [{}, {'num_samples': 30}])
    def test_basic_instrument_load(self, kwargs):
        """Test that the correct day loads with input year and doy."""

        # Load data by year and day of year
        self.testInst.load(self.ref_time.year, self.ref_doy, **kwargs)

        # Test that the loaded date range is correct
        self.eval_successful_load()
        return

    def test_basic_instrument_load_two_days(self):
        """Test that the correct day loads (checking object date and data)."""

        # Load the reference date
        end_date = self.ref_time + dt.timedelta(days=2)
        end_doy = int(end_date.strftime("%j"))
        self.testInst.load(self.ref_time.year, self.ref_doy, end_date.year,
                           end_doy)

        # Test that the loaded date range is correct
        self.eval_successful_load(end_date=end_date)
        return

    def test_basic_instrument_bad_keyword_init(self):
        """Check for error when instantiating with bad load keywords on init."""

        # Test that the correct error is raised
        with pytest.raises(ValueError) as verr:
            pysat.Instrument(platform=self.testInst.platform,
                             name=self.testInst.name, num_samples=10,
                             clean_level='clean',
                             unsupported_keyword_yeah=True)

        # Evaluate error message
        assert str(verr).find("unknown keyword supplied") > 0
        return

    def test_basic_instrument_bad_keyword_at_load(self):
        """Check for error when calling load with bad keywords."""

        # Test that the correct error is raised
        with pytest.raises(TypeError) as terr:
            self.testInst.load(date=self.ref_time, unsupported_keyword=True)

        # Evaluate error message
        assert str(terr).find("load() got an unexpected keyword") >= 0
        return

    @pytest.mark.parametrize('kwarg', ['supported_tags', 'start', 'stop',
                                       'freq', 'date_array', 'data_path'])
    def test_basic_instrument_reserved_keyword(self, kwarg):
        """Check for error when instantiating with reserved keywords."""

        # Check that the correct error is raised
        with pytest.raises(ValueError) as err:
            pysat.Instrument(platform=self.testInst.platform,
                             name=self.testInst.name, num_samples=10,
                             clean_level='clean',
                             **{kwarg: '1s'})

        # Check that the error message is correct
        estr = ''.join(('Reserved keyword "', kwarg, '" is not ',
                        'allowed at instantiation.'))
        assert str(err).find(estr) >= 0
        return

    def test_basic_instrument_load_yr_no_doy(self):
        """Ensure doy required if yr present."""

        # Check that the correct error is raised
        with pytest.raises(TypeError) as err:
            self.testInst.load(self.ref_time.year)

        # Check that the error message is correct
        estr = 'Unknown or incomplete input combination.'
        assert str(err).find(estr) >= 0
        return

    @pytest.mark.parametrize('doy', [0, 367, 1000, -1, -10000])
    def test_basic_instrument_load_yr_bad_doy(self, doy):
        """Ensure doy load argument in valid range."""

        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, doy)
        estr = 'Day of year (doy) is only valid between and '
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize('end_doy', [0, 367, 1000, -1, -10000])
    def test_basic_instrument_load_yr_bad_end_doy(self, end_doy):
        """Ensure end_doy keyword in valid range."""

        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, 1, end_yr=self.ref_time.year,
                               end_doy=end_doy)
        estr = 'Day of year (end_doy) is only valid between and '
        assert str(err).find(estr) >= 0

        return

    def test_basic_instrument_load_yr_no_end_doy(self):
        """Ensure end_doy required if end_yr present."""

        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, self.ref_doy,
                               self.ref_time.year)
        estr = 'Both end_yr and end_doy must be set'
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize("input", [{'yr': 2009, 'doy': 1,
                                        'date': dt.datetime(2009, 1, 1)},
                                       {'yr': 2009, 'doy': 1,
                                        'end_date': dt.datetime(2009, 1, 1)},
                                       {'yr': 2009, 'doy': 1,
                                        'fname': 'dummy_str.nofile'},
                                       {'yr': 2009, 'doy': 1,
                                        'stop_fname': 'dummy_str.nofile'},
                                       {'date': dt.datetime(2009, 1, 1),
                                        'fname': 'dummy_str.nofile'},
                                       {'date': dt.datetime(2009, 1, 1),
                                        'stop_fname': 'dummy_str.nofile'},
                                       {'date': dt.datetime(2009, 1, 1),
                                        'fname': 'dummy_str.nofile',
                                        'end_yr': 2009, 'end_doy': 1}])
    def test_basic_instrument_load_mixed_inputs(self, input):
        """Ensure mixed load inputs raise ValueError."""

        with pytest.raises(ValueError) as err:
            self.testInst.load(**input)
        estr = 'An inconsistent set of inputs have been'
        assert str(err).find(estr) >= 0
        return

    def test_basic_instrument_load_no_input(self):
        """Test that `.load()` loads all data."""

        self.testInst.load()
        assert (self.testInst.index[0] == self.testInst.files.start_date)
        assert (self.testInst.index[-1] >= self.testInst.files.stop_date)
        assert (self.testInst.index[-1] <= self.testInst.files.stop_date
                + dt.timedelta(days=1))
        return

    @pytest.mark.parametrize('load_in,verr',
                             [('fname', 'have multi_file_day and load by file'),
                              (None, 'is not supported with multi_file_day')])
    def test_instrument_load_errors_with_multifile(self, load_in, verr):
        """Ensure load calls raises ValueError with multi_file_day as True."""

        self.testInst.multi_file_day = True

        if load_in == 'fname':
            load_kwargs = {load_in: self.testInst.files[0]}
        else:
            load_kwargs = dict()

        with pytest.raises(ValueError) as err:
            self.testInst.load(**load_kwargs)

        assert str(err).find(verr) >= 0

        return

    def test_basic_instrument_load_by_date(self):
        """Test loading by date."""

        self.testInst.load(date=self.ref_time)
        self.eval_successful_load()
        return

    def test_basic_instrument_load_by_dates(self):
        """Test date range loading, date and end_date."""

        end_date = self.ref_time + dt.timedelta(days=2)
        self.testInst.load(date=self.ref_time, end_date=end_date)
        self.eval_successful_load(end_date=end_date)
        return

    def test_basic_instrument_load_by_date_with_extra_time(self):
        """Ensure `.load(date=date)` only uses date portion of datetime."""

        # put in a date that has more than year, month, day
        self.testInst.load(date=(self.ref_time + dt.timedelta(minutes=71)))
        self.eval_successful_load()
        return

    def test_basic_instrument_load_data(self):
        """Test that correct day loads (checking down to the sec)."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.eval_successful_load()
        return

    def test_basic_instrument_load_leap_year(self):
        """Test if the correct day is being loaded (Leap-Year)."""

        self.ref_time = dt.datetime(2008, 12, 31)
        self.ref_doy = 366
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.eval_successful_load()
        return

    @pytest.mark.parametrize("operator,ref_time",
                             [('next', dt.datetime(2008, 1, 1)),
                              ('prev', dt.datetime(2010, 12, 31))])
    def test_file_load_default(self, operator, ref_time):
        """Test if correct day loads by default when first invoking `.next`."""

        getattr(self.testInst, operator)()

        # Modify ref time since iterator changes load date.
        self.ref_time = ref_time
        self.eval_successful_load()
        return

    @pytest.mark.parametrize("operator", [('next'), ('prev')])
    def test_file_load_bad_start_file(self, operator):
        """Test Error for in new day when on a file not in iteration list."""

        self.testInst.load(fname=self.testInst.files[12])

        # Set new bounds that do not include this date.
        self.testInst.bounds = (self.testInst.files[9], self.testInst.files[20],
                                2, 1)
        with pytest.raises(StopIteration) as err:
            getattr(self.testInst, operator)()
        estr = 'Unable to find loaded filename '
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize("operator", [('next'), ('prev')])
    def test_file_load_bad_start_date(self, operator):
        """Test that day iterators raise Error on bad start date."""

        self.testInst.load(date=self.ref_time)

        # Set new bounds that do not include this date.
        self.testInst.bounds = (self.ref_time + dt.timedelta(days=1),
                                self.ref_time + dt.timedelta(days=10),
                                '2D', dt.timedelta(days=1))

        with pytest.raises(StopIteration) as err:
            getattr(self.testInst, operator)()
        estr = 'Unable to find loaded date '
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize("operator", [('next'), ('prev')])
    def test_file_load_empty_iteration(self, operator):
        """Ensure empty iteration list is fine via day iteration."""

        self.testInst.bounds = (None, None, '10000D',
                                dt.timedelta(days=10000))
        with pytest.raises(StopIteration) as err:
            getattr(self.testInst, operator)()
        estr = 'File list is empty. '
        assert str(err).find(estr) >= 0

        return

    def test_basic_fname_instrument_load(self):
        """Test loading by filename from attached `.files`."""

        # If mangle_file_date is true, index will not match exactly.
        # Find the closest point.
        ind = np.argmin(abs(self.testInst.files.files.index - self.ref_time))
        self.testInst.load(fname=self.testInst.files[ind])
        self.eval_successful_load()
        return

    @pytest.mark.parametrize("operator,direction",
                             [('next', 1),
                              ('prev', -1)])
    def test_fname_load_default(self, operator, direction):
        """Test correct day loads when moving by day, starting w/ fname."""

        # If mangle_file_date is true, index will not match exactly.
        # Find the closest point.
        ind = np.argmin(abs(self.testInst.files.files.index - self.ref_time))
        self.testInst.load(fname=self.testInst.files[ind])
        getattr(self.testInst, operator)()

        # Modify ref time since iterator changes load date.
        self.ref_time = self.ref_time + direction * dt.timedelta(days=1)
        self.eval_successful_load()
        return

    def test_filename_load(self):
        """Test if file is loadable by filename with no path."""

        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'))
        self.eval_successful_load()
        return

    def test_filenames_load(self):
        """Test if files are loadable by filename range."""

        stop_fname = self.ref_time + dt.timedelta(days=1)
        stop_fname = stop_fname.strftime('%Y-%m-%d.nofile')
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'),
                           stop_fname=stop_fname)
        assert self.testInst.index[0] == self.ref_time
        assert self.testInst.index[-1] >= self.ref_time + dt.timedelta(days=1)
        assert self.testInst.index[-1] <= self.ref_time + dt.timedelta(days=2)
        return

    def test_filenames_load_out_of_order(self):
        """Test error raised if fnames out of temporal order."""

        stop_fname = self.ref_time + dt.timedelta(days=1)
        stop_fname = stop_fname.strftime('%Y-%m-%d.nofile')
        with pytest.raises(ValueError) as err:
            check_fname = self.ref_time.strftime('%Y-%m-%d.nofile')
            self.testInst.load(fname=stop_fname,
                               stop_fname=check_fname)
        estr = '`stop_fname` must occur at a later date '
        assert str(err).find(estr) >= 0
        return

    def test_list_files(self):
        """Test that `inst.files.files` returns a pandas series."""

        files = self.testInst.files.files
        assert isinstance(files, pds.Series)
        return

    @pytest.mark.parametrize("remote_func,num", [('remote_file_list', 31),
                                                 ('remote_date_range', 2)])
    def test_remote_functions(self, remote_func, num):
        """Test simulated remote functions for valid list of files."""

        stop = self.ref_time + dt.timedelta(days=30)
        self.out = getattr(self.testInst, remote_func)(start=self.ref_time,
                                                       stop=stop)
        assert len(self.out) == num

        # Get index if a pds.Series is returned.
        if isinstance(self.out, pds.Series):
            self.out = self.out.index
        assert filter_datetime_input(self.out[0]) == self.ref_time
        assert filter_datetime_input(self.out[-1]) == stop
        return

    @pytest.mark.parametrize("file_bounds, non_default",
                             [(False, False), (True, False), (False, True),
                              (True, True)])
    def test_download_updated_files(self, caplog, file_bounds, non_default):
        """Test download_updated_files and default bounds are updated."""

        if file_bounds:
            if non_default:
                # set bounds to second and second to last file
                self.testInst.bounds = (self.testInst.files[1],
                                        self.testInst.files[-2])
            else:
                # set bounds to first and last file
                self.testInst.bounds = (self.testInst.files[0],
                                        self.testInst.files[-1])
        else:
            if non_default:
                # set bounds to first and first date
                self.testInst.bounds = (self.testInst.files.start_date,
                                        self.testInst.files.start_date)

        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download_updated_files()

        # Test the logging output for the following conditions:
        # - perform a local search,
        # - new files are found,
        # - download new files, and
        # - update local file list.
        assert "local files" in caplog.text
        assert "that are new or updated" in caplog.text
        assert "Downloading data to" in caplog.text
        assert "Updating pysat file list" in caplog.text

        if non_default:
            assert "Updating instrument object bounds " not in caplog.text
        else:
            text = caplog.text
            if file_bounds:
                assert "Updating instrument object bounds by file" in text
            else:
                assert "Updating instrument object bounds by date" in text
        return

    def test_download_recent_data(self, caplog):
        """Test download of recent data."""

        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download()

        # Ensure user was told that recent data will be downloaded
        assert "most recent data by default" in caplog.text

        # Ensure user was notified of new files being download
        assert "Downloading data to" in caplog.text

        # Ensure user was notified of updates to the local file list
        assert "Updating pysat file list" in caplog.text

        return

    def test_download_bad_date_range(self, caplog):
        """Test download with bad date input."""

        with caplog.at_level(logging.WARNING, logger='pysat'):
            self.testInst.download(start=self.ref_time,
                                   stop=self.ref_time - dt.timedelta(days=10))

        # Ensure user is warned about not calling download due to bad time input
        assert "Requested download over an empty date range" in caplog.text
        return

    # -------------------------------------------------------------------------
    #
    # Test date helpers
    #
    # -------------------------------------------------------------------------
    def test_today_yesterday_and_tomorrow(self):
        """Test the correct instantiation of yesterday/today/tomorrow dates."""

        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day)
        assert self.out == self.testInst.today()
        assert self.out - dt.timedelta(days=1) == self.testInst.yesterday()
        assert self.out + dt.timedelta(days=1) == self.testInst.tomorrow()
        return

    def test_filtered_date_attribute(self):
        """Test use of filter during date assignment."""

        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day)
        self.testInst.date = self.ref_time
        assert self.out == self.testInst.date
        return

    # -------------------------------------------------------------------------
    #
    # Test __eq__ method
    #
    # -------------------------------------------------------------------------

    def test_eq_no_data(self):
        """Test equality when the same object."""

        inst_copy = self.testInst.copy()
        assert inst_copy == self.testInst
        return

    def test_eq_both_with_data(self):
        """Test equality when the same object with loaded data."""

        self.testInst.load(date=self.ref_time)
        inst_copy = self.testInst.copy()
        assert inst_copy == self.testInst
        return

    def test_eq_one_with_data(self):
        """Test equality when the same objects but only one with loaded data."""

        self.testInst.load(date=self.ref_time)
        inst_copy = self.testInst.copy()
        inst_copy.data = self.testInst._null_data
        assert not (inst_copy == self.testInst)
        return

    def test_eq_different_data_type(self):
        """Test equality different data type."""

        self.testInst.load(date=self.ref_time)
        inst_copy = self.testInst.copy()
        if self.testInst.pandas_format:
            inst_copy.pandas_format = False
            inst_copy.data = xr.Dataset()
        else:
            inst_copy.pandas_format = True
            inst_copy.data = pds.DataFrame()
        assert not (inst_copy == self.testInst)
        return

    def test_eq_different_object(self):
        """Test equality using different pysat.Instrument objects."""

        reload(pysat.instruments.pysat_testing)
        obj1 = pysat.Instrument(platform='pysat', name='testing',
                                num_samples=10, clean_level='clean',
                                update_files=True)

        reload(pysat.instruments.pysat_testing_xarray)
        obj2 = pysat.Instrument(platform='pysat', name='testing_xarray',
                                num_samples=10, clean_level='clean',
                                update_files=True)
        assert not (obj1 == obj2)
        return

    def test_eq_different_type(self):
        """Test equality False when non-Instrument object."""

        assert self.testInst != np.array([])
        return

    def test_inequality_modified_object(self):
        """Test that equality is false if other missing attributes."""

        self.out = self.testInst.copy()

        # Remove attribute
        del self.out.platform

        assert self.testInst != self.out
        return

    def test_inequality_reduced_object(self):
        """Test that equality is false if self missing attributes."""

        self.out = self.testInst.copy()
        self.out.hi_there = 'hi'
        assert self.testInst != self.out
        return

    # -------------------------------------------------------------------------
    #
    # Test copy method
    #
    # -------------------------------------------------------------------------

    def test_copy(self):
        """Test `.copy()`."""

        inst_copy = self.testInst.copy()
        assert inst_copy == self.testInst
        return

    def test_copy_from_reference(self):
        """Test `.copy()` if invoked from a `weakref.proxy` of Instrument."""

        inst_copy = self.testInst.orbits.inst.copy()
        inst_copy2 = self.testInst.files.inst_info['inst'].copy()
        assert inst_copy == self.testInst
        assert inst_copy == inst_copy2
        assert inst_copy2 == self.testInst
        return

    def test_copy_w_inst_module(self):
        """Test `.copy()` with inst_module != None."""

        # Assign module to inst_module
        self.testInst.inst_module = pysat.instruments.pysat_testing

        inst_copy = self.testInst.copy()

        # Confirm equality and that module is still present
        assert inst_copy == self.testInst
        assert inst_copy.inst_module == pysat.instruments.pysat_testing
        assert self.testInst.inst_module == pysat.instruments.pysat_testing

        return

    # -------------------------------------------------------------------------
    #
    # Test concat_data method
    #
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("prepend, sort_dim_toggle",
                             [(True, True), (True, False), (False, False)])
    def test_concat_data(self, prepend, sort_dim_toggle):
        """Test Instrument data concatonation."""

        # Load a data set to concatonate
        self.testInst.load(self.ref_time.year, self.ref_doy + 1)
        data2 = self.testInst.data
        len2 = len(self.testInst.index)

        # Load a different data set into the instrument
        self.testInst.load(self.ref_time.year, self.ref_doy)
        len1 = len(self.testInst.index)

        # Set the keyword arguments
        kwargs = {'prepend': prepend}
        if sort_dim_toggle:
            if self.testInst.pandas_format:
                kwargs['sort'] = True
            else:
                kwargs['dim'] = 'Epoch2'
                data2 = data2.rename({xarray_epoch_name: 'Epoch2'})
                self.testInst.data = self.testInst.data.rename(
                    {xarray_epoch_name: 'Epoch2'})

        # Concat together
        self.testInst.concat_data(data2, **kwargs)

        if sort_dim_toggle and not self.testInst.pandas_format:
            # Rename to the standard epoch name
            self.testInst.data = self.testInst.data.rename(
                {'Epoch2': xarray_epoch_name})

        # Basic test for concatenation
        self.out = len(self.testInst.index)
        assert (self.out == len1 + len2)

        # Detailed test for concatonation through index
        if prepend:
            assert np.all(self.testInst.index[:len1]
                          > self.testInst.index[len1:])
        else:
            assert np.all(self.testInst.index[:len1]
                          < self.testInst.index[len1:])

        if self.testInst.pandas_format:
            if sort_dim_toggle:
                assert np.all(self.testInst.data.columns
                              == np.sort(data2.columns))
            else:
                assert np.all(self.testInst.data.columns == data2.columns)
        return

    # -------------------------------------------------------------------------
    #
    # Test empty property flags, if True, no data
    #
    # -------------------------------------------------------------------------
    def test_empty_flag_data_empty(self):
        """Test the status of the empty flag for unloaded data."""

        assert self.testInst.empty
        return

    def test_empty_flag_data_not_empty(self):
        """Test the status of the empty flag for loaded data."""

        self.testInst.load(date=self.ref_time)
        assert not self.testInst.empty
        return

    # -------------------------------------------------------------------------
    #
    # Test index attribute, should always be a datetime index
    #
    # -------------------------------------------------------------------------
    def test_index_attribute(self):
        """Test the index attribute before and after loading data."""

        # empty Instrument test
        assert isinstance(self.testInst.index, pds.Index)

        # now repeat the same test but with data loaded
        self.testInst.load(date=self.ref_time)
        assert isinstance(self.testInst.index, pds.Index)
        return

    def test_index_return(self):
        """Test that the index is returned in the proper format."""

        # load data
        self.testInst.load(self.ref_time.year, self.ref_doy)
        # ensure we get the index back
        if self.testInst.pandas_format:
            assert np.all(self.testInst.index == self.testInst.data.index)
        else:
            assert np.all(self.testInst.index
                          == self.testInst.data.indexes[xarray_epoch_name])
        return

    # #------------------------------------------------------------------------
    # #
    # # Test custom attributes
    # #
    # #------------------------------------------------------------------------

    def test_retrieve_bad_attribute(self):
        """Test that AttributeError is raised if bad attribute is retrieved."""

        with pytest.raises(AttributeError) as aerr:
            self.testInst.bad_attr
        assert str(aerr).find("object has no attribute") >= 0
        return

    def test_base_attr(self):
        """Test retrieval of base attribute."""

        self.testInst._base_attr
        assert '_base_attr' in dir(self.testInst)
        return

    def test_inst_attributes_not_overwritten(self):
        """Test that custom Instrument attributes are preserved on load."""

        greeting = '... listen!'
        self.testInst.hei = greeting
        self.testInst.load(date=self.ref_time)
        assert self.testInst.hei == greeting
        return

    # -------------------------------------------------------------------------
    #
    # test textual representations
    #
    # -------------------------------------------------------------------------
    def test_basic_repr(self):
        """The repr output will match the beginning of the str output."""

        self.out = self.testInst.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("pysat.Instrument(") == 0
        return

    def test_basic_str(self):
        """Check for lines from each decision point in repr."""

        self.out = self.testInst.__str__()
        assert isinstance(self.out, str)
        assert self.out.find('pysat Instrument object') == 0
        # No custom functions
        assert self.out.find('Custom Functions: 0') > 0
        # No orbital info
        assert self.out.find('Orbit Settings') < 0
        # Files exist for test inst
        assert self.out.find('Date Range:') > 0
        # No loaded data
        assert self.out.find('No loaded data') > 0
        assert self.out.find('Number of variables') < 0
        assert self.out.find('uts') < 0
        return

    def test_str_w_orbit(self):
        """Test string output with Orbit data."""

        reload(pysat.instruments.pysat_testing)
        orbit_info = {'index': 'mlt',
                      'kind': 'local time',
                      'period': np.timedelta64(97, 'm')}
        testInst = pysat.Instrument(platform='pysat', name='testing',
                                    num_samples=10,
                                    clean_level='clean',
                                    update_files=True,
                                    orbit_info=orbit_info)

        self.out = testInst.__str__()

        # Check that orbit info is passed through
        assert self.out.find('Orbit Settings') > 0
        assert self.out.find(orbit_info['kind']) > 0
        assert self.out.find('Loaded Orbit Number: 0') > 0

        # Activate orbits, check that message has changed
        testInst.load(self.ref_time.year, self.ref_doy)
        testInst.orbits.next()
        self.out = testInst.__str__()
        assert self.out.find('Loaded Orbit Number: 1') > 0
        return

    def test_str_w_padding(self):
        """Test string output with data padding."""

        self.testInst.pad = dt.timedelta(minutes=5)
        self.out = self.testInst.__str__()
        assert self.out.find('Data Padding: 0:05:00') > 0
        return

    def test_str_w_custom_func(self):
        """Test string output with custom function."""

        def passfunc(self):
            pass
        self.testInst.custom_attach(passfunc)
        self.out = self.testInst.__str__()
        assert self.out.find('passfunc') > 0
        return

    def test_str_w_load_lots_data(self):
        """Test string output with loaded data."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = self.testInst.__str__()
        assert self.out.find('Number of variables:') > 0
        assert self.out.find('...') > 0
        return

    def test_str_w_load_less_data(self):
        """Test string output with loaded data."""

        # Load the test data
        self.testInst.load(self.ref_time.year, self.ref_doy)

        # Ensure the desired data variable is present and delete all others
        # 4-6 variables are needed to test all lines; choose the lesser limit
        nvar = 4
        self.testInst.data = self.testInst.data[self.testInst.variables[:nvar]]

        # Test output with one data variable
        self.out = self.testInst.__str__()
        assert self.out.find('Number of variables: 4') > 0
        assert self.out.find('Variable Names') > 0
        for n in range(nvar):
            assert self.out.find(self.testInst.variables[n]) > 0
        return

    # -------------------------------------------------------------------------
    #
    # test instrument initialization functions
    #
    # -------------------------------------------------------------------------
    def test_instrument_init(self):
        """Test if init function supplied by instrument can modify object."""

        assert self.testInst.new_thing
        return

    def test_custom_instrument_load(self):
        """Test if the correct day is being loaded with routines."""

        import pysat.instruments.pysat_testing as test
        self.out = pysat.Instrument(inst_module=test, tag='',
                                    clean_level='clean')
        self.ref_time = dt.datetime(2009, 2, 1)
        self.ref_doy = 32
        self.out.load(self.ref_time.year, self.ref_doy)
        assert self.out.date == self.ref_time
        return

    @pytest.mark.parametrize('del_routine', ['list_files', 'load'])
    def test_custom_instrument_load_incomplete(self, del_routine):
        """Test if exception is thrown if supplied routines are incomplete."""

        import pysat.instruments.pysat_testing as test
        delattr(test, del_routine)

        with pytest.raises(AttributeError) as aerr:
            pysat.Instrument(inst_module=test, tag='',
                             clean_level='clean')
        estr = 'A `{:}` function is required'.format(del_routine)
        assert str(aerr).find(estr) >= 0
        return

    # -------------------------------------------------------------------------
    #
    # test instrument initialization keyword mapping to instrument functions
    #
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("func, kwarg, val", [('init', 'test_init_kwarg',
                                                   True),
                                                  ('clean', 'test_clean_kwarg',
                                                   False),
                                                  ('preprocess',
                                                   'test_preprocess_kwarg',
                                                   'test_phrase'),
                                                  ('load', 'test_load_kwarg',
                                                   'bright_light'),
                                                  ('list_files',
                                                   'test_list_files_kwarg',
                                                   'sleep_tight'),
                                                  ('list_remote_files',
                                                   'test_list_remote_kwarg',
                                                   'one_eye_open'),
                                                  ('download',
                                                   'test_download_kwarg',
                                                   'exit_night')
                                                  ])
    def test_instrument_function_keywords(self, func, kwarg, val, caplog):
        """Test if Instrument function keywords are registered by pysat."""

        with caplog.at_level(logging.INFO, logger='pysat'):
            # Trigger load functions
            self.testInst.load(date=self.ref_time)

            # Refresh files to trigger other functions
            self.testInst.files.refresh()

            # Get remote file list
            self.testInst.download_updated_files()

        # Confirm kwargs made it where they should be
        assert kwarg in self.testInst.kwargs[func]
        assert self.testInst.kwargs[func][kwarg] == val

        # Check if function under test can assign attributes, not all can
        live_check = hasattr(self.testInst, kwarg)

        if live_check:
            # Confirm attribute value
            assert getattr(self.testInst, kwarg) == val
        else:
            # Confirm value echoed to log for functions that can't assign
            # attributes. Get log text.
            captured = caplog.text

            # Test for expected string
            test_str = ''.join((kwarg, ' = ', str(val)))
            assert captured.find(test_str) >= 0

        return

    @pytest.mark.parametrize("func, kwarg", [('clean', 'test_clean_kwarg'),
                                             ('preprocess',
                                              'test_preprocess_kwarg'),
                                             ('load',
                                              'test_load_kwarg'),
                                             ('list_files',
                                              'test_list_files_kwarg'),
                                             ('list_files',
                                              'test_list_files_kwarg'),
                                             ('list_remote_files',
                                              'test_list_remote_kwarg'),
                                             ('download',
                                              'test_download_kwarg')
                                             ])
    def test_instrument_function_keyword_liveness(self, func, kwarg, caplog):
        """Test if changed keywords are propagated by pysat to functions."""

        # Assign a new value to a keyword argument
        val = 'live_value'
        self.testInst.kwargs[func][kwarg] = val

        with caplog.at_level(logging.INFO, logger='pysat'):
            # Trigger load functions
            self.testInst.load(date=self.ref_time)

            # Refresh files to trigger other functions
            self.testInst.files.refresh()

            # Get remote file list
            self.testInst.download_updated_files()

        # The passed parameter should be set on Instrument, if a full function
        live_check = hasattr(self.testInst, kwarg)

        # Not all functions are passed the instrument object
        if live_check:
            # Confirm attribute value
            assert getattr(self.testInst, kwarg) == val
        else:
            # Confirm value echoed to log for functions that can't assign
            # attributes.
            captured = caplog.text

            # Confirm presence of test string in log
            test_str = ''.join((kwarg, ' = ', str(val)))
            assert captured.find(test_str) >= 0

        return

    def test_error_undefined_input_keywords(self):
        """Test for error if undefined keywords provided at instantiation."""

        # Add a new keyword
        self.testInst.kwargs['load']['undefined_keyword1'] = True
        self.testInst.kwargs['load']['undefined_keyword2'] = False

        with pytest.raises(ValueError) as err:
            # Instantiate instrument with new undefined keyword involved
            eval(self.testInst.__repr__())

        estr = "".join(("unknown keywords supplied: ['undefined_keyword1',",
                        " 'undefined_keyword2']"))
        assert str(err).find(estr) >= 0
        return

    def test_supported_input_keywords(self):
        """Test that supported keywords exist."""

        funcs = ['load', 'init', 'list_remote_files', 'list_files', 'download',
                 'preprocess', 'clean']

        # Test instruments all have a supported keyword. Ensure keyword
        # present for all functions.
        for func in funcs:
            assert func in self.testInst.kwargs_supported
            assert len(self.testInst.kwargs_supported[func]) > 0

        # Confirm all user provided keywords are in the supported keywords
        for func in funcs:
            for kwarg in self.testInst.kwargs[func]:
                assert kwarg in self.testInst.kwargs_supported[func]

        return

    # -------------------------------------------------------------------------
    #
    # Test basic data access features, both getting and setting data
    #
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("labels", [('mlt'),
                                        (['mlt', 'longitude']),
                                        (['longitude', 'mlt'])])
    def test_basic_data_access_by_name(self, labels):
        """Check that data can be accessed at the instrument level."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all((self.testInst[labels]
                       == self.testInst.data[labels]).values)
        return

    @pytest.mark.parametrize("index", [(0),
                                       ([0, 1, 2, 3]),
                                       (slice(0, 10)),
                                       (np.arange(0, 10))])
    def test_data_access_by_indices_and_name(self, index):
        """Check that variables and be accessed by each supported index type."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[index, 'mlt']
                      == self.testInst.data['mlt'][index])
        return

    def test_data_access_by_row_slicing_and_name_slicing(self):
        """Check that each variable is downsampled."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        result = self.testInst[0:10, :]
        for variable, array in result.items():
            assert len(array) == len(self.testInst.data[variable].values[0:10])
            assert np.all(array == self.testInst.data[variable].values[0:10])
        return

    def test_data_access_by_datetime_and_name(self):
        """Check that datetime can be used to access data."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = dt.datetime(2009, 1, 1, 0, 0, 0)
        assert np.all(self.testInst[self.out, 'uts']
                      == self.testInst.data['uts'].values[0])
        return

    def test_data_access_by_datetime_slicing_and_name(self):
        """Check that a slice of datetimes can be used to access data."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        time_step = (self.testInst.index[1]
                     - self.testInst.index[0]).value / 1.E9
        offset = dt.timedelta(seconds=(10 * time_step))
        start = dt.datetime(2009, 1, 1, 0, 0, 0)
        stop = start + offset
        assert np.all(self.testInst[start:stop, 'uts']
                      == self.testInst.data['uts'].values[0:11])
        return

    def test_setting_data_by_name(self):
        """Test setting data by name."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])
        return

    def test_setting_series_data_by_name(self):
        """Test setting series data by name."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = \
            2. * pds.Series(self.testInst['mlt'].values,
                            index=self.testInst.index)
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])

        self.testInst['blankMLT'] = pds.Series(None, dtype='float64')
        assert np.all(np.isnan(self.testInst['blankMLT']))
        return

    def test_setting_pandas_dataframe_by_names(self):
        """Test setting pandas dataframe by name."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst[['doubleMLT', 'tripleMLT']] = \
            pds.DataFrame({'doubleMLT': 2. * self.testInst['mlt'].values,
                           'tripleMLT': 3. * self.testInst['mlt'].values},
                          index=self.testInst.index)
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])
        assert np.all(self.testInst['tripleMLT'] == 3. * self.testInst['mlt'])
        return

    def test_setting_data_by_name_single_element(self):
        """Test setting data by name for a single element."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2.
        assert np.all(self.testInst['doubleMLT'] == 2.)

        self.testInst['nanMLT'] = np.nan
        assert np.all(np.isnan(self.testInst['nanMLT']))
        return

    def test_setting_data_by_name_with_meta(self):
        """Test setting data by name with meta."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = {'data': 2. * self.testInst['mlt'],
                                      'units': 'hours',
                                      'long_name': 'double trouble'}
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])
        assert self.testInst.meta['doubleMLT'].units == 'hours'
        assert self.testInst.meta['doubleMLT'].long_name == 'double trouble'
        return

    def test_setting_partial_data(self):
        """Test setting partial data by index."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = self.testInst
        if self.testInst.pandas_format:
            self.testInst[0:3] = 0
            # First three values should be changed.
            assert np.all(self.testInst[0:3] == 0)
            # Other data should be unchanged.
            assert np.all(self.testInst[3:] == self.out[3:])
        else:
            pytest.skip("This notation does not make sense for xarray")
        return

    @pytest.mark.parametrize("changed,fixed",
                             [(0, slice(1, None)),
                              ([0, 1, 2, 3], slice(4, None)),
                              (slice(0, 10), slice(10, None)),
                              (np.array([0, 1, 2, 3]), slice(4, None)),
                              (dt.datetime(2009, 1, 1), slice(1, None)),
                              (slice(dt.datetime(2009, 1, 1),
                                     dt.datetime(2009, 1, 1, 0, 1)),
                               slice(dt.datetime(2009, 1, 1, 0, 1), None))])
    def test_setting_partial_data_by_inputs(self, changed, fixed):
        """Check that data can be set using each supported input type."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[changed, 'doubleMLT'] = 0
        assert (self.testInst[fixed, 'doubleMLT']
                == 2. * self.testInst[fixed, 'mlt']).all
        assert (self.testInst[changed, 'doubleMLT'] == 0).all
        return

    def test_modifying_data_inplace(self):
        """Test modification of data inplace."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst['doubleMLT'] += 100
        assert (self.testInst['doubleMLT']
                == 2. * self.testInst['mlt'] + 100).all
        return

    @pytest.mark.parametrize("index", [([0, 1, 2, 3, 4]),
                                       (np.array([0, 1, 2, 3, 4]))])
    def test_getting_all_data_by_index(self, index):
        """Test getting all data by index."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        a = self.testInst[index]
        if self.testInst.pandas_format:
            assert len(a) == len(index)
        else:
            assert a.sizes[xarray_epoch_name] == len(index)
        return

    # -------------------------------------------------------------------------
    #
    # Test variable renaming
    #
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("values", [{'uts': 'uts1'},
                                        {'uts': 'uts2',
                                         'mlt': 'mlt2'},
                                        {'uts': 'long change with spaces'}])
    def test_basic_variable_renaming(self, values):
        """Test basic variable renaming."""

        # test single variable
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.rename(values)
        for key in values:
            # check for new name
            assert values[key] in self.testInst.data
            assert values[key] in self.testInst.meta
            # ensure old name not present
            assert key not in self.testInst.data
            assert key not in self.testInst.meta
        return

    @pytest.mark.parametrize("values", [{'help': 'I need somebody'},
                                        {'UTS': 'litte_uts'},
                                        {'utS': 'uts1'},
                                        {'utS': 'uts'}])
    def test_unknown_variable_error_renaming(self, values):
        """Test that unknown variable renaming raises an error."""

        # check for error for unknown variable name
        self.testInst.load(self.ref_time.year, self.ref_doy)
        with pytest.raises(ValueError) as verr:
            self.testInst.rename(values)
        assert str(verr).find("cannot rename") >= 0
        return

    @pytest.mark.parametrize("values", [{'uts': 'UTS1'},
                                        {'uts': 'UTs2',
                                         'mlt': 'Mlt2'},
                                        {'uts': 'Long Change with spaces'}])
    def test_basic_variable_renaming_lowercase(self, values):
        """Test new variable names are converted to lowercase."""

        # test single variable
        self.testInst.load(self.ref_time.year, self.ref_doy)
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
        return

    @pytest.mark.parametrize("values", [{'profiles': {'density': 'ionization'}},
                                        {'profiles': {'density': 'mass'},
                                         'alt_profiles':
                                             {'density': 'volume'}}])
    def test_ho_pandas_variable_renaming(self, values):
        """Test rename of higher order pandas variable."""

        # check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(self.ref_time.year, self.ref_doy)
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
        return

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
        """Test higher order pandas variable rename raises error if unknown."""

        # check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(self.ref_time.year, self.ref_doy)
                # check for error for unknown column or HO variable name
                with pytest.raises(ValueError) as verr:
                    self.testInst.rename(values)
                assert str(verr).find("cannot rename") >= 0
            else:
                pytest.skip("Not implemented for this instrument")
        return

    @pytest.mark.parametrize("values", [{'profiles': {'density': 'Ionization'}},
                                        {'profiles': {'density': 'MASa'},
                                         'alt_profiles':
                                             {'density': 'VoLuMe'}}])
    def test_ho_pandas_variable_renaming_lowercase(self, values):
        """Test rename higher order pandas variable uses lowercase."""

        # check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(self.ref_time.year, self.ref_doy)
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
        return

    # -------------------------------------------------------------------------
    #
    # Test iteration behaviors
    #
    # -------------------------------------------------------------------------
    def test_list_comprehension(self):
        """Test list comprehensions for length, uniqueness, iteration."""

        self.testInst.bounds = (self.testInst.files.files.index[0],
                                self.testInst.files.files.index[9])
        # ensure no data to begin
        assert self.testInst.empty
        # perform comprehension and ensure there are as many as there should be
        insts = [inst for inst in self.testInst]
        assert len(insts) == 10
        # get list of dates
        dates = pds.Series([inst.date for inst in insts])
        assert dates.is_monotonic_increasing
        # dates are unique
        assert np.all(np.unique(dates) == dates.values)
        # iteration instruments are not the same as original
        for inst in insts:
            assert not (inst is self.testInst)
        # check there is data after iteration
        assert not self.testInst.empty

        return

    @pytest.mark.parametrize("first,second", [('next', 'prev'),
                                              ('prev', 'next')])
    def test_passing_bounds_with_orbit_iteration(self, first, second):
        """Test if passing bounds raises StopIteration."""

        # load first data
        getattr(self.testInst, first)()
        with pytest.raises(StopIteration) as err:
            # Iterate to a day outside the bounds.
            getattr(self.testInst, second)()
        assert str(err).find("Outside the set date boundaries") >= 0
        return

    def test_set_bounds_with_frequency(self):
        """Test setting bounds with non-default step."""

        start = self.ref_time
        stop = self.ref_time + dt.timedelta(days=14)
        self.testInst.bounds = (start, stop, 'M')
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='M').tolist())
        return

    def test_iterate_bounds_with_frequency(self):
        """Test iterating bounds with non-default step."""

        start = self.ref_time
        stop = self.ref_time + dt.timedelta(days=15)
        self.testInst.bounds = (start, stop, '2D')
        self.eval_iter_list(start, stop, dates=True, freq=2)
        return

    def test_set_bounds_with_frequency_and_width(self):
        """Set date bounds with step/width > 1."""

        start = self.ref_time
        stop = self.ref_time + pds.DateOffset(months=11, days=25)
        stop = stop.to_pydatetime()
        self.testInst.bounds = (start, stop, '10D', dt.timedelta(days=10))
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='10D').tolist())
        return

    def verify_inclusive_iteration(self, out, reverse=False):
        """Verify loaded dates for inclusive iteration, forward or backward."""

        # Verify range of loaded data when iterating forward.
        for i, trange in enumerate(out['observed_times']):
            # Determine which range we are in.
            b_range = 0
            while out['expected_times'][i] > out['stops'][b_range]:
                b_range += 1
            # Check loaded range is correct.
            assert trange[0] == out['expected_times'][i], \
                "Did not load the expected start time"

            check = out['expected_times'][i] + out['width']
            check -= dt.timedelta(days=1)
            assert trange[1] > check, "End time outside of expected range"

            check = out['stops'][b_range] + dt.timedelta(days=1)
            assert trange[1] < check, "End time outside of expected range"

            if reverse:
                if i == 0:
                    # Check first load is before end of bounds.
                    check = out['stops'][b_range] - out['width']
                    check += dt.timedelta(days=1)
                    assert trange[0] == check
                    assert trange[1] > out['stops'][b_range]
                    check = out['stops'][b_range] + dt.timedelta(days=1)
                    assert trange[1] < check
                elif i == len(out['observed_times']) - 1:
                    # last load at start of bounds
                    assert trange[0] == out['starts'][b_range]
                    assert trange[1] > out['starts'][b_range]
                    assert trange[1] < out['starts'][b_range] + out['width']

        return

    def verify_exclusive_iteration(self, out, reverse=False):
        """Verify loaded dates for exclusive iteration, forward or backward."""

        # Verify range of loaded data.
        for i, trange in enumerate(out['observed_times']):
            # Determine the current range.
            b_range = 0
            while out['expected_times'][i] > out['stops'][b_range]:
                b_range += 1

            # Check to see if the loaded range is correct.
            assert trange[0] == out['expected_times'][i], \
                "Loaded start time is not correct"
            check = out['expected_times'][i] + out['width']
            check -= dt.timedelta(days=1)
            assert trange[1] > check

            if not reverse:
                assert trange[1] < out['stops'][b_range]
            else:
                check = out['stops'][b_range] + dt.timedelta(days=1)
                assert trange[1] < check
                if i == 0:
                    # check first load is before end of bounds
                    check = out['stops'][b_range] - out['width']
                    check += dt.timedelta(days=1)
                    assert trange[0] < check
                    assert trange[1] < out['stops'][b_range]
                elif i == len(out['observed_times']) - 1:
                    # last load at start of bounds
                    assert trange[0] == out['starts'][b_range]
                    assert trange[1] > out['starts'][b_range]
                    assert trange[1] < out['starts'][b_range] + out['width']

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 3),
                                         2, 2),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4),
                                         2, 3),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5),
                                         3, 1),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 17),
                                         5, 1)
                                        ])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_bounds_with_frequency_and_width(self, values, by_date):
        """Test iterate via date with mixed step/width, excludes stop date."""

        out = self.support_iter_evaluations(values, for_loop=True,
                                            by_date=by_date)
        self.verify_exclusive_iteration(out, reverse=False)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4),
                                         2, 2),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4),
                                         3, 1),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4),
                                         1, 4),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5),
                                         4, 1),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5),
                                         2, 3),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5),
                                         3, 2)])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_bounds_with_frequency_and_width_incl(self, values,
                                                          by_date):
        """Test iterate via date with mixed step/width, includes stop date."""

        out = self.support_iter_evaluations(values, for_loop=True,
                                            by_date=by_date)
        self.verify_inclusive_iteration(out, reverse=False)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 10),
                                         2, 2),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 9),
                                         4, 1),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11),
                                         1, 3),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11),
                                         1, 11),
                                        ])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_with_frequency_and_width_incl(self, values, reverse,
                                                   by_date):
        """Test iteration via date step/width >1, includes stop date."""

        out = self.support_iter_evaluations(values, reverse=reverse,
                                            by_date=by_date)
        self.verify_inclusive_iteration(out, reverse=reverse)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11),
                                         2, 2),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 12),
                                         2, 3),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 13),
                                         3, 2),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 3),
                                         4, 2),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 12),
                                         2, 1)])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_with_frequency_and_width(self, values, reverse, by_date):
        """Test iteration via date step/width > 1, exclude stop date."""

        out = self.support_iter_evaluations(values, reverse=reverse,
                                            by_date=by_date)
        self.verify_exclusive_iteration(out, reverse=reverse)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 13)),
                                         2, 2),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         3, 1),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         2, 4)
                                        ])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_season_frequency_and_width_incl(self, values, reverse,
                                                     by_date):
        """Test iteration via date season step/width > 1, include stop date."""

        out = self.support_iter_evaluations(values, reverse=reverse,
                                            by_date=by_date)
        self.verify_inclusive_iteration(out, reverse=reverse)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 12)),
                                         2, 2),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         3, 1),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         2, 4)
                                        ])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_season_frequency_and_width(self, values, reverse,
                                                by_date):
        """Test iteration via date season step/width>1, exclude stop date."""

        out = self.support_iter_evaluations(values, reverse=reverse,
                                            by_date=by_date)
        self.verify_exclusive_iteration(out, reverse=reverse)

        return

    @pytest.mark.parametrize("new_bounds,errmsg",
                             [([dt.datetime(2009, 1, 1)],
                               "Must supply both a start and stop date/file"),
                              ([dt.datetime(2009, 1, 1), '2009-01-01.nofile'],
                               "must all be of the same type"),
                              ([dt.datetime(2009, 1, 1), 1],
                               "must all be of the same type"),
                              ([[dt.datetime(2009, 1, 1)] * 2,
                                '2009-01-01.nofile'],
                               "must have the same number of elements"),
                              ([[dt.datetime(2009, 1, 1)] * 2,
                               [dt.datetime(2009, 1, 1), '2009-01-01.nofile']],
                               "must all be of the same type"),
                              ([dt.datetime(2009, 1, 1),
                                dt.datetime(2009, 1, 1), '1D',
                                dt.timedelta(days=1), False],
                               'Too many input arguments.')])
    def test_set_bounds_error_message(self, new_bounds, errmsg):
        """Test ValueError when setting bounds with wrong inputs."""

        with pytest.raises(ValueError) as verr:
            self.testInst.bounds = new_bounds
        assert str(verr).find(errmsg) >= 0
        return

    def test_set_bounds_string_default_start(self):
        """Test set bounds with default start."""

        self.testInst.bounds = [None, '2009-01-01.nofile']
        assert self.testInst.bounds[0][0] == self.testInst.files[0]
        return

    def test_set_bounds_string_default_stop(self):
        """Test set bounds with default stop."""

        self.testInst.bounds = ['2009-01-01.nofile', None]
        assert self.testInst.bounds[1][0] == self.testInst.files[-1]
        return

    def test_set_bounds_by_default_dates(self):
        """Verify bounds behavior with default date related inputs."""

        start = self.testInst.files.start_date
        stop = self.testInst.files.stop_date
        full_list = pds.date_range(start, stop).tolist()
        self.testInst.bounds = (None, None)
        assert np.all(self.testInst._iter_list == full_list)
        self.testInst.bounds = None
        assert np.all(self.testInst._iter_list == full_list)
        self.testInst.bounds = (start, None)
        assert np.all(self.testInst._iter_list == full_list)
        self.testInst.bounds = (None, stop)
        assert np.all(self.testInst._iter_list == full_list)
        return

    @pytest.mark.parametrize("start,stop", [(dt.datetime(2009, 1, 1),
                                             dt.datetime(2009, 1, 15)),
                                            ([dt.datetime(2009, 1, 1),
                                              dt.datetime(2009, 2, 1)],
                                             [dt.datetime(2009, 1, 15),
                                              dt.datetime(2009, 2, 15)])])
    def test_set_bounds_by_date(self, start, stop):
        """Test setting bounds with datetimes over simple range and season."""

        self.testInst.bounds = (start, stop)
        self.eval_iter_list(start, stop)
        return

    @pytest.mark.parametrize("start,stop", [(dt.datetime(2009, 1, 15),
                                             dt.datetime(2009, 1, 1)),
                                            ([dt.datetime(2009, 1, 1),
                                              dt.datetime(2009, 2, 1)],
                                             [dt.datetime(2009, 1, 12),
                                              dt.datetime(2009, 1, 15)])])
    def test_set_bounds_by_date_wrong_order(self, start, stop):
        """Test error if bounds assignment has stop date before start."""

        with pytest.raises(Exception) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be set in increasing'
        assert str(err).find(estr) >= 0
        return

    @pytest.mark.parametrize(
        "start,stop", [(dt.datetime(2009, 1, 1, 1, 10),
                        dt.datetime(2009, 1, 15, 1, 10)),
                       ([dt.datetime(2009, 1, 1, 1, 10),
                         dt.datetime(2009, 2, 1, 1, 10)],
                        [dt.datetime(2009, 1, 15, 1, 10),
                         dt.datetime(2009, 2, 15, 1, 10)])])
    def test_set_bounds_by_date_extra_time(self, start, stop):
        """Test set bounds by date with extra time."""

        self.testInst.bounds = (start, stop)
        start = filter_datetime_input(start)
        stop = filter_datetime_input(stop)
        self.eval_iter_list(start, stop)
        return

    @pytest.mark.parametrize("start,stop", [(dt.datetime(2010, 12, 1),
                                             dt.datetime(2010, 12, 31)),
                                            (dt.datetime(2009, 1, 1),
                                             dt.datetime(2009, 1, 15)),
                                            ([dt.datetime(2009, 1, 1),
                                              dt.datetime(2009, 2, 1)],
                                             [dt.datetime(2009, 1, 15),
                                              dt.datetime(2009, 2, 15)]),
                                            ([dt.datetime(2009, 1, 1, 1, 10),
                                              dt.datetime(2009, 2, 1, 1, 10)],
                                             [dt.datetime(2009, 1, 15, 1, 10),
                                              dt.datetime(2009, 2, 15, 1, 10)])
                                            ])
    def test_iterate_over_bounds_set_by_date(self, start, stop):
        """Test iterate over bounds via single date range."""

        self.testInst.bounds = (start, stop)
        # Filter time inputs.
        start = filter_datetime_input(start)
        stop = filter_datetime_input(stop)
        self.eval_iter_list(start, stop, dates=True)
        return

    def test_iterate_over_default_bounds(self):
        """Test iterate over default bounds."""

        date_range = pds.date_range(self.ref_time,
                                    self.ref_time + dt.timedelta(days=10))
        self.testInst.kwargs['list_files']['file_date_range'] = date_range
        self.testInst.files.refresh()
        self.testInst.bounds = (None, None)
        self.eval_iter_list(date_range[0], date_range[-1], dates=True)
        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 12)),
                                         2, 2),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         3, 1),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         2, 4)
                                        ])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_over_bounds_season_step_width(self, values, by_date):
        """Test iterate over season, step/width > 1, exclude stop bounds."""

        out = self.support_iter_evaluations(values, for_loop=True,
                                            by_date=by_date)

        self.verify_exclusive_iteration(out, reverse=False)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 13)),
                                         2, 2),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         3, 1),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         2, 4)
                                        ])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_bounds_season_step_width_incl(self, values, by_date):
        """Test iterate over season, step/width > 1, includes stop bounds."""

        out = self.support_iter_evaluations(values, for_loop=True,
                                            by_date=by_date)
        self.verify_inclusive_iteration(out, reverse=False)

        return

    def test_set_bounds_by_fname(self):
        """Test set bounds by fname."""

        start = '2009-01-01.nofile'
        stop = '2009-01-03.nofile'
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list
                      == ['2009-01-01.nofile', '2009-01-02.nofile',
                          '2009-01-03.nofile'])
        return

    def test_iterate_over_bounds_set_by_fname(self):
        """Test iterate over bounds set by fname."""

        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1)
        stop_d = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        self.eval_iter_list(start_d, stop_d, dates=True)
        return

    @pytest.mark.parametrize("start,stop", [('2009-01-13.nofile',
                                             '2009-01-01.nofile'),
                                            (['2009-01-01.nofile',
                                              '2009-02-03.nofile'],
                                             ['2009-01-03.nofile',
                                              '2009-02-01.nofile'])])
    def test_set_bounds_by_fname_wrong_order(self, start, stop):
        """Test for error if stop file before start file."""

        with pytest.raises(Exception) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be in increasing date'
        assert str(err).find(estr) >= 0
        return

    @pytest.mark.parametrize("operator", ['next', 'prev'])
    def test_iterate_over_bounds_set_by_fname_via_attr(self, operator):
        """Test iterate over bounds set by fname via operators."""

        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1)
        stop_d = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        dates = []
        loop_next = True
        while loop_next:
            try:
                getattr(self.testInst, operator)()
                dates.append(self.testInst.date)
            except StopIteration:
                loop_next = False
        out = pds.date_range(start_d, stop_d).tolist()
        pysat.utils.testing.assert_lists_equal(dates, out)
        return

    def test_set_bounds_by_fname_season(self):
        """Test set bounds by fname season."""

        start = ['2009-01-01.nofile', '2009-02-01.nofile']
        stop = ['2009-01-03.nofile', '2009-02-03.nofile']
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list
                      == ['2009-01-01.nofile', '2009-01-02.nofile',
                          '2009-01-03.nofile', '2009-02-01.nofile',
                          '2009-02-02.nofile', '2009-02-03.nofile'])
        return

    def test_iterate_over_bounds_set_by_fname_season(self):
        """Test set bounds using multiple filenames."""

        start = ['2009-01-01.nofile', '2009-02-01.nofile']
        stop = ['2009-01-15.nofile', '2009-02-15.nofile']
        start_d = [dt.datetime(2009, 1, 1), dt.datetime(2009, 2, 1)]
        stop_d = [dt.datetime(2009, 1, 15), dt.datetime(2009, 2, 15)]
        self.testInst.bounds = (start, stop)
        self.eval_iter_list(start_d, stop_d, dates=True)
        return

    def test_set_bounds_fname_with_frequency(self):
        """Test set bounds using filenames and non-default step."""

        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3)
        self.testInst.bounds = (start, stop, 2)
        out = pds.date_range(start_date, stop_date, freq='2D').tolist()

        # Convert filenames in list to a date
        for i, item in enumerate(self.testInst._iter_list):
            snip = item.split('.')[0]
            ref_snip = out[i].strftime('%Y-%m-%d')
            assert snip == ref_snip
        return

    def test_iterate_bounds_fname_with_frequency(self):
        """Test iterate over bounds using filenames and non-default step."""

        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3)
        self.testInst.bounds = (start, stop, 2)

        self.eval_iter_list(start_date, stop_date, dates=True, freq=2)
        return

    def test_set_bounds_fname_with_frequency_and_width(self):
        """Test set fname bounds with step/width > 1."""

        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3)
        self.testInst.bounds = (start, stop, 2, 2)
        out = pds.date_range(start_date, stop_date - dt.timedelta(days=1),
                             freq='2D').tolist()
        # convert filenames in list to a date
        date_list = []
        for item in self.testInst._iter_list:
            snip = item.split('.')[0]
            date_list.append(dt.datetime.strptime(snip, '%Y-%m-%d'))
        assert np.all(date_list == out)
        return

    def test_creating_empty_instrument_object(self):
        """Ensure empty Instrument instantiation runs."""

        null = pysat.Instrument()
        assert isinstance(null, pysat.Instrument)
        return

    def test_incorrect_creation_empty_instrument_object(self):
        """Ensure instantiation with missing name errors."""

        with pytest.raises(ValueError) as err:
            # Both name and platform should be empty
            pysat.Instrument(platform='cnofs')
        estr = 'Inputs platform and name must both'
        assert str(err).find(estr) >= 0
        return

    @pytest.mark.parametrize(
        "kwargs,estr",
        [({'inst_id': 'invalid_inst_id'},
          "'invalid_inst_id' is not one of the supported inst_ids."),
         ({'inst_id': '', 'tag': 'bad_tag'},
          "'bad_tag' is not one of the supported tags.")])
    def test_error_bad_instrument_object(self, kwargs, estr):
        """Ensure instantiation with invalid inst_id or tag errors."""

        with pytest.raises(ValueError) as err:
            pysat.Instrument(platform=self.testInst.platform,
                             name=self.testInst.name,
                             **kwargs)
        assert str(err).find(estr) >= 0
        return

    def test_supplying_instrument_module_requires_name_and_platform(self):
        """Ensure instantiation via inst_module with missing name errors."""

        class Dummy(object):
            pass
        Dummy.name = 'help'

        with pytest.raises(AttributeError) as err:
            pysat.Instrument(inst_module=Dummy)
        estr = 'Supplied module '
        assert str(err).find(estr) >= 0
        return

    def test_get_var_type_code_unknown_type(self):
        """Ensure that Error is thrown if unknown type is supplied."""

        with pytest.raises(TypeError) as err:
            self.testInst._get_var_type_code(type(None))
        estr = 'Unknown Variable'
        assert str(err).find(estr) >= 0
        return


class TestBasicsInstModule(TestBasics):
    """Basic tests for instrument instantiated via inst_module."""

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        imod = pysat.instruments.pysat_testing
        self.testInst = pysat.Instrument(inst_module=imod,
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = imod._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


# -----------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# -----------------------------------------------------------------------------
class TestBasicsXarray(TestBasics):
    """Basic tests for xarray `pysat.Instrument`."""

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = \
            pysat.instruments.pysat_testing_xarray._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


class TestBasics2D(TestBasics):
    """Basic tests for 2D pandas `pysat.Instrument`."""

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing2d)
        self.testInst = pysat.Instrument(platform='pysat', name='testing2d',
                                         num_samples=50,
                                         clean_level='clean',
                                         update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing2d._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


class TestBasics2DXarray(TestBasics):
    """Basic tests for 2D xarray `pysat.Instrument`.

    Note
    ----
    Includes additional tests for multidimensional objects.
    """

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing2d_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing2d_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = \
            pysat.instruments.pysat_testing2d_xarray._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return

    @pytest.mark.parametrize("index", [(0),
                                       ([0, 1, 2, 3]),
                                       (slice(0, 10)),
                                       (np.array([0, 1, 2, 3]))])
    def test_data_access_by_2d_indices_and_name(self, index):
        """Check that variables and be accessed by each supported index type."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[index, index, 'profiles']
                      == self.testInst.data['profiles'][index, index])
        return

    def test_data_access_by_2d_tuple_indices_and_name(self):
        """Check that variables and be accessed by multi-dim tuple index."""

        self.testInst.load(date=self.ref_time)
        index = ([0, 1, 2, 3], [0, 1, 2, 3])
        assert np.all(self.testInst[index, 'profiles']
                      == self.testInst.data['profiles'][index[0], index[1]])
        return

    def test_data_access_bad_dimension_tuple(self):
        """Test raises ValueError for mismatched tuple index and data dims."""

        self.testInst.load(date=self.ref_time)
        index = ([0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3])

        with pytest.raises(ValueError) as verr:
            self.testInst[index, 'profiles']

        estr = 'not convert tuple'
        assert str(verr).find(estr) > 0
        return

    def test_data_access_bad_dimension_for_multidim(self):
        """Test raises ValueError for mismatched index and data dimensions."""

        self.testInst.load(date=self.ref_time)
        index = [0, 1, 2, 3]

        with pytest.raises(ValueError) as verr:
            self.testInst[index, index, index, 'profiles']

        estr = "don't match data"
        assert str(verr).find(estr) > 0
        return

    @pytest.mark.parametrize("changed,fixed",
                             [(0, slice(1, None)),
                              ([0, 1, 2, 3], slice(4, None)),
                              (slice(0, 10), slice(10, None)),
                              (np.array([0, 1, 2, 3]), slice(4, None))])
    def test_setting_partial_data_by_2d_indices_and_name(self, changed, fixed):
        """Check that data can be set using each supported index type."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleProfile'] = 2. * self.testInst['profiles']
        self.testInst[changed, changed, 'doubleProfile'] = 0
        assert np.all(np.all(self.testInst[fixed, fixed, 'doubleProfile']
                             == 2. * self.testInst[fixed, 'profiles']))
        assert np.all(np.all(self.testInst[changed, changed, 'doubleProfile']
                             == 0))
        return


class TestBasicsShiftedFileDates(TestBasics):
    """Basic tests for pandas `pysat.Instrument` with shifted file dates."""

    def setup(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         mangle_file_dates=True,
                                         strict_time_flag=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


class TestDeprecation(object):
    """Unit test for deprecation warnings."""

    def setup(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        self.in_kwargs = {"platform": 'pysat', "name": 'testing',
                          "clean_level": 'clean'}
        self.warn_msgs = ["".join(["`pysat.Instrument.download` kwarg `freq` ",
                                   "has been deprecated and will be removed ",
                                   "in pysat 3.2.0+"])]
        self.warn_msgs = np.array(self.warn_msgs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.in_kwargs, self.warn_msgs, self.ref_time
        return

    def test_download_freq_kwarg(self):
        """Test deprecation of download kwarg `freq`."""

        # Catch the warnings
        with warnings.catch_warnings(record=True) as war:
            tinst = pysat.Instrument(**self.in_kwargs)
            tinst.download(start=self.ref_time, freq='D')

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        found_msgs = pysat.instruments.methods.testing.eval_dep_warnings(
            war, self.warn_msgs)

        for i, good in enumerate(found_msgs):
            assert good, "didn't find warning about: {:}".format(
                self.warn_msgs[i])

        return
