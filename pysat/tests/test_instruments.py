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
import pysat.tests.classes.cls_instrument_library as cls_inst_lib
from pysat.tests.classes.cls_instrument_library import InstLibTests
import pysat.tests.instrument_test_class as itc
from pysat.utils import testing

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
                inst_module=inst_dict['inst_module'], start_time=kwarg,
                use_header=True)
        else:
            self.test_inst = pysat.Instrument(
                inst_module=inst_dict['inst_module'], use_header=True)

        self.test_inst.load(date=date)

        assert self.test_inst['uts'][0] == output
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
                                          num_samples=num, use_header=True)
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
                                          update_files=True, use_header=True)
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
        self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'],
                                          use_header=True)
        if self.test_inst.name != 'testmodel':
            self.test_inst.load(date=date, max_latitude=10.)
            assert np.all(np.abs(self.test_inst['latitude']) <= 10.)
        else:
            # Skipping testmodel Instrument
            pytest.skip("kwarg not implemented in testmodel")

        return


class TestDeprecation(object):
    """Unit test for deprecation warnings."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        return

    def test_subclass_inst_test_class(self):
        """Check that subclass of old instrument library tests is deprecated."""

        with warnings.catch_warnings(record=True) as war:

            class OldClass(itc.InstTestClass):
                """Dummy subclass."""

                pass

        self.warn_msgs = ["`InstTestClass` has been deprecated",
                          "`test_load` now uses `@pytest.mark.load_options`"]
        self.warn_msgs = np.array(self.warn_msgs)

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        testing.eval_warnings(war, self.warn_msgs)
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
        testing.eval_warnings(war, self.warn_msgs)
        return

    def test_old_pytest_mark_presence(self):
        """Test that pytest mark is backwards compatible."""

        n_args = len(InstLibTests.test_load.pytestmark)
        mark_names = [InstLibTests.test_load.pytestmark[j].name
                      for j in range(0, n_args)]

        assert "download" in mark_names

    @pytest.mark.parametrize("inst_module", ['pysat_testing2d',
                                             'pysat_testing_xarray',
                                             'pysat_testing2d_xarray'])
    def test_deprecated_instruments(self, inst_module):
        """Check that instantiating old instruments raises a DeprecationWarning.

        Parameters
        ----------
        inst_module : str
            name of deprecated module.

        """

        with warnings.catch_warnings(record=True) as war:
            pysat.Instrument(inst_module=getattr(pysat.instruments,
                                                 inst_module),
                             use_header=True)

        warn_msgs = [" ".join(["The instrument module",
                               "`{:}`".format(inst_module),
                               "has been deprecated and will be removed",
                               "in 3.2.0+."])]

        # Ensure the minimum number of warnings were raised.
        assert len(war) >= len(warn_msgs)

        # Test the warning messages, ensuring each attribute is present.
        testing.eval_warnings(war, warn_msgs)
        return
