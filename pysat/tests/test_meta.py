#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat Meta object."""

import logging
import netCDF4
import numpy as np
import os
import pandas as pds
import pytest
import tempfile
import warnings

import pysat
import pysat.instruments.pysat_testing
import pysat.tests.test_utils_io
from pysat.utils import testing


class TestMeta(object):
    """Basic unit tests for standard metadata operations."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""

        # Use a temporary directory so that the user's setup is not altered.
        self.tempdir = tempfile.TemporaryDirectory()
        self.saved_path = pysat.params['data_dirs']
        pysat.params['data_dirs'] = self.tempdir.name
        return

    def teardown_class(self):
        """Clean up downloaded files and parameters from tests."""

        pysat.params['data_dirs'] = self.saved_path
        self.tempdir.cleanup()
        del self.saved_path, self.tempdir
        return

    def setup(self):
        """Set up the unit test environment for each method."""

        self.testInst = None
        self.meta = pysat.Meta()

        self.meta_labels = {'units': ('Units', str),
                            'name': ('Long_Name', str),
                            'desc': ('Description', str),
                            'notes': ('Note', str),
                            'min_val': ('Minimum', np.float64),
                            'max_val': ('Maximum', np.float64),
                            'fill_val': ('Fill_Value', np.float64)}
        self.dval = None
        self.default_name = ['long_name']
        self.default_nan = ['fill', 'value_min', 'value_max']
        self.default_val = {'notes': '', 'units': '', 'desc': ''}
        self.frame_list = ['dummy_frame1', 'dummy_frame2']
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""
        del self.meta, self.meta_labels, self.default_name, self.default_nan
        del self.default_val, self.dval, self.frame_list, self.testInst
        return

    # ---------------
    # Utility methods

    def set_meta(self, inst_kwargs=None):
        """Set the `meta` and `testInst` attributes using test Instruments.

        Parameters
        ----------
        inst_kwargs : NoneType or dict
            kwargs to initialize pysat.Instrument object

        """
        if inst_kwargs is not None:
            # Load the test Instrument
            self.testInst = pysat.Instrument(**inst_kwargs)
            stime = self.testInst.inst_module._test_dates['']['']
            self.testInst.load(date=stime)

            # Save the meta object and data variable list
            self.meta = self.testInst.meta
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
                                     list(self.meta.ho_data['help'].keys()))
        testing.assert_list_contains(self.frame_list,
                                     list(self.meta['help']['children'].keys()))

        # Test the meta settings at the base and nD level
        for label in meta_dict.keys():
            if label == 'meta':
                testing.assert_lists_equal(
                    list(self.meta['help']['children'].attrs()),
                    list(meta_dict[label].attrs()))
                testing.assert_lists_equal(
                    list(self.meta['help']['children'].keys()),
                    list(meta_dict[label].keys()))

                for lvar in self.meta['help']['children'].attrs():
                    for dvar in self.meta['help']['children'].keys():
                        assert (self.meta['help']['children'][dvar, lvar]
                                == meta_dict[label][dvar, lvar]), \
                            "'help' child {:s} {:s} value {:} != {:}".format(
                                dvar, lvar,
                                self.meta['help']['children'][dvar,
                                                              lvar].__repr__(),
                                meta_dict[label][dvar, lvar].__repr__())
            else:
                assert self.meta['help']['children'].hasattr_case_neutral(label)
                assert self.meta['help', label] == meta_dict[label], \
                    "{:s} label value {:} != {:}".format(
                        label, self.meta['help', label].__repr__(),
                        meta_dict[label].__repr__())

        return

    # -----------------------
    # Test the Error messages

    def test_setting_nonpandas_metadata(self):
        """Test meta initialization with bad metadata."""

        with pytest.raises(ValueError) as verr:
            pysat.Meta(metadata='Not a Panda')

        assert str(verr).find("Input must be a pandas DataFrame type") >= 0
        return

    def test_pop_w_bad_key(self):
        """Test that a bad key will raise a KeyError for `meta.pop`."""

        with pytest.raises(KeyError) as kerr:
            self.meta.pop('not_a_key')

        assert str(kerr).find('Key not present in metadata variables') >= 0
        return

    def test_getitem_w_bad_key(self):
        """Test that a bad key will raise a KeyError in meta access."""

        with pytest.raises(KeyError) as kerr:
            self.meta['not_a_key']

        assert str(kerr).find('not found in MetaData') >= 0
        return

    def test_getitem_w_index(self):
        """Test raises NotImplementedError with an iteger index."""

        with pytest.raises(NotImplementedError) as ierr:
            self.meta[1]

        assert str(ierr).find('expected tuple, list, or str') >= 0
        return

    def test_concat_strict_w_collision(self):
        """Test raises KeyError when new meta names overlap."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Create a second object with the same data variables, but different
        # units
        concat_meta = self.meta.copy()

        # Test the error message
        with pytest.raises(KeyError) as kerr:
            self.meta.concat(concat_meta, strict=True)

        assert str(kerr).find(
            'Duplicated keys (variable names) in Meta.keys()') >= 0
        return

    def test_concat_strict_w_ho_collision(self):
        """Test raises KeyError when higher-order variable nams overlap."""

        # Set the meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing2d'})

        # Create a second object with the same higher-order data variables
        concat_meta = pysat.Meta()
        for dvar in self.meta.keys_nD():
            concat_meta[dvar] = self.meta[dvar]

        # Test the error message
        with pytest.raises(KeyError) as kerr:
            self.meta.concat(concat_meta, strict=True)

        assert str(kerr).find(
            'Duplicated keys (variable names) in Meta.keys()') >= 0
        return

    def test_multiple_meta_assignment_error(self):
        """Test that assignment of multiple metadata raises a ValueError."""

        with pytest.raises(ValueError) as verr:
            self.meta[['new', 'new2']] = {'units': ['hey', 'hey2'],
                                          'long_name': ['boo']}

        assert str(verr).find(
            'Length of data_vars and inputs must be equal') >= 0
        return

    def test_transfer_attributes_overwrite_with_strict_names(self):
        """Test raises AttributeError when overwriting with `strict_names`."""

        # Set the Meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Update the Meta and Instrument objects
        self.meta.mutable = True
        self.meta.jojo_beans = 'yep!'
        self.testInst.jojo_beans = 'nope!'

        # Catch and evaluate error message
        with pytest.raises(AttributeError) as aerr:
            self.meta.transfer_attributes_to_instrument(self.testInst,
                                                        strict_names=True)

        assert str(aerr).find("cannot be transferred as it already exists") > 0
        return

    def test_meta_immutable(self):
        """Test raises AttributeError if Meta is immutable."""

        # Update Meta settings
        self.meta.mutable = False

        # Catch and test the error message
        with pytest.raises(AttributeError) as aerr:
            self.meta.hey = "this won't work."

        assert str(aerr).find("Cannot set attribute") >= 0
        return

    def test_transfer_attributes_to_non_instrument(self):
        """Test raises ValueError when transferring custom meta to non-Inst."""

        # Set the Meta object without setting testInst
        self.meta.mutable = True
        self.meta.new_attribute = 'hello'

        # Catch and test error message
        with pytest.raises(ValueError) as verr:
            self.meta.transfer_attributes_to_instrument(self.testInst)

        assert str(verr).find("Can't transfer Meta attributes to non-") >= 0
        return

    @pytest.mark.parametrize("bad_key,bad_val,err_msg",
                             [("col_names", [], "col_names must include"),
                              ("filename", None, "Must supply an instrument"),
                              ("filename", 5, "Keyword name must be related"),
                              ("filename", 'fake_inst',
                               "Unable to create valid file path")])
    def test_meta_csv_load_w_errors(self, bad_key, bad_val, err_msg):
        """Test error handling when loading metadata from a CSV file."""

        # Initialize the bad reading inputs
        name = os.path.join(pysat.__path__[0], 'tests', 'cindi_ivm_meta.txt')
        kwargs = {'filename': name, 'na_values': [],
                  'keep_default_na': False, 'col_names': None}
        kwargs[bad_key] = bad_val

        # Raise the expected error and test the message
        with pytest.raises(ValueError) as verr:
            self.meta.from_csv(**kwargs)

        assert str(verr.value).find(err_msg) >= 0
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
                               ' missing in the Instrument'])
        assert len(war) >= 1
        assert war[0].category == UserWarning
        assert default_str in str(war[0].message)

        # Prepare to test the Metadata
        self.dval = 'int32_dummy'
        self.default_val['fill'] = -1
        self.default_val['notes'] = default_str
        self.default_nan.pop(self.default_nan.index('fill'))

        # Test the Meta settings
        self.eval_meta_settings()
        return

    # -------------------------
    # Test the logging messages

    @pytest.mark.parametrize("in_val", [1., 1, {}, None, []])
    def test_info_message_incorrect_input_meta_labels(self, in_val, caplog):
        """Test for info message when labels input not correct."""

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

    @pytest.mark.parametrize('long_str', [True, False])
    @pytest.mark.parametrize('inst_kwargs',
                             [None, {'platform': 'pysat', 'name': 'testing'},
                              {'platform': 'pysat', 'name': 'testing2d'}])
    def test_str(self, long_str, inst_kwargs):
        """Test long string output with custom meta data."""

        # Set the meta object
        self.set_meta(inst_kwargs=inst_kwargs)

        # Get the output string
        out = self.meta.__str__(long_str=long_str)

        # Evaluate the common parts of the output string
        assert out.find('pysat Meta object') >= 0
        assert out.find('standard variables') > 0
        assert out.find('ND variables') > 0

        # Evaluate the extra parts of the long output string
        if long_str:
            if inst_kwargs is not None:
                ndvar = 0
                for dvar in self.testInst.variables:
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
        """Test Meta equality for the same objecct."""

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

    @pytest.mark.parametrize("inst_name", ["testing", "testing2d",
                                           "testing2d_xarray", "testing_xarray",
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
        """Test that meta inequality for different comparison objects.

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

    @pytest.mark.parametrize('val_dict', [
        {'units': 'U', 'long_name': 'HO Val', 'radn': 'raiden'},
        {'units': 'MetaU', 'long_name': 'HO Val'}])
    def test_inequality_with_higher_order_meta(self, val_dict):
        """Test inequality with higher order metadata."""

        meta_dict = {'units': {'ho_val': 'U', 'ho_prof': 'e-'},
                     'long_name': {'ho_val': 'HO Val', 'ho_prof': 'HO Profile'}}

        # Set the default meta object
        self.meta['ho_data'] = pysat.Meta(pds.DataFrame(meta_dict))

        # Set the altrered meta object
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
        """Test that meta equality works without copy."""

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

    @pytest.mark.parametrize("inst_name", ["testing", "testing2d",
                                           "testing2d_xarray", "testing_xarray",
                                           "testmodel"])
    def test_pop(self, inst_name):
        """Test meta attributes are retained when extracted using pop."""

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': inst_name})

        # Pop each of the data variables
        for dvar in self.testInst.variables:
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
            if isinstance(self.meta.labels.label_type[mattr], str) else -47
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
                if isinstance(self.meta.labels.label_type[mattr], str) else -47
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

    @pytest.mark.parametrize('inst_name', ['testing', 'testing2d'])
    @pytest.mark.parametrize('num_mvals', [0, 1, 3])
    @pytest.mark.parametrize('num_dvals', [0, 1, 3])
    def test_selected_meta_retrieval(self, inst_name, num_mvals, num_dvals):
        """Test metadata retrieval using various restrictions.

        Parameters
        ----------
        num_mvals : int
            Number of meta attributes to retrieve
        num_dvals : int
            Number of data values to retrieve

        """

        # Set the meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': inst_name})

        # Get the selection criteria
        dvals = list(self.testInst.variables[:num_dvals])
        mvals = [getattr(self.meta.labels, mattr)
                 for mattr in list(self.meta_labels.keys())[:num_mvals]]

        # If dvals is greater than zero and there is higher order data,
        # make sure at least one is included
        nd_inds = list()
        if len(dvals) > 0:
            nd_vals = [key for key in self.meta.keys_nD()]

            if len(nd_vals) > 0:
                for val in nd_vals:
                    if val in dvals:
                        nd_inds.append(dvals.index(val))
    
                if len(nd_inds) == 0:
                    dvals[0] = nd_vals[0]
                    nd_inds = [0]

                if len(mvals) > 0:
                    mvals[0] = 'children'
                    

        # Retrieve meta data for desired values
        sel_meta = self.meta[dvals, mvals]

        # Evaluate retrieved data
        assert isinstance(sel_meta, pds.DataFrame)
        testing.assert_lists_equal(dvals, list(sel_meta.index))
        testing.assert_lists_equal(mvals, list(sel_meta.columns))

        # If there is higher order data, test the retrieval
        if len(nd_inds) > 0:
            warnings.warn(''.join(['TODO: Higher order data cannot be ',
                                   'retrieved in batches']))
            
        return

    def test_replace_meta(self):
        """Test replacement of metadata units."""

        # Set the meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': "testing"})

        # Change the meta and update the evaluation data
        self.dval = self.testInst.variables[0]

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
                    # Because no type was specified for this label,
                    # it defaults to float with a fill value of NaN
                    # regardless of the values it is set to.
                    assert np.isnan(self.meta[dval, mlabel]), \
                        "Custom label set after init didn't default to NaN"
                else:
                    assert self.meta[dval, mlabel] == meta_dict[mlabel], \
                        "{:} label has unexpected value ({:} != {:})".format(
                            dval.__repr__(), self.meta[dval, mlabel].__repr__(),
                            meta_dict[mlabel].__repr__())
        return

    def test_meta_immutable_at_instrument_instantiation(self):
        """Test that meta is immutable at instrument Instantiation."""

        # Set the Meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Test the default value for `mutable`
        assert self.meta.mutable is False, \
            "Meta `mutable` attribute initialized to the wrong value."

        return

    def test_transfer_attributes_to_instrument(self):
        """Test transfer of custom meta attributes."""

        # Set the Meta object
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})
        self.meta.mutable = True

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
        for dval in self.testInst.variables:
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
        """Test Meta initialization with data."""

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
        """Test string assignment to meta with a list of strings."""

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

    def test_inst_data_assign_meta_empty_list(self):
        """Test meta assignment from empty list."""

        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})
        self.testInst['help'] = {'data': self.testInst['mlt'],
                                 'units': [],
                                 'long_name': 'The Doors'}
        assert self.testInst.meta['help', 'units'] == ''
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

    def test_transfer_attributes_to_instrument_leading_underscore(self):
        """Ensure private custom meta attributes not transferred."""

        # Set meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})
        self.meta.mutable = True

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

    def test_transfer_attributes_to_instrument_strict_names_false(self):
        """Test attr transfer with strict_names set to False."""

        # Set meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})
        self.meta.mutable = True

        # Add the same attribute with different values to Meta and Instrument
        self.meta.overwrite_attribute = 'Meta Value'
        self.testInst.overwrite_attribute = 'Inst Value'

        # Overwrite the Instrument attribute value with the meta vale
        self.meta.transfer_attributes_to_instrument(self.testInst,
                                                    strict_names=False)

        # Test the result
        assert self.testInst.overwrite_attribute == 'Meta Value'
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
        self.dval = self.testInst.variables[:num_drop]
        testing.assert_list_contains(self.dval,
                                     [val for val in self.meta.keys()])

        # Drop the values
        self.meta.drop(self.dval)

        # Test the successful deletion
        meta_vals = [val for val in self.meta.keys()]

        assert len(meta_vals) == len(self.testInst.variables) - num_drop
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
        self.dval = self.testInst.variables[:num_keep]
        testing.assert_list_contains(self.dval,
                                     [val for val in self.meta.keys()])

        # Drop the values
        self.meta.keep(self.dval)

        # Test the successful deletion of unspecified values
        testing.assert_lists_equal(self.dval, [val for val in self.meta.keys()])
        return

    @pytest.mark.parametrize('use_method', [True, False])
    def test_nan_metadata_filtered_netcdf4(self, use_method):
        """Test that metadata set to NaN is excluded from netCDF output.

        Parameters
        ----------
        use_method : bool
            Use meta method and `export_nan` kwarg if True, use defaults
            if False

        """
        # TODO: consider moving to class with netCDF tests

        # Create an instrument object that has a meta with some
        # variables allowed to be nan within metadata when exporting
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Create new variable
        self.testInst['test_nan_variable'] = 1.0

        # Assign additional metadata
        self.testInst.meta['test_nan_variable'] = {'test_nan_export': np.nan}

        # Get the export kwarg and set the evaluation data
        if use_method:
            # Keep a non-standard set of NaN meta labels in the file
            present = self.testInst.meta._export_nan
            missing = [present.pop()]
            present.append('test_nan_export')
            export_nan = list(present)
        else:
            # Keep the standard set of NaN meta labels in the file
            export_nan = None
            present = self.testInst.meta._export_nan
            missing = ['test_nan_export']
        
        # Write the file
        pysat.tests.test_utils_io.prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.to_netcdf4(outfile, export_nan=export_nan)

        # Load file back and test metadata is as expected
        with netCDF4.Dataset(outfile) as open_f:
            test_vars = open_f['test_nan_variable'].ncattrs()

        testing.assert_list_contains(present, test_vars)

        for mvar in missing:
            assert mvar not in test_vars, \
                '{:} was written to the netCDF file'.format(mvar.__repr__())

        return

    # -------------------------------
    # Tests for higher order metadata

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
        """Test the assignment of the higher order metadata."""

        # Initialize the Meta data
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})

        # Alter the Meta data
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        inst_data = [frame for i in range(self.testInst.index.shape[0])]

        if meta_dict is None:
            self.testInst['help'] = inst_data
            meta_dict = {'units': '', 'long_name': 'help', 'desc': ''}
        else:
            meta_dict.update({'data': inst_data})
            self.testInst['help'] = meta_dict

            if 'data' in meta_dict.keys():
                del meta_dict['data']

        self.meta = self.testInst.meta

        # Test the ND metadata results
        self.eval_ho_meta_settings(meta_dict)
        return

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

        # Assign the metadata
        self.testInst['help'] = meta_dict

        # Alter the data
        self.testInst['help'] = inst_data

        # Test the ND metadata results
        self.meta = self.testInst.meta
        self.eval_ho_meta_settings(meta_dict)
        return

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

    def test_inst_assign_from_meta_w_ho(self):
        """Test assignment to Instrument from Meta with higher order data."""
        # I DON'T THINK THIS TEST DOES ANYTHING NEW, WHY IS IT HERE?

        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        self.meta = pysat.Meta()
        self.meta['dummy_frame1'] = {'units': 'A'}
        self.meta['dummy_frame2'] = {'desc': 'nothing'}
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'long_name': 'The Doors',
                                 'meta': self.meta}
        self.testInst['help2'] = self.testInst['help']
        self.testInst.meta['help2'] = self.testInst.meta['help']

        assert self.testInst.meta['help'].children['dummy_frame1',
                                                   'units'] == 'A'
        assert self.testInst.meta['help2', 'long_name'] == 'The Doors'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help']['children'])
        for label in ['units', 'desc']:
            assert self.testInst.meta['help']['children'].hasattr_case_neutral(
                label)

        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'desc'] == ''
        assert self.testInst.meta['help2']['children']['dummy_frame2',
                                                       'desc'] == 'nothing'
        assert 'children' not in self.testInst.meta.data.columns
        return

    def test_inst_assign_from_meta_w_ho_then_update(self):
        """Test assign `Instrument.meta` from separate Meta with HO data."""
        # I ALSO DON'T THINK THIS TEST DOES ANYTHING THAT HASN'T BEEN TESTED
        self.set_meta(inst_kwargs={'platform': 'pysat', 'name': 'testing'})
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        self.meta = pysat.Meta()
        self.meta['dummy_frame1'] = {'units': 'A'}
        self.meta['dummy_frame2'] = {'desc': 'nothing'}
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'name': 'The Doors',
                                 'meta': self.meta}
        self.testInst['help2'] = self.testInst['help']
        self.testInst.meta['help2'] = self.testInst.meta['help']
        new_meta = self.testInst.meta['help2'].children
        new_meta['dummy_frame1'] = {'units': 'Amps', 'desc': 'something',
                                    'label': 'John Wick'}
        self.testInst.meta['help2'] = new_meta
        self.testInst.meta['help2'] = {'label': 'The Doors Return'}

        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'units'] == 'A'
        assert self.testInst.meta['help2', 'name'] == 'The Doors'
        assert self.testInst.meta['help2', 'label'] == 'The Doors Return'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help2'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help2']['children'])
        for label in ['units', 'desc']:
            assert self.testInst.meta['help2']['children'].hasattr_case_neutral(
                label)

        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'desc'] == 'something'
        assert self.testInst.meta['help2']['children']['dummy_frame2',
                                                       'desc'] == 'nothing'
        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'units'] == 'Amps'
        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'label'] == 'John Wick'
        assert 'children' not in self.testInst.meta.data.columns
        return

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
                # TODO: Isssue #911 will either fix this or require warning test
                assert self.meta[dvar].children[
                    cvar, self.meta.labels.units].find('Updated') < 0
        return

    # HERE
    def test_assign_higher_order_meta(self):
        """Test assign higher order metadata."""

        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = meta
        return

    def test_assign_higher_order_meta_from_dict(self):
        """Test assign higher order metadata from dict."""

        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = {'meta': meta}
        assert self.meta['higher'].children == meta
        return

    def test_assign_higher_order_meta_from_dict_w_multiple(self):
        """Test assign higher order metadata from dict with multiple types."""

        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta[['higher', 'lower']] = {'meta': [meta, None],
                                          'units': [None, 'boo'],
                                          'long_name': [None, 'boohoo']}
        assert self.meta['lower'].units == 'boo'
        assert self.meta['lower'].long_name == 'boohoo'
        assert self.meta['higher'].children == meta
        return

    def test_assign_higher_order_meta_from_dict_w_multiple_2(self):
        """Test assign higher order metadata from dict with multiple types."""

        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta[['higher', 'lower', 'lower2']] = \
            {'meta': [meta, None, meta],
             'units': [None, 'boo', None],
             'long_name': [None, 'boohoo', None]}
        assert self.meta['lower'].units == 'boo'
        assert self.meta['lower'].long_name == 'boohoo'
        assert self.meta['higher'].children == meta
        return

    def test_create_new_metadata_from_old(self):
        """Test create new metadata from old metadata."""

        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta[['higher', 'lower', 'lower2']] = \
            {'meta': [meta, None, meta],
             'units': [None, 'boo', None],
             'long_name': [None, 'boohoo', None],
             'fill': [1, 1, 1],
             'value_min': [0, 0, 0],
             'value_max': [1, 1, 1]}
        meta2 = pysat.Meta(metadata=self.meta.data)
        m1 = meta2['lower']
        m2 = self.meta['lower']
        assert m1['children'] is None
        assert m2['children'] is None
        for key in m1.index:
            if key not in ['children']:
                assert m1[key] == m2[key]
        # make sure both have the same indexes
        assert np.all(m1.index == m2.index)
        return

    def test_replace_meta_units_list(self):
        """Test replace metadata units as a list."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta[['new2', 'new']] = {'units': ['yeppers', 'yep']}
        assert self.meta['new'].units == 'yep'
        assert self.meta['new'].long_name == 'boo'
        assert self.meta['new2'].units == 'yeppers'
        assert self.meta['new2'].long_name == 'boo2'
        return

    # assign multiple values to default
    def test_multiple_input_names_null_value(self):
        """Test setting multiple input names to null."""

        self.meta[['test1', 'test2']] = {}
        assert self.meta['test1', 'units'] == ''
        assert self.meta['test2', 'long_name'] == 'test2'
        return

    def test_multiple_input_names_null_value_preexisting_values(self):
        """Test setting multiple input names to null w/ pre-existing values."""

        self.meta[['test1', 'test2']] = {'units': ['degrees', 'hams'],
                                         'long_name': ['testing', 'further']}
        self.meta[['test1', 'test2']] = {}
        assert self.meta['test1', 'units'] == 'degrees'
        assert self.meta['test2', 'long_name'] == 'further'
        return

    # test behaviors related to case changes
    def test_assign_capitalized_labels(self):
        """Test assignment of capitalized label names."""

        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'Units': 'hey', 'Long_Name': 'boo'}
        self.meta['new2'] = {'Units': 'hey2', 'Long_Name': 'boo2'}

        assert (self.meta['new'].Units == 'hey')
        assert (self.meta['new'].Long_Name == 'boo')
        assert (self.meta['new2'].Units == 'hey2')
        assert (self.meta['new2'].Long_Name == 'boo2')
        return

    def test_get_Units_wrong_case(self):
        """Test that getting Units works if the case is wrong."""

        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'Units': 'hey', 'Long_Name': 'boo'}
        self.meta['new2'] = {'Units': 'hey2', 'Long_Name': 'boo2'}

        assert (self.meta['new', 'units'] == 'hey')
        assert (self.meta['new', 'long_name'] == 'boo')
        assert (self.meta['new2', 'units'] == 'hey2')
        assert (self.meta['new2', 'long_name'] == 'boo2')
        return

    def test_set_Units_wrong_case(self):
        """Test that setting Units works if the case is wrong."""

        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}

        assert self.meta['new'].Units == 'hey'
        assert self.meta['new'].Long_Name == 'boo'
        assert self.meta['new2'].Units == 'hey2'
        assert self.meta['new2'].Long_Name == 'boo2'
        return

    def test_repeated_set_Units_wrong_case(self):
        """Test that setting Units repeatedly works if the case is wrong."""

        self.meta = pysat.Meta(labels=self.meta_labels)
        for i in np.arange(10):
            self.meta['new'] = {'units': 'hey%d' % i, 'long_name': 'boo%d' % i}
            self.meta['new_%d' % i] = {'units': 'hey%d' % i,
                                       'long_name': 'boo%d' % i}

        for i in np.arange(10):
            self.meta['new_5'] = {'units': 'hey%d' % i,
                                  'long_name': 'boo%d' % i}
            self.meta['new_%d' % i] = {'units': 'heyhey%d' % i,
                                       'long_name': 'booboo%d' % i}

        assert self.meta['new'].Units == 'hey9'
        assert self.meta['new'].Long_Name == 'boo9'
        assert self.meta['new_9'].Units == 'heyhey9'
        assert self.meta['new_9'].Long_Name == 'booboo9'
        assert self.meta['new_5'].Units == 'hey9'
        assert self.meta['new_5'].Long_Name == 'boo9'
        return

    def test_contains_case_insensitive(self):
        """Test that labels are case insensitive for keys in meta."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        assert ('new2' in self.meta)
        assert ('NEW2' in self.meta)
        return

    def test_contains_case_insensitive_w_ho(self):
        """Test that labels are case insensitive for keys in ho meta."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['new21'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta['new2'] = meta2
        assert ('new2' in self.meta)
        assert ('NEW2' in self.meta)
        assert ('new21' not in self.meta)
        assert ('NEW21' not in self.meta)
        return

    def test_get_variable_name_case_preservation(self):
        """Test `meta.var_case_name` preserves the required output case."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['NEW2'] = {'units': 'hey2', 'long_name': 'boo2'}

        assert ('NEW2' == self.meta.var_case_name('new2'))
        assert ('NEW2' == self.meta.var_case_name('nEw2'))
        assert ('NEW2' == self.meta.var_case_name('neW2'))
        assert ('NEW2' == self.meta.var_case_name('NEW2'))
        return

    def test_get_attribute_name_case_preservation(self):
        """Test that meta labels and values preserve the input case."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['NEW2'] = {'units': 'hey2', 'long_name': 'boo2',
                             'YoYoYO': 'yolo'}
        self.meta['new'] = {'yoyoyo': 'YOLO'}

        assert (self.meta.attr_case_name('YoYoYo') == 'YoYoYO')
        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['new', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2', 'YoYoYO'] == 'yolo')
        return

    def test_get_attribute_name_case_preservation_w_higher_order(self):
        """Test that get attribute names preserves the case with ho metadata."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['NEW2'] = meta2
        self.meta['new'] = {'yoyoyo': 'YOLO'}

        assert (self.meta.attr_case_name('YoYoYo') == 'YoYoYO')
        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['new', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2'].children['new21', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2'].children['new21', 'YoYoYO'] == 'yolo')
        assert (self.meta['new2'].children.attr_case_name('YoYoYo')
                == 'YoYoYO')
        return

    def test_get_attribute_name_case_preservation_w_higher_order_2(self):
        """Test that get attribute names preserves the case with ho metadata."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['NEW2'] = meta2
        self.meta['NEW'] = {'yoyoyo': 'YOLO'}

        assert (self.meta.attr_case_name('YoYoYo') == 'YoYoYO')
        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['NEW', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2'].children['new21', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2'].children['new21', 'YoYoYO'] == 'yolo')
        assert (self.meta['new2'].children.attr_case_name('YoYoYo')
                == 'YoYoYO')
        return

    def test_get_attribute_name_case_preservation_w_ho_reverse_order(self):
        """Test that getting attribute names preserves the case in reverse."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['new'] = {'yoyoyo': 'YOLO'}
        self.meta['NEW2'] = meta2

        assert (self.meta.attr_case_name('YoYoYo') == 'yoyoyo')
        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['new', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2'].children['new21', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2'].children['new21', 'YoYoYO'] == 'yolo')
        assert (self.meta['new2'].children.attr_case_name('YoYoYo')
                == 'yoyoyo')
        return

    def test_has_attr_name_case_preservation_w_ho_reverse_order(self):
        """Test that has_attr_name preserves the case with ho in reverse."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['new'] = {'yoyoyo': 'YOLO'}
        self.meta['NEW2'] = meta2

        assert (self.meta.hasattr_case_neutral('YoYoYo'))
        assert (self.meta.hasattr_case_neutral('yoyoyo'))
        assert not (self.meta.hasattr_case_neutral('YoYoYyo'))
        return

    def test_has_attr_name_case_preservation_w_higher_order(self):
        """Test that has_attr_name preserves the case with higher order."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['NEW2'] = meta2

        assert not (self.meta.hasattr_case_neutral('YoYoYo'))
        assert not (self.meta.hasattr_case_neutral('yoyoyo'))
        assert not (self.meta.hasattr_case_neutral('YoYoYyo'))
        return

    # check support on case preservation, but case insensitive
    def test_replace_meta_units_list_weird_case(self):
        """Test that replacing meta units is case independent."""

        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta[['NEW2', 'new']] = {'units': ['yeppers', 'yep']}

        assert (self.meta['new'].units == 'yep')
        assert (self.meta['new'].long_name == 'boo')
        assert (self.meta['new2'].units == 'yeppers')
        assert (self.meta['new2'].long_name == 'boo2')
        return

    def test_meta_mutable_properties(self):
        """Test that @properties are always mutable."""

        self.meta = pysat.Meta()
        self.meta.mutable = False
        self.meta.data = pds.DataFrame()
        self.meta.ho_data = {}
        self.meta.labels.units = 'nT'
        self.meta.labels.name = 'my name'
        return


class TestMetaImmutable(TestMeta):
    """Unit tests for immutable metadata."""

    def setup(self):
        """Set up the unit test environment for each method."""

        # Instrument object and disable mutability
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean')
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.meta = self.testInst.meta
        self.meta.mutable = False
        self.meta_labels = {'units': ('Units', str),
                            'name': ('Long_Name', str)}

        # Assign remaining values
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
