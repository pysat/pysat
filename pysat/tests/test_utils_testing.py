#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""
test the pysat utility testing routines
"""

import numpy as np
import pytest

from pysat.utils import testing


class TestTestingUtils():

    @pytest.mark.parametrize("slist, blist",
                             [([1, 2.0], [1, 2.0, 3]),
                              (['one', 'two'], ['three', 'two', 'one']),
                              ([None, False], [True, False, None])])
    def test_assert_list_contains_good(self, slist, blist):
        """ Test the successful evaluation of overlapping list contents
        """
        testing.assert_list_contains(slist, blist)

    @pytest.mark.parametrize("slist, blist",
                             [([1, 4.0], [1, 2.0, 3]),
                              (['one', 'two'], ['three', 'one']),
                              ([None, False], [True, False, "None"])])
    def test_assert_list_contains_bad(self, slist, blist):
        """ Test raises AssertionError for lists with elements that are unique
        """
        with pytest.raises(AssertionError) as aerr:
            testing.assert_list_contains(slist, blist)

        assert str(aerr).find('not in')

    @pytest.mark.parametrize("slist, blist",
                             [([1, 2.0], [1, 2.0]),
                              (['one', 'two'], ['two', 'one']),
                              ([None, True, False], [True, False, None])])
    def test_assert_list_equal_good(self, slist, blist):
        """ Test the evaluation of lists with unordered but identical values
        """
        testing.assert_lists_equal(slist, blist)

    @pytest.mark.parametrize("slist, blist",
                             [([1, 4.0], [1, 2.0, 3]),
                              (['one', 'two'], ['three', 'one']),
                              ([None, False], [True, False, "None"])])
    def test_assert_list_equal_bad(self, slist, blist):
        """ Test the evaluation of overlapping list contents
        """
        with pytest.raises(AssertionError):
            testing.assert_lists_equal(slist, blist)

    @pytest.mark.parametrize("val1, val2", [(0.0, 0), (np.nan, np.nan),
                                            ('one', 'one'), (None, None),
                                            (True, 1), (False, 0),
                                            (np.inf, np.inf), (10, 10)])
    def test_nan_equal_good(self, val1, val2):
        """Test successful evaluation of equivalent values
        """
        assert testing.nan_equal(val1, val2)

    @pytest.mark.parametrize("val1, val2", [(0.0, 1.0), (np.nan, np.inf),
                                            ('one', 'One'), (None, False),
                                            (True, 'true'), (False, 'F'),
                                            (np.inf, -np.inf), (1, 11)])
    def test_nan_equal_bad(self, val1, val2):
        """Test successful evaluation of un-equivalent values
        """
        assert not testing.nan_equal(val1, val2)
