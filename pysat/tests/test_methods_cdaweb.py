import datetime as dt
import requests

import pytest

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw


class TestCDAWeb():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.supported_tags = pysat.instruments.cnofs_plp.supported_tags
        self.kwargs = {'tag': '', 'sat_id': ''}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.supported_tags, self.kwargs

    def test_remote_file_list_connection_error_append(self):
        """pysat should append suggested help to ConnectionError"""
        with pytest.raises(Exception) as excinfo:
            # Giving a bad remote_site address yields similar ConnectionError
            cdw.list_remote_files(tag='', sat_id='',
                                  supported_tags=self.supported_tags,
                                  remote_site='http:/')

        assert excinfo.type is requests.exceptions.ConnectionError
        # Check that pysat appends the message
        assert str(excinfo.value).find('pysat -> Request potentially') > 0

    def test_load_with_empty_file_list(self):
        """pysat should return empty data if no files are requested"""
        data, meta = cdw.load(fnames=[])
        assert len(data) == 0
        assert meta is None

    @pytest.mark.parametrize("bad_key,bad_val,err_msg",
                             [("tag", "badval", "Tag name unknown"),
                              ("sat_id", "badval", "Tag name unknown")])
    def test_bad_tag_download(self, bad_key, bad_val, err_msg):
        date_array = [dt.datetime(2019, 1, 1)]
        self.kwargs[bad_key] = bad_val
        with pytest.raises(ValueError) as excinfo:
            cdw.download(supported_tags=self.supported_tags,
                         date_array=date_array,
                         tag=self.kwargs['tag'],
                         sat_id=self.kwargs['sat_id'])
        assert str(excinfo.value).find('Tag name unknown') >= 0
