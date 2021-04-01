import requests
import warnings

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw


class TestCDAWeb():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        warnings.filterwarnings("always", category=DeprecationWarning)
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

    def test_list_remote_files_deprecation_warning(self):
        """Test deprecation warnings for remote_file_list routine and kwargs
        """
        with warnings.catch_warnings(record=True) as war:
            # testing with single day since we just need the warning
            cdw.list_remote_files(tag='', sat_id='',
                                  supported_tags=self.supported_tags,
                                  year=2009, month=1, day=1)

        assert len(war) >= 2
        assert war[0].category == DeprecationWarning

    def test_load_deprecation_warning(self):
        """Test generation of deprecation warning for load
        """
        with warnings.catch_warnings(record=True) as war:
            # testing with single day since we just need the warning
            cdw.load([], tag='', sat_id='')

        assert len(war) == 1
        assert war[0].category == DeprecationWarning
        assert str(war[0].message).find(".load has been deprecated") >= 0

    def test_download_deprecation_warning(self):
        """Test generation of deprecation warning for download
        """
        with warnings.catch_warnings(record=True) as war:
            # testing with single day since we just need the warning
            cdw.download(self.supported_tags, [], '', '')

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
        assert str(war[0].message).find(".download has been deprecated") >= 0

    def test_list_files_deprecation_warning(self):
        """Test generation of deprecation warning for list_files kwargs
        """
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
