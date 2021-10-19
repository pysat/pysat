"""Tests for data access and related functions in the pysat Instrument object.

Includes:
* data loading
* equality method comparisons
* index tests
* setter and getter functions
* concat
* empty data flags
* variable renaming

Note
----
Base class stored here, but tests inherited by test_instrument.py

"""

import datetime as dt
from importlib import reload
import logging
import numpy as np

import pandas as pds
import pytest
import xarray as xr

import pysat

logger = pysat.logger


class InstAccessTests(object):
    """Basic tests for `pysat.Instrument` data access.

    Note
    ----
    Inherited by classes in test_instrument.py.  Setup and teardown methods are
    specified there.

    See Also
    --------
    `pysat.tests.test_instrument`

    """

    def eval_successful_load(self, end_date=None):
        """Evaluate successful loading of `self.testInst`.

        Parameters
        ----------
        end_date : dt.datetime or NoneType
            End date for loading data.  If None, assumes self.ref_time + 1 day.
            (default=None)

        Note
        ----
        Success of test is tied to `self.ref_time`.

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

    @pytest.mark.parametrize("kwargs", [{}, {'num_samples': 30}])
    def test_basic_instrument_load(self, kwargs):
        """Test that the correct day loads with input year and doy.

        Parameters
        ----------
        kwargs : dict
            Dictionary of keywords and arguments to invoke when loading.

        """

        # Load data by year and day of year
        self.testInst.load(self.ref_time.year, self.ref_doy, **kwargs)

        # Test that the loaded date range is correct
        self.eval_successful_load()
        return

    def test_basic_instrument_load_no_data(self, caplog):
        """Test Instrument load with no data for appropriate log messages.

        """

        # Get a date that is not covered by an Instrument object.
        no_data_d = self.testInst.files.files.index[0] - dt.timedelta(weeks=10)

        with caplog.at_level(logging.INFO, logger='pysat'):

            # Attempt to load data for a date with no data
            self.testInst.load(date=no_data_d)

            # Confirm by checking against caplog that metadata was
            # not assigned.
            captured = caplog.text

            assert captured.find("Metadata was not assigned as there") >= 0

            # Generate string to verify proper no data message
            output_str = '{platform} {name} {tag} {inst_id}'
            output_str = output_str.format(platform=self.testInst.platform,
                                           name=self.testInst.name,
                                           tag=self.testInst.tag,
                                           inst_id=self.testInst.inst_id)
            output_str = ''.join(("No ", output_str))

            # Remove any extra spaces. Follows code in _instrument.
            output_str = " ".join(output_str.split())

            assert captured.find(output_str) >= 0

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

    def test_basic_instrument_bad_keyword_at_load(self):
        """Check for error when calling load with bad keywords."""

        # Test that the correct error is raised
        with pytest.raises(TypeError) as terr:
            self.testInst.load(date=self.ref_time, unsupported_keyword=True)

        # Evaluate error message
        assert str(terr).find("load() got an unexpected keyword") >= 0
        return

    def test_basic_instrument_load_yr_no_doy(self):
        """Ensure day of year required if year is present."""

        # Check that the correct error is raised
        with pytest.raises(TypeError) as err:
            self.testInst.load(self.ref_time.year)

        # Check that the error message is correct
        estr = 'Unknown or incomplete input combination.'
        assert str(err).find(estr) >= 0
        return

    @pytest.mark.parametrize('doy', [0, 367, 1000, -1, -10000])
    def test_basic_instrument_load_yr_bad_doy(self, doy):
        """Ensure error raised if day of year load argument out of valid range.

        Parameters
        ----------
        doy : int
            Day of year to create an error when loading.

        """

        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, doy)
        estr = 'Day of year (doy) is only valid between and '
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize('end_doy', [0, 367, 1000, -1, -10000])
    def test_basic_instrument_load_yr_bad_end_doy(self, end_doy):
        """Ensure error raised if `end_doy` keyword out of valid range.

        Parameters
        ----------
        end_doy : int
            Day of year to create an error when loading by end_date.

        """

        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, 1, end_yr=self.ref_time.year,
                               end_doy=end_doy)
        estr = 'Day of year (end_doy) is only valid between and '
        assert str(err).find(estr) >= 0

        return

    def test_basic_instrument_load_yr_no_end_doy(self):
        """Ensure `end_doy` required if `end_yr` present."""

        with pytest.raises(ValueError) as err:
            self.testInst.load(self.ref_time.year, self.ref_doy,
                               self.ref_time.year)
        estr = 'Both end_yr and end_doy must be set'
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize("kwargs", [{'yr': 2009, 'doy': 1,
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
    def test_basic_instrument_load_mixed_inputs(self, kwargs):
        """Ensure mixed load inputs raise ValueError.

        Parameters
        ----------
        kwargs : dict
            Dictionary of keywords and arguments to produce an error when
            instrument is loaded.

        """

        with pytest.raises(ValueError) as err:
            self.testInst.load(**kwargs)
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
        """Ensure improper usage of load with `multi_file_day` raises ValueError.

        Parameters
        ----------
        load_in : str or NoneType
            If 'fname', load by filename. If None, load without kwargs.
        verr : str
            Text that should be contained in the error message generated by
            the improper load configuration above.

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
        """Test loading by date."""

        self.testInst.load(date=self.ref_time)
        self.eval_successful_load()
        return

    def test_basic_instrument_load_by_dates(self):
        """Test date range loading, `date` and `end_date`."""

        end_date = self.ref_time + dt.timedelta(days=2)
        self.testInst.load(date=self.ref_time, end_date=end_date)
        self.eval_successful_load(end_date=end_date)
        return

    def test_basic_instrument_load_by_date_with_extra_time(self):
        """Ensure `.load(date=date)` only uses date portion of datetime."""

        # Put in a date that has more than year, month, day
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
        """Test if correct day loads by default when first invoking iteration.

        Parameters
        ----------
        operator : str
            Name of iterator to use.
        ref_time : dt.datetime
            Expected date to load when iteration is first invoked.

        """

        getattr(self.testInst, operator)()

        # Modify ref time since iterator changes load date.
        self.ref_time = ref_time
        self.eval_successful_load()
        return

    @pytest.mark.parametrize("operator", [('next'), ('prev')])
    def test_file_load_bad_start_file(self, operator):
        """Test Error when starting iteration on a file not in iteration list.

        Parameters
        ----------
        operator : str
            Name of iterator to use.

        """

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
        """Test that day iterators raise Error on bad start date.

        Parameters
        ----------
        operator : str
            Name of iterator to use.

        """

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

    def test_basic_fname_instrument_load(self):
        """Test loading by filename from attached `.files`."""

        # If mangle_file_date is true, index will not match exactly.
        # Find the closest point instead.
        ind = np.argmin(abs(self.testInst.files.files.index - self.ref_time))
        self.testInst.load(fname=self.testInst.files[ind])
        self.eval_successful_load()
        return

    @pytest.mark.parametrize("operator,direction",
                             [('next', 1),
                              ('prev', -1)])
    def test_fname_load_default(self, operator, direction):
        """Test correct day loads when moving by day, starting with `fname`.

        Parameters
        ----------
        operator : str
            Name of iterator to use.
        direction : int
            Positive if moving forward, negative if moving backward.

        """

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
        assert inst_copy != self.testInst
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
        assert inst_copy != self.testInst
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

    @pytest.mark.parametrize("prepend, sort_dim_toggle",
                             [(True, True), (True, False), (False, False)])
    def test_concat_data(self, prepend, sort_dim_toggle):
        """Test `pysat.Instrument.data` concatenation.

        Parameters
        ----------
        prepend : bool
            Behavior of `concat_data`.  If True, assign new data before existing
            data; if False append new data.
        sort_dim_toggle : bool
            If True, sort variable names in pandas before concatenation.  If
            False, do not sort for pandas objects.  For xarray objects, rename
            the epoch if True.

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
                data2 = data2.rename({self.xarray_epoch_name: 'Epoch2'})
                self.testInst.data = self.testInst.data.rename(
                    {self.xarray_epoch_name: 'Epoch2'})

        # Concat together
        self.testInst.concat_data(data2, **kwargs)

        if sort_dim_toggle and not self.testInst.pandas_format:
            # Rename to the standard epoch name
            self.testInst.data = self.testInst.data.rename(
                {'Epoch2': self.xarray_epoch_name})

        # Basic test for concatenation
        self.out = len(self.testInst.index)
        assert (self.out == len1 + len2)

        # Detailed test for concatenation through index
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

    def test_empty_flag_data_empty(self):
        """Test the status of the empty flag for unloaded data."""

        assert self.testInst.empty
        return

    def test_empty_flag_data_not_empty(self):
        """Test the status of the empty flag for loaded data."""

        self.testInst.load(date=self.ref_time)
        assert not self.testInst.empty
        return

    def test_index_attribute(self):
        """Test the index attribute before and after loading data."""

        # Test that an index is present, even with an empty Instrument
        assert isinstance(self.testInst.index, pds.Index)

        # Test an index is present with data loaded in an Instrument
        self.testInst.load(date=self.ref_time)
        assert isinstance(self.testInst.index, pds.Index)
        return

    def test_index_return(self):
        """Test that the index is returned in the proper format."""

        # Load data
        self.testInst.load(self.ref_time.year, self.ref_doy)

        # Ensure we get the index back
        if self.testInst.pandas_format:
            assert np.all(self.testInst.index == self.testInst.data.index)
        else:
            assert np.all(self.testInst.index
                          == self.testInst.data.indexes[self.xarray_epoch_name])
        return

    @pytest.mark.parametrize("labels", [('mlt'),
                                        (['mlt', 'longitude']),
                                        (['longitude', 'mlt'])])
    def test_basic_data_access_by_name(self, labels):
        """Check that data can be accessed by name at the instrument level.

        Parameters
        ----------
        labels : list of str
            List of variable names to access.

        """

        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all((self.testInst[labels]
                       == self.testInst.data[labels]).values)
        return

    @pytest.mark.parametrize("index", [(0),
                                       ([0, 1, 2, 3]),
                                       (slice(0, 10)),
                                       (np.arange(0, 10))])
    def test_data_access_by_indices_and_name(self, index):
        """Check that variables can be accessed by each supported index type.

        Parameters
        ----------
        index : int, list, slice, or np.array
            Indices to retrieve data.

        """

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
        """Check that data can be set using each supported index type.

        Parameters
        ----------
        changed : index-like parameters
            Index of values that change during the test.
        fixed : index-like parameters
            Index of values that should remain the same during the test.

        """

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
        """Test getting all data by index.

        Parameters
        ----------
        index : index-like parameters
            Index of values to retrieve.

        """

        self.testInst.load(self.ref_time.year, self.ref_doy)
        inst_subset = self.testInst[index]
        if self.testInst.pandas_format:
            assert len(inst_subset) == len(index)
        else:
            assert inst_subset.sizes[self.xarray_epoch_name] == len(index)
        return

    @pytest.mark.parametrize("values", [{'uts': 'uts1'},
                                        {'uts': 'uts2',
                                         'mlt': 'mlt2'},
                                        {'uts': 'long change with spaces'}])
    def test_basic_variable_renaming(self, values):
        """Test basic variable renaming.

        Parameters
        ----------
        values : dict
            Variables to be renamed.  A dict where each key is the current
            variable and its value is the new variable name.

        """

        # Test single variable
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.rename(values)
        for key in values:
            # Check for new name
            assert values[key] in self.testInst.data
            assert values[key] in self.testInst.meta

            # Ensure old name not present
            assert key not in self.testInst.data
            assert key not in self.testInst.meta
        return

    @pytest.mark.parametrize("values", [{'help': 'I need somebody'},
                                        {'UTS': 'litte_uts'},
                                        {'utS': 'uts1'},
                                        {'utS': 'uts'}])
    def test_unknown_variable_error_renaming(self, values):
        """Test that unknown variable renaming raises an error.

        Parameters
        ----------
        values : dict
            Variables to be renamed.  A dict where each key is the current
            variable and its value is the new variable name.

        """

        # Check for error for unknown variable name
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
        """Test new variable names are converted to lowercase.

        Parameters
        ----------
        values : dict
            Variables to be renamed.  A dict where each key is the current
            variable and its value is the new variable name.

        """

        # Test single variable
        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst.rename(values, lowercase_data_labels=True)
        for key in values:
            # Check for new name
            assert values[key].lower() in self.testInst.data
            assert values[key].lower() in self.testInst.meta

            # Ensure case retained in meta
            assert values[key] == self.testInst.meta[values[key]].name

            # Ensure old name not present
            assert key not in self.testInst.data
            assert key not in self.testInst.meta
        return

    @pytest.mark.parametrize("values", [{'profiles': {'density': 'ionization'}},
                                        {'profiles': {'density': 'mass'},
                                         'alt_profiles':
                                             {'density': 'volume'}}])
    def test_ho_pandas_variable_renaming(self, values):
        """Test rename of higher order pandas variable.

        Parameters
        ----------
        values : dict
            Variables to be renamed.  A dict where each key is the current
            variable and its value is the new variable name.

        """
        # TODO(#789): Remove when meta children support is dropped.

        # Check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(self.ref_time.year, self.ref_doy)
                self.testInst.rename(values)
                for key in values:
                    for ikey in values[key]:
                        # Check column name unchanged
                        assert key in self.testInst.data
                        assert key in self.testInst.meta
                        # Check for new name in HO data
                        assert values[key][ikey] in self.testInst[0, key]
                        check_var = self.testInst.meta[key]['children']
                        assert values[key][ikey] in check_var
                        # Ensure old name not present
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
        """Test higher order pandas variable rename raises error if unknown.

        Parameters
        ----------
        values : dict
            Variables to be renamed.  A dict where each key is the current
            variable and its value is the new variable name.

        """
        # TODO(#789): Remove when meta children support is dropped.

        # Check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(self.ref_time.year, self.ref_doy)

                # Check for error for unknown column or HO variable name
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
        """Test rename higher order pandas variable uses lowercase.

        Parameters
        ----------
        values : dict
            Variables to be renamed.  A dict where each key is the current
            variable and its value is the new variable name.

        """
        # TODO(#789): Remove when meta children support is dropped.

        # Check for pysat_testing2d instrument
        if self.testInst.platform == 'pysat':
            if self.testInst.name == 'testing2d':
                self.testInst.load(self.ref_time.year, self.ref_doy)
                self.testInst.rename(values)
                for key in values:
                    for ikey in values[key]:
                        # Check column name unchanged
                        assert key in self.testInst.data
                        assert key in self.testInst.meta
                        # Check for new name in HO data
                        test_val = values[key][ikey]
                        assert test_val in self.testInst[0, key]
                        check_var = self.testInst.meta[key]['children']
                        # Case insensitive check
                        assert values[key][ikey] in check_var
                        # Ensure new case in there
                        check_var = check_var[values[key][ikey]].name
                        assert values[key][ikey] == check_var
                        # Ensure old name not present
                        assert ikey not in self.testInst[0, key]
                        check_var = self.testInst.meta[key]['children']
                        assert ikey not in check_var
        return
