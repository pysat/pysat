from nose.tools import raises
import warnings

import pysat
from pysat import model_utils as mu


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing',
                                         clean_level='clean')
        self.start = pysat.datetime(2009, 1, 1)
        self.stop = pysat.datetime(2009, 1, 1)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.start, self.stop

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_date(self):
        """Try to run without start or stop dates"""
        mu.collect_inst_model_pairs(inst=self.testInst)

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_inst(self):
        """Try to run without an instrument"""
        mu.collect_inst_model_pairs(start=self.start, stop=self.stop)

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_model(self):
        """Try to run without a model"""
        mu.collect_inst_model_pairs(start=self.start, stop=self.stop,
                                    inst=self.testInst)


class TestDeprecation():

    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always")

    def teardown(self):
        """Runs after every method to clean up previous testing"""

    def test_satellite_view_through_model_deprecation(self):
        """Test if satellite_view_through_model is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                mu.satellite_view_through_model(None, None, None, None)
            except TypeError:
                # Setting inst to None should produce a TypeError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_collect_inst_model_pairs_deprecation(self):
        """Test if collect_inst_model_pairs is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                mu.collect_inst_model_pairs(inst=None)
            except ValueError:
                # Setting inst to None should produce a ValueError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_compare_model_and_inst_deprecation(self):
        """Test if compare_model_and_inst is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                mu.compare_model_and_inst(pairs=None)
            except ValueError:
                # Setting pairs to None should produce a ValueError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_extract_modelled_observations_deprecation(self):
        """Test if extract_modelled_observations is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                mu.extract_modelled_observations(inst=None)
            except ValueError:
                # Setting inst to None should produce a ValueError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
