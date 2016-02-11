import pysat
import pandas as pds
import numpy as np
from nose.tools import assert_raises, raises
import nose.tools

class TestBasics:
    def setup(self):
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat','testing', '10', 'clean')

    def teardown(self):
        '''Runs after every method to clean up previous testing.'''
        del self.testInst

    @raises(ValueError)        
    def test_single_modifying_custom_function(self):
        """Test if custom function works correctly. Modify function that returns pandas object.
        Modify function returns an object which will produce an Error."""
        def custom1(inst):
            inst.data['doubleMLT'] = 2.*inst.data.mlt
            return 5.*inst.data

        self.testInst.custom.add(custom1, 'modify')
        self.testInst.load(2009,1)

    def test_single_adding_custom_function(self):
        '''Test if custom function works correctly. Add function that returns pandas object.'''
        def custom1(inst):
            d = 2.*inst.data.mlt
            d.name='doubleMLT'
            return d

        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'].values == 2.*self.testInst.data.mlt.values).all()
        assert ans

    def test_single_adding_custom_function_wrong_times(self):
        '''Only the data at the correct time should be accepted, otherwise nan'''
        def custom1(inst):
            d = 2.*inst.data.mlt
            d.name='doubleMLT'
            d.index += pds.DateOffset(microseconds=10)
            return d

        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'].isnull()).all()
        assert ans

    def test_single_adding_custom_function_that_modifies_passed_data(self):
        '''Test if custom function works correctly. Add function that returns pandas object but modifies passed satellite object.
        Changes to passed object should not propagate back.'''
        def custom1(inst):
            inst.data['doubleMLT'] = 2.*inst.data.mlt
            inst.data.mlt=0.
            return inst.data.doubleMLT

        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans

    def test_add_function_tuple_return_style(self):
        '''Test if custom function works correctly. Add function that returns name and numpy array.'''
        def custom1(inst):
            return ('doubleMLT',2.*inst.data.mlt.values)
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans
        
    def test_add_multiple_custom_functions_tuple_return_style(self):
        '''Test if multiple custom functions that add data work correctly. Add function that returns name and numpy array.'''
        def custom1(inst):
            return (['doubleMLT', 'tripleMLT'],[2.*inst.data.mlt.values, 3.*inst.data.mlt.values])
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (((self.testInst.data['doubleMLT'] == 2.*self.testInst.data.mlt).all()) & ((self.testInst.data['tripleMLT'] == 3.*self.testInst.data.mlt).all()))
        assert ans

    @raises(ValueError)
    def test_add_function_tuple_return_style_too_few_elements(self):
        '''Test if custom function works correctly. Add function that returns name and numpy array.'''
        def custom1(inst):
            return ('doubleMLT',2.*inst.data.mlt.values[0:-5])
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)

    @raises(ValueError)
    def test_add_function_tuple_return_style_too_many_elements(self):
        '''Test if custom function works correctly. Add function that returns name and numpy array.'''
        def custom1(inst):
            return ('doubleMLT',np.arange(2.*len(inst.data.mlt)))
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
                                                        
    def test_add_dataframe(self):
        def custom1(inst):
            out = pysat.DataFrame({'doubleMLT':inst.data.mlt*2, 
                                'tripleMLT':inst.data.mlt*3}, 
                                index=inst.data.index)
            return out
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans = (((self.testInst.data['doubleMLT'] == 2.*self.testInst.data.mlt).all()) & ((self.testInst.data['tripleMLT'] == 3.*self.testInst.data.mlt).all()))
        assert ans

    def test_add_dataframe_w_meta(self):
        def custom1(inst):
            out = pysat.DataFrame({'doubleMLT':inst.data.mlt*2, 
                                'tripleMLT':inst.data.mlt*3}, 
                                index=inst.data.index)
            return {'data':out, 'long_name':['doubleMLTlong', 'tripleMLTlong'],
                    'units':['hours1', 'hours2']}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        ans3 = self.testInst.meta['tripleMLT'].units == 'hours2'        
        ans4 = self.testInst.meta['tripleMLT'].long_name == 'tripleMLTlong'
        ans5 = (self.testInst['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        ans6 = (self.testInst['tripleMLT'] == 3.*self.testInst.data.mlt).all()
        assert ans1 & ans2 & ans3 & ans4 & ans5 & ans6
        
    def test_add_series_w_meta(self):
        def custom1(inst):
            out = pysat.Series(inst.data.mlt*2, 
                                index=inst.data.index)
            out.name = 'doubleMLT'
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        ans3 = (self.testInst['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans1 & ans2 & ans3

    def test_add_series_w_meta_missing_long_name(self):
        def custom1(inst):
            out = pysat.Series(2.*inst.data.mlt.values, 
                                index=inst.data.index)
            out.name = 'doubleMLT'
            return {'data':out, 
                    'units':'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLT'
        ans3 = (self.testInst['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans1 & ans2 & ans3        
        
    def test_add_series_w_meta_name_in_dict(self):
        def custom1(inst):
            out = pysat.Series(2.*inst.data.mlt.values, 
                                index=inst.data.index)
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1', 'name':'doubleMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        ans3 = (self.testInst['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans1 & ans2 & ans3
        
    @raises(ValueError)    
    def test_add_series_w_meta_no_name(self):
        def custom1(inst):
            out = pysat.Series({'doubleMLT':inst.data.mlt*2}, 
                                index=inst.data.index)
            #out.name = 'doubleMLT'
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)   

    def test_add_numpy_array_w_meta_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt*2).values
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1', 'name':'doubleMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        ans3 = (self.testInst['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans1 & ans2 & ans3

    @raises(ValueError)  
    def test_add_numpy_array_w_meta_no_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt*2).values
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)


    def test_add_list_w_meta_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt*2).tolist()
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1', 'name':'doubleMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        ans3 = (self.testInst['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans1 & ans2 * ans3

    @raises(ValueError)  
    def test_add_list_w_meta_no_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt*2).tolist()
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
    