# -*- coding: utf-8 -*-
#Test some of the basic _core functions

import pysat
import pandas as pds
from nose.tools import assert_raises, raises
import nose.tools
import pysat.instruments.pysat_testing

class TestBasics:
    def setup(self):
        reload(pysat.instruments.pysat_testing)
	'''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '10', 'clean')

    def teardown(self):
        '''Runs after every method to clean up previous testing.'''
        del self.testInst
    
    def test_basic_instrument_load(self):
        '''Test if the correct day is being loaded (checking object date).'''
        self.testInst.load(2009,1)
        assert self.testInst.date == pds.datetime(2009,1,1)	

    def test_next_load_default(self):
        '''Test if first day is loaded by default when first invoking .next.'''
        self.testInst.next()
        assert self.testInst.date == pds.datetime(2008,1,1)

    def test_prev_load_default(self):
        '''Test if last day is loaded by default when first invoking .prev.'''
        self.testInst.prev()
        assert self.testInst.date == pds.datetime(2010,12,31)
    
    def test_filename_load(self):
        '''Test if file is loadable by filename, relative to top_data_dir/platform/name/tag'''
        self.testInst.load(fname='12/31/10.nofile')
        assert self.testInst.data.index[0] == pds.datetime(2010,12,31)
        
    def test_instrument_init(self):
        """Test if init function supplied by instrument can modify object"""
        assert self.testInst.new_thing==True

    @raises(StopIteration)
    def test_left_bounds_with_prev(self):
        '''Test if passing bounds raises StopIteration.'''
        self.testInst.next()
        self.testInst.prev()
        self.testInst.prev()        
        
    @raises(StopIteration)
    def test_right_bounds_with_next(self):
        '''Test if passing bounds raises StopIteration.'''
        self.testInst.prev()
        self.testInst.next()
        self.testInst.next()        

    def test_basic_instrument_load_data(self):
        '''Test if the correct day is being loaded (checking data).'''
        self.testInst.load(2009,1)
        assert self.testInst.data.index[0] == pds.datetime(2009,1,1,0,0,0)

    def test_basic_instrument_load_leap_year(self):
        '''Test if the correct day is being loaded (Leap-Year).'''
        self.testInst.load(2008,366)
        assert self.testInst.date == pds.datetime(2008,12,31)	

    def test_getyrdoy_1(self):
	'''Test the date to year, day of year code functionality'''
        date = pds.datetime(2009,1,1)
        yr, doy = pysat.utils.getyrdoy(date)
        assert ((yr == 2009) & (doy == 1))

    def test_getyrdoy_leap_year(self):
	'''Test the date to year, day of year code functionality (leap_year)'''
        date = pds.datetime(2008,12,31)
        yr, doy = pysat.utils.getyrdoy(date)
        assert ((yr == 2008) & (doy == 366)) 


    def test_custom_instrument_load(self):
        '''
        Test if the correct day is being loaded (End-to-End), 
        with no instrument file but routines are passed.
        '''
        import pysat.instruments.pysat_testing as test
        testInst = pysat.Instrument(inst_module=test, tag='1000', clean_level='clean')
        testInst.load(2009,32)
        assert testInst.date == pds.datetime(2009,2,1)	
        
    @raises(AttributeError)
    def test_custom_instrument_load_2(self):
        '''
        Test if an exception is thrown correctly if there is no 
        instrument file and supplied routines are incomplete.
        '''
        import pysat.instruments.pysat_testing as test
        del test.list_files
        testIn = pysat.Instrument(inst_module=test, tag='1000', clean_level='clean')
        testIn.load(2009,1)

    @raises(AttributeError)
    def test_custom_instrument_load_3(self):
        '''
        Test if an exception is thrown correctly if there is no 
        instrument file and supplied routines are incomplete.
        '''
        import pysat.instruments.pysat_testing as test
        del test.load
        testIn = pysat.Instrument(inst_module=test, tag='1000', clean_level='clean')
        testIn.load(2009,1)

    def test_data_padding(self):
        te = pysat.Instrument('pysat','testing', '10000', pad=True, minutes=5)
        te.load(2009,1, verifyPad=True)
        print te.data.index[0]
        print te.data.index[-1]
        assert ( (te.data.index[0] == te.date - pds.DateOffset(minutes=5)) & 
                (te.data.index[-1] == te.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + pds.DateOffset(minutes=5)) )
            
    def test_data_padding_removal(self):
        te = pysat.Instrument('pysat','testing', '10000', pad=True, minutes=5)
        te.load(2009,1)
        assert (te.data.index[0] == te.date ) & (te.data.index[-1] == te.date + pds.DateOffset(hour=23, minutes=59,seconds=59) )