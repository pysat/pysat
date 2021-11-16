"""Test pysat Files object and code."""

import datetime as dt
import functools
from importlib import reload
from multiprocessing import Pool
import numpy as np
import os
import pandas as pds
import tempfile
import time

import pytest

import pysat
from pysat.instruments.methods.testing import create_files
import pysat.instruments.pysat_testing
from pysat.tests.classes.cls_ci import CICleanSetup


def create_dir(inst=None, temporary_file_list=False):
    """Create a temporary datset directory for a test instrument."""
    if inst is None:
        # create instrument
        inst = pysat.Instrument(platform='pysat', name='testing',
                                temporary_file_list=temporary_file_list,
                                update_files=True)

    # create data directories
    try:
        os.makedirs(inst.files.data_path)
    except OSError:
        # File already exists
        pass
    return


def list_files(tag=None, inst_id=None, data_path=None, format_str=None,
               version=False):
    """Return a Pandas Series of every file for chosen instrument data."""

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
    return


class TestNoDataDir(object):
    """Test cases where data directory is not specified."""

    def setup(self):
        """Set up the unit test environment for each method."""
        self.temporary_file_list = False

        # Store the current pysat directory
        self.saved_data_path = pysat.params['data_dirs']

        pysat.params.data['data_dirs'] = []
        reload(pysat._files)
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        pysat.params.data['data_dirs'] = self.saved_data_path
        reload(pysat._files)
        return

    def test_no_data_dir(self):
        """Test that error is raised if no data directory is specified."""
        with pytest.raises(NameError) as nerr:
            pysat.Instrument()
        assert str(nerr).find("Please set a top-level directory path") >= 0
        return


class TestBasics(object):
    """Unit tests for `pysat._files`."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = False
        self.version = False
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return

    def setup(self):
        """Set up the unit test environment for each method."""
        self.out = ''

        # Use a two-year as default.  Some tests will use custom ranges.
        self.start = dt.datetime(2008, 1, 1)
        self.stop = dt.datetime(2009, 12, 31)

        # Store current pysat directory
        self.data_paths = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing, clean_level='clean',
            temporary_file_list=self.temporary_file_list, update_files=True)

        # Create instrument directories in tempdir
        create_dir(self.testInst)
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        pysat.params['data_dirs'] = self.data_paths
        self.tempdir.cleanup()
        del self.testInst, self.out, self.tempdir, self.start, self.stop
        return

    def test_basic_repr(self):
        """Test the standard `__repr__` output."""
        self.out = self.testInst.files.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("pysat.Files(") >= 0
        return

    def test_eval_repr(self):
        """Test that eval of repr recreates object."""
        # Evaluate __repr__ string
        self.out = eval(self.testInst.files.__repr__())

        # Confirm new Instrument equal to original
        assert self.out == self.testInst.files
        return

    def test_eval_repr_and_copy(self):
        """Test that eval of repr consistent with object copy."""
        # Evaluate __repr__ string
        self.out = eval(self.testInst.files.__repr__())

        # Get copy of original object
        second_out = self.testInst.files.copy()

        # Confirm new object equal to copy
        assert self.out == second_out

        return

    def test_basic_str(self):
        """Check for lines from each decision point in str."""
        self.out = self.testInst.files.__str__()
        assert isinstance(self.out, str)

        # Test basic file output
        assert self.out.find('Number of files') > 0

        # Test no files
        assert self.out.find('Date Range') > 0
        return

    def test_equality_with_copy(self):
        """Test that copy is the same as original."""
        # Create copy
        self.out = self.testInst.files.copy()

        # Confirm equal to original
        assert self.out == self.testInst.files
        return

    def test_equality_with_copy_with_data(self):
        """Test that copy is the same as original, loaded `inst.data`."""
        # Load data
        self.testInst.load(date=self.start)

        # Make copy
        self.out = self.testInst.files.copy()

        # Test for equality
        assert self.out == self.testInst.files
        return

    def test_inequality_modified_object(self):
        """Test that equality is false if other missing attributes."""
        # Copy files class
        self.out = self.testInst.files.copy()

        # Remove attribute
        del self.out.start_date

        # Confirm not equal
        assert self.testInst.files != self.out
        return

    def test_inequality_reduced_object(self):
        """Test that equality is false if self missing attributes."""
        self.out = self.testInst.files.copy()
        self.out.hi_there = 'hi'
        assert self.testInst.files != self.out
        return

    def test_inequality_different_data(self):
        """Test that equality is false if different data."""
        self.out = self.testInst.files.copy()
        self.out.files = pds.Series()
        assert self.out != self.testInst.files
        return

    def test_inequality_different_type(self):
        """Test that equality is false if different type."""
        assert self.testInst.files != self.testInst
        return

    def test_from_os_requires_data_path(self):
        """Check that path required for from_os."""
        with pytest.raises(ValueError) as verr:
            self.testInst.files.from_os()
        assert str(verr).find('Must supply instrument') > 0
        return

    def test_year_doy_files_directly_call_from_os(self):
        """Check that Files.from_os generates file list."""
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
        return

    def test_year_doy_files_no_gap_in_name_directly_call_from_os(self):
        """Test that `Files.from_os` makes file list for date w/o delimiter."""

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
        return

    def test_year_month_day_files_directly_call_from_os(self):
        """Test that `Files.from_os` generates file list for date w/ month."""
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
        return

    def test_year_month_day_hour_files_directly_call_from_os(self):
        """Test that `Files.from_os` generates file list for date w hours."""
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
        return

    def test_year_month_day_hour_minute_files_directly_call_from_os(self):
        """Test `Files.from_os` generates file list w/ hours and minutes."""
        root_fname = ''.join(('pysat_testing_fromos_{year:04d}_gold_{day:03d}_',
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
        return

    def test_year_month_day_hms_files_directly_call_from_os(self):
        """Test `Files.from_os` generates file list for date w/ hour/min/sec."""
        root_fname = ''.join(('pysat_testing_hms_{year:04d}_gold_{day:03d}_',
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
        return

    def test_year_month_files_direct_call_to_from_os(self):
        """Test that `Files.from_os` generates file list for monthly files."""
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
        return

    def test_instrument_has_no_files(self):
        """Test that instrument generates empty file list if no files."""

        pysat.instruments.pysat_testing.list_files = functools.partial(
            list_files, version=self.version)
        inst = pysat.Instrument(platform='pysat', name='testing',
                                update_files=True)
        reload(pysat.instruments.pysat_testing)
        assert(inst.files.files.empty)
        return

    def test_instrument_has_files(self):
        """Test that instrument generates file list if there are files."""
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

        pysat.instruments.pysat_testing.list_files = functools.partial(
            list_files, version=self.version)
        inst = pysat.Instrument(platform='pysat', name='testing',
                                update_files=True)
        reload(pysat.instruments.pysat_testing)

        assert (np.all(inst.files.files.index == dates))
        return

    def test_get_file_array_single(self):
        """Test `get_file_array` basic access."""

        files = self.testInst.files.get_file_array(self.testInst.files[0],
                                                   self.testInst.files[-1])

        # Ensure we have the right number files
        assert len(files) == len(self.testInst.files.files)
        assert len(files) > 0

        # Ensure it stores strings
        assert isinstance(files[0], str)
        return

    def test_get_file_array_multiple(self):
        """Test `get_file_array` basic access with a list of strings."""

        start1 = self.testInst.files[0]
        stop1 = self.testInst.files[10]

        start2 = self.testInst.files[11]
        stop2 = self.testInst.files[-1]

        # Get list of files
        files = self.testInst.files.get_file_array([start1, start2],
                                                   [stop1, stop2])

        # Get what should be same list of files
        files2 = self.testInst.files.get_file_array(start1, stop2)

        # Ensure we have the right files
        assert np.all(files == files2)
        return

    def test_get_index(self):
        """Ensure `test_index` working as expected."""
        in_idxs = [0, 10, 100]
        for in_idx in in_idxs:
            idx = self.testInst.files.get_index(self.testInst.files[in_idx])
            assert idx == in_idx
        return

    def test_get_index_nonexistent_file(self):
        """Ensure test_index working as expected file not found."""
        in_idxs = [0, 10, 100]
        for in_idx in in_idxs:
            test_str = ''.join(('_', self.testInst.files[in_idx]))
            with pytest.raises(ValueError) as verr:
                self.testInst.files.get_index(test_str)
            assert str(verr).find('in available file list') > 0
        return

    def test_default_directory_format(self):
        """Ensure default directory format from params is used."""
        files = pysat.Files(self.testInst)
        assert files.directory_format == pysat.params['directory_format']
        return


class TestBasicsNoFileListStorage(TestBasics):
    """Repeat basic tests with temporary file list."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = True
        self.version = False
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return


class TestInstWithFiles(object):
    """Test basic file operations within an instrument."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = False
        self.version = False
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return

    def setup(self):
        """Set up the unit test environment for each method."""
        # Store current pysat directory
        self.data_paths = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]
        # create testing directory
        create_dir(temporary_file_list=self.temporary_file_list)

        # create a test instrument, make sure it is getting files from
        # filesystem
        reload(pysat.instruments.pysat_testing)
        pysat.instruments.pysat_testing.list_files = functools.partial(
            list_files, version=self.version)
        # create a bunch of files by year and doy
        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
            clean_level='clean',
            temporary_file_list=self.temporary_file_list,
            update_files=True)

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

        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
            clean_level='clean',
            update_files=True,
            file_format=self.root_fname,
            temporary_file_list=self.temporary_file_list)
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        del self.testInst
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list, no files
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=self.temporary_file_list)
        pysat.params['data_dirs'] = self.data_paths
        self.tempdir.cleanup()
        del self.tempdir, self.start, self.stop, self.start2, self.stop2
        return

    def test_refresh(self):
        """Check that refresh updates the files."""
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
        return

    def test_refresh_on_ignore_empty_files(self):
        """Check that refresh can ignore empty files."""
        # setup created empty files - make sure such files can be ignored
        self.testInst.files.ignore_empty_files = True
        self.testInst.files.refresh()
        assert len(self.testInst.files.files) == 0
        return

        # create new files with content and make sure they are captured
        create_files(self.testInst, self.start, self.stop, freq='100min',
                     use_doy=False,
                     root_fname=self.root_fname,
                     content='test', version=self.version)
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))
        return

    def test_refresh_on_unchanged_files(self):
        """Make sure new refresh does not duplicate files."""
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='100min')
        assert (np.all(self.testInst.files.files.index == dates))
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))
        return

    def test_instrument_with_ignore_empty_files(self):
        """Make sure new instruments can ignore empty files."""
        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
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
        return

    def test_get_new_files_after_adding_files(self):
        """Check that get_new locates new files."""
        # create new files and make sure that new files are captured
        create_files(self.testInst, self.start2, self.stop2, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        dates = pysat.utils.time.create_date_range(self.start2, self.stop2,
                                                   freq='100min')
        new_files = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates))
        return

    def test_get_new_files_after_refresh(self):
        """Check that get_new locates new files after refresh."""
        # create new files and make sure that new files are captured
        create_files(self.testInst, self.start2, self.stop2, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)
        dates = pysat.utils.time.create_date_range(self.start2, self.stop2,
                                                   freq='100min')
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))
        return

    def test_get_new_files_after_multiple_refreshes(self):
        """Check that get_new locates new files after multiple refreshes."""
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
        return

    def test_get_new_files_after_adding_files_and_adding_file(self):
        """Check that get_new works after multiple rounds of added files."""
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
        return

    def test_get_new_files_after_deleting_files_and_adding_files(self):
        """Check that get_new works after deleting and adding files."""
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
        return


class TestInstWithFilesNonStandard(object):
    """Specialized tests for instruments with non-standard setups."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = False
        self.version = False
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return

    def setup(self):
        """Set up the unit test environment for each method."""
        # store current pysat directory
        self.data_paths = pysat.params['data_dirs']
        # create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.start = dt.datetime(2008, 1, 11)
        self.stop = dt.datetime(2008, 1, 15)
        self.root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_',
                                   '{day:03d}_stuff_{month:02d}_{hour:02d}_',
                                   '{minute:02d}_{second:02d}.pysat_testing_',
                                   'file'))
        reload(pysat.instruments.pysat_testing)

        # Use custom list_files routine
        pysat.instruments.pysat_testing.list_files = functools.partial(
            list_files, version=self.version)
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        self.tempdir.cleanup()
        del self.tempdir
        if hasattr(self, 'testInst'):
            # The two tests for error do not generate testInst
            del self.testInst
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list, no files
        pysat.params['data_dirs'] = self.data_paths
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                         clean_level='clean',
                         update_files=True,
                         temporary_file_list=self.temporary_file_list)
        del self.start, self.stop
        return

    def test_files_non_standard_pysat_directory(self):
        """Check that files work with a weird directory structure."""
        # Create new files and make sure that new files are captured
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='100min')

        nonstandard_dir = 'pysat_testing_{tag}_{inst_id}'

        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
            clean_level='clean',
            directory_format=nonstandard_dir,
            update_files=True, file_format=self.root_fname,
            temporary_file_list=self.temporary_file_list)

        # Add new files
        create_dir(self.testInst)
        create_files(self.testInst, self.start, self.stop, freq='100min',
                     use_doy=False, root_fname=self.root_fname,
                     version=self.version)

        # Refresh file list
        self.testInst.files.refresh()

        # Get new files
        new_files = self.testInst.files.get_new()
        assert np.all(self.testInst.files.files.index == dates)
        assert np.all(new_files.index == dates)
        return

    def test_files_non_standard_file_format_template(self):
        """Check that files work if format has a weird heirarchy."""
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

        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
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
        return

    def test_files_non_standard_file_format_template_no_variables(self):
        """Test instrument raises error if format template has no variables."""

        with pytest.raises(ValueError) as verr:
            self.testInst = pysat.Instrument(
                inst_module=pysat.instruments.pysat_testing,
                clean_level='clean',
                file_format=''.join(('pysat_testing_unique_junk_stuff.',
                                     'pysat_testing_file')),
                update_files=True,
                temporary_file_list=self.temporary_file_list)
        assert str(verr).find('file format set to default') > 0
        return

    def test_files_non_standard_file_format_template_wrong_type(self):
        """Test instrument raises error if format template is not a string."""

        with pytest.raises(ValueError) as verr:
            self.testInst = pysat.Instrument(
                inst_module=pysat.instruments.pysat_testing,
                clean_level='clean',
                file_format=15,
                update_files=True,
                temporary_file_list=self.temporary_file_list)
        assert str(verr).find('file format set to default') >= 0
        return


class TestInstWithFilesNoFileListStorage(TestInstWithFiles):
    """Repeat all file tests with a temporary file list."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = True
        self.version = False
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return


class TestInstWithFilesNoFileListStorageNonStd(TestInstWithFilesNonStandard):
    """Repeat all file tests with a temporary file list."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = True
        self.version = False
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return


class TestInstWithVersionedFiles(TestInstWithFiles):
    """Repeat all file tests with versioned files."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = False
        self.version = True
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return


class TestInstWithVersionedFilesNonStandard(TestInstWithFilesNonStandard):
    """Repeat all non-standard file tests with versioned files.

    Note
    ----
    Includes additional tests for versioned strings.

    """

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = False
        self.version = True
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list, self.version
        return

    def test_files_when_duplicates_forced(self):
        """Test that new files are captured when duplicates are forced."""
        # Create new files and make sure that new files are captured
        dates = pysat.utils.time.create_date_range(self.start, self.stop,
                                                   freq='1D')

        file_format = ''.join(('pysat_testing_unique_{version:02d}_',
                               '{revision:03d}_{cycle:02d}_{year:04d}',
                               '_g_{day:03d}_st.pysat_testing_file'))
        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
            clean_level='clean',
            file_format=file_format,
            update_files=True,
            temporary_file_list=self.temporary_file_list)

        # add new files
        create_dir(self.testInst)
        create_files(self.testInst, self.start, self.stop, freq='1D',
                     use_doy=False, root_fname=file_format,
                     version=self.version)

        pysat.instruments.pysat_testing.list_files = functools.partial(
            list_files, version=self.version)
        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
            clean_level='clean', file_format=file_format,
            update_files=True,
            temporary_file_list=self.temporary_file_list)
        assert (np.all(self.testInst.files.files.index == dates))
        return


def create_instrument(j):
    """Create new instrument with files for unit tests.

    Note
    ----
    This function must be in the top level to be picklable.

    update_files should update the file list in .pysat

    """
    root_fname = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}',
                          '_{day:03d}{hour:02d}{minute:02d}',
                          '{second:02d}_stuff_{version:02d}_',
                          '{revision:03d}_{cycle:02d}.pysat_testing_file'))

    testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                                clean_level='clean',
                                update_files=True,
                                temporary_file_list=False)

    start = dt.datetime(2007, 12, 30)
    stop = dt.datetime(2007, 12, 31)
    create_files(testInst, start, stop, freq='1D', use_doy=False,
                 root_fname=root_fname, timeout=0.5, version=True)

    testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                                clean_level='clean',
                                update_files=True,
                                temporary_file_list=False)

    print('initial files created in {}:'.format(testInst.files.data_path))

    return 'instrument {}'.format(j)


class TestFilesRaceCondition(object):
    """Tests for multiple instances of pysat running simultaneously."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""
        self.temporary_file_list = False
        return

    def teardown_class(self):
        """Clean up class-level variables after all tests are run."""
        del self.temporary_file_list
        return

    def setup(self):
        """Set up the unit test environment for each method."""
        # Store current pysat directory
        self.data_paths = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]
        # create testing directory
        create_dir(temporary_file_list=self.temporary_file_list)

        # create a test instrument, make sure it is getting files from
        # filesystem
        reload(pysat.instruments.pysat_testing)
        pysat.instruments.pysat_testing.list_files = functools.partial(
            list_files, version=True)
        # create a bunch of files by year and doy
        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
            clean_level='clean',
            temporary_file_list=self.temporary_file_list,
            update_files=True)

        self.root_fname = ''.join(('pysat_testing_junk_{year:04d}_{month:02d}',
                                   '_{day:03d}{hour:02d}{minute:02d}',
                                   '{second:02d}_stuff_{version:02d}_',
                                   '{revision:03d}_{cycle:02d}',
                                   '.pysat_testing_file'))
        start = dt.datetime(2007, 12, 30)
        stop = dt.datetime(2008, 12, 31)
        create_files(self.testInst, start, stop, freq='1D',
                     use_doy=False, root_fname=self.root_fname, version=True)

        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing,
            clean_level='clean',
            update_files=True,
            temporary_file_list=self.temporary_file_list)

        print(' '.join(('initial files created in ',
                        self.testInst.files.data_path)))

    def teardown(self):
        """Clean up the unit test environment after each method."""
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
        pysat.params['data_dirs'] = self.data_paths

# TODO(#871): This needs to be replaced or expanded based on the tests that
# portalocker uses
    def test_race_condition(self):
        """Test that multiple instances of pysat instrument creation run."""
        processes = 5
        proc_pool = Pool(processes)
        pysat.file_timeout = 1

        proc_pool.map(create_instrument, range(processes))
        return


class TestCIonly(CICleanSetup):
    """Tests where we mess with local settings.

    Note
    ----
    These only run in CI environments to avoid breaking an end user's setup

    """

    def test_initial_pysat_load(self, capsys):
        """Ensure data_dirs check in Files works."""

        # Ensure pysat is running in 'first-time' mode
        reload(pysat)
        captured = capsys.readouterr()
        assert captured.out.find("Hi there!") >= 0

        # Ensure the pysat 'data_dirs' param is empty list on both
        # local systems and CI.
        pysat.params.data['data_dirs'] = []

        # Try to instantiate Instrument
        with pytest.raises(NameError) as nerr:
            pysat.Instrument('pysat', 'testing')

        # Confirm we have the correct error
        assert str(nerr).find("pysat's `data_dirs` hasn't been set.") >= 0
        return
