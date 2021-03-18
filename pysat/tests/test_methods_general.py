import datetime as dt
from nose.tools import raises
import warnings

import pysat
from pysat.instruments.methods import general as gen


class TestGenMethods():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        fname = 'fake_data_{year:04d}{month:02d}{day:02d}_v05.cdf'
        self.kwargs = {'tag': '', 'sat_id': '', 'data_path': '/fake/path/',
                       'format_str': None,
                       'supported_tags': {'': {'': fname}}}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.kwargs


class TestRemoveLeadText():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Load a test instrument
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=12,
                                         clean_level='clean')
        self.testInst.load(2009, 1)
        self.Npts = len(self.testInst['uts'])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.Npts

    @raises(ValueError)
    def test_remove_prefix_w_bad_target(self):
        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
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
        warnings.filterwarnings('ignore', category=DeprecationWarning)
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
        # check prepended text removed from variables
        assert '_profiles' in self.testInst.data.variables
        assert self.testInst.data['_profiles'].shape[0] == self.Npts
        # check prepended text removed from metadata
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


class TestDeprecation():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always", DeprecationWarning)
        self.tag = ''
        self.sat_id = ''

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.tag, self.sat_id

    def test_list_files_kwarg_dep(self):
        """Test the deprecation of kwargs in list_files routine"""

        wmsg = "list_files kwarg `fake_daily_files_from_monthly` has been dep"

        with warnings.catch_warnings(record=True) as war:
            try:
                gen.list_files(tag=self.tag, sat_id=self.sat_id,
                               fake_daily_files_from_monthly=True)
            except ValueError as verr:
                # Ensure the expected ValueError for no data path was raised
                if str(verr).find('A directory must be passed') < 0:
                    raise ValueError(verr)

        found_msg = False
        for iwar in war:
            if iwar.category == DeprecationWarning \
               and str(iwar.message).find(wmsg) >= 0:
                found_msg = True

        assert found_msg, "didn't find warning about: {:}".format(wmsg)
        return

    @raises(ValueError)
    def test_list_files_cadance_future_error(self):
        """Test raises ValueError if future behaviour attempted"""

        gen.list_files(tag=self.tag, sat_id=self.sat_id,
                       file_cadance=dt.timedelta(days=47))
        return
