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
"""Unit and Integration Tests for each instrument module.

Note
----
Imports test methods from pysat.tests.instrument_test_class

"""

import datetime as dt
import numpy as np
import pandas as pds

import pytest

import pysat
import pysat.tests.classes.cls_instrument_library as cls_inst_lib
from pysat.tests.classes.cls_instrument_library import InstLibTests

# Optional code to pass through user and password info to test instruments
# dict, keyed by pysat instrument, with a list of usernames and passwords
user_info = {'pysat_testing': {'user': 'pysat_testing',
                               'password': 'pysat.developers@gmail.com'}}

# Initialize tests for sources in pysat.instruments in the same way data sources
# outside of pysat would be tested
instruments = InstLibTests.initialize_test_package(InstLibTests,
                                                   inst_loc=pysat.instruments,
                                                   user_info=user_info)


class TestInstruments(InstLibTests):
    """Main class for instrument tests.

    Note
    ----
    All standard tests, setup, and teardown inherited from the core pysat
    instrument test class.

    """

    # Custom package unit tests can be added here

    # Custom Integration Tests added to all test instruments in core package
    @pytest.mark.parametrize("inst_dict", instruments['download'])
    @pytest.mark.parametrize("kwarg,output", [(None, 0.0),
                                              (dt.timedelta(hours=1), 3600.0)])
    def test_inst_start_time(self, inst_dict, kwarg, output):
        """Test operation of start_time keyword, including default behavior.

        Parameters
        ----------
        inst_dict : dict
            One of the dictionaries returned from
            `InstLibTests.initialize_test_package` with instruments to test
        kwarg : dt.timedelta or NoneType
            Passed to `pysat.Instrument` as value for `start_time` keyword
        output : float
            Expected value for the first loaded value in variable `uts`

        """

        _, date = cls_inst_lib.initialize_test_inst_and_date(inst_dict)
        if kwarg:
            self.test_inst = pysat.Instrument(
                inst_module=inst_dict['inst_module'], start_time=kwarg)
        else:
            self.test_inst = pysat.Instrument(
                inst_module=inst_dict['inst_module'])

        self.test_inst.load(date=date)

        assert self.test_inst[0, 'uts'] == output
        return

    @pytest.mark.parametrize("inst_dict", instruments['download'])
    def test_inst_num_samples(self, inst_dict):
        """Test operation of num_samples keyword.

        Parameters
        ----------
        inst_dict : dict
            One of the dictionaries returned from
            `InstLibTests.initialize_test_package` with instruments to test

        """

        # Number of samples needs to be <96 because freq is not settable.
        # Different test instruments have different default number of points.
        num = 10
        _, date = cls_inst_lib.initialize_test_inst_and_date(inst_dict)
        self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'],
                                          num_samples=num)
        self.test_inst.load(date=date)

        assert len(self.test_inst['uts']) == num
        return

    @pytest.mark.parametrize("inst_dict", instruments['download'])
    def test_inst_file_date_range(self, inst_dict):
        """Test operation of file_date_range keyword.

        Parameters
        ----------
        inst_dict : dict
            One of the dictionaries returned from
            `InstLibTests.initialize_test_package` with instruments to test

        """

        file_date_range = pds.date_range(dt.datetime(2021, 1, 1),
                                         dt.datetime(2021, 12, 31))
        _, date = cls_inst_lib.initialize_test_inst_and_date(inst_dict)
        self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'],
                                          file_date_range=file_date_range,
                                          update_files=True)
        file_list = self.test_inst.files.files

        assert all(file_date_range == file_list.index)
        return

    @pytest.mark.parametrize("inst_dict", instruments['download'])
    def test_inst_max_latitude(self, inst_dict):
        """Test operation of max_latitude keyword.

        Parameters
        ----------
        inst_dict : dict
            One of the dictionaries returned from
            `InstLibTests.initialize_test_package` with instruments to test

        """

        _, date = cls_inst_lib.initialize_test_inst_and_date(inst_dict)
        self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'])
        if self.test_inst.name != 'testmodel':
            self.test_inst.load(date=date, max_latitude=10.)
            assert np.all(np.abs(self.test_inst['latitude']) <= 10.)
        else:
            # Skipping testmodel Instrument
            pytest.skip("kwarg not implemented in testmodel")

        return

    @pytest.mark.second
    @pytest.mark.parametrize("clean_level", ['clean', 'dusty', 'dirty'])
    @pytest.mark.parametrize("change", [True, False])
    @pytest.mark.parametrize('warn_type', ['logger', 'warning', 'error',
                                           'mult'])
    @pytest.mark.parametrize("inst_dict", instruments['download'])
    def test_clean_with_warnings(self, clean_level, change, warn_type,
                                 inst_dict, caplog):
        """Run `test_clean_warn` with different warning behaviours.

        Parameters
        ----------
        clean_level : str
            Cleanliness level for loaded instrument data; must run the clean
            routine (not include 'none').
        change : bool
            Specify whether or not clean level should change.
        warn_type : str
            Desired type of warning or error to be raised.
        inst_dict : dict
            One of the dictionaries returned from
            `InstLibTests.initialize_test_package` with instruments to test.

        """
        # Set the default values
        warn_level = {'logger': 'WARN', 'warning': UserWarning,
                      'error': ValueError}
        warn_msg = 'Default warning message'
        if change:
            final_level = 'none' if clean_level == 'clean' else 'clean'
        else:
            final_level = clean_level

        # Construct the expected warnings
        if warn_type == 'mult':
            # Note that we cannot test errors along with other warnings
            # TODO(#1184) test for both warnings and errors
            inst_dict['inst_module']._clean_warn = {
                inst_dict['inst_id']: {inst_dict['tag']: {clean_level: [
                    ('warning', warn_level['warning'], warn_msg, final_level),
                    ('logger', warn_level['logger'], warn_msg, final_level)]}}}
        else:
            inst_dict['inst_module']._clean_warn = {
                inst_dict['inst_id']: {inst_dict['tag']: {clean_level: [
                    (warn_type, warn_level[warn_type], warn_msg,
                     final_level)]}}}

        # Set the additional Instrument kwargs
        if 'kwargs' in inst_dict.keys():
            # Ensure the test instrument cleaning kwarg is reset
            inst_dict['kwargs']['test_clean_kwarg'] = {'change': final_level}
        else:
            inst_dict['kwargs'] = {'test_clean_kwarg': {'change': final_level}}

        if warn_type == 'mult':
            inst_dict['kwargs']['test_clean_kwarg']['logger'] = warn_msg
            inst_dict['kwargs']['test_clean_kwarg']['warning'] = warn_msg
        else:
            inst_dict['kwargs']['test_clean_kwarg'][warn_type] = warn_msg

        # Run the test
        self.test_clean_warn(clean_level, inst_dict, caplog)

        return
