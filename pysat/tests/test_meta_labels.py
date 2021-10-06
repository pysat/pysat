#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat MetaLabels object."""

import logging
import numpy as np
import pytest

import pysat


class TestMetaLabels(object):
    """Unit and integration tests for the MetaLabels class."""

    def setup(self):
        """Set up the unit test environment for each method."""

        testInst = pysat.Instrument('pysat', 'testing')
        self.meta_labels = testInst.meta.labels
        self.meta = pysat.Meta()

        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        del self.meta, self.meta_labels
        return

    # -----------------------
    # Test the Error messages

    def test_default_label_value_raises_error(self):
        """Test `MetaLabels.default_values_from_attr` errors with bad attr."""

        with pytest.raises(ValueError) as verr:
            self.meta_labels.default_values_from_attr('not_an_attr')

        assert verr.match("unknown label attribute")
        return

    # -------------------------
    # Test the logging messages

    @pytest.mark.parametrize("in_val", [1., 1, {}, None, []])
    def test_default_value_from_type_unexpected_input(self, in_val, caplog):
        """Test `MetaLabels.default_values_from_type` with unexpected input."""

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
    # Test the class public methods

    @pytest.mark.parametrize("in_val",
                             [float, np.float16, np.float32, np.float64])
    def test_default_value_from_type_float_inputs(self, in_val):
        """Test `MetaLabels.default_values_from_type` with float inputs."""

        out = self.meta.labels.default_values_from_type(in_val)
        assert np.isnan(out)

        return

    @pytest.mark.parametrize("in_val, comp_val",
                             [(int, -1), (np.int8, -1), (np.int16, -1),
                              (np.int32, -1), (np.int64, -1), (str, '')])
    def test_default_value_from_type_int_inputs(self, in_val, comp_val):
        """Test `MetaLabels.default_values_from_type` with int inputs."""

        out = self.meta.labels.default_values_from_type(in_val)
        assert out == comp_val

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
