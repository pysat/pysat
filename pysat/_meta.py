import os
import pandas as pds

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

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False    

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
            if 'units' not in value.keys():
                if name not in self.data.index:
                    value['units'] = ''
                else:
                    value['units'] = self.data.ix[name,'units']

            if 'long_name' not in value.keys():
                if name not in self.data.index:
                    # only set default if name not already in meta
                    value['long_name'] = name  
                else:
                    value['long_name'] = self.data.ix[name, 'long_name']
                
            if hasattr(value[value.keys()[0]], '__iter__' ):
                # an iterable of things         
                for key in value.keys():
                    if len(name) != len(value[key]):
                        raise ValueError('Length of names and inputs must be equal.')
                new = DataFrame(value, index=name)
                self.data = self.data.append(new) 
            else:
                for key in value.keys():
                    value[key] = [value[key]]
                new = DataFrame(value, index=[name])

                if name in self.data.index:
                    #self.data.ix[name] = new.ix[name]
                    self.data = self.data.drop(name)
                    self.data = self.data.append(new)
                else:
                    self.data = self.data.append(new)
                #self.data.ix[name] = new[name]
                
        if isinstance(value, Series):
            self.data.ix[name] = value
        
    def __getitem__(self,key):
        """Convenience method for obtaining metadata.
        
        Maps to pandas DataFrame.ix method.
        
        Examples
        --------
        ::
        
            print meta['name']
        
        """
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
        
    @classmethod
    def from_nc():
        """not implemented yet, load metadata from netCDF"""
        pass
        
    @classmethod
    def from_dict():
        """not implemented yet, load metadata from dict of items/list types"""
        pass
