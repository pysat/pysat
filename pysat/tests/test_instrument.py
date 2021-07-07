# -*- coding: utf-8 -*-
# Test some of the basic _core functions
import datetime as dt
from importlib import reload
import logging
import numpy as np

import pandas as pds
import pytest
import xarray as xr

import pysat
import pysat.instruments.pysat_testing
import pysat.instruments.pysat_testing_xarray
import pysat.instruments.pysat_testing2d
import pysat.instruments.pysat_testing2d_xarray
from pysat.utils import generate_instrument_list
from pysat.utils.time import filter_datetime_input

xarray_epoch_name = 'time'

testing_kwargs = {'test_init_kwarg': True, 'test_clean_kwarg': False,
                  'test_preprocess_kwarg': 'test_phrase',
                  'test_load_kwarg': 'bright_light',
                  'test_list_files_kwarg': 'sleep_tight',
                  'test_list_remote_kwarg': 'one_eye_open',
                  'test_download_kwarg': 'exit_night'}


# -----------------------------------------------------------------------------
#
# Test Instrument object basics
#
# -----------------------------------------------------------------------------
class TestBasics():
    def setup(self):
        global testing_kwargs
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy

    def support_iter_evaluations(self, values, for_loop=False, reverse=False):
        """Supports testing of .next/.prev via dates/files"""
        # First, treat with no processing to provide testing as inputs
        # supplied
        if len(values) == 4:
            # testing by date
            starts = values[0]
            stops = values[1]
            step = values[2]
            width = values[3]
            self.testInst.bounds = (starts, stops, step, width)
        elif len(values) == 6:
            # testing by file
            start_files = values[0]
            starts = values[1]
            stop_files = values[2]
            stops = values[3]
            step = values[4]
            width = values[5]
            self.testInst.bounds = (start_files, stop_files, step, width)

        # create list of dates for consistency of later code
        starts = np.asarray([starts])
        stops = np.asarray([stops])
        if len(starts.shape) > 1:
            starts = starts.squeeze().tolist()
            stops = stops.squeeze().tolist()
        else:
            starts = starts.tolist()
            stops = stops.tolist()

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
            out = out[::-1]
        assert np.all(dates == out)

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
        """Support routine for evaluating successful loading of self.testInst

        Parameters
        ----------
        end_date : dt.datetime or NoneType
            End date for loadind data.  If None, assumes self.ref_time + 1 day.
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

    def test_basic_instrument_load(self):
        """Test that the correct day is loaded, specifying only start year, doy
        """
        # Load data by year and day of year
        self.testInst.load(self.ref_time.year, self.ref_doy)

        # Test that the loaded date range is correct
        self.eval_successful_load()
        return

    def test_basic_instrument_load_w_kwargs(self):
        """Test that the correct day is loaded with optional kwarg
        """
        # Load data by year and day of year
        self.testInst.load(self.ref_time.year, self.ref_doy, num_samples=30)

        # Test that the loaded date range is correct
        self.eval_successful_load()
        return

    def test_basic_instrument_load_two_days(self):
        """Test that the correct day is loaded (checking object date and data).
        """
        # Load the reference date
        end_date = self.ref_time + dt.timedelta(days=2)
        end_doy = int(end_date.strftime("%j"))
        self.testInst.load(self.ref_time.year, self.ref_doy, end_date.year,
                           end_doy)

        # Test that the loaded date range is correct
        self.eval_successful_load(end_date=end_date)
        return

    def test_basic_instrument_bad_keyword_init(self):
        """Checks for error when instantiating with bad load keywords on init.
        """
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
        """Checks for error when calling load with bad keywords.
        """
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
        """Ensure doy load keyword in valid range"""
        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, doy)
        estr = 'Day of year (doy) is only valid between and '
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize('end_doy', [0, 367, 1000, -1, -10000])
    def test_basic_instrument_load_yr_bad_end_doy(self, end_doy):
        """Ensure end_doy keyword in valid range"""
        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, 1, end_yr=self.ref_time.year,
                               end_doy=end_doy)
        estr = 'Day of year (end_doy) is only valid between and '
        assert str(err).find(estr) >= 0

        return

    def test_basic_instrument_load_yr_no_end_doy(self):
        """Ensure end_doy required if end_yr present"""
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
        """Ensure mixed load inputs raise ValueError"""
        with pytest.raises(ValueError) as err:
            self.testInst.load(**input)
        estr = 'An inconsistent set of inputs have been'
        assert str(err).find(estr) >= 0
        return

    def test_basic_instrument_load_no_input(self):
        """Test .load() loads all data"""
        self.testInst.load()
        assert (self.testInst.index[0] == self.testInst.files.start_date)
        assert (self.testInst.index[-1] >= self.testInst.files.stop_date)
        assert (self.testInst.index[-1] <= self.testInst.files.stop_date
                + dt.timedelta(days=1))
        return

    @pytest.mark.parametrize('load_in,verr',
                             [('fname', 'have multi_file_day and load by file'),
                              (None, 'is not supported with multi_file_day')])
    def test_basic_instrument_load_by_file_and_multifile(self, load_in, verr):
        """Ensure some load calls raises ValueError with multi_file_day as True
        """
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
        """Test loading by date"""
        self.testInst.load(date=self.ref_time)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_basic_instrument_load_by_dates(self):
        """Test date range loading, date and end_date"""
        end_date = self.ref_time + dt.timedelta(days=2)
        self.testInst.load(date=self.ref_time, end_date=end_date)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)
        self.out = self.testInst.index[-1]
        assert (self.out >= self.ref_time + dt.timedelta(days=1))
        assert (self.out <= self.ref_time + dt.timedelta(days=2))

    def test_basic_instrument_load_by_date_with_extra_time(self):
        """Ensure .load(date=date) only uses year, month, day portion of date"""
        # put in a date that has more than year, month, day
        self.testInst.load(date=dt.datetime(2009, 1, 1, 1, 1, 1))
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_basic_instrument_load_data(self):
        """Test if the correct day is being loaded (checking down to the sec).
        """
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert (self.testInst.index[0] == self.ref_time)

    def test_basic_instrument_load_leap_year(self):
        """Test if the correct day is being loaded (Leap-Year)."""
        self.ref_time = dt.datetime(2008, 12, 31)
        self.ref_doy = 366
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_next_load_default(self):
        """Test if first day is loaded by default when first invoking .next.
        """
        self.ref_time = dt.datetime(2008, 1, 1)
        self.testInst.next()
        self.out = self.testInst.index[0]
        assert self.out == self.ref_time
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_prev_load_default(self):
        """Test if last day is loaded by default when first invoking .prev.
        """
        self.ref_time = dt.datetime(2010, 12, 31)
        self.testInst.prev()
        self.out = self.testInst.index[0]
        assert self.out == self.ref_time
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_next_load_bad_start_file(self):
        """Test Error if trying to iterate when on a file not in iteration list
        """
        self.testInst.load(fname=self.testInst.files[1])
        # set new bounds that doesn't include this date
        self.testInst.bounds = (self.testInst.files[0], self.testInst.files[20],
                                2, 1)
        with pytest.raises(StopIteration) as err:
            self.testInst.next()
        estr = 'Unable to find loaded filename '
        assert str(err).find(estr) >= 0

        return

    def test_prev_load_bad_start_file(self):
        """Test Error if trying to iterate when on a file not in iteration list
        """
        self.testInst.load(fname=self.testInst.files[12])
        # set new bounds that doesn't include this date
        self.testInst.bounds = (self.testInst.files[9], self.testInst.files[20],
                                2, 1)
        with pytest.raises(StopIteration) as err:
            self.testInst.prev()
        estr = 'Unable to find loaded filename '
        assert str(err).find(estr) >= 0

        return

    def test_next_load_bad_start_date(self):
        """Test Error if trying to iterate when on a date not in iteration list
        """
        self.testInst.load(date=self.ref_time)
        # set new bounds that doesn't include this date
        self.testInst.bounds = (self.ref_time + dt.timedelta(days=1),
                                self.ref_time + dt.timedelta(days=10),
                                '2D', dt.timedelta(days=1))

        with pytest.raises(StopIteration) as err:
            self.testInst.next()
        estr = 'Unable to find loaded date '
        assert str(err).find(estr) >= 0

        return

    def test_prev_load_bad_start_date(self):
        """Test Error if trying to iterate when on a date not in iteration list
        """
        self.ref_time = dt.datetime(2008, 1, 2)
        self.testInst.load(date=self.ref_time)
        # set new bounds that doesn't include this date
        self.testInst.bounds = (self.ref_time + dt.timedelta(days=1),
                                self.ref_time + dt.timedelta(days=10),
                                '2D', dt.timedelta(days=1))
        with pytest.raises(StopIteration) as err:
            self.testInst.prev()
        estr = 'Unable to find loaded date '
        assert str(err).find(estr) >= 0

        return

    def test_next_load_empty_iteration(self):
        """Ensure empty iteration list handled ok via .next"""
        self.testInst.bounds = (None, None, '10000D',
                                dt.timedelta(days=10000))
        with pytest.raises(StopIteration) as err:
            self.testInst.next()
        estr = 'File list is empty. '
        assert str(err).find(estr) >= 0

        return

    def test_prev_load_empty_iteration(self):
        """Ensure empty iteration list handled ok via .prev"""
        self.testInst.bounds = (None, None, '10000D',
                                dt.timedelta(days=10000))
        with pytest.raises(StopIteration) as err:
            self.testInst.prev()
        estr = 'File list is empty. '
        assert str(err).find(estr) >= 0

        return

    def test_next_fname_load_default(self):
        """Test next day is being loaded (checking object date)."""
        self.ref_time = dt.datetime(2008, 1, 2)
        self.testInst.load(fname=self.testInst.files[0])
        self.testInst.next()
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_prev_fname_load_default(self):
        """Test prev day is loaded when invoking .prev."""
        self.ref_time = dt.datetime(2008, 1, 3)
        self.testInst.load(fname=self.testInst.files[3])
        self.testInst.prev()
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_basic_fname_instrument_load(self):
        """Test loading by filename from attached .files.
        """
        self.ref_time = dt.datetime(2008, 1, 1)
        self.testInst.load(fname=self.testInst.files[0])
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_filename_load(self):
        """Test if file is loadable by filename, relative to
        top_data_dir/platform/name/tag"""
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'))
        assert self.testInst.index[0] == self.ref_time

    def test_filenames_load(self):
        """Test if files are loadable by filenames, relative to
        top_data_dir/platform/name/tag"""
        stop_fname = self.ref_time + dt.timedelta(days=1)
        stop_fname = stop_fname.strftime('%Y-%m-%d.nofile')
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'),
                           stop_fname=stop_fname)
        assert self.testInst.index[0] == self.ref_time
        assert self.testInst.index[-1] >= self.ref_time + dt.timedelta(days=1)
        assert self.testInst.index[-1] <= self.ref_time + dt.timedelta(days=2)

    def test_filenames_load_out_of_order(self):
        """Test error raised if fnames out of temporal order"""
        stop_fname = self.ref_time + dt.timedelta(days=1)
        stop_fname = stop_fname.strftime('%Y-%m-%d.nofile')
        with pytest.raises(ValueError) as err:
            check_fname = self.ref_time.strftime('%Y-%m-%d.nofile')
            self.testInst.load(fname=stop_fname,
                               stop_fname=check_fname)
        estr = '`stop_fname` must occur at a later date '
        assert str(err).find(estr) >= 0

    def test_next_filename_load_default(self):
        """Test next day is being loaded (checking object date)."""
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'))
        self.testInst.next()
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time + dt.timedelta(days=1))
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_prev_filename_load_default(self):
        """Test prev day is loaded when invoking .prev."""
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'))
        self.testInst.prev()
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time - dt.timedelta(days=1))
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day)
        assert (self.out == self.testInst.date)

    def test_list_files(self):
        files = self.testInst.files.files
        assert isinstance(files, pds.Series)

    def test_remote_file_list(self):
        """Test remote_file_list for valid list of files"""
        stop = self.ref_time + dt.timedelta(days=30)
        self.out = self.testInst.remote_file_list(start=self.ref_time,
                                                  stop=stop)
        assert filter_datetime_input(self.out.index[0]) == self.ref_time
        assert filter_datetime_input(self.out.index[-1]) == stop

    def test_remote_date_range(self):
        """Test remote_date_range for valid pair of dates"""
        stop = self.ref_time + dt.timedelta(days=30)
        self.out = self.testInst.remote_date_range(start=self.ref_time,
                                                   stop=stop)
        assert len(self.out) == 2
        assert filter_datetime_input(self.out[0]) == self.ref_time
        assert filter_datetime_input(self.out[-1]) == stop

    @pytest.mark.parametrize("file_bounds, non_default",
                             [(False, False), (True, False), (False, True),
                              (True, True)])
    def test_download_updated_files(self, caplog, file_bounds, non_default):
        """Test download_updated_files and default bounds are updated"""
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

    def test_download_recent_data(self, caplog):
        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download()

        # Ensure user was told that recent data will be downloaded
        assert "most recent data by default" in caplog.text

        # Ensure user was notified of new files being download
        assert "Downloading data to" in caplog.text

        # Ensure user was notified of updates to the local file list
        assert "Updating pysat file list" in caplog.text

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
        """ Test the correct instantiation of yesterday/today/tomorrow dates
        """
        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day)
        assert self.out == self.testInst.today()
        assert self.out - dt.timedelta(days=1) == self.testInst.yesterday()
        assert self.out + dt.timedelta(days=1) == self.testInst.tomorrow()

    @pytest.mark.parametrize("in_time, islist",
                             [(dt.datetime.utcnow(), False),
                              (dt.datetime(2010, 1, 1, 12, tzinfo=dt.timezone(
                                  dt.timedelta(seconds=14400))), False),
                              ([dt.datetime(2010, 1, 1, 12, i,
                                            tzinfo=dt.timezone(
                                                dt.timedelta(seconds=14400)))
                                for i in range(3)], True)])
    def test_filter_datetime(self, in_time, islist):
        """ Test the range of allowed inputs for the Instrument datetime filter
        """
        # Because the input datetime is the middle of the day and the offset
        # is four hours, the reference date and input date are the same
        if islist:
            self.ref_time = [dt.datetime(tt.year, tt.month, tt.day)
                             for tt in in_time]
            self.out = filter_datetime_input(in_time)
        else:
            self.ref_time = [dt.datetime(in_time.year, in_time.month,
                                         in_time.day)]
            self.out = [filter_datetime_input(in_time)]

        # Test for the date values and timezone awareness status
        for i, tt in enumerate(self.out):
            assert self.out[i] == self.ref_time[i]
            assert self.out[i].tzinfo is None or self.out[i].utcoffset() is None

    def test_filtered_date_attribute(self):
        """ Test use of filter during date assignment
        """
        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day)
        self.testInst.date = self.ref_time
        assert self.out == self.testInst.date

    # -------------------------------------------------------------------------
    #
    # Test __eq__ method
    #
    # -------------------------------------------------------------------------

    def test_eq_no_data(self):
        """Test equality when the same object"""
        inst_copy = self.testInst.copy()
        assert inst_copy == self.testInst
        return

    def test_eq_both_with_data(self):
        """Test equality when the same object with loaded data"""
        self.testInst.load(date=self.ref_time)
        inst_copy = self.testInst.copy()
        assert inst_copy == self.testInst
        return

    def test_eq_one_with_data(self):
        """Test equality when the same objects but only one with loaded data"""
        self.testInst.load(date=self.ref_time)
        inst_copy = self.testInst.copy()
        inst_copy.data = self.testInst._null_data
        assert not (inst_copy == self.testInst)
        return

    def test_eq_different_data_type(self):
        """Test equality different data type"""
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
        """Test equality using different pysat.Instrument objects"""
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
        """Test equality False when non-Instrument object"""
        assert self.testInst != np.array([])
        return

    def test_inequality_modified_object(self):
        """Test that equality is false if other missing attributes"""
        self.out = self.testInst.copy()

        # Remove attribute
        del self.out.platform

        assert self.testInst != self.out
        return

    def test_inequality_reduced_object(self):
        """Test that equality is false if self missing attributes"""
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
        """Test .copy()"""
        inst_copy = self.testInst.copy()
        assert inst_copy == self.testInst
        return

    def test_copy_from_reference(self):
        """Test .copy() if a user invokes from a weakref.proxy of Instrument"""
        inst_copy = self.testInst.orbits.inst.copy()
        inst_copy2 = self.testInst.files.inst_info['inst'].copy()
        assert inst_copy == self.testInst
        assert inst_copy == inst_copy2
        assert inst_copy2 == self.testInst
        return

    def test_copy_w_inst_module(self):
        """Test .copy() with inst_module != None"""
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
        """ Test Instrument data concatonation
        """
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

    # -------------------------------------------------------------------------
    #
    # Test empty property flags, if True, no data
    #
    # -------------------------------------------------------------------------
    def test_empty_flag_data_empty(self):
        """ Test the status of the empty flag for unloaded data."""
        assert self.testInst.empty
        return

    def test_empty_flag_data_not_empty(self):
        """ Test the status of the empty flag for loaded data."""
        self.testInst.load(date=self.ref_time)
        assert not self.testInst.empty

    # -------------------------------------------------------------------------
    #
    # Test index attribute, should always be a datetime index
    #
    # -------------------------------------------------------------------------
    def test_index_attribute(self):
        """ Test the index attribute before and after loading data."""
        # empty Instrument test
        assert isinstance(self.testInst.index, pds.Index)

        # now repeat the same test but with data loaded
        self.testInst.load(date=self.ref_time)
        assert isinstance(self.testInst.index, pds.Index)

    def test_index_return(self):
        # load data
        self.testInst.load(self.ref_time.year, self.ref_doy)
        # ensure we get the index back
        if self.testInst.pandas_format:
            assert np.all(self.testInst.index == self.testInst.data.index)
        else:
            assert np.all(self.testInst.index
                          == self.testInst.data.indexes[xarray_epoch_name])

    # #------------------------------------------------------------------------
    # #
    # # Test custom attributes
    # #
    # #------------------------------------------------------------------------

    def test_retrieve_bad_attribute(self):
        with pytest.raises(AttributeError):
            self.testInst.bad_attr

    def test_base_attr(self):
        self.testInst._base_attr
        assert '_base_attr' in dir(self.testInst)

    def test_inst_attributes_not_overridden(self):
        """Test that custom Instrument attributes are not overwritten upon load
        """
        greeting = '... listen!'
        self.testInst.hei = greeting
        self.testInst.load(date=self.ref_time)
        assert self.testInst.hei == greeting

    # -------------------------------------------------------------------------
    #
    # test textual representations
    #
    # -------------------------------------------------------------------------
    def test_basic_repr(self):
        """The repr output will match the beginning of the str output"""
        self.out = self.testInst.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("pysat.Instrument(") == 0

    def test_basic_str(self):
        """Check for lines from each decision point in repr"""
        self.out = self.testInst.__str__()
        assert isinstance(self.out, str)
        assert self.out.find('pysat Instrument object') == 0
        # No custom functions
        assert self.out.find('Custom Functions: 0') > 0
        # No orbital info
        assert self.out.find('Orbit Settins') < 0
        # Files exist for test inst
        assert self.out.find('Date Range:') > 0
        # No loaded data
        assert self.out.find('No loaded data') > 0
        assert self.out.find('Number of variables') < 0
        assert self.out.find('uts') < 0

    def test_str_w_orbit(self):
        """Test string output with Orbit data """
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

    def test_str_w_padding(self):
        """Test string output with data padding """
        self.testInst.pad = dt.timedelta(minutes=5)
        self.out = self.testInst.__str__()
        assert self.out.find('Data Padding: 0:05:00') > 0

    def test_str_w_custom_func(self):
        """Test string output with custom function """
        def testfunc(self):
            pass
        self.testInst.custom_attach(testfunc)
        self.out = self.testInst.__str__()
        assert self.out.find('testfunc') > 0

    def test_str_w_load_lots_data(self):
        """Test string output with loaded data """
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = self.testInst.__str__()
        assert self.out.find('Number of variables:') > 0
        assert self.out.find('...') > 0

    def test_str_w_load_less_data(self):
        """Test string output with loaded data """
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

    # -------------------------------------------------------------------------
    #
    # test instrument initialization functions
    #
    # -------------------------------------------------------------------------
    def test_instrument_init(self):
        """Test if init function supplied by instrument can modify object"""
        assert self.testInst.new_thing

    def test_custom_instrument_load(self):
        """
        Test if the correct day is being loaded (End-to-End),
        with no instrument file but routines are passed.
        """
        import pysat.instruments.pysat_testing as test
        self.out = pysat.Instrument(inst_module=test, tag='',
                                    clean_level='clean')
        self.ref_time = dt.datetime(2009, 2, 1)
        self.ref_doy = 32
        self.out.load(self.ref_time.year, self.ref_doy)
        assert self.out.date == self.ref_time

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
        """Test if Instrument function keywords are registered by pysat"""

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
        """Test if changed keywords are propagated by pysat to functions"""

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
        """Test for error if undefined keywords provided at instantiation"""

        # Add a new keyword
        self.testInst.kwargs['load']['undefined_keyword1'] = True
        self.testInst.kwargs['load']['undefined_keyword2'] = False

        with pytest.raises(ValueError) as err:
            # Instantiate instrument with new undefined keyword involved
            eval(self.testInst.__repr__())

        estr = "".join(("unknown keywords supplied: ['undefined_keyword1',",
                        " 'undefined_keyword2']"))
        assert str(err).find(estr) >= 0

    def test_supported_input_keywords(self):
        """Test that supported keywords exist"""

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
        """Check that data can be accessed at the instrument level"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all((self.testInst[labels]
                       == self.testInst.data[labels]).values)

    @pytest.mark.parametrize("index", [(0),
                                       ([0, 1, 2, 3]),
                                       (slice(0, 10)),
                                       (np.arange(0, 10))])
    def test_data_access_by_indices_and_name(self, index):
        """Check that variables and be accessed by each supported index type"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[index, 'mlt']
                      == self.testInst.data['mlt'][index])

    def test_data_access_by_row_slicing_and_name_slicing(self):
        """Check that each variable is downsampled """
        self.testInst.load(self.ref_time.year, self.ref_doy)
        result = self.testInst[0:10, :]
        for variable, array in result.items():
            assert len(array) == len(self.testInst.data[variable].values[0:10])
            assert np.all(array == self.testInst.data[variable].values[0:10])

    def test_data_access_by_datetime_and_name(self):
        """Check that datetime can be used to access data"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = dt.datetime(2009, 1, 1, 0, 0, 0)
        assert np.all(self.testInst[self.out, 'uts']
                      == self.testInst.data['uts'].values[0])

    def test_data_access_by_datetime_slicing_and_name(self):
        """Check that a slice of datetimes can be used to access data"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        time_step = (self.testInst.index[1]
                     - self.testInst.index[0]).value / 1.E9
        offset = dt.timedelta(seconds=(10 * time_step))
        start = dt.datetime(2009, 1, 1, 0, 0, 0)
        stop = start + offset
        assert np.all(self.testInst[start:stop, 'uts']
                      == self.testInst.data['uts'].values[0:11])

    def test_setting_data_by_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])

    def test_setting_series_data_by_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = \
            2. * pds.Series(self.testInst['mlt'].values,
                            index=self.testInst.index)
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])

        self.testInst['blankMLT'] = pds.Series(None, dtype='float64')
        assert np.all(np.isnan(self.testInst['blankMLT']))

    def test_setting_pandas_dataframe_by_names(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst[['doubleMLT', 'tripleMLT']] = \
            pds.DataFrame({'doubleMLT': 2. * self.testInst['mlt'].values,
                           'tripleMLT': 3. * self.testInst['mlt'].values},
                          index=self.testInst.index)
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])
        assert np.all(self.testInst['tripleMLT'] == 3. * self.testInst['mlt'])

    def test_setting_data_by_name_single_element(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2.
        assert np.all(self.testInst['doubleMLT'] == 2.)

        self.testInst['nanMLT'] = np.nan
        assert np.all(np.isnan(self.testInst['nanMLT']))

    def test_setting_data_by_name_with_meta(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = {'data': 2. * self.testInst['mlt'],
                                      'units': 'hours',
                                      'long_name': 'double trouble'}
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])
        assert self.testInst.meta['doubleMLT'].units == 'hours'
        assert self.testInst.meta['doubleMLT'].long_name == 'double trouble'

    def test_setting_partial_data(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = self.testInst
        if self.testInst.pandas_format:
            self.testInst[0:3] = 0
            assert np.all(self.testInst[3:] == self.out[3:])
            assert np.all(self.testInst[0:3] == 0)
        else:
            pytest.skip("This notation does not make sense for xarray")

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
        """Check that data can be set using each supported input type"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[changed, 'doubleMLT'] = 0
        assert (self.testInst[fixed, 'doubleMLT']
                == 2. * self.testInst[fixed, 'mlt']).all
        assert (self.testInst[changed, 'doubleMLT'] == 0).all

    def test_setting_partial_data_by_index_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[self.testInst.index[0:10], 'doubleMLT'] = 0
        assert (self.testInst[10:, 'doubleMLT']
                == 2. * self.testInst[10:, 'mlt']).all
        assert (self.testInst[0:10, 'doubleMLT'] == 0).all

    def test_modifying_data_inplace(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst['doubleMLT'] += 100
        assert (self.testInst['doubleMLT']
                == 2. * self.testInst['mlt'] + 100).all

    def test_getting_all_data_by_index(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        a = self.testInst[[0, 1, 2, 3, 4]]
        if self.testInst.pandas_format:
            assert len(a) == 5
        else:
            assert a.sizes[xarray_epoch_name] == 5

    def test_getting_all_data_by_numpy_array_of_int(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        a = self.testInst[np.array([0, 1, 2, 3, 4])]
        if self.testInst.pandas_format:
            assert len(a) == 5
        else:
            assert a.sizes[xarray_epoch_name] == 5

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

    @pytest.mark.parametrize("values", [{'help': 'I need somebody'},
                                        {'UTS': 'litte_uts'},
                                        {'utS': 'uts1'},
                                        {'utS': 'uts'}])
    def test_unknown_variable_error_renaming(self, values):
        # check for error for unknown variable name
        self.testInst.load(self.ref_time.year, self.ref_doy)
        with pytest.raises(ValueError):
            self.testInst.rename(values)

    @pytest.mark.parametrize("values", [{'uts': 'UTS1'},
                                        {'uts': 'UTs2',
                                         'mlt': 'Mlt2'},
                                        {'uts': 'Long Change with spaces'}])
    def test_basic_variable_renaming_lowercase(self, values):
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

    @pytest.mark.parametrize("values", [{'profiles': {'density': 'ionization'}},
                                        {'profiles': {'density': 'mass'},
                                         'alt_profiles':
                                             {'density': 'volume'}}])
    def test_ho_pandas_variable_renaming(self, values):
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
                self.testInst.load(self.ref_time.year, self.ref_doy)
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

    # -------------------------------------------------------------------------
    #
    # Test iteration behaviors
    #
    # -------------------------------------------------------------------------
    def test_list_comprehension(self):
        """Test list comprehensions for length, uniqueness, post iteration data
        """
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
        """Test setting bounds with non-default step"""
        start = self.ref_time
        stop = self.ref_time + dt.timedelta(days=14)
        self.testInst.bounds = (start, stop, 'M')
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='M').tolist())

    def test_iterate_bounds_with_frequency(self):
        """Test iterating bounds with non-default step"""
        start = self.ref_time
        stop = self.ref_time + dt.timedelta(days=15)
        self.testInst.bounds = (start, stop, '2D')
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start, stop, freq='2D').tolist()
        assert np.all(dates == out)

    def test_set_bounds_with_frequency_and_width(self):
        """Set date bounds with step/width>1"""
        start = self.ref_time
        stop = self.ref_time + pds.DateOffset(months=11, days=25)
        stop = stop.to_pydatetime()
        self.testInst.bounds = (start, stop, '10D', dt.timedelta(days=10))
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='10D').tolist())

    def verify_inclusive_iteration(self, out, forward=True):
        """Verify loaded dates for inclusive iteration, forward or backward"""
        if forward:
            # verify range of loaded data when iterating forward
            for i, trange in enumerate(out['observed_times']):
                # determine which range we are in
                b_range = 0
                while out['expected_times'][i] > out['stops'][b_range]:
                    b_range += 1
                # check loaded range is correct
                assert trange[0] == out['expected_times'][i]
                check = out['expected_times'][i] + out['width']
                check -= dt.timedelta(days=1)
                assert trange[1] > check
                check = out['stops'][b_range] + dt.timedelta(days=1)
                assert trange[1] < check
        else:
            # verify range of loaded data when going backwards
            for i, trange in enumerate(out['observed_times']):
                # determine which range we are in
                b_range = 0
                while out['expected_times'][i] > out['stops'][b_range]:
                    b_range += 1
                # check start against expectations
                assert trange[0] == out['expected_times'][i]
                # check end against expectations
                check = out['expected_times'][i] + out['width']
                check -= dt.timedelta(days=1)
                assert trange[1] > check
                check = out['stops'][b_range] + dt.timedelta(days=1)
                assert trange[1] < check
                if i == 0:
                    # check first load is before end of bounds
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

    def verify_exclusive_iteration(self, out, forward=True):
        """Verify loaded dates for exclusive iteration, forward or backward"""
        # verify range of loaded data
        if forward:
            for i, trange in enumerate(out['observed_times']):
                # determine which range we are in
                b_range = 0
                while out['expected_times'][i] > out['stops'][b_range]:
                    b_range += 1
                # check loaded range is correct
                assert trange[0] == out['expected_times'][i]
                check = out['expected_times'][i] + out['width']
                check -= dt.timedelta(days=1)
                assert trange[1] > check
                assert trange[1] < out['stops'][b_range]

        else:

            for i, trange in enumerate(out['observed_times']):
                # determine which range we are in
                b_range = 0
                while out['expected_times'][i] > out['stops'][b_range]:
                    b_range += 1
                # check start against expectations
                assert trange[0] == out['expected_times'][i]
                # check end against expectations
                check = out['expected_times'][i] + out['width']
                check -= dt.timedelta(days=1)
                assert trange[1] > check
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
                                         dt.datetime(2009, 1, 3), '2D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4), '2D',
                                         dt.timedelta(days=3)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5), '3D',
                                         dt.timedelta(days=1)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 17), '5D',
                                         dt.timedelta(days=1))
                                        ])
    def test_iterate_bounds_with_frequency_and_width(self, values):
        """Iterate via date with mixed step/width, excludes stop date"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4), '2D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4), '3D',
                                         dt.timedelta(days=1)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 4), '1D',
                                         dt.timedelta(days=4)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5), '4D',
                                         dt.timedelta(days=1)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5), '2D',
                                         dt.timedelta(days=3)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 5), '3D',
                                         dt.timedelta(days=2))])
    def test_iterate_bounds_with_frequency_and_width_incl(self, values):
        """Iterate via date with mixed step/width, includes stop date"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 10), '2D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 9), '4D',
                                         dt.timedelta(days=1)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11), '1D',
                                         dt.timedelta(days=3)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11), '1D',
                                         dt.timedelta(days=11)),
                                        ])
    def test_next_date_with_frequency_and_width_incl(self, values):
        """Test .next() via date step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11), '2D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 12), '2D',
                                         dt.timedelta(days=3)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 13), '3D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 3), '4D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 12), '2D',
                                         dt.timedelta(days=1))])
    def test_next_date_with_frequency_and_width(self, values):
        """Test .next() via date step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 13)),
                                         '2D',
                                         dt.timedelta(days=2)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         '3D',
                                         dt.timedelta(days=1)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         '2D',
                                         dt.timedelta(days=4))
                                        ])
    def test_next_date_season_frequency_and_width_incl(self, values):
        """Test .next() via date season step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 12)),
                                         '2D',
                                         dt.timedelta(days=2)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         '3D',
                                         dt.timedelta(days=1)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         '2D',
                                         dt.timedelta(days=4))
                                        ])
    def test_next_date_season_frequency_and_width(self, values):
        """Test .next() via date season step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 10), '2D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 9), '4D',
                                         dt.timedelta(days=1)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11), '1D',
                                         dt.timedelta(days=3)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11), '1D',
                                         dt.timedelta(days=11)),
                                        ])
    def test_prev_date_with_frequency_and_width_incl(self, values):
        """Test .prev() via date step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values", [(dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 11), '2D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 12), '2D',
                                         dt.timedelta(days=3)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 13), '3D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 3), '4D',
                                         dt.timedelta(days=2)),
                                        (dt.datetime(2009, 1, 1),
                                         dt.datetime(2009, 1, 12), '2D',
                                         dt.timedelta(days=1))])
    def test_prev_date_with_frequency_and_width(self, values):
        """Test .prev() via date step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 13)),
                                         '2D',
                                         dt.timedelta(days=2)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         '3D',
                                         dt.timedelta(days=1)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         '2D',
                                         dt.timedelta(days=4))
                                        ])
    def test_prev_date_season_frequency_and_width_incl(self, values):
        """Test .prev() via date season step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 12)),
                                         '2D',
                                         dt.timedelta(days=2)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         '3D',
                                         dt.timedelta(days=1)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         '2D',
                                         dt.timedelta(days=4))
                                        ])
    def test_prev_date_season_frequency_and_width(self, values):
        """Test .prev() via date season step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    def test_set_bounds_too_few(self):
        start = dt.datetime(2009, 1, 1)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start]

    def test_set_bounds_mixed(self):
        start = dt.datetime(2009, 1, 1)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, '2009-01-01.nofile']

    def test_set_bounds_wrong_type(self):
        """Test Exception when setting bounds with inconsistent types"""
        start = dt.datetime(2009, 1, 1)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, 1]

    def test_set_bounds_mixed_iterable(self):
        start = [dt.datetime(2009, 1, 1)] * 2
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, '2009-01-01.nofile']

    def test_set_bounds_mixed_iterabless(self):
        start = [dt.datetime(2009, 1, 1)] * 2
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
        """Ensure error if too many inputs to inst.bounds"""
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2009, 1, 1)
        width = dt.timedelta(days=1)
        with pytest.raises(ValueError) as err:
            self.testInst.bounds = [start, stop, '1D', width, False]
        estr = 'Too many input arguments.'
        assert str(err).find(estr) >= 0

    def test_set_bounds_by_date(self):
        """Test setting bounds with datetimes over simple range"""
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop).tolist())

    def test_set_bounds_by_date_wrong_order(self):
        """Test error if bounds assignment has stop date before start"""
        start = dt.datetime(2009, 1, 15)
        stop = dt.datetime(2009, 1, 1)
        with pytest.raises(Exception) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be set in increasing'
        assert str(err).find(estr) >= 0

    def test_set_bounds_by_default_dates(self):
        """Verify bounds behavior with default date related inputs"""
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

    def test_set_bounds_by_date_extra_time(self):
        start = dt.datetime(2009, 1, 1, 1, 10)
        stop = dt.datetime(2009, 1, 15, 1, 10)
        self.testInst.bounds = (start, stop)
        start = filter_datetime_input(start)
        stop = filter_datetime_input(stop)
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop).tolist())

    @pytest.mark.parametrize("start,stop", [(dt.datetime(2010, 12, 1),
                                             dt.datetime(2010, 12, 31)),
                                            (dt.datetime(2009, 1, 1),
                                             dt.datetime(2009, 1, 15))
                                            ])
    def test_iterate_over_bounds_set_by_date(self, start, stop):
        """Test iterating over bounds via single date range"""
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start, stop).tolist()
        assert np.all(dates == out)

    def test_iterate_over_default_bounds(self):
        """Test iterating over default bounds"""
        date_range = pds.date_range(self.ref_time,
                                    self.ref_time + dt.timedelta(days=10))
        self.testInst.kwargs['list_files']['file_date_range'] = date_range
        self.testInst.files.refresh()
        self.testInst.bounds = (None, None)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = date_range.tolist()
        assert np.all(dates == out)

    def test_set_bounds_by_date_season(self):
        start = [dt.datetime(2009, 1, 1), dt.datetime(2009, 2, 1)]
        stop = [dt.datetime(2009, 1, 15), dt.datetime(2009, 2, 15)]
        self.testInst.bounds = (start, stop)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(self.testInst._iter_list == out)

    def test_set_bounds_by_date_season_wrong_order(self):
        """Test error if bounds season assignment has stop date before start"""
        start = [dt.datetime(2009, 1, 1), dt.datetime(2009, 2, 1)]
        stop = [dt.datetime(2009, 1, 12), dt.datetime(2009, 1, 15)]
        with pytest.raises(Exception) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be set in increasing'
        assert str(err).find(estr) >= 0

    def test_set_bounds_by_date_season_extra_time(self):
        start = [dt.datetime(2009, 1, 1, 1, 10),
                 dt.datetime(2009, 2, 1, 1, 10)]
        stop = [dt.datetime(2009, 1, 15, 1, 10),
                dt.datetime(2009, 2, 15, 1, 10)]
        self.testInst.bounds = (start, stop)
        start = filter_datetime_input(start)
        stop = filter_datetime_input(stop)
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

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 12)),
                                         '2D',
                                         dt.timedelta(days=2)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         '3D',
                                         dt.timedelta(days=1)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         '2D',
                                         dt.timedelta(days=4))
                                        ])
    def test_iterate_over_bounds_set_by_date_season_step_width(self, values):
        """Iterate over season, step/width > 1, excludes stop bounds"""

        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 13)),
                                         '2D',
                                         dt.timedelta(days=2)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 7),
                                          dt.datetime(2009, 1, 16)),
                                         '3D',
                                         dt.timedelta(days=1)),
                                        ((dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 10)),
                                         (dt.datetime(2009, 1, 6),
                                          dt.datetime(2009, 1, 15)),
                                         '2D',
                                         dt.timedelta(days=4))
                                        ])
    def test_iterate_bounds_set_by_date_season_step_width_incl(self, values):
        """Iterate over season, step/width > 1, includes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    def test_iterate_over_bounds_set_by_date_season_extra_time(self):
        start = [dt.datetime(2009, 1, 1, 1, 10),
                 dt.datetime(2009, 2, 1, 1, 10)]
        stop = [dt.datetime(2009, 1, 15, 1, 10),
                dt.datetime(2009, 2, 15, 1, 10)]
        self.testInst.bounds = (start, stop)
        # filter
        start = filter_datetime_input(start)
        stop = filter_datetime_input(stop)
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
        assert np.all(self.testInst._iter_list
                      == ['2009-01-01.nofile', '2009-01-02.nofile',
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

    def test_set_bounds_by_fname_wrong_order(self):
        """Test for error if stop file before start file"""
        start = '2009-01-13.nofile'
        stop = '2009-01-01.nofile'
        with pytest.raises(Exception) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be in increasing date'
        assert str(err).find(estr) >= 0
        return

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
        assert np.all(self.testInst._iter_list
                      == ['2009-01-01.nofile', '2009-01-02.nofile',
                          '2009-01-03.nofile', '2009-02-01.nofile',
                          '2009-02-02.nofile', '2009-02-03.nofile'])

    def test_set_bounds_by_fname_season_wrong_order(self):
        """Test for error if stop file before start file, season"""

        start = ['2009-01-01.nofile', '2009-02-03.nofile']
        stop = ['2009-01-03.nofile', '2009-02-01.nofile']
        with pytest.raises(Exception) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be in increasing date'
        assert str(err).find(estr) >= 0
        return

    def test_iterate_over_bounds_set_by_fname_season(self):
        """Test set bounds using multiple filenames"""
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

    def test_set_bounds_fname_with_frequency(self):
        """Test set bounds using filenames and non-default step"""
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

    def test_iterate_bounds_fname_with_frequency(self):
        """Test iterate over bounds using filenames and non-default step"""
        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3)
        self.testInst.bounds = (start, stop, 2)

        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start_date, stop_date, freq='2D').tolist()
        assert np.all(dates == out)

    def test_set_bounds_fname_with_frequency_and_width(self):
        """Set fname bounds with step/width>1"""
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

    @pytest.mark.parametrize("values", [('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-03.nofile',
                                         dt.datetime(2009, 1, 3),
                                         2, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-04.nofile',
                                         dt.datetime(2009, 1, 4),
                                         2, 3),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-05.nofile',
                                         dt.datetime(2009, 1, 5),
                                         3, 1)])
    def test_iterate_bounds_fname_with_frequency_and_width(self, values):
        """File iteration in bounds with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-04.nofile',
                                         dt.datetime(2009, 1, 4),
                                         2, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-04.nofile',
                                         dt.datetime(2009, 1, 4),
                                         3, 1),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-04.nofile',
                                         dt.datetime(2009, 1, 4),
                                         1, 4),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-05.nofile',
                                         dt.datetime(2009, 1, 5),
                                         2, 3)])
    def test_iterate_bounds_fname_with_frequency_and_width_incl(self, values):
        """File iteration in bounds with step/width>1, includes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-03.nofile',
                                          '2009-01-13.nofile'),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 13)), 2, 2),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 2, 3),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-05.nofile',
                                          '2009-01-15.nofile'),
                                         (dt.datetime(2009, 1, 5),
                                          dt.datetime(2009, 1, 15)), 3, 1)])
    def test_iterate_fname_season_with_frequency_and_width(self, values):
        """File season iteration with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 2, 2),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 3, 1),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 1, 4),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-05.nofile',
                                          '2009-01-15.nofile'),
                                         (dt.datetime(2009, 1, 5),
                                          dt.datetime(2009, 1, 15)), 2, 3)])
    def test_iterate_fname_season_with_frequency_and_width_incl(self, values):
        """File iteration in bounds with step/width>1, includes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 11), 2, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-12.nofile',
                                         dt.datetime(2009, 1, 12), 2, 3),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-13.nofile',
                                         dt.datetime(2009, 1, 13), 3, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-03.nofile',
                                         dt.datetime(2009, 1, 3), 4, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-12.nofile',
                                         dt.datetime(2009, 1, 12), 2, 1)])
    def test_next_fname_with_frequency_and_width(self, values):
        """Test .next() via fname step/width>1, excludes stop file"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 10),
                                         2, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-09.nofile',
                                         dt.datetime(2009, 1, 9),
                                         4, 1),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 11),
                                         1, 3),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 11),
                                         1, 11),
                                        ])
    def test_next_fname_with_frequency_and_width_incl(self, values):
        """Test .next() via fname step/width>1, includes stop file"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-03.nofile',
                                          '2009-01-13.nofile'),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 13)), 2, 2),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 2, 3),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-05.nofile',
                                          '2009-01-15.nofile'),
                                         (dt.datetime(2009, 1, 5),
                                          dt.datetime(2009, 1, 15)), 3, 1)])
    def test_next_fname_season_with_frequency_and_width(self, values):
        """File next season with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [(('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 2, 2),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 3, 1),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 1, 4),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-05.nofile',
                                          '2009-01-15.nofile'),
                                         (dt.datetime(2009, 1, 5),
                                          dt.datetime(2009, 1, 15)), 2, 3)])
    def test_next_fname_season_with_frequency_and_width_incl(self, values):
        """File next season with step/width>1, includes stop bounds"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values", [('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 11),
                                         2, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-12.nofile',
                                         dt.datetime(2009, 1, 12),
                                         2, 3),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-13.nofile',
                                         dt.datetime(2009, 1, 13),
                                         3, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-03.nofile',
                                         dt.datetime(2009, 1, 3),
                                         4, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-12.nofile',
                                         dt.datetime(2009, 1, 12),
                                         2, 1)])
    def test_prev_fname_with_frequency_and_width(self, values):
        """Test prev() fname step/width>1, excludes stop bound"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values", [('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 10),
                                         2, 2),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-09.nofile',
                                         dt.datetime(2009, 1, 9),
                                         4, 1),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 11),
                                         1, 3),
                                        ('2009-01-01.nofile',
                                         dt.datetime(2009, 1, 1),
                                         '2009-01-11.nofile',
                                         dt.datetime(2009, 1, 11),
                                         1, 11),
                                        ])
    def test_prev_fname_with_frequency_and_width_incl(self, values):
        """Test prev() fname step/width>1, includes bounds stop date"""

        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values", [(('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-03.nofile',
                                          '2009-01-13.nofile'),
                                         (dt.datetime(2009, 1, 3),
                                          dt.datetime(2009, 1, 13)), 2, 2),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 2, 3),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-05.nofile',
                                          '2009-01-15.nofile'),
                                         (dt.datetime(2009, 1, 5),
                                          dt.datetime(2009, 1, 15)), 3, 1)])
    def test_prev_fname_season_with_frequency_and_width(self, values):
        """File prev season with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values", [(('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 2, 2),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 3, 1),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-04.nofile',
                                          '2009-01-14.nofile'),
                                         (dt.datetime(2009, 1, 4),
                                          dt.datetime(2009, 1, 14)), 1, 4),
                                        (('2009-01-01.nofile',
                                          '2009-01-11.nofile'),
                                         (dt.datetime(2009, 1, 1),
                                          dt.datetime(2009, 1, 11)),
                                         ('2009-01-05.nofile',
                                          '2009-01-15.nofile'),
                                         (dt.datetime(2009, 1, 5),
                                          dt.datetime(2009, 1, 15)), 2, 3)])
    def test_prev_fname_season_with_frequency_and_width_incl(self, values):
        """File prev season with step/width>1, includes stop bounds"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=False)

        return

    def test_creating_empty_instrument_object(self):
        """Ensure empty Instrument instantiation runs"""
        null = pysat.Instrument()
        assert isinstance(null, pysat.Instrument)

    def test_incorrect_creation_empty_instrument_object(self):
        """Ensure instantiation with missing name errors"""
        with pytest.raises(ValueError) as err:
            # Both name and platform should be empty
            pysat.Instrument(platform='cnofs')
        estr = 'Inputs platform and name must both'
        assert str(err).find(estr) >= 0

    def test_error_bad_inst_id_instrument_object(self):
        """Ensure instantiation with invalid inst_id errors"""
        with pytest.raises(ValueError) as err:
            pysat.Instrument(platform=self.testInst.platform,
                             name=self.testInst.name,
                             inst_id='invalid_inst_id')
        estr = "'invalid_inst_id' is not one of the supported inst_ids."
        assert str(err).find(estr) >= 0

    def test_error_bad_tag_instrument_object(self):
        """Ensure instantiation with invalid inst_id errors"""
        with pytest.raises(ValueError) as err:
            pysat.Instrument(platform=self.testInst.platform,
                             name=self.testInst.name,
                             inst_id='',
                             tag='bad_tag')
        estr = "'bad_tag' is not one of the supported tags."
        assert str(err).find(estr) >= 0

    def test_supplying_instrument_module_requires_name_and_platform(self):
        """Ensure instantiation via inst_module with missing name errors"""
        class Dummy:
            pass
        Dummy.name = 'help'

        with pytest.raises(AttributeError) as err:
            pysat.Instrument(inst_module=Dummy)
        estr = 'Supplied module '
        assert str(err).find(estr) >= 0

    def test_get_var_type_code_unknown_type(self):
        """Ensure that Error is thrown if unknown type is supplied"""
        with pytest.raises(TypeError) as err:
            self.testInst._get_var_type_code(type(None))
        estr = 'Unknown Variable'
        assert str(err).find(estr) >= 0


# -----------------------------------------------------------------------------
#
# Repeat tests above with Instrument instantiated via inst_module
#
# -----------------------------------------------------------------------------
class TestBasicsInstModule(TestBasics):
    def setup(self):
        global testing_kwargs
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        imod = pysat.instruments.pysat_testing
        self.testInst = pysat.Instrument(inst_module=imod,
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **testing_kwargs)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy


# -----------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# -----------------------------------------------------------------------------
class TestBasicsXarray(TestBasics):
    def setup(self):
        global testing_kwargs
        reload(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **testing_kwargs)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy


# -----------------------------------------------------------------------------
#
# Repeat tests above with 2d data
#
# -----------------------------------------------------------------------------
class TestBasics2D(TestBasics):
    def setup(self):
        global testing_kwargs
        reload(pysat.instruments.pysat_testing2d)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing2d',
                                         num_samples=50,
                                         clean_level='clean',
                                         update_files=True,
                                         **testing_kwargs)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy


# -----------------------------------------------------------------------------
#
# Repeat tests above with 2d xarray data
#
# -----------------------------------------------------------------------------
class TestBasics2DXarray(TestBasics):
    def setup(self):
        global testing_kwargs
        reload(pysat.instruments.pysat_testing2d_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing2d_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         **testing_kwargs)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy

    @pytest.mark.parametrize("index", [(0),
                                       ([0, 1, 2, 3]),
                                       (slice(0, 10)),
                                       (np.array([0, 1, 2, 3]))])
    def test_data_access_by_2d_indices_and_name(self, index):
        """Check that variables and be accessed by each supported index type"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[index, index, 'profiles']
                      == self.testInst.data['profiles'][index, index])

    def test_data_access_by_2d_tuple_indices_and_name(self):
        """Check that variables and be accessed by multi-dim tuple index
        """
        self.testInst.load(date=self.ref_time)
        index = ([0, 1, 2, 3], [0, 1, 2, 3])
        assert np.all(self.testInst[index, 'profiles']
                      == self.testInst.data['profiles'][index[0], index[1]])

    def test_data_access_bad_dimension_tuple(self):
        """Test raises ValueError for mismatched tuple index and data dimensions
        """
        self.testInst.load(date=self.ref_time)
        index = ([0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3])

        with pytest.raises(ValueError) as verr:
            self.testInst[index, 'profiles']

        estr = 'not convert tuple'
        assert str(verr).find(estr) > 0

    def test_data_access_bad_dimension_for_multidim(self):
        """Test raises ValueError for mismatched index and data dimensions
        """
        self.testInst.load(date=self.ref_time)
        index = [0, 1, 2, 3]

        with pytest.raises(ValueError) as verr:
            self.testInst[index, index, index, 'profiles']

        estr = "don't match data"
        assert str(verr).find(estr) > 0

    @pytest.mark.parametrize("changed,fixed",
                             [(0, slice(1, None)),
                              ([0, 1, 2, 3], slice(4, None)),
                              (slice(0, 10), slice(10, None)),
                              (np.array([0, 1, 2, 3]), slice(4, None))])
    def test_setting_partial_data_by_2d_indices_and_name(self, changed, fixed):
        """Check that data can be set using each supported index type"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleProfile'] = 2. * self.testInst['profiles']
        self.testInst[changed, changed, 'doubleProfile'] = 0
        assert np.all(np.all(self.testInst[fixed, fixed, 'doubleProfile']
                             == 2. * self.testInst[fixed, 'profiles']))
        assert np.all(np.all(self.testInst[changed, changed, 'doubleProfile']
                             == 0))


# -----------------------------------------------------------------------------
#
# Repeat TestBasics above with shifted file dates
#
# -----------------------------------------------------------------------------

class TestBasicsShiftedFileDates(TestBasics):
    def setup(self):
        global testing_kwargs
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         mangle_file_dates=True,
                                         strict_time_flag=True,
                                         **testing_kwargs)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy


# -----------------------------------------------------------------------------
#
# Test Instrument with a non-unique and non-monotonic index
#
# -----------------------------------------------------------------------------
class TestMalformedIndex():
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy

    # -------------------------------------------------------------------------
    #
    # Test checks on time uniqueness and monotonicity
    #
    # -------------------------------------------------------------------------
    def test_ensure_unique_index(self):
        """Ensure that if Instrument index not-unique error is raised"""
        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, self.ref_doy)
        estr = 'Loaded data is not unique.'
        assert str(err).find(estr) > 0


# -----------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# -----------------------------------------------------------------------------
class TestMalformedIndexXarray(TestMalformedIndex):
    def setup(self):
        reload(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         malformed_index=True,
                                         update_files=True,
                                         strict_time_flag=True)
        self.ref_time = dt.datetime(2009, 1, 1)
        self.ref_doy = 1

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy


# -----------------------------------------------------------------------------
#
# Test data padding, loading by file
#
# -----------------------------------------------------------------------------
class TestDataPaddingbyFile():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)
        self.testInst.bounds = ('2008-01-01.nofile', '2010-12-31.nofile')

        self.rawInst = pysat.Instrument(platform='pysat', name='testing',
                                        clean_level='clean',
                                        update_files=True)
        self.rawInst.bounds = self.testInst.bounds
        self.delta = 0

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.rawInst, self.delta

    def test_fname_data_padding(self):
        """Test data padding loading by filename"""
        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[1])
        self.delta = dt.timedelta(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_next(self):
        """Test data padding loading by filename when using next"""
        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[2])
        self.delta = dt.timedelta(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_multi_next(self):
        """Test data padding loading by filename when using next multiple times
        """
        self.testInst.load(fname=self.testInst.files[1])
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[3])
        self.delta = dt.timedelta(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_prev(self):
        """Test data padding loading by filename when using prev"""
        self.testInst.load(fname=self.testInst.files[2], verifyPad=True)
        self.testInst.prev(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[1])
        self.delta = dt.timedelta(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_multi_prev(self):
        """Test data padding loading by filename when using prev multiple times
        """
        self.testInst.load(fname=self.testInst.files[10])
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[8])
        self.delta = dt.timedelta(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_jump(self):
        """Test data padding by filename after loading non-consecutive file"""
        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.testInst.load(fname=self.testInst.files[10], verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[10])
        self.delta = dt.timedelta(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_uniqueness(self):
        """Ensure uniqueness data padding when loading by file"""
        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        assert (self.testInst.index.is_unique)

    def test_fname_data_padding_all_samples_present(self):
        """Ensure all samples present when padding and loading by file"""
        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.delta = pds.date_range(self.testInst.index[0],
                                    self.testInst.index[-1], freq='S')
        assert (np.all(self.testInst.index == self.delta))

    def test_fname_data_padding_removal(self):
        """Ensure padded samples nominally dropped, loading by file."""
        self.testInst.load(fname=self.testInst.files[1])
        self.rawInst.load(fname=self.testInst.files[1])
        assert self.testInst.index[0] == self.rawInst.index[0]
        assert self.testInst.index[-1] == self.rawInst.index[-1]
        assert len(self.rawInst.data) == len(self.testInst.data)


# -----------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# -----------------------------------------------------------------------------
class TestDataPaddingbyFileXarray(TestDataPaddingbyFile):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        reload(pysat.instruments.pysat_testing_xarray)
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
        self.delta = 0

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.rawInst, self.delta


class TestOffsetRightFileDataPaddingBasics(TestDataPaddingbyFile):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
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
        self.delta = 0

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.rawInst, self.delta


class TestOffsetRightFileDataPaddingBasicsXarray(TestDataPaddingbyFile):
    def setup(self):
        reload(pysat.instruments.pysat_testing_xarray)
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
        self.delta = 0

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.rawInst, self.delta


class TestOffsetLeftFileDataPaddingBasics(TestDataPaddingbyFile):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
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
        self.delta = 0

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.rawInst, self.delta


class TestDataPadding():
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy

    def test_data_padding(self):
        """Ensure that pad works at the instrument level"""
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        assert (self.testInst.index[0]
                == self.testInst.date - dt.timedelta(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + dt.timedelta(minutes=5))

    @pytest.mark.parametrize('pad', [dt.timedelta(minutes=5),
                                     pds.DateOffset(minutes=5),
                                     {'minutes': 5}])
    def test_data_padding_offset_instantiation(self, pad):
        """Ensure pad can be used as datetime, pandas, or dict"""
        testInst = pysat.Instrument(platform='pysat', name='testing',
                                    clean_level='clean',
                                    pad=pad,
                                    update_files=True)
        testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        assert (testInst.index[0] == testInst.date - dt.timedelta(minutes=5))
        assert (testInst.index[-1] == testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + dt.timedelta(minutes=5))

    def test_data_padding_bad_instantiation(self):
        """Ensure error when padding input type incorrect"""
        with pytest.raises(ValueError) as err:
            pysat.Instrument(platform='pysat', name='testing',
                             clean_level='clean',
                             pad=2,
                             update_files=True)
        estr = ' '.join(('pad must be a dict, NoneType, datetime.timedelta,',
                         'or pandas.DateOffset instance.'))
        assert str(err).find(estr) >= 0

    def test_data_padding_bad_load(self):
        """Not allowed to enable data padding when loading all data, load()"""
        with pytest.raises(ValueError) as err:
            self.testInst.load()

        if self.testInst.multi_file_day:
            estr = '`load()` is not supported with multi_file_day'
        else:
            estr = '`load()` is not supported with data padding'
        assert str(err).find(estr) >= 0

    def test_padding_exceeds_load_window(self):
        """Ensure error is padding window larger than loading window"""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         pad={'days': 2},
                                         update_files=True)
        with pytest.raises(ValueError) as err:
            self.testInst.load(date=self.ref_time)
        estr = 'Data padding window must be shorter than '
        assert str(err).find(estr) >= 0

    def test_yrdoy_data_padding_missing_earlier_days(self):
        """Test padding feature operates when there are missing prev days"""
        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.start_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] == self.testInst.date
        assert self.testInst.index[-1] > self.testInst.date \
               + dt.timedelta(days=1)

        self.testInst.load(yr, doy)
        assert self.testInst.index[0] == self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + dt.timedelta(days=1)

    def test_yrdoy_data_padding_missing_later_days(self):
        """Test padding feature operates when there are missing later days"""
        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.stop_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] < self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + dt.timedelta(days=1)

        self.testInst.load(yr, doy)
        assert self.testInst.index[0] == self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + dt.timedelta(days=1)

    def test_yrdoy_data_padding_missing_earlier_and_later_days(self):
        """Test padding feature operates when missing earlier/later days"""
        # reduce available files
        self.testInst.files.files = self.testInst.files.files[0:1]
        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.start_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] == self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + dt.timedelta(days=1)

    def test_data_padding_next(self):
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.next(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - dt.timedelta(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + dt.timedelta(minutes=5))

    def test_data_padding_multi_next(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - dt.timedelta(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + dt.timedelta(minutes=5))

    def test_data_padding_prev(self):
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.prev(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - dt.timedelta(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + dt.timedelta(minutes=5))

    def test_data_padding_multi_prev(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.ref_doy = 10
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - dt.timedelta(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + dt.timedelta(minutes=5))

    def test_data_padding_jump(self):
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.load(self.ref_time.year, self.ref_doy + 10,
                           verifyPad=True)
        assert (self.testInst.index[0]
                == self.testInst.date - dt.timedelta(minutes=5))
        assert (self.testInst.index[-1]
                == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59)
                + dt.timedelta(minutes=5))

    def test_data_padding_uniqueness(self):
        self.ref_doy = 1
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        assert (self.testInst.index.is_unique)

    def test_data_padding_all_samples_present(self):
        self.ref_doy = 1
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        test_index = pds.date_range(self.testInst.index[0],
                                    self.testInst.index[-1], freq='S')
        assert (np.all(self.testInst.index == test_index))

    def test_data_padding_removal(self):
        self.ref_doy = 1
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert (self.testInst.index[0] == self.testInst.date)
        assert (self.testInst.index[-1] == self.testInst.date
                + dt.timedelta(hours=23, minutes=59, seconds=59))


class TestDataPaddingXarray(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy


class TestMultiFileRightDataPaddingBasics(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5})
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy


class TestMultiFileRightDataPaddingBasicsXarray(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes': 5})
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy


class TestMultiFileLeftDataPaddingBasics(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5})
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy


class TestMultiFileLeftDataPaddingBasicsXarray(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes': 5})
        self.testInst.multi_file_day = True
        self.ref_time = dt.datetime(2009, 1, 2)
        self.ref_doy = 2

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy


class TestInstListGeneration():
    """Provides tests to ensure the instrument test class is working as expected
    """

    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.test_library = pysat.instruments

    def teardown(self):
        """Runs after every method to clean up previous testing.
        """
        # reset pysat instrument library
        reload(pysat.instruments)
        reload(pysat.instruments.pysat_testing)
        del self.test_library

    def test_import_error_behavior(self):
        """Check that instrument list works if a broken instrument is found"""
        self.test_library.__all__.append('broken_inst')
        # This instrument does not exist.  The routine should run without error
        inst_list = generate_instrument_list(self.test_library)
        assert 'broken_inst' in inst_list['names']
        for dict in inst_list['download']:
            assert 'broken_inst' not in dict['inst_module'].__name__
        for dict in inst_list['no_download']:
            assert 'broken_inst' not in dict['inst_module'].__name__

    def test_for_missing_test_date(self):
        """Check that instruments without _test_dates are still added to the list
        """
        del self.test_library.pysat_testing._test_dates
        # If an instrument does not have the _test_dates attribute, it should
        # still be added to the list for other checks to be run
        # This will be caught later by InstTestClass.test_instrument_test_dates
        assert not hasattr(self.test_library.pysat_testing, '_test_dates')
        inst_list = generate_instrument_list(self.test_library)
        assert 'pysat_testing' in inst_list['names']
