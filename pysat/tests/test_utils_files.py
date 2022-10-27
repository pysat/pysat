#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the `pysat.utils.files` functions."""

import datetime as dt
from importlib import reload
import numpy as np
import os
import pandas as pds
import platform
import pytest
import tempfile

import pysat
import pysat.instruments.methods.testing as pimtesting
from pysat.tests.classes.cls_ci import CICleanSetup
from pysat.utils import files as futils
from pysat.utils import testing


class TestParseDelimitedFilenames(object):
    """Unit tests for the `parse_delimited_filename` function."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.temporary_file_list = False
        self.fkwargs = [{"year": 2009, "month": 12, "day": 12 + 3 * i,
                         "hour": 8 + 2 * i, "minute": 8 + 2 * i,
                         "second": 1 + 3 * i, "version": 'v{:d}'.format(i),
                         "revision": i, "cycle": 'c{:d}'.format(i + 2)}
                        for i in range(6)]
        self.kw_format = {'year': '{year:04d}', 'month': '{month:02d}',
                          'day': '{day:02d}', 'hour': '{hour:02d}',
                          'minute': '{minute:02d}', 'second': '{second:02d}',
                          'version': '{version:2s}',
                          'revision': '{revision:02d}', 'cycle': '{cycle:2s}'}
        self.file_dict = {}

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.fkwargs, self.file_dict, self.kw_format
        del self.temporary_file_list

    def eval_parse_delimited_filename(self):
        """Evaluate the output of a `parse_delimited_filename` unit test.

        Returns
        -------
        bool
            True if there is data to evalute, False if data dict is empty

        """
        # Evaluate the returned data dict
        if len(self.file_dict.keys()) < 2:
            return False

        # Extract the test lists
        if len(self.fkwargs) > 0:
            test_kwargs = {fkey: [kwargs[fkey] for kwargs in self.fkwargs]
                           for fkey in self.fkwargs[0].keys()}
        else:
            test_kwargs = {}

        # Test each of the returned data keys
        for fkey in self.file_dict.keys():
            if fkey in test_kwargs:
                testing.assert_lists_equal(test_kwargs[fkey],
                                           self.file_dict[fkey])
            elif fkey == 'files':
                assert len(self.fkwargs) == len(self.file_dict[fkey]), \
                    "unexpected file list length"
            elif fkey != "format_str":
                assert self.file_dict[fkey] is None, \
                    "unused format key has a value"

        return True

    @pytest.mark.parametrize("sep_char,flead,good_kwargs", [
        ("_", "test_", ['year', 'month', 'day', 'hour', 'minute', 'version']),
        ('-', "test", ['year', 'day', 'hour', 'minute', 'second', 'cycle',
                       'revision']), ('fun', 'test', [])])
    def test_parse_delimited_filename(self, sep_char, flead, good_kwargs):
        """Check ability to parse list of delimited files."""
        # Format the test input
        fname = '{:s}{:s}.cdf'.format(flead, sep_char.join(
            [self.kw_format[fkey] for fkey in good_kwargs]))

        # Adjust the test input/comparison data for this run
        bad_kwargs = [fkey for fkey in self.fkwargs[0]
                      if fkey not in good_kwargs]

        for kwargs in self.fkwargs:
            for fkey in bad_kwargs:
                del kwargs[fkey]

        # Create the input file list
        file_list = [fname.format(**kwargs) for kwargs in self.fkwargs]

        # Get the test results
        self.file_dict = futils.parse_delimited_filenames(file_list, fname,
                                                          sep_char)

        # Test each of the return values
        assert self.eval_parse_delimited_filename()
        return

    def test_parse_delimited_filename_empty(self):
        """Check ability to parse list of delimited files with no files."""
        # Format the test input
        sep_char = '_'
        fname = ''.join(('test', '{year:04d}', '{day:03d}', '{hour:02d}',
                         '{minute:02d}', '{second:02d}', '{cycle:2s}.txt'))
        self.fkwargs = []

        # Get the test results
        self.file_dict = futils.parse_delimited_filenames([], fname, sep_char)

        # Test each of the return values
        assert self.eval_parse_delimited_filename()
        return


class TestFileDirectoryTranslations(CICleanSetup):
    """Unit tests for file directory setup."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        # Module is only required for testing installations on CI servers
        import pysatSpaceWeather

        # Create clean environment on the CI server
        CICleanSetup.setup_method(self)
        reload(pysat)

        # create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        # Create several pysat.SpaceWeather instruments and download data.
        # We want to start with a setup that covers general cases a user may
        # have.
        pysat.utils.registry.register_by_module(pysatSpaceWeather.instruments)

        self.insts = []
        self.insts_dates = []
        self.insts_kwargs = []

        # Data by day, ACE SIS data
        self.insts.append(pysat.Instrument('ace', 'sis', tag='historic',
                                           use_header=True))
        test_dates = pysatSpaceWeather.instruments.ace_sis._test_dates
        self.insts_dates.append([test_dates['']['historic']] * 2)
        self.insts_kwargs.append({})

        # Data with date mangling, regular F10.7 data, stored monthly
        self.insts.append(pysat.Instrument('sw', 'f107', tag='historic',
                                           use_header=True))
        test_dates = pysatSpaceWeather.instruments.sw_f107._test_dates
        self.insts_dates.append([test_dates['']['historic'],
                                 test_dates['']['historic']
                                 + dt.timedelta(weeks=52)])
        self.insts_kwargs.append({'freq': 'MS'})

        # Download data for all instruments
        for inst, dates, kwargs in zip(self.insts, self.insts_dates,
                                       self.insts_kwargs):
            ostr = ' '.join(('Downloading data for', inst.platform,
                             inst.name, inst.tag, inst.inst_id))
            print(ostr)

            # Support non-daily download frequencies
            dates = pds.date_range(dates[0], dates[1], **kwargs)
            inst.download(date_array=dates)

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        # Clean environment
        CICleanSetup.teardown_method(self)

        self.tempdir.cleanup()

    def test_updating_directories(self, capsys):
        """Test directory structure update method."""

        # A variety of options are performed within a single test
        # so that only one round of downloads is performed.

        # New Template
        templ = '{platform}'

        # Convert directories to simpler platform structure, as a test run,
        # with expanded descriptive output.
        futils.update_data_directory_structure(new_template=templ,
                                               full_breakdown=True)

        # Capture printouts
        captured = capsys.readouterr()

        # Check for descriptive output from full_breakdown
        fstr = 'Will move: '
        assert captured.out.find(fstr) >= 0

        # Check how many instruments have no files found. Will be used later.
        index = 0
        orig_num_missing = 0
        while index < len(captured.out):
            index = captured.out.find('No files found.', index)
            if index == -1:
                break
            else:
                index += 1
                orig_num_missing += 1

        # Convert directories to simpler platform structure
        futils.update_data_directory_structure(new_template=templ,
                                               test_run=False,
                                               remove_empty_dirs=True,
                                               full_breakdown=True)

        # Capture printouts
        captured = capsys.readouterr()

        # Check if we did things correctly. Look for correct output strings.
        for inst in self.insts:
            # Check for all files moved.
            fstr = ' '.join(('All', inst.platform, inst.name, inst.tag,
                             inst.inst_id, 'files moved and accounted for.',
                             '\n'))
            assert captured.out.find(fstr) >= 0

            # Check that directories were removed.
            assert not os.path.isdir(inst.files.data_path)

        # Store newly organized directory format
        pysat.params['directory_format'] = templ

        # Convert directories back to more complex structure
        # First, define new template
        templ = os.path.join('{platform}', '{name}', '{tag}', '{inst_id}')

        # Update structure
        futils.update_data_directory_structure(new_template=templ,
                                               test_run=False,
                                               remove_empty_dirs=True,
                                               full_breakdown=True)

        # Capture printouts
        captured = capsys.readouterr()

        # Check if we did things correctly. Look for correct output strings.
        for inst in self.insts:
            # Check for all files moved.
            fstr = ' '.join(('All', inst.platform, inst.name, inst.tag,
                             inst.inst_id, 'files moved and accounted for.',
                             '\n'))
            assert captured.out.find(fstr) >= 0

            # Refresh inst with the old directory template set to get now 'old'
            # path information.
            inst2 = pysat.Instrument(inst.platform, inst.name, tag=inst.tag,
                                     inst_id=inst.inst_id, use_header=True)

            # Check that directories with simpler platform org were NOT removed.
            assert os.path.isdir(inst2.files.data_path)

            # Confirm that the code was aware the directory was not empty.
            fstr = ''.join(('Directory is not empty: ',
                            inst2.files.data_path, '\nEnding cleanup.', '\n'))
            assert captured.out.find(fstr) >= 0

        # Try to update structure again. Files have already moved so
        # no files should be found.
        futils.update_data_directory_structure(new_template=templ,
                                               test_run=False,
                                               remove_empty_dirs=True,
                                               full_breakdown=True)

        # Capture printouts
        captured = capsys.readouterr()

        # Check for no files output
        index = 0
        num_missing = 0
        while index < len(captured.out):
            index = captured.out.find('No files found.', index)
            if index == -1:
                break
            else:
                index += 1
                num_missing += 1

        # Get difference in number of instruments with no files.
        new_missing = num_missing - orig_num_missing

        # Confirm none of the instruments had files.
        assert new_missing == len(self.insts)

        # Store new format like a typical user would
        pysat.params['directory_format'] = templ


class TestFileUtils(CICleanSetup):
    """Unit tests for general file/path utilities."""

    def setup_method(self):
        """Set up the unit test environment for each method."""
        self.out = ''

        # Use a two-year as default.  Some tests will use custom ranges.
        self.start = pysat.instruments.pysat_testing._test_dates['']['']
        self.stop = self.start + pds.DateOffset(years=2) - dt.timedelta(days=1)

        # Store current pysat directory
        self.data_paths = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.testInst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing, clean_level='clean',
            update_files=True, use_header=True)

        # Create instrument directories in tempdir
        pysat.utils.files.check_and_make_path(self.testInst.files.data_path)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        pysat.params['data_dirs'] = self.data_paths
        self.tempdir.cleanup()
        del self.testInst, self.out, self.tempdir, self.start, self.stop
        return

    def test_get_file_information(self):
        """Test `utils.files.get_file_information` success with existing files.

        """

        # Create a bunch of files by year and doy
        root_fname = ''.join(('pysat_testing_junk_{year:04d}_gold_',
                              '{day:03d}_stuff.pysat_testing_file'))
        pimtesting.create_files(self.testInst, self.start, self.stop, freq='1D',
                                root_fname=root_fname)

        # Use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
                                    format_str=root_fname)

        # Get file attributes
        root_dir = self.testInst.files.data_path
        file_info = futils.get_file_information(files.values,
                                                root_dir=root_dir)

        # Check overall length for each output key.
        for key in file_info.keys():
            assert len(file_info[key]) == len(files)

        # Ensure general correctness of time. If epoch or units wrong
        # then time will be way off. Allowing for difference between local
        # and UTC times.
        today = pysat.utils.time.today()
        assert np.all(file_info['content_modified_time']
                      <= today + dt.timedelta(days=1))
        assert np.all(file_info['content_modified_time']
                      >= today - dt.timedelta(days=1))

        return

    def test_check_and_make_path_exists(self):
        """Test successful pass at creating existing directory."""

        # Create a temporary directory
        tempdir = tempfile.TemporaryDirectory()
        assert os.path.isdir(tempdir.name)

        # Assert check_and_make_path does not re-create the directory
        assert not pysat.utils.files.check_and_make_path(tempdir.name)

        # Clean up temporary directory
        tempdir.cleanup()
        return

    @pytest.mark.parametrize("trailer", [None, '', 'extra',
                                         os.path.join('extra', 'extra'),
                                         os.path.join('yes', 'way', '..',
                                                      'brah'),
                                         os.path.join('.', 'yeppers')])
    def test_check_and_make_path_new(self, trailer):
        """Test successful pass at creating existing directory."""

        # Create a temporary directory and get its name
        tempdir = tempfile.TemporaryDirectory()
        new_dir = tempdir.name

        if trailer is not None:
            new_dir = os.path.join(new_dir, trailer)

        # Clean up temporary directory
        tempdir.cleanup()
        assert not os.path.isdir(new_dir)

        # Assert check_and_make_path re-creates the directory
        assert pysat.utils.files.check_and_make_path(new_dir)

        # Clean up the test directory
        os.rmdir(new_dir)
        return

    def test_check_and_make_path_expand_path(self):
        """Test successful pass at creating directory relative to home."""

        if platform.system == 'Windows':
            home = '%homedrive%%homepath%'
        else:
            home = '~'

        # Create path to a testing directory
        new_dir = os.path.join(home, 'pysat_check_path_testing')

        assert not os.path.isdir(new_dir)

        # Assert check_and_make_path creates the directory
        assert pysat.utils.files.check_and_make_path(new_dir, expand_path=True)

        new_dir = os.path.expanduser(new_dir)
        new_dir = os.path.expandvars(new_dir)
        assert os.path.isdir(new_dir)

        # Clean up the test directory
        os.rmdir(new_dir)
        return

    @pytest.mark.parametrize("path", ['no_starting_path_info',
                                      os.path.join('no', ' way ', ' brah ')])
    def test_check_and_make_path_error(self, path):
        """Test ValueError raised for invalid paths.

        Parameters
        ----------
        path : str
            String providing path

        """

        testing.eval_bad_input(pysat.utils.files.check_and_make_path,
                               ValueError, 'Invalid path specification.',
                               input_args=[path])

        return
