"""Unit tests for the `pysat.Instrument.index` attribute."""

import datetime as dt
from importlib import reload
import numpy as np
import warnings

import pytest

import pysat
from pysat.utils import testing


class TestIndex(object):
    """Unit tests for pandas `pysat.Instrument` index checks."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.name = 'testing'
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.ref_time, self.name
        return

    @pytest.mark.parametrize("kwargs,msg",
                             [({'non_monotonic_index': True},
                               'Loaded data is not monotonic'),
                              ({'non_unique_index': True},
                               'Loaded data is not unique')])
    def test_index_error_messages(self, kwargs, msg):
        """Ensure that a bad Instrument index will raise correct error.

        Parameters
        ----------
        kwargs : dict
            Keywords and arguments to pass through for instrument instantiation.
            Kwargs should trigger an error message when used on a test
            instrument.
        msg : str
            Excerpt of expected error message.

        """

        test_inst = pysat.Instrument(platform='pysat',
                                     name=self.name,
                                     num_samples=10,
                                     clean_level='clean',
                                     update_files=True,
                                     strict_time_flag=True,
                                     use_header=True,
                                     **kwargs)
        year, doy = pysat.utils.time.getyrdoy(self.ref_time)
        testing.eval_bad_input(test_inst.load, ValueError, msg,
                               input_args=[year, doy])
        return


class TestIndexXArray(TestIndex):
    """Unit tests for xarray `pysat.Instrument` index checks."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.name = 'ndtesting'
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.ref_time, self.name
        return


class TestDeprecation(object):
    """Unit test for deprecation warnings for index."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.warn_msgs = []
        self.war = ""
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.ref_time, self.warn_msgs, self.war
        return

    def eval_warnings(self):
        """Evaluate the number and message of the raised warnings."""

        # Ensure the minimum number of warnings were raised.
        assert len(self.war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present.
        testing.eval_warnings(self.war, self.warn_msgs)
        return

    # TODO(#1094): Remove in pysat 3.2.0, potentially with class
    @pytest.mark.parametrize('name', ['testing', 'ndtesting', 'testing_xarray',
                                      'testing2d'])
    def test_kwarg_malformed_index(self, name):
        """Test deprecation of `malformed_index` kwarg.

        Parameters
        ----------
        name : str
            name of instrument that uses the deprecated `malformed_index` kwarg.

        """

        test_inst = pysat.Instrument(platform='pysat',
                                     name=name,
                                     strict_time_flag=False,
                                     use_header=True,
                                     malformed_index=True)

        # Catch the warnings
        with warnings.catch_warnings(record=True) as self.war:
            test_inst.load(date=self.ref_time)

        self.warn_msgs = np.array([" ".join(["The kwarg malformed_index has",
                                             "been deprecated"])])

        # Evaluate the warning output
        self.eval_warnings()

        # Check that resulting index is both non-monotonic and non-unique
        assert not test_inst.index.is_monotonic_increasing
        assert not test_inst.index.is_unique
        return
