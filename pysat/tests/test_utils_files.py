import datetime as dt
from importlib import reload
import numpy as np
import os
import tempfile

import pysat
from pysat.utils import files as futils
from pysat.tests.ci_test_class import CICleanSetup


class TestBasics():

    temporary_file_list = False

    def setup(self):
        """Runs before every method to create a clean testing setup."""

    def teardown(self):
        """Runs after every method to clean up previous testing."""

    def test_parse_delimited_filename(self):
        """Check ability to parse list of delimited files"""
        # Note: Can be removed if future instrument that uses delimited
        # filenames is added to routine end-to-end testing
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


class TestFileDirectoryTranslations(CICleanSetup):

    def setup(self):
        """Runs before every method to create a clean testing setup."""

        # Module is only required for testing installations on CI servers
        import pysatSpaceWeather

        # Create clean environment on the CI server
        CICleanSetup.setup(self)
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
            inst.download(start=dates[0], stop=dates[1], **kwargs)

    def teardown(self):
        """Runs after every method to clean up previous testing."""

        # Clean environment
        CICleanSetup.teardown(self)

        self.tempdir.cleanup()

    def test_updating_directories(self, capsys):
        """Test directory structure update method"""

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
