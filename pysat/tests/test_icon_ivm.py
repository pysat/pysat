import pysat
import pysat.instruments.methods.general as icivm


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
        icivm.remove_leading_text(self.testInst)
        # check variables unchanged
        assert (len(self.testInst['ICON_L27_Blurp']) > 0)
        # check other names untouched
        assert (len(self.testInst['dummy1']) > 0)

    def test_remove_names_target(self):
        self.testInst.tag = ''
        self.testInst.sat_id = 'a'

        self.testInst['ICON_L27_Blurp'] = self.testInst['dummy1']
        icivm.remove_leading_text(self.testInst, target='ICON_L27')
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
