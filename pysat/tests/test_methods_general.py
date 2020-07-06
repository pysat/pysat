import pytest

import pysat
from pysat.instruments.methods import general as gen


class TestGenMethods():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        fname = 'fake_data_{year:04d}{month:02d}{day:02d}_v05.cdf'
        self.kwargs = {'tag': '', 'sat_id': '', 'data_path': '/fake/path/',
                       'format_str': None,
                       'supported_tags': {'': {'': fname}}}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.kwargs

    @pytest.mark.parametrize("bad_key,bad_val,err_msg",
                             [("data_path", None,
                               "A directory must be passed"),
                              ("tag", "badval", "Unknown sat_id or tag"),
                              ("sat_id", "badval", "Unknown sat_id or tag")])
    def test_bad_kwarg_list_files(self, bad_key, bad_val, err_msg):
        self.kwargs[bad_key] = bad_val
        with pytest.raises(ValueError) as excinfo:
            gen.list_files(**self.kwargs)
        assert str(excinfo.value).find(err_msg) >= 0


class TestICONIVMCustom():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing', tag='12',
                                         clean_level='clean')
        self.testInst.load(2009, 1)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_remove_names_wo_target(self):
        self.testInst.tag = ''
        self.testInst.sat_id = 'a'

        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst)
        # check variables unchanged
        assert (len(self.testInst['ICON_L27_Blurp']) > 0)
        # check other names untouched
        assert (len(self.testInst['dummy1']) > 0)

    def test_remove_names_target(self):
        self.testInst.tag = ''
        self.testInst.sat_id = 'a'

        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        gen.remove_leading_text(self.testInst, target='ICON_L27')
        # check prepended text removed
        assert (len(self.testInst['_Blurp']) > 0)
        # check other names untouched
        assert (len(self.testInst['dummy1']) > 0)


class TestRemoveLeadTextXarray(TestICONIVMCustom):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Load a test instrument
        self.testInst = pysat.Instrument('pysat', 'testing_xarray', tag='12',
                                         clean_level='clean')
        self.testInst.load(2009, 1)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
