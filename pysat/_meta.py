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
        
    """
    def __init__(self, metadata=None, units_label='units', name_label='long_name'):
        self._units_label = units_label
        self._name_label = name_label
        self.replace(metadata=metadata)
        self.ho_data = {}

        self._base_attr = dir(self)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __contains__(self, other):

        if other in self.data.index:
            return True
        if other in self.ho_data.keys():
            return True
        return False

    def __repr__(self):
        # cover 1D parameters
        output_str = 'Metadata for 1D parameters\n'
        # print('Metadata for 1D parameters')
        # print(self.data)
        output_str += self.data.__str__()
        output_str += '\n'
        for item_name in self.ho_data.keys():
            output_str += '\n\n'
            output_str += 'Metadata for '+item_name+'\n'
            # print(self.ho_data[item_name].data)
            output_str += self.ho_data[item_name].data.__str__()
        return output_str

    def concat(self, other):
        """Concats two metadata objects together."""

        # concat data frames
        mdata = self.copy()
        mdata.data = pds.concat([self.data, other.data])
        # add together higher order data
        for key in other.ho_data.keys():
            if not (key in mdata.ho_data):
                mdata.ho_data[key] = other.ho_data[key]
        return mdata
                 
    def copy(self):
        from copy import deepcopy as deepcopy
        """Deep copy of the meta object."""
        return deepcopy(self) 
               
    def __setitem__(self, name, value):
        """Convenience method for adding metadata.
        
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
        
        """
        
        if isinstance(value, dict):
            # check if dict empty
            if value.keys() == []:
                # null input, everything should be set to default
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
                        # all variables exist, can leave
                        return
                    else:
                        # otherwise, continue on and set defaults
                        # create empty input for all remaining names
                        value = {}
                        value[self._units_label] = ['']*len(name)
                        value[self._name_label] = name
                        # for na in name:
                        #     value[na] = [[]]

            # perform some checks on the data
            # if not passed an iterable, make it one
            if isinstance(name, basestring):
                name = [name]
                for key in value.keys():
                    value[key] = [value[key]]

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

            # check if 'units' have been provided
            # check against units_label, case insensitive
            lower_keys = [k.lower() for k in value.keys()]
            if self._units_label.lower() not in lower_keys:
                # 'units' not provided
                # provide default value, or copy existing
                value[self._units_label] = []
                for item_name in name:
                    if item_name not in self:
                        # overall variable not in Meta, can use default
                        # 'default'
                        value[self._units_label].append('')
                    else:
                        # copy existing
                        value[self._units_label].append(self[item_name, self._units_label])
            elif self._units_label not in value.keys():
                # case of 'units' provided doesn't match up with _units_label
                # make it match
                for unit_key, lower_key in zip(value.keys(), lower_keys):
                    if lower_key == self._units_label.lower():
                        # print('popping units_key ', unit_key)
                        value[self._units_label] = value.pop(unit_key)
                        break
            # check if 'long_name' has been provided
            # check against name_label, case insensitive
            lower_keys = [k.lower() for k in value.keys()]
            if self._name_label.lower() not in lower_keys:
                # provide default value, or copy existing
                value[self._name_label] = []
                for item_name in name:
                    if item_name not in self:
                        value[self._name_label].append(item_name)
                    else:
                        value[self._name_label].append(self[item_name, self._name_label])
            elif self._name_label not in value.keys():
                # case of 'units' provided doesn't match up with _name_label
                # make it match
                for label_key, lower_key in zip(value.keys(), lower_keys):
                    if lower_key == self._name_label.lower():
                        # print('popping label_key ', label_key)
                        value[self._name_label] = value.pop(label_key)
                        break

            # time to actually add the metadata
            if len(name) > 0:
                # make sure there is still something to add
                new = DataFrame(value, index=name)
                for item_name, item in new.iterrows():
                    if item_name not in self:
                        self.data = self.data.append(item)
                    else:
                        # info already exists, update with new info
                        for item_key in item.keys():
                            self.data.loc[item_name, item_key] = item[item_key]

        elif isinstance(value, Series):
            self.data.loc[name] = value

        elif isinstance(value, Meta):
            # dealing with higher order data set
            self.ho_data[name] = value

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
            index = key[0]
            column = key[1]
            # column name needs to be checked against lower case form
            # ignores but preserves case for column access
            avail_cols = self.data.columns
            lower_cols = [col.lower() for col in avail_cols]
            if column in lower_cols:
                for col, true_col in zip(lower_cols, avail_cols):
                    if column == col:
                        return self.data.loc[index, true_col]
            # didn't find the column
            # hail mary call below
            return self.data.loc[index, column]

        # single variable request
        if key in self.ho_data.keys():
            return self.ho_data[key]
        else:
            return self.data.loc[key]

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
                if self._name_label.lower() not in lower_columns:
                    self.data[self._name_label] = self.data.index
                if self._units_label.lower() not in lower_columns:
                    self.data[self._units_label] = ''
            else:
                raise ValueError("Input must be a pandas DataFrame type. "+
                            "See other constructors for alternate inputs.")
        else:
            self.data = DataFrame(None, columns=[self._name_label, self._units_label])
        
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
