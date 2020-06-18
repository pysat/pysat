"""
tests the pysat meta object and code
"""
import glob
import numpy as np
import os
import sys

from nose.tools import raises
import pandas as pds
import tempfile

import pysat
import pysat.instruments.pysat_testing

if sys.version_info[0] >= 3:
    from importlib import reload as re_load
else:
    re_load = reload


def create_dir(inst=None, temporary_file_list=False):
    if inst is None:
        # create instrument
        inst = pysat.Instrument(platform='pysat', name='testing',
                                temporary_file_list=temporary_file_list)

    # create data directories
    try:
        os.makedirs(inst.files.data_path)
    except OSError:
        pass
    return


def remove_files(inst=None):
    # remove any files
    temp_dir = inst.files.data_path
    for the_file in os.listdir(temp_dir):
        if (the_file[0:13] == 'pysat_testing') & \
                (the_file[-19:] == '.pysat_testing_file'):
            file_path = os.path.join(temp_dir, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)


# create year doy file set
def create_files(inst, start, stop, freq=None, use_doy=True, root_fname=None,
                 content=None):

    if freq is None:
        freq = '1D'
    dates = pysat.utils.time.create_date_range(start, stop, freq=freq)

    if root_fname is None:
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_',
                              'stuff.pysat_testing_file'))
    # create empty file
    for date in dates:
        yr, doy = pysat.utils.time.getyrdoy(date)
        if use_doy:
            doy = doy
        else:
            doy = date.day

        fname = os.path.join(inst.files.data_path, root_fname.format(year=yr,
                             day=doy, month=date.month, hour=date.hour,
                             minute=date.minute, second=date.second))
        with open(fname, 'w') as f:
            if content is not None:
                f.write(content)


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data"""

    if format_str is None:
        format_str = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_',
                              'stuff_{month:02d}_{hour:02d}_{minute:02d}_',
                              '{second:02d}.pysat_testing_file'))

    if tag is not None:
        if tag == '':
            return pysat.Files.from_os(data_path=data_path,
                                       format_str=format_str)
        else:
            raise ValueError('Unrecognized tag name')
    else:
        raise ValueError('A tag name must be passed ')


class TestNoDataDir():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.temporary_file_list = False
        # store current pysat directory
        self.saved_data_path = pysat.data_dir

        pysat.data_dir = ''
        re_load(pysat._files)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.data_dir = self.saved_data_path
        re_load(pysat._files)

    @raises(Exception)
    def test_no_data_dir(self):
        _ = pysat.Instrument()


class TestBasics():

    temporary_file_list = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir

        # create temporary directory
        dir_name = tempfile.mkdtemp()
        pysat.utils.set_data_dir(dir_name, store=False)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             temporary_file_list=self.temporary_file_list)
        # create testing directory
        create_dir(self.testInst)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        remove_files(self.testInst)
        try:
            pysat.utils.set_data_dir(self.data_path, store=False)
        except:
            pass
        del self.testInst

    def test_parse_delimited_filename(self):
        """Check ability to parse delimited files"""
        # Note: Can be removed if future instrument that uses delimited
        # filenames is added to routine travis end-to-end testing
        fname = ''.join(('test_{year:4d}_{month:2d}_{day:2d}_{hour:2d}',
                         '_{minute:2d}_{second:2d}_{version:2s}_r02.cdf'))
        year = np.ones(6)*2009
        month = np.ones(6)*12
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

        file_dict = pysat._files.parse_delimited_filenames(file_list, fname,
                                                           '_')
        assert np.all(file_dict['year'] == year)
        assert np.all(file_dict['month'] == month)
        assert np.all(file_dict['day'] == day)
        assert np.all(file_dict['hour'] == hour)
        assert np.all(file_dict['minute'] == minute)
        assert np.all(file_dict['day'] == day)
        assert np.all(file_dict['version'] == version)
        assert (file_dict['revision'] is None)

    def test_year_doy_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008, 1, 1)
        stop = pysat.datetime(2009, 12, 31)
        create_files(self.testInst, start, stop, freq='1D')
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=''.join(('pysat_testing_junk_',
                                                        '{year:04d}_gold_',
                                                        '{day:03d}_stuff.',
                                                        'pysat_testing_file')))
        # check overall length
        check1 = len(files) == (365 + 366)
        # check specific dates
        check2 = pds.to_datetime(files.index[0]) == pysat.datetime(2008, 1, 1)
        check3 = pds.to_datetime(files.index[365]) == \
            pysat.datetime(2008, 12, 31)
        check4 = pds.to_datetime(files.index[-1]) == \
            pysat.datetime(2009, 12, 31)
        assert(check1 & check2 & check3 & check4)

    def test_year_doy_files_no_gap_in_name_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008, 1, 1)
        stop = pysat.datetime(2009, 12, 31)
        create_files(self.testInst, start, stop, freq='1D',
                     root_fname=''.join(('pysat_testing_junk_{year:04d}',
                                         '{day:03d}_stuff.pysat_testing_',
                                         'file')))
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=''.join(('pysat_testing_junk_',
                                                        '{year:04d}{day:03d}_',
                                                        'stuff.pysat_testing_',
                                                        'file')))
        # check overall length
        check1 = len(files) == (365 + 366)
        # check specific dates
        check2 = pds.to_datetime(files.index[0]) == pysat.datetime(2008, 1, 1)
        check3 = pds.to_datetime(files.index[365]) == \
            pysat.datetime(2008, 12, 31)
        check4 = pds.to_datetime(files.index[-1]) == \
            pysat.datetime(2009, 12, 31)
        assert(check1 & check2 & check3 & check4)

    def test_year_month_day_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008, 1, 1)
        stop = pysat.datetime(2009, 12, 31)
        create_files(self.testInst, start, stop, freq='1D', use_doy=False,
                     root_fname=''.join(('pysat_testing_junk_{year:04d}_gold_',
                                         '{day:03d}_stuff_{month:02d}.pysat_',
                                         'testing_file')))
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=''.join(('pysat_testing_junk_',
                                                        '{year:04d}_gold_',
                                                        '{day:03d}_stuff_',
                                                        '{month:02d}.pysat_',
                                                        'testing_file')))
        # check overall length
        check1 = len(files) == (365 + 366)
        # check specific dates
        check2 = pds.to_datetime(files.index[0]) == pysat.datetime(2008, 1, 1)
        check3 = pds.to_datetime(files.index[365]) == \
            pysat.datetime(2008, 12, 31)
        check4 = pds.to_datetime(files.index[-1]) == \
            pysat.datetime(2009, 12, 31)
        assert(check1 & check2 & check3 & check4)

    def test_year_month_day_hour_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008, 1, 1)
        stop = pysat.datetime(2009, 12, 31)
        create_files(self.testInst, start, stop, freq='6h',
                     use_doy=False,
                     root_fname=''.join(('pysat_testing_junk_{year:04d}_gold_',
                                         '{day:03d}_stuff_{month:02d}_',
                                         '{hour:02d}.pysat_testing_file')))
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=''.join(('pysat_testing_junk_',
                                                        '{year:04d}_gold_',
                                                        '{day:03d}_stuff_',
                                                        '{month:02d}_',
                                                        '{hour:02d}.pysat_',
                                                        'testing_file')))
        # check overall length
        check1 = len(files) == (365+366)*4-3
        # check specific dates
        check2 = pds.to_datetime(files.index[0]) == pysat.datetime(2008, 1, 1)
        check3 = pds.to_datetime(files.index[1460]) == \
            pysat.datetime(2008, 12, 31)
        check4 = pds.to_datetime(files.index[-1]) == \
            pysat.datetime(2009, 12, 31)
        assert(check1 & check2 & check3 & check4)

    def test_year_month_day_hour_minute_files_direct_call_to_from_os(self):
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_',
                              'stuff_{month:02d}_{hour:02d}{minute:02d}.',
                              'pysat_testing_file'))
        # create a bunch of files by year and doy
        start = pysat.datetime(2008, 1, 1)
        stop = pysat.datetime(2008, 1, 4)
        create_files(self.testInst, start, stop, freq='30min',
                     use_doy=False,
                     root_fname=root_fname)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        check1 = len(files) == 145
        # check specific dates
        check2 = pds.to_datetime(files.index[0]) == pysat.datetime(2008, 1, 1)
        check3 = pds.to_datetime(files.index[1]) == \
            pysat.datetime(2008, 1, 1, 0, 30)
        check4 = pds.to_datetime(files.index[10]) == \
            pysat.datetime(2008, 1, 1, 5, 0)
        check5 = pds.to_datetime(files.index[-1]) == pysat.datetime(2008, 1, 4)
        assert(check1 & check2 & check3 & check4 & check5)

    def test_year_month_day_hour_minute_second_files_direct_call_to_from_os(self):
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_',
                              'stuff_{month:02d}_{hour:02d}_{minute:02d}_',
                              '{second:02d}.pysat_testing_file'))
        # create a bunch of files by year and doy
        start = pysat.datetime(2008, 1, 1)
        stop = pysat.datetime(2008, 1, 3)
        create_files(self.testInst, start, stop, freq='30s',
                     use_doy=False, root_fname=root_fname)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        check1 = len(files) == 5761
        # check specific dates
        check2 = pds.to_datetime(files.index[0]) == pysat.datetime(2008, 1, 1)
        check3 = pds.to_datetime(files.index[1]) == \
            pysat.datetime(2008, 1, 1, 0, 0, 30)
        check4 = pds.to_datetime(files.index[-1]) == \
            pysat.datetime(2008, 1, 3)
        assert(check1 & check2 & check3 & check4)

    def test_year_month_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008, 1, 1)
        stop = pysat.datetime(2009, 12, 31)
        create_files(self.testInst, start, stop, freq='1MS',
                     root_fname=''.join(('pysat_testing_junk_{year:04d}_gold_',
                                         'stuff_{month:02d}.pysat_testing_',
                                         'file')))
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=''.join(('pysat_testing_junk_',
                                                        '{year:04d}_gold_',
                                                        'stuff_{month:02d}.',
                                                        'pysat_testing_file')))
        # check overall length
        check1 = len(files) == 24
        # check specific dates
        check2 = pds.to_datetime(files.index[0]) == pysat.datetime(2008, 1, 1)
        check3 = pds.to_datetime(files.index[11]) == \
            pysat.datetime(2008, 12, 1)
        check4 = pds.to_datetime(files.index[-1]) == \
            pysat.datetime(2009, 12, 1)
        assert(check1 & check2 & check3 & check4)

    def test_instrument_has_no_files(self):
        import pysat.instruments.pysat_testing

        pysat.instruments.pysat_testing.list_files = list_files
        inst = pysat.Instrument(platform='pysat', name='testing',
                                update_files=True)
        re_load(pysat.instruments.pysat_testing)
        assert(inst.files.files.empty)

    def test_instrument_has_files(self):
        import pysat.instruments.pysat_testing

        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_'
                              'stuff_{month:02d}_{hour:02d}_{minute:02d}_'
                              '{second:02d}.pysat_testing_file'))
        # create a bunch of files by year and doy
        start = pysat.datetime(2007, 12, 31)
        stop = pysat.datetime(2008, 1, 10)
        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False, root_fname=root_fname)
        # create the same range of dates
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        pysat.instruments.pysat_testing.list_files = list_files
        inst = pysat.Instrument(platform='pysat', name='testing',
                                update_files=True)
        re_load(pysat.instruments.pysat_testing)
        assert (np.all(inst.files.files.index == dates))


class TestBasicsNoFileListStorage(TestBasics):

    temporary_file_list = True


class TestInstrumentWithFiles():

    temporary_file_list = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir
        # create temporary directory
        dir_name = tempfile.mkdtemp()
        pysat.utils.set_data_dir(dir_name, store=False)
        # create testing directory
        create_dir(temporary_file_list=self.temporary_file_list)

        # create a test instrument, make sure it is getting files from
        # filesystem
        re_load(pysat.instruments.pysat_testing)
        pysat.instruments.pysat_testing.list_files = list_files
        # create a bunch of files by year and doy
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             temporary_file_list=self.temporary_file_list)

        self.root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_',
                                   '{day:03d}_stuff_{month:02d}_{hour:02d}_',
                                   '{minute:02d}_{second:02d}.pysat_testing_',
                                   'file'))
        start = pysat.datetime(2007, 12, 31)
        stop = pysat.datetime(2008, 1, 10)
        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        remove_files(self.testInst)
        del self.testInst
        re_load(pysat.instruments.pysat_testing)
        re_load(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list, no files
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=self.temporary_file_list)
        pysat.utils.set_data_dir(self.data_path, store=False)

    def test_refresh(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 10)
        stop = pysat.datetime(2008, 1, 12)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname)
        start = pysat.datetime(2007, 12, 31)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_refresh_on_ignore_empty_files(self):
        # setup created empty files - make sure such files can be ignored
        self.testInst.files.ignore_empty_files = True
        self.testInst.files.refresh()
        assert len(self.testInst.files.files) == 0

        # create new files with content and make sure they are captured
        start = pysat.datetime(2007, 12, 31)
        stop = pysat.datetime(2008, 1, 10)
        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname,
                     content='test')
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_instrument_with_ignore_empty_files(self):
        """Make sure new instruments can ignore empty files"""
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             update_files=True,
                             temporary_file_list=self.temporary_file_list,
                             ignore_empty_files=True)

        assert len(self.testInst.files.files) == 0

        # create new files with content and make sure they are captured
        start = pysat.datetime(2007, 12, 31)
        stop = pysat.datetime(2008, 1, 10)
        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname,
                     content='test')
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_refresh_on_unchanged_files(self):
        start = pysat.datetime(2007, 12, 31)
        stop = pysat.datetime(2008, 1, 10)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_get_new_files_after_refresh(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_multiple_refreshes(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        self.testInst.files.refresh()
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_adding_files(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        new_files = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_adding_files_and_adding_file(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        new_files = self.testInst.files.get_new()

        start = pysat.datetime(2008, 1, 15)
        stop = pysat.datetime(2008, 1, 18)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname)
        dates2 = pysat.utils.time.create_date_range(start, stop, freq='100min')
        new_files2 = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates) &
                np.all(new_files2.index == dates2))

    def test_get_new_files_after_deleting_files_and_adding_files(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')

        # remove files, same number as will be added
        to_be_removed = len(dates)
        for the_file in os.listdir(self.testInst.files.data_path):
            if (the_file[0:13] == 'pysat_testing') & \
                    (the_file[-19:] == '.pysat_testing_file'):
                file_path = os.path.join(self.testInst.files.data_path,
                                         the_file)
                if os.path.isfile(file_path) & (to_be_removed > 0):
                    # print(file_path)
                    to_be_removed -= 1
                    os.unlink(file_path)
        # add new files
        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname)
        # get new files
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))

    def test_files_non_standard_pysat_directory(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 15)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             sat_id='hello',
                             directory_format='pysat_testing_{tag}_{sat_id}',
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)
        # add new files
        create_dir(self.testInst)
        remove_files(self.testInst)
        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             sat_id='hello',
                             directory_format=''.join(('pysat_testing_',
                                                       '{tag}_{sat_id}')),
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

        # get new files
        new_files = self.testInst.files.get_new()
        assert (np.all(self.testInst.files.files.index == dates) &
                np.all(new_files.index == dates))

    def test_files_non_standard_file_format_template(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 15)
        dates = pysat.utils.time.create_date_range(start, stop, freq='1D')

        # clear out old files, create new ones
        remove_files(self.testInst)
        create_files(self.testInst, start, stop, freq='1D',
                     use_doy=False,
                     root_fname=''.join(('pysat_testing_unique_junk_',
                                         '{year:04d}_gold_{day:03d}_stuff',
                                         '.pysat_testing_file')))

        pysat.instruments.pysat_testing.list_files = list_files
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             file_format=''.join(('pysat_testing_unique_',
                                                  'junk_{year:04d}_gold_',
                                                  '{day:03d}_stuff',
                                                  '.pysat_testing_file')),
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

        assert (np.all(self.testInst.files.files.index == dates))

    @raises(ValueError)
    def test_files_non_standard_file_format_template_misformatted(self):

        pysat.instruments.pysat_testing.list_files = list_files
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             file_format=''.join(('pysat_testing_unique_',
                                                  'junk_stuff.pysat_testing',
                                                  '_file')),
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

    @raises(ValueError)
    def test_files_non_standard_file_format_template_misformatted_2(self):

        pysat.instruments.pysat_testing.list_files = list_files
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             file_format=15,
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)


class TestInstrumentWithFilesNoFileListStorage(TestInstrumentWithFiles):

    temporary_file_list = True


# create year doy file set with multiple versions
def create_versioned_files(inst, start=None, stop=None, freq='1D',
                           use_doy=True, root_fname=None):
    # create a bunch of files
    if start is None:
        start = pysat.datetime(2009, 1, 1)
    if stop is None:
        stop = pysat.datetime(2013, 12, 31)
    dates = pysat.utils.time.create_date_range(start, stop, freq=freq)

    versions = np.array([1, 2])
    revisions = np.array([0, 1])

    if root_fname is None:
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}_',
                              '{day:03d}{hour:02d}{minute:02d}{second:02d}_',
                              'stuff_{version:02d}_{revision:03d}.pysat_',
                              'testing_file'))
    # create empty file
    for date in dates:
        for version in versions:
            for revision in revisions:
                yr, doy = pysat.utils.time.getyrdoy(date)
                if use_doy:
                    doy = doy
                else:
                    doy = date.day

                fname = os.path.join(inst.files.data_path,
                                     root_fname.format(year=yr,
                                                       day=doy,
                                                       month=date.month,
                                                       hour=date.hour,
                                                       minute=date.minute,
                                                       second=date.second,
                                                       version=version,
                                                       revision=revision))
                with open(fname, 'w') as f:
                    pass


def list_versioned_files(tag=None, sat_id=None, data_path=None,
                         format_str=None):
    """Return a Pandas Series of every file for chosen satellite data"""

    if format_str is None:
        format_str = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}_',
                              '{day:03d}{hour:02d}{minute:02d}{second:02d}_',
                              'stuff_{version:02d}_{revision:03d}.pysat_',
                              'testing_file'))
    if tag is not None:
        if tag == '':
            return pysat.Files.from_os(data_path=data_path,
                                       format_str=format_str)
        else:
            raise ValueError('Unrecognized tag name')
    else:
        raise ValueError('A tag name must be passed ')


class TestInstrumentWithVersionedFiles():

    temporary_file_list = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir
        # create temporary directory
        dir_name = tempfile.gettempdir()
        pysat.utils.set_data_dir(dir_name, store=False)
        # create testing directory
        create_dir(temporary_file_list=self.temporary_file_list)

        # create a test instrument, make sure it is getting files from
        # filesystem
        re_load(pysat.instruments.pysat_testing)
        pysat.instruments.pysat_testing.list_files = list_versioned_files
        # create a bunch of files by year and doy
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             temporary_file_list=self.temporary_file_list)

        self.root_fname = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}',
                                   '_{day:03d}{hour:02d}{minute:02d}',
                                   '{second:02d}_stuff_{version:02d}_',
                                   '{revision:03d}.pysat_testing_file'))
        start = pysat.datetime(2007, 12, 31)
        stop = pysat.datetime(2008, 1, 10)
        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False, root_fname=self.root_fname)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        remove_files(self.testInst)
        del self.testInst
        re_load(pysat.instruments.pysat_testing)
        re_load(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list, no files
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=self.temporary_file_list)
        pysat.utils.set_data_dir(self.data_path, store=False)

    def test_refresh(self):
        # create new files and make sure that new files are captured
        # files slready exist from 2007, 12, 31 through to 10th
        start = pysat.datetime(2008, 1, 10)
        stop = pysat.datetime(2008, 1, 12)
        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False,
                               root_fname=self.root_fname)
        # create list of dates for all files that should be there
        start = pysat.datetime(2007, 12, 31)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        # update instrument file list
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_refresh_on_unchanged_files(self):

        start = pysat.datetime(2007, 12, 31)
        stop = pysat.datetime(2008, 1, 10)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_get_new_files_after_refresh(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False,
                               root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_multiple_refreshes(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False,
                               root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        self.testInst.files.refresh()
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_adding_files(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False,
                               root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        new_files = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_adding_files_and_adding_file(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)

        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False,
                               root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        new_files = self.testInst.files.get_new()

        start = pysat.datetime(2008, 1, 15)
        stop = pysat.datetime(2008, 1, 18)

        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False,
                               root_fname=self.root_fname)
        dates2 = pysat.utils.time.create_date_range(start, stop, freq='100min')
        new_files2 = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates) &
                np.all(new_files2.index == dates2))

    def test_get_new_files_after_deleting_files_and_adding_files(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 12)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        # remove files, same number as will be added
        to_be_removed = len(dates)
        for the_file in os.listdir(self.testInst.files.data_path):
            if (the_file[0:13] == 'pysat_testing') & \
                    (the_file[-19:] == '.pysat_testing_file'):
                file_path = os.path.join(self.testInst.files.data_path,
                                         the_file)
                if os.path.isfile(file_path) & (to_be_removed > 0):
                    to_be_removed -= 1
                    # Remove all versions of the file
                    # otherwise, previous versions will look like new files
                    pattern = '_'.join(file_path.split('_')[0:7]) + \
                        '*.pysat_testing_file'
                    map(os.unlink, glob.glob(pattern))
                    # os.unlink(file_path)
        # add new files
        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False, root_fname=self.root_fname)
        # get new files
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))

    def test_files_non_standard_pysat_directory(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 15)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        pysat.instruments.pysat_testing.list_files = list_versioned_files
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             sat_id='hello',
                             directory_format='pysat_testing_{tag}_{sat_id}',
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)
        # add new files
        create_dir(self.testInst)
        remove_files(self.testInst)
        create_versioned_files(self.testInst, start, stop, freq='100min',
                               use_doy=False, root_fname=self.root_fname)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             sat_id='hello',
                             directory_format='pysat_testing_{tag}_{sat_id}',
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

        # get new files
        new_files = self.testInst.files.get_new()
        assert (np.all(self.testInst.files.files.index == dates) &
                np.all(new_files.index == dates))

    def test_files_non_standard_file_format_template(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 15)
        dates = pysat.utils.time.create_date_range(start, stop, freq='1D')

        # clear out old files, create new ones
        remove_files(self.testInst)
        create_versioned_files(self.testInst, start, stop, freq='1D',
                               use_doy=False,
                               root_fname=''.join(('pysat_testing_unique_',
                                                   '{version:02d}_',
                                                   '{revision:03d}_{year:04d}',
                                                   '_g_{day:03d}_st.pysat_',
                                                   'testing_file')))

        pysat.instruments.pysat_testing.list_files = list_versioned_files
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             file_format=''.join(('pysat_testing_unique_',
                                                  '{version:02d}_',
                                                  '{revision:03d}_{year:04d}_',
                                                  'g_{day:03d}_st.pysat_',
                                                  'testing_file')),
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)
        assert (np.all(self.testInst.files.files.index == dates))

    def test_files_when_duplicates_forced(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008, 1, 11)
        stop = pysat.datetime(2008, 1, 15)
        dates = pysat.utils.time.create_date_range(start, stop, freq='1D')

        # clear out old files, create new ones
        remove_files(self.testInst)
        create_versioned_files(self.testInst, start, stop, freq='1D',
                               use_doy=False,
                               root_fname=''.join(('pysat_testing_unique_',
                                                   '{version:02d}_',
                                                   '{revision:03d}_{year:04d}',
                                                   '_g_{day:03d}_st.pysat_',
                                                   'testing_file')))

        pysat.instruments.pysat_testing.list_files = list_files
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             file_format=''.join(('pysat_testing_unique_??_',
                                                  '???_{year:04d}_g_{day:03d}',
                                                  '_st.pysat_testing_file')),
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)
        assert (np.all(self.testInst.files.files.index == dates))


class TestInstrumentWithVersionedFilesNoFileListStorage(TestInstrumentWithVersionedFiles):

    temporary_file_list = True
