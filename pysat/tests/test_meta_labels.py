#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat MetaLabels object."""

import datetime as dt
import logging
import numpy as np
import pytest

import pysat
from pysat.utils import testing


class TestMetaLabels(object):
    """Unit and integration tests for the MetaLabels class."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        testInst = pysat.Instrument('pysat', 'testing')
        self.meta_labels = testInst.meta.labels
        self.meta = pysat.Meta()

        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        del self.meta, self.meta_labels
        return

    # -----------------------
    # Test the Error messages

    def test_default_label_value_raises_error(self):
        """Test `MetaLabels.default_values_from_attr` errors with bad attr."""

        testing.eval_bad_input(self.meta_labels.default_values_from_attr,
                               ValueError, "unknown label attribute",
                               ['not_an_attr'])
        return

    @pytest.mark.parametrize("iter_type", [list, dict, set, tuple, np.ndarray])
    def test_set_bad_type(self, iter_type):
        """Test MetaLabels type evaluations does not allow iterables.

        Parameters
        ----------
        iter_type : type
            Different iterable types

        """

        testing.eval_bad_input(pysat.MetaLabels, TypeError,
                               "iterable types like",
                               input_kwargs={'value_range':
                                             ('val_range', iter_type)})

        return

    @pytest.mark.parametrize("iter_type", [list, dict, set, tuple, np.ndarray])
    def test_update_bad_type(self, iter_type):
        """Test MetaLabels type evaluations does not allow iterables.

        Parameters
        ----------
        iter_type : type
            Different iterable types

        """

        testing.eval_bad_input(self.meta_labels.update, TypeError,
                               "iterable types like", input_args=[
                                   "value_range", 'val_range', iter_type])
        return

    # -------------------------
    # Test the logging messages

    @pytest.mark.parametrize("in_val", [1., 1, {}, None, []])
    def test_default_value_from_type_unexpected_input(self, in_val, caplog):
        """Test `MetaLabels.default_values_from_type` with unexpected input.

        Parameters
        ----------
        in_val : any
            The type of `in_val`, rather than the value, drives this test

        """

        with caplog.at_level(logging.INFO, logger='pysat'):
            self.meta_labels.default_values_from_type(in_val)

            # Test for expected string
            captured = caplog.text
            test_str = 'No type match found for '
            assert captured.find(test_str) >= 0

        return

    # ---------------------------
    # Test the class magic methods

    def test_repr(self):
        """Test the `MetaLabels.__repr__` method."""

        out = self.meta_labels.__repr__()
        assert isinstance(out, str)
        assert out.find('pysat.MetaLabels(') >= 0
        return

    # -----------------------------
    # Test the class hidden methods

    @pytest.mark.parametrize("val_type", [int, float, type(None), str, bytes,
                                          bool, np.float32, np.float64,
                                          np.int32, np.int64, np.datetime64,
                                          dt.datetime, dt.timedelta])
    def test_eval_label_type_true(self, val_type):
        """Test successful ID of an allowable meta data type.

        Parameters
        ----------
        val_type : type
            Scalar data type

        """

        assert self.meta_labels._eval_label_type(val_type)
        return

    @pytest.mark.parametrize("val_type", [list, dict, set, tuple, np.ndarray])
    def test_eval_label_type_false(self, val_type):
        """Test successful ID of an allowable meta data type.

        Parameters
        ----------
        val_type : type
            Iterable data type

        """

        assert not self.meta_labels._eval_label_type(val_type)
        return

    # -----------------------------
    # Test the class public methods

    @pytest.mark.parametrize("in_val",
                             [float, np.float16, np.float32, np.float64])
    def test_default_value_from_type_float_inputs(self, in_val):
        """Test `MetaLabels.default_values_from_type` with float inputs.

        Parameters
        ----------
        in_val : type
            A sub-type within general floating point numbers

        """

        out = self.meta.labels.default_values_from_type(in_val)
        assert np.isnan(out)

        return

    @pytest.mark.parametrize("in_val, comp_val",
                             [(int, -1), (np.int8, -1), (np.int16, -1),
                              (np.int32, -1), (np.int64, -1), (str, '')])
    def test_default_value_from_type_int_inputs(self, in_val, comp_val):
        """Test `MetaLabels.default_values_from_type` with int inputs.

        Parameters
        ----------
        in_val :  type
            Type of data
        comp_val : any
            Target value for internal test

        """

        out = self.meta.labels.default_values_from_type(in_val)
        assert out == comp_val

        return

    def test_update(self):
        """Test successful update of MetaLabels."""
        self.meta_labels.update('new_label', 'new_name', int)

        assert hasattr(self.meta_labels, 'new_label')
        assert self.meta_labels.new_label == 'new_name'
        assert self.meta_labels.label_type['new_label'] == int
        return

    # ----------------------------------------
    # Test the integration with the Meta class

    def test_change_case_of_meta_labels(self):
        """Test changing case of meta labels after initialization."""

        self.meta_labels = {'units': ('units', str), 'name': ('long_name', str)}
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta.labels.units = 'Units'
        self.meta.labels.name = 'Long_Name'
        assert (self.meta['new'].Units == 'hey')
        assert (self.meta['new'].Long_Name == 'boo')
        assert (self.meta['new2'].Units == 'hey2')
        assert (self.meta['new2'].Long_Name == 'boo2')
        return

    def test_case_change_of_meta_labels_w_ho(self):
        """Test change case of meta labels after initialization with HO data."""

        # Set the initial labels
        self.meta_labels = {'units': ('units', str), 'name': ('long_Name', str)}
        self.meta = pysat.Meta(labels=self.meta_labels)
        meta2 = pysat.Meta(labels=self.meta_labels)

        # Set meta data values
        meta2['new21'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = meta2

        # Change the label name
        self.meta.labels.units = 'Units'
        self.meta.labels.name = 'Long_Name'

        # Evaluate the results in the main data
        assert (self.meta['new'].Units == 'hey')
        assert (self.meta['new'].Long_Name == 'boo')

        # Evaluate the results in the higher order data
        assert (self.meta['new2'].children['new21'].Units == 'hey2')
        assert (self.meta['new2'].children['new21'].Long_Name == 'boo2')
        return
