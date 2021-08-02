#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

from copy import deepcopy
import os
import warnings
import numpy as np
import pandas as pds

import pysat
import pysat.utils._core as core_utils
from pysat.utils import testing


class Meta(object):
    """ Stores metadata for Instrument instance, similar to CF-1.6 netCDFdata
    standard.

    Parameters
    ----------
    metadata : pandas.DataFrame
        DataFrame should be indexed by variable name that contains at minimum
        the standard_name (name), units, and long_name for the data stored in
        the associated pysat Instrument object.
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', float), 'max_val': ('value_max', float),
        'fill_val': ('fill', float)})
    export_nan : list or NoneType
        List of labels that should be exported even if their value is nan or
        None for an empty list. When used, metadata with a value of nan will
        be excluded from export. Will always allow nan export for labels of
        the float type (default=None)

    Attributes
    ----------
    data : pandas.DataFrame
        index is variable standard name, 'units', 'long_name', and other
        defaults are also stored along with additional user provided labels.
    labels : MetaLabels
        Labels for MetaData attributes

    Note
    ----
    Meta object preserves the case of variables and attributes as it first
    receives the data. Subsequent calls to set new metadata with the same
    variable or attribute will use case of first call. Accessing or setting
    data thereafter is case insensitive. In practice, use is case insensitive
    but the original case is preserved. Case preseveration is built in to
    support writing files with a desired case to meet standards.

    Metadata for higher order data objects, those that have
    multiple products under a single variable name in a pysat.Instrument
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

    Examples
    --------
    ::

        # instantiate Meta object, default values for attribute labels are used
        meta = pysat.Meta()
        # set a couple base units
        # note that other base parameters not set below will
        # be assigned a default value
        meta['name'] = {'long_name': string, 'units': string}
        # update 'units' to new value
        meta['name'] = {'units': string}
        # update 'long_name' to new value
        meta['name'] = {'long_name': string}
        # attach new info with partial information, 'long_name' set to 'name2'
        meta['name2'] = {'units': string}
        # units are set to '' by default
        meta['name3'] = {'long_name': string}

        # assigning custom meta parameters
        meta['name4'] = {'units': string, 'long_name': string
                         'custom1': string, 'custom2': value}
        meta['name5'] = {'custom1': string, 'custom3': value}

        # assign multiple variables at once
        meta[['name1', 'name2']] = {'long_name': [string1, string2],
                                    'units': [string1, string2],
                                    'custom10': [string1, string2]}

        # assiging metadata for n-Dimensional variables
        meta2 = pysat.Meta()
        meta2['name41'] = {'long_name': string, 'units': string}
        meta2['name42'] = {'long_name': string, 'units': string}
        meta['name4'] = {'meta': meta2}

        # or
        meta['name4'] = meta2
        meta['name4'].children['name41']

        # mixture of 1D and higher dimensional data
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        meta2 = pysat.Meta()
        meta2[['higher', 'lower']] = {'meta': [meta, None],
                                      'units': [None, 'boo'],
                                      'long_name': [None, 'boohoo']}

        # assign from another Meta object
        meta[key1] = meta2[key2]

        # access fill info for a variable, presuming default label
        meta[key1, 'fill']

        # access same info, even if 'fill' not used to label fill values
        meta[key1, meta.fill_label]


        # change a label used by Meta object
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

    def __init__(self, metadata=None,
                 labels={'units': ('units', str), 'name': ('long_name', str),
                         'notes': ('notes', str), 'desc': ('desc', str),
                         'min_val': ('value_min', float),
                         'max_val': ('value_max', float),
                         'fill_val': ('fill', float)}, export_nan=None):

        # Set mutability of Meta attributes.  This flag must be set before
        # anything else, or `__setattr__` breaks.
        self.mutable = True

        # Set the NaN export list
        self._export_nan = [] if export_nan is None else export_nan
        for lvals in labels.values():
            if lvals[0] not in self._export_nan and lvals[1] == float:
                self._export_nan.append(lvals[0])

        # Set the labels
        self.labels = MetaLabels(metadata=self, **labels)

        # init higher order (nD) data structure container, a dict
        self._ho_data = {}

        # Use any user provided data to instantiate object with data
        # Attributes unit and name labels are called within
        if metadata is not None:
            if isinstance(metadata, pds.DataFrame):
                self._data = metadata

                # Make sure defaults are taken care of for required metadata
                self.accept_default_labels(self)
            else:
                raise ValueError(''.join(('Input must be a pandas DataFrame',
                                          'type. See other constructors for',
                                          ' alternate inputs.')))
        else:
            columns = [getattr(self.labels, mlab)
                       for mlab in self.labels.label_type.keys()]
            self._data = pds.DataFrame(None, columns=columns)

        # Establish attributes intrinsic to object, before user can
        # add any
        self._base_attr = dir(self)

    def __repr__(self):
        """String describing MetaData instantiation parameters

        Returns
        -------
        out_str : str
            Simply formatted output string

        """
        nvar = len([kk for kk in self.keys()])
        out_str = ''.join(['pysat.Meta(metadata=', self._data.__repr__(),
                           ', labels=', self.labels.__repr__(),
                           'export_nan=', self._export_nan.__repr__(),
                           ') -> {:d} Variables'.format(nvar)])
        return out_str

    def __str__(self, long_str=True):
        """String describing Meta instance, variables, and attributes

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

        # Print the longer output
        if long_str:
            # Print all the metadata labels
            out_str += "\n{:s}".format(self.labels.__str__())

            # Print a subset of the metadata variables, divided by order
            ncol = 3
            max_num = 6  # Should be divible by 2 and ncol
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
        """Conditionally sets attributes based on self.mutable flag

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

        # mutable handled explicitly to avoid recursion
        if name != 'mutable':

            # check if this attribute is a property
            propobj = getattr(self.__class__, name, None)
            if isinstance(propobj, property):
                # check if the property is settable
                if propobj.fset is None:
                    raise AttributeError(''.join("can't set attribute  ",
                                                 name, " to ", value, ", ",
                                                 "property has no fset"))

                # make mutable in case fset needs it to be
                mutable_tmp = self.mutable
                self.mutable = True

                # set the property
                propobj.fset(self, value)

                # restore mutability flag
                self.mutable = mutable_tmp
            else:
                # a normal attribute
                if self.mutable:
                    # use Object to avoid recursion
                    super(Meta, self).__setattr__(name, value)
                else:
                    estr = ' '.join(("Cannot set attribute", name, "to {val!s}",
                                     "since the Meta object attributes are",
                                     "set to immutable.")).format(val=value)
                    raise AttributeError(estr)
        else:
            super(Meta, self).__setattr__(name, value)

    def __setitem__(self, data_vars, input_data):
        """Convenience method for adding metadata.

        Parameters
        ----------
        data_vars : str, list
            Data variable names for the input metadata
        input_data : dict, pds.Series, or Meta
            Input metadata to be assigned

        """

        input_data = deepcopy(input_data)

        if isinstance(input_data, dict):
            # If not passed an iterable, make it one
            if isinstance(data_vars, str):
                data_vars = [data_vars]
                for key in input_data:
                    input_data[key] = [input_data[key]]
            elif isinstance(data_vars, slice) and (data_vars.step is None):
                # Check for use of instrument[indx, :] or instrument[idx]
                data_vars = [dkey for dkey in self.data.keys()]

            # Make sure the variable names are in good shape.  The Meta object
            # is case insensitive, but case preserving. Convert given data_vars
            # into ones Meta has already seen. If new, then input names
            # become the standard
            data_vars = [self.var_case_name(var) for var in data_vars]
            for var in data_vars:
                if var not in self:
                    self._insert_default_values(var)

            # Check if input dict empty.  If so, no metadata was assigned by
            # the user.  This is an empty call and we can head out,
            # since defaults have been assigned
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
            for iname in input_keys:
                new_name = self.attr_case_name(iname)
                if new_name != iname:
                    input_data[new_name] = input_data.pop(iname)

            # Time to actually add the metadata
            for ikey in input_data:
                if ikey not in ['children', 'meta']:
                    for i, var in enumerate(data_vars):
                        to_be_set = input_data[ikey][i]
                        if hasattr(to_be_set, '__iter__') \
                           and not isinstance(to_be_set, str):
                            # We have some list-like object that can only
                            # store a single element
                            if len(to_be_set) == 0:
                                # Empty list, ensure there is something to set
                                to_be_set = ['']
                            if isinstance(to_be_set[0], str) \
                                    or isinstance(to_be_set, bytes):
                                if isinstance(to_be_set, bytes):
                                    to_be_set = to_be_set.decode("utf-8")

                                self._data.loc[var, ikey] = '\n\n'.join(
                                    to_be_set)
                            else:
                                warnings.warn(' '.join(('Array elements are',
                                                        'not allowed in meta.',
                                                        'Dropping input :',
                                                        key)))
                        else:
                            self._data.loc[var, ikey] = to_be_set
                else:
                    # key is 'meta' or 'children'
                    # process higher order stuff. Meta inputs could be part of
                    # larger multiple parameter assignment
                    # so not all names may actually have 'meta' to add
                    for j, (item, val) in enumerate(zip(data_vars,
                                                        input_data['meta'])):
                        if val is not None:
                            # Assign meta data, using a recursive call...
                            # heads to if Meta instance call
                            self[item] = val

        elif isinstance(input_data, pds.Series):
            # Outputs from Meta object are a Series. Thus this takes in input
            # from a Meta object. Set data using standard assignment via a dict
            in_dict = input_data.to_dict()
            if 'children' in in_dict:
                child = in_dict.pop('children')
                if child is not None:
                    # if not child.data.empty:
                    self.ho_data[data_vars] = child

            # Remaining items are simply assigned
            self[data_vars] = in_dict

        elif isinstance(input_data, Meta):
            # Dealing with a higher order data set.
            # data_vars is only a single name here (by choice for support)
            if (data_vars in self._ho_data) and (input_data.empty):
                # No actual metadata provided and there is already some
                # higher order metadata in self
                return

            # Get Meta approved variable data_vars
            new_item_name = self.var_case_name(data_vars)

            # Ensure that Meta labels of object to be assigned are
            # consistent with self.  input_data accepts self's labels
            input_data.accept_default_labels(self)

            # Go through and ensure Meta object to be added has variable and
            # attribute names consistent with other variables and attributes
            # this covers custom attributes not handled by default routine
            # above
            attr_names = input_data.attrs()
            new_names = []
            for name in attr_names:
                new_names.append(self.attr_case_name(name))
            input_data.data.columns = new_names

            # Same thing for variables
            var_names = input_data.data.index
            new_names = []
            for name in var_names:
                new_names.append(self.var_case_name(name))
            input_data.data.index = new_names

            # Assign Meta object now that things are consistent with Meta
            # object settings, but first make sure there are lower dimension
            # metadata parameters, passing in an empty dict fills in defaults
            # if there is no existing metadata info
            self[new_item_name] = {}

            # Now add to higher order data
            self._ho_data[new_item_name] = input_data
        return

    def __getitem__(self, key):
        """Convenience method for obtaining metadata.

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

            meta['name']
            meta['name1', 'units']
            meta[['name1', 'name2'], 'units']
            meta[:, 'units']

            # for higher order data
            meta['name1', 'subvar', 'units']
            meta['name1', ('units', 'scale')]

        """
        # Define a local convenience function
        def match_name(func, var_name, index_or_column):
            """Applies func on input variables(s) depending on variable type
            """
            if isinstance(var_name, str):
                # If variable is a string, use it as input
                return func(var_name)
            elif isinstance(var_name, slice):
                # If variable is a slice, use it to select data from the
                # supplied index or column input
                return [func(var) for var in index_or_column[var_name]]
            else:
                # Otherwise, assume the variable iterable input
                return [func(var) for var in var_name]

        # Access desired metadata based on key data type
        if isinstance(key, tuple):
            # If key is a tuple, looking at index, column access pattern
            if len(key) == 2:
                # If tuple length is 2, index, column
                new_index = match_name(self.var_case_name, key[0],
                                       self.data.index)
                new_name = match_name(self.attr_case_name, key[1],
                                      self.data.columns)
                return self.data.loc[new_index, new_name]

            elif len(key) == 3:
                # If tuple length is 3, index, child_index, column
                new_index = self.var_case_name(key[0])
                new_child_index = self.var_case_name(key[1])
                new_name = self.attr_case_name(key[2])
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
                # the lower metadata.
                #
                # Assign meta_row using copy to avoid pandas
                # SettingWithCopyWarning, as suggested in
                # https://www.dataquest.io/blog/settingwithcopywarning/
                meta_row = self.data.loc[new_key].copy()
                if new_key in self.keys_nD():
                    meta_row.at['children'] = self.ho_data[new_key].copy()
                else:
                    meta_row.at['children'] = None  # Return empty meta instance

                return meta_row
            else:
                raise KeyError('Key not found in MetaData')
        else:
            raise NotImplementedError("".join(["No way to handle MetaData key ",
                                               "{}; ".format(key.__repr__()),
                                               "expected tuple, list, or str"]))

    def __contains__(self, data_var):
        """case insensitive check for variable name

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
        """ Check equality between Meta instances

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
        # as equal, though mathematically NaN is not equal to anything
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
        # to anything
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
        """Set the default label values for a data variable

        Parameters
        ----------
        data_var : str
            Name of the data variable

        Note
        ----
        Sets NaN for all float values, -1 for all int values, 'data_var' for
        names labels, '' for all other str values, and None for any other
        data type.

        """
        # Cycle through each label type to create a list off label names
        # and label default values
        labels = list()
        default_vals = list()
        for lattr in self.labels.label_type.keys():
            labels.append(getattr(self.labels, lattr))

            if lattr in ['name']:
                default_vals.append(data_var)
            else:
                default_vals.append(self.labels.default_values_from_attr(lattr))

        # Assign the default values to the DataFrame for this data variable
        self._data.loc[data_var, labels] = default_vals

        return

    def _label_setter(self, new_label, current_label, default_type,
                      use_names_default=False):
        """Generalized setter of default meta attributes

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
        return self._data

    @data.setter
    def data(self, new_frame):
        """ Set the data property

        Paramters
        ---------
        new_frame : pds.DataFrame
            Data frame containing the metadata, with label names as columns

        """
        self._data = new_frame

    @property
    def ho_data(self):
        return self._ho_data

    @ho_data.setter
    def ho_data(self, new_dict):
        """ Set the higher order data property

        Paramters
        ---------
        new_dict : dict
            Dict containing the higher order data

        """
        self._ho_data = new_dict

    @property
    def empty(self):
        """Return boolean True if there is no metadata

        Returns
        -------
        bool
            Returns True if there is no data, and False if there is data

        """

        # only need to check on lower data since lower data
        # is set when higher metadata assigned
        if self.data.empty:
            return True
        else:
            return False

    def merge(self, other):
        """Adds metadata variables to self that are in other but not in self.

        Parameters
        ----------
        other : pysat.Meta

        """

        for key in other.keys():
            if key not in self:
                # Copies over both lower and higher dimensional data
                self[key] = other[key]
        return

    def drop(self, names):
        """Drops variables (names) from metadata.

        Parameters
        ----------
        names : list-like
            List of string specifying the variable names to drop

        """

        # Drop the lower dimension data
        self.data = self._data.drop(names, axis=0)

        # Drop the higher dimension data
        for name in names:
            if name in self._ho_data:
                self._ho_data.pop(name)
        return

    def keep(self, keep_names):
        """Keeps variables (keep_names) while dropping other parameters

        Parameters
        ----------
        keep_names : list-like
            variables to keep

        """
        # Create a list of variable names to keep
        keep_names = [self.var_case_name(name) for name in keep_names]

        # Get a list of current variable names
        current_names = self._data.index

        # Build a list of variable names to drop
        drop_names = [name for name in current_names if name not in keep_names]

        # Drop names not specified in keep_names list
        self.drop(drop_names)
        return

    def apply_meta_labels(self, other_meta):
        """Applies the existing meta labels from self onto different MetaData

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
        """Applies labels for default meta labels from other onto self.

        Parameters
        ----------
        other_meta : Meta
            Meta object to take default labels from

        """

        # Update labels in metadata
        for key in other_meta.labels.label_type:
            new_name = getattr(other_meta.labels, key)
            old_name = getattr(self.labels, key)
            if old_name != new_name:
                self._label_setter(new_name, old_name,
                                   other_meta.labels.label_type[key],
                                   use_names_default=True)

        self.labels = other_meta.labels

        return

    def var_case_name(self, name):
        """Provides stored name (case preserved) for case insensitive input

        Parameters
        ----------
        name : str
            variable name in any case

        Returns
        -------
        out_name : str
            String with case preserved as in the meta object

        Note
        ----
        If name is not found (case-insensitive check) then name is returned,
        as input. This function is intended to be used to help ensure the
        case of a given variable name is the same across the Meta object.

        """

        # Get a lower-case version of the name
        lower_name = name.lower()

        # Cycle through all places where this variable name could be, returning
        # the variable name whose lower-case version matches the lower-case
        # version of the variable name supplied.
        if name in self:
            for out_name in self.keys():
                if lower_name == out_name.lower():
                    return out_name

            for out_name in self.keys_nD():
                if lower_name == out_name.lower():
                    return out_name
        else:
            out_name = name

        return out_name

    def keys(self):
        """Yields variable names stored for 1D variables"""

        for ikey in self.data.index:
            yield ikey

    def keys_nD(self):
        """Yields keys for higher order metadata"""

        for ndkey in self.ho_data:
            yield ndkey

    def attrs(self):
        """Yields metadata products stored for each variable name"""

        for dcol in self.data.columns:
            yield dcol

    def hasattr_case_neutral(self, attr_name):
        """Case-insensitive check for attribute names in this class

        Parameters
        ----------
        attr_name : str
            Name of attribute to find

        Returns
        -------
        has_name : bool
            True if case-insesitive check for attribute name is True

        Note
        ----
        Does not check higher order meta objects

        """
        has_name = False

        if attr_name.lower() in [dcol.lower() for dcol in self.data.columns]:
            has_name = True

        return has_name

    def attr_case_name(self, name):
        """Returns preserved case name for case insensitive value of name.

        Parameters
        ----------
        name : str
            Name of variable to get stored case form

        Returns
        -------
        out_name : str
            Name in proper case

        Note
        ----
        Checks first within standard attributes. If not found there, checks
        attributes for higher order data structures. If not found, returns
        supplied name as it is available for use. Intended to be used to help
        ensure that the same case is applied to all repetitions of a given
        variable name.

        """
        lower_name = name.lower()
        for out_name in self.attrs():
            if lower_name == out_name.lower():
                return out_name

        # check if attribute present in higher order structures
        for key in self.keys_nD():
            for out_name in self[key].children.attrs():
                if lower_name == out_name.lower():
                    return out_name

        # nothing was found if still here
        # pass name back, free to be whatever
        return name

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

        Note
        ----
        Uses units and name label of self if other_meta is different

        """

        mdata = self.copy()

        # Check the inputs
        if strict:
            for key in other_meta.keys():
                if key in mdata:
                    raise RuntimeError(''.join(('Duplicated keys (variable ',
                                                'names) across Meta ',
                                                'objects in keys().')))
            for key in other_meta.keys_nD():
                if key in mdata:
                    raise RuntimeError(''.join(('Duplicated keys (variable ',
                                                'names) across Meta '
                                                'objects in keys_nD().')))

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
        """Remove and return metadata about variable

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

    def transfer_attributes_to_instrument(self, inst, strict_names=False):
        """Transfer non-standard attributes in Meta to Instrument object.

        Parameters
        ----------
        inst : pysat.Instrument
            Instrument object to transfer attributes to
        strict_names : bool
            If True, produces an error if the Instrument object already
            has an attribute with the same name to be copied (default=False).

        Note
        ----
        pysat's load_netCDF and similar routines are only able to attach
        netCDF4 attributes to a Meta object. This routine identifies these
        attributes and removes them from the Meta object. Intent is to
        support simple transfers to the pysat.Instrument object.

        Will not transfer names that conflict with pysat default attributes.

        """

        # Save the base Instrument attributes
        banned = inst._base_attr

        # Current attributes
        inst_attr = dir(inst)

        # Get base attribute set, and attributes attached to instance
        base_attrb = self._base_attr
        this_attrb = dir(self)

        # Collect these attributes into a dict
        adict = {}
        transfer_key = []
        for key in this_attrb:
            if key not in banned:
                if key not in base_attrb:
                    # Don't store any hidden attributes
                    if key[0] != '_':
                        adict[key] = getattr(self, key)
                        transfer_key.append(key)
                        # remove key from meta
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
                        rerr = ''.join(('Attribute ', key, 'attached to the '
                                        'Meta object can not be transferred ',
                                        'as it already exists in the ',
                                        'Instrument object.'))
                        raise RuntimeError(rerr)
        return

    @classmethod
    def from_csv(cls, filename=None, col_names=None, sep=None, **kwargs):
        """Create instrument metadata object from csv.

        Parameters
        ----------
        filename : string
            absolute filename for csv file or name of file stored in pandas
            instruments location
        col_names : list-like collection of strings
            column names in csv and resultant meta object
        sep : string
            column seperator for supplied csv filename
        **kwargs : dict
            Optional kwargs used by pds.read_csv

        Note
        ----
        column names must include at least ['name', 'long_name', 'units'],
        assumed if col_names is None.

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

    # TODO
    # @classmethod
    # def from_nc():
    #     """not implemented yet, load metadata from netCDF"""
    #     pass
    #
    # @classmethod
    # def from_dict():
    #     """not implemented yet, load metadata from dict of items/list types
    #     """
    #     pass


class MetaLabels(object):
    """ Stores metadata labels for Instrument instance

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
    data : pandas.DataFrame
        index is variable standard name, 'units', 'long_name', and other
        defaults are also stored along with additional user provided labels.
    units : str
        String used to label units in storage. (default='units')
    name : str
        String used to label long_name in storage. (default='long_name')
    notes : str
       String used to label 'notes' in storage. (default='notes')
    desc : str
       String used to label variable descriptions in storage.
       (default='desc')
    min_val : str
       String used to label typical variable value min limit in storage.
       (default='value_min')
    max_val : str
       String used to label typical variable value max limit in storage.
       (default='value_max')
    fill_val : str
        String used to label fill value in storage. The default follows the
        netCDF4 standards (default='fill')

    Note
    ----
    Meta object preserves the case of variables and attributes as it first
    receives the data. Subsequent calls to set new metadata with the same
    variable or attribute will use case of first call. Accessing or setting
    data thereafter is case insensitive. In practice, use is case insensitive
    but the original case is preserved. Case preseveration is built in to
    support writing files with a desired case to meet standards.

    Metadata for higher order data objects, those that have
    multiple products under a single variable name in a pysat.Instrument
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
        """ Initialize the MetaLabels class

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
            Minimum value label name and value type
            (default=('value_min', float))
        max_val : tuple
            Maximum value label name and value type
            (default=('value_max', float))
        fill_val : tuple
            Fill value label name and value type (default=('fill', float))
        kwargs : dict
            Dictionary containing optional label attributes, where the keys
            are the attribute names and the values are tuples containing the
            label name and value type

        """
        # Initialize the coupled metadata
        self.meta = metadata

        # Initialize a dictionary of label types, whose keys are the label
        # attributes
        self.label_type = {'units': units[1], 'name': name[1],
                           'notes': notes[1], 'desc': desc[1],
                           'min_val': min_val[1], 'max_val': max_val[1],
                           'fill_val': fill_val[1]}

        # Set the default labels and types
        self.units = units[0]
        self.name = name[0]
        self.notes = notes[0]
        self.desc = desc[0]
        self.min_val = min_val[0]
        self.max_val = max_val[0]
        self.fill_val = fill_val[0]

        # Set the custom labels and label types
        for custom_label in kwargs.keys():
            setattr(self, custom_label, kwargs[custom_label][0])
            self.label_type[custom_label] = kwargs[custom_label][1]

        return

    def __setattr__(self, name, value):
        """Conditionally sets attributes based on their type

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
        """String describing MetaData instantiation parameters

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
        """String describing Meta instance, variables, and attributes

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

    def default_values_from_type(self, val_type):
        """ Return the default values for each label based on their type

        Parameters
        ----------
        val_type : type
            Variable type for the value to be assigned to a MetaLabel

        Returns
        -------
        default_val : str, float, int, NoneType
            Sets NaN for all float values, -1 for all int values, and '' for
            all str values except for 'scale', which defaults to 'linear', and
            None for any other data type

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
        """ Return the default values for each label based on their type

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
            For unknown attr_name

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
