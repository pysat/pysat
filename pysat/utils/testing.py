#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Utilities to perform common evaluations."""

import numpy as np


def assert_list_contains(small_list, big_list, test_nan=False, test_case=True):
    """Assert all elements of one list exist within the other list.

    Parameters
    ----------
    small_list : list
        List whose values must all be present within big_list
    big_list : list
        List that must contain all the values in small_list
    test_nan : bool
        Test the lists for the presence of NaN values
    test_case : bool
        Requires strings to be the same case when testing

    Raises
    ------
    AssertionError
        If a small_list value is missing from big_list

    """
    if test_nan:
        big_num_nan = np.isnan(big_list).sum()
        small_num_nan = 0
    elif not test_case:
        big_lower = [value.lower() for value in big_list]

    # Test the presence of non-NaN values from `small_list` in `big_list` and
    # determine the number of NaN values in `small_list`
    for value in small_list:
        if test_nan and np.isnan(value):
            small_num_nan += 1
        elif test_case:
            assert value in big_list, "{:} not in {:}".format(value.__repr__(),
                                                              big_list)
        else:
            assert value.lower() in big_lower, "{:} not in {:}".format(
                value.lower(), big_lower)

    if test_nan:
        # Ensure `small_list` does not have more NaNs than `big_list`
        assert small_num_nan <= big_num_nan
    return


def assert_lists_equal(list1, list2, test_nan=False, test_case=True):
    """Assert that the lists contain the same elements.

    Parameters
    ----------
    list1 : list
        Input list one
    list2 : list
        Input list two
    test_nan : bool
        Test the lists for the presence of NaN values
    test_case : bool
        Requires strings to be the same case when testing

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
    assert_list_contains(list1, list2, test_nan=test_nan, test_case=test_case)

    return


def assert_hasattr(obj, attr_name):
    """Provide useful info if object is missing a required attribute.

    Parameters
    ----------
    obj : object
        Name of object to check
    attr_name : str
        Name of required attribute that must be present in `obj`

    Raises
    ------
    AssertionError
        If `obj` does not have attribute `attr_name`

    """

    estr = "Object {:} missing attribute {:}".format(obj.__repr__(),
                                                     attr_name)
    assert hasattr(obj, attr_name), estr
    return


def assert_isinstance(obj, obj_type):
    """Provide useful info if object is the wrong type.

    Parameters
    ----------
    obj : object
        Name of object to check
    obj_type : str
        Required type of object

    Raises
    ------
    AssertionError
        If `obj` is not type `obj_type`

    """

    estr = "Object {:} is type {:}, but should be type {:}".format(
        obj.__repr__(), type(obj), obj_type)
    assert isinstance(obj, obj_type), estr
    return


def nan_equal(value1, value2):
    """Determine if values are equal or are both NaN.

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


def eval_warnings(warns, check_msgs, warn_type=DeprecationWarning):
    """Evaluate warnings by category and message.

    Parameters
    ----------
    warns : list
        List of warnings.WarningMessage objects
    check_msgs : list
        List of strings containing the expected warning messages
    warn_type : type
        Type for the warning messages (default=DeprecationWarning)

    Raises
    ------
    AssertionError
        If warning category doesn't match type or an expected message is missing

    """

    # Initialize the output
    found_msgs = [False for msg in check_msgs]

    # Test the warning messages, ensuring each attribute is present
    for iwar in warns:
        for i, msg in enumerate(check_msgs):
            if str(iwar.message).find(msg) >= 0:
                assert iwar.category == warn_type, \
                    "bad warning type for message: {:}".format(msg)
                found_msgs[i] = True

    assert np.all(found_msgs), "did not find {:d} expected {:}".format(
        len(found_msgs) - np.sum(found_msgs), repr(warn_type))

    return


def eval_bad_input(func, error, err_msg, input_args=None, input_kwargs=None):
    """Evaluate bad function or method input.

    Parameters
    ----------
    func : function, method, or class
        Function, class, or method to be evaluated
    error : class
        Expected error or exception
    err_msg : str
        Expected error message
    input_args : list or NoneType
        Input arguments or None for no input arguments (default=None)
    input_kwargs : dict or NoneType
        Input keyword arguments or None for no input kwargs (default=None)

    Raises
    ------
    AssertionError
        If unexpected error message is returned
    Exception
        If error or exception of unexpected type is returned, it is raised

    """

    # Ensure there are appropriate input lists and dicts
    if input_args is None:
        input_args = []

    if input_kwargs is None:
        input_kwargs = {}

    # Call the function, catching only the expected error type
    try:
        func(*input_args, **input_kwargs)
    except error as err:
        # Evaluate the error message
        assert str(err).find(err_msg) >= 0, \
            "unexpected error message ('{:}' not in '{:}')".format(err_msg,
                                                                   str(err))

    return
