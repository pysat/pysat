#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
""" Utilities to perform common evaluations
"""

import numpy as np


def assert_list_contains(small_list, big_list):
    """ Assert all elements of one list exist within the other list

    Parameters
    ----------
    small_list : list
        List whose values must all be present within big_list
    big_list : list
        List that must contain all the values in small_list

    Raises
    ------
    AssertionError
        If a small_list value is missing from big_list

    """

    for value in small_list:
        assert value in big_list, "{:} not in {:}".format(value, big_list)

    return


def assert_lists_equal(list1, list2):
    """Assert that the lists contain the same elements

    Parameters
    ----------
    list1 : list
        Input list one
    list2 : list
        Input list two

    Raises
    ------
    AssertionError
        If a list1 value is missing from list2 or list lengths are unequal

    Note
    ----
    This test does not require that the lists have the same elements in the
    same order, and so is also a good test for keys.

    """

    assert len(list1) == len(list2)
    assert_list_contains(list1, list2)

    return


def nan_equal(value1, value2):
    """ Determine if values are equal or are both NaN

    Parameters
    ----------
    value1 : scalar-like
        Value of any type that can be compared without iterating
    value2 : scalar-like
        Another value of any type that can be compared without iterating

    Returns
    -------
    is_equal : bool
        True if both values are equal or NaN, False if they are not

    """

    is_equal = (value1 == value2)

    if not is_equal:
        try:
            if np.isnan(value1) and np.isnan(value2):
                is_equal = True
        except TypeError:
            # One or both of value1 and value2 cannot be evaluated by np.isnan
            # and so have been correctly identified as unequal
            pass

    return is_equal
