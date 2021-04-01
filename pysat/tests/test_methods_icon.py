import requests
import warnings

import pysat
from pysat.instruments.methods import icon as mm_icon


class TestICON():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        warnings.filterwarnings("always", category=DeprecationWarning)
        self.supported_tags = pysat.instruments.icon_ivm.supported_tags

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.supported_tags

    def test_list_remote_files_deprecation_warning(self):
        """Test deprecation warnings for remote_file_list routine and kwargs
        """
        with warnings.catch_warnings(record=True) as war:
            # testing with non-supported user since we just need the warning
            try:
                mm_icon.list_remote_files(tag='', sat_id='a',
                                          supported_tags=self.supported_tags,
                                          user='break_the_test')
            except(ValueError):
                # If a user-name is supplied, the test will error
                pass

        self.warn_msg = ".icon.list_remote_files` instead"
        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
        assert str(war[0].message).find(self.warn_msg) >= 0

    def test_download_deprecation_warning(self):
        """Test generation of deprecation warning for download
        """
        with warnings.catch_warnings(record=True) as war:
            try:
                mm_icon.ssl_download([], '', '')
            except(IndexError):
                # testing with an empty array will produce an Index Error
                pass

        self.warn_msg = ".cdaweb.download` instead"
        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
        assert str(war[0].message).find(self.warn_msg) >= 0
