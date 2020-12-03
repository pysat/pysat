# -*- coding: utf-8 -*-
# Test some of the basic _core functions
import datetime as dt
from importlib import reload
import logging
import numpy as np

import pandas as pds
import pytest

import pysat
import pysat.instruments.pysat_testing
import pysat.instruments.pysat_testing_xarray
import pysat.instruments.pysat_testing2d
from pysat.utils import generate_instrument_list

xarray_epoch_name = 'time'


# -----------------------------------------------------------------------------
#
# Test Instrument object basics
#
# -----------------------------------------------------------------------------
class TestBasics():
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True)
        self.ref_time = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        self.ref_doy = 1
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy

    def support_iter_evaluations(self, values, for_loop=False, reverse=False):
        """Supports testing of .next/.prev via dates/files"""
        # first, treat with no processing to provide testing as inputs
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
                time_range.append((inst.index[0], inst.index[-1]))
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
            width = pds.DateOffset(days=width)

        out = []
        for start, stop in zip(starts, stops):
            tdate = stop - width + pds.DateOffset(days=1)
            out.extend([tt.to_pydatetime() for tt in
                        pds.date_range(start, tdate, freq=step)])
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
    def test_basic_instrument_load(self):
        """Test if the correct day is being loaded (checking object date and
        data)."""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_basic_instrument_load_two_days(self):
        """Test if the correct day is being loaded (checking object date and
        data)."""
        self.testInst.load(self.ref_time.year, self.ref_doy,
                           self.ref_time.year, self.ref_doy + 2)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)
        self.out = self.testInst.index[-1]
        assert (self.out >= self.ref_time + pds.DateOffset(days=1))
        assert (self.out <= self.ref_time + pds.DateOffset(days=2))

    def test_basic_instrument_bad_keyword(self):
        """Checks for error when instantiating with bad load_rtn keywords"""
        with pytest.raises(ValueError):
            pysat.Instrument(platform=self.testInst.platform,
                             name=self.testInst.name, num_samples=10,
                             clean_level='clean',
                             unsupported_keyword_yeah=True)

    def test_basic_instrument_load_yr_no_doy(self):
        """Ensure doy required if yr present"""
        with pytest.raises(TypeError) as err:
            self.testInst.load(self.ref_time.year)

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

    @pytest.mark.parametrize("input",
                             [{'yr': 2009, 'doy': 1,
                               'date': dt.datetime(2009, 1, 1,
                                                   tzinfo=dt.timezone.utc)},
                              {'yr': 2009, 'doy': 1,
                               'end_date': dt.datetime(2009, 1, 1,
                                                       tzinfo=dt.timezone.utc)},
                              {'yr': 2009, 'doy': 1,
                               'fname': 'dummy_str.nofile'},
                              {'yr': 2009, 'doy': 1,
                               'stop_fname': 'dummy_str.nofile'},
                              {'date': dt.datetime(2009, 1, 1,
                                                   tzinfo=dt.timezone.utc),
                               'fname': 'dummy_str.nofile'},
                              {'date': dt.datetime(2009, 1, 1,
                                                   tzinfo=dt.timezone.utc),
                               'stop_fname': 'dummy_str.nofile'},
                              {'date': dt.datetime(2009, 1, 1,
                                                   tzinfo=dt.timezone.utc),
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
                + pds.DateOffset(days=1))
        return

    def test_basic_instrument_load_by_file_and_multifile(self):
        """Ensure multi_file_day has to be False when loading by filename"""
        self.out = pysat.Instrument(platform=self.testInst.platform,
                                    name=self.testInst.name,
                                    num_samples=10,
                                    clean_level='clean',
                                    update_files=True,
                                    multi_file_day=True)
        with pytest.raises(ValueError) as err:
            self.out.load(fname=self.out.files[0])
        estr = "have multi_file_day and load by file"
        assert str(err).find(estr) >= 0

        return

    def test_basic_instrument_load_and_multifile(self):
        """Ensure .load() only runs when multi_file_day is False"""
        self.out = pysat.Instrument(platform=self.testInst.platform,
                                    name=self.testInst.name,
                                    num_samples=10,
                                    clean_level='clean',
                                    update_files=True,
                                    multi_file_day=True)
        with pytest.raises(ValueError) as err:
            self.out.load()
        estr = '`load()` is not supported with multi_file_day'
        assert str(err).find(estr) >= 0

        return

    def test_basic_instrument_load_by_date(self):
        """Test loading by date"""
        self.testInst.load(date=self.ref_time)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_basic_instrument_load_by_dates(self):
        """Test date range loading, date and end_date"""
        end_date = self.ref_time + pds.DateOffset(days=2)
        self.testInst.load(date=self.ref_time, end_date=end_date)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)
        self.out = self.testInst.index[-1]
        assert (self.out >= self.ref_time + pds.DateOffset(days=1))
        assert (self.out <= self.ref_time + pds.DateOffset(days=2))

    def test_basic_instrument_load_by_date_with_extra_time(self):
        """Ensure .load(date=date) only uses year, month, day portion of date"""
        # put in a date that has more than year, month, day
        self.testInst.load(date=dt.datetime(2009, 1, 1, 1, 1, 1,
                                            tzinfo=dt.timezone.utc))
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_basic_instrument_load_data(self):
        """Test if the correct day is being loaded (checking down to the sec).
        """
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert (self.testInst.index[0] == self.ref_time)

    def test_basic_instrument_load_leap_year(self):
        """Test if the correct day is being loaded (Leap-Year)."""
        self.ref_time = dt.datetime(2008, 12, 31, tzinfo=dt.timezone.utc)
        self.ref_doy = 366
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_next_load_default(self):
        """Test if first day is loaded by default when first invoking .next.
        """
        self.ref_time = dt.datetime(2008, 1, 1, tzinfo=dt.timezone.utc)
        self.testInst.next()
        self.out = self.testInst.index[0]
        assert self.out == self.ref_time
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_prev_load_default(self):
        """Test if last day is loaded by default when first invoking .prev.
        """
        self.ref_time = dt.datetime(2010, 12, 31, tzinfo=dt.timezone.utc)
        self.testInst.prev()
        self.out = self.testInst.index[0]
        assert self.out == self.ref_time
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
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
        self.testInst.bounds = (self.ref_time + pds.DateOffset(days=1),
                                self.ref_time + pds.DateOffset(days=10),
                                '2D', pds.DateOffset(days=1))

        with pytest.raises(StopIteration) as err:
            self.testInst.next()
        estr = 'Unable to find loaded date '
        assert str(err).find(estr) >= 0

        return

    def test_prev_load_bad_start_date(self):
        """Test Error if trying to iterate when on a date not in iteration list
        """
        self.ref_time = dt.datetime(2008, 1, 2, tzinfo=dt.timezone.utc)
        self.testInst.load(date=self.ref_time)
        # set new bounds that doesn't include this date
        self.testInst.bounds = (self.ref_time + pds.DateOffset(days=1),
                                self.ref_time + pds.DateOffset(days=10),
                                '2D', pds.DateOffset(days=1))
        with pytest.raises(StopIteration) as err:
            self.testInst.prev()
        estr = 'Unable to find loaded date '
        assert str(err).find(estr) >= 0

        return

    def test_next_load_empty_iteration(self):
        """Ensure empty iteration list handled ok via .next"""
        self.testInst.bounds = (None, None, '10000D',
                                pds.DateOffset(days=10000))
        with pytest.raises(StopIteration) as err:
            self.testInst.next()
        estr = 'File list is empty. '
        assert str(err).find(estr) >= 0

        return

    def test_prev_load_empty_iteration(self):
        """Ensure empty iteration list handled ok via .prev"""
        self.testInst.bounds = (None, None, '10000D',
                                pds.DateOffset(days=10000))
        with pytest.raises(StopIteration) as err:
            self.testInst.prev()
        estr = 'File list is empty. '
        assert str(err).find(estr) >= 0

        return

    def test_next_fname_load_default(self):
        """Test next day is being loaded (checking object date)."""
        self.ref_time = dt.datetime(2008, 1, 2, tzinfo=dt.timezone.utc)
        self.testInst.load(fname=self.testInst.files[0])
        self.testInst.next()
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_prev_fname_load_default(self):
        """Test prev day is loaded when invoking .prev."""
        self.ref_time = dt.datetime(2008, 1, 3, tzinfo=dt.timezone.utc)
        self.testInst.load(fname=self.testInst.files[3])
        self.testInst.prev()
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_basic_fname_instrument_load(self):
        """Test loading by filename from attached .files.
        """
        self.ref_time = dt.datetime(2008, 1, 1, tzinfo=dt.timezone.utc)
        self.testInst.load(fname=self.testInst.files[0])
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time)
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_filename_load(self):
        """Test if file is loadable by filename, relative to
        top_data_dir/platform/name/tag"""
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'))
        assert self.testInst.index[0] == self.ref_time

    def test_filenames_load(self):
        """Test if files are loadable by filenames, relative to
        top_data_dir/platform/name/tag"""
        stop_fname = self.ref_time + pds.DateOffset(days=1)
        stop_fname = stop_fname.strftime('%Y-%m-%d.nofile')
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'),
                           stop_fname=stop_fname)
        assert self.testInst.index[0] == self.ref_time
        assert self.testInst.index[-1] >= self.ref_time + pds.DateOffset(days=1)
        assert self.testInst.index[-1] <= self.ref_time + pds.DateOffset(days=2)

    def test_filenames_load_out_of_order(self):
        """Test error raised if fnames out of temporal order"""
        stop_fname = self.ref_time + pds.DateOffset(days=1)
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
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_prev_filename_load_default(self):
        """Test prev day is loaded when invoking .prev."""
        self.testInst.load(fname=self.ref_time.strftime('%Y-%m-%d.nofile'))
        self.testInst.prev()
        self.out = self.testInst.index[0]
        assert (self.out == self.ref_time - dt.timedelta(days=1))
        self.out = dt.datetime(self.out.year, self.out.month, self.out.day,
                               tzinfo=dt.timezone.utc)
        assert (self.out == self.testInst.date)

    def test_list_files(self):
        files = self.testInst.files.files
        assert isinstance(files, pds.Series)

    def test_remote_file_list(self):
        stop = self.ref_time + dt.timedelta(days=30)
        self.out = self.testInst.remote_file_list(start=self.ref_time,
                                                  stop=stop)
        assert self.out.index[0] == self.ref_time
        assert self.out.index[-1] == stop

    def test_remote_date_range(self):
        stop = self.ref_time + dt.timedelta(days=30)
        self.out = self.testInst.remote_date_range(start=self.ref_time,
                                                   stop=stop)
        assert len(self.out) == 2
        assert self.out[0] == self.ref_time
        assert self.out[-1] == stop

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
        # Perform a local search
        assert "local files" in caplog.text
        # New files are found
        assert "that are new or updated" in caplog.text
        # download new files
        assert "Downloading data to" in caplog.text
        # Update local file list
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
        # Tells user that recent data will be downloaded
        assert "most recent data by default" in caplog.text
        # download new files
        assert "Downloading data to" in caplog.text
        # Update local file list
        assert "Updating pysat file list" in caplog.text

    # -------------------------------------------------------------------------
    #
    # Test date helpers
    #
    # -------------------------------------------------------------------------
    def test_today_yesterday_and_tomorrow(self):
        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day, tzinfo=dt.timezone.utc)
        assert self.out == self.testInst.today()
        assert self.out - pds.DateOffset(days=1) == self.testInst.yesterday()
        assert self.out + pds.DateOffset(days=1) == self.testInst.tomorrow()

    def test_filter_datetime(self):
        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day, tzinfo=dt.timezone.utc)
        assert self.out == self.testInst._filter_datetime_input(self.ref_time)

    def test_filtered_date_attribute(self):
        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day, tzinfo=dt.timezone.utc)
        self.testInst.date = self.ref_time
        assert self.out == self.testInst.date

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
        assert self.testInst.empty

    def test_empty_flag_data_not_empty(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert not self.testInst.empty

    # -------------------------------------------------------------------------
    #
    # Test index attribute, should always be a datetime index
    #
    # -------------------------------------------------------------------------
    def test_index_attribute(self):
        # empty Instrument test
        assert isinstance(self.testInst.index, pds.Index)
        # now repeat the same test but with data loaded
        self.testInst.load(self.ref_time.year, self.ref_doy)
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

    # -------------------------------------------------------------------------
    #
    # test textual representations
    #
    # -------------------------------------------------------------------------
    def test_basic_repr(self):
        """The repr output will match the beginning of the str output"""
        self.out = self.testInst.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("Instrument(") == 0

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
        self.testInst.pad = pds.DateOffset(minutes=5)
        self.out = self.testInst.__str__()
        assert self.out.find('DateOffset: minutes=5') > 0

    def test_str_w_custom_func(self):
        """Test string output with custom function """
        def testfunc(self):
            pass
        self.testInst.custom.attach(testfunc, 'modify')
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
        self.ref_time = dt.datetime(2009, 2, 1, tzinfo=dt.timezone.utc)
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
    # Test basic data access features, both getting and setting data
    #
    # -------------------------------------------------------------------------
    def test_basic_data_access_by_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst['mlt'] == self.testInst.data['mlt'])

    def test_basic_data_access_by_name_list(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[['longitude', 'mlt']]
                      == self.testInst.data[['longitude', 'mlt']])

    def test_data_access_by_row_slicing_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[0:10, 'mlt']
                      == self.testInst.data['mlt'].values[0:10])

    def test_data_access_by_row_slicing_and_name_slicing(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        result = self.testInst[0:10, :]
        for variable, array in result.items():
            assert len(array) == len(self.testInst.data[variable].values[0:10])
            assert np.all(array == self.testInst.data[variable].values[0:10])

    def test_data_access_by_row_slicing_w_ndarray_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[np.arange(0, 10), 'mlt']
                      == self.testInst.data['mlt'].values[0:10])

    def test_data_access_by_row_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[0, 'mlt']
                      == self.testInst.data['mlt'].values[0])

    def test_data_access_by_row_index(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = np.arange(10)
        assert np.all(self.testInst[self.out]['mlt']
                      == self.testInst.data['mlt'].values[self.out])

    def test_data_access_by_datetime_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.out = dt.datetime(2009, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
        assert np.all(self.testInst[self.out, 'mlt']
                      == self.testInst.data['mlt'].values[0])

    def test_data_access_by_datetime_slicing_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        time_step = (self.testInst.index[1]
                     - self.testInst.index[0]).value / 1.E9
        offset = pds.DateOffset(seconds=(10 * time_step))
        start = dt.datetime(2009, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
        stop = start + offset
        assert np.all(self.testInst[start:stop, 'mlt']
                      == self.testInst.data['mlt'].values[0:11])

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
        assert np.all(self.testInst['doubleMLT'].values
                      == 2. * self.testInst['mlt'].values)
        assert np.all(self.testInst['tripleMLT'].values
                      == 3. * self.testInst['mlt'].values)

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
            # This command does not work for xarray
            assert True

    def test_setting_partial_data_by_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[0, 'doubleMLT'] = 0
        assert np.all(self.testInst[1:, 'doubleMLT']
                      == 2. * self.testInst[1:, 'mlt'])
        assert self.testInst[0, 'doubleMLT'] == 0

    def test_setting_partial_data_by_integer_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[[0, 1, 2, 3], 'doubleMLT'] = 0
        assert np.all(self.testInst[4:, 'doubleMLT']
                      == 2. * self.testInst[4:, 'mlt'])
        assert np.all(self.testInst[[0, 1, 2, 3], 'doubleMLT'] == 0)

    def test_setting_partial_data_by_slice_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[0:10, 'doubleMLT'] = 0
        assert np.all(self.testInst[10:, 'doubleMLT']
                      == 2. * self.testInst[10:, 'mlt'])
        assert np.all(self.testInst[0:10, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_index_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[self.testInst.index[0:10], 'doubleMLT'] = 0
        assert np.all(self.testInst[10:, 'doubleMLT']
                      == 2. * self.testInst[10:, 'mlt'])
        assert np.all(self.testInst[0:10, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_numpy_array_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[np.array([0, 1, 2, 3]), 'doubleMLT'] = 0
        assert np.all(self.testInst[4:, 'doubleMLT']
                      == 2. * self.testInst[4:, 'mlt'])
        assert np.all(self.testInst[0:4, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_datetime_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst[dt.datetime(2009, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc),
                      'doubleMLT'] = 0
        assert np.all(self.testInst[0, 'doubleMLT']
                      == 2. * self.testInst[0, 'mlt'])
        assert np.all(self.testInst[0, 'doubleMLT'] == 0)

    def test_setting_partial_data_by_datetime_slicing_and_name(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        time_step = (self.testInst.index[1]
                     - self.testInst.index[0]).value / 1.E9
        offset = pds.DateOffset(seconds=(10 * time_step))
        start = dt.datetime(2009, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
        stop = start + offset
        self.testInst[start:stop, 'doubleMLT'] = 0
        assert np.all(self.testInst[11:, 'doubleMLT']
                      == 2. * self.testInst[11:, 'mlt'])
        assert np.all(self.testInst[0:11, 'doubleMLT'] == 0)

    def test_modifying_data_inplace(self):
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = 2. * self.testInst['mlt']
        self.testInst['doubleMLT'] += 100
        assert np.all(self.testInst['doubleMLT']
                      == 2. * self.testInst['mlt'] + 100)

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
        assert len(np.unique(dates)) == len(insts)

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
        stop = self.ref_time + pds.DateOffset(days=14)
        stop = stop.to_pydatetime()
        self.testInst.bounds = (start, stop, 'M')
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='M').tolist())

    def test_iterate_bounds_with_frequency(self):
        """Test iterating bounds with non-default step"""
        start = self.ref_time
        stop = self.ref_time + pds.DateOffset(days=15)
        stop = stop.to_pydatetime()
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
        self.testInst.bounds = (start, stop, '10D', pds.DateOffset(days=10))
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
                check -= pds.DateOffset(days=1)
                assert trange[1] > check
                check = out['stops'][b_range] + pds.DateOffset(days=1)
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
                check -= pds.DateOffset(days=1)
                assert trange[1] > check
                check = out['stops'][b_range] + pds.DateOffset(days=1)
                assert trange[1] < check
                if i == 0:
                    # check first load is before end of bounds
                    check = out['stops'][b_range] - out['width']
                    check += pds.DateOffset(days=1)
                    assert trange[0] == check
                    assert trange[1] > out['stops'][b_range]
                    check = out['stops'][b_range] + pds.DateOffset(days=1)
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
                check -= pds.DateOffset(days=1)
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
                check -= pds.DateOffset(days=1)
                assert trange[1] > check
                check = out['stops'][b_range] + pds.DateOffset(days=1)
                assert trange[1] < check
                if i == 0:
                    # check first load is before end of bounds
                    check = out['stops'][b_range] - out['width']
                    check += pds.DateOffset(days=1)
                    assert trange[0] < check
                    assert trange[1] < out['stops'][b_range]
                elif i == len(out['observed_times']) - 1:
                    # last load at start of bounds
                    assert trange[0] == out['starts'][b_range]
                    assert trange[1] > out['starts'][b_range]
                    assert trange[1] < out['starts'][b_range] + out['width']

        return

    @pytest.mark.parametrize("values",
                             [(dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=3)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                               '3D', pds.DateOffset(days=1)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 17, tzinfo=dt.timezone.utc),
                               '5D', pds.DateOffset(days=1))])
    def test_iterate_bounds_with_frequency_and_width(self, values):
        """Iterate via date with mixed step/width, excludes stop date"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               '3D', pds.DateOffset(days=1)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               '1D', pds.DateOffset(days=4)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                               '4D', pds.DateOffset(days=1)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=3)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                               '3D', pds.DateOffset(days=2))])
    def test_iterate_bounds_with_frequency_and_width_incl(self, values):
        """Iterate via date with mixed step/width, includes stop date"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 10, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 9, tzinfo=dt.timezone.utc),
                               '4D', pds.DateOffset(days=1)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               '1D', pds.DateOffset(days=3)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               '1D', pds.DateOffset(days=11))])
    def test_next_date_with_frequency_and_width_incl(self, values):
        """Test .next() via date step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 12, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=3)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 13, tzinfo=dt.timezone.utc),
                               '3D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                               '4D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 12, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=1))])
    def test_next_date_with_frequency_and_width(self, values):
        """Test .next() via date step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 13,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=2)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 7, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 16,
                                            tzinfo=dt.timezone.utc)),
                               '3D', pds.DateOffset(days=1)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 6, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=4))])
    def test_next_date_season_frequency_and_width_incl(self, values):
        """Test .next() via date season step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 12,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=2)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 6, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)),
                               '3D', pds.DateOffset(days=1)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 7, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 16,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=4))])
    def test_next_date_season_frequency_and_width(self, values):
        """Test .next() via date season step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 10, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 9, tzinfo=dt.timezone.utc),
                               '4D', pds.DateOffset(days=1)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               '1D', pds.DateOffset(days=3)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               '1D', pds.DateOffset(days=11))])
    def test_prev_date_with_frequency_and_width_incl(self, values):
        """Test .prev() via date step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values",
                             [(dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 12, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=3)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 13, tzinfo=dt.timezone.utc),
                               '3D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                               '4D', pds.DateOffset(days=2)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 12, tzinfo=dt.timezone.utc),
                               '2D', pds.DateOffset(days=1))])
    def test_prev_date_with_frequency_and_width(self, values):
        """Test .prev() via date step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values",
                             [((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 13,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=2)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 7, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 16,
                                            tzinfo=dt.timezone.utc)),
                               '3D', pds.DateOffset(days=1)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 6, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=4))])
    def test_prev_date_season_frequency_and_width_incl(self, values):
        """Test .prev() via date season step/width>1, includes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values",
                             [((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 12,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=2)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 6, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)),
                               '3D', pds.DateOffset(days=1)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 7, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 16,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=4))])
    def test_prev_date_season_frequency_and_width(self, values):
        """Test .prev() via date season step/width>1, excludes stop date"""
        out = self.support_iter_evaluations(values, reverse=True)

        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    def test_set_bounds_too_few(self):
        start = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start]

    def test_set_bounds_mixed(self):
        start = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, '2009-01-01.nofile']

    def test_set_bounds_wrong_type(self):
        """Test Exception when setting bounds with inconsistent types"""
        start = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, 1]

    def test_set_bounds_mixed_iterable(self):
        start = [dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)] * 2
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, '2009-01-01.nofile']

    def test_set_bounds_mixed_iterabless(self):
        start = [dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)] * 2
        with pytest.raises(ValueError):
            self.testInst.bounds = [start, [dt.datetime(2009, 1, 1,
                                                        tzinfo=dt.timezone.utc),
                                            '2009-01-01.nofile']]

    def test_set_bounds_string_default_start(self):
        self.testInst.bounds = [None, '2009-01-01.nofile']
        assert self.testInst.bounds[0][0] == self.testInst.files[0]

    def test_set_bounds_string_default_end(self):
        self.testInst.bounds = ['2009-01-01.nofile', None]
        assert self.testInst.bounds[1][0] == self.testInst.files[-1]

    def test_set_bounds_too_many(self):
        """Ensure error if too many inputs to inst.bounds"""
        start = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        width = pds.DateOffset(days=1)
        with pytest.raises(ValueError) as err:
            self.testInst.bounds = [start, stop, '1D', width, False]
        estr = 'Too many input arguments.'
        assert str(err).find(estr) >= 0

    def test_set_bounds_by_date(self):
        """Test setting bounds with datetimes over simple range"""
        start = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop = dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc)
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop).tolist())

    def test_set_bounds_by_date_wrong_order(self):
        """Test error if bounds assignment has stop date before start"""
        start = dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc)
        stop = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
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
        start = dt.datetime(2009, 1, 1, 1, 10, tzinfo=dt.timezone.utc)
        stop = dt.datetime(2009, 1, 15, 1, 10, tzinfo=dt.timezone.utc)
        self.testInst.bounds = (start, stop)
        start = self.testInst._filter_datetime_input(start)
        stop = self.testInst._filter_datetime_input(stop)
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop).tolist())

    @pytest.mark.parametrize("start,stop",
                             [(dt.datetime(2008, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2010, 12, 31,
                                           tzinfo=dt.timezone.utc)),
                              (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               dt.datetime(2009, 1, 15,
                                           tzinfo=dt.timezone.utc))])
    def test_iterate_over_bounds_set_by_date(self, start, stop):
        """Test iterating over bounds via single date range"""
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
        start = [dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                 dt.datetime(2009, 2, 1, tzinfo=dt.timezone.utc)]
        stop = [dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc),
                dt.datetime(2009, 2, 15, tzinfo=dt.timezone.utc)]
        self.testInst.bounds = (start, stop)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(self.testInst._iter_list == out)

    def test_set_bounds_by_date_season_wrong_order(self):
        """Test error if bounds season assignment has stop date before start"""
        start = [dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                 dt.datetime(2009, 2, 1, tzinfo=dt.timezone.utc)]
        stop = [dt.datetime(2009, 1, 12, tzinfo=dt.timezone.utc),
                dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc)]
        with pytest.raises(Exception) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be set in increasing'
        assert str(err).find(estr) >= 0

    def test_set_bounds_by_date_season_extra_time(self):
        start = [dt.datetime(2009, 1, 1, 1, 10, tzinfo=dt.timezone.utc),
                 dt.datetime(2009, 2, 1, 1, 10, tzinfo=dt.timezone.utc)]
        stop = [dt.datetime(2009, 1, 15, 1, 10, tzinfo=dt.timezone.utc),
                dt.datetime(2009, 2, 15, 1, 10, tzinfo=dt.timezone.utc)]
        self.testInst.bounds = (start, stop)
        start = self.testInst._filter_datetime_input(start)
        stop = self.testInst._filter_datetime_input(stop)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(self.testInst._iter_list == out)

    def test_iterate_over_bounds_set_by_date_season(self):
        start = [dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                 dt.datetime(2009, 2, 1, tzinfo=dt.timezone.utc)]
        stop = [dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc),
                dt.datetime(2009, 2, 15, tzinfo=dt.timezone.utc)]
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(dates == out)

    @pytest.mark.parametrize("values",
                             [((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 12,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=2)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 6, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)),
                               '3D', pds.DateOffset(days=1)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 7, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 16,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=4))])
    def test_iterate_over_bounds_set_by_date_season_step_width(self, values):
        """Iterate over season, step/width > 1, excludes stop bounds"""

        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 13,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=2)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 7, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 16,
                                            tzinfo=dt.timezone.utc)),
                               '3D', pds.DateOffset(days=1)),
                              ((dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 10,
                                            tzinfo=dt.timezone.utc)),
                               (dt.datetime(2009, 1, 6, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)),
                               '2D', pds.DateOffset(days=4))])
    def test_iterate_bounds_set_by_date_season_step_width_incl(self, values):
        """Iterate over season, step/width > 1, includes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    def test_iterate_over_bounds_set_by_date_season_extra_time(self):
        start = [dt.datetime(2009, 1, 1, 1, 10, tzinfo=dt.timezone.utc),
                 dt.datetime(2009, 2, 1, 1, 10, tzinfo=dt.timezone.utc)]
        stop = [dt.datetime(2009, 1, 15, 1, 10, tzinfo=dt.timezone.utc),
                dt.datetime(2009, 2, 15, 1, 10, tzinfo=dt.timezone.utc)]
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
        assert np.all(self.testInst._iter_list
                      == ['2009-01-01.nofile', '2009-01-02.nofile',
                          '2009-01-03.nofile'])

    def test_iterate_over_bounds_set_by_fname(self):
        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop_d = dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc)
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
        start_d = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop_d = dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc)
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
        start_d = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop_d = dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc)
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
        start_d = [dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                   dt.datetime(2009, 2, 1, tzinfo=dt.timezone.utc)]
        stop_d = [dt.datetime(2009, 1, 15, tzinfo=dt.timezone.utc),
                  dt.datetime(2009, 2, 15, tzinfo=dt.timezone.utc)]
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
        start_date = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc)
        self.testInst.bounds = (start, stop, 2)
        out = pds.date_range(start_date, stop_date, freq='2D').tolist()

        # Evaluate each filename date
        for i, item in enumerate(self.testInst._iter_list):
            snip = item.split('.')[0]
            ref_snip = out[i].strftime('%Y-%m-%d')
            assert snip == ref_snip

    def test_iterate_bounds_fname_with_frequency(self):
        """Test iterate over bounds using filenames and non-default step"""
        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc)
        self.testInst.bounds = (start, stop, 2)

        dates = []
        for inst in self.testInst:
            dates.append(inst.date)
        out = pds.date_range(start_date, stop_date, freq='2D').tolist()
        assert np.all(dates == out)

    def test_set_bounds_fname_with_frequency_and_width(self):
        """Set fname bounds with step/width>1"""
        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc)
        self.testInst.bounds = (start, stop, 2, 2)
        out = pds.date_range(start_date, stop_date - pds.DateOffset(days=1),
                             freq='2D').tolist()
        # convert filenames in list to a date
        date_list = []
        for i, item in enumerate(self.testInst._iter_list):
            snip = item.split('.')[0]
            ref_snip = out[i].strftime('%Y-%m-%d')
            assert snip == ref_snip

    @pytest.mark.parametrize("values",
                             [('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-03.nofile',
                               dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                               2, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-04.nofile',
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               2, 3),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-05.nofile',
                               dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                               3, 1)])
    def test_iterate_bounds_fname_with_frequency_and_width(self, values):
        """File iteration in bounds with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-04.nofile',
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               2, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-04.nofile',
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               3, 1),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-04.nofile',
                               dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                               1, 4),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-05.nofile',
                               dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                               2, 3)])
    def test_iterate_bounds_fname_with_frequency_and_width_incl(self, values):
        """File iteration in bounds with step/width>1, includes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-03.nofile', '2009-01-13.nofile'),
                               (dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 13,
                                            tzinfo=dt.timezone.utc)), 2, 2),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 2, 3),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-05.nofile', '2009-01-15.nofile'),
                               (dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)), 3, 1)])
    def test_iterate_fname_season_with_frequency_and_width(self, values):
        """File season iteration with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 2, 2),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 3, 1),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 1, 4),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-05.nofile', '2009-01-15.nofile'),
                               (dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)), 2, 3)])
    def test_iterate_fname_season_with_frequency_and_width_incl(self, values):
        """File iteration in bounds with step/width>1, includes stop bounds"""
        out = self.support_iter_evaluations(values, for_loop=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 11,
                                           tzinfo=dt.timezone.utc), 2, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-12.nofile',
                               dt.datetime(2009, 1, 12,
                                           tzinfo=dt.timezone.utc), 2, 3),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-13.nofile',
                               dt.datetime(2009, 1, 13,
                                           tzinfo=dt.timezone.utc), 3, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-03.nofile',
                               dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                               4, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-12.nofile',
                               dt.datetime(2009, 1, 12,
                                           tzinfo=dt.timezone.utc), 2, 1)])
    def test_next_fname_with_frequency_and_width(self, values):
        """Test .next() via fname step/width>1, excludes stop file"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 10, tzinfo=dt.timezone.utc),
                               2, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-09.nofile',
                               dt.datetime(2009, 1, 9, tzinfo=dt.timezone.utc),
                               4, 1),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               1, 3),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               1, 11)])
    def test_next_fname_with_frequency_and_width_incl(self, values):
        """Test .next() via fname step/width>1, includes stop file"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-03.nofile', '2009-01-13.nofile'),
                               (dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 13,
                                            tzinfo=dt.timezone.utc)), 2, 2),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 2, 3),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-05.nofile', '2009-01-15.nofile'),
                               (dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)), 3, 1)])
    def test_next_fname_season_with_frequency_and_width(self, values):
        """File next season with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [(('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 2, 2),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 3, 1),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 1, 4),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-05.nofile', '2009-01-15.nofile'),
                               (dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)), 2, 3)])
    def test_next_fname_season_with_frequency_and_width_incl(self, values):
        """File next season with step/width>1, includes stop bounds"""
        out = self.support_iter_evaluations(values)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=True)

        return

    @pytest.mark.parametrize("values",
                             [('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               2, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-12.nofile',
                               dt.datetime(2009, 1, 12, tzinfo=dt.timezone.utc),
                               2, 3),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-13.nofile',
                               dt.datetime(2009, 1, 13, tzinfo=dt.timezone.utc),
                               3, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-03.nofile',
                               dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                               4, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-12.nofile',
                               dt.datetime(2009, 1, 12, tzinfo=dt.timezone.utc),
                               2, 1)])
    def test_prev_fname_with_frequency_and_width(self, values):
        """Test prev() fname step/width>1, excludes stop bound"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values",
                             [('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 10, tzinfo=dt.timezone.utc),
                               2, 2),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-09.nofile',
                               dt.datetime(2009, 1, 9, tzinfo=dt.timezone.utc),
                               4, 1),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               1, 3),
                              ('2009-01-01.nofile',
                               dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                               '2009-01-11.nofile',
                               dt.datetime(2009, 1, 11, tzinfo=dt.timezone.utc),
                               1, 11)])
    def test_prev_fname_with_frequency_and_width_incl(self, values):
        """Test prev() fname step/width>1, includes bounds stop date"""

        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_inclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values",
                             [(('2009-01-01.nofile',  '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-03.nofile', '2009-01-13.nofile'),
                               (dt.datetime(2009, 1, 3, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 13,
                                            tzinfo=dt.timezone.utc)), 2, 2),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 2, 3),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-05.nofile', '2009-01-15.nofile'),
                               (dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)), 3, 1)])
    def test_prev_fname_season_with_frequency_and_width(self, values):
        """File prev season with step/width>1, excludes stop bounds"""
        out = self.support_iter_evaluations(values, reverse=True)
        # verify range of loaded data
        self.verify_exclusive_iteration(out, forward=False)

        return

    @pytest.mark.parametrize("values",
                             [(('2009-01-01.nofile',  '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 2, 2),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 3, 1),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-04.nofile', '2009-01-14.nofile'),
                               (dt.datetime(2009, 1, 4, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 14,
                                            tzinfo=dt.timezone.utc)), 1, 4),
                              (('2009-01-01.nofile', '2009-01-11.nofile'),
                               (dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 11,
                                            tzinfo=dt.timezone.utc)),
                               ('2009-01-05.nofile', '2009-01-15.nofile'),
                               (dt.datetime(2009, 1, 5, tzinfo=dt.timezone.utc),
                                dt.datetime(2009, 1, 15,
                                            tzinfo=dt.timezone.utc)), 2, 3)])
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
            # both name and platform should be empty
            _ = pysat.Instrument(platform='cnofs')
        estr = 'Inputs platform and name must both'
        assert str(err).find(estr) >= 0

    def test_supplying_instrument_module_requires_name_and_platform(self):
        """Ensure instantiation via inst_module with missing name errors"""
        class Dummy:
            pass
        Dummy.name = 'help'

        with pytest.raises(AttributeError) as err:
            _ = pysat.Instrument(inst_module=Dummy)
        estr = 'Supplied module '
        assert str(err).find(estr) >= 0


# -----------------------------------------------------------------------------
#
# Repeat tests above with xarray data
#
# -----------------------------------------------------------------------------
class TestBasicsXarray(TestBasics):
    def setup(self):
        reload(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True)
        self.ref_time = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
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
        reload(pysat.instruments.pysat_testing2d)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing2d',
                                         num_samples=50,
                                         clean_level='clean',
                                         update_files=True)
        self.ref_time = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
        self.ref_doy = 1
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.out, self.ref_time, self.ref_doy


# -----------------------------------------------------------------------------
#
# Repeat TestBasics above with shifted file dates
#
# -----------------------------------------------------------------------------

class TestBasicsShiftedFileDates(TestBasics):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         mangle_file_dates=True,
                                         strict_time_flag=True)
        self.ref_time = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
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
        self.ref_time = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
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
        self.ref_time = dt.datetime(2009, 1, 1, tzinfo=dt.timezone.utc)
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
        self.delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_next(self):
        """Test data padding loading by filename when using next"""
        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[2])
        self.delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_multi_next(self):
        """Test data padding loading by filename when using next multiple times
        """
        self.testInst.load(fname=self.testInst.files[1])
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[3])
        self.delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_prev(self):
        """Test data padding loading by filename when using prev"""
        self.testInst.load(fname=self.testInst.files[2], verifyPad=True)
        self.testInst.prev(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[1])
        self.delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_multi_prev(self):
        """Test data padding loading by filename when using prev multiple times
        """
        self.testInst.load(fname=self.testInst.files[10])
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[8])
        self.delta = pds.DateOffset(minutes=5)
        assert (self.testInst.index[0] == self.rawInst.index[0] - self.delta)
        assert (self.testInst.index[-1] == self.rawInst.index[-1] + self.delta)

    def test_fname_data_padding_jump(self):
        """Test data padding by filename after loading non-consecutive file"""
        self.testInst.load(fname=self.testInst.files[1], verifyPad=True)
        self.testInst.load(fname=self.testInst.files[10], verifyPad=True)
        self.rawInst.load(fname=self.testInst.files[10])
        self.delta = pds.DateOffset(minutes=5)
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
        self.ref_time = dt.datetime(2009, 1, 2, tzinfo=dt.timezone.utc)
        self.ref_doy = 2

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.ref_time, self.ref_doy

    def test_data_padding(self):
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        assert (self.testInst.index[0]
                == self.testInst.date - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_offset_instantiation(self):
        testInst = pysat.Instrument(platform='pysat', name='testing',
                                    clean_level='clean',
                                    pad=pds.DateOffset(minutes=5),
                                    update_files=True)
        testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        assert (testInst.index[0] == testInst.date - pds.DateOffset(minutes=5))
        assert (testInst.index[-1] == testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_bad_instantiation(self):
        """Ensure error when padding input type incorrect"""
        with pytest.raises(ValueError) as err:
            pysat.Instrument(platform='pysat', name='testing',
                             clean_level='clean',
                             pad=2,
                             update_files=True)
        estr = 'pad must be a dict, NoneType, or pandas.DateOffset instance.'
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
               + pds.DateOffset(days=1)

        self.testInst.load(yr, doy)
        assert self.testInst.index[0] == self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + pds.DateOffset(days=1)

    def test_yrdoy_data_padding_missing_later_days(self):
        """Test padding feature operates when there are missing later days"""
        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.stop_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] < self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + pds.DateOffset(days=1)

        self.testInst.load(yr, doy)
        assert self.testInst.index[0] == self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + pds.DateOffset(days=1)

    def test_yrdoy_data_padding_missing_earlier_and_later_days(self):
        """Test padding feature operates when missing earlier/later days"""
        # reduce available files
        self.testInst.files.files = self.testInst.files.files[0:1]
        yr, doy = pysat.utils.time.getyrdoy(self.testInst.files.start_date)
        self.testInst.load(yr, doy, verifyPad=True)
        assert self.testInst.index[0] == self.testInst.date
        assert self.testInst.index[-1] < self.testInst.date \
               + pds.DateOffset(days=1)

    def test_data_padding_next(self):
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.next(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_multi_next(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_prev(self):
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.prev(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_multi_prev(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.ref_doy = 10
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        assert (self.testInst.index[0] == self.testInst.date
                - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1] == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

    def test_data_padding_jump(self):
        self.testInst.load(self.ref_time.year, self.ref_doy, verifyPad=True)
        self.testInst.load(self.ref_time.year, self.ref_doy + 10,
                           verifyPad=True)
        assert (self.testInst.index[0]
                == self.testInst.date - pds.DateOffset(minutes=5))
        assert (self.testInst.index[-1]
                == self.testInst.date
                + pds.DateOffset(hours=23, minutes=59, seconds=59)
                + pds.DateOffset(minutes=5))

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
                + pds.DateOffset(hour=23, minutes=59, seconds=59))


class TestDataPaddingXarray(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing_xarray)
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         clean_level='clean',
                                         pad={'minutes': 5},
                                         update_files=True)
        self.ref_time = dt.datetime(2009, 1, 2, tzinfo=dt.timezone.utc)
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
                                         pad={'minutes': 5},
                                         multi_file_day=True)
        self.ref_time = dt.datetime(2009, 1, 2, tzinfo=dt.timezone.utc)
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
                                         pad={'minutes': 5},
                                         multi_file_day=True)
        self.ref_time = dt.datetime(2009, 1, 2, tzinfo=dt.timezone.utc)
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
                                         pad={'minutes': 5},
                                         multi_file_day=True)
        self.ref_time = dt.datetime(2009, 1, 2, tzinfo=dt.timezone.utc)
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
                                         pad={'minutes': 5},
                                         multi_file_day=True)
        self.ref_time = dt.datetime(2009, 1, 2, tzinfo=dt.timezone.utc)
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
        """Check that instruments without _test_dates are still included
        """
        del self.test_library.pysat_testing._test_dates
        # If an instrument does not have the _test_dates attribute, it should
        # still be added to the list for other checks to be run
        # This will be caught later by InstTestClass.test_instrument_test_dates
        assert not hasattr(self.test_library.pysat_testing, '_test_dates')
        inst_list = generate_instrument_list(self.test_library)
        assert 'pysat_testing' in inst_list['names']
