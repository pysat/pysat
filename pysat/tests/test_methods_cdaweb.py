import requests
import warnings

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw


class TestCDAWeb():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.supported_tags = pysat.instruments.cnofs_plp.supported_tags

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.supported_tags

    def test_remote_file_list_connection_error_append(self):
        """Test that pysat appends suggested help to ConnectionError"""
        # Giving a bad remote_site address yields similar ConnectionError
        try:
            cdw.list_remote_files(tag='', sat_id='',
                                  supported_tags=self.supported_tags,
                                  remote_site='http:/')
        except Exception as excinfo:
            assert isinstance(excinfo, requests.exceptions.ConnectionError)
            # Check that pysat appends the message
            assert str(excinfo).find('pysat -> Request potentially') > 0
        else:
            raise(ValueError, 'Test was expected to raise an Exception.')

    def test_remote_file_list_deprecation_warning(self):
        """Test generation of deprecation warning for remote_file_list kwargs
        """
        warnings.simplefilter("always")

        with warnings.catch_warnings(record=True) as war:
            # testing with single day since we just need the warning
            cdw.list_remote_files(tag='', sat_id='',
                                  supported_tags=self.supported_tags,
                                  year=2009, month=1, day=1)

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_list_files_deprecation_warning(self):
        """Test generation of deprecation warning for list_files kwargs
        """
        warnings.simplefilter("always")

        with warnings.catch_warnings(record=True) as war1:
            # testing with single day since we just need the warning
            try:
                pysat.instruments.methods.nasa_cdaweb.list_files()
            except ValueError:
                # Using default tags will produce a ValueError
                pass

        with warnings.catch_warnings(record=True) as war2:
            # testing with single day since we just need the warning
            try:
                pysat.instruments.methods.general.list_files()
            except ValueError:
                # Using default tags will produce a ValueError
                pass

        assert len(war1) >= 1
        assert war1[0].category == DeprecationWarning
        assert len(war2) == 0
