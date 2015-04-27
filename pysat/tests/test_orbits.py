import pysat
import pandas as pds
from nose.tools import assert_raises, raises
import nose.tools

from dateutil.relativedelta import relativedelta as relativedelta
class TestOrbits:
    
    def setup(self):
	'''Runs before every method to create a clean testing setup.'''
	info = {'index':'mlt'}
        self.testInst = pysat.Instrument('pysat','testing', '86400', 'clean', 
                                        orbit_info=info)

    def teardown(self):
        '''Runs after every method to clean up previous testing.'''
        del self.testInst 
    
    def test_single_orbit_call_orbit_starts_0_UT_using_next(self):
        self.testInst.load(2009,1)
	self.testInst.orbits.next()
	ans = (self.testInst.data.index[0] == pds.datetime(2009,1,1))
	ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1,1,36,59) ))
	print self.testInst.data.index[0]
        print self.testInst.data.index[-1]
	print ans
	print ans2
	assert ans & ans2

    def test_single_orbit_call_orbit_starts_0_UT_using_prev(self):
        
        self.testInst.load(2009,1)
	self.testInst.orbits.prev()
	ans = (self.testInst.data.index[0] == (pds.datetime(2009,1,1)-relativedelta(hours=1, minutes=37)) )
	ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1)-relativedelta(seconds=1) ))
	assert ans & ans2 
	
    def test_single_orbit_call_orbit_starts_off_0_UT_using_next(self):
        from dateutil.relativedelta import relativedelta as relativedelta
        self.testInst.load(2008,366)
	self.testInst.orbits.next()
	print self.testInst.data.index[0], pds.datetime(2008,12,30, 23, 45), self.testInst.data.index[-1], (pds.datetime(2008,12,30, 23, 45)+relativedelta(hours=1, minutes=36, seconds=59) )
	ans = (self.testInst.data.index[0] == pds.datetime(2008,12,30, 23, 45))
	ans2 = (self.testInst.data.index[-1] == (pds.datetime(2008,12,30, 23, 45)+relativedelta(hours=1, minutes=36, seconds=59) ))
	assert ans & ans2

    def test_single_orbit_call_orbit_starts_off_0_UT_using_prev(self):
        self.testInst.load(2008,366)
	self.testInst.orbits.prev()
	ans = (self.testInst.data.index[0] == (pds.datetime(2008,12,30, 23, 45)-relativedelta(hours=1, minutes=37)) )
	ans2 = (self.testInst.data.index[-1] == (pds.datetime(2008,12,30, 23, 45)-relativedelta(seconds=1) ))
	assert ans & ans2 
	
    def test_repeated_orbit_calls_symmetric_single_day_0_UT(self):
        self.testInst.load(2009,1)
	self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(10):
	    self.testInst.orbits.next()
	for j in xrange(10):
	    self.testInst.orbits.prev()
	assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_symmetric_multi_day_0_UT(self):
        self.testInst.load(2009,1)
	self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(20):
	    self.testInst.orbits.next()
	for j in xrange(20):
	    self.testInst.orbits.prev()
        print control.data.mlt
        print self.testInst.data.mlt
	assert all(control.data == self.testInst.data)      

    def test_repeated_orbit_calls_symmetric_single_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(10):
	    self.testInst.orbits.next()
	for j in xrange(10):
	    self.testInst.orbits.prev()
	assert all(control.data == self.testInst.data)
	
    def test_repeated_orbit_calls_symmetric_multi_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(20):
	    self.testInst.orbits.next()
	for j in xrange(20):
	    self.testInst.orbits.prev()
	assert all(control.data == self.testInst.data)        	

    def test_repeated_orbit_calls_antisymmetric_multi_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(10):
	    self.testInst.orbits.next()
	for j in xrange(20):
	    self.testInst.orbits.prev()
	for j in xrange(10):
	    self.testInst.orbits.next()
	print control.data.mlt
        print self.testInst.data.mlt
	assert all(control.data == self.testInst.data) 

    def test_repeated_orbit_calls_antisymmetric_multi_multi_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(20):
	    self.testInst.orbits.next()
	for j in xrange(40):
	    self.testInst.orbits.prev()
	for j in xrange(20):
	    self.testInst.orbits.next()
	print control.data.mlt
        print self.testInst.data.mlt
	assert all(control.data == self.testInst.data )	                    

    def test_repeated_orbit_calls_antisymmetric_multi_day_0_UT(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(10):
	    self.testInst.orbits.next()
	for j in xrange(20):
	    self.testInst.orbits.prev()
	for j in xrange(10):
	    self.testInst.orbits.next()
	print control.data.mlt
        print self.testInst.data.mlt
	assert all(control.data == self.testInst.data )

    def test_repeated_orbit_calls_antisymmetric_multi_multi_day_0_UT(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
	for j in xrange(20):
	    self.testInst.orbits.next()
	for j in xrange(40):
	    self.testInst.orbits.prev()
	for j in xrange(20):
	    self.testInst.orbits.next()
	print control.data.mlt
        print self.testInst.data.mlt
	assert all(control.data == self.testInst.data )