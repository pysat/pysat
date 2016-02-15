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
        self.testInst = pysat.Instrument('pysat', 'testing', '', 'clean')

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

    #def test_replace_meta_units_list(self):
    #    self.meta['new'] = {'units':'hey', 'long_name':'boo'}
    #    self.meta['new2'] = {'units':'hey2', 'long_name':'boo2'}
    #    self.meta['new2','new'] = {'units':['yeppers','yep']}
    #    print self.meta['new']
    #    print self.meta['new2']
    #    assert ((self.meta['new'].units == 'yep') & (self.meta['new'].long_name == 'boo') &
    #        (self.meta['new2'].units == 'yeppers') & (self.meta['new2'].long_name == 'boo2'))



