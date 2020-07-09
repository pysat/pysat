import requests
import warnings

import pytest

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
        with pytest.raises(Exception) as excinfo:
            # Giving a bad remote_site address yields similar ConnectionError
            cdw.list_remote_files(tag='', sat_id='',
                                  supported_tags=self.supported_tags,
                                  remote_site='http:/')

        assert excinfo.type is requests.exceptions.ConnectionError
        # Check that pysat appends the message
        assert str(excinfo.value).find('pysat -> Request potentially') > 0

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
        """Test generation of deprecation warning for remote_file_list kwargs
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
