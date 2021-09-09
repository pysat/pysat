"""Unit and Integration Tests for each instrument module.

Note
----
Imports test methods from pysat.tests.instrument_test_class

"""

import datetime as dt
import pandas as pds

import pytest

import pysat
# Make sure to import your instrument package here
# e.g.,
# import mypackage

# Need initialize_test_inst_and_date if custom tests are being added.
from pysat.tests.instrument_test_class import initialize_test_inst_and_date
# Import the test classes from pysat
from pysat.tests.instrument_test_class import InstTestClass
from pysat.utils import generate_instrument_list


# Optional code to pass through user and password info to test instruments
# dict, keyed by pysat instrument, with a list of usernames and passwords
# user_info = {'platform_name': {'user': 'pysat_user',
#                                'password': 'None'}}
user_info = {'pysat_testing': {'user': 'pysat_testing',
                               'password': 'pysat.developers@gmail.com'}}

# Developers for instrument libraries should update the following line to
# point to their own subpackage location
# e.g.,
# InstTestClass.apply_marks_to_tests(InstTestClass, inst_loc=mypackage.inst)
# If user and password info supplied, use the following instead
# InstTestClass.apply_marks_to_tests(InstTestClass, inst_loc=mypackage.inst,
#                                    user_info=user_info)
instruments = InstTestClass.initialize_test_package(InstTestClass,
                                                    inst_loc=pysat.instruments,
                                                    user_info=user_info)


class TestInstruments(InstTestClass):
    """Main class for instrument tests.

    Note
    ----
    All standard tests, setup, and teardown inherited from the core pysat
    instrument test class.

    """

    # Custom package unit tests can be added here

    # Custom Integration Tests added to all test instruments in core package.
    @pytest.mark.parametrize("inst_dict", instruments['download'])
    @pytest.mark.parametrize("kwarg,output", [(None, 0.0),
                                              (dt.timedelta(hours=1), 3600.0)])
    def test_inst_start_time(self, inst_dict, kwarg, output):
        """Test operation of start_time keyword, including default behavior."""

        _, date = initialize_test_inst_and_date(inst_dict)
        if kwarg:
            self.test_inst = pysat.Instrument(
                inst_module=inst_dict['inst_module'], start_time=kwarg)
        else:
            self.test_inst = pysat.Instrument(
                inst_module=inst_dict['inst_module'])

        self.test_inst.load(date=date)

        assert self.test_inst['uts'][0] == output
        return

    @pytest.mark.parametrize("inst_dict", instruments['download'])
    def test_inst_num_samples(self, inst_dict):
        """Test operation of num_samples keyword."""

        # Number of samples needs to be <96 because freq is not settable.
        # Different test instruments have different default number of points.
        num = 10
        _, date = initialize_test_inst_and_date(inst_dict)
        self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'],
                                          num_samples=num)
        self.test_inst.load(date=date)

        assert len(self.test_inst['uts']) == num
        return

    @pytest.mark.parametrize("inst_dict", instruments['download'])
    def test_inst_file_date_range(self, inst_dict):
        """Test operation of file_date_range keyword."""

        file_date_range = pds.date_range(dt.datetime(2021, 1, 1),
                                         dt.datetime(2021, 12, 31))
        _, date = initialize_test_inst_and_date(inst_dict)
        self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'],
                                          file_date_range=file_date_range)
        file_list = self.test_inst.files.files

        assert all(file_date_range == file_list.index)
        return
