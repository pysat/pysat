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
        
    Attributes
    ----------
    data : pandas.DataFrame
        index is variable standard name, 'units' and 'long_name' are also stored along
        with additional user provided labels.
        
    """
    def __init__(self, metadata=None):
        self.replace(metadata=metadata)
        self.ho_data = {}

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
        output_str += self.data.__repr__()
        output_str += '\n'
        for item_name in self.ho_data.keys():
            output_str += '\n\n'
            output_str += 'Metadata for '+item_name+'\n'
            # print(self.ho_data[item_name].data)
            output_str += self.ho_data[item_name].data.__repr__()
        return output_str

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
        
        if isinstance(value,dict):
            # check if dict empty
            if value.keys() == []:
                if name in self:
                    return
                # otherwise, continue on and set defaults

            # if not passed an iterable, make it one
            if isinstance(name, basestring):
                name = [name]
                for key in value.keys():
                    value[key] = [value[key]]

            # if len(name) != len(value):
            #     raise ValueError('Length of names and all inputs must be equal.')

            for key in value.keys():
                if len(name) != len(value[key]):
                    raise ValueError('Length of names and inputs must be equal.')

            if 'meta' in value.keys():
                # process higher order stuff first
                # multiple assignment, check length is appropriate
                pop_list = []
                for item, val in zip(name, value['meta']):
                    if val is not None:
                        self[item] = val
                        pop_list.append(item)
                for item in pop_list:
                    value = value.pop(item)

            if 'units' not in value.keys():
                # provide default value, or copy existing
                value['units'] = []
                for item_name in name:
                    if item_name not in self:
                        value['units'].append('')
                    else:
                        value['units'].append(self.data.ix[item_name,'units'])

            if 'long_name' not in value.keys():
                # provide default value, or copy existing
                value['long_name'] = []
                for item_name in name:
                    if item_name not in self:
                        value['long_name'].append(item_name)
                    else:
                        value['long_name'].append(self.data.ix[item_name,'long_name'])

            new = DataFrame(value, index=name)
            for item_name,item in new.iterrows():
                if item_name not in self:
                    self.data = self.data.append(item)
                else:
                    # info already exists, update with new info
                    for item_key in item.keys():
                        self.data.ix[item_name,item_key] = item[item_key]

        elif isinstance(value, Series):
            self.data.ix[name] = value

        elif isinstance(value, Meta):
            # dealing with higher order data set
            self.ho_data[name] = value

    def __getitem__(self,key):
        """Convenience method for obtaining metadata.
        
        Maps to pandas DataFrame.ix method.
        
        Examples
        --------
        ::
        
            print(meta['name'])
        
        """
        if key in self.ho_data.keys():
            return self.ho_data[key]
        else:
            return self.data.ix[key]
        
    def replace(self, metadata=None):
        """Replace stored metadata with input data.
        
        Parameters
        ----------
        metadata : pandas.DataFrame 
            DataFrame should be indexed by variable name that contains at minimum the 
            standard_name (name), units, and long_name for the data stored in the associated 
            pysat Instrument object.
            
        """
        import string
        if metadata is not None:
            if isinstance(metadata, DataFrame):
                self.data = metadata
                self.data.columns = map(string.lower, self.data.columns)
                if 'long_name' not in self.data.columns:
                    self.data['long_name'] = self.data.index
                if 'units' not in self.data.columns:
                    self.data['units'] = ''
            else:
                raise ValueError("Input must be a pandas DataFrame type. "+
                            "See other constructors for alternate inputs.")
            
        else:
            self.data = DataFrame(None, columns=['long_name', 'units'])
        #self._orig_data = self.data.copy()
        
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
