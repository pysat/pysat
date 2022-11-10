"""Unit tests for the general instrument methods."""

import datetime as dt
from os import path
import pandas as pds
import pytest
import warnings

import pysat
from pysat.instruments.methods import general as gen
from pysat.utils import testing


class TestListFiles(object):
    """Unit tests for `pysat.instrument.methods.general.list_files`."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        fname = 'fake_data_{year:04d}{month:02d}{day:02d}_v05.cdf'
        self.kwargs = {'tag': '', 'inst_id': '', 'data_path': '/fake/path/',
                       'format_str': None,
                       'supported_tags': {'': {'': fname}}}
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.kwargs
        return

    @pytest.mark.parametrize("bad_key,bad_val,err_msg",
                             [("tag", "badval", "Unknown inst_id or tag"),
                              ("inst_id", "badval", "Unknown inst_id or tag")])
    def test_bad_kwarg_list_files(self, bad_key, bad_val, err_msg):
        """Test that bad kwargs raise a ValueError with an expected message.

        Parameters
        ----------
        bad_key : str
            Keyword arg to update
        badval : any type
            Bad value to use with `bad_key`
        err_msg : str
            Expected error message

        """

        self.kwargs[bad_key] = bad_val

        testing.eval_bad_input(gen.list_files, ValueError, err_msg,
                               input_kwargs=self.kwargs)
        return


class TestFileCadence(object):
    """Unit tests for `instruments.methods.general.is_daily_file_cadence`."""

    @pytest.mark.parametrize("time_kwarg, time_val, is_daily",
                             [("microseconds", 1, True), ("seconds", 1, True),
                              ("minutes", 1, True), ("hours", 1, True),
                              ("days", 1, True), ("days", 2, False)])
    def test_datetime_file_cadence(self, time_kwarg, time_val, is_daily):
        """Test `is_daily_file_cadence` with dt.datetime input.

        Parameters
        ----------
        time_kwarg : str
            Keyword argument for `dt.timedelta`
        time_val : int
            Value for keyword argument above
        is_daily : bool
            Target value for internal test files have daily cadence

        """

        in_time = dt.timedelta(**{time_kwarg: time_val})
        check_daily = gen.is_daily_file_cadence(in_time)

        assert check_daily == is_daily
        return

    @pytest.mark.parametrize("time_kwarg, time_val, is_daily",
                             [("microseconds", 1, True), ("seconds", 1, True),
                              ("minutes", 1, True), ("hours", 1, True),
                              ("days", 1, True), ("days", 2, False),
                              ("months", 1, False), ("years", 1, False)])
    def test_dateoffset_file_cadence(self, time_kwarg, time_val, is_daily):
        """Test `is_daily_file_cadence` with pds.DateOffset input.

        Parameters
        ----------
        time_kwarg : str
            Keyword argument for `dt.timedelta`
        time_val : int
            Value for keyword argument above
        is_daily : bool
            Target value for internal test files have daily cadence

        """

        in_time = pds.DateOffset(**{time_kwarg: time_val})
        check_daily = gen.is_daily_file_cadence(in_time)

        assert check_daily == is_daily
        return


class TestRemoveLeadText(object):
    """Unit tests for `pysat.instrument.methods.general.remove_leading_text`."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=12,
                                         clean_level='clean', use_header=True)
        self.testInst.load(2009, 1)
        self.npts = len(self.testInst['uts'])
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.npts
        return

    def test_remove_prefix_w_bad_target(self):
        """Test that a bad target in `remove_leading_text` raises an error."""

        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']

        testing.eval_bad_input(gen.remove_leading_text, ValueError,
                               'target must be a string or list of strings',
                               input_args=[self.testInst],
                               input_kwargs={'target': 17.5})
        return

    def test_remove_names_wo_target(self):
        """Test that an unspecified target leaves variable names unchanged."""

        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst)

        # Check variables unchanged
        assert len(self.testInst['ICON_L27_Blurp']) == self.npts

        # Check other names untouched
        assert len(self.testInst['dummy1']) == self.npts
        return

    def test_remove_names_w_target(self):
        """Test that only names with the target prefix are changed."""

        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst, target='ICON_L27')

        # Check prepended text removed
        assert len(self.testInst['_Blurp']) == self.npts

        # Check other names untouched
        assert len(self.testInst['dummy1']) == self.npts

        # Check prepended text removed from metadata
        assert '_Blurp' in self.testInst.meta.keys()
        return

    def test_remove_names_w_target_list(self):
        """Test that multiple targets can be removed via a list."""

        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        self.testInst['ICON_L23_Bloop'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst,
                                target=['ICON_L27', 'ICON_L23_B'])

        # Check prepended text removed
        assert len(self.testInst['_Blurp']) == self.npts
        assert len(self.testInst['loop']) == self.npts

        # Check other names untouched
        assert len(self.testInst['dummy1']) == self.npts

        # Check prepended text removed from metadata
        assert '_Blurp' in self.testInst.meta.keys()
        assert 'loop' in self.testInst.meta.keys()
        return


class TestRemoveLeadTextXarray(TestRemoveLeadText):
    """Unit tests for `pysat.instrument.methods.general.remove_leading_text`.

    Note
    ----
    Includes additional xarray-specific tests.

    """

    def setup_method(self):
        """Set up the unit test environment for each method."""

        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'ndtesting',
                                         num_samples=12,
                                         clean_level='clean',
                                         use_header=True)
        self.testInst.load(2009, 1)
        self.npts = len(self.testInst['uts'])
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.npts
        return

    def test_remove_2D_names_w_target(self):
        """Test that 2D variables are changed appropriately."""

        gen.remove_leading_text(self.testInst, target='variable')

        # Check prepended text removed from variables
        assert '_profiles' in self.testInst.data.variables
        assert self.testInst.data['_profiles'].shape[0] == self.npts

        # Check prepended text removed from metadata
        assert '_profiles' in self.testInst.meta.keys()
        return

    def test_remove_2D_names_w_target_list(self):
        """Test that 2D variables can be modified with a target list."""

        gen.remove_leading_text(self.testInst,
                                target=['variable', 'im'])

        # Check prepended text removed from variables
        assert '_profiles' in self.testInst.data.variables
        assert self.testInst.data['_profiles'].shape[0] == self.npts
        assert 'ages' in self.testInst.data.variables

        # Check prepended text removed from metadata
        assert '_profiles' in self.testInst.meta.keys()
        assert 'ages' in self.testInst.meta.keys()
        return


class TestLoadCSVData(object):
    """Unit tests for `pysat.instrument.methods.general.load_csv_data`."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        # Load a test instrument
        self.csv_file = path.join(path.abspath(path.dirname(__file__)),
                                  'test_data', 'sw', 'kp', 'recent',
                                  'kp_recent_2019-03-18.txt')
        self.data_cols = ['mid_lat_Kp', 'high_lat_Kp', 'Kp']
        self.data = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.csv_file, self.data, self.data_cols
        return

    def eval_data_cols(self):
        """Evaluate the data columns in the output."""
        for dcol in self.data_cols:
            assert dcol in self.data.columns
        return

    def test_load_single_file(self):
        """Test the CVS data load with a single file."""

        self.data = gen.load_csv_data(self.csv_file)
        assert isinstance(self.data.index, pds.RangeIndex)
        self.eval_data_cols()
        assert len(self.data.columns) == len(self.data_cols) + 1
        return

    def test_load_file_list(self):
        """Test the CVS data load with multiple files."""

        self.data = gen.load_csv_data([self.csv_file, self.csv_file])
        assert self.data.index.dtype == 'int64'
        self.eval_data_cols()
        assert len(self.data.columns) == len(self.data_cols) + 1
        return

    def test_load_file_with_kwargs(self):
        """Test the CVS data load with kwargs."""

        self.data = gen.load_csv_data([self.csv_file],
                                      read_csv_kwargs={"parse_dates": True,
                                                       "index_col": 0})
        assert isinstance(self.data.index, pds.DatetimeIndex)
        self.eval_data_cols()
        assert len(self.data.columns) == len(self.data_cols)
        return


class TestDeprecation(object):
    """Unit tests for deprecated methods."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        return

    def test_convert_timestamp_to_datetime(self):
        """Test that convert_timestamp_to_datetime is deprecated."""

        warn_msgs = [" ".join(
            ["New kwargs added to `pysat.utils.io.load_netCDF4`",
             "for generalized handling, deprecated",
             "function will be removed in pysat 3.2.0+"])]

        test = pysat.Instrument('pysat', 'testing', use_header=True)
        test.load(2009, 1)
        with warnings.catch_warnings(record=True) as war:
            gen.convert_timestamp_to_datetime(test, epoch_name='uts')

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        pysat.utils.testing.eval_warnings(war, warn_msgs)
        return
