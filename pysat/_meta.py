import os
import pandas as pds

from pysat import DataFrame, Series

class Meta(object):
    """
    Stores metadata for an associated pysat Satellite instance. 
    Similar to CF-1.6 data standard info.
    
    inputs:
        metadata: pandas DataFrame indexed by variable name that contains
         atleast the standard_name (name), units, and long_name for the data 
         stored in the associated pysat Satellite object.
    """
    def __init__(self, metadata=None):
        self.replace(metadata=metadata)    

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False    

    def copy(self):
        from copy import deepcopy as deepcopy
        """Deep copy of the meta object."""
        return deepcopy(self) 
               
    def __setitem__(self, name, value):
        """add metadata information"""
        if isinstance(value,dict):
            if 'units' not in value.keys():
                raise ValueError('Must provide "units" in input dictionary.')
            if 'long_name' not in value.keys():
                value['long_name'] = name  
                
            if hasattr(value[value.keys()[0]], '__iter__' ):
                # an iterable of things         
                for key in value.keys():
                    if len(name) != len(value[key]):
                        raise ValueError('Length of names and inputs must be equal.')
                new = DataFrame(value, index=name)
                self.data = self.data.append(new) 
            else:
                new = Series(value)
                self.data.ix[name] = new
                
        if isinstance(value, Series):
            self.data.ix[name] = value
        
        
    def __getitem__(self,key):
        return self.data.ix[key]
        """return metadata"""
    
    #def restore(self):
    #    """Restore metadata from saved metadata"""
    #    self.data = self._orig_data
        
    def replace(self, metadata=None):
        """Replace metadata and saved metadata with input data.
        
        inputs:
            metadata: pandas DataFrame indexed by variable name that contains
            standard_name(name), units, and long_name for the data stored in 
            the associated pysat Satellite object.
        """
        if metadata is not None:
            if isinstance(metadata, DataFrame):
                self.data = metadata
            else:
                raise ValueError("Input must be a pandas DataFrame type."+
                            "See other constructors for alternate inputs.")
            
        else:
            self.data = DataFrame(None, columns=['long_name', 'units'])
        #self._orig_data = self.data.copy()
        
    @classmethod
    def from_csv(cls, name=None, col_names=None, sep=None, **kwargs):
        """
        Create satellite metadata object from csv
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
        else:
            if not os.path.isfile(name):
                # Not a real file, assume input is a pysat instrument name
                # and look in the standard pysat location.
                test =  os.path.join(pysat.__path__,'instruments',name+'_meta.txt')
                #print test
                if os.path.isfile(test):
                    name = test
                else:
                    #trying to form an absolute path for success
                    test = os.path.abspath(name)
                    #print test
                    if not os.path.isfile(test):
                        raise ValueError("Unable to create valid file path.")
                    else:
                        #success
                        name = test
                                     
        mdata = pds.read_csv(name, names=col_names, sep=sep, **kwargs) 
        if not mdata.empty:
            #make sure the data name is the index
            mdata.index = mdata['name']
            return cls(metadata=mdata)
        else:
            raise ValueError('Unable to retrieve information from ' + name)
        
    
    def from_nc():
        """load metadata from netCDF"""
        pass
    
    def from_dict():
        """load metadata from dict of items/list types"""
        pass
