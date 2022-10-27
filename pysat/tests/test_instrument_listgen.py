"""Unit tests for the list generation methods in `pysat.Instrument`."""

from importlib import reload

import pysat
from pysat.utils import generate_instrument_list


class TestInstListGeneration(object):
    """Tests that ensure `generate_instrument_list` is working as expected."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.test_library = pysat.instruments
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        # Reset the pysat instrument library.
        reload(pysat.instruments)
        reload(pysat.instruments.pysat_testing)
        del self.test_library
        return

    def test_import_error_behavior(self):
        """Test `generate_instrument_list` works with a broken instrument."""

        self.test_library.__all__.append('broken_inst')

        # This instrument does not exist.  The routine should run without error.
        inst_list = generate_instrument_list(self.test_library)
        assert 'broken_inst' in inst_list['names']
        for dict in inst_list['download']:
            assert 'broken_inst' not in dict['inst_module'].__name__
        for dict in inst_list['no_download']:
            assert 'broken_inst' not in dict['inst_module'].__name__
        return

    def test_for_missing_test_date(self):
        """Test that instruments without the `_test_dates` attr are added."""

        del self.test_library.pysat_testing._test_dates

        # If an instrument does not have the _test_dates attribute, it should
        # still be added to the list for other checks to be run.
        # This will be caught later by InstTestClass.test_instrument_test_dates.
        assert not hasattr(self.test_library.pysat_testing, '_test_dates')
        inst_list = generate_instrument_list(self.test_library)
        assert 'pysat_testing' in inst_list['names']
        return
