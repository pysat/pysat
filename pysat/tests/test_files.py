"""
tests the pysat meta object and code
"""
import datetime as dt
import functools
from importlib import reload
import numpy as np
import os
import time
import warnings

import pandas as pds
import pytest
import tempfile

import pysat
import pysat.instruments.pysat_testing
from pysat.utils import NetworkLock


def create_dir(inst=None, temporary_file_list=False):
    """Create a temporary datset directory for a test instrument"""
    if inst is None:
        # create instrument
        inst = pysat.Instrument(platform='pysat', name='testing',
                                temporary_file_list=temporary_file_list)

    # create data directories
    try:
        os.makedirs(inst.files.data_path)
    except OSError:
        # File already exists
        pass
    return


def create_files(inst, start, stop, freq=None, use_doy=True, root_fname=None,
                 version=False, content=None, timeout=None):
    """Create year doy file set

    Parameters
    ----------
    inst : pysat.Instrument
        A test instrument, used to generate file path
    start : dt.datetime
        The date for the first file to create
    stop : dt.datetime
        The date for the last file to create
    freq : str
        Frequency of file output.  Ex: '1D', '100min'
        (default=None)
    use_doy : bool
        If True, use Day of Year (doy)
        If False, use month / day
        (default=True)
    root_fname : str
        The format of the file name to create.  Uses standard pysat variables.
        Ex: 'pysat_testing_junk_{year:04d}_{day:03d}.txt'
        (default=None)
    version : bool
        If True, iterate over version / revision / cycle
        If False, ignore version / revision / cycle
        (default=False)
    content : str
        Custom text to write to temporary files
        (default=None)
    timeout : float
        Time is seconds to lock the files being created.  If None, no timeout is
        used.  (default=None)

    """

    if freq is None:
        freq = '1D'
    dates = pysat.utils.time.create_date_range(start, stop, freq=freq)

    if root_fname is None:
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_',
                              'stuff.pysat_testing_file'))
    if version:
        versions = np.array([1, 2])
        revisions = np.array([0, 1])
        cycles = np.array([0, 1])
    else:
        versions = [None]
        revisions = [None]
        cycles = [None]

    # create empty file
    for date in dates:
        yr, doy = pysat.utils.time.getyrdoy(date)
        if use_doy:
            doy = doy
        else:
            doy = date.day
        for version in versions:
            for revision in revisions:
                for cycle in cycles:

                    fname = os.path.join(inst.files.data_path,
                                         root_fname.format(year=yr,
                                                           day=doy,
                                                           month=date.month,
                                                           hour=date.hour,
                                                           minute=date.minute,
                                                           second=date.second,
                                                           version=version,
                                                           revision=revision,
                                                           cycle=cycle))
                    with NetworkLock(fname, 'w') as fout:
                        if content is not None:
                            fout.write(content)
                        if timeout is not None:
                            time.sleep(timeout)


def list_files(tag=None, inst_id=None, data_path=None, format_str=None,
               version=False):
    """Return a Pandas Series of every file for chosen instrument data"""

    if format_str is None:
        if version:
            format_str = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}_',
                                  '{day:03d}{hour:02d}{minute:02d}{second:02d}',
                                  '_stuff_{version:02d}_{revision:03d}_',
                                  '{cycle:02d}.pysat_testing_file'))
        else:
            format_str = ''.join(('pysat_testing_junk_{year:04d}_gold_',
                                  '{day:03d}_stuff_{month:02d}_{hour:02d}_',
                                  '{minute:02d}_{second:02d}.',
                                  'pysat_testing_file'))

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
        reload(pysat._files)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.data_dir = self.saved_data_path
        reload(pysat._files)

    def test_no_data_dir(self):
        """Instrument should error if no data directory is specified."""
        with pytest.raises(RuntimeError):
            pysat.Instrument()


class TestBasics():

    temporary_file_list = False
    version = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.out = ''
        # Use a two-year as default.  Some tests will use custom ranges.
        self.start = dt.datetime(2008, 1, 1)
        self.stop = dt.datetime(2009, 12, 31)

        # store current pysat directory
        self.data_path = pysat.data_dir

        # create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.utils.set_data_dir(self.tempdir.name, store=False)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             temporary_file_list=self.temporary_file_list)
        # create instrument directories in tempdir
        create_dir(self.testInst)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.utils.set_data_dir(self.data_path, store=False)
        self.tempdir.cleanup()
        del self.testInst, self.out, self.tempdir, self.start, self.stop

    def test_basic_repr(self):
        """The repr output will match the str output"""
        self.out = self.testInst.files.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("Local files") > 0

    def test_basic_str(self):
        """Check for lines from each decision point in str"""
        self.out = self.testInst.files.__str__()
        assert isinstance(self.out, str)
        # Test basic file output
        assert self.out.find('Number of files') > 0
        # Test no files
        assert self.out.find('Date Range') > 0

    def test_year_doy_files_directly_call_from_os(self):
        """Check that Files.from_os generates file list"""
        # create a bunch of files by year and doy
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_',
                              '{day:03d}_stuff.pysat_testing_file'))
        create_files(self.testInst, self.start, self.stop, freq='1D',
                     root_fname=root_fname, version=self.version)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        assert len(files) == (365 + 366)
        # check specific dates
        assert pds.to_datetime(files.index[0]) == dt.datetime(2008, 1, 1)
        assert pds.to_datetime(files.index[365]) == dt.datetime(2008, 12, 31)
        assert pds.to_datetime(files.index[-1]) == dt.datetime(2009, 12, 31)

    def test_year_doy_files_no_gap_in_name_directly_call_from_os(self):
        """Files.from_os generates file list for date w/o delimiter"""
        # create a bunch of files by year and doy
        root_fname = ''.join(('pysat_testing_junk_{year:04d}{day:03d}_stuff.',
                              'pysat_testing_file'))
        create_files(self.testInst, self.start, self.stop, freq='1D',
                     root_fname=root_fname, version=self.version)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        assert len(files) == (365 + 366)
        # check specific dates
        assert pds.to_datetime(files.index[0]) == dt.datetime(2008, 1, 1)
        assert pds.to_datetime(files.index[365]) == dt.datetime(2008, 12, 31)
        assert pds.to_datetime(files.index[-1]) == dt.datetime(2009, 12, 31)

    def test_year_month_day_files_directly_call_from_os(self):
        """Files.from_os generates file list for date w/ month"""
        # create a bunch of files by year and doy
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}',
                              '_stuff_{month:02d}.pysat_testing_file'))
        create_files(self.testInst, self.start, self.stop, freq='1D',
                     use_doy=False, root_fname=root_fname, version=self.version)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        assert len(files) == (365 + 366)
        # check specific dates
        assert pds.to_datetime(files.index[0]) == dt.datetime(2008, 1, 1)
        assert pds.to_datetime(files.index[365]) == dt.datetime(2008, 12, 31)
        assert pds.to_datetime(files.index[-1]) == dt.datetime(2009, 12, 31)

    def test_year_month_day_hour_files_directly_call_from_os(self):
        """Files.from_os generates file list for date w hours"""
        # create a bunch of files by year and doy
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}',
                              '_stuff_{month:02d}_{hour:02d}.pysat_testing',
                              '_file'))
        create_files(self.testInst, self.start, self.stop, freq='6h',
                     use_doy=False, root_fname=root_fname, version=self.version)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        assert len(files) == (365 + 366) * 4 - 3
        # check specific dates
        assert pds.to_datetime(files.index[0]) == dt.datetime(2008, 1, 1)
        assert pds.to_datetime(files.index[1460]) == dt.datetime(2008, 12, 31)
        assert pds.to_datetime(files.index[-1]) == dt.datetime(2009, 12, 31)

    def test_year_month_day_hour_minute_files_directly_call_from_os(self):
        """Files.from_os generates file list for date w/ hours and minutes"""
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_',
                              'stuff_{month:02d}_{hour:02d}{minute:02d}.',
                              'pysat_testing_file'))
        # create a bunch of files by year and doy
        start = dt.datetime(2008, 1, 1)
        stop = dt.datetime(2008, 1, 4)
        create_files(self.testInst, start, stop, freq='30min',
                     use_doy=False, root_fname=root_fname, version=self.version)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        assert len(files) == 145
        # check specific dates
        assert pds.to_datetime(files.index[0]) == dt.datetime(2008, 1, 1)
        assert pds.to_datetime(files.index[1]) == dt.datetime(2008, 1, 1, 0, 30)
        assert pds.to_datetime(files.index[10]) == dt.datetime(2008, 1, 1, 5, 0)
        assert pds.to_datetime(files.index[-1]) == dt.datetime(2008, 1, 4)

    def test_year_month_day_hms_files_directly_call_from_os(self):
        """Files.from_os generates file list for date w/ hour/min/sec"""
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_',
                              'stuff_{month:02d}_{hour:02d}_{minute:02d}_',
                              '{second:02d}.pysat_testing_file'))
        # create a bunch of files by year and doy
        start = dt.datetime(2008, 1, 1)
        stop = dt.datetime(2008, 1, 3)
        create_files(self.testInst, start, stop, freq='30s',
                     use_doy=False, root_fname=root_fname, version=self.version)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        assert len(files) == 5761
        # check specific dates
        assert pds.to_datetime(files.index[0]) == dt.datetime(2008, 1, 1)
        assert (pds.to_datetime(files.index[1])
                == dt.datetime(2008, 1, 1, 0, 0, 30))
        assert pds.to_datetime(files.index[-1]) == dt.datetime(2008, 1, 3)

    def test_year_month_files_direct_call_to_from_os(self):
        """Files.from_os generates file list for monthly files"""
        # create a bunch of files by year and doy
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_stuff',
                              '_{month:02d}.pysat_testing_file'))
        create_files(self.testInst, self.start, self.stop, freq='1MS',
                     root_fname=root_fname, version=self.version)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)
        # check overall length
        assert len(files) == 24
        # check specific dates
        assert pds.to_datetime(files.index[0]) == dt.datetime(2008, 1, 1)
        assert pds.to_datetime(files.index[11]) == dt.datetime(2008, 12, 1)
        assert pds.to_datetime(files.index[-1]) == dt.datetime(2009, 12, 1)

    def test_instrument_has_no_files(self):
        """Instrument generates empty file list if no files"""

        pysat.instruments.pysat_testing.list_files = \
            functools.partial(list_files, version=self.version)
        inst = pysat.Instrument(platform='pysat', name='testing',
                                update_files=True)
        reload(pysat.instruments.pysat_testing)
        assert(inst.files.files.empty)

    def test_instrument_has_files(self):
        """Instrument generates file list if there are files"""
        import pysat.instruments.pysat_testing

        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_{day:03d}_'
                              'stuff_{month:02d}_{hour:02d}_{minute:02d}_'
                              '{second:02d}.pysat_testing_file'))
        # create a bunch of files by year and doy
        start = dt.datetime(2007, 12, 31)
        stop = dt.datetime(2008, 1, 10)
        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False, root_fname=root_fname)
        # create the same range of dates
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        pysat.instruments.pysat_testing.list_files = \
            functools.partial(list_files, version=self.version)
        inst = pysat.Instrument(platform='pysat', name='testing',
                                update_files=True)
        reload(pysat.instruments.pysat_testing)
        assert (np.all(inst.files.files.index == dates))


class TestBasicsNoFileListStorage(TestBasics):
    """Repeat basic tests with temporary file list"""

    temporary_file_list = True


class TestInstWithFiles():
    """Test basic file operations within an instrument"""

    temporary_file_list = False
    version = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir
        # create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.utils.set_data_dir(self.tempdir.name, store=False)
        # create testing directory
        create_dir(temporary_file_list=self.temporary_file_list)

        # create a test instrument, make sure it is getting files from
        # filesystem
        reload(pysat.instruments.pysat_testing)
        pysat.instruments.pysat_testing.list_files = \
            functools.partial(list_files, version=self.version)
        # create a bunch of files by year and doy
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             temporary_file_list=self.temporary_file_list)

        self.root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_',
                                   '{day:03d}_stuff_{month:02d}_{hour:02d}_',
                                   '{minute:02d}_{second:02d}.pysat_testing_',
                                   'file'))
        # Default file range.  Some tests will use custom ranges.
        self.start = dt.datetime(2007, 12, 31)
        self.stop = dt.datetime(2008, 1, 10)
        self.start2 = dt.datetime(2008, 1, 11)
        self.stop2 = dt.datetime(2008, 1, 12)

        create_files(self.testInst, self.start, self.stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             update_files=True,
                             file_format=self.root_fname,
                             temporary_file_list=self.temporary_file_list)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list, no files
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=self.temporary_file_list)
        pysat.utils.set_data_dir(self.data_path, store=False)
        self.tempdir.cleanup()
        del self.tempdir, self.start, self.stop, self.start2, self.stop2

    def test_refresh(self):
        """Check that refresh updates the files"""
        # create new files and make sure that new files are captured
        start = dt.datetime(2008, 1, 10)
        stop = dt.datetime(2008, 1, 12)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        start = dt.datetime(2007, 12, 31)
        dates = pysat.utils.time.create_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_refresh_on_ignore_empty_files(self):
        """Check that refresh can ignore empty files"""
        # setup created empty files - make sure such files can be ignored
        self.testInst.files.ignore_empty_files = True
        self.testInst.files.refresh()
        assert len(self.testInst.files.files) == 0

        # create new files with content and make sure they are captured
        create_files(self.testInst, self.start, self.stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname,
                     content='test', version=self.version)
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_refresh_on_unchanged_files(self):
        """Make sure new refresh does not duplicate files"""
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='100min')
        assert (np.all(self.testInst.files.files.index == dates))
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_instrument_with_ignore_empty_files(self):
        """Make sure new instruments can ignore empty files"""
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean', update_files=True,
                             temporary_file_list=self.temporary_file_list,
                             file_format=self.root_fname,
                             ignore_empty_files=True)

        assert len(self.testInst.files.files) == 0

        # create new files with content and make sure they are captured
        create_files(self.testInst, self.start, self.stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname, content='test',
                     version=self.version)
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_get_new_files_after_adding_files(self):
        """Check that get_new locates new files"""
        # create new files and make sure that new files are captured
        create_files(self.testInst, self.start2, self.stop2, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        dates = pysat.utils.time.create_date_range(self.start2, self.stop2,
                                                   freq='100min')
        new_files = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_refresh(self):
        """Check that get_new locates new files after refresh"""
        # create new files and make sure that new files are captured
        create_files(self.testInst, self.start2, self.stop2, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        dates = pysat.utils.time.create_date_range(self.start2, self.stop2,
                                                   freq='100min')
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_multiple_refreshes(self):
        """Check that get_new locates new files after multiple refreshes"""
        # create new files and make sure that new files are captured
        create_files(self.testInst, self.start2, self.stop2, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        dates = pysat.utils.time.create_date_range(self.start2, self.stop2,
                                                   freq='100min')
        self.testInst.files.refresh()
        self.testInst.files.refresh()
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_adding_files_and_adding_file(self):
        """Check that get_new works after multiple rounds of added files"""
        # create new files and make sure that new files are captured
        create_files(self.testInst, self.start2, self.stop2, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname)
        dates = pysat.utils.time.create_date_range(self.start2, self.stop2,
                                                   freq='100min')
        new_files = self.testInst.files.get_new()

        start = dt.datetime(2008, 1, 15)
        stop = dt.datetime(2008, 1, 18)

        create_files(self.testInst, start, stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        dates2 = pysat.utils.time.create_date_range(start, stop, freq='100min')
        new_files2 = self.testInst.files.get_new()
        assert np.all(new_files.index == dates)
        assert np.all(new_files2.index == dates2)

    def test_get_new_files_after_deleting_files_and_adding_files(self):
        """Check that get_new works after deleting and adding files"""
        # create new files and make sure that new files are captured
        dates = pysat.utils.time.create_date_range(self.start2, self.stop2,
                                                   freq='100min')

        # remove files, same number as will be added
        to_be_removed = len(dates)
        for the_file in os.listdir(self.testInst.files.data_path):
            if (the_file[0:13] == 'pysat_testing') & \
                    (the_file[-19:] == '.pysat_testing_file'):
                file_path = os.path.join(self.testInst.files.data_path,
                                         the_file)
                if os.path.isfile(file_path) & (to_be_removed > 0):
                    to_be_removed -= 1
                    os.unlink(file_path)
        # add new files
        create_files(self.testInst, self.start2, self.stop2, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        # get new files
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))


class TestInstWithFilesNonStandard():
    """Specialized tests for instruments with non-standard setups"""

    temporary_file_list = False
    version = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir
        # create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.utils.set_data_dir(self.tempdir.name, store=False)

        self.start = dt.datetime(2008, 1, 11)
        self.stop = dt.datetime(2008, 1, 15)
        self.root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_',
                                   '{day:03d}_stuff_{month:02d}_{hour:02d}_',
                                   '{minute:02d}_{second:02d}.pysat_testing_',
                                   'file'))
        reload(pysat.instruments.pysat_testing)

        # Use custom list_files routine
        pysat.instruments.pysat_testing.list_files = \
            functools.partial(list_files, version=self.version)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        self.tempdir.cleanup()
        del self.tempdir
        if hasattr(self, 'testInst'):
            # The two tests for error do not generate testInst
            del self.testInst
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list, no files
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=self.temporary_file_list)
        pysat.utils.set_data_dir(self.data_path, store=False)
        del self.start, self.stop

    def test_files_non_standard_pysat_directory(self):
        """Check that files work with a weird directory structure"""
        # create new files and make sure that new files are captured
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='100min')

        nonstandard_dir = 'pysat_testing_{tag}_{inst_id}'

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             inst_id='hello',
                             directory_format=nonstandard_dir,
                             update_files=True, file_format=self.root_fname,
                             temporary_file_list=self.temporary_file_list)
        # add new files
        create_dir(self.testInst)
        create_files(self.testInst, self.start, self.stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)

        # refresh file list
        self.testInst.files.refresh()

        # get new files
        new_files = self.testInst.files.get_new()
        assert np.all(self.testInst.files.files.index == dates)
        assert np.all(new_files.index == dates)

    def test_files_non_standard_file_format_template(self):
        """Check that files work if format has a weird heirarchy"""
        # create new files and make sure that new files are captured
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='1D')
        if self.version:
            root_fname = ''.join(('pysat_testing_unique_{version:02d}_',
                                  '{revision:03d}_{cycle:02d}_{year:04d}',
                                  '_g_{day:03d}_st.pysat_testing_file'))
        else:
            root_fname = ''.join(('pysat_testing_unique_junk_{year:04d}_gold',
                                  '_{day:03d}_stuff.pysat_testing_file'))

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             file_format=root_fname,
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

        # add new files
        create_dir(self.testInst)
        create_files(self.testInst, self.start, self.stop, freq='1D',
                     use_doy=False, root_fname=root_fname, version=self.version)
        # refresh file list
        self.testInst.files.refresh()

        assert (np.all(self.testInst.files.files.index == dates))

    def test_files_non_standard_file_format_template_no_variables(self):
        """Instrument should error if format template has no variables"""

        with pytest.raises(ValueError):
            self.testInst = \
                pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                                 clean_level='clean',
                                 file_format=''.join(('pysat_testing_unique_',
                                                      'junk_stuff.',
                                                      'pysat_testing_file')),
                                 update_files=True,
                                 temporary_file_list=self.temporary_file_list)

    def test_files_non_standard_file_format_template_wrong_type(self):
        """Instrument should error if format template is not a string"""

        with pytest.raises(ValueError):
            self.testInst = \
                pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                                 clean_level='clean',
                                 file_format=15,
                                 update_files=True,
                                 temporary_file_list=self.temporary_file_list)


class TestInstWithFilesNoFileListStorage(TestInstWithFiles):
    """Repeat all file tests with a temporary file list"""

    temporary_file_list = True
    version = False


class TestInstWithFilesNoFileListStorageNonStd(TestInstWithFilesNonStandard):
    """Repeat all file tests with a temporary file list"""

    temporary_file_list = True
    version = False


class TestInstWithVersionedFiles(TestInstWithFiles):
    """Repeat all file tests with versioned files"""

    temporary_file_list = False
    version = True


class TestInstWithVersionedFilesNonStandard(TestInstWithFilesNonStandard):
    """Repeat all non-standard file tests with versioned files.
    Includes additional tests for versioned strings"""

    temporary_file_list = False
    version = True

    def test_files_when_duplicates_forced(self):
        # create new files and make sure that new files are captured
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='1D')

        file_format = ''.join(('pysat_testing_unique_{version:02d}_',
                               '{revision:03d}_{cycle:02d}_{year:04d}',
                               '_g_{day:03d}_st.pysat_testing_file'))
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             file_format=file_format,
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

        # add new files
        create_dir(self.testInst)
        create_files(self.testInst, self.start, self.stop, freq='1D',
                     use_doy=False, root_fname=file_format,
                     version=self.version)

        pysat.instruments.pysat_testing.list_files = \
            functools.partial(list_files, version=self.version)
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean', file_format=file_format,
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)
        assert (np.all(self.testInst.files.files.index == dates))


def create_instrument(j):
    """This function must be in the top level to be picklable

    update_files should update the file list in .pysat
    """
    root_fname = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}',
                          '_{day:03d}{hour:02d}{minute:02d}',
                          '{second:02d}_stuff_{version:02d}_',
                          '{revision:03d}_{cycle:02d}.pysat_testing_file'))

    testInst = \
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=False)

    start = dt.datetime(2007, 12, 30)
    stop = dt.datetime(2007, 12, 31)
    create_files(testInst, start, stop, freq='1D', use_doy=False,
                 root_fname=root_fname, timeout=0.5, version=True)

    testInst = \
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=False)

    print('initial files created in {}:'.format(testInst.files.data_path))

    return 'instrument {}'.format(j)


class TestFilesRaceCondition():

    temporary_file_list = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir
        # create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.utils.set_data_dir(self.tempdir.name, store=False)
        # create testing directory
        create_dir(temporary_file_list=self.temporary_file_list)

        # create a test instrument, make sure it is getting files from
        # filesystem
        reload(pysat.instruments.pysat_testing)
        pysat.instruments.pysat_testing.list_files = \
            functools.partial(list_files, version=True)
        # create a bunch of files by year and doy
        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             temporary_file_list=self.temporary_file_list)

        self.root_fname = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}',
                                   '_{day:03d}{hour:02d}{minute:02d}',
                                   '{second:02d}_stuff_{version:02d}_',
                                   '{revision:03d}_{cycle:02d}',
                                   '.pysat_testing_file'))
        start = dt.datetime(2007, 12, 30)
        stop = dt.datetime(2008, 12, 31)
        create_files(self.testInst, start, stop, freq='1D',
                     use_doy=False, root_fname=self.root_fname, version=True)

        self.testInst = \
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             clean_level='clean',
                             update_files=True,
                             temporary_file_list=self.temporary_file_list)

        print(' '.join(('initial files created in ',
                        self.testInst.files.data_path)))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        self.tempdir.cleanup()
        del self.testInst, self.tempdir
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list, no files
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=self.temporary_file_list)
        pysat.utils.set_data_dir(self.data_path, store=False)

# TODO: This needs to be replaced or expanded based on the tests that
# portalocker uses
    def test_race_condition(self):
        from multiprocessing import Pool
        processes = 5
        p = Pool(processes)
        pysat.file_timeout = 1

        print('beginning tests with file_timeout {}'.format(pysat.file_timeout))
        result = p.map(create_instrument, range(processes))
        print(result)


class TestDeprecation():

    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always")

    def teardown(self):
        """Runs after every method to clean up previous testing"""

    def test_deprecation_warning_process_parsed_filenames(self):
        """Test if _files.process_parsed_filenames is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                pysat._files.process_parsed_filenames({})
            except KeyError:
                # Inputting empty dict will produce KeyError
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_deprecation_warning_parse_fixed_width_filenames(self):
        """Test if _files.parse_fixed_width_filenames is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            # Empty input produces empty output
            pysat._files.parse_fixed_width_filenames([], '')

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_deprecation_warning_parse_delimited_filenames(self):
        """Test if _files.parse_delimited_filenames is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            # Empty input produces empty output
            pysat._files.parse_delimited_filenames([], '', '')

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_deprecation_warning_construct_searchstring_from_format(self):
        """Test if _files.construct_searchstring_from_format is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            # Empty input produces empty output
            pysat._files.construct_searchstring_from_format('')

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_deprecation_warning_search_local_system_formatted_filename(self):
        """Test if _files.search_local_system_formatted_filename is deprecated
        """

        with warnings.catch_warnings(record=True) as war:
            # Empty input produces empty output
            pysat._files.search_local_system_formatted_filename('', '')

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
