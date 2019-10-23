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
        _ = mu.collect_inst_model_pairs(inst=self.testInst)

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_inst(self):
        """Try to run without an instrument"""
        _ = mu.collect_inst_model_pairs(start=self.start, stop=self.stop)

    @raises(ValueError)
    def test_collect_inst_model_pairs_wo_model(self):
        """Try to run without a model"""
        _ = mu.collect_inst_model_pairs(start=self.start, stop=self.stop,
                                        inst=self.testInst)

    def test_satellite_view_through_model_deprecation(self):
        """Test if satellite_view_through_model is deprecated"""
        warnings.simplefilter('always')

        with warnings.catch_warnings(record=True) as w:
            try:
                mu.satellite_view_through_model(None, None, None, None)
            except TypeError:
                pass

        assert len(w) >= 1
        assert w[0].category == DeprecationWarning

    def test_collect_inst_model_pairs_deprecation(self):
        """Test if collect_inst_model_pairs is deprecated"""
        warnings.simplefilter('always')

        with warnings.catch_warnings(record=True) as w:
            try:
                mu.collect_inst_model_pairs()
            except ValueError:
                pass

        assert len(w) >= 1
        assert w[0].category == DeprecationWarning

    def test_compare_model_and_inst_deprecation(self):
        """Test if compare_model_and_inst is deprecated"""
        warnings.simplefilter('always')

        with warnings.catch_warnings(record=True) as w:
            try:
                mu.compare_model_and_inst()
            except ValueError:
                pass

        assert len(w) >= 1
        assert w[0].category == DeprecationWarning

    def test_extract_modelled_observations_deprecation(self):
        """Test if extract_modelled_observations is deprecated"""
        warnings.simplefilter('always')

        with warnings.catch_warnings(record=True) as w:
            try:
                mu.extract_modelled_observations()
            except ValueError:
                pass

        assert len(w) >= 1
        assert w[0].category == DeprecationWarning
