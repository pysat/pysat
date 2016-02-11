import numpy as np
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
    
    def test_single_orbit_call_by_0_index(self):
        self.testInst.load(2009,1)
        self.testInst.orbits[0]
        ans = (self.testInst.data.index[0] == pds.datetime(2009,1,1))
        ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1,1,36,59) ))
        # print (ans,ans2)
        # print (self.testInst.data.index[0], self.testInst.data.index[-1])
        assert ans & ans2

    def test_single_orbit_call_by_negative_1_index(self):
        self.testInst.load(2008,366)
        self.testInst.orbits[-1]
        ans = (self.testInst.data.index[0] == (pds.datetime(2009,1,1)-relativedelta(hours=1, minutes=37)) )
        ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1)-relativedelta(seconds=1) ))
        assert ans & ans2

    def test_all_single_orbit_calls_in_day(self):
        self.testInst.load(2009,1)
        ans = []; ans2=[];
        self.testInst.bounds= (pysat.datetime(2009,1,1), None)
        for i,inst in enumerate(self.testInst.orbits):
            if i > 14:
                break

            ans.append(self.testInst.data.index[0] == (pds.datetime(2009,1,1)+i*relativedelta(hours=1, minutes=37)))
            ans2.append(self.testInst.data.index[-1] == (pds.datetime(2009,1,1)+(i+1)*relativedelta(hours=1, minutes=37) -
                                                         relativedelta(seconds=1) ))

        assert np.all(ans) & np.all(ans2)

    def test_orbit_next_call_no_loaded_data(self):
        self.testInst.orbits.next()
        ans = (self.testInst.data.index[0] == pds.datetime(2008,1,1))
        #ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1,1,36,59) ))

        assert ans 

    def test_orbit_prev_call_no_loaded_data(self):
        self.testInst.orbits.prev()
        ans = (self.testInst.data.index[-1] == pds.datetime(2010,12,31,23,59,59))
        #ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1,1,36,59) ))

        assert ans 

    def test_single_orbit_call_orbit_starts_0_UT_using_next(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.next()
        ans = (self.testInst.data.index[0] == pds.datetime(2009,1,1))
        ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1,1,36,59) ))
        # print (ans,ans2)
        # print (self.testInst.data.index[0], self.testInst.data.index[-1])
        assert ans & ans2

    def test_single_orbit_call_orbit_starts_0_UT_using_prev(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.prev()
        ans = (self.testInst.data.index[0] == (pds.datetime(2009,1,1)+14*relativedelta(hours=1, minutes=37)) )
        ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1)+15*relativedelta(hours=1, minutes=37)-relativedelta(seconds=1) ))
        assert ans & ans2

    def test_single_orbit_call_orbit_starts_off_0_UT_using_next(self):
        from dateutil.relativedelta import relativedelta as relativedelta
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        # print self.testInst.data.index[0], pds.datetime(2008,12,30, 23, 45), self.testInst.data.index[-1], (pds.datetime(2008,12,30, 23, 45)+relativedelta(hours=1, minutes=36, seconds=59) )
        ans = (self.testInst.data.index[0] == pds.datetime(2008,12,30, 23, 45))
        ans2 = (self.testInst.data.index[-1] == (pds.datetime(2008,12,30, 23, 45)+relativedelta(hours=1, minutes=36, seconds=59) ))
        assert ans & ans2

    def test_single_orbit_call_orbit_starts_off_0_UT_using_prev(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.prev()
        ans = (self.testInst.data.index[0] == (pds.datetime(2009,1,1)-relativedelta(hours=1, minutes=37)) )
        ans2 = (self.testInst.data.index[-1] == (pds.datetime(2009,1,1)-relativedelta(seconds=1) ))
        assert ans & ans2

    def test_repeated_orbit_calls_symmetric_single_day_0_UT(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(10):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_symmetric_multi_day_0_UT(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_symmetric_single_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(10):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)
	
    def test_repeated_orbit_calls_symmetric_multi_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_antisymmetric_multi_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        for j in range(10):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_antisymmetric_multi_multi_day_off_0_UT(self):
        self.testInst.load(2008,366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(40):
            self.testInst.orbits.prev()
        for j in range(20):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data )

    def test_repeated_orbit_calls_antisymmetric_multi_day_0_UT(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        for j in range(10):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data )

    def test_repeated_orbit_calls_antisymmetric_multi_multi_day_0_UT(self):
        self.testInst.load(2009,1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(40):
            self.testInst.orbits.prev()
        for j in range(20):
            self.testInst.orbits.next()
        print(control.data)
        print(self.testInst.data)
        assert all(control.data == self.testInst.data )