#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat utility testing routines."""

import numpy as np
import os
import pytest
import tempfile
import warnings

from pysat.utils import testing


class TestTestingUtils(object):
    """Unit tests for `pysat.utils.testing` functions."""

    def setup_method(self):
        """Create a clean test environment."""
        warnings.simplefilter("always")
        return

    def teardown_method(self):
        """Clean up the test environment."""
        warnings.resetwarnings()
        return

    @pytest.mark.parametrize("slist, blist",
                             [([1, 2.0], [1, 2.0, 3]),
                              (['one', 'two'], ['three', 'two', 'one']),
                              ([None, False], [True, False, None])])
    def test_assert_list_contains_good(self, slist, blist):
        """Test the successful evaluation of overlapping list contents.

        Parameters
        ----------
        slist : list
            Input list for testing
        blist : list
            Second input list for testing

        """

        testing.assert_list_contains(slist, blist)
        return

    @pytest.mark.parametrize("slist, blist",
                             [([1, 4.0], [1, 2.0, 3]),
                              (['one', 'two'], ['three', 'one']),
                              ([None, False], [True, False, "None"])])
    def test_assert_list_contains_bad(self, slist, blist):
        """Test raises AssertionError for lists where elements are unique.

        Parameters
        ----------
        slist : list
            Input list for testing
        blist : list
            Second input list for testing

        """

        with pytest.raises(AssertionError) as aerr:
            testing.assert_list_contains(slist, blist)

        assert str(aerr).find('not in')
        return

    @pytest.mark.parametrize("slist, blist, kwargs",
                             [([1, 2.0], [1, 2.0], {}),
                              (['one', 'two'], ['two', 'one'], {}),
                              ([None, True, False], [True, False, None], {}),
                              (['one', 'two'], ['Two', 'ONE'],
                               {"test_case": False}),
                              ([np.nan, 1], [1, np.nan], {"test_nan": True})])
    def test_assert_list_equal_good(self, slist, blist, kwargs):
        """Test the evaluation of lists with unordered but identical values.

        Parameters
        ----------
        slist : list
            Input list for testing
        blist : list
            Second input list for testing
        kwargs : dict
            Dictionary of keyword arguments and values passed to
            `testing.assert_lists_equal`
        """

        testing.assert_lists_equal(slist, blist, **kwargs)
        return

    @pytest.mark.parametrize("slist, blist",
                             [([1, 4.0], [1, 2.0, 3]),
                              ([1, np.nan], [1, 2.0]),
                              (['one', 'two'], ['three', 'one']),
                              (['one', 'two'], ['One', 'TWO']),
                              ([None, False], [True, False, "None"])])
    def test_assert_list_equal_bad(self, slist, blist):
        """Test the evaluation of overlapping list contents.

        Parameters
        ----------
        slist : list
            Input list for testing
        blist : list
            Second input list for testing

        """

        with pytest.raises(AssertionError):
            testing.assert_lists_equal(slist, blist)
        return

    @pytest.mark.parametrize("val1, val2", [(0.0, 0), (np.nan, np.nan),
                                            ('one', 'one'), (None, None),
                                            (True, 1), (False, 0),
                                            (np.inf, np.inf), (10, 10)])
    def test_nan_equal_good(self, val1, val2):
        """Test successful evaluation of equivalent values.

        Parameters
        ----------
        val1 : any
            First item for equivalence comparison
        val2 : any
            Second item for equivalence comparison

        """

        assert testing.nan_equal(val1, val2)
        return

    @pytest.mark.parametrize("val1, val2", [(0.0, 1.0), (np.nan, np.inf),
                                            ('one', 'One'), (None, False),
                                            (True, 'true'), (False, 'F'),
                                            (np.inf, -np.inf), (1, 11)])
    def test_nan_equal_bad(self, val1, val2):
        """Test successful evaluation of un-equivalent values.

        Parameters
        ----------
        val1 : any
            First item for equivalence comparison
        val2 : any
            Second item for equivalence comparison

        """

        assert not testing.nan_equal(val1, val2)
        return

    @pytest.mark.parametrize("warn_type", [
        UserWarning, DeprecationWarning, SyntaxWarning, RuntimeWarning,
        FutureWarning, PendingDeprecationWarning, ImportWarning,
        UnicodeWarning, BytesWarning, ResourceWarning])
    def test_good_eval_warnings(self, warn_type):
        """Test warning evaluation function success.

        Parameters
        ----------
        warn_type : Warning
            Warning class to be raised

        """
        warn_msg = 'test warning'

        # Raise the desired warning
        with warnings.catch_warnings(record=True) as war:
            warnings.warn(warn_msg, warn_type)

        # Evaluate the warning output
        testing.eval_warnings(war, [warn_msg], warn_type)
        return

    @pytest.mark.parametrize("warn_type", [
        UserWarning, DeprecationWarning, SyntaxWarning, RuntimeWarning,
        FutureWarning, PendingDeprecationWarning, ImportWarning,
        UnicodeWarning, BytesWarning, ResourceWarning])
    def test_eval_warnings_bad_type(self, warn_type):
        """Test warning evaluation function failure for mismatched type.

        Parameters
        ----------
        warn_type : Warning
            Warning class to be raised

        """
        warn_msg = 'test warning'
        bad_type = UserWarning if warn_type != UserWarning else BytesWarning

        # Raise the desired warning
        with warnings.catch_warnings(record=True) as war:
            warnings.warn(warn_msg, warn_type)

        # Catch and evaluate the expected error
        with pytest.raises(AssertionError) as aerr:
            testing.eval_warnings(war, [warn_msg], bad_type)

        assert str(aerr).find('bad warning type for message') >= 0
        return

    @pytest.mark.parametrize("warn_type", [
        UserWarning, DeprecationWarning, SyntaxWarning, RuntimeWarning,
        FutureWarning, PendingDeprecationWarning, ImportWarning,
        UnicodeWarning, BytesWarning, ResourceWarning])
    def test_eval_warnings_bad_msg(self, warn_type):
        """Test warning evaluation function failure for mismatched message.

        Parameters
        ----------
        warn_type : Warning
            Warning class to be raised

        """
        warn_msg = 'test warning'
        bad_msg = 'not correct'

        # Raise the desired warning
        with warnings.catch_warnings(record=True) as war:
            warnings.warn(warn_msg, warn_type)

        # Catch and evaluate the expected error
        with pytest.raises(AssertionError) as aerr:
            testing.eval_warnings(war, [bad_msg], warn_type)

        assert str(aerr).find('did not find') >= 0
        return

    @pytest.mark.parametrize("error", [
        Exception, AssertionError, AttributeError, EOFError, FloatingPointError,
        GeneratorExit, ImportError, IndexError, KeyError, KeyboardInterrupt,
        MemoryError, NameError, NotImplementedError, OSError, OverflowError,
        RecursionError, ReferenceError, RuntimeError, StopIteration,
        SyntaxError, SystemError, SystemExit, TypeError, UnboundLocalError,
        ZeroDivisionError, EnvironmentError])
    def test_eval_bad_input_success(self, error):
        """Test error evaluation function success for test function.

        Parameters
        ----------
        error : class
            Expected error or exception

        """

        def test_func():
            raise error("test func")

        testing.eval_bad_input(test_func, error, "test func")
        return

    @pytest.mark.parametrize("error", [
        AssertionError, AttributeError, EOFError, FloatingPointError,
        GeneratorExit, ImportError, IndexError, KeyError, KeyboardInterrupt,
        MemoryError, NameError, NotImplementedError, OSError, OverflowError,
        RecursionError, ReferenceError, RuntimeError, StopIteration,
        SyntaxError, SystemError, SystemExit, TypeError, UnboundLocalError,
        ZeroDivisionError, EnvironmentError])
    def test_eval_bad_input_type_failure(self, error):
        """Test error evaluation function type failure for test function.

        Parameters
        ----------
        error : class
            Not the expected error or exception

        """

        def test_func():
            raise ValueError("test func")

        with pytest.raises(ValueError) as verr:
            testing.eval_bad_input(test_func, error, "test func")

        assert str(verr).find("test func") >= 0
        return

    def test_eval_bad_input_msg_failure(self):
        """Test error evaluation function message failure for test function."""

        def test_func():
            raise ValueError("test func")

        with pytest.raises(AssertionError) as aerr:
            testing.eval_bad_input(test_func, ValueError, "testing function")

        assert str(aerr).find("unexpected error message") >= 0
        return
