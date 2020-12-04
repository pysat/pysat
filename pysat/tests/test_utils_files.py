import numpy as np
from pysat.utils import files as futils


class TestBasics():

    temporary_file_list = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""

    def teardown(self):
        """Runs after every method to clean up previous testing."""

    def test_parse_delimited_filename(self):
        """Check ability to parse list of delimited files"""
        # Note: Can be removed if future instrument that uses delimited
        # filenames is added to routine travis end-to-end testing
        fname = ''.join(('test_{year:4d}_{month:2d}_{day:2d}_{hour:2d}',
                         '_{minute:2d}_{second:2d}_{version:2s}_r02.cdf'))
        year = np.ones(6) * 2009
        month = np.ones(6) * 12
        day = np.array([12, 15, 17, 19, 22, 24])
        hour = np.array([8, 10, 6, 18, 3, 23])
        minute = np.array([8, 10, 6, 18, 3, 59])
        second = np.array([58, 11, 26, 2, 18, 59])
        version = np.array(['v1', 'v2', 'r1', 'r3', 'v5', 'a6'])
        file_list = []
        for i in range(6):
            file_list.append(fname.format(year=year[i].astype(int),
                                          month=month[i].astype(int),
                                          day=day[i], hour=hour[i],
                                          minute=minute[i], second=second[i],
                                          version=version[i]))

        file_dict = futils.parse_delimited_filenames(file_list, fname, '_')
        assert np.all(file_dict['year'] == year)
        assert np.all(file_dict['month'] == month)
        assert np.all(file_dict['day'] == day)
        assert np.all(file_dict['hour'] == hour)
        assert np.all(file_dict['minute'] == minute)
        assert np.all(file_dict['day'] == day)
        assert np.all(file_dict['version'] == version)
        assert (file_dict['revision'] is None)
        assert (file_dict['cycle'] is None)
