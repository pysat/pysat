import pysat
import pandas as pds
from nose.tools import assert_raises, raises
import nose.tools

class TestBasics:
    def setup(self):
	'''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('testing', '10', 'clean')

    def teardown(self):
        '''Runs after every method to clean up previous testing.'''
        del self.testInst

    @raises(ValueError)        
    def test_single_modifying_custom_function(self):
	'''Test if custom function works correctly. Modify function that returns pandas object. Modify function returns an object which will produce an Error.'''
        def custom1(inst):
            inst.data['doubleMLT'] = 2.*inst.data.mlt
            return 5.*inst.data
	
        self.testInst.custom.add(custom1, 'modify')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'].values == 2.*self.testInst.data.mlt.values).all()
        assert ans

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

    def test_adding_single_custom_function_old_return_style(self):
	'''Test if custom function works correctly. Add function that returns name and numpy array.'''
        def custom1(inst):
            return ('doubleMLT',2.*inst.data.mlt.values)
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'] == 2.*self.testInst.data.mlt).all()
        assert ans
        
    def test_adding_multiple_custom_functions_old_return_style(self):
	'''Test if multiple custom functions that add data work correctly. Add function that returns name and numpy array.'''
        def custom1(inst):
            return (['doubleMLT', 'tripleMLT'],[2.*inst.data.mlt.values, 3.*inst.data.mlt.values])
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (((self.testInst.data['doubleMLT'] == 2.*self.testInst.data.mlt).all()) & ((self.testInst.data['tripleMLT'] == 3.*self.testInst.data.mlt).all()))
        assert ans

