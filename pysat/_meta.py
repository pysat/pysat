from __future__ import print_function
from __future__ import absolute_import

import os
import pandas as pds
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str
    
from pysat import DataFrame, Series

class Meta(object):
    """
    Stores metadata for Instrument instance, similar to CF-1.6 netCDFdata standard.
    
    Parameters
    ----------
    metadata : pandas.DataFrame 
        DataFrame should be indexed by variable name that contains at minimum the 
        standard_name (name), units, and long_name for the data stored in the associated 
        pysat Instrument object.
    units_label : str
        String used to label units in storage. Defaults to 'units'. 
    name_label : str
        String used to label long_name in storage. Defaults to 'long_name'. 
        
        
    Attributes
    ----------
    data : pandas.DataFrame
        index is variable standard name, 'units' and 'long_name' are also stored along
        with additional user provided labels.
    units_label : str
        string used to identify units
    name_label : str
        string used to idensity variable names
        
    Notes
    -----
    Meta object preserves the case of variables and attributes as it first 
    receives the data. Subsequent calls to set new metadata with the same variable
    or attribute will use case of first call. Accessing or setting data thereafter
    is case insensitive. In practice, use is case insensitive but the original
    case is preserved. Case preseveration is built in to support writing
    files with a desired case to meet standards.

    Metadata for higher order data objects, those that have
    multiple products under a single variable name in a pysat.Instrument
    object, are stored by providing a Meta object under the single name.
        
    Examples
    --------
    ::
        
        meta = pysat.Meta()
        meta['name'] = {'long_name':string, 'units':string}
        # update 'units' to new value
        meta['name'] = {'units':string}
        # update 'long_name' to new value
        meta['name'] = {'long_name':string}
        # attach new info with partial information, 'long_name' set to 'name2'
        meta['name2'] = {'units':string}
        # units are set to '' by default
        meta['name3'] = {'long_name':string}
        
        # assign multiple variables at once
        meta[['name1', 'name2']] = {'long_name':[string1, string2], 
                                    'units':[string1, string2]}
        
        # assiging metadata for n-Dimensional variables
        meta2 = pysat.Meta()
        meta2['name41'] = {'long_name':string, 'units':string}
        meta2['name42'] = {'long_name':string, 'units':string}
        meta['name4'] = {'meta':meta2}
        # or
        meta['name4'] = meta2
        meta['name4']['name41']
        
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
        
    """
    def __init__(self, metadata=None, units_label='units', name_label='long_name'):
        # set units and name labels directly
        self._units_label = units_label
        self._name_label = name_label
        # init higher order (nD) data structure container, a dict
        self._ho_data = {}
        # use any user provided data to instantiate object with data
        # attirube unit and name labels are called within
        self.replace(metadata=metadata)
        # establish attributes intrinsic to object, before user could
        # add any
        self._base_attr = dir(self)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False
    
    def __contains__(self, other):
        """case insensitive check for variable name"""
        
        if other.lower() in [i.lower() for i in self.keys()]:
            return True
        if other.lower() in [i.lower() for i in self.keys_nD()]:
            return True
        return False

    def __repr__(self, recurse=True):
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
                output_str += self._ho_data[item_name].__repr__(False)

        return output_str

    def __setitem__(self, name, value):
        """Convenience method for adding metadata."""
        
        if isinstance(value, dict):
            # check if dict empty
            if value.keys() == []:
                # null input, variable name provided but no metadata is actually
                # included. Everything should be set to default.
                if isinstance(name, basestring):
                    if name in self:
                        # variable already exists and we don't have anything
                        # new to add, just leave
                        return
                    # otherwise, continue on and set defaults
                else:
                    new_name = []
                    for n in name:
                        if n not in self:
                            new_name.append(n)
                    name = new_name
                    if len(name) == 0:
                        # all variables already exist, can simply leave
                        return
                    else:
                        # otherwise, continue on and set defaults
                        # create empty input for all remaining names
                        value = {}
                        value[self.units_label] = ['']*len(name)
                        value[self.name_label] = name
            
            # perform some checks on the data
            # if not passed an iterable, make it one
            if isinstance(name, basestring):
                name = [name]
                for key in value.keys():
                    value[key] = [value[key]]
            # make sure number of inputs matches number of metadata inputs
            for key in value.keys():
                if len(name) != len(value[key]):
                    raise ValueError('Length of names and inputs must be equal.')

            if 'meta' in value.keys():
                # process higher order stuff first
                # could be part of multiple assignment
                # so assign the Meta objects, then remove all trace
                # of names with Meta
                pop_list = []
                pop_loc = []
                for j, (item, val) in enumerate(zip(name, value['meta'])):
                    if val is not None:
                        # assign meta data, recursive call....
                        self[item] = val
                        pop_list.append(item)
                        pop_loc.append(j)
                        
                # remove 'meta' objects from input
                if len(value.keys()) > 1:
                    _ = value.pop('meta')
                else:
                    value = {}
                    name = []
                    
                for item, loc in zip(pop_list[::-1], pop_loc[::-1]):
                    # remove data names that had a Meta object assigned
                    # they are not part of any future processing
                    if len(name) > 1:
                        _ = name.pop(loc)
                    else:
                        name = []
                    # remove place holder data in other values that used
                    # to have to account for presence of Meta object
                    # going through backwards so I don't mess with location references
                    for key in value.keys():
                        _ = value[key].pop(loc)

            # check if 'units' has been provided
            # check against units_label, case insensitive
            lower_keys = [k.lower() for k in value.keys()]
            if self.units_label.lower() not in lower_keys:
                # 'units' not provided
                # provide default value, or copy existing
                value[self.units_label] = []
                for item_name in name:
                    if item_name not in self:
                        # overall variable not in Meta, can use default
                        # 'default'
                        value[self.units_label].append('')
                    else:
                        # copy existing
                        value[self.units_label].append(self[item_name, self.units_label])
            elif self.units_label not in value.keys():
                # 'units' was provided, however the case 
                # provided doesn't match up with _units_label
                # make it match
                for unit_key, lower_key in zip(value.keys(), lower_keys):
                    if lower_key == self.units_label.lower():
                        # print('popping units_key ', unit_key)
                        value[self.units_label] = value.pop(unit_key)
                        break
            # check if 'long_name' has been provided
            # check against name_label, case insensitive
            lower_keys = [k.lower() for k in value.keys()]
            if self.name_label.lower() not in lower_keys:
                # provide default value, or copy existing
                value[self.name_label] = []
                for item_name in name:
                    if item_name not in self:
                        value[self.name_label].append(item_name)
                    else:
                        value[self.name_label].append(self[item_name, self.name_label])
            elif self.name_label not in value.keys():
                # case of 'units' provided doesn't match up with _name_label
                # make it match
                for label_key, lower_key in zip(value.keys(), lower_keys):
                    if lower_key == self.name_label.lower():
                        # print('popping label_key ', label_key)
                        value[self.name_label] = value.pop(label_key)
                        break

            # check name of attributes against existing attribute names
            # if attribute name exists somewhere, then case will be matched
            # by default for consistency
            keys = value.keys()
            for key in keys:
                new_key = self.attr_case_name(key)
                value[new_key] = value.pop(key)
                
            # time to actually add the metadata
            if len(name) > 0:
                # make sure there is still something to add
                new = DataFrame(value, index=name)
                for item_name, item in new.iterrows():
                    if item_name not in self:
                        self.data = self.data.append(item)
                    else:
                        # info already exists, update with new info
                        new_item_name = self.var_case_name(item_name)
                        for item_key in item.keys():
                            self.data.loc[new_item_name, item_key] = item[item_key]

        elif isinstance(value, Series):
            # check 
            if name in self:
                new_item_name = self.var_case_name(name)
            else:
                new_item_name = name
                            
            # check attribute names against existing entries
            new_index = [self.attr_case_name(ind) for ind in value.index]
            value.index = new_index
            # pandas handles missing data during assignment
            self.data.loc[new_item_name] = value
            # need to do a check here on units and name labels

        elif isinstance(value, Meta):
            # dealing with higher order data set
            if name in self:
                new_item_name = self.var_case_name(name)
            else:
                new_item_name = name
            # ensure that units and name labels are always consistent
            value.units_label = self.units_label
            value.name_label = self.name_label
            # go through and ensure Meta object to be added has variable and
            # attribute names consistent with other variables and attributes
            names = value.data.columns
            new_names = []
            for name in names:
                new_names.append(self.attr_case_name(name))
            value.data.columns = new_names
            names = value.data.index
            new_names = []
            for name in names:
                new_names.append(self.var_case_name(name))
            value.data.index = new_names

            self._ho_data[new_item_name] = value

    def __getitem__(self, key):
        """Convenience method for obtaining metadata.
        
        Maps to pandas DataFrame.loc method.
        
        Examples
        --------
        ::
        
            meta['name']
            
            meta[ 'name1', 'units' ]
        
        """

        # if key is a tuple, looking at index, column access pattern
        if isinstance(key, tuple):
            new_index = self.var_case_name(key[0])
            new_name = self.attr_case_name(key[1])
            return self.data.loc[new_index, new_name]        
      
        else:
            if key in self:
                # ensure variable is present somewhere
                new_key = self.var_case_name(key)
                # single variable request
                if new_key in self.keys_nD():
                    # higher order data
                    return self._ho_data[new_key]
                elif new_key in self.keys():
                    # plain old variable request
                    return self.data.loc[new_key]
            else:
                raise KeyError('Key not found in MetaData')
        
    @property
    def units_label(self):
        return self._units_label

    @units_label.setter        
    def units_label(self, value=None):
        """Update units_label employed by Metaobject and update attributes"""
        if value not in self.attrs():
            # update existing units label, if present
            if self.units_label in self.attrs():
                self.data.loc[:, value] = self.data.loc[:, self.units_label]
                self.data.drop(self.units_label, axis=1, inplace=True)
            # check higher order structures as well
            for key in self.keys_nD():
                if self.units_label in self[key].attrs():
                    self[key].data.loc[:, value] = self[key].data.loc[:, self.units_label]
                    self[key].data.drop(self.units_label, axis=1, inplace=True)
            
        self._units_label = value
                                       
    @property
    def name_label(self):
        return self._name_label
        
    @name_label.setter        
    def name_label(self, value=None):
        """Update name_label employed by Metaobject and update attributes"""
        if value not in self.attrs():
            if self.name_label in self.attrs():
                self.data.loc[:, value] = self.data.loc[:, self.name_label]
                self.data.drop(self.name_label, axis=1, inplace=True)
            # check higher order structures as well
            for key in self.keys_nD():
                if self.name_label in self[key].attrs():
                    self[key].data.loc[:, value] = self[key].data.loc[:, self.name_label]
                    self[key].data.drop(self.name_label, axis=1, inplace=True)

        self._name_label = value
        
    def var_case_name(self, name):
        """Provides stored name (case preserved) for case insensitive input
        
        Parameters
        ----------
        name : str
            variable name in any case
            
        Returns
        -------
        str
            string with case preserved as in metaobject
            
        """
        
        if name in self:
            for i in self.keys():
                if name.lower() == i.lower():
                    return i
            for i in self.keys_nD():
                if name.lower() == i.lower():
                    return i
        return name

    def keys(self):
        """Yields variable names stored for 1D variables"""
        
        for i in self.data.index:
            yield i
    
    def keys_nD(self):
        """Yields keys for higher order metadata"""
        
        for i in self._ho_data.keys():
            yield i

    def keypairs_ho(self):
        """Yields keypairs for higher order metadata, (key1, attribute1) """
        
        for i in self._ho_data.keys():
            for j in self[i].keys:
                yield (i, j)

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
        attributes for higher order data structures. IF not found, returns supplied 
        name. It is available for use.
        
        Parameters
        ----------
        name : str
            name of variable to get stored case form
            
        Returns
        -------
        str
            name in proper case
        
        """
        
        for i in self.attrs():
            if name.lower() == i.lower():
                return i
        # check if attribute present in higher order structures
        for key in self.keys_nD():
            for i in self[key].attrs():
                if name.lower() == i.lower():
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
                    raise RuntimeError('Duplicated keys (variable names) across '
                                        'Meta objects in keys().')
        for key in other.keys_nD():
            if key in mdata:
                raise RuntimeError('Duplicated keys (variable names) across '
                                    'Meta objects in keys_nD().')
        # concat 1D metadata in data frames to copy of
        # current metadata
        for key in other.keys():
            mdata[key] = other[key]
        # add together higher order data
        for key in other.keys_nD():
            mdata[key] = other[key]
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
        
        if name in self:
            # get case preserved name for variable
            new_name = self.var_case_name(name)
            # check if 1D or nD
            if new_name in self.keys():
                output = self[new_name]
                self.data.drop(new_name, inplace=True, axis=0)
            else:
                output = self._ho_data.pop(new_name)
                
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
                        raise RuntimeError('Attribute ' + key +  'attached to Meta object '+
                                             'can not be transferred as it already exists in the Instrument object.')
        # return inst

    def replace(self, metadata=None):
        """Replace stored metadata with input data.
        
        Parameters
        ----------
        metadata : pandas.DataFrame 
            DataFrame should be indexed by variable name that contains at minimum the 
            standard_name (name), units, and long_name for the data stored in the associated 
            pysat Instrument object.
            
        """
        if metadata is not None:
            if isinstance(metadata, DataFrame):
                self.data = metadata
                lower_columns = [name.lower() for name in self.data.columns]
                if self.name_label.lower() not in lower_columns:
                    self.data[self.name_label] = self.data.index                    
                if self.units_label.lower() not in lower_columns:
                    self.data[self.units_label] = ''
                # make sure case of name and units labels are correct
                # if they were provided by user
                # going to reset labels to current values, this will 
                # trigger a name check and corrections
                self.units_label = self.units_label
                self.name_label = self.name_label
            else:
                raise ValueError("Input must be a pandas DataFrame type. "+
                            "See other constructors for alternate inputs.")
        else:
            self.data = DataFrame(None, columns=[self.name_label, self.units_label])
        
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
        req_names = ['name','long_name','units']
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
                test =  os.path.join(pysat.__path__[0],'instruments',name)
                if os.path.isfile(test):
                    name = test
                else:
                    #trying to form an absolute path for success
                    test = os.path.abspath(name)
                    if not os.path.isfile(test):
                        raise ValueError("Unable to create valid file path.")
                    else:
                        #success
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
    #     """not implemented yet, load metadata from dict of items/list types"""
    #     pass
