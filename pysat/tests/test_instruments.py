"""Unit and Integration Tests for each instrument module.

Note
----
Imports test methods from pysat.tests.instrument_test_class

"""

import datetime as dt
import numpy as np
import pandas as pds
import warnings

import pytest

import pysat
# Make sure to import your instrument package here
# e.g.,
# import mypackage

# Need extra functions if custom tests are being added.
import pysat.tests.classes.cls_instrument_library as cls_inst_lib

# Import the test classes from pysat.
from pysat.tests.classes.cls_instrument_library import InstLibTests

# Import old classes for Deprecation tests.
import pysat.tests.instrument_test_class as itc

# Optional code to pass through user and password info to test instruments
# dict, keyed by pysat instrument, with a list of usernames and passwords
# user_info = {'platform_name': {'user': 'pysat_user',
#                                'password': 'None'}}
user_info = {'pysat_testing': {'user': 'pysat_testing',
                               'password': 'pysat.developers@gmail.com'}}

# Developers for instrument libraries should update the following line to
# point to their own subpackage location
# e.g.,
# InstLibTests.initialize_test_package(InstLibTests, inst_loc=mypackage.inst)

# If user and password info supplied, use the following instead
# InstLibTests.initialize_test_package(InstLibTests, inst_loc=mypackage.inst,
#                                       user_info=user_info)

# If custom tests need to be added to the class, the instrument lists may be
# included as an optional output.
# instruments = InstLibTests.initialize_test_package(InstLibTests,
#                                                    inst_loc=mypackage.inst)
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

    # Custom Integration Tests added to all test instruments in core package.
    @pytest.mark.parametrize("inst_dict", instruments['download'])
    @pytest.mark.parametrize("kwarg,output", [(None, 0.0),
                                              (dt.timedelta(hours=1), 3600.0)])
    def test_inst_start_time(self, inst_dict, kwarg, output):
        """Test operation of start_time keyword, including default behavior."""

        _, date = cls_inst_lib.initialize_test_inst_and_date(inst_dict)
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
        _, date = cls_inst_lib.initialize_test_inst_and_date(inst_dict)
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
        _, date = cls_inst_lib.initialize_test_inst_and_date(inst_dict)
        self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'],
                                          file_date_range=file_date_range)
        file_list = self.test_inst.files.files

        assert all(file_date_range == file_list.index)
        return


class TestDeprecation(object):
    """Unit test for deprecation warnings."""

    def setup(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        return

    def test_subclass_inst_test_class(self):
        """Check that subclass of old instrument library tests is deprecated."""

        with warnings.catch_warnings(record=True) as war:

            class OldClass(itc.InstTestClass):
                """Dummy subclass."""

                pass

        self.warn_msgs = ["`InstTestClass` has been deprecated"]
        self.warn_msgs = np.array(self.warn_msgs)

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        found_msgs = pysat.instruments.methods.testing.eval_dep_warnings(
            war, self.warn_msgs)

        for i, good in enumerate(found_msgs):
            assert good, "didn't find warning about: {:}".format(
                self.warn_msgs[i])

        return

    def test_old_initialize_inst_and_date(self):
        """Check that subclass of old instrument library tests is deprecated."""

        with warnings.catch_warnings(record=True) as war:
            try:
                itc.initialize_test_inst_and_date({})
            except KeyError:
                # empty dict produces KeyError
                pass

        self.warn_msgs = ["`initialize_test_inst_and_date` has been moved to"]
        self.warn_msgs = np.array(self.warn_msgs)

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        found_msgs = pysat.instruments.methods.testing.eval_dep_warnings(
            war, self.warn_msgs)

        for i, good in enumerate(found_msgs):
            assert good, "didn't find warning about: {:}".format(
                self.warn_msgs[i])

        return
