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

    def setup(self):
        """Create a clean test environment."""
        warnings.simplefilter("always")
        return

    def teardown(self):
        """Clean up the test environment."""
        warnings.resetwarnings()
        return

    @pytest.mark.parametrize("slist, blist",
                             [([1, 2.0], [1, 2.0, 3]),
                              (['one', 'two'], ['three', 'two', 'one']),
                              ([None, False], [True, False, None])])
    def test_assert_list_contains_good(self, slist, blist):
        """Test the successful evaluation of overlapping list contents."""

        testing.assert_list_contains(slist, blist)
        return

    @pytest.mark.parametrize("slist, blist",
                             [([1, 4.0], [1, 2.0, 3]),
                              (['one', 'two'], ['three', 'one']),
                              ([None, False], [True, False, "None"])])
    def test_assert_list_contains_bad(self, slist, blist):
        """Test raises AssertionError for lists where elements are unique."""

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
        """Test the evaluation of lists with unordered but identical values."""

        testing.assert_lists_equal(slist, blist, **kwargs)
        return

    @pytest.mark.parametrize("slist, blist",
                             [([1, 4.0], [1, 2.0, 3]),
                              ([1, np.nan], [1, 2.0]),
                              (['one', 'two'], ['three', 'one']),
                              (['one', 'two'], ['One', 'TWO']),
                              ([None, False], [True, False, "None"])])
    def test_assert_list_equal_bad(self, slist, blist):
        """Test the evaluation of overlapping list contents."""

        with pytest.raises(AssertionError):
            testing.assert_lists_equal(slist, blist)
        return

    @pytest.mark.parametrize("val1, val2", [(0.0, 0), (np.nan, np.nan),
                                            ('one', 'one'), (None, None),
                                            (True, 1), (False, 0),
                                            (np.inf, np.inf), (10, 10)])
    def test_nan_equal_good(self, val1, val2):
        """Test successful evaluation of equivalent values."""

        assert testing.nan_equal(val1, val2)
        return

    @pytest.mark.parametrize("val1, val2", [(0.0, 1.0), (np.nan, np.inf),
                                            ('one', 'One'), (None, False),
                                            (True, 'true'), (False, 'F'),
                                            (np.inf, -np.inf), (1, 11)])
    def test_nan_equal_bad(self, val1, val2):
        """Test successful evaluation of un-equivalent values."""

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

    def test_prep_dir_exists(self):
        """Test successful pass at creating existing directory."""

        # Create a temporary directory
        tempdir = tempfile.TemporaryDirectory()
        assert os.path.isdir(tempdir.name)

        # Assert prep_dir does not re-create the directory
        assert not testing.prep_dir(tempdir.name)

        # Clean up temporary directory
        tempdir.cleanup()
        return

    def test_prep_dir_new(self):
        """Test successful pass at creating existing directory."""

        # Create a temporary directory and get its name
        tempdir = tempfile.TemporaryDirectory()
        new_dir = tempdir.name

        # Clean up temporary directory
        tempdir.cleanup()
        assert not os.path.isdir(new_dir)

        # Assert prep_dir re-creates the directory
        assert testing.prep_dir(new_dir)

        # Clean up the test directory
        os.rmdir(new_dir)
        return
