#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Classes for storing and managing meta data."""

from copy import deepcopy
import numpy as np
import os
import pandas as pds
import warnings

import pysat
import pysat.utils._core as core_utils
from pysat.utils import testing


class Meta(object):
    """Store metadata for the Instrument and Constellation classes.

    Parameters
    ----------
    metadata : pandas.DataFrame
        DataFrame should be indexed by variable name that contains at minimum
        the standard_name (name), units, and long_name for the data stored in
        the associated pysat Instrument object.
    header_data : dict or NoneType
        Global meta data to be assigned to the header attribute.  Keys denote
        the desired attribute names and values the metadata for that attribute.
        (default=None)
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', float), 'max_val': ('value_max', float),
        'fill_val': ('fill', float)})
    export_nan : list or NoneType
        List of labels that should be exported even if their value is NaN or
        None for an empty list. When used, metadata with a value of NaN will
        be excluded from export. Will always allow NaN export for labels of
        the float type. (default=None)

    Attributes
    ----------
    data : pandas.DataFrame
        Index is variable standard name, 'units', 'long_name', and other
        defaults are also stored along with additional user provided labels.
    labels : MetaLabels
        Labels for MetaData attributes
    mutable : bool
        If True, attributes directly attached to Meta are modifiable
    header : MetaHeader
        Class containing global metadata

    Note
    ----
    Meta object preserves the case of variables and attributes as it first
    receives the data. Subsequent calls to set new metadata with the same
    variable or attribute will use case of first call. Accessing or setting
    data thereafter is case insensitive. In practice, use is case insensitive
    but the original case is preserved. Case preseveration is built in to
    support writing files with a desired case to meet standards.

    Metadata for higher order data objects, those that have
    multiple products under a single variable name in a `pysat.Instrument`
    object, are stored by providing a Meta object under the single name.

    Supports any custom metadata values in addition to the expected metadata
    attributes (units, name, notes, desc, value_min, value_max, and fill).
    These base attributes may be used to programatically access and set types
    of metadata regardless of the string values used for the attribute. String
    values for attributes may need to be changed depending upon the standards
    of code or files interacting with pysat.

    Meta objects returned as part of pysat loading routines are automatically
    updated to use the same values of units, etc. as found in the
    `pysat.Instrument` object.

    Meta objects have a structure similar to the CF-1.6 netCDF data standard.

    Examples
    --------
    ::

        # Instantiate Meta object, default values for attribute labels are used
        meta = pysat.Meta()

        # Set several variable units. Note that other base parameters are not
        # set below, and so will be assigned a default value.
        meta['var_name'] = {meta.labels.name: 'Variable Name',
                            meta.labels.units: 'MegaUnits'}

        # Update only 'units' to new value.  You can use the value of
        # `meta.labels.units` instead of the class attribute, as was done in
        # the above example.
        meta['var_name'] = {'units': 'MU'}

        # Custom meta data variables may be assigned using the same method.
        # This example uses non-standard meta data variables 'scale', 'PI',
        # and 'axis_multiplier'.  You can include or not include any of the
        # standard meta data information.
        meta['var_name'] = {'units': 'MU', 'long_name': 'Variable Name',
                            'scale': 'linear', 'axis_multiplier': 1e4}
        meta['var_name'] = {'PI': 'Dr. R. Song'}

        # Meta data may be assigned to multiple variables at once
        meta[['var_name1', 'var_name2']] = {'long_name': ['Name1', 'Name2'],
                                            'units': ['Units1', 'Units2'],
                                            'scale': ['linear', 'linear']}

        # Sometimes n-Dimensional (nD) variables require multi-dimensional
        # meta data structures.
        meta2 = pysat.Meta()
        meta2['var_name41'] = {'long_name': 'name1of4', 'units': 'Units1'}
        meta2['var_name42'] = {'long_name': 'name2of4', 'units': 'Units2'}
        meta['var_name4'] = {'meta': meta2}

        # An alternative method to achieve the same result is:
        meta['var_name4'] = meta2
        meta['var_name4'].children['name41']
        meta['var_name4'].children['name42']

        # You may, of course, have a mixture of 1D and nD data
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        meta2 = pysat.Meta()
        meta2[['higher', 'lower']] = {'meta': [meta, None],
                                      'units': [None, 'boo'],
                                      'long_name': [None, 'boohoo']}

        # Meta data may be assigned from another Meta object using dict-like
        # assignments
        key1 = 'var_name'
        key2 = 'var_name4'
        meta[key1] = meta2[key2]

        # When accessing one meta data value for any data variable, first use
        # the data variable and then the meta data label.
        meta['var_name', 'fill']

        # A more robust method is to use the available Meta variable attributes
        # in the attached MetaLabels class object.
        meta[key1, meta.labels.fill_val]

        # You may change a label used by Meta object to have a different value
        meta.labels.fill_val = '_FillValue'

        # Note that the fill label is intended for use when interacting
        # with external files. Thus, any fill values (NaN) within the Meta
        # object are not updated when changing the metadata string label,
        # or when updating the value representing fill data. A future update
        # (Issue #707) will expand functionality to include these custom
        # fill values when producing files.

    """

    # -----------------------------------------------------------------------
    # Define the magic methods

    def __init__(self, metadata=None, header_data=None,
                 labels={'units': ('units', str), 'name': ('long_name', str),
                         'notes': ('notes', str), 'desc': ('desc', str),
                         'min_val': ('value_min', float),
                         'max_val': ('value_max', float),
                         'fill_val': ('fill', float)}, export_nan=None):
        """Initialize `pysat.Meta` object."""
        # Set mutability of Meta attributes.  This flag must be set before
        # anything else, or `__setattr__` breaks.
        self.mutable = True

        # Set the global meta data
        self.header = MetaHeader(header_data)

        # Set the NaN export list
        self._export_nan = [] if export_nan is None else export_nan
        for lvals in labels.values():
            if lvals[0] not in self._export_nan and lvals[1] == float:
                self._export_nan.append(lvals[0])

        # Set the labels
        self.labels = MetaLabels(metadata=self, **labels)

        # Initialize higher order (nD) data structure container, a dict
        self._ho_data = {}

        # Use any user provided data to instantiate object with data.
        # Attributes unit and name labels are called within.
        if metadata is not None:
            if isinstance(metadata, pds.DataFrame):
                self._data = metadata

                # Make sure defaults are taken care of for required metadata
                self.accept_default_labels(self)
            else:
                raise ValueError(''.join(('Input must be a pandas DataFrame ',
                                          'type. See other constructors for ',
                                          'alternate inputs.')))
        else:
            columns = [getattr(self.labels, mlab)
                       for mlab in self.labels.label_type.keys()]
            self._data = pds.DataFrame(None, columns=columns)

        # Establish attributes intrinsic to object, before user can add any
        self._base_attr = dir(self)

    def __repr__(self):
        """Print a representation of the Meta instantiation callable by `eval`.

        Returns
        -------
        out_str : str
            Simply formatted output string

        """
        nvar = len([kk for kk in self.keys()])
        out_str = ''.join(['pysat.Meta(metadata=', repr(self._data),
                           ', header_data=', repr(self.header), ', labels=',
                           repr(self.labels), ', export_nan=',
                           repr(self._export_nan),
                           ') -> {:d} Variables'.format(nvar)])
        return out_str

    def __str__(self, long_str=True):
        """Print Meta instance, variables, and attributes.

        Parameters
        ----------
        long_str : bool
            Return short version if False and long version if True
            (default=True)

        Returns
        -------
        out_str : str
            Nicely formatted output string

        """
        # Get the desired variables as lists
        labs = [var for var in self.attrs()]
        vdim = [var for var in self.keys() if var not in self.keys_nD()]
        nchild = {var: len([kk for kk in self[var]['children'].keys()])
                  for var in self.keys_nD()}
        ndim = ["{:} -> {:d} children".format(var, nchild[var])
                for var in self.keys_nD()]

        # Get the lengths of each list
        nlabels = len(labs)
        nvdim = len(vdim)
        nndim = len(ndim)

        # Print the short output
        out_str = "pysat Meta object\n"
        out_str += "-----------------\n"
        out_str += "Tracking {:d} metadata values\n".format(nlabels)
        out_str += "Metadata for {:d} standard variables\n".format(nvdim)
        out_str += "Metadata for {:d} ND variables\n".format(nndim)

        # Print the global meta data. `max_num` should be divisible by 2 and
        # `ncol`.
        max_num = 6 if long_str else 0
        out_str += self.header.__str__(max_num_display=max_num)

        # Print the longer output
        if long_str:
            # Print all the metadata labels
            out_str += "\n{:s}".format(self.labels.__str__())

            # Print a subset of the metadata variables, divided by order
            ncol = 3
            if nvdim > 0:
                out_str += "\nStandard Metadata variables:\n"
                out_str += core_utils.fmt_output_in_cols(vdim, ncols=ncol,
                                                         max_num=max_num)
            if nndim > 0:
                out_str += "\nND Metadata variables:\n"
                out_str += core_utils.fmt_output_in_cols(ndim, ncols=ncol,
                                                         max_num=max_num)

        return out_str

    def __setattr__(self, name, value):
        """Conditionally set attributes based on `self.mutable` flag.

        Parameters
        ----------
        name : str
            Attribute name to be assigned to Meta
        value : str or boolean
            String to be assigned to attribute specified by name or boolean
            if name is 'mutable'

        Note
        ----
        @properties are assumed to be mutable.

        We avoid recursively setting properties using
        method from https://stackoverflow.com/a/15751135

        """
        # Mutable handled explicitly to avoid recursion
        if name != 'mutable':

            # Check if this attribute is a property
            propobj = getattr(self.__class__, name, None)
            if isinstance(propobj, property):
                # Check if the property is settable
                if propobj.fset is None:
                    raise AttributeError(''.join("can't set attribute  ",
                                                 name, " to ", value, ", ",
                                                 "property has no fset"))

                # Make self mutable in case `fset` needs it to be
                mutable_tmp = self.mutable
                self.mutable = True

                # Set the property
                propobj.fset(self, value)

                # Restore mutability flag
                self.mutable = mutable_tmp
            else:
                # A normal attribute
                if self.mutable:
                    # Use Object to avoid recursion
                    super(Meta, self).__setattr__(name, value)
                else:
                    estr = ' '.join(("Cannot set attribute", name, "to {val!s}",
                                     "since the Meta object attributes are",
                                     "set to immutable.")).format(val=value)
                    raise AttributeError(estr)
        else:
            super(Meta, self).__setattr__(name, value)

    def __setitem__(self, data_vars, input_dat):
        """Add metadata.

        Parameters
        ----------
        data_vars : str, list
            Data variable names for the input metadata
        input_dat : dict, pds.Series, or Meta
            Input metadata to be assigned

        """

        input_data = deepcopy(input_dat)

        if isinstance(input_data, dict):
            # If not passed an iterable, make it one
            if isinstance(data_vars, str):
                data_vars = [data_vars]
                for key in input_data:
                    input_data[key] = [input_data[key]]
            elif isinstance(data_vars, slice) and (data_vars.step is None):
                # Using instrument[indx, :] or instrument[idx],
                # which means all variables are at issue.
                data_vars = [dkey for dkey in self.data.keys()]

            # Make sure the variable names are in good shape.  The Meta object
            # is case insensitive, but case preserving. Convert given data_vars
            # into ones Meta has already seen. If new, then input names
            # become the standard.
            data_vars = self.var_case_name(data_vars)
            meta_vars = list(self.keys())
            def_vars = list()
            for var in data_vars:
                if var not in meta_vars:
                    def_vars.append(var)
            if len(def_vars) > 0:
                self._insert_default_values(def_vars)

            # Check if input dict empty.  If so, no metadata was assigned by
            # the user.  This is an empty call and we can head out,
            # since defaults have been assigned.
            if len(input_data.keys()) == 0:
                return

            # Perform some checks on the data and make sure number of inputs
            # matches number of metadata inputs.
            for dkey in input_data:
                if len(data_vars) != len(input_data[dkey]):
                    raise ValueError(''.join(('Length of data_vars and inputs',
                                              ' must be equal.')))

            # Make sure the attribute names are in good shape.  Check the
            # attribute's name against existing attribute names.  If the
            # attribute name exists somewhere, then the case of the existing
            # attribute will be enforced upon new data by default for
            # consistency.
            input_keys = [ikey for ikey in input_data]
            new_names = self.attr_case_name(input_keys)
            for iname, new_name in zip(input_keys, new_names):
                if new_name != iname:
                    input_data[new_name] = input_data.pop(iname)

            # Time to actually add the metadata
            for ikey in input_data:
                if ikey not in ['children', 'meta']:
                    for i, var in enumerate(data_vars):
                        to_be_set = input_data[ikey][i]
                        good_set = True

                        # See if this meta data key has already been defined
                        # in MetaLabels
                        if ikey in self.labels.label_attrs.keys():
                            iattr = self.labels.label_attrs[ikey]
                            if not isinstance(
                                    to_be_set, self.labels.label_type[iattr]):
                                # If this is a disagreement between byte data
                                # and an expected str, resolve it here
                                if(isinstance(to_be_set, bytes)
                                   and self.labels.label_type[iattr] == str):
                                    to_be_set = core_utils.stringify(to_be_set)
                                else:
                                    # This type is incorrect, try casting it
                                    wmsg = ''.join(['Metadata with type ',
                                                    repr(type(to_be_set)),
                                                    ' does not match expected ',
                                                    'type ',
                                                    repr(self.labels.label_type[
                                                        iattr])])
                                    try:
                                        if hasattr(to_be_set, '__iter__'):
                                            if self.labels.label_type[
                                                    iattr] == str:
                                                to_be_set = '\n\n'.join(
                                                    [str(tval) for tval in
                                                     to_be_set])
                                            else:
                                                raise TypeError("can't recast")
                                        else:
                                            to_be_set = self.labels.label_type[
                                                iattr](to_be_set)

                                        # Inform user data was recast
                                        pysat.logger.info(''.join((
                                            wmsg, '. Recasting input for ',
                                            repr(var), ' with key ',
                                            repr(ikey))))
                                    except (TypeError, ValueError):
                                        # Warn user data was dropped
                                        warnings.warn(''.join((
                                            wmsg, '. Dropping input for ',
                                            repr(var), ' with key ',
                                            repr(ikey))))
                                        good_set = False
                        else:
                            # Extend the meta labels. Ensure the attribute
                            # name has no spaces and that bytes are used instead
                            # of strings.
                            iattr = ikey.replace(" ", "_")
                            itype = type(to_be_set)
                            if itype == bytes:
                                itype = str

                            # Update the MetaLabels object and the existing
                            # metadata to ensure all data have all labels
                            self.labels.update(iattr, ikey, itype)
                            self._label_setter(ikey, ikey, type(to_be_set))

                        # Set the data
                        if good_set:
                            self._data.loc[var, ikey] = to_be_set
                else:
                    # Key is 'meta' or 'children', providing higher order
                    # metadata. Meta inputs could be part of a larger multiple
                    # parameter assignment, so not all names may actually have
                    # a 'meta' object to add.
                    for item, val in zip(data_vars, input_data['meta']):
                        if val is not None:
                            # Assign meta data, using a recursive call...
                            # Heads to if Meta instance call.
                            self[item] = val

        elif isinstance(input_data, pds.Series):
            # Outputs from Meta object are a Series. Thus, this takes in input
            # from a Meta object. Set data using standard assignment via a dict.
            in_dict = input_data.to_dict()
            if 'children' in in_dict:
                child = in_dict.pop('children')
                if child is not None:
                    # If there is data in the child object, assign it here
                    self._warn_meta_children()
                    self.ho_data[data_vars] = child
            # Remaining items are simply assigned via recursive call
            self[data_vars] = in_dict

        elif isinstance(input_data, Meta):
            # Dealing with a higher order data set
            self._warn_meta_children()
            # `data_vars` is only a single name here (by choice for support)
            if (data_vars in self._ho_data) and input_data.empty:
                # No actual metadata provided and there is already some
                # higher order metadata in self
                return

            # Get Meta approved variable data names
            new_item_name = self.var_case_name(data_vars)

            # Ensure that Meta labels of object to be assigned are
            # consistent with self.  input_data accepts self's labels.
            input_data.accept_default_labels(self)

            # Go through and ensure Meta object to be added has variable and
            # attribute names consistent with other variables and attributes
            # this covers custom attributes not handled by default routine
            # above
            attr_names = [item for item in input_data.attrs()]
            input_data.data.columns = self.attr_case_name(attr_names)

            # Same thing for variables
            input_data.data.index = self.var_case_name(input_data.data.index)

            # Assign Meta object now that things are consistent with Meta
            # object settings, but first make sure there are lower dimension
            # metadata parameters, passing in an empty dict fills in defaults
            # if there is no existing metadata info.
            self[new_item_name] = {}

            # Now add to higher order data
            self._ho_data[new_item_name] = input_data
        return

    def __getitem__(self, key):
        """Obtain metadata.

        Maps to pandas DataFrame.loc method.

        Parameters
        ----------
        key : str, tuple, or list
            A single variable name, a tuple, or a list

        Raises
        ------
        KeyError
            If a properly formatted key is not present
        NotImplementedError
            If the input is not one of the allowed data types

        Examples
        --------
        ::

            import pysat
            inst = pysat.Instrument('pysat', 'testing2d')
            inst.load(date=inst.inst_module._test_dates[''][''])
            meta = inst.meta

            # For standard data, many slicing options are available
            meta['uts']
            meta['uts', 'units']
            meta['uts', ['units', 'long_name']]
            meta[['uts', 'mlt'], 'units']
            meta[['uts', 'mlt'], ['units', 'long_name']]
            meta[:, 'units']
            meta[:, ['units', 'long_name']]

            # For higher order data, slicing is not supported for multiple
            # parents with any children
            meta['profiles', 'density', 'units']
            meta['profiles', 'density', ['units', 'long_name']]
            meta['profiles', ['density', 'dummy_str'], ['units', 'long_name']]
            meta['profiles', ('units', 'long_name')]
            meta[['series_profiles', 'profiles'], ('units', 'long_name')]

        """
        # Define a local convenience function
        def match_name(func, var_name, index_or_column):
            """Alter variables using input function."""

            if isinstance(var_name, slice):
                # If variable is a slice, use it to select data from the
                # supplied index or column input
                return func(index_or_column[var_name])
            else:
                return func(var_name)

        # Access desired metadata based on key data type
        if isinstance(key, tuple):
            # If key is a tuple, looking at index, column access pattern
            if len(key) == 2:
                # If tuple length is 2, index, column
                new_index = match_name(self.var_case_name, key[0],
                                       self.data.index)
                try:
                    # Assume this is a label name
                    new_name = match_name(self.attr_case_name, key[1],
                                          self.data.columns)
                    return self.data.loc[new_index, new_name]
                except KeyError as kerr:
                    # This may instead be a child variable, check for children
                    if(hasattr(self[new_index], 'children')
                       and self[new_index].children is None):
                        raise kerr

                    try:
                        new_child_index = match_name(
                            self.attr_case_name, key[1],
                            self[new_index].children.data.index)
                        return self.ho_data[new_index].data.loc[new_child_index]
                    except AttributeError:
                        raise NotImplementedError(
                            ''.join(['Cannot retrieve child meta data ',
                                     'from multiple parents']))

            elif len(key) == 3:
                # If tuple length is 3, index, child_index, column
                new_index = match_name(self.var_case_name, key[0],
                                       self.data.index)
                try:
                    new_child_index = match_name(
                        self.attr_case_name, key[1],
                        self[new_index].children.data.index)
                except AttributeError:
                    raise NotImplementedError(
                        'Cannot retrieve child meta data from multiple parents')

                new_name = match_name(self.attr_case_name, key[2],
                                      self.data.columns)
                return self.ho_data[new_index].data.loc[new_child_index,
                                                        new_name]

        elif isinstance(key, list):
            # If key is a list, selection works as-is
            return self[key, :]

        elif isinstance(key, str):
            # If key is a string, treatment varies based on metadata dimension
            if key in self:
                # Get case preserved string for variable name
                new_key = self.var_case_name(key)

                # Don't need to check if in lower, all variables are always in
                # the lower metadata
                #
                # Assign meta_row using copy to avoid pandas
                # SettingWithCopyWarning, as suggested in
                # https://www.dataquest.io/blog/settingwithcopywarning/
                # TODO(#1024): The use of copy is no longer required to avoid
                #  the warnings and the .copy() have been commented out. This
                #  change was made late in the v3.0.2 review thus the comment
                #  above and commented .copy code below have been kept. Remove
                #  for any subsequent releases if things are still ok.
                meta_row = self.data.loc[new_key]  # .copy()
                if new_key in self.keys_nD():
                    meta_row.at['children'] = self.ho_data[new_key]  # .copy()
                else:
                    # Not higher order meta. Assign value of None. First, we
                    # assign a string, and then None. Ensures column is not
                    # a numeric data type.
                    meta_row.at['children'] = ''
                    meta_row.at['children'] = None
                return meta_row
            else:
                raise KeyError("Key '{:}' not found in MetaData".format(key))
        else:
            raise NotImplementedError("".join(["No way to handle MetaData key ",
                                               "{}; ".format(key.__repr__()),
                                               "expected tuple, list, or str"]))

    def __contains__(self, data_var):
        """Check variable name, not distinguishing by case.

        Parameters
        ----------
        data_var : str
            Variable name to check if present within the Meta object.

        Returns
        -------
        does_contain : boolean
            True if input Meta class contains the default labels, False if it
            does not

        """
        does_contain = False

        if data_var.lower() in [ikey.lower() for ikey in self.keys()]:
            does_contain = True

        if not does_contain:
            if data_var.lower() in [ikey.lower() for ikey in self.keys_nD()]:
                does_contain = True

        return does_contain

    def __eq__(self, other_meta):
        """Check equality between Meta instances.

        Parameters
        ----------
        other_meta : Meta
            A second Meta class object

        Returns
        -------
        bool
            True if equal, False if not equal

        Note
        ----
        Good for testing.

        Checks if variable names, attribute names, and metadata values
        are all equal between to Meta objects. Note that this comparison
        treats np.NaN == np.NaN as True.

        Name comparison is case-sensitive.

        """
        if not isinstance(other_meta, Meta):
            # The object being compared wasn't even the correct class
            return NotImplemented

        # Check if the variables and attributes are the same
        for iter1, iter2 in [(self.keys(), other_meta.keys()),
                             (self.attrs(), other_meta.attrs())]:
            list1 = [value for value in iter1]
            list2 = [value for value in iter2]

            try:
                testing.assert_lists_equal(list1, list2)
            except AssertionError:
                return False

        # Check that the values of all elements are the same. NaN is treated
        # as equal, though mathematically NaN is not equal to anything.
        for key in self.keys():
            for attr in self.attrs():
                if not testing.nan_equal(self[key, attr],
                                         other_meta[key, attr]):
                    return False

        # Check the higher order products. Recursive call into this function
        # didn't work, so spell out the details.
        keys1 = [key for key in self.keys_nD()]
        keys2 = [key for key in other_meta.keys_nD()]
        try:
            testing.assert_lists_equal(keys1, keys2)
        except AssertionError:
            return False

        # Check the higher order variables within each nD key are the same.
        # NaN is treated as equal, though mathematically NaN is not equal
        # to anything.
        for key in self.keys_nD():
            for iter1, iter2 in [(self[key].children.keys(),
                                  other_meta[key].children.keys()),
                                 (self[key].children.attrs(),
                                  other_meta[key].children.attrs())]:
                list1 = [value for value in iter1]
                list2 = [value for value in iter2]

                try:
                    testing.assert_lists_equal(list1, list2)
                except AssertionError:
                    return False

            # Check if all elements are individually equal
            for ckey in self[key].children.keys():
                for cattr in self[key].children.attrs():
                    if not testing.nan_equal(
                            self[key].children[ckey, cattr],
                            other_meta[key].children[ckey, cattr]):
                        return False

        # If we made it this far, things are good
        return True

    # -----------------------------------------------------------------------
    # Define the hidden methods

    def _insert_default_values(self, data_var):
        """Set the default label values for a data variable.

        Parameters
        ----------
        data_var : str or list
            Single or multiple data variable name(s).

        Note
        ----
        Sets NaN for all float values, -1 for all int values, 'data_var' for
        names labels, '' for all other str values, and None for any other
        data type.

        """
        # Cycle through each label type to create a list of label names
        # and label default values
        labels = list()
        default_vals = list()
        name_idx = None
        for i, lattr in enumerate(self.labels.label_type.keys()):
            labels.append(getattr(self.labels, lattr))

            if lattr in ['name']:
                default_vals.append('')
                name_idx = i
            else:
                default_vals.append(self.labels.default_values_from_attr(lattr))

        # Assign the default values to the DataFrame for this data variable(s).
        data_vars = pysat.utils.listify(data_var)
        for var in data_vars:
            if name_idx is not None:
                default_vals[name_idx] = var
            self._data.loc[var, labels] = default_vals

        return

    def _label_setter(self, new_label, current_label, default_type,
                      use_names_default=False):
        """Set default meta attributes for variable.

        Parameters
        ----------
        new_label : str
            New label to use in the Meta object
        current_label : str
            The current label used within Meta object
        default_type : type
            Type of value to be stored
        use_names_default : bool
            if True, MetaData variable names are used as the default
            value for the specified Meta attributes settings (default=False)

        Note
        ----
        Not intended for end user

        """
        self_attrs = list(self.attrs())
        if new_label not in self_attrs:
            # New label not in metadata
            if current_label in self_attrs:
                # Current label exists and has expected case
                self.data.loc[:, new_label] = self.data.loc[:, current_label]
                self.data = self.data.drop(current_label, axis=1)
            else:
                if self.hasattr_case_neutral(current_label):
                    # There is a similar label with different capitalization
                    current_label = self.attr_case_name(current_label)
                    self.data.loc[:, new_label] = self.data.loc[:,
                                                                current_label]
                    self.data = self.data.drop(current_label, axis=1)
                else:
                    # There is no existing label, setting for the first time
                    if use_names_default:
                        self.data[new_label] = self.data.index
                    else:
                        default_val = self.labels.default_values_from_type(
                            default_type)
                        self.data[new_label] = default_val
                        if default_val is None:
                            mstr = ' '.join(('A problem may have been',
                                             'encountered with the user',
                                             'supplied type for Meta',
                                             'variable: ', new_label,
                                             'Please check the settings',
                                             'provided to `labels` at',
                                             'Meta instantiation.'))
                            pysat.logger.info(mstr)

            # Check higher order structures and recursively change labels
            for key in self.keys_nD():
                # Update children
                self.ho_data[key]._label_setter(new_label, current_label,
                                                default_type, use_names_default)

        return

    # -----------------------------------------------------------------------
    # Define the public methods and properties

    @property
    def data(self):
        """Retrieve data.

        May be set using `data.setter(new_frame)`, where `new_frame` is a
        pandas Dataframe containing the metadata with label names as columns.

        """
        return self._data

    @data.setter
    def data(self, new_frame):
        # Set the data property.  See docstring for property above.
        self._data = new_frame
        return

    @property
    def ho_data(self):
        """Retrieve higher order data.

        May be set using `ho_data.setter(new_dict)`, where `new_dict` is a
        dict containing the higher order metadata.

        """
        return self._ho_data

    @ho_data.setter
    def ho_data(self, new_dict):
        # Set the ho_data property.  See docstring for property above.
        self._ho_data = new_dict
        return

    @property
    def empty(self):
        """Return boolean True if there is no metadata.

        Returns
        -------
        bool
            Returns True if there is no data, and False if there is data

        """

        # Only need to check on lower data since lower data
        # is set when higher metadata assigned.
        if self.data.empty:
            return True
        else:
            return False

    def merge(self, other):
        """Add metadata variables to `self` that are in other but not in `self`.

        Parameters
        ----------
        other : pysat.Meta
            Metadata to be merged into `self`

        """

        for key in other.keys():
            if key not in self:
                # Copies over both lower and higher dimensional data
                self[key] = other[key]
        return

    def drop(self, names):
        """Drop variables (names) from metadata.

        Parameters
        ----------
        names : list-like
            List of strings specifying the variable names to drop

        """

        # Drop the lower dimension data
        self.data = self._data.drop(names, axis=0)

        # Drop the higher dimension data
        for name in names:
            if name in self._ho_data:
                self._ho_data.pop(name)
        return

    def keep(self, keep_names):
        """Keep variables (keep_names) while dropping other parameters.

        Parameters
        ----------
        keep_names : list-like
            Variables to keep

        """
        # Create a list of variable names to keep
        keep_names = self.var_case_name(keep_names)

        # Get a list of current variable names
        current_names = self._data.index

        # Build a list of variable names to drop
        drop_names = [name for name in current_names if name not in keep_names]

        # Drop names not specified in keep_names list
        self.drop(drop_names)
        return

    def apply_meta_labels(self, other_meta):
        """Apply the existing meta labels from `self` onto different MetaData.

        Parameters
        ----------
        other_meta : Meta
            Meta object to have default labels applied

        Returns
        -------
        other_updated : Meta
            Meta object with the default labels applied

        """
        # Create a copy of other, to avoid altering in place
        other_updated = other_meta.copy()

        # Update the Meta labels
        other_updated.accept_default_labels(self.labels)

        # Return the updated Meta class object
        return other_updated

    def accept_default_labels(self, other_meta):
        """Apply labels for default meta labels from other onto `self`.

        Parameters
        ----------
        other_meta : Meta
            Meta object to take default labels from

        """
        # Update labels in metadata
        for key in other_meta.labels.label_type.keys():
            new_name = getattr(other_meta.labels, key)

            if hasattr(self.labels, key):
                # This label exists, but the name may need updating
                old_name = getattr(self.labels, key)
                if old_name != new_name:
                    self._label_setter(new_name, old_name,
                                       other_meta.labels.label_type[key],
                                       use_names_default=True)
            else:
                # This label doesn't exist, add it.
                self.labels.update(key, new_name,
                                   other_meta.labels.label_type[key])
                self._label_setter(new_name, new_name,
                                   other_meta.labels.label_type[key])

        # Need to deal with case where self has labels that other doesn't
        for key in self.labels.label_type.keys():
            if not hasattr(other_meta.labels, key):
                # This label doesn't exist, add it.
                new_name = getattr(self.labels, key)
                other_meta.labels.update(key, new_name,
                                         self.labels.label_type[key])
                other_meta._label_setter(new_name, new_name,
                                         self.labels.label_type[key])

        self.labels = other_meta.labels

        return

    def var_case_name(self, name):
        """Provide stored name (case preserved) for case insensitive input.

        Parameters
        ----------
        name : str or list
            Single or multiple variable name(s) using any capitalization scheme.

        Returns
        -------
        case_names : str or list
            Maintains the same type as input, returning the stored name(s) of
            the meta object.

        Note
        ----
        If name is not found (case-insensitive check) then `name` is returned,
        as input. This function is intended to be used to help ensure the
        case of a given variable name is the same across the Meta object.

        """

        # Ensure input is a str if string-like
        name = pysat.utils.stringify(name)

        # Flag if list-like input provided
        return_list = False if isinstance(name, str) else True

        # Ensure we operate on a list of names
        names = pysat.utils.listify(name)

        # Get a lower-case version of the name(s)
        lower_names = [iname.lower() for iname in names]

        # Cycle through all places where this variable name could be, returning
        # the variable name whose lower-case version matches the lower-case
        # version of the variable name supplied.
        case_names = []

        # Create a list of all variable names and lower case variable names
        self_keys = [key for key in self.keys()]
        lower_self_keys = [key.lower() for key in self_keys]

        for iname, lower_name in zip(names, lower_names):
            if lower_name in lower_self_keys:
                for out_name, lout_name in zip(self_keys, lower_self_keys):
                    if lower_name == lout_name:
                        case_names.append(out_name)
                        break
            else:
                case_names.append(iname)

        if not return_list:
            case_names = case_names[0]

        return case_names

    def keys(self):
        """Yield variable names stored for 1D variables."""
        for ikey in self.data.index:
            yield ikey

    def keys_nD(self):
        """Yield keys for higher order metadata."""
        for ndkey in self.ho_data:
            yield ndkey

    def attrs(self):
        """Yield metadata products stored for each variable name."""
        for dcol in self.data.columns:
            yield dcol

    def hasattr_case_neutral(self, attr_name):
        """Case-insensitive check for attribute names in this class.

        Parameters
        ----------
        attr_name : str
            Name of attribute to find

        Returns
        -------
        has_name : bool
            True if the case-insensitive check for attribute name is successful,
            False if no attribute name is present.

        Note
        ----
        Does not check higher order meta objects

        """

        if attr_name.lower() in [dcol.lower() for dcol in self.data.columns]:
            return True

        return False

    def attr_case_name(self, name):
        """Retrieve preserved case name for case insensitive value of name.

        Parameters
        ----------
        name : str or list
            Single or multiple variable name(s) to get stored case form.

        Returns
        -------
        out_name : str or list
            Maintains same type as input. Name(s) in proper case.

        Note
        ----
        Checks first within standard attributes. If not found there, checks
        attributes for higher order data structures. If not found, returns
        supplied name as it is available for use. Intended to be used to help
        ensure that the same case is applied to all repetitions of a given
        variable name.

        """

        # Ensure input is a str if string-like
        name = pysat.utils.stringify(name)

        # Flag if list-like object provided
        return_list = False if isinstance(name, str) else True

        # Ensure we operate on a list of names
        names = pysat.utils.listify(name)

        # Get a lower-case version of the name(s)
        lower_names = [iname.lower() for iname in names]

        # Create a list of all attribute names and lower case attribute names
        self_keys = [key for key in self.attrs()]
        for key in list(self.keys_nD()):
            self_keys.extend(self.ho_data[key].data.columns)
        lower_self_keys = [key.lower() for key in self_keys]

        case_names = []
        for lname, iname in zip(lower_names, names):
            if lname in lower_self_keys:
                for out_name, lout_name in zip(self_keys, lower_self_keys):
                    if lname == lout_name:
                        case_names.append(out_name)
                        break
            else:
                # Name not currently used. Free.
                case_names.append(iname)

        if not return_list:
            case_names = case_names[0]

        return case_names

    def rename(self, mapper):
        """Update the preserved case name for mapped value of name.

        Parameters
        ----------
        mapper : dict or func
            Dictionary with old names as keys and new names as variables or
            a function to apply to all names

        Raises
        ------
        ValueError
            When normal data is treated like higher-order data in dict mapping.

        Note
        ----
        Checks first within standard attributes. If not found there, checks
        attributes for higher order data structures. If not found, returns
        supplied name as it is available for use. Intended to be used to help
        ensure that the same case is applied to all repetitions of a given
        variable name.

        """

        # Cycle through the top-level variables
        for var in self.keys():
            # Update the attribute name
            map_var = core_utils.get_mapped_value(var, mapper)
            if map_var is not None:
                if isinstance(map_var, dict):
                    if var in self.keys_nD():
                        child_meta = self[var].children.copy()
                        child_meta.rename(map_var)
                        self.ho_data[var] = child_meta
                    else:
                        raise ValueError('unknown mapped value at {:}'.format(
                            repr(var)))
                else:
                    # Get and update the meta data
                    hold_meta = self[var].copy()
                    hold_meta.name = map_var

                    # Remove the metadata under the previous variable name
                    self.drop(var)
                    if var in self.ho_data:
                        del self.ho_data[var]

                    # Re-add the meta data with the updated variable name
                    self[map_var] = hold_meta

                    # Determine if the attribute is present in higher order
                    # structures
                    if map_var in self.keys_nD():
                        # The children attribute is a Meta class object.
                        # Recursively call the current routine. The only way to
                        # avoid Meta undoing the renaming process is to assign
                        # the meta data to `ho_data`.
                        child_meta = self[map_var].children.copy()
                        child_meta.rename(mapper)
                        self.ho_data[map_var] = child_meta

        return

    def concat(self, other_meta, strict=False):
        """Concats two metadata objects together.

        Parameters
        ----------
        other_meta : Meta
            Meta object to be concatenated
        strict : bool
            If True, this flag ensures there are no duplicate variable names
            (default=False)

        Returns
        -------
        mdata : Meta
            Concatenated object

        Raises
        ------
        KeyError
            If there are duplicate keys and the `strict` flag is True.

        Note
        ----
        Uses units and name label of `self` if `other_meta` is different

        """
        mdata = self.copy()
        mdata_keys = [key.lower() for key in mdata.keys()]

        # Check the inputs
        if strict:
            for key in other_meta.keys():
                if key.lower() in mdata_keys:
                    raise KeyError(''.join(('Duplicated keys (variable names) ',
                                            'in Meta.keys().')))

        # Make sure labels between the two objects are the same
        other_meta_updated = other_meta.copy()
        other_meta_updated.labels = self.labels

        # Concat 1D metadata in data frames to copy of current metadata
        for key in other_meta_updated.keys():
            mdata.data.loc[key] = other_meta.data.loc[key]

        # Combine the higher order meta data
        for key in other_meta_updated.keys_nD():
            mdata.ho_data[key] = other_meta.ho_data[key]

        return mdata

    def copy(self):
        """Deep copy of the meta object."""
        return deepcopy(self)

    def pop(self, label_name):
        """Remove and return metadata about variable.

        Parameters
        ----------
        label_name : str
            Meta key for a data variable

        Returns
        -------
        output : pds.Series
            Series of metadata for variable

        """
        # Check if the specified label name is present
        if label_name in self:
            # Get case preserved name for variable
            new_name = self.var_case_name(label_name)

            # Check if the label name is for 1D or nD meta data
            if new_name in self.keys():
                output = self[new_name]
                self.data = self.data.drop(new_name, axis=0)
            else:
                output = self.ho_data.pop(new_name)
        else:
            raise KeyError('Key not present in metadata variables')

        return output

    def transfer_attributes_to_header(self, strict_names=False):
        """Transfer non-standard attributes in Meta to the MetaHeader object.

        Parameters
        ----------
        strict_names : bool
            If True, produces an error if the MetaHeader object already
            has an attribute with the same name to be copied (default=False)

        Raises
        ------
        AttributeError
            If `strict_names` is True and a global attribute would be updated.

        """

        # Get base attribute set, and attributes attached to Meta
        base_attrb = self._base_attr
        this_attrb = dir(self)

        # Update the MetaHeader
        for key in this_attrb:
            # Don't store any hidden or base attributes
            if key not in base_attrb and key[0] != '_':
                if strict_names and key in self.header.global_attrs:
                    raise AttributeError(''.join([
                        'Attribute ', repr(key), ' attached to the Meta cannot',
                        ' be transferred as it already exists in MetaHeader']))

                # Save the attribute name (key) and value
                setattr(self.header, key, getattr(self, key))

                # Remove key from meta
                delattr(self, key)

        return

    def transfer_attributes_to_instrument(self, inst, strict_names=False):
        """Transfer non-standard attributes in Meta to Instrument object.

        Parameters
        ----------
        inst : pysat.Instrument
            Instrument object to transfer attributes to
        strict_names : bool
            If True, produces an error if the Instrument object already
            has an attribute with the same name to be copied (default=False)

        Raises
        ------
        ValueError
            If `inst` type is not pysat.Instrument.

        Note
        ----
        `pysat.files.io.load_netCDF` and similar routines are only able to
        attach netCDF4 attributes to a Meta object. This routine identifies
        these attributes and removes them from the Meta object. Intent is to
        support simple transfers to the pysat.Instrument object.

        Will not transfer names that conflict with pysat default attributes.

        """

        # Test the instrument parameter for type
        if not isinstance(inst, pysat.Instrument):
            raise ValueError("".join(["Can't transfer Meta attributes to ",
                                      "non-Instrument object of type ",
                                      str(type(inst))]))

        # Save the base Instrument attributes
        banned = inst._base_attr

        # Get base attribute set, and attributes attached to instance
        base_attrb = self._base_attr
        this_attrb = dir(self)

        # Collect these attributes into a dict
        adict = {}
        transfer_key = []
        for key in this_attrb:
            # Don't store any hidden, banned, or base attributes
            if key not in banned and key not in base_attrb and key[0] != '_':
                adict[key] = getattr(self, key)
                transfer_key.append(key)

                # Remove key from meta
                delattr(self, key)

        # Store any non-standard attributes in Instrument get list of
        # instrument objects attributes first to check if a duplicate
        # instrument attributes stay with instrument
        inst_attr = dir(inst)

        for key in transfer_key:
            # Note, keys in transfer_key already checked against banned
            if key not in inst_attr:
                setattr(inst, key, adict[key])
            else:
                if not strict_names:
                    setattr(inst, key, adict[key])
                else:
                    if not strict_names:
                        # Use naming convention: new_name = 'pysat_attr_' + key
                        inst.__setattr__(key, adict[key])
                    else:
                        aerr = ''.join(('Attribute ', repr(key),
                                        ' attached to the Meta cannot be'
                                        ' transferred as it already exists in ',
                                        'the Instrument object.'))
                        raise AttributeError(aerr)
        return

    def add_epoch_metadata(self, epoch_name):
        """Add epoch or time-index metadata if it is missing.

        Parameters
        ----------
        epoch_name : str
            Data key for time-index or epoch data

        """
        # Get existing meta data
        if epoch_name in self:
            new_dict = self[self.var_case_name(epoch_name)]
        else:
            new_dict = {}

        # Update basic labels, if they are missing
        epoch_label = 'Milliseconds since 1970-1-1 00:00:00'
        basic_labels = [self.labels.units, self.labels.name, self.labels.desc,
                        self.labels.notes]
        for label in basic_labels:
            if label not in new_dict or len(new_dict[label]) == 0:
                new_dict[label] = epoch_label

        # Update the meta data
        self[self.var_case_name(epoch_name)] = new_dict

        return

    def to_dict(self, preserve_case=False):
        """Convert self into a dictionary.

        Parameters
        ----------
        preserve_case : bool
            If True, the case of variables within self are preserved. If False,
            all variables returned as lower case. (default=False)

        Returns
        -------
        export_dict : dict
            A dictionary of the metadata for each variable of an output file

        """

        export_dict = {}

        # First Order Data
        for key in self.data.index:
            if preserve_case:
                case_key = self.var_case_name(key)
            else:
                case_key = key.lower()

            # Translate each key if a translation is provided
            export_dict[case_key] = {}
            meta_dict = self.data.loc[key].to_dict()
            for orig_key in meta_dict:
                export_dict[case_key][orig_key] = meta_dict[orig_key]

        # Higher Order Data
        # TODO(#789): remove in pysat 3.2.0
        for key in self.ho_data:
            if preserve_case:
                case_key = self.var_case_name(key)
            else:
                case_key = key.lower()

            if case_key not in export_dict:
                export_dict[case_key] = {}
            for ho_key in self.ho_data[key].data.index:
                if preserve_case:
                    case_ho_key = self.var_case_name(ho_key)
                else:
                    case_ho_key = ho_key.lower()

                new_key = '_'.join((case_key, case_ho_key))
                export_dict[new_key] = \
                    self.ho_data[key].data.loc[ho_key].to_dict()

        return export_dict

    @classmethod
    def from_csv(cls, filename=None, col_names=None, sep=None, **kwargs):
        """Create instrument metadata object from csv.

        Parameters
        ----------
        filename : string
            Absolute filename for csv file or name of file stored in pandas
            instruments location
        col_names : list-like collection of strings
            Column names in csv and resultant meta object
        sep : string
            Column seperator for supplied csv filename
        **kwargs : dict
            Optional kwargs used by `pds.read_csv`

        Note
        ----
        Column names must include at least ['name', 'long_name', 'units'],
        which are assumed if `col_names` is None

        """
        req_names = ['name', 'long_name', 'units']
        if col_names is None:
            col_names = req_names
        elif not all([rname in col_names for rname in req_names]):
            raise ValueError('col_names must include name, long_name, units.')

        if sep is None:
            sep = ','

        if filename is None:
            raise ValueError('Must supply an instrument module or file path.')
        elif not isinstance(filename, str):
            raise ValueError('Keyword name must be related to a string')
        elif not os.path.isfile(filename):
            # Not a real file, assume input is a pysat instrument name
            # and look in the standard pysat location.
            testfile = os.path.join(pysat.__path__[0], 'instruments', filename)
            if os.path.isfile(testfile):
                filename = testfile
            else:
                # Try to form an absolute path, if the relative path failed
                testfile = os.path.abspath(filename)
                if not os.path.isfile(testfile):
                    raise ValueError("Unable to create valid file path.")
                else:
                    filename = testfile

        mdata = pds.read_csv(filename, names=col_names, sep=sep, **kwargs)

        if not mdata.empty:
            # Make sure the data name is the index
            mdata.index = mdata['name']
            del mdata['name']
            return cls(metadata=mdata)
        else:
            raise ValueError(''.join(['Unable to retrieve information from ',
                                      filename]))

    # TODO(#789): remove in pysat 3.2.0
    def _warn_meta_children(self):
        """Warn the user that higher order metadata is deprecated."""

        warnings.warn(" ".join(["Support for higher order metadata has been",
                                "deprecated and will be removed in 3.2.0+."]),
                      DeprecationWarning, stacklevel=2)
        return


class MetaLabels(object):
    """Store metadata labels for Instrument instance.

    Parameters
    ----------
    units : tuple
        Units label name and value type (default=('units', str))
    name : tuple
        Name label name and value type (default=('long_name', str))
    notes : tuple
        Notes label name and value type (default=('notes', str))
    desc : tuple
        Description label name and value type (default=('desc', str))
    min_val : tuple
        Minimum value label name and value type (default=('value_min', float))
    max_val : tuple
        Maximum value label name and value type (default=('value_max', float))
    fill_val : tuple
        Fill value label name and value type (default=('fill', float))
    kwargs : dict
        Dictionary containing optional label attributes, where the keys are the
        attribute names and the values are tuples containing the label name and
        value type

    Attributes
    ----------
    meta : pandas.DataFrame or NoneType
        Coupled MetaData data object or NoneType
    units : str
        String used to label units in storage (default='units')
    name : str
        String used to label long_name in storage (default='long_name')
    notes : str
       String used to label notes in storage (default='notes')
    desc : str
       String used to label variable descriptions in storage
       (default='desc')
    min_val : str
       String used to label typical variable value min limit in storage
       (default='value_min')
    max_val : str
       String used to label typical variable value max limit in storage
       (default='value_max')
    fill_val : str
        String used to label fill value in storage. The default follows the
        netCDF4 standards. (default='fill')
    label_type : dict
        Dict with attribute names as keys and expected data types as values
    label_attrs : dict
        Dict with attribute names as values and attributes values as keys

    Raises
    ------
    TypeError
        If meta data type is invalid

    Note
    ----
    Meta object preserves the case of variables and attributes as it first
    receives the data. Subsequent calls to set new metadata with the same
    variable or attribute will use case of first call. Accessing or setting
    data thereafter is case insensitive. In practice, use is case insensitive
    but the original case is preserved. Case preservation is built in to
    support writing files with a desired case to meet standards.

    Metadata for higher order data objects, those that have
    multiple products under a single variable name in a `pysat.Instrument`
    object, are stored by providing a Meta object under the single name.

    Supports any custom metadata values in addition to the expected metadata
    attributes (units, name, notes, desc, value_min, value_max, and fill).
    These base attributes may be used to programatically access and set types
    of metadata regardless of the string values used for the attribute. String
    values for attributes may need to be changed depending upon the standards
    of code or files interacting with pysat.

    Meta objects returned as part of pysat loading routines are automatically
    updated to use the same values of units, etc. as found in the
    pysat.Instrument object.

    """

    def __init__(self, metadata=None, units=('units', str),
                 name=('long_name', str), notes=('notes', str),
                 desc=('desc', str), min_val=('value_min', float),
                 max_val=('value_max', float), fill_val=('fill', float),
                 **kwargs):
        """Initialize the MetaLabels class."""

        # Initialize the coupled metadata
        self.meta = metadata

        # Initialize a dictionary of label types, whose keys are the label
        # attributes
        self.label_type = {'units': units[1], 'name': name[1],
                           'notes': notes[1], 'desc': desc[1],
                           'min_val': min_val[1], 'max_val': max_val[1],
                           'fill_val': fill_val[1]}
        self.label_attrs = {units[0]: 'units', name[0]: 'name',
                            notes[0]: 'notes', desc[0]: 'desc',
                            min_val[0]: 'min_val', max_val[0]: 'max_val',
                            fill_val[0]: 'fill_val'}

        # Ensure all standard label types are valid
        for label in self.label_type.keys():
            if not self._eval_label_type(self.label_type[label]):
                raise TypeError(''.join([
                    'iterable types like ', repr(self.label_type[label]),
                    ' (set for ', repr(label), ') are not allowed']))

        # Set the standard label attributes
        for label_val in self.label_attrs.keys():
            setattr(self, self.label_attrs[label_val], label_val)

        # Set and evaluate the custom labels and label types
        for custom_label in kwargs.keys():
            self.update(custom_label, *kwargs[custom_label])

        return

    def __setattr__(self, name, value):
        """Conditionally set attributes based on their type.

        Parameters
        ----------
        name : str
            Attribute name to be assigned to MetaLabels
        value
            Value (any type) to be assigned to attribute specified by name

        """
        # Get old attribute value for reference
        if hasattr(self, name):
            old_value = getattr(self, name)
        else:
            old_value = None

        # Use Object to avoid recursion
        super(MetaLabels, self).__setattr__(name, value)

        # Before setting the attribute, see if upstream changes are needed
        if old_value is not None and name not in ['label_type', 'meta']:
            if hasattr(self, 'meta') and hasattr(self.meta, 'data'):
                self.meta._label_setter(value, getattr(self, name),
                                        self.label_type[name],
                                        use_names_default=True)

    def __repr__(self):
        """Print MetaLabels instantiation parameters.

        Returns
        -------
        out_str : str
            Simply formatted output string

        """
        label_str = ', '.join(["{:s}={:} {:}".format(mlab, getattr(self, mlab),
                                                     self.label_type[mlab])
                               for mlab in self.label_type.keys()])
        out_str = ''.join(['pysat.MetaLabels(', label_str, ")"])
        return out_str

    def __str__(self):
        """Print MetaLabels instance, variables, and attributes.

        Returns
        -------
        out_str : str
            Nicely formatted output string

        """
        # Set the printing limits and get the label attributes
        ncol = 3
        lab_attrs = ["{:s}->{:s}".format(mlab, getattr(self, mlab))
                     for mlab in self.label_type.keys()]
        nlabels = len(lab_attrs)

        # Print the MetaLabels
        out_str = "MetaLabels:\n"
        out_str += "-----------\n"
        out_str += core_utils.fmt_output_in_cols(lab_attrs, ncols=ncol,
                                                 max_num=nlabels)

        return out_str

    def _eval_label_type(self, val_type):
        """Evaluate the label type for validity.

        Parameters
        ----------
        val_type : type
            Variable type for the value to be assigned to a MetaLabel

        Returns
        -------
        valid : bool
            True if this is a valid type, False if not valid

        """

        default_val = self.default_values_from_type(val_type)
        valid = True

        if default_val is None and val_type not in [type(None), bool, bytes]:
            # Ensure the type is not iterable
            try:
                val_type([])
                valid = False
            except (TypeError, ValueError):
                # If a list can't be cast, the type is not iterable and is
                # likely valid.  There may be some objects that prove
                # problematic, but they haven't been encountered yet.
                pass

        return valid

    def default_values_from_type(self, val_type):
        """Retrieve the default values for each label based on their type.

        Parameters
        ----------
        val_type : type
            Variable type for the value to be assigned to a MetaLabel

        Returns
        -------
        default_val : str, float, int, NoneType
            Sets NaN for all float values, -1 for all int values, and '' for
            all str values, and None for any other data type

        """

        # Perform some pre-checks on type, checks that could error with
        # unexpected input.
        try:
            floating_check = isinstance(val_type(), np.floating)
        except TypeError as err:
            if str(err).find('not a callable function') > 0:
                floating_check = False
            else:
                # Unexpected input
                floating_check = None
        try:
            int_check = isinstance(val_type(), np.integer)
        except TypeError as err:
            if str(err).find('not a callable function') > 0:
                int_check = False
            else:
                # Unexpected input
                int_check = None

        try:
            str_check = issubclass(val_type, str)
        except TypeError as err:
            if str(err).find('must be a class') > 0:
                str_check = False
            else:
                # Unexpected input
                str_check = None

        # Assign the default value
        if str_check:
            default_val = ''
        elif val_type is float or floating_check:
            default_val = np.nan
        elif val_type is int or int_check:
            default_val = -1
        else:
            mstr = ''.join(('No type match found for ', str(val_type)))
            pysat.logger.info(mstr)
            default_val = None

        return default_val

    def default_values_from_attr(self, attr_name):
        """Retrieve the default values for each label based on their type.

        Parameters
        ----------
        attr_name : str
            Label attribute name (e.g., max_val)

        Returns
        -------
        default_val : str, float, int, or NoneType
            Sets NaN for all float values, -1 for all int values, and ''
            for all str values except for 'scale', which defaults to 'linear',
            and None for any other data type

        Raises
        ------
        ValueError
            For unknown `attr_name`

        """

        # Test the input parameter
        if attr_name not in self.label_type.keys():
            raise ValueError('unknown label attribute {:}'.format(attr_name))

        # Assign the default value
        if attr_name == 'scale':
            default_val = 'linear'
        else:
            default_val = self.default_values_from_type(
                self.label_type[attr_name])
            if default_val is None:
                mstr = ' '.join(('A problem may have been',
                                 'encountered with the user',
                                 'supplied type for Meta',
                                 'attribute: ', attr_name,
                                 'Please check the settings',
                                 'provided to `labels` at',
                                 'Meta instantiation.'))
                pysat.logger.info(mstr)

        return default_val

    def update(self, lattr, lname, ltype):
        """Update MetaLabels with a new label.

        Parameters
        ----------
        lattr : str
            Attribute for this new label
        lname : str
            MetaData name for this label
        ltype : type
            Expected data type for this label

        Raises
        ------
        TypeError
            If meta data type is invalid

        """

        if self._eval_label_type(ltype):
            # This is a valid meta data type, update the class attributes
            setattr(self, lattr, lname)
            self.label_type[lattr] = ltype
            self.label_attrs[lname] = lattr
        else:
            # This is an invalid meta data type, raise a TypeError
            raise TypeError(''.join(['iterable types like ', repr(ltype),
                                     ' (set for ', repr(lattr),
                                     ') are not allowed']))
        return


class MetaHeader(object):
    """Stores global metadata.

    Parameters
    ----------
    header_data : dict or NoneType
        Meta data to be assigned to the class.  Keys denote the desired
        attribute names and values the metadata for that attribute.
        (default=None)

    Attributes
    ----------
    global_attrs : list
        List of global attribute names
    <attrs> :
        Attributes with names corresponding to the values of `global_attrs`,
        may have any type

    Methods
    -------
    to_dict()
        Convert global attributes to a dictionary.

    """

    def __init__(self, header_data=None):
        """Initialize the MetaHeader class."""

        if header_data is None:
            header_data = {}

        # Initialize the list of attributes
        self.global_attrs = list(header_data.keys())

        # Set the global attributes
        for attr_name in self.global_attrs:
            setattr(self, attr_name, header_data[attr_name])

        return

    def __setattr__(self, name, value):
        """Set attributes based on their type and update `global_attrs`.

        Parameters
        ----------
        name : str
            Attribute name to be assigned to MetaLabels
        value
            Value (any type) to be assigned to attribute specified by name

        """
        # If this is a new attribute, update the `global_attrs` list
        if not hasattr(self, name) and name != 'global_attrs':
            # Only need to expand the global attributes if the new name
            # is not present in the list
            if name not in self.global_attrs:
                self.global_attrs.append(name)

        # Use Object to avoid recursion
        super(MetaHeader, self).__setattr__(name, value)
        return

    def __repr__(self):
        """Print MetaHeader instantiation parameters.

        Returns
        -------
        out_str : str
            Simply formatted output string

        """
        out_str = ''.join(['pysat.MetaHeader(header_data=',
                           repr(self.to_dict()), ")"])
        return out_str

    def __str__(self, max_num_display=3):
        """Print MetaHeader instance, variables, and attributes.

        Parameters
        ----------
        max_num_display : int
            Maximum number of attribute names to display

        Returns
        -------
        out_str : str
            Nicely formatted output string

        """
        # Set the printing limits and get the label attributes
        ncol = 3
        nattrs = len(self.global_attrs)
        lab_attrs = [repr(gattr) for gattr in self.global_attrs]

        # Print the MetaHeader data
        out_str = "Metadata for {:d} global attributes\n".format(nattrs)
        if nattrs > 0 and max_num_display > 0:
            out_str += "-----------------------------------\n"
            out_str += core_utils.fmt_output_in_cols(lab_attrs, ncols=ncol,
                                                     max_num=max_num_display)

        return out_str

    def __eq__(self, other):
        """Determine class equality.

        Parameters
        ----------
        other : any
            Other object to compare for equality

        Returns
        -------
        bool
            True if objects are identical, False if they are not.

        """

        # Check if other is the same class or not
        if not isinstance(other, self.__class__):
            return False

        # Ensure the expected attributes are present and equal
        if not hasattr(other, "to_dict") or not hasattr(self, "to_dict"):
            return False

        if not hasattr(other,
                       "global_attrs") or not hasattr(self, "global_attrs"):
            return False
        else:
            try:
                testing.assert_lists_equal(getattr(other, "global_attrs"),
                                           getattr(self, "global_attrs"))
            except AssertionError:
                return False

        # Ensure the global header data is the same
        for attr in other.global_attrs:
            if not hasattr(self, attr):
                return False

            if getattr(other, attr) != getattr(self, attr):
                return False

        return True

    def to_dict(self):
        """Convert the header data to a dictionary.

        Returns
        -------
        header_data : dict
            Global meta data where the keys are the attribute names and values
            the metadata for that attribute.

        """

        header_data = {hattr: getattr(self, hattr)
                       for hattr in self.global_attrs}

        return header_data
