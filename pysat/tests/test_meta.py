#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat Meta object."""

import copy
import logging
import numpy as np
import os
import pandas as pds
import pytest
import warnings

import pysat
import pysat.instruments.pysat_testing
import pysat.tests.test_utils_io
from pysat.utils import testing


class TestMeta(object):
    """Basic unit tests for standard metadata operations."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = None
        self.meta = pysat.Meta()
        self.mutable = True

        self.meta_labels = {'units': ('Units', str),
                            'name': ('Long_Name', str),
                            'desc': ('Desc', str),
                            'notes': ('Notes', str),
                            'min_val': ('Minimum', np.float64),
                            'max_val': ('Maximum', np.float64),
                            'fill_val': ('Fill_Value', np.float64)}
        self.dval = None
        self.default_name = ['long_name']
        self.default_nan = ['fill', 'value_min', 'value_max']
        self.default_val = {'notes': '', 'units': '', 'desc': ''}
        self.frame_list = ['dummy_frame1', 'dummy_frame2']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        del self.meta, self.meta_labels, self.default_name, self.default_nan
        del self.default_val, self.dval, self.frame_list, self.testInst
        del self.mutable
        return

    # ---------------
    # Utility methods

    def set_meta(self, inst_kwargs=None, keep_mutable=False):
        """Set the `meta` and `testInst` attributes using test Instruments.

        Parameters
        ----------
        inst_kwargs : NoneType or dict
            kwargs to initialize pysat.Instrument object (default=None)
        keep_mutable : bool
            Keep the default `meta.mutable` value if True, if False set to
            class `mutable` attribute. (default=False)

        """
        if inst_kwargs is not None:
            # Load the test Instrument
            self.testInst = pysat.Instrument(**inst_kwargs, use_header=True)
            stime = self.testInst.inst_module._test_dates['']['']
            self.testInst.load(date=stime)

            # Save the meta object and data variable list
            self.meta = self.testInst.meta

            # Update the mutable flag, if desired
            if not keep_mutable:
                self.meta.mutable = self.mutable
        return

    def eval_meta_settings(self):
        """Test the Meta settings for a specified value."""
        # Test the Meta data for the data value, self.dval
        for lkey in self.default_name:
            assert self.meta[self.dval, lkey] == self.dval, \
                "{:} differs from the default value ({:} != {:})".format(
                    lkey.__repr__(), self.meta[self.dval, lkey].__repr__(),
                    self.dval.__repr__())

        for lkey in self.default_nan:
            assert np.isnan(self.meta[self.dval, lkey]), \
                "{:} should be NaN but is not.".format(lkey.__repr__())

        for lkey in self.default_val.keys():
            assert self.meta[self.dval, lkey] == self.default_val[lkey],  \
                "{:} values not equal ({:} != {:})".format(
                    lkey.__repr__(), self.meta[self.dval, lkey].__repr__(),
                    self.default_val[lkey].__repr__())

        assert 'children' not in self.meta.data.columns
        assert self.dval not in self.meta.keys_nD()
        return

    def eval_ho_meta_settings(self, meta_dict):
        """Test the Meta settings for higher order data.

        Parameters
        ----------
        meta_dict : dict
            Dict with meta data labels as keys and values to test against

        """

        # Test the ND metadata results
        testing.assert_list_contains(self.frame_list,
                                     list(self.meta.ho_data[self.dval].keys()))
        testing.assert_list_contains(
            self.frame_list, list(self.meta[self.dval]['children'].keys()))

        # Test the meta settings at the base and nD level
        for label in meta_dict.keys():
            if label == 'meta':
                testing.assert_lists_equal(
                    list(self.meta[self.dval]['children'].attrs()),
                    list(meta_dict[label].attrs()))
                testing.assert_lists_equal(
                    list(self.meta[self.dval]['children'].keys()),
                    list(meta_dict[label].keys()))

                for lvar in self.meta[self.dval]['children'].attrs():
                    for dvar in self.meta[self.dval]['children'].keys():
                        if lvar in self.default_nan:
                            assert np.isnan(
                                self.meta[self.dval]['children'][dvar, lvar]), \
                                "{:s} child {:s} {:s} value {:} != NaN".format(
                                    self.dval.__repr__(), dvar.__repr__(),
                                    lvar.__repr__(),
                                    self.meta[self.dval]['children'][
                                        dvar, lvar].__repr__())
                        else:
                            assert (self.meta[self.dval]['children'][dvar, lvar]
                                    == meta_dict[label][dvar, lvar]), \
                                "{:s} child {:s} {:s} value {:} != {:}".format(
                                    self.dval.__repr__(), dvar.__repr__(),
                                    lvar.__repr__(),
                                    self.meta[self.dval]['children'][
                                        dvar, lvar].__repr__(),
                                    meta_dict[label][dvar, lvar].__repr__())
            else:
                assert self.meta[self.dval]['children'].hasattr_case_neutral(
                    label)
                assert self.meta[self.dval, label] == meta_dict[label], \
                    "{:s} label value {:} != {:}".format(
                        label, self.meta[self.dval, label].__repr__(),
                        meta_dict[label].__repr__())

        return

    # -----------------------
    # Test the Error messages

    def test_setting_nonpandas_metadata(self):
        """Test meta initialization with bad metadata."""

        testing.eval_bad_input(pysat.Meta, ValueError,
                               "Input must be a pandas DataFrame type",
                               input_kwargs={'metadata': 'Not a Panda'})
        return

    def test_pop_w_bad_key(self):
        """Test that a bad key will raise a KeyError for `meta.pop`."""

        testing.eval_bad_input(self.meta.pop, KeyError,
                               'Key not present in metadata variables',
                               input_args=['not_a_key'])
        return

    def test_getitem_w_bad_key(self):
        """Test that a bad key will raise a KeyError in meta access."""

        with pytest.raises(KeyError) as kerr:
            self.meta['not_a_key']

        assert str(kerr).find('not found in MetaData') >= 0
        return

    def test_getitem_w_index(self):
        """Test raises NotImplementedError with an integer index."""

        with pytest.raises(NotImplementedError) as ierr:
            self.meta[1]

        assert str(ierr).find('expected tuple, list, or str') >= 0
        return

    # TODO(#913): remove tests for 2D metadata
    @pytest.mark.parametrize("parent_child", [
        (['alt_profiles', 'profiles'], 'density'),
        (['alt_profiles', 'profiles'], ['density', 'dummy_str']),
        (['alt_profiles', 'profiles'], 'density', 'units'),
        (['alt_profiles', 'profiles'], 'density', ['units', 'long_name'])])
    def test_getitem_w_ho_child_slicing(self, parent_child):
        """Test raises NotImplementedError with parent/child slicing.

        Parameters
        ----------
        parent_child : list
            List of inputs with unsupported parent/child slicing options

        """

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        with pytest.raises(NotImplementedError) as ierr:
            self.meta[parent_child]

        assert str(ierr).find("retrieve child meta data from multiple") >= 0
        return

    def test_concat_strict_w_collision(self):
        """Test raises KeyError when new meta names overlap."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Create a second object with the same data variables, but different
        # units
        concat_meta = self.meta.copy()

        # Test the error message
        testing.eval_bad_input(
            self.meta.concat, KeyError,
            'Duplicated keys (variable names) in Meta.keys()',
            input_args=[concat_meta], input_kwargs={'strict': True})

        return

    # TODO(#913): remove tests for 2d metadata
    def test_concat_strict_w_ho_collision(self):
        """Test raises KeyError when higher-order variable nams overlap."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        # Create a second object with the same higher-order data variables
        concat_meta = pysat.Meta()
        for dvar in self.meta.keys_nD():
            concat_meta[dvar] = self.meta[dvar]

        # Test the error message
        testing.eval_bad_input(
            self.meta.concat, KeyError,
            'Duplicated keys (variable names) in Meta.keys()', [concat_meta],
            {'strict': True})
        return

    def test_multiple_meta_assignment_error(self):
        """Test that assignment of multiple metadata raises a ValueError."""

        with pytest.raises(ValueError) as verr:
            self.meta[['new', 'new2']] = {'units': ['hey', 'hey2'],
                                          'long_name': ['boo']}

        assert str(verr).find(
            'Length of data_vars and inputs must be equal') >= 0
        return

    def test_transfer_attributes_to_non_instrument(self):
        """Test raises ValueError when transferring custom meta to non-Inst."""

        # Set the Meta object without setting testInst
        self.meta.new_attribute = 'hello'

        # Catch and test error message
        testing.eval_bad_input(self.meta.transfer_attributes_to_instrument,
                               ValueError,
                               "Can't transfer Meta attributes to non-",
                               [self.testInst])
        return

    @pytest.mark.parametrize("bad_key,bad_val,err_msg",
                             [("col_names", [], "col_names must include"),
                              ("filename", None, "Must supply an instrument"),
                              ("filename", 5, "Keyword name must be related"),
                              ("filename", 'fake_inst',
                               "Unable to create valid file path")])
    def test_meta_csv_load_w_errors(self, bad_key, bad_val, err_msg):
        """Test raises ValueError when using bad input for loading a CSV file.

        Parameters
        ----------
        bad_key : str
            Kwarg to update with bad data
        bad_val : any type
            Bad input value assinged to `bad_key`
        err_msg : str
            Expected error message

        """

        # Initialize the bad reading inputs
        name = os.path.join(pysat.__path__[0], 'tests', 'cindi_ivm_meta.txt')
        kwargs = {'filename': name, 'na_values': [],
                  'keep_default_na': False, 'col_names': None}
        kwargs[bad_key] = bad_val

        # Raise the expected error and test the message
        testing.eval_bad_input(self.meta.from_csv, ValueError, err_msg,
                               input_kwargs=kwargs)
        return

    # TODO(#913): remove tests for 2D metadata
    def test_meta_rename_bad_ho_input(self):
        """Test raises ValueError when treating normal data like HO data."""

        # Initialize the meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        # Set a bad mapping dictionary
        mapper = {'mlt': {'mlt_profile': 'mlt_density_is_not_real'}}

        testing.eval_bad_input(self.meta.rename, ValueError,
                               "unknown mapped value at 'mlt'", [mapper])
        return

    # -------------------------
    # Test the Warning messages

    def test_init_labels_w_int_default(self):
        """Test MetaLabels initiation with an integer label type."""

        # Reinitialize the Meta and test for warning
        self.meta_labels = {'fill_val': ("fill", int)}

        with warnings.catch_warnings(record=True) as war:
            self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing',
                                       'tag': 'default_meta',
                                       'clean_level': 'clean',
                                       'labels': self.meta_labels})

        # Test the warning
        default_str = ''.join(['Metadata set to defaults, as they were',
                               ' missing in the Instrument.'])
        assert len(war) >= 1

        categories = [war[j].category for j in range(len(war))]
        assert UserWarning in categories

        ind = categories.index(UserWarning)
        assert default_str[8:] in str(war[ind].message)

        # Prepare to test the Metadata
        self.dval = 'int32_dummy'
        self.default_val['fill'] = -1
        self.default_val['notes'] = default_str
        self.default_nan.pop(self.default_nan.index('fill'))

        # Test the Meta settings
        self.eval_meta_settings()
        return

    @pytest.mark.parametrize('bad_val', [[1, 2], None])
    def test_set_meta_with_wrong_type_drop(self, bad_val):
        """Test that setting meta as not-recastable type raises warning.

        Parameters
        ----------
        bad_val : not str
            Any value of a type that is not str

        """

        with warnings.catch_warnings(record=True) as war:
            self.meta['fake_var'] = {'value_max': bad_val}

        # Test the warning
        assert len(war) >= 1
        assert war[0].category == UserWarning
        assert 'Metadata with type' in str(war[0].message)
        assert 'Dropping input' in str(war[0].message)

        # Check that meta is blank
        assert np.isnan(self.meta['fake_var']['value_max'])
        return

    # -------------------------
    # Test the logging messages

    @pytest.mark.parametrize('bad_val', [[1, 2], 1, 2.0, True, None])
    def test_set_meta_with_wrong_type_cast(self, bad_val, caplog):
        """Test that setting meta as recastable type raises appropriate warning.

        Parameters
        ----------
        bad_val : not str
            Any value of a type that is not str

        """

        with caplog.at_level(logging.INFO, logger='pysat'):
            self.meta['fake_var'] = {'units': bad_val}

        # Test the warning
        captured = caplog.text
        assert captured.find('Metadata with type') >= 0
        assert captured.find('Recasting input') >= 0

        # Check that meta is set
        if hasattr(bad_val, "__iter__"):
            exp_val = "\n\n".join([str(bval) for bval in bad_val])
        else:
            exp_val = str(bad_val)
        assert self.meta['fake_var']['units'] == exp_val
        return

    @pytest.mark.parametrize("in_val", [1., 1, {}, None, []])
    def test_info_message_incorrect_input_meta_labels(self, in_val, caplog):
        """Test for info message when labels input not correct.

        Parameters
        ----------
        in_val : any
            Value to assign to test metadata variable

        """

        with caplog.at_level(logging.INFO, logger='pysat'):
            self.meta = pysat.Meta(labels={'min_val': ('min_val', in_val)})

            # Assign any new meta variable
            self.meta['hi'] = {'units': 'goodbye'}

            # Test for expected string
            captured = caplog.text
            test_str = ''.join(('A problem may have been encountered with the',
                                ' user supplied type for Meta attribute'))
            assert captured.find(test_str) >= 0

        return

    # ----------------------------
    # Test the class magic methods

    def test_repr(self):
        """Test the `Meta.__repr__` method."""

        out = self.meta.__repr__()
        assert isinstance(out, str)
        assert out.find('Meta(') >= 0
        return

    # TODO(#913): remove tests for 2d metadata
    @pytest.mark.parametrize('long_str', [True, False])
    @pytest.mark.parametrize('inst_kwargs',
                             [None, {'platform': 'pysat', 'name': 'testing'},
                              {'platform': 'pysat', 'name': 'testing2d'}])
    def test_str(self, long_str, inst_kwargs):
        """Test long string output with custom meta data.

        Parameters
        ----------
        long_str : bool
            Flag for testing expanded output
        inst_kwargs : dict or NoneType
            Passed to `self.set_meta`

        """

        # Set the meta object
        self.set_meta(inst_kwargs=inst_kwargs)

        # Get the output string
        out = self.meta.__str__(long_str=long_str)

        # Evaluate the common parts of the output string
        assert out.find('pysat Meta object') >= 0
        assert out.find('standard variables') > 0
        assert out.find('ND variables') > 0
        assert out.find('global attributes') > 0

        # Evaluate the extra parts of the long output string
        if long_str:
            if inst_kwargs is not None:
                ndvar = 0
                for dvar in self.testInst.vars_no_time:
                    if out.find(dvar) > 0:
                        ndvar += 1
                assert ndvar > 0, "Represented data variable names missing"

                assert out.find('Standard Metadata variables:') > 0
            else:
                assert out.find('Standard Metadata variables:') < 0

            if inst_kwargs is not None and inst_kwargs['name'] == 'testing2d':
                assert out.find('ND Metadata variables:') > 0
            else:
                assert out.find('ND Metadata variables:') < 0
        else:
            assert out.find('Standard Metadata variables:') < 0
            assert out.find('ND Metadata variables:') < 0
        return

    def test_self_equality(self):
        """Test Meta equality for the same object."""

        assert self.meta == self.meta
        return

    def test_equality(self):
        """Test that meta equality works with identically set objects."""

        # Add identical data to the test and comparison meta objects
        cmeta = pysat.Meta()

        for mobj in [self.meta, cmeta]:
            mobj['test_var'] = {'units': 'testU',
                                'name': 'test variable',
                                'notes': 'test notes',
                                'desc': 'test description',
                                'min_val': 0.0,
                                'max_val': 10.0,
                                'fill_val': -1.0}

        # Test the equality
        assert cmeta == self.meta, "identical meta objects differ"
        return

    # TODO(#908): remove tests for deprecated instruments
    @pytest.mark.parametrize("inst_name", ["testing", "testing2d",
                                           "ndtesting", "testing_xarray",
                                           "testmodel"])
    def test_equality_w_copy(self, inst_name):
        """Test that meta remains the same when copied.

        Parameters
        ----------
        inst_name : str
            String corresponding to a pysat test Instrument name.

        """

        # Initialize the instrument to create a full meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': inst_name})

        # Create and test a copy
        meta_copy = self.meta.copy()
        assert meta_copy == self.meta, "copy of meta data differs"
        return

    @pytest.mark.parametrize("emeta", [pysat.Meta(), pysat.Instrument()])
    def test_inequality(self, emeta):
        """Test meta inequality for different comparison objects.

        Parameters
        ----------
        emeta : object
            Object of any type that is not equal to the Meta data from the
            `pysat_testing.py` Instrument.

        """

        # Initialize the instrument to create a full meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': "testing"})

        # Evaluate the inequality
        assert emeta != self.meta, "meta equality not detectinng differences"
        return

    # TODO(#789): remove tests for higher order meta
    @pytest.mark.parametrize('val_dict', [
        {'units': 'U', 'long_name': 'HO Val', 'radn': 'raiden'},
        {'units': 'MetaU', 'long_name': 'HO Val'}])
    def test_inequality_with_higher_order_meta(self, val_dict):
        """Test inequality with higher order metadata.

        Parameters
        ----------
        val_dict : dict
            Information to be added to higher order metadata variable

        """

        meta_dict = {'units': {'ho_val': 'U', 'ho_prof': 'e-'},
                     'long_name': {'ho_val': 'HO Val', 'ho_prof': 'HO Profile'}}

        # Set the default meta object
        self.meta['ho_data'] = pysat.Meta(pds.DataFrame(meta_dict))

        # Set the altered meta object
        cmeta = pysat.Meta()

        for vkey in val_dict.keys():
            if vkey in meta_dict.keys():
                meta_dict[vkey]['ho_val'] = val_dict[vkey]
            else:
                meta_dict[vkey] = {'ho_val': val_dict[vkey]}

        cmeta['ho_data'] = pysat.Meta(pds.DataFrame(meta_dict))

        # Evaluate the inequality
        assert cmeta != self.meta
        return

    @pytest.mark.parametrize("label_key", ["units", "name", "notes", "desc",
                                           "min_val", "max_val", "fill_val"])
    def test_value_inequality(self, label_key):
        """Test that meta equality works without copy.

        Parameters
        ----------
        label_key : str
            metadata key being tested

        """

        # Add different data to the test and comparison meta objects
        meta_dict = {'units': 'testU',
                     'name': 'test variable',
                     'notes': "test notes",
                     'desc': "test description",
                     "min_val": 0.0,
                     "max_val": 10.0,
                     "fill_val": -1.0}

        self.meta['test_var'] = meta_dict

        if isinstance(meta_dict[label_key], str):
            meta_dict[label_key] = "different"
        else:
            meta_dict[label_key] = 99.0

        cmeta = pysat.Meta()
        cmeta['test_var'] = meta_dict

        # Test the equality
        assert cmeta != self.meta, \
            "differences not detected in label {:s}".format(label_key)
        return

    # TODO(#908): remove tests for deprecated instruments
    @pytest.mark.parametrize("inst_name", ["testing", "testing2d",
                                           "ndtesting", "testing_xarray",
                                           "testmodel"])
    def test_pop(self, inst_name):
        """Test meta attributes are retained when extracted using pop.

        Parameters
        ----------
        inst_name : str
            pysat test instrument name

        """

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': inst_name})

        # Pop each of the data variables
        for dvar in self.testInst.vars_no_time:
            mcomp = self.meta[dvar]
            mpop = self.meta.pop(dvar)

            # Test the popped object labels
            pop_attrs = list(mpop.keys())
            pop_attrs.pop(pop_attrs.index('children'))
            testing.assert_lists_equal(pop_attrs, list(self.meta.attrs()))

            # Test the popped object values
            pop_values = [mpop[pattr] for pattr in pop_attrs]
            comp_values = [mcomp[pattr] for pattr in pop_attrs]
            testing.assert_lists_equal(pop_values, comp_values)

            if mpop['children'] is not None:
                assert mpop['children'] == mcomp['children']

            # Test that the popped variable is no longer in the main object
            assert dvar not in self.meta.keys(), "pop did not remove metadata"

        return

    # -------------------------------------
    # Test the class with standard metadata

    def test_accept_default_labels(self):
        """Test `Meta.accept_default_labels."""

        # Start with default test labels
        other_labels = copy.deepcopy(self.meta_labels)

        # Remove 'units' label
        other_labels.pop('units')

        # Modify remaining labels
        for label in other_labels.keys():
            other_labels[label] = (self.meta_labels[label][0].upper(),
                                   self.meta_labels[label][1])

        # Define new label
        other_labels['new_label_label'] = ('new_data_label', np.int64)

        # Run function
        other_meta = pysat.Meta(labels=other_labels)
        self.meta.accept_default_labels(other_meta)

        # Confirm results at MetaLabels level
        other_meta_labels = pysat.MetaLabels(metadata=pysat.Meta(),
                                             **other_labels)

        # Confirm underlying information correct
        assert self.meta.labels.label_type == other_meta_labels.label_type
        assert self.meta.labels.label_attrs == other_meta_labels.label_attrs

        return

    @pytest.mark.parametrize("custom_attr", [None, 'custom_meta'])
    @pytest.mark.parametrize("assign_type", [dict, pds.Series])
    def test_meta_assignment(self, custom_attr, assign_type):
        """Test basic assignment of metadata using different data types.

        Parameters
        ----------
        custom_attr : str or NoneType
            Custom meta attribute label or None to use only defaults.
        assign_type : type
            Data types that may be used to set metadata for a data variable.

        """

        # Set the desired values
        self.dval = 'test_meta_dict_assignment'
        self.default_val = {
            getattr(self.meta.labels, mattr): ' '.join(['test', mattr])
            if self.meta.labels.label_type[mattr] == str else -47
            for mattr in self.meta.labels.label_type.keys()}
        self.default_name = []
        self.default_nan = []

        if custom_attr is not None:
            self.default_val[custom_attr] = 'Custom Attribute Value'

        # Assign the meta data using a dictionary
        self.meta[self.dval] = assign_type(self.default_val)

        # Evaluate the meta data
        self.eval_meta_settings()
        return

    @pytest.mark.parametrize("custom_attr", [None, 'custom_meta'])
    @pytest.mark.parametrize("assign_type", [dict, pds.Series])
    def test_multiple_meta_assignment(self, custom_attr, assign_type):
        """Test assignment of multiple metadata.

        Parameters
        ----------
        custom_attr : str or NoneType
            Custom meta attribute label or None to use only defaults.
        assign_type : type
            Data types that may be used to set metadata for a data variable.

        """

        # Set the desired values
        dvals = ['mult1', 'mult2']
        default_vals = {
            getattr(self.meta.labels, mattr): [
                ' '.join(['test', mattr, self.dval])
                if self.meta.labels.label_type[mattr] == str else -47
                for self.dval in dvals]
            for mattr in self.meta.labels.label_type.keys()}
        self.default_name = []
        self.default_nan = []

        if custom_attr is not None:
            default_vals[custom_attr] = ['Custom Attr {:s}'.format(self.dval)
                                         for self.dval in dvals]

        # Assign the meta data
        self.meta[dvals] = assign_type(default_vals)

        # Test the data assignment for each value
        for i, self.dval in enumerate(dvals):
            self.default_val = {mattr: default_vals[mattr][i]
                                for mattr in default_vals.keys()}
            self.eval_meta_settings()
        return

    # TODO(#913): remove tests for 2D metadata
    @pytest.mark.parametrize('inst_name', ['testing', 'testing2d'])
    @pytest.mark.parametrize('num_mvals', [0, 1, 3])
    @pytest.mark.parametrize('num_dvals', [0, 1, 3])
    def test_selected_meta_retrieval(self, inst_name, num_mvals, num_dvals):
        """Test metadata retrieval using various restrictions.

        Parameters
        ----------
        inst_name : str
            Name of the pysat test instrument
        num_mvals : int
            Number of meta attributes to retrieve
        num_dvals : int
            Number of data values to retrieve

        """

        # Set the meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': inst_name})

        # Get the selection criteria
        dvals = list(self.testInst.vars_no_time[:num_dvals])
        mvals = [getattr(self.meta.labels, mattr)
                 for mattr in list(self.meta_labels.keys())[:num_mvals]]

        # If dvals is greater than zero and there is higher order data,
        # make sure at least one is included
        nd_inds = list()
        if len(dvals) > 0:
            nd_vals = [key for key in self.meta.keys_nD()]

            if len(nd_vals) > 0:
                nd_inds = [dvals.index(self.dval) for self.dval in nd_vals
                           if self.dval in dvals]

                if len(nd_inds) == 0:
                    dvals[0] = nd_vals[0]
                    nd_inds = [0]

        # Retrieve meta data for desired values
        sel_meta = self.meta[dvals, mvals]

        # Evaluate retrieved data
        assert isinstance(sel_meta, pds.DataFrame)
        testing.assert_lists_equal(dvals, list(sel_meta.index))
        testing.assert_lists_equal(mvals, list(sel_meta.columns))

        # If there is higher order data, test the retrieval
        for pind in nd_inds:
            # Get the desired number of child variables
            self.dval = dvals[pind]
            cvals = [kk for kk in self.meta[self.dval].children.keys()][
                :num_dvals]

        # Retrieve meta data for desired values
            sel_meta = self.meta[self.dval, cvals, mvals]

            # Evaluate retrieved data
            assert isinstance(sel_meta, pds.DataFrame)
            testing.assert_lists_equal(cvals, list(sel_meta.index))
            testing.assert_lists_equal(mvals, list(sel_meta.columns))

        return

    def test_replace_meta(self):
        """Test replacement of metadata units."""

        # Set the meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': "testing"})

        # Change the meta and update the evaluation data
        self.dval = self.testInst.vars_no_time[0]

        for val in self.default_val.keys():
            # These values will be unaltered, use what was set
            self.default_val[val] = self.meta[self.dval, val]

        for val in self.default_nan:
            # Change these meta values to the best number for testing
            self.meta[self.dval] = {val: -47.0}
            self.default_val[val] = -47.0

        for val in self.default_name:
            # Change these meta values to a new name for testing
            new_val = " ".join(["New", self.meta[self.dval, val]])
            self.meta[self.dval] = {val: new_val}
            self.default_val[val] = new_val

        self.default_nan = []
        self.default_name = []

        # Evaluate the updated meta data
        self.eval_meta_settings()
        return

    @pytest.mark.parametrize("num_dvars", [0, 1, 3])
    @pytest.mark.parametrize("use_upper", [True, False])
    def test_replace_multiple_meta_w_list(self, num_dvars, use_upper):
        """Test replace multiple metadata units as a list.

        Parameters
        ----------
        num_dvars : int
            Number of data variables for which 'units' will be updated.
        use_upper : bool
            Use upper-case for variable names, testing case-insensitivity

        """

        # Set the meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': "testing"})
        self.default_name = []

        # Update the meta data
        dvals = [self.dval.upper() if use_upper else self.dval
                 for self.dval in self.testInst.vars_no_time[:num_dvars]]

        for label in self.default_nan:
            self.default_val[label] = -47
            lval = [self.default_val[label] for self.dval in dvals]
            self.meta[dvals] = {label: lval}

        # Evaluate the meta data
        self.default_nan = []

        for i, self.dval in enumerate(dvals):
            for label in self.default_val.keys():
                self.default_val[label] = self.meta[self.dval, label]
            self.eval_meta_settings()
        return

    def test_add_meta_then_add_new_metadata_types(self):
        """Test addition of new metadata followed by new metadata types."""

        # Set a meta value using only standard labels
        meta_dict = {self.meta.labels.units: 'U'}
        self.meta['no_custom'] = meta_dict

        # Set another meta value using standard and custom labels
        meta_dict['custom_label'] = 'I am a custom value'
        self.meta['yes_custom'] = meta_dict

        # Evaluate the results
        for mlabel in meta_dict.keys():
            for dval in ['yes_custom', 'no_custom']:
                if mlabel == 'custom_label' and dval == 'no_custom':
                    assert self.meta[dval, mlabel] == '', \
                        "Custom label set after init didn't default correctly"
                else:
                    assert self.meta[dval, mlabel] == meta_dict[mlabel], \
                        "{:} label has unexpected value ({:} != {:})".format(
                            dval.__repr__(), self.meta[dval, mlabel].__repr__(),
                            meta_dict[mlabel].__repr__())
        return

    def test_meta_immutable_at_instrument_instantiation(self):
        """Test that meta is immutable at instrument Instantiation."""

        # Set the Meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'},
                      keep_mutable=True)

        # Test the default value for `mutable`
        assert self.meta.mutable is False, \
            "Meta `mutable` attribute initialized to the wrong value."

        return

    # TODO(#913): remove tests for 2D metadata
    @pytest.mark.parametrize('inst_name', ['testing', 'testing2d'])
    def test_assign_nonstandard_metalabels(self, inst_name):
        """Test labels do not conform to the standard values if set that way.

        Parameters
        ----------
        inst_name : str
            String denoting the pysat testing instrument name

        """

        # Assign meta data with non-standard labels
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': inst_name,
                                   'labels': self.meta_labels})

        # Test that standard attributes are missing and non-standard
        # attributes are present
        standard_labels = pysat.MetaLabels()
        for dval in self.testInst.vars_no_time:
            for label in self.meta_labels.keys():
                slabel = getattr(standard_labels, label)
                assert not hasattr(self.meta[dval], slabel), \
                    "standard label {:} should not be present for {:}".format(
                        slabel.__repr__(), dval.__repr__())

            assert hasattr(self.meta[dval], self.meta_labels[label][0]), \
                "non-standard label {:} is missing for {:}".format(
                    self.meta_labels[label][0].__repr__(), dval.__repr__())
        return

    @pytest.mark.parametrize("labels, vals",
                             [([], []),
                              (['units', 'long_name'], ['V', 'Longgggg']),
                              (['fill'], [-999])])
    def test_inst_data_assign_meta(self, labels, vals):
        """Test Meta initialization with data.

        Parameters
        ----------
        labels : list
            List of strings for metadata keys to be tested
        vals : list
            List of values for metadata keys

        """

        # Initialize the instrument
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Update the testing data and set the new data dictionary
        self.dval = 'test_inst_data_assign_meta'
        set_dict = {'data': self.testInst['mlt']}
        for i, slabel in enumerate(labels):
            if slabel in self.default_name:
                self.default_name.pop(self.default_name.index(slabel))
            elif slabel in self.default_nan:
                self.default_nan.pop(self.default_nan.index(slabel))
            self.default_val[slabel] = vals[i]
            set_dict[slabel] = vals[i]

        # Initialize the Meta data
        self.testInst[self.dval] = set_dict
        self.meta = self.testInst.meta

        # Test the Meta settings
        self.eval_meta_settings()
        return

    @pytest.mark.parametrize("mlabel,slist", [("units", []),
                                              ("notes", ['A', 'B'])])
    def test_inst_data_assign_meta_string_list(self, mlabel, slist):
        """Test string assignment to meta with a list of strings.

        Parameters
        ----------
        mlabel : str
            Meta key to be tested
        slist : list
            List of values to be assigned to `mlabel`

        """

        # Initialize the instrument
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Alter the Meta Data
        self.dval = 'test_inst_data_assign_meta_string_list'
        self.testInst[self.dval] = {'data': self.testInst['mlt'],
                                    mlabel: slist}
        self.meta = self.testInst.meta

        # Update the testing data
        self.default_val[mlabel] = '\n\n'.join(slist)

        # Test the Meta settings
        self.eval_meta_settings()
        return

    def test_inst_data_assign_meta_then_data(self):
        """Test meta assignment when data updated after metadata."""

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Alter the Meta data
        self.dval = 'test_inst_data_assign_meta_then_data'
        self.testInst[self.dval] = {'data': self.testInst['mlt'], 'units': 'V'}
        self.testInst[self.dval] = self.testInst['mlt']
        self.meta = self.testInst.meta

        # Update the testing data
        self.default_val['units'] = 'V'

        # Test the Meta settings
        self.eval_meta_settings()
        return

    def test_inst_assign_from_meta(self):
        """Test Meta assignment from another meta object."""

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Alter the Meta data
        self.dval = "test_inst_assign_from_meta"
        self.testInst['new_data'] = self.testInst['mlt']
        self.testInst[self.dval] = self.testInst['mlt']
        self.testInst.meta[self.dval] = self.testInst.meta['new_data']
        self.meta = self.testInst.meta

        # Update the testing info
        for skey in self.default_name:
            self.default_val[skey] = 'new_data'
        self.default_name = []

        # Test the Meta settings
        self.eval_meta_settings()
        return

    def test_concat(self):
        """Test that `meta.concat` adds new meta objects appropriately."""

        # Create meta data to concatenate
        meta2 = pysat.Meta()
        meta2['new3'] = {'units': 'hey3', 'long_name': 'crew_brew'}

        # Perform and test for successful concatenation
        self.meta = self.meta.concat(meta2)
        assert self.meta['new3'].units == 'hey3'
        return

    def test_meta_csv_load(self):
        """Test load metadata from a CSV file."""

        # Set the meta data from a Comma Separated Value file
        name = os.path.join(pysat.__path__[0], 'tests', 'cindi_ivm_meta.txt')
        self.meta = self.meta.from_csv(filename=name, na_values=[],
                                       keep_default_na=False,
                                       col_names=['name', 'long_name', 'idx',
                                                  'units', 'description'])
        # Set the evaluation data
        self.dval = 'iv_mer'
        self.default_val = {'long_name': 'Ion Drift Meridional',
                            'idx': 117, 'units': 'm/s',
                            'description': 'Constructed using IGRF mag field.'}
        self.default_name = []
        self.default_nan = []

        # Test the output
        self.eval_meta_settings()
        testing.assert_lists_equal([val for val in self.meta.keys()],
                                   ['yrdoy', 'uts', 'glat', 'glong', 'alt',
                                    'pos_eci_x', 'pos_eci_y', 'pos_eci_z',
                                    'vel_eci_x', 'vel_eci_y', 'vel_eci_z',
                                    'sza', 'slt', 'apex_alt', 'apex_lat',
                                    'apex_long', 'inv_lat', 'mag_incl', 'mlat',
                                    'mlt', 'bg_n', 'bg_e', 'bg_d', 'rpa_flag',
                                    'dm_flag', 'iv_x', 'iv_x_var', 'iv_y',
                                    'iv_y_var', 'iv_z', 'iv_z_var', 'ion_dens',
                                    'ion_dens_var', 'ion_temp', 'ion_temp_var',
                                    'frac_dens_o', 'frac_dens_o_var',
                                    'frac_dens_h', 'frac_dens_h_var',
                                    'sens_pot', 'sens_pot_var', 'dm_a_flag',
                                    'dm_a_dens', 'dm_a_dens_var', 'dm_b_flag',
                                    'dm_b_dens', 'dm_b_dens_var', 'bg_x',
                                    'bg_y', 'bg_z', 'sra', 'ion_dens_zni',
                                    'vel_sc_x', 'vel_sc_y', 'vel_sc_z',
                                    'velr_sc_x', 'velr_sc_y', 'velr_sc_z',
                                    'offset_flag', 'iv_zon', 'iv_zon_var',
                                    'iv_par', 'iv_par_var', 'iv_mer',
                                    'iv_mer_var', 'unit_zon_x', 'unit_zon_y',
                                    'unit_zon_z', 'unit_par_x', 'unit_par_y',
                                    'unit_par_z', 'unit_mer_x', 'unit_mer_y',
                                    'unit_mer_z'])
        return

    def test_meta_merge(self):
        """Test merging two meta object."""

        # Set meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Create a second meta object to merge
        self.dval = 'merged_data'
        meta_dict = {'units': 'U', 'long_name': 'Merged Data',
                     'custom_label': 'PI Information'}
        merge_meta = pysat.Meta()
        merge_meta[self.dval] = meta_dict

        # Test that the data to merge in is not present
        assert self.dval not in self.meta.keys()

        # Merge the Meta objects into `self.meta`.
        self.meta.merge(merge_meta)

        # Test the results
        assert self.dval in self.meta.keys()

        for label in meta_dict.keys():
            assert self.meta[self.dval, label] == meta_dict[label], \
                "{:} label has unexpected value ({:} != {:})".format(
                    label.__repr__(), self.meta[self.dval, label].__repr__(),
                    meta_dict[label].__repr__())
        return

    @pytest.mark.parametrize("num_drop", [0, 1, 3])
    def test_meta_drop(self, num_drop):
        """Test successful deletion of meta data for specific values.

        Parameters
        ----------
        num_drop : int
            Number of variables to drop in a single go.

        """

        # Set meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Get the data variables to drop
        self.dval = self.testInst.vars_no_time[:num_drop]
        testing.assert_list_contains(self.dval,
                                     [val for val in self.meta.keys()])

        # Drop the values
        self.meta.drop(self.dval)

        # Test the successful deletion
        meta_vals = [val for val in self.meta.keys()]

        assert len(meta_vals) == len(self.testInst.vars_no_time) - num_drop
        for val in self.dval:
            assert val not in meta_vals, \
                "{:} not dropped from Meta".format(val.__repr__())
        return

    @pytest.mark.parametrize("num_keep", [0, 1, 3])
    def test_meta_keep(self, num_keep):
        """Test successful deletion of meta data for values not specified.

        Parameters
        ----------
        num_keep : int
            Number of variables to keep in a single go.

        """

        # Set meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Get the data variables to drop
        self.dval = self.testInst.vars_no_time[:num_keep]
        testing.assert_list_contains(self.dval,
                                     [val for val in self.meta.keys()])

        # Drop the values
        self.meta.keep(self.dval)

        # Test the successful deletion of unspecified values
        testing.assert_lists_equal(self.dval, [val for val in self.meta.keys()])
        return

    def test_create_new_metadata_from_old(self):
        """Test create new metadata from old metadata."""

        # Set the meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Create new meta data
        new_meta = pysat.Meta(metadata=self.meta.data)

        # Evaluate using equality
        assert self.meta == new_meta
        return

    def test_retrieve_wrong_case(self):
        """Test that label retrieval work when the case is wrong."""

        # Set default meta data with capitalized labels
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.dval = 'retrieve_wrong_case'
        self.meta[self.dval] = {'Long_Name': self.dval}

        # Evaluate data with lower case labels
        self.default_nan = [self.meta_labels[mkey][0].lower()
                            for mkey in ['fill_val', 'max_val', 'min_val']]
        self.eval_meta_settings()
        return

    @pytest.mark.parametrize("num_dvals", [0, 1, 3])
    def test_set_wrong_case(self, num_dvals):
        """Test that setting labels works if the case is wrong.

        Parameters
        ----------
        num_dvals : int
            Number of data values to retrieve

        """

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing',
                                   'labels': self.meta_labels})

        # Set data using lower case labels
        dvals = self.testInst.vars_no_time[:num_dvals]

        for label in ['fill_val', 'max_val', 'min_val']:
            self.meta[dvals] = {self.meta_labels[label][0].lower():
                                [-47 for i in range(num_dvals)]}

        # Evaluate the data with lower case labels
        self.default_name = []
        self.default_nan = []
        for self.dval in dvals:
            self.default_val = {label.lower(): self.meta[self.dval, label]
                                for label, mtype in self.meta_labels.values()}
            self.eval_meta_settings()
        return

    def test_data_retrieval_case_insensitive(self):
        """Test that data variables are case insensitive for keys in meta."""

        # Initalize the meta data
        self.dval = "test_val"
        self.meta[self.dval] = self.default_val

        # Test that the data value is present using real key and upper-case
        # version of that key
        assert self.dval in self.meta.keys()

        # Cannot specify keys for case-insensitive look-up
        assert self.dval.upper() in self.meta
        return

    @pytest.mark.parametrize("data_val", ['test_val', 'TEST_VAL', 'Test_Val',
                                          'TeSt_vAl'])
    def test_var_case_name(self, data_val):
        """Test `meta.var_case_name` preserves the required output case.

        Parameters
        ----------
        data_val : str
            Data value name

        """

        # Set the meta data variable
        self.meta[data_val] = self.default_val

        # Evaluate method performance using different input variations
        assert data_val == self.meta.var_case_name(data_val.lower())
        assert data_val == self.meta.var_case_name(data_val.upper())
        assert data_val == self.meta.var_case_name(data_val.capitalize())
        assert data_val == self.meta.var_case_name(data_val)
        return

    @pytest.mark.parametrize("data_val", ['test_val', 'TEST_VAL', 'Test_Val',
                                          'TeSt_vAl'])
    def test_var_case_name_list_input(self, data_val):
        """Test `meta.var_case_name` preserves case for list inputs.

        Parameters
        ----------
        data_val : str
            Key string used for testing

        """

        self.meta[data_val] = self.default_val

        output = self.meta.var_case_name([data_val.lower(),
                                          data_val.capitalize(),
                                          data_val.upper(),
                                          data_val])
        target = [data_val] * len(output)
        assert np.all(target == output)
        return

    @pytest.mark.parametrize("label", ['meta_label', 'META_LABEL', 'Meta_Label',
                                       'MeTa_lAbEl'])
    def test_attribute_name_case(self, label):
        """Test that `meta.attribute_case_name` preserves the stored case.

        Parameters
        ----------
        label : str
            Label name

        """

        # Set the meta data variable
        self.dval = 'test_val'
        self.meta[self.dval] = {label: 'Test meta data for meta label'}

        # Test the meta method using different input variations
        assert self.meta.attr_case_name(label.upper()) == label
        assert self.meta.attr_case_name(label.lower()) == label
        assert self.meta.attr_case_name(label.capitalize()) == label
        assert self.meta.attr_case_name(label) == label
        return

    @pytest.mark.parametrize("label", ['meta_label', 'META_LABEL', 'Meta_Label',
                                       'MeTa_lAbEl'])
    def test_get_attribute_name_case_preservation_list_input(self, label):
        """Test that meta labels and values preserve the input case, list input.

        Parameters
        ----------
        label : str
            Metadata string label used for testing

        """

        # Set the meta data variable
        self.dval = 'test_val'
        self.meta[self.dval] = {label: 'Test meta data for meta label'}

        # Test the meta method using different input variations
        ins = [label.upper(), label.lower(), label.capitalize(),
               label]
        outs = [label] * len(ins)
        assert np.all(self.meta.attr_case_name(ins) == outs)
        return

    @pytest.mark.parametrize("label", ['meta_label', 'META_LABEL', 'Meta_Label',
                                       'MeTa_lAbEl'])
    def test_hasattr_case_neutral(self, label):
        """Test `meta.hasattr_case_neutral` identifies the label name.

        Parameters
        ----------
        label : str
            Label name

        """

        # Set the meta data variable
        self.dval = 'test_val'
        self.meta[self.dval] = {label: 'Test meta data for meta label'}

        # Test the meta method using different input variations
        assert self.meta.hasattr_case_neutral(label.upper())
        assert self.meta.hasattr_case_neutral(label.lower())
        assert self.meta.hasattr_case_neutral(label.capitalize())
        assert self.meta.hasattr_case_neutral(label)
        return

    def test_meta_rename_function(self):
        """Test `meta.rename` method using a function."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Rename the meta variables to be all upper case, this will differ
        # from the Instrument variables, as pysat defaults to lower case
        self.meta.rename(str.upper)

        for dvar in self.testInst.vars_no_time:
            assert dvar not in self.meta.keys(), \
                "variable not renamed: {:}".format(repr(dvar))
            assert dvar.upper() in self.meta.keys(), \
                "renamed variable missing: {:}".format(repr(dvar.upper()))

        return

    def test_meta_rename_dict(self):
        """Test `meta.rename` method using a dict."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Create a renaming dictionary, which only changes three of the
        # variable names
        rename_dict = {dvar: dvar.upper()
                       for i, dvar in enumerate(self.testInst.vars_no_time)
                       if i < 3}

        # Rename the meta variables to be all upper case, this will differ
        # from the Instrument variables, as pysat defaults to lower case
        self.meta.rename(rename_dict)

        for dvar in self.testInst.vars_no_time:
            if dvar in rename_dict.keys():
                assert dvar not in self.meta.keys(), \
                    "variable not renamed: {:}".format(repr(dvar))
                assert rename_dict[dvar] in self.meta.keys(), \
                    "renamed variable missing: {:}".format(
                        repr(rename_dict[dvar]))
            else:
                assert dvar in self.meta.keys(), \
                    "unmapped variable renamed: {:}".format(repr(dvar))

        return

    def test_add_epoch(self):
        """Test that epoch metadata is added upon request."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Test that the epoch meta data is absent
        assert self.testInst.index.name not in self.meta.keys()

        # Add the epoch meta data
        self.meta.add_epoch_metadata(self.testInst.index.name)

        # Test the new metadata
        assert self.testInst.index.name in self.meta.keys()
        for label in [self.meta.labels.units, self.meta.labels.name,
                      self.meta.labels.desc, self.meta.labels.notes]:
            mval = self.meta[self.testInst.index.name, label]
            assert mval.find('Milliseconds since 1970-1-1 00:00:00') >= 0, \
                "unexpected value for {:} label {:}: {:}".format(
                    self.testInst.index.name, label, repr(mval))

        return

    def test_update_epoch(self):
        """Test that epoch metadata is updated upon request."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Set units to a special value
        self.meta['time'] = {self.meta.labels.units: "U"}

        # Update the epoch meta data that was set to unknown default values
        self.meta.add_epoch_metadata("time")

        # Test the new metadata
        assert "U" == self.meta["time", self.meta.labels.units]
        assert "time" == self.meta["time", self.meta.labels.name]
        for label in [self.meta.labels.desc, self.meta.labels.notes]:
            mval = self.meta["time", label]
            assert mval.find('Milliseconds since 1970-1-1 00:00:00') >= 0, \
                "unexpected value for time label {:}: {:}".format(
                    label, repr(mval))

        return

    # -------------------------------
    # Tests for higher order metadata

    # TODO(#789): remove tests for higher order meta
    @pytest.mark.parametrize('meta_dict', [
        None, {'units': 'V', 'long_name': 'test name'},
        {'units': 'V', 'long_name': 'test name',
         'meta': pysat.Meta(metadata=pds.DataFrame(
             {'units': {'dummy_frame1': 'A', 'dummy_frame2': ''},
              'desc': {'dummy_frame1': '',
                       'dummy_frame2': 'A filler description'},
              'long_name': {'dummy_frame1': 'Dummy 1',
                            'dummy_frame2': 'Dummy 2'}}))},
        {'units': 'V', 'long_name': 'test name', 'bananas': 0,
         'meta': pysat.Meta(metadata=pds.DataFrame(
             {'units': {'dummy_frame1': 'A', 'dummy_frame2': ''},
              'desc': {'dummy_frame1': '',
                       'dummy_frame2': 'A filler description'},
              'long_name': {'dummy_frame1': 'Dummy 1',
                            'dummy_frame2': 'Dummy 2'},
              'bananas': {'dummy_frame1': 1, 'dummy_frame2': 2}}))}])
    def test_inst_ho_data_assignment(self, meta_dict):
        """Test the assignment of the higher order metadata.

        Parameters
        ----------
        meta_dict : dict or NoneType
            Dictionary used to create test metadata

        """

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Alter the Meta data
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        inst_data = [frame for i in range(self.testInst.index.shape[0])]
        self.dval = 'test_val'

        if meta_dict is None:
            self.testInst[self.dval] = inst_data
            meta_dict = {'units': '', 'long_name': self.dval, 'desc': ''}
        else:
            meta_dict.update({'data': inst_data})
            self.testInst[self.dval] = meta_dict

            # Remove data key for evaluation
            del meta_dict['data']

        self.meta = self.testInst.meta

        # Test the ND metadata results
        self.eval_ho_meta_settings(meta_dict)
        return

    # TODO(#789): remove tests for higher order meta
    @pytest.mark.parametrize("num_ho, num_lo", [(1, 1), (2, 2)])
    def test_assign_mult_higher_order_meta_from_dict(self, num_ho, num_lo):
        """Test assign higher order metadata from dict with multiple types.

        Parameters
        ----------
        num_ho : int
            Number of higher order data values to initialize
        num_lo : int
            Number of lower order data valuess to initialize

        """

        # Initialize the lower order evaluation data
        self.default_val['units'] = 'U'

        # Initialize the higher-order meta data
        ho_meta = pysat.Meta()
        for flist in self.frame_list:
            ho_meta[flist] = {'units': 'U', 'long_name': flist}

        # Initialize the meta dict for setting the data values
        dvals = ['higher_{:d}'.format(i) for i in range(num_ho)]
        dvals.extend(['lower_{:d}'.format(i) for i in range(num_lo)])

        meta_dict = {'units': ['U' for i in range(len(dvals))],
                     'long_name': [val for val in dvals],
                     'meta': [ho_meta for i in range(num_ho)]}
        meta_dict['meta'].extend([None for i in range(num_lo)])

        # Assign and test the meta data
        self.meta[dvals] = meta_dict

        for i, self.dval in enumerate(dvals):
            if i < num_ho:
                eval_dict = {label: meta_dict[label][i]
                             for label in meta_dict.keys()}
                self.eval_ho_meta_settings(eval_dict)
            else:
                self.eval_meta_settings()
        return

    # TODO(#789): remove tests for higher order meta
    def test_inst_ho_data_assign_meta_then_data(self):
        """Test assignment of higher order metadata before assigning data."""

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Alter the Meta data
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        inst_data = [frame for i in range(self.testInst.index.shape[0])]
        meta_dict = {'data': inst_data, 'units': 'V', 'long_name': 'The Doors',
                     'meta': pysat.Meta(metadata=pds.DataFrame(
                         {'units': {dvar: "{:d}".format(i)
                                    for i, dvar in enumerate(self.frame_list)},
                          'desc': {dvar: "{:s} desc".format(dvar)
                                   for dvar in self.frame_list},
                          'long_name': {dvar: dvar
                                        for dvar in self.frame_list}}))}
        self.dval = 'test_data'

        # Assign the metadata
        self.testInst[self.dval] = meta_dict

        # Alter the data
        self.testInst[self.dval] = inst_data

        # Test the ND metadata results
        self.meta = self.testInst.meta
        del meta_dict['data']
        self.eval_ho_meta_settings(meta_dict)
        return

    # TODO(#913): remove tests for 2D metadata
    def test_inst_ho_data_assign_meta_different_labels(self):
        """Test the higher order assignment of custom metadata labels."""

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        # Alter the higher order metadata
        ho_meta = pysat.Meta(labels={'units': ('barrels', str),
                                     'desc': ('Monkeys', str),
                                     'meta': ('meta', object)})
        self.frame_list = list(
            self.testInst.meta['profiles']['children'].keys())
        for dvar in self.frame_list:
            if dvar == 'density':
                ho_meta[dvar] = {'barrels': 'A'}
            else:
                ho_meta[dvar] = {'Monkeys': 'are fun', 'bananas': 2}

        # The 'units', 'desc' and other labels used on self.testInst are
        # applied to the input metadata to ensure everything remains
        # consistent across the object.
        self.testInst['profiles'] = {'data': self.testInst.data['profiles'],
                                     'units': 'V', 'long_name': 'The Doors',
                                     'meta': ho_meta}
        self.meta = self.testInst.meta

        # Test the nD metadata
        assert self.testInst.meta['profiles', 'long_name'] == 'The Doors'
        testing.assert_list_contains(self.frame_list,
                                     self.meta.ho_data['profiles'])
        testing.assert_list_contains(self.frame_list,
                                     self.meta['profiles']['children'])

        for label in ['units', 'desc']:
            assert self.meta['profiles']['children'].hasattr_case_neutral(label)

        assert self.meta['profiles']['children']['density', 'units'] == 'A'
        assert self.meta['profiles']['children']['density', 'desc'] == ''

        for dvar in ['dummy_str', 'dummy_ustr']:
            assert self.meta['profiles']['children'][dvar, 'desc'] == 'are fun'
            assert self.meta['profiles']['children'][dvar, 'bananas'] == 2
        return

    # TODO(#789): remove tests for higher order meta
    def test_concat_w_ho(self):
        """Test `meta.concat` adds new meta objects with higher order data."""

        # Create meta data to concatenate
        meta2 = pysat.Meta()
        meta2['new3'] = {'units': 'hey3', 'long_name': 'crew_brew'}
        meta2['new4'] = pysat.Meta(pds.DataFrame({
            'units': {'new41': 'hey4'}, 'long_name': {'new41': 'crew_brew'},
            'bob_level': {'new41': 'max'}}))

        # Perform and test for successful concatenation
        self.meta = self.meta.concat(meta2)
        assert self.meta['new3'].units == 'hey3'
        assert self.meta['new4'].children['new41'].units == 'hey4'
        return

    # TODO(#913): remove tests for 2d metadata
    def test_concat_not_strict_w_ho_collision(self):
        """Test non-strict concat with overlapping higher-order data."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        # Create a second object with the same higher-order data variables
        concat_meta = pysat.Meta()
        for dvar in self.meta.keys_nD():
            concat_meta[dvar] = self.meta[dvar]

            # Change the units of the HO data variables
            for cvar in concat_meta[dvar].children.keys():
                # HERE FIX, DOESN'T WORK
                concat_meta[dvar].children[cvar] = {
                    concat_meta.labels.units: "UpdatedUnits"}

        # Concatenate the data
        self.meta = self.meta.concat(concat_meta, strict=False)

        # Test that the Meta data kept the original values
        testing.assert_list_contains(list(concat_meta.keys_nD()),
                                     list(self.meta.keys_nD()))

        for dvar in concat_meta.keys_nD():
            testing.assert_lists_equal(list(concat_meta[dvar].children.keys()),
                                       list(self.meta[dvar].children.keys()))

            for cvar in concat_meta[dvar].children.keys():
                assert self.meta[dvar].children[
                    cvar, self.meta.labels.units].find('Updated') >= 0
        return

    # TODO(#789): remove tests for higher order meta
    @pytest.mark.parametrize("label", ['meta_label', 'META_LABEL', 'Meta_Label',
                                       'MeTa_lAbEl'])
    def test_ho_attribute_name_case(self, label):
        """Test that `meta.attribute_case_name` preserves the HO stored case.

        Parameters
        ----------
        label : str
            Label name

        """

        # Only set `label` in the child data variable
        self.dval = 'test_val'
        self.meta[self.dval] = self.default_val
        cmeta = pysat.Meta()
        cval = "_".join([self.dval, "child"])
        cmeta[cval] = {label: 'Test meta data for child meta label'}
        self.meta[self.dval] = cmeta

        # Test the meta method using different input variations
        assert self.meta.attr_case_name(label.upper()) == label
        assert self.meta.attr_case_name(label.lower()) == label
        assert self.meta.attr_case_name(label.capitalize()) == label
        assert self.meta.attr_case_name(label) == label
        return

    # TODO(#789): remove tests for higher order meta
    @pytest.mark.parametrize("label", ['meta_label', 'META_LABEL', 'Meta_Label',
                                       'MeTa_lAbEl'])
    def test_ho_hasattr_case_neutral(self, label):
        """Test `meta.hasattr_case_neutral` identifies the HO label name.

        Parameters
        ----------
        label : str
            Label name

        """

        # Only set `label` in the child data variable
        self.dval = 'test_val'
        self.meta[self.dval] = self.default_val
        cmeta = pysat.Meta()
        cval = "_".join([self.dval, "child"])
        cmeta[cval] = {label: 'Test meta data for child meta label'}
        self.meta[self.dval] = cmeta

        # Test the meta method using different input variations
        assert self.meta[self.dval].children.hasattr_case_neutral(label.upper())
        assert self.meta[self.dval].children.hasattr_case_neutral(label.lower())
        assert self.meta[self.dval].children.hasattr_case_neutral(
            label.capitalize())
        assert self.meta[self.dval].children.hasattr_case_neutral(label)
        return

    # TODO(#913): remove tests for 2D metadata
    def test_ho_meta_rename_function(self):
        """Test `meta.rename` method with ho data using a function."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        # Rename the meta variables to be all upper case, this will differ
        # from the Instrument variables, as pysat defaults to lower case
        self.meta.rename(str.upper)

        for dvar in self.testInst.vars_no_time:
            mvar = dvar.upper()

            # Test the lower order variables
            assert dvar not in self.meta.keys(), \
                "variable not renamed: {:}".format(repr(dvar))
            assert mvar in self.meta.keys(), \
                "renamed variable missing: {:}".format(repr(mvar))

            if mvar in self.meta.keys_nD():
                # Get the variable names from the children
                if hasattr(self.testInst[dvar][0], 'columns'):
                    columns = getattr(self.testInst[dvar][0], 'columns')
                else:
                    columns = [dvar]

                # Test the higher order variables
                for cvar in columns:
                    cmvar = cvar.upper()
                    assert cmvar in self.meta[mvar].children, \
                        "renamed HO variable missing: {:} ({:})".format(
                            repr(cmvar), repr(mvar))

        return

    # TODO(#913): remove tests for 2D metadata
    def test_ho_meta_rename_dict(self):
        """Test `meta.rename` method with ho data using a dict."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        # Create a renaming dictionary, which only changes up to four of the
        # variable names
        rename_dict = {dvar: dvar.upper()
                       for i, dvar in enumerate(self.testInst.vars_no_time)
                       if i < 3 or dvar == 'profiles'}
        rename_dict['profiles'] = {'density': 'DeNsItY'}

        # Rename the meta variables to be all upper case, this will differ
        # from the Instrument variables, as pysat defaults to lower case
        self.meta.rename(rename_dict)

        for dvar in self.testInst.vars_no_time:
            # Test the lower order variables
            if dvar in rename_dict.keys():
                mvar = rename_dict[dvar]

                if isinstance(mvar, dict):
                    assert dvar in self.meta.keys_nD()

                    # Get the variable names from the children
                    if hasattr(self.testInst[dvar][0], 'columns'):
                        columns = getattr(self.testInst[dvar][0], 'columns')
                    else:
                        columns = [dvar]

                    # Test the higher order variables.
                    for cvar in columns:
                        if cvar in mvar.keys():
                            cmvar = mvar[cvar]
                            assert cmvar in self.meta[dvar].children.keys(), \
                                "renamed HO variable missing: {:} ({:})".format(
                                    repr(cmvar), repr(dvar))
                        else:
                            assert cvar in self.meta[dvar].children.keys(), \
                                "unmapped HO var altered: {:} ({:})".format(
                                    repr(cvar), repr(dvar))
                else:
                    assert dvar not in self.meta.keys(), \
                        "variable not renamed: {:}".format(repr(dvar))
                    assert mvar in self.meta.keys(), \
                        "renamed variable missing: {:}".format(repr(mvar))
            else:
                mvar = dvar
                assert dvar in self.meta.keys(), \
                    "unmapped variable renamed: {:}".format(repr(dvar))

        return

    # TODO(#789): remove tests for higher order meta
    @pytest.mark.parametrize("label", ['meta_label', 'META_LABEL', 'Meta_Label',
                                       'MeTa_lAbEl'])
    def test_get_attribute_name_case_preservation_w_higher_order_list_in(self,
                                                                         label):
        """Test that get attribute names preserves the case with ho metadata.

        Parameters
        ----------
        label : str
            String label used for testing metadata

        """

        # Set a meta data variable
        self.dval = 'test_val'
        self.meta[self.dval] = self.default_val

        # Set an attribute with case in `label`
        cval = ''.join([self.dval, '21'])
        meta2 = pysat.Meta()
        meta2[cval] = {label: 'Test meta data for meta label'}

        # Attach child metadata to root meta
        dval2 = ''.join([self.dval, '2'])
        self.meta[dval2] = meta2

        # Attempt to assign to same label at root but potentially different
        # case.
        self.meta[self.dval] = {label.lower(): 'Test meta data for meta label'}

        # Create inputs and get the attribute case names
        ins = [label.upper(), label.lower(), label.capitalize(),
               label]
        outputs = self.meta.attr_case_name(ins)

        targets = [label] * len(ins)

        # Confirm original input case retained.
        assert np.all(outputs == targets)

        return

    # TODO(#789): remove tests for higher order meta
    def test_ho_data_retrieval_case_insensitive(self):
        """Test that higher order data variables are case insensitive."""

        # Initalize the meta data
        self.dval = "test_val"
        self.meta[self.dval] = self.default_val

        cmeta = pysat.Meta()
        cval = '_'.join([self.dval, 'child'])
        cmeta[cval] = self.default_val
        self.meta[self.dval] = cmeta

        # Test that the data value is present using real key and upper-case
        # version of that key
        assert self.dval in self.meta.keys()

        # Test the child variable, which should only be present through the
        # children attribute. Cannot specify keys for case-insensitive look-up.
        assert cval not in self.meta.keys()
        assert cval in self.meta[self.dval].children.keys()
        assert cval.upper() in self.meta[self.dval].children
        return


class TestMetaImmutable(TestMeta):
    """Unit tests for immutable metadata."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = None
        self.meta = pysat.Meta()
        self.mutable = False

        self.meta_labels = {'units': ('Units', str),
                            'name': ('Long_Name', str),
                            'desc': ('Desc', str),
                            'notes': ('Notes', str),
                            'min_val': ('Minimum', np.float64),
                            'max_val': ('Maximum', np.float64),
                            'fill_val': ('Fill_Value', np.float64)}
        self.dval = None
        self.default_name = ['long_name']
        self.default_nan = ['fill', 'value_min', 'value_max']
        self.default_val = {'notes': '', 'units': '', 'desc': ''}
        self.frame_list = ['dummy_frame1', 'dummy_frame2']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        del self.meta, self.meta_labels, self.default_name, self.default_nan
        del self.default_val, self.dval, self.frame_list, self.testInst
        del self.mutable
        return

    # TODO(#789): remove tests for higher order meta
    @pytest.mark.parametrize("prop,set_val", [('data', pds.DataFrame()),
                                              ('ho_data', {})])
    def test_meta_mutable_properties(self, prop, set_val):
        """Test that @properties are always mutable.

        Parameters
        ----------
        prop : str
            Attribute on `self.meta` to be tested
        set_val : any
            Value to be assigned to `prop` on `self.meta`

        """

        # Set anything that can be immutable to be immutable
        self.meta.mutable = self.mutable

        # Test that data and label values can be updated
        for prop, set_val in [('data', pds.DataFrame()), ('ho_data', {})]:
            try:
                # Pandas does not support dataframe equality
                setattr(self.meta, prop, set_val)
            except AttributeError:
                raise AssertionError(
                    "Couldn't update mutable property {:}".format(
                        prop.__repr__()))

    @pytest.mark.parametrize("label", ['units', 'name', 'desc', 'notes',
                                       'min_val', 'max_val', 'fill_val'])
    def test_meta_mutable_properties_labels(self, label):
        """Test that @properties are always mutable.

        Parameters
        ----------
        label : str
            Metadata label to be tested

        """

        # Set anything that can be immutable to be immutable
        self.meta.mutable = self.mutable

        set_val = "test value"
        setattr(self.meta.labels, label, set_val)
        assert getattr(self.meta.labels, label) == set_val
        return

    def test_meta_immutable(self):
        """Test raises AttributeError if Meta is immutable."""

        # Update Meta settings
        self.meta.mutable = self.mutable

        # Catch and test the error message
        with pytest.raises(AttributeError) as aerr:
            self.meta.hey = "this won't work."

        assert str(aerr).find("Cannot set attribute") >= 0
        return


class TestMetaMutable(object):
    """Mutable-specific Meta data unit tests."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         use_header=True)
        self.testInst.load(date=self.testInst.inst_module._test_dates[''][''])
        self.meta = self.testInst.meta
        self.meta.mutable = True

        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        del self.meta, self.testInst
        return

    def test_transfer_attr_inst_overwrite_with_strict_names(self):
        """Test `strict_names` raises AttributeError with existing Inst attr."""

        # Update the Meta and Instrument objects
        self.meta.jojo_beans = 'yep!'
        self.testInst.jojo_beans = 'nope!'

        # Catch and evaluate error message
        testing.eval_bad_input(self.meta.transfer_attributes_to_instrument,
                               AttributeError,
                               "cannot be transferred as it already exists",
                               [self.testInst], {'strict_names': True})
        return

    def test_transfer_attr_header_overwrite_with_strict_names(self):
        """Test `strict_names` raises AttributeError with existing header attr.

        """

        # Update the Meta and Instrument objects
        self.meta.jojo_beans = 'yep!'
        setattr(self.meta.header, 'jojo_beans', 'nope!')

        # Catch and evaluate error message
        testing.eval_bad_input(self.meta.transfer_attributes_to_header,
                               AttributeError,
                               "cannot be transferred as it already exists",
                               input_kwargs={'strict_names': True})
        return

    def test_transfer_attr_inst_to_instrument_strict_names_false(self):
        """Test attr transfer to Instrument with strict_names set to False."""

        # Add the same attribute with different values to Meta and Instrument
        self.meta.overwrite_attribute = 'Meta Value'
        self.testInst.overwrite_attribute = 'Inst Value'

        # Overwrite the Instrument attribute value with the meta vale
        self.meta.transfer_attributes_to_instrument(self.testInst,
                                                    strict_names=False)

        # Test the result
        assert self.testInst.overwrite_attribute == 'Meta Value'
        return

    def test_transfer_attr_inst_to_header_strict_names_false(self):
        """Test attr transfer to MetaHeader with strict_names set to False."""

        # Add the same attribute with different values to Meta and Instrument
        self.meta.overwrite_attribute = 'Meta Value'
        setattr(self.meta.header, "overwrite_attribute", 'Head Value')

        # Overwrite the Instrument attribute value with the meta vale
        self.meta.transfer_attributes_to_header(strict_names=False)

        # Test the result
        assert self.meta.header.overwrite_attribute == 'Meta Value'
        return

    def test_transfer_attributes_to_instrument(self):
        """Test transfer of custom meta attributes to Instrument."""

        # Set non-conflicting attribute
        self.meta.new_attribute = 'hello'
        self.meta.transfer_attributes_to_instrument(self.testInst)

        # Test to see if attribute was transferred successfully to Instrument
        assert hasattr(self.testInst, "new_attribute"), \
            "custom Meta attribute not transferred to Instrument."
        assert self.testInst.new_attribute == 'hello'

        # Ensure transferred attributes are removed from Meta
        assert not hasattr(self.meta, "new_attribute"), \
            "custom Meta attribute not removed during transfer to Instrument."
        return

    def test_transfer_attributes_to_header(self):
        """Test transfer of custom meta attributes to MetaHeader."""

        # Set non-conflicting attribute
        self.meta.new_attribute = 'hello'
        self.meta.transfer_attributes_to_header()

        # Test to see if attribute was transferred successfully to Instrument
        assert hasattr(self.meta.header, "new_attribute"), \
            "custom Meta attribute not transferred to Instrument."
        assert self.meta.header.new_attribute == 'hello'
        assert "new_attribute" in self.meta.header.global_attrs

        # Ensure transferred attributes are removed from Meta
        assert not hasattr(self.meta, "new_attribute"), \
            "custom Meta attribute not removed during transfer to Instrument."
        return

    def test_transfer_attributes_to_instrument_leading_underscore(self):
        """Ensure private custom meta attributes not transferred."""

        # Set standard, hidden, and private attributes
        self.meta.standard_attribute = 'hello'
        self.meta._hidden_attribute = 'is it me'
        self.meta.__private_attribute = "you're looking for"

        # Include standard parameters as well
        self.meta.transfer_attributes_to_instrument(self.testInst)

        # Test correct attachment to Instrument
        assert self.testInst.standard_attribute == 'hello'
        assert not hasattr(self.testInst, "_hidden_attribute")
        assert not hasattr(self.testInst, "__private_attribute")

        # Test correct transfer from Meta
        assert not hasattr(self.meta, "standard_attribute")
        assert self.meta._hidden_attribute == 'is it me'
        assert self.meta.__private_attribute == "you're looking for"
        return


class TestDeprecation(object):
    """Unit tests for DeprecationWarnings in the Meta class."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        self.meta = pysat.Meta()
        self.warn_msgs = []
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.meta, self.warn_msgs
        return

    def test_higher_order_meta_deprecation(self):
        """Test that setting higher order meta raises DeprecationWarning."""

        # Initialize higher-order metadata to add to the main meta object
        ho_meta = pysat.Meta()
        ho_meta['series_profiles'] = {'long_name': 'series'}

        # Raise and catch warnings
        with warnings.catch_warnings(record=True) as war:
            self.meta['series_profiles'] = {'meta': ho_meta,
                                            'long_name': 'series'}

        # Evaluate warnings
        self.warn_msgs = ["Support for higher order metadata has been"]
        self.warn_msgs = np.array(self.warn_msgs)

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        testing.eval_warnings(war, self.warn_msgs)

        return

    def test_higher_order_meta_rename_deprecation(self):
        """Test that renaming higher order meta raises DeprecationWarning."""

        # Initialize higher-order metadata to add to the main meta object
        ho_meta = pysat.Meta()
        ho_meta['series_profiles'] = {'long_name': 'series'}
        self.meta['series_profiles'] = {'meta': ho_meta,
                                        'long_name': 'series'}

        # Raise and catch warnings
        with warnings.catch_warnings(record=True) as war:
            self.meta.rename(str.upper)

        # Evaluate warnings
        self.warn_msgs = ["Support for higher order metadata has been"]
        self.warn_msgs = np.array(self.warn_msgs)

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        testing.eval_warnings(war, self.warn_msgs)

        return


class TestToDict(object):
    """Test `.to_dict` method using pysat test Instruments."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=5,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.testInst.load(date=self.stime)

        # For output
        self.out = None

        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        del self.testInst, self.stime, self.out

        return

    @pytest.mark.parametrize("preserve_case", [False, True])
    def test_to_dict(self, preserve_case):
        """Test `to_dict` method.

        Parameters
        ----------
        preserve_case : bool
            Flag passed along to `to_dict`.

        """

        self.out = self.testInst.meta.to_dict(preserve_case=preserve_case)

        # Confirm type
        assert isinstance(self.out, dict)

        # Check for higher order products
        ho_vars = []
        for var in self.testInst.meta.keys():
            if 'children' in self.testInst.meta[var]:
                if self.testInst.meta[var]['children'] is not None:
                    for subvar in self.testInst.meta[var]['children'].keys():
                        ho_vars.append('_'.join([var, subvar]))

        # Confirm the contents of the output for variables
        for var in self.out.keys():
            if var not in ho_vars:
                for label in self.out[var]:
                    assert label in self.testInst.meta.data.columns
                    assert testing.nan_equal(self.out[var][label],
                                             self.testInst.meta[var][label]), \
                        'Differing values.'

        # Confirm case
        if not preserve_case:
            # Outputs should all be lower case
            for key in self.out.keys():
                assert key == key.lower(), 'Output not lower case.'
            for key in ho_vars:
                assert key == key.lower(), 'Output not lower case.'
                assert key.lower() in self.out, 'Missing output variable.'
        else:
            # Case should be preserved
            for key in self.out.keys():
                assert key == self.testInst.meta.var_case_name(key), \
                    'Output case different.'
            for key in ho_vars:
                assert key in self.out, 'Output case different, or missing.'

        num_target_vars = len(ho_vars) + len(list(self.testInst.meta.keys()))
        assert num_target_vars == len(self.out), \
            'Different number of variables.'

        return


class TestToDictXarray(TestToDict):
    """Test `.to_dict` methods using pysat test Instruments."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         num_samples=5, use_header=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        self.testInst.load(date=self.stime)

        # For output
        self.out = None

        return


class TestToDictXarrayND(TestToDict):
    """Test `.to_dict` methods using pysat test Instruments."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'ndtesting',
                                         num_samples=5, use_header=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        self.testInst.load(date=self.stime)

        # For output
        self.out = None

        return


class TestToDictPandas2D(TestToDict):
    """Test `.to_dict` methods using pysat test Instruments."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing2d',
                                         num_samples=5, use_header=True)
        self.stime = pysat.instruments.pysat_testing2d._test_dates['']['']
        self.testInst.load(date=self.stime)

        # For output
        self.out = None

        return


class TestToDictXarrayModel(TestToDict):
    """Test `.to_dict` methods using pysat test Instruments."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testmodel',
                                         num_samples=5, use_header=True)
        self.stime = pysat.instruments.pysat_testmodel._test_dates['']['']
        self.testInst.load(date=self.stime)

        # For output
        self.out = None

        return
