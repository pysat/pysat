"""
tests the pysat meta object and code
"""
import pysat
import pandas as pds
from nose.tools import assert_raises, raises
import nose.tools
import pysat.instruments.pysat_testing
import numpy as np

class TestBasics:
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.meta = pysat.Meta()
        self.testInst = pysat.Instrument('pysat', 'testing', tag='', clean_level='clean')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
    
    def test_basic_meta_assignment(self):
        self.meta['new'] = {'units':'hey', 'long_name':'boo'}
        assert (self.meta['new'].units == 'hey') & (self.meta['new'].long_name == 'boo')

    def test_basic_meta_assignment_w_Series(self):
        self.meta['new'] = pds.Series({'units':'hey', 'long_name':'boo'})
        assert (self.meta['new'].units == 'hey') & (self.meta['new'].long_name == 'boo')

    def test_multiple_meta_assignment(self):
        self.meta[['new','new2']] = {'units':['hey', 'hey2'], 'long_name':['boo', 'boo2']}
        assert ((self.meta['new'].units == 'hey') & (self.meta['new'].long_name == 'boo') &
               (self.meta['new2'].units == 'hey2') & (self.meta['new2'].long_name == 'boo2'))

    @raises(ValueError)
    def test_multiple_meta_assignment_error(self):
        self.meta[['new','new2']] = {'units':['hey', 'hey2'], 'long_name':['boo']}
        assert ((self.meta['new'].units == 'hey') & (self.meta['new'].long_name == 'boo') &
               (self.meta['new2'].units == 'hey2') & (self.meta['new2'].long_name == 'boo2'))

    def test_replace_meta_units(self):
        self.meta['new'] = {'units':'hey', 'long_name':'boo'}
        self.meta['new'] = {'units':'yep'}
        assert (self.meta['new'].units == 'yep') & (self.meta['new'].long_name == 'boo')

    def test_replace_meta_long_name(self):
        self.meta['new'] = {'units':'hey', 'long_name':'boo'}
        self.meta['new'] = {'long_name':'yep'}
        assert (self.meta['new'].units == 'hey') & (self.meta['new'].long_name == 'yep')
    
    def test_add_additional_metadata_types(self):
        self.meta['new'] = {'units':'hey', 'long_name':'boo', 'description':'boohoo'}

        assert ((self.meta['new'].units == 'hey') & 
                (self.meta['new'].long_name == 'boo') &
                (self.meta['new'].description == 'boohoo'))

    def test_add_meta_then_add_additional_metadata_types(self):
        self.meta['new'] = {'units':'hey', 'long_name':'crew'}
        self.meta['new'] = {'units':'hey', 'long_name':'boo', 'description':'boohoo'}

        assert ((self.meta['new'].units == 'hey') & 
                (self.meta['new'].long_name == 'boo') &
                (self.meta['new'].description == 'boohoo'))
            
    def test_add_meta_then_add_different_additional_metadata_types(self):
        self.meta['new1'] = {'units':'hey1', 'long_name':'crew'}
        self.meta['new2'] = {'units':'hey', 'long_name':'boo', 'description':'boohoo'}
        assert ((self.meta['new2'].units == 'hey') & 
                (self.meta['new2'].long_name == 'boo') &
                (self.meta['new2'].description == 'boohoo') &
                (self.meta['new1'].units == 'hey1') &
                (self.meta['new1'].long_name == 'crew') &
                (np.isnan(self.meta['new1'].description)))

    def test_add_meta_then_partially_add_additional_metadata_types(self):
        self.meta['new'] = {'units':'hey', 'long_name':'crew'}
        self.meta['new'] = {'long_name':'boo', 'description':'boohoo'}

        assert ((self.meta['new'].units == 'hey') & 
                (self.meta['new'].long_name == 'boo') &
                (self.meta['new'].description == 'boohoo'))

    def test_meta_equality(self):
        
        assert self.testInst.meta == self.testInst.meta  

    def test_false_meta_equality(self):

        assert not (self.testInst.meta == self.testInst)
        
    def test_assign_higher_order_meta(self):
        meta = pysat.Meta()
        meta['dm'] = {'units':'hey', 'long_name':'boo'}
        meta['rpa'] = {'units':'crazy', 'long_name':'boo_whoo'}
        self.meta['higher'] = meta

    def test_assign_higher_order_meta_from_dict(self):
        meta = pysat.Meta()
        meta['dm'] = {'units':'hey', 'long_name':'boo'}
        meta['rpa'] = {'units':'crazy', 'long_name':'boo_whoo'}
        self.meta['higher'] = {'meta':meta}

    def test_assign_higher_order_meta_from_dict_correct(self):
        meta = pysat.Meta()
        meta['dm'] = {'units':'hey', 'long_name':'boo'}
        meta['rpa'] = {'units':'crazy', 'long_name':'boo_whoo'}
        self.meta['higher'] = {'meta':meta}
        assert self.meta['higher'] == meta

    def test_assign_higher_order_meta_from_dict_w_multiple(self):
        meta = pysat.Meta()
        meta['dm'] = {'units':'hey', 'long_name':'boo'}
        meta['rpa'] = {'units':'crazy', 'long_name':'boo_whoo'}
        self.meta[['higher', 'lower']] = {'meta':[meta, None],
                                          'units':[None, 'boo'],
                                          'long_name':[None, 'boohoo']}
        check1 = self.meta['lower'].units == 'boo'
        check2 = self.meta['lower'].long_name == 'boohoo'
        check3 = self.meta['higher'] == meta
        assert check1 & check2 & check3

    def test_assign_higher_order_meta_from_dict_w_multiple_2(self):
        meta = pysat.Meta()
        meta['dm'] = {'units':'hey', 'long_name':'boo'}
        meta['rpa'] = {'units':'crazy', 'long_name':'boo_whoo'}
        self.meta[['higher', 'lower', 'lower2']] = {'meta':[meta, None, meta],
                                          'units':[None, 'boo', None],
                                          'long_name':[None, 'boohoo', None]}
        check1 = self.meta['lower'].units == 'boo'
        check2 = self.meta['lower'].long_name == 'boohoo'
        check3 = self.meta['higher'] == meta
        assert check1 & check2 & check3
        
    def test_create_new_metadata_from_old(self):
        meta = pysat.Meta()
        meta['dm'] = {'units':'hey', 'long_name':'boo'}
        meta['rpa'] = {'units':'crazy', 'long_name':'boo_whoo'}
        self.meta[['higher', 'lower', 'lower2']] = {'meta':[meta, None, meta],
                                          'units':[None, 'boo', None],
                                          'long_name':[None, 'boohoo', None]}
        meta2 = pysat.Meta(metadata=self.meta.data)
        check1 = np.all(meta2['lower'] == self.meta['lower'])
        assert check1

        


    def test_replace_meta_units_list(self):
        self.meta['new'] = {'units':'hey', 'long_name':'boo'}
        self.meta['new2'] = {'units':'hey2', 'long_name':'boo2'}
        self.meta['new2','new'] = {'units':['yeppers','yep']}
        #print self.meta['new']
        #print self.meta['new2']
        assert ((self.meta['new'].units == 'yep') & (self.meta['new'].long_name == 'boo') &
            (self.meta['new2'].units == 'yeppers') & (self.meta['new2'].long_name == 'boo2'))
    
    def test_meta_repr_functions(self):
        print (self.testInst)
        # if it doesn't produce an error, we presume it works
        # how do you test a print??
        assert True
        
    def test_meta_csv_load(self):
        import os
        name = os.path.join(pysat.__path__[0],'tests', 'cindi_ivm_meta.txt')
        mdata = pysat.Meta.from_csv(name=name,  na_values=[ ], #index_col=2, 
                                    keep_default_na=False,
                                    col_names=['name','long_name','idx','units','description'])
        check = []
        check.append(mdata['yrdoy'].long_name == 'Date')
        check.append(mdata['unit_mer_z'].long_name == 'Unit Vector - Meridional Dir - S/C z')
        check.append(mdata['iv_mer'].description == 'Constructed using IGRF mag field.') 
        assert np.all(check)
    
    def test_meta_csv_load_and_operations(self):
        import os
        name = os.path.join(pysat.__path__[0],'tests', 'cindi_ivm_meta.txt')
        mdata = pysat.Meta.from_csv(name=name,  na_values=[ ], #index_col=2, 
                                    keep_default_na=False,
                                    col_names=['name','long_name','idx','units','description'])
        #names aren't provided for all data in file, filling in gaps                  
        #print mdata.data  
        mdata.data.loc[:,'name'] = mdata.data.index       
        mdata.data.index = mdata.data['idx']
        new = mdata.data.reindex(index = np.arange(mdata.data['idx'].iloc[-1]+1))
        idx, = np.where(new['name'].isnull())
        new.ix[idx, 'name'] = idx.astype(str)
        new.ix[idx,'units']=''
        new.ix[idx,'long_name'] =''
        new.ix[idx,'description']=''
        new['idx'] = new.index.values
        new.index = new['name']
        
        #update metadata object with new info
        mdata.replace(metadata=new)
        assert len(mdata.data == mdata[-1, 'idx'])



