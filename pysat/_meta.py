from __future__ import print_function
from __future__ import absolute_import

import os
import warnings
import numpy as np
import pandas as pds
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str

from pysat import DataFrame, Series


class Meta(object):
    """ Stores metadata for Instrument instance, similar to CF-1.6 netCDFdata
    standard.

    Parameters
    ----------
    metadata : pandas.DataFrame
        DataFrame should be indexed by variable name that contains at minimum
        the standard_name (name), units, and long_name for the data stored in
        the associated pysat Instrument object.

    units_label : str
        String used to label units in storage. Defaults to 'units'.
    name_label : str
        String used to label long_name in storage. Defaults to 'long_name'.
    notes_label : str
        String used to label 'notes' in storage. Defaults to 'notes'
    desc_label : str
        String used to label variable descriptions in storage.
        Defaults to 'desc'
    plot_label : str
        String used to label variables in plots. Defaults to 'label'
    axis_label : str
        Label used for axis on a plot. Defaults to 'axis'
    scale_label : str
        string used to label plot scaling type in storage. Defaults to 'scale'
    min_label : str
        String used to label typical variable value min limit in storage.
        Defaults to 'value_min'
    max_label : str
        String used to label typical variable value max limit in storage.
        Defaults to 'value_max'
    fill_label : str
        String used to label fill value in storage. Defaults to 'fill' per
        netCDF4 standard


    Attributes
    ----------
    data : pandas.DataFrame
        index is variable standard name, 'units', 'long_name', and other
        defaults are also stored along with additional user provided labels.

    units_label : str
        String used to label units in storage. Defaults to 'units'.
    name_label : str
        String used to label long_name in storage. Defaults to 'long_name'.
    notes_label : str
       String used to label 'notes' in storage. Defaults to 'notes'
    desc_label : str
       String used to label variable descriptions in storage.
       Defaults to 'desc'
    plot_label : str
       String used to label variables in plots. Defaults to 'label'
    axis_label : str
        Label used for axis on a plot. Defaults to 'axis'
    scale_label : str
       string used to label plot scaling type in storage. Defaults to 'scale'
    min_label : str
       String used to label typical variable value min limit in storage.
       Defaults to 'value_min'
    max_label : str
       String used to label typical variable value max limit in storage.
       Defaults to 'value_max'
    fill_label : str
        String used to label fill value in storage. Defaults to 'fill' per
        netCDF4 standard
    export_nan: list
        List of labels that should be exported even if their value is nan.
        By default, metadata with a value of nan will be exluded from export.


    Notes
    -----
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
    attributes (units, name, notes, desc, plot_label, axis, scale, value_min,
    value_max, and fill). These base attributes may be used to programatically
    access and set types of metadata regardless of the string values used for
    the attribute. String values for attributes may need to be changed
    depending upon the standards of code or files interacting with pysat.

    Meta objects returned as part of pysat loading routines are automatically
    updated to use the same values of plot_label, units_label, etc. as found
    on the pysat.Instrument object.

    Examples
    --------
    ::

        # instantiate Meta object, default values for attribute labels are used
        meta = pysat.Meta()
        # set a couple base units
        # note that other base parameters not set below will
        # be assigned a default value
        meta['name'] = {'long_name':string, 'units':string}
        # update 'units' to new value
        meta['name'] = {'units':string}
        # update 'long_name' to new value
        meta['name'] = {'long_name':string}
        # attach new info with partial information, 'long_name' set to 'name2'
        meta['name2'] = {'units':string}
        # units are set to '' by default
        meta['name3'] = {'long_name':string}

        # assigning custom meta parameters
        meta['name4'] = {'units':string, 'long_name':string
                         'custom1':string, 'custom2':value}
        meta['name5'] = {'custom1':string, 'custom3':value}

        # assign multiple variables at once
        meta[['name1', 'name2']] = {'long_name':[string1, string2],
                                    'units':[string1, string2],
                                    'custom10':[string1, string2]}

        # assiging metadata for n-Dimensional variables
        meta2 = pysat.Meta()
        meta2['name41'] = {'long_name':string, 'units':string}
        meta2['name42'] = {'long_name':string, 'units':string}
        meta['name4'] = {'meta':meta2}
        # or
        meta['name4'] = meta2
        meta['name4'].children['name41']

        # mixture of 1D and higher dimensional data
        meta = pysat.Meta()
        meta['dm'] = {'units':'hey', 'long_name':'boo'}
        meta['rpa'] = {'units':'crazy', 'long_name':'boo_whoo'}
        meta2 = pysat.Meta()
        meta2[['higher', 'lower']] = {'meta':[meta, None],
                                      'units':[None, 'boo'],
                                      'long_name':[None, 'boohoo']}

        # assign from another Meta object
        meta[key1] = meta2[key2]

        # access fill info for a variable, presuming default label
        meta[key1, 'fill']
        # access same info, even if 'fill' not used to label fill values
        meta[key1, meta.fill_label]


        # change a label used by Meta object
        # note that all instances of fill_label
        # within the meta object are updated
        meta.fill_label = '_FillValue'
        meta.plot_label = 'Special Plot Variable'
        # this feature is useful when converting metadata within pysat
        # so that it is consistent with externally imposed file standards

    """

    def __init__(self, metadata=None, units_label='units',
                 name_label='long_name', notes_label='notes',
                 desc_label='desc', plot_label='label', axis_label='axis',
                 scale_label='scale', min_label='value_min',
                 max_label='value_max', fill_label='fill',
                 export_nan=[]):

        # set mutability of Meta attributes
        self.mutable = True

        # set units and name labels directly
        self._units_label = units_label
        self._name_label = name_label
        self._notes_label = notes_label
        self._desc_label = desc_label
        self._plot_label = plot_label
        self._axis_label = axis_label
        self._scale_label = scale_label
        self._min_label = min_label
        self._max_label = max_label
        self._fill_label = fill_label
        # by default metadata with a value of nan will not be exported
        # unless the name is in the _export_nan list. Initialize the list
        # with the fill label, since it is reasonable to assume that a fill
        # value of nan would be intended to be exported
        self._export_nan = [fill_label] + export_nan
        # init higher order (nD) data structure container, a dict
        self._ho_data = {}
        # use any user provided data to instantiate object with data
        # attirube unit and name labels are called within
        if metadata is not None:
            if isinstance(metadata, DataFrame):
                self._data = metadata
                # make sure defaults are taken care of for required metadata
                self.accept_default_labels(self)
            else:
                raise ValueError(''.join(('Input must be a pandas DataFrame',
                                          'type. See other constructors for',
                                          ' alternate inputs.')))
        else:
            self._data = DataFrame(None, columns=[self._units_label,
                                                  self._name_label,
                                                  self._desc_label,
                                                  self._plot_label,
                                                  self._axis_label,
                                                  self._scale_label,
                                                  self.notes_label,
                                                  self._min_label,
                                                  self._max_label,
                                                  self._fill_label])

        # establish attributes intrinsic to object, before user can
        # add any
        self._base_attr = dir(self)

    @property
    def ho_data(self):
        return self._ho_data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_frame):
        self._data = new_frame
        # self.keys = self._data.columns.lower()

    @ho_data.setter
    def ho_data(self, new_dict):
        self._ho_data = new_dict

    @property
    def empty(self):
        """Return boolean True if there is no metadata"""

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
                # copies over both lower and higher dimensional data
                self[key] = other[key]

    def drop(self, names):
        """Drops variables (names) from metadata."""

        # drop lower dimension data
        self.data = self._data.drop(names, axis=0)
        # drop higher dimension data
        for name in names:
            if name in self._ho_data:
                _ = self._ho_data.pop(name)

    def keep(self, keep_names):
        """Keeps variables (keep_names) while dropping other parameters

        Parameters
        ----------
        keep_names : list-like
            variables to keep
        """
        keep_names = [self.var_case_name(name) for name in keep_names]
        current_names = self._data.index
        drop_names = []
        for name in current_names:
            if name not in keep_names:
                drop_names.append(name)
        self.drop(drop_names)

    def apply_default_labels(self, other):
        """Applies labels for default meta labels from self onto other.

        Parameters
        ----------
        other : Meta
            Meta object to have default labels applied

        Returns
        -------
        Meta

        """
        other_updated = other.copy()
        other_updated.units_label = self.units_label
        other_updated.name_label = self.name_label
        other_updated.notes_label = self.notes_label
        other_updated.desc_label = self.desc_label
        other_updated.plot_label = self.plot_label
        other_updated.axis_label = self.axis_label
        other_updated.scale_label = self.scale_label
        other_updated.min_label = self.min_label
        other_updated.max_label = self.max_label
        other_updated.fill_label = self.fill_label
        return other_updated

    def accept_default_labels(self, other):
        """Applies labels for default meta labels from other onto self.

        Parameters
        ----------
        other : Meta
            Meta object to take default labels from

        Returns
        -------
        Meta

        """

        self.units_label = other.units_label
        self.name_label = other.name_label
        self.notes_label = other.notes_label
        self.desc_label = other.desc_label
        self.plot_label = other.plot_label
        self.axis_label = other.axis_label
        self.scale_label = other.scale_label
        self.min_label = other.min_label
        self.max_label = other.max_label
        self.fill_label = other.fill_label
        return

    def __contains__(self, other):
        """case insensitive check for variable name"""

        if other.lower() in [i.lower() for i in self.keys()]:
            return True
        if other.lower() in [i.lower() for i in self.keys_nD()]:
            return True
        return False

    def __repr__(self):
        return 'pysat.MetaData'

    def __str__(self, recurse=True):
        """String describing Meta instance, variables, and attributes"""

        # cover 1D parameters
        if recurse:
            output_str = 'Metadata for 1D variables\n'
        else:
            output_str = ''

        for ind in self.keys():
            output_str += ind.ljust(30)
        output_str += '\n\n'
        output_str += 'Tracking the following:\n'
        for col in self.attrs():
            output_str += col.ljust(30)

        output_str += '\n'
        if recurse:
            for item_name in self.keys_nD():
                output_str += '\n\n'
                output_str += 'Metadata for '+item_name+'\n'
                output_str += self.ho_data[item_name].__str__(False)

        return output_str

    def _insert_default_values(self, input_name):

        default_str = ''
        default_nan = np.NaN
        labels = [self.units_label, self.name_label, self.notes_label,
                  self.desc_label, self.plot_label, self.axis_label,
                  self.scale_label, self.min_label, self.max_label,
                  self.fill_label]
        defaults = [default_str, input_name, default_str, default_str,
                    input_name, input_name, 'linear', default_nan,
                    default_nan, default_nan]
        self._data.loc[input_name, labels] = defaults


    def __setattr__(self, name, value):
        """Conditionally sets attributes based on self.mutable flag
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
                    raise AttributeError(''.join("can't set attribute - ",
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
                    raise AttributeError(''.join(("cannot set attribute - ",
                                                    "object's attributes are immutable")))
        else:
            super(Meta, self).__setattr__(name, value)


    def __setitem__(self, names, input_data):
        """Convenience method for adding metadata."""

        if isinstance(input_data, dict):
            # if not passed an iterable, make it one
            if isinstance(names, basestring):
                names = [names]
                for key in input_data:
                    input_data[key] = [input_data[key]]
            elif isinstance(names, slice) and (names.step is None):
                # Check for instrument[indx,:] or instrument[idx] usage
                names = list(self.data.keys())
            # make sure the variable names are in good shape
            # Meta object is case insensitive but case preserving
            # convert given names into ones Meta has already seen
            # if new, then input names become the standard
            names = [self.var_case_name(name) for name in names]
            for name in names:
                if name not in self:
                    self._insert_default_values(name)
            # check if input dict empty
            if input_data.keys() == []:
                # meta wasn't actually assigned by user, empty call
                # we can head out - we've assigned defaults if first data
                return
            # perform some checks on the data
            # make sure number of inputs matches number of metadata inputs
            for key in input_data:
                if len(names) != len(input_data[key]):
                    raise ValueError(''.join(('Length of names and inputs',
                                              ' must be equal.')))
            # make sure the attribute names are in good shape
            # check name of attributes against existing attribute names
            # if attribute name exists somewhere, then case of existing
            # attribute
            # will be enforced upon new data by default for consistency
            keys = [i for i in input_data]
            for name in keys:
                new_name = self.attr_case_name(name)
                if new_name != name:
                    input_data[new_name] = input_data.pop(name)

            # time to actually add the metadata
            for key in input_data:
                if key not in ['children', 'meta']:
                    for i, name in enumerate(names):
                        to_be_set = input_data[key][i]
                        if hasattr(to_be_set, '__iter__') and \
                                not isinstance(to_be_set, basestring):
                            # we have some list-like object
                            # can only store a single element
                            if len(to_be_set) == 0:
                                # empty list, ensure there is something
                                to_be_set = ['']
                            if isinstance(to_be_set[0], basestring):
                                self._data.loc[name, key] = \
                                    '\n\n'.join(to_be_set)
                            else:
                                warnings.warn(' '.join(('Array elements are',
                                                        'not allowed in meta.',
                                                        'Dropping input :',
                                                        key)))
                        else:
                            self._data.loc[name, key] = to_be_set
                else:
                    # key is 'meta' or 'children'
                    # process higher order stuff. Meta inputs could be part of
                    # larger multiple parameter assignment
                    # so not all names may actually have 'meta' to add
                    for j, (item, val) in enumerate(zip(names,
                                                        input_data['meta'])):
                        if val is not None:
                            # assign meta data, recursive call....
                            # heads to if Meta instance call
                            self[item] = val

        elif isinstance(input_data, Series):
            # outputs from Meta object are a Series.
            # thus this takes in input from a Meta object
            # set data usind standard assignment via a dict
            in_dict = input_data.to_dict()
            if 'children' in in_dict:
                child = in_dict.pop('children')
                if child is not None:
                    # if not child.data.empty:
                    self.ho_data[names] = child
            # remaining items are simply assigned
            self[names] = in_dict

        elif isinstance(input_data, Meta):
            # dealing with higher order data set
            # names is only a single name here (by choice for support)
            if (names in self._ho_data) and (input_data.empty):
                # no actual metadata provided and there is already some
                # higher order metadata in self
                return

            # get Meta approved variable names
            new_item_name = self.var_case_name(names)
            # ensure that Meta labels of object to be assigned
            # are consistent with self
            # input_data accepts self's labels
            input_data.accept_default_labels(self)

            # go through and ensure Meta object to be added has variable and
            # attribute names consistent with other variables and attributes
            # this covers custom attributes not handled by default routine
            # above
            attr_names = input_data.attrs()
            new_names = []
            for name in attr_names:
                new_names.append(self.attr_case_name(name))
            input_data.data.columns = new_names
            # same thing for variables
            var_names = input_data.data.index
            new_names = []
            for name in var_names:
                new_names.append(self.var_case_name(name))
            input_data.data.index = new_names
            # assign Meta object now that things are consistent with Meta
            # object settings
            # but first, make sure there are lower dimension metadata
            # parameters, passing in an empty dict fills in defaults
            # if there is no existing metadata info
            self[new_item_name] = {}
            # now add to higher order data
            self._ho_data[new_item_name] = input_data

    def __getitem__(self, key):
        """Convenience method for obtaining metadata.

        Maps to pandas DataFrame.loc method.

        Examples
        --------
        ::

            meta['name']

            meta[ 'name1', 'units' ]

            meta[[ 'name1', 'name2'], 'units']

            meta[:, 'units']

            for higher order data

            meta[ 'name1', 'subvar', 'units' ]

            meta[ 'name1', ('units', 'scale') ]

        """
        # if key is a tuple, looking at index, column access pattern

        def match_name(func, name, names):
            """Applies func on name(s) depending on name type"""
            if isinstance(name, basestring):
                return func(name)
            elif isinstance(name, slice):
                return [func(nn) for nn in names[name]]
            else:
                # assume iterable
                return [func(nn) for nn in name]

        if isinstance(key, tuple):
            # if tuple length is 2, index, column
            if len(key) == 2:
                new_index = match_name(self.var_case_name, key[0],
                                        self.data.index)
                new_name = match_name(self.attr_case_name, key[1],
                                        self.data.columns)
                return self.data.loc[new_index, new_name]

            # if tuple length is 3, index, child_index, column
            elif len(key) == 3:
                new_index = self.var_case_name(key[0])
                new_child_index = self.var_case_name(key[1])
                new_name = self.attr_case_name(key[2])
                return self.ho_data[new_index].data.loc[new_child_index,
                                                        new_name]

        elif isinstance(key, list):
            return self[key, :]

        elif isinstance(key, basestring):
            # ensure variable is present somewhere
            if key in self:
                # get case preserved string for variable name
                new_key = self.var_case_name(key)
                # if new_key in self.keys():
                # don't need to check if in lower, all variables
                # are always in the lower metadata
                meta_row = self.data.loc[new_key]
                if new_key in self.keys_nD():
                    meta_row.at['children'] = self.ho_data[new_key].copy()
                else:
                    # empty_meta = Meta()
                    # self.apply_default_labels(empty_meta)
                    # Following line issues a pandas SettingWithCopyWarning
                    meta_row.at['children'] = None  # empty_meta
                return meta_row
                # else:
                #     return pds.Series([self.ho_data[new_key].copy()],
                #                       index=['children'])
            else:
                raise KeyError('Key not found in MetaData')
        else:
            raise NotImplementedError("No way to handle MetaData key {}".format(
                key.__repr__()))

    def _label_setter(self, new_label, current_label, attr_label,
                      default=np.NaN, use_names_default=False):
        """Generalized setter of default meta attributes

        Parameters
        ----------
        new_label : str
            New label to use in the Meta object
        current_label : str
            The hidden attribute to be updated that actually stores metadata
        default :
            Deafult setting to use for label if there is no attribute
            value
        use_names_default : bool
            if True, MetaData variable names are used as the default
            value for the specified Meta attributes settings

        Examples
        --------
        :
                @name_label.setter
                def name_label(self, new_label):
                    self._label_setter(new_label, self._name_label,
                                        use_names_default=True)

        Notes
        -----
        Not intended for end user

        """

        if new_label not in self.attrs():
            # new label not in metadata, including case
            # update existing label, if present
            if current_label in self.attrs():
                # old label exists and has expected case
                self.data.loc[:, new_label] = self.data.loc[:, current_label]
                self.data.drop(current_label, axis=1, inplace=True)
            else:
                if self.has_attr(current_label):
                    # there is something like label, wrong case though
                    current_label = self.attr_case_name(current_label)
                    self.data.loc[:, new_label] = \
                        self.data.loc[:, current_label]
                    self.data.drop(current_label, axis=1, inplace=True)
                else:
                    # there is no existing label
                    # setting for the first time
                    if use_names_default:
                        self.data[new_label] = self.data.index
                    else:
                        self.data[new_label] = default
            # check higher order structures as well
            # recursively change labels here
            for key in self.keys_nD():
                setattr(self.ho_data[key], attr_label, new_label)

        # now update 'hidden' attribute value
        # current_label = new_label
        setattr(self, ''.join(('_', attr_label)), new_label)

    @property
    def units_label(self):
        return self._units_label

    @property
    def name_label(self):
        return self._name_label

    @property
    def notes_label(self):
        return self._notes_label

    @property
    def desc_label(self):
        return self._desc_label

    @property
    def plot_label(self):
        return self._plot_label

    @property
    def axis_label(self):
        return self._axis_label

    @property
    def scale_label(self):
        return self._scale_label

    @property
    def min_label(self):
        return self._min_label

    @property
    def max_label(self):
        return self._max_label

    @property
    def fill_label(self):
        return self._fill_label

    @units_label.setter
    def units_label(self, new_label):
        self._label_setter(new_label, self._units_label, 'units_label', '')

    @name_label.setter
    def name_label(self, new_label):
        self._label_setter(new_label, self._name_label, 'name_label',
                           use_names_default=True)

    @notes_label.setter
    def notes_label(self, new_label):
        self._label_setter(new_label, self._notes_label, 'notes_label', '')

    @desc_label.setter
    def desc_label(self, new_label):
        self._label_setter(new_label, self._desc_label, 'desc_label', '')

    @plot_label.setter
    def plot_label(self, new_label):
        self._label_setter(new_label, self._plot_label, 'plot_label',
                           use_names_default=True)

    @axis_label.setter
    def axis_label(self, new_label):
        self._label_setter(new_label, self._axis_label, 'axis_label',
                           use_names_default=True)

    @scale_label.setter
    def scale_label(self, new_label):
        self._label_setter(new_label, self._scale_label, 'scale_label',
                           'linear')

    @min_label.setter
    def min_label(self, new_label):
        self._label_setter(new_label, self._min_label, 'min_label', np.NaN)

    @max_label.setter
    def max_label(self, new_label):
        self._label_setter(new_label, self._max_label, 'max_label', np.NaN)

    @fill_label.setter
    def fill_label(self, new_label):
        self._label_setter(new_label, self._fill_label, 'fill_label', np.NaN)

    def var_case_name(self, name):
        """Provides stored name (case preserved) for case insensitive input

        If name is not found (case-insensitive check) then name is returned,
        as input. This function is intended to be used to help ensure the
        case of a given variable name is the same across the Meta object.

        Parameters
        ----------
        name : str
            variable name in any case

        Returns
        -------
        str
            string with case preserved as in metaobject

        """

        lower_name = name.lower()
        if name in self:
            for i in self.keys():
                if lower_name == i.lower():
                    return i
            for i in self.keys_nD():
                if lower_name == i.lower():
                    return i
        return name

    def keys(self):
        """Yields variable names stored for 1D variables"""

        for i in self.data.index:
            yield i

    def keys_nD(self):
        """Yields keys for higher order metadata"""

        for i in self.ho_data:
            yield i

    def attrs(self):
        """Yields metadata products stored for each variable name"""

        for i in self.data.columns:
            yield i

    def has_attr(self, name):
        """Returns boolean indicating presence of given attribute name

        Case-insensitive check

        Notes
        -----
        Does not check higher order meta objects

        Parameters
        ----------
        name : str
            name of variable to get stored case form

        Returns
        -------
        bool
            True if case-insesitive check for attribute name is True

        """

        if name.lower() in [i.lower() for i in self.data.columns]:
            return True
        return False

    def attr_case_name(self, name):
        """Returns preserved case name for case insensitive value of name.

        Checks first within standard attributes. If not found there, checks
        attributes for higher order data structures. If not found, returns
        supplied name as it is available for use. Intended to be used to help
        ensure that the same case is applied to all repetitions of a given
        variable name.

        Parameters
        ----------
        name : str
            name of variable to get stored case form

        Returns
        -------
        str
            name in proper case
        """

        lower_name = name.lower()
        for i in self.attrs():
            if lower_name == i.lower():
                return i
        # check if attribute present in higher order structures
        for key in self.keys_nD():
            for i in self[key].children.attrs():
                if lower_name == i.lower():
                    return i
        # nothing was found if still here
        # pass name back, free to be whatever
        return name

    def concat(self, other, strict=False):
        """Concats two metadata objects together.

        Parameters
        ----------
        other : Meta
            Meta object to be concatenated
        strict : bool
            if True, ensure there are no duplicate variable names

        Notes
        -----
        Uses units and name label of self if other is different

        Returns
        -------
        Meta
            Concatenated object
        """

        mdata = self.copy()
        # checks
        if strict:
            for key in other.keys():
                if key in mdata:
                    raise RuntimeError(''.join(('Duplicated keys (variable ',
                                                'names) across Meta ',
                                                'objects in keys().')))
            for key in other.keys_nD():
                if key in mdata:

                    raise RuntimeError(''.join(('Duplicated keys (variable ',
                                                'names) across Meta '
                                                'objects in keys_nD().')))

        # make sure labels between the two objects are the same
        other_updated = self.apply_default_labels(other)
        # concat 1D metadata in data frames to copy of
        # current metadata
        for key in other_updated.keys():
            mdata.data.loc[key] = other.data.loc[key]
        # add together higher order data
        for key in other_updated.keys_nD():
            mdata.ho_data[key] = other.ho_data[key]

        return mdata

    def copy(self):
        from copy import deepcopy as deepcopy
        """Deep copy of the meta object."""
        return deepcopy(self)

    def pop(self, name):
        """Remove and return metadata about variable

        Parameters
        ----------
        name : str
            variable name

        Returns
        -------
        pandas.Series
            Series of metadata for variable
        """
        # check if present
        if name in self:
            # get case preserved name for variable
            new_name = self.var_case_name(name)
            # check if 1D or nD
            if new_name in self.keys():
                output = self[new_name]
                self.data.drop(new_name, inplace=True, axis=0)
            else:
                output = self.ho_data.pop(new_name)

            return output
        else:
            raise KeyError('Key not present in metadata variables')

    def transfer_attributes_to_instrument(self, inst, strict_names=False):
        """Transfer non-standard attributes in Meta to Instrument object.

        Pysat's load_netCDF and similar routines are only able to attach
        netCDF4 attributes to a Meta object. This routine identifies these
        attributes and removes them from the Meta object. Intent is to
        support simple transfers to the pysat.Instrument object.

        Will not transfer names that conflict with pysat default attributes.

        Parameters
        ----------
        inst : pysat.Instrument
            Instrument object to transfer attributes to
        strict_names : boolean (False)
            If True, produces an error if the Instrument object already
            has an attribute with the same name to be copied.

        Returns
        -------
        None
            pysat.Instrument object modified in place with new attributes
        """

        # base Instrument attributes
        banned = inst._base_attr
        # get base attribute set, and attributes attached to instance
        base_attrb = self._base_attr
        this_attrb = dir(self)
        # collect these attributes into a dict
        adict = {}
        transfer_key = []
        for key in this_attrb:
            if key not in banned:
                if key not in base_attrb:
                    # don't store _ leading attributes
                    if key[0] != '_':
                        adict[key] = self.__getattribute__(key)
                        transfer_key.append(key)

        # store any non-standard attributes in Instrument
        # get list of instrument objects attributes first
        # to check if a duplicate

        # instrument attributes are now inst.meta attributes
        inst_attr = dir(inst)

        for key in transfer_key:
            if key not in banned:
                if key not in inst_attr:
                    inst.__setattr__(key, adict[key])
                else:
                    if not strict_names:
                        # new_name = 'pysat_attr_'+key
                        inst.__setattr__(key, adict[key])
                    else:
                        raise RuntimeError(''.join(('Attribute ', key,
                                                    ' attached to Meta object',
                                                    ' can not be transferred',
                                                    ' as it already exists in',
                                                    ' the Instrument object.'
                                                    )))
        # return inst

    def __eq__(self, other):
        """
        Check equality between Meta instances. Good for testing.

        Checks if variable names, attribute names, and metadata values
        are all equal between to Meta objects. Note that this comparison
        treats np.NaN == np.NaN as True.

        Name comparison is case-sensitive.

        """

        if isinstance(other, Meta):
            # check first if variables and attributes are the same
            # quick check on length
            keys1 = [i for i in self.keys()]
            keys2 = [i for i in other.keys()]
            if len(keys1) != len(keys2):
                return False
            # now iterate over each of the keys in the first one
            # don't need to iterate over second one, if all of the first
            # in the second we are good. No more or less items in second from
            # check earlier.
            for key in keys1:
                if key not in keys2:
                    return False
            # do same checks on attributes
            attrs1 = [i for i in self.attrs()]
            attrs2 = [i for i in other.attrs()]
            if len(attrs1) != len(attrs2):
                return False
            for attr in attrs1:
                if attr not in attrs2:
                    return False
            # now check the values of all elements now that we know all
            # variable and attribute names are the same
            for key in self.keys():
                for attr in self.attrs():
                    if not (self[key, attr] == other[key, attr]):
                        # np.nan is not equal to anything
                        # if both values are NaN, ok in my book
                        try:
                            if not (np.isnan(self[key, attr]) and
                                    np.isnan(other[key, attr])):
                                # one or both are not NaN and they aren't equal
                                # test failed
                                return False
                        except TypeError:
                            # comparison above gets unhappy with string inputs
                            return False

            # check through higher order products
            # in the same manner as code above
            keys1 = [i for i in self.keys_nD()]
            keys2 = [i for i in other.keys_nD()]
            if len(keys1) != len(keys2):
                return False
            for key in keys1:
                if key not in keys2:
                    return False
            # do same check on all sub variables within each nD key
            for key in self.keys_nD():
                keys1 = [i for i in self[key].children.keys()]
                keys2 = [i for i in other[key].children.keys()]
                if len(keys1) != len(keys2):
                    return False
                for key_check in keys1:
                    if key_check not in keys2:
                        return False
                # check if attributes are the same
                attrs1 = [i for i in self[key].children.attrs()]
                attrs2 = [i for i in other[key].children.attrs()]
                if len(attrs1) != len(attrs2):
                    return False
                for attr in attrs1:
                    if attr not in attrs2:
                        return False
                # now time to check if all elements are individually equal
                for key2 in self[key].children.keys():
                    for attr in self[key].children.attrs():
                        if not (self[key].children[key2, attr] ==
                                other[key].children[key2, attr]):
                            try:
                                if not (np.isnan(self[key].children[key2,
                                                                    attr]) and
                                        np.isnan(other[key].children[key2,
                                                                     attr])):
                                    return False
                            except TypeError:
                                # comparison above gets unhappy with string
                                # inputs
                                return False
            # if we made it this far, things are good
            return True
        else:
            # wasn't even the correct class
            return False

    @classmethod
    def from_csv(cls, name=None, col_names=None, sep=None, **kwargs):
        """Create instrument metadata object from csv.

        Parameters
        ----------
        name : string
            absolute filename for csv file or name of file
            stored in pandas instruments location
        col_names : list-like collection of strings
            column names in csv and resultant meta object
        sep : string
            column seperator for supplied csv filename

        Note
        ----
        column names must include at least ['name', 'long_name', 'units'],
        assumed if col_names is None.
        """
        import pysat
        req_names = ['name', 'long_name', 'units']
        if col_names is None:
            col_names = req_names
        elif not all([i in col_names for i in req_names]):
            raise ValueError('col_names must include name, long_name, units.')

        if sep is None:
            sep = ','

        if name is None:
            raise ValueError('Must supply an instrument name or file path.')
        elif not isinstance(name, str):
            raise ValueError('keyword name must be related to a string')
        elif not os.path.isfile(name):
            # Not a real file, assume input is a pysat instrument name
            # and look in the standard pysat location.
            test = os.path.join(pysat.__path__[0], 'instruments', name)
            if os.path.isfile(test):
                name = test
            else:
                # trying to form an absolute path for success
                test = os.path.abspath(name)
                if not os.path.isfile(test):
                    raise ValueError("Unable to create valid file path.")
                else:
                    # success
                    name = test

        mdata = pds.read_csv(name, names=col_names, sep=sep, **kwargs)

        if not mdata.empty:
            # make sure the data name is the index
            mdata.index = mdata['name']
            del mdata['name']
            return cls(metadata=mdata)
        else:
            raise ValueError('Unable to retrieve information from ' + name)

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
