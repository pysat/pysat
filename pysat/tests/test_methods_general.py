import datetime as dt
import pandas as pds
import pytest

import pysat
from pysat.instruments.methods import general as gen


class TestGenMethods():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        fname = 'fake_data_{year:04d}{month:02d}{day:02d}_v05.cdf'
        self.kwargs = {'tag': '', 'inst_id': '', 'data_path': '/fake/path/',
                       'format_str': None,
                       'supported_tags': {'': {'': fname}}}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.kwargs

    @pytest.mark.parametrize("bad_key,bad_val,err_msg",
                             [("data_path", None,
                               "A directory must be passed"),
                              ("tag", "badval", "Unknown inst_id or tag"),
                              ("inst_id", "badval", "Unknown inst_id or tag")])
    def test_bad_kwarg_list_files(self, bad_key, bad_val, err_msg):
        self.kwargs[bad_key] = bad_val
        with pytest.raises(ValueError) as excinfo:
            gen.list_files(**self.kwargs)
        assert str(excinfo.value).find(err_msg) >= 0


class TestFileCadence():

    @pytest.mark.parametrize("time_kwarg, time_val, is_daily",
                             [("microseconds", 1, True), ("seconds", 1, True),
                              ("minutes", 1, True), ("hours", 1, True),
                              ("days", 1, True), ("days", 2, False)])
    def test_datetime_file_cadence(self, time_kwarg, time_val, is_daily):
        """ Test is_daily_file_cadence with dt.datetime input
        """
        in_time = dt.timedelta(**{time_kwarg: time_val})
        check_daily = gen.is_daily_file_cadence(in_time)

        assert check_daily == is_daily

    @pytest.mark.parametrize("time_kwarg, time_val, is_daily",
                             [("microseconds", 1, True), ("seconds", 1, True),
                              ("minutes", 1, True), ("hours", 1, True),
                              ("days", 1, True), ("days", 2, False),
                              ("months", 1, False), ("years", 1, False)])
    def test_dateoffset_file_cadence(self, time_kwarg, time_val, is_daily):
        """ Test is_daily_file_cadence with pds.DateOffset input
        """
        in_time = pds.DateOffset(**{time_kwarg: time_val})
        check_daily = gen.is_daily_file_cadence(in_time)

        assert check_daily == is_daily


class TestRemoveLeadText():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=12,
                                         clean_level='clean')
        self.testInst.load(2009, 1)
        self.Npts = len(self.testInst['uts'])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.Npts

    def test_remove_prefix_w_bad_target(self):
        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        with pytest.raises(ValueError):
            gen.remove_leading_text(self.testInst, target=17.5)

    def test_remove_names_wo_target(self):
        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst)
        # check variables unchanged
        assert (len(self.testInst['ICON_L27_Blurp']) == self.Npts)
        # check other names untouched
        assert (len(self.testInst['dummy1']) == self.Npts)

    def test_remove_names_w_target(self):
        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst, target='ICON_L27')
        # check prepended text removed
        assert len(self.testInst['_Blurp']) == self.Npts
        # check other names untouched
        assert len(self.testInst['dummy1']) == self.Npts
        # check prepended text removed from metadata
        assert '_Blurp' in self.testInst.meta.keys()

    def test_remove_names_w_target_list(self):
        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        self.testInst['ICON_L23_Bloop'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst,
                                target=['ICON_L27', 'ICON_L23_B'])
        # check prepended text removed
        assert len(self.testInst['_Blurp']) == self.Npts
        assert len(self.testInst['loop']) == self.Npts
        # check other names untouched
        assert len(self.testInst['dummy1']) == self.Npts
        # check prepended text removed from metadata
        assert '_Blurp' in self.testInst.meta.keys()
        assert 'loop' in self.testInst.meta.keys()


class TestRemoveLeadTextXarray(TestRemoveLeadText):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing2d_xarray',
                                         num_samples=12,
                                         clean_level='clean')
        self.testInst.load(2009, 1)
        self.Npts = len(self.testInst['uts'])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.Npts

    def test_remove_2D_names_w_target(self):
        gen.remove_leading_text(self.testInst, target='variable')
        # Check prepended text removed from variables
        assert '_profiles' in self.testInst.data.variables
        assert self.testInst.data['_profiles'].shape[0] == self.Npts

        # Check prepended text removed from metadata
        assert '_profiles' in self.testInst.meta.keys()

    def test_remove_2D_names_w_target_list(self):
        gen.remove_leading_text(self.testInst,
                                target=['variable', 'im'])
        # check prepended text removed from variables
        assert '_profiles' in self.testInst.data.variables
        assert self.testInst.data['_profiles'].shape[0] == self.Npts
        assert 'ages' in self.testInst.data.variables
        # check prepended text removed from metadata
        assert '_profiles' in self.testInst.meta.keys()
        assert 'ages' in self.testInst.meta.keys()
