#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat MetaLabels object."""

import logging
import pytest

import pysat


class TestMetaLabels(object):
    """Basic unit tests for the MetaLabels class."""

    
    def setup(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing')
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.meta_labels = self.testInst.meta.labels

        self.label_dict = {'units': ('Units', str),
                           'name': ('Long_Name', str)}
        self.dval = None
        self.default_name = ['long_name']
        self.default_nan = ['fill', 'value_min', 'value_max']
        self.default_val = {'notes': '', 'units': '', 'desc': ''}
        self.frame_list = ['dummy_frame1', 'dummy_frame2']
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        del self.testInst, self.meta, self.stime, self.meta_labels
        del self.default_name, self.default_nan, self.default_val, self.dval
        del self.frame_list
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
