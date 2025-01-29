#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Tests the `pysat.utils.files` functions."""

from collections import OrderedDict
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


class TestConstructSearchstring(object):
    """Unit tests for the `construct_searchstring_from_format` function."""

    def setup_method(self):
        """Set up the unit test environment for each method."""
        self.out_dict = {}
        self.num_fmt = None
        self.str_len = None
        self.fill_len = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.out_dict, self.num_fmt, self.str_len, self.fill_len
        return

    def eval_output(self):
        """Evaluate the output dictionary."""

        testing.assert_lists_equal(['search_string', 'keys', 'type', 'lengths',
                                    'string_blocks'],
                                   list(self.out_dict.keys()))

        assert len(self.out_dict['keys']) == self.num_fmt
        assert len(''.join(self.out_dict['string_blocks'])) == self.str_len
        assert sum(self.out_dict['lengths']) == self.fill_len

        if self.out_dict['search_string'].find('*') < 0:
            assert len(
                self.out_dict['search_string']) == self.fill_len + self.str_len
        else:
            assert len(
                self.out_dict['search_string']) <= self.fill_len + self.str_len
        return

    @pytest.mark.parametrize("format_str,nfmt,slen,flen", [
        ("", 0, 0, 0), ("test", 0, 4, 0), ("{year:02d}{month:02d}", 2, 0, 4),
        ("test_{year:04d}.ext", 1, 9, 4)])
    def test_searchstring_success(self, format_str, nfmt, slen, flen):
        """Test successful construction of a searchable string.

        Parameters
        ----------
        format_str : str
            The naming pattern of the instrument files and the locations of
            date/version/revision/cycle information needed to create an ordered
            list.
        nfmt : int
            Number of formatting options included in the format string
        slen : int
            Length of non-formatted string segments
        flen : int
            Length of formatted segments

        """
        # Set the evaluation criteria
        self.num_fmt = nfmt
        self.str_len = slen
        self.fill_len = flen

        # Get the streachstring dictionary
        self.out_dict = futils.construct_searchstring_from_format(format_str)

        # Evaluate the output
        self.eval_output()
        return

    @pytest.mark.parametrize("format_str,nfmt,slen,flen, nwc", [
        ("", 0, 0, 0, 0), ("test", 0, 4, 0, 0),
        ("{year:02d}{month:02d}", 2, 0, 4, 2),
        ("test_{year:04d}_{month:02d}.ext", 2, 10, 6, 2)])
    def test_searchstring_w_wildcard(self, format_str, nfmt, slen, flen, nwc):
        """Test successful construction of a searchable string with wildcards.

        Parameters
        ----------
        format_str : str
            The naming pattern of the instrument files and the locations of
            date/version/revision/cycle information needed to create an ordered
            list.
        nfmt : int
            Number of formatting options included in the format string
        slen : int
            Length of non-formatted string segments
        flen : int
            Length of formatted segments
        nwc : int
            Number of wildcard (*) symbols

        """
        # Set the evaluation criteria
        self.num_fmt = nfmt
        self.str_len = slen
        self.fill_len = flen

        # Get the streachstring dictionary
        self.out_dict = futils.construct_searchstring_from_format(format_str,
                                                                  True)

        # Evaluate the output
        self.eval_output()
        assert len(self.out_dict['search_string'].split('*')) == nwc + 1
        return

    def test_searchstring_noformat(self):
        """Test failure if the input argument is NoneType."""

        testing.eval_bad_input(futils.construct_searchstring_from_format,
                               ValueError,
                               'Must supply a filename template (format_str).',
                               input_args=[None])
        return

    def test_searchstring_bad_wildcard(self):
        """Test failure if unsupported wildcard use is encountered."""

        testing.eval_bad_input(futils.construct_searchstring_from_format,
                               ValueError,
                               "Couldn't determine formatting width, check",
                               input_args=["test{year:02d}{month:d}.txt"])
        return


class TestParseFilenames(object):
    """Unit tests for the file parsing functions."""

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

    def eval_parsed_filenames(self):
        """Evaluate the output of a `parse_delimited_filename` unit test."""
        # Evaluate the returned data dict
        assert len(self.file_dict.keys()) >= 2, "insufficient keys in file dict"

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

        return

    @pytest.mark.parametrize("sep_char,flead,good_kwargs", [
        ("_", "test_", ['year', 'month', 'day', 'hour', 'minute', 'version']),
        ('-', "test", ['year', 'day', 'hour', 'minute', 'second', 'cycle',
                       'revision']), ('fun', 'test', [])])
    def test_parse_delimited_filename(self, sep_char, flead, good_kwargs):
        """Check ability to parse list of delimited files.

        Parameters
        ----------
        sep_char : str
            Separation character to use in joining the filename
        flead : str
            File prefix
        good_kwargs : list
            List of kwargs to include in the file format

        """
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
        self.eval_parsed_filenames()
        return

    @pytest.mark.parametrize("is_fixed", [True, False])
    def test_parse_filenames_all_bad(self, is_fixed):
        """Test files with a bad format are removed from consideration.

        Parameters
        ----------
        is_fixed : bool
            True for the fixed-width function, false for delimted.

        """

        # Format the test input
        format_str = 'bad_test_{:s}.cdf'.format("_".join(
            [self.kw_format[fkey] for fkey in self.fkwargs[0].keys()]))
        bad_format = format_str.replace('revision:02d', 'revision:2s')

        # Create the input file list
        file_list = []
        for kwargs in self.fkwargs:
            kwargs['revision'] = 'aa'
            file_list.append(bad_format.format(**kwargs))

        # Get the test results
        if is_fixed:
            self.file_dict = futils.parse_fixed_width_filenames(file_list,
                                                                format_str)
        else:
            self.file_dict = futils.parse_delimited_filenames(file_list,
                                                              format_str, "_")

        # Test that all files were removed
        assert len(self.file_dict['files']) == 0
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
        self.eval_parsed_filenames()
        return

    @pytest.mark.parametrize("sep_char,flead,good_kwargs", [
        ("_", "*_", ['year', 'month', 'day', 'hour', 'minute', 'version']),
        ('?', "test", ['year', 'day', 'hour', 'minute', 'second', 'cycle',
                       'revision']), ('fun', '*', [])])
    def test_parse_fixed_filename(self, sep_char, flead, good_kwargs):
        """Check ability to parse list of fixed width files.

        Parameters
        ----------
        sep_char : str
            Separation character to use in joining the filename
        flead : str
            File prefix
        good_kwargs : list
            List of kwargs to include in the file format

        """
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
        self.file_dict = futils.parse_fixed_width_filenames(file_list, fname)

        # Test each of the return values
        self.eval_parsed_filenames()
        return

    def test_parse_fixed_width_filename_empty(self):
        """Check ability to parse list of fixed-width files with no files."""
        # Format the test input
        fname = ''.join(('test*', '{year:04d}', '{day:03d}', '{hour:02d}',
                         '{minute:02d}', '{second:02d}', '{cycle:2s}.txt'))
        self.fkwargs = []

        # Get the test results
        self.file_dict = futils.parse_fixed_width_filenames([], fname)

        # Test each of the return values
        self.eval_parsed_filenames()
        return

    def test_init_parse_filename_empty(self):
        """Check the `_init_parse_filenames` output with no files."""
        # Format the test input
        fname = ''.join(('test*', '{year:04d}', '{day:03d}', '{hour:02d}',
                         '{minute:02d}', '{second:02d}', '{cycle:2s}.txt'))
        self.fkwargs = []

        # Get the test results
        self.file_dict, sdict = futils._init_parse_filenames([], fname)

        # Test each of the return values
        self.eval_parsed_filenames()
        assert len(sdict.keys()) == 0, "Search dict was defined unnecessarily"
        return

    def test_init_parse_filename_with_files(self):
        """Check the `_init_parse_filenames` output with files."""
        # Format the test input
        fname = ''.join(('test*', '{year:04d}', '{day:03d}', '{hour:02d}',
                         '{minute:02d}', '{second:02d}', '{cycle:2s}.txt'))

        # Create the input file list
        file_list = [fname.format(**kwargs) for kwargs in self.fkwargs]

        # Get the test results
        self.file_dict, sdict = futils._init_parse_filenames(file_list, fname)

        # Test the initalized dictionaries
        testing.assert_lists_equal(['search_string', 'keys', 'type', 'lengths',
                                    'string_blocks'], list(sdict.keys()))

        for skey in sdict['keys']:
            assert skey in self.file_dict.keys(), "Missing key {:}".format(skey)

        for fkey in self.file_dict.keys():
            assert self.file_dict[fkey] is None, "File dict not initalized"

        assert "files" not in self.file_dict.keys(), "'files' key set early"
        assert "format_str" not in self.file_dict.keys(), \
            "'format_str' key set early"
        return

    @pytest.mark.parametrize("bad_files", [[], [0]])
    def test_finish_parsed_filenames(self, bad_files):
        """Test output restucturing for `_finish_parsed_filenames`.

        Parameters
        ----------
        bad_files : list
            List of bad file indices

        """
        # Format the test input
        fname = ''.join(('test*', '{year:04d}', '{day:03d}', '{hour:02d}',
                         '{minute:02d}', '{second:02d}', '{cycle:2s}.txt'))

        # Create the input file list and dict
        file_list = [fname.format(**kwargs) for kwargs in self.fkwargs]
        self.file_dict = {'int': [1 for fname in file_list], 'none': None,
                          'float': [1.0 for fname in file_list],
                          'str': ['hi' for fname in file_list]}

        # Get the test results
        self.file_dict = futils._finish_parse_filenames(self.file_dict,
                                                        file_list, fname,
                                                        bad_files)

        # Adjust the expected file output
        if len(bad_files) > 0:
            file_list = [fname for i, fname in enumerate(file_list)
                         if i not in bad_files]

        # Test the output
        for fkey in self.file_dict:
            if fkey == 'none':
                assert self.file_dict[fkey] is None
            elif fkey == 'files':
                testing.assert_lists_equal(file_list, self.file_dict[fkey])
            elif fkey == 'format_str':
                assert fname == self.file_dict[fkey]
            else:
                testing.assert_isinstance(self.file_dict[fkey], np.ndarray)
                assert len(self.file_dict[fkey]) == len(file_list)
        return


class TestProcessParsedFilenames(object):
    """Unit tests for `process_parsed_filenames` function."""

    def setup_method(self):
        """Set up the unit test environment for each method."""
        self.stored = OrderedDict({'year': np.full(shape=3, fill_value=2001),
                                   'month': np.full(shape=3, fill_value=2),
                                   'day': np.ones(shape=3, dtype=np.int64),
                                   'hour': np.zeros(shape=3, dtype=np.int64),
                                   'minute': np.zeros(shape=3, dtype=np.int64),
                                   'second': np.arange(0, 3, 1),
                                   'version': np.arange(0, 3, 1),
                                   'revision': np.arange(3, 0, -1),
                                   'cycle': np.array([1, 3, 2])})
        self.format_str = "_".join(["test", "{year:04d}", "{month:02d}",
                                    "{day:02d}", "{hour:02d}", "{minute:02d}",
                                    "{second:02d}", "v{version:02d}",
                                    "r{revision:02d}", "c{cycle:02d}.cdf"])

        return

    def teardown_method(self):
        """Clean up the unit test environment for each method."""

        del self.stored, self.format_str
        return

    def complete_stored(self):
        """Add the 'files' and 'format_str' kwargs to the `stored` dict."""

        file_list = []
        for ind in range(len(self.stored['year'])):
            ind_dict = {skey: self.stored[skey][ind]
                        for skey in self.stored.keys()}
            file_list.append(self.format_str.format(**ind_dict))

        self.stored['files'] = file_list
        self.stored['format_str'] = self.format_str
        return

    @pytest.mark.parametrize("year_break", [0, 50])
    def test_two_digit_years(self, year_break):
        """Test the results of using different year breaks for YY formats."""
        # Complete the ordered dict of file information
        self.stored['year'] -= 2000
        self.format_str = self.format_str.replace('year:04', 'year:02')
        self.complete_stored()

        # Get the file series
        series = futils.process_parsed_filenames(
            self.stored, two_digit_year_break=year_break)

        # Test the series year
        test_year = series.index.max().year
        century = 1900 if year_break == 0 else 2000
        assert test_year - century < 100, "year break caused wrong century"

        # Test that the series length is correct and all filenames are unique
        assert series.shape == self.stored['year'].shape
        assert np.unique(series.values).shape == self.stored['year'].shape
        return

    def test_version_selection(self):
        """Test version selection dominates when time is the same."""
        # Complete the ordered dict of file information
        self.stored['second'] = np.zeros(shape=self.stored['year'].shape,
                                         dtype=np.int64)
        self.complete_stored()

        # Get the file series
        series = futils.process_parsed_filenames(self.stored)

        # Ensure there is only one file and that it has the highest version
        ver_num = "v{:02d}".format(self.stored['version'].max())
        assert series.shape == (1, )
        assert series.values[0].find(ver_num) > 0
        return

    def test_revision_selection(self):
        """Test revision selection dominates after time and version."""
        # Complete the ordered dict of file information
        self.stored['second'] = np.zeros(shape=self.stored['year'].shape,
                                         dtype=np.int64)
        self.stored['version'] = np.zeros(shape=self.stored['year'].shape,
                                          dtype=np.int64)
        self.complete_stored()

        # Get the file series
        series = futils.process_parsed_filenames(self.stored)

        # Ensure there is only one file and that it has the highest version
        rev_num = "r{:02d}".format(self.stored['revision'].max())
        assert series.shape == (1, )
        assert series.values[0].find(rev_num) > 0
        return

    def test_cycle_selection(self):
        """Test cycle selection dominates after time, version, and revision."""
        # Complete the ordered dict of file information
        self.stored['second'] = np.zeros(shape=self.stored['year'].shape,
                                         dtype=np.int64)
        self.stored['version'] = np.zeros(shape=self.stored['year'].shape,
                                          dtype=np.int64)
        self.stored['revision'] = np.zeros(shape=self.stored['year'].shape,
                                           dtype=np.int64)
        self.complete_stored()

        # Get the file series
        series = futils.process_parsed_filenames(self.stored)

        # Ensure there is only one file and that it has the highest version
        cyc_num = "c{:02d}".format(self.stored['cycle'].max())
        assert series.shape == (1, )
        assert series.values[0].find(cyc_num) > 0
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
        self.insts.append(pysat.Instrument('ace', 'sis', tag='historic'))
        test_dates = pysatSpaceWeather.instruments.ace_sis._test_dates
        self.insts_dates.append([test_dates['']['historic']] * 2)
        self.insts_kwargs.append({})

        # Data with date mangling, regular F10.7 data, stored monthly
        self.insts.append(pysat.Instrument('sw', 'f107', tag='historic'))
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
                                     inst_id=inst.inst_id)

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
            update_files=True)

        # Create instrument directories in tempdir
        pysat.utils.files.check_and_make_path(self.testInst.files.data_path)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        pysat.params['data_dirs'] = self.data_paths
        self.tempdir.cleanup()
        del self.testInst, self.out, self.tempdir, self.start, self.stop
        return

    @pytest.mark.skipif(os.environ.get('CI') != 'true', reason="CI test only")
    def test_updating_directories_no_registration(self, capsys):
        """Test directory structure update method without registered insts."""
        # Convert directories to simpler platform structure, to get output
        templ = '{platform}'
        futils.update_data_directory_structure(new_template=templ,
                                               full_breakdown=True)

        # Capture printouts and test the results
        captured = capsys.readouterr()
        captxt = captured.out
        assert captxt.find("No registered instruments detected.") >= 0, \
            "Expected output not captured in STDOUT: {:}".format(captxt)
        return

    def test_search_local_system_formatted_filename(self):
        """Test `search_local_system_formatted_filename` success."""
        # Create a temporary file with a unique, searchable name
        prefix = "test_me"
        suffix = "tstfile"
        searchstr = "*".join([prefix, suffix])
        with tempfile.NamedTemporaryFile(dir=self.testInst.files.data_path,
                                         prefix=prefix, suffix=suffix):
            files = futils.search_local_system_formatted_filename(
                self.testInst.files.data_path, searchstr)

        assert len(files) == 1, "unexpected number of files in search results"
        assert files[0].find(
            prefix) >= 0, "unexpected file prefix in search results"
        assert files[0].find(
            suffix) > 0, "unexpected file extension in search results"
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

    @pytest.mark.parametrize("use_cwd", [True, False])
    def test_check_and_make_path_exists(self, use_cwd):
        """Test successful pass at creating existing directory.

        Parameters
        ----------
        use_cwd : bool
            Use current working directory or a temporary directory

        """
        if use_cwd:
            dir_name = ""
        else:
            # Create a temporary directory
            tempdir = tempfile.TemporaryDirectory()
            dir_name = tempdir.name
            assert os.path.isdir(tempdir.name)

        # Assert check_and_make_path does not re-create the directory
        assert not pysat.utils.files.check_and_make_path(dir_name)

        if not use_cwd:
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
