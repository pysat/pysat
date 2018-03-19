"""
tests the pysat averaging code
"""
import pysat
import pandas as pds
from nose.tools import assert_raises, raises
import nose.tools
import pysat.instruments.pysat_testing
import numpy as np
import os

import sys
if sys.version_info[0] >= 3:
    if sys.version_info[1] < 4:
        import imp
        re_load = imp.reload
    else:
        import importlib
        re_load = importlib.reload
else:
    re_load = reload


class TestBasics:
    def setup(self):
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat','testing', clean_level='clean')

    def teardown(self):
        '''Runs after every method to clean up previous testing.'''
        del self.testInst

    def test_basic_seasonal_average(self):
        
        self.testInst.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        results = pysat.ssnl.avg.median2D(self.testInst, [0., 360., 24.], 'longitude',
                                          [0., 24, 24], 'mlt', ['dummy1', 'dummy2', 'dummy3'])
        dummy_val = results['dummy1']['median']
        dummy_dev = results['dummy1']['avg_abs_dev']

        dummy2_val = results['dummy2']['median']
        dummy2_dev = results['dummy2']['avg_abs_dev']

        dummy3_val = results['dummy3']['median']
        dummy3_dev = results['dummy3']['avg_abs_dev']
        
        dummy_x = results['dummy1']['bin_x']
        dummy_y = results['dummy1']['bin_y']
        
        # iterate over all y rows, value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, y in enumerate(dummy_y[:-1]):
            check.append(np.all(dummy_val[i, :] == y.astype(int)))
            check.append(np.all(dummy_dev[i, :] == 0))

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy2_val[:, i] == x/15.) )
            check.append(np.all(dummy2_dev[:, i] == 0))

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy3_val[:, i] == x/15.*1000. + dummy_y[:-1]) )
            check.append(np.all(dummy3_dev[:, i] == 0))
                            
        import code
        code.interact(local=dict(globals(), **locals())) # FIXME
        assert self.testInst.data.size == sum([ sum(i) for i in results['dummy1']['count'] ])

        assert False
        assert np.all(check)

    def test_basic_daily_mean(self):        
        self.testInst.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        ans = pysat.ssnl.avg.mean_by_day(self.testInst, 'dummy4')
        assert np.all(ans == 86399/2.)
        
    def test_basic_orbit_mean(self):
        orbit_info = {'kind':'local time', 'index':'mlt'}
        self.testInst = pysat.Instrument('pysat','testing', clean_level='clean', orbit_info=orbit_info)      
        self.testInst.bounds = (pysat.datetime(2009,1,1), pysat.datetime(2009,1,2))
        ans = pysat.ssnl.avg.mean_by_orbit(self.testInst, 'mlt')
        # note last orbit is incomplete thus not expected to satisfy relation
        assert np.allclose(ans[:-1], np.ones(len(ans)-1)*12., 1.E-2)

    def test_basic_file_mean(self):
        index = pds.date_range(pysat.datetime(2008,1,1), pysat.datetime(2008,2,1)) 
        names = [ date.strftime('%D')+'.nofile' for date in index]
        #print (self.testInst.files.files)
        #print(names)
        self.testInst.bounds = (names[0], names[-1])
        ans = pysat.ssnl.avg.mean_by_file(self.testInst, 'dummy4')
        assert np.all(ans == 86399/2.)

class TestConstellation:
    def setup(self):
        insts = []
        for i in range(5):
            insts.append(pysat.Instrument('pysat','testing', clean_level='clean'))
        self.testC = pysat.Constellation(instruments=insts)

    def teardown(self):
        del self.testC

    def test_constellation_average(self):
        for i in self.testC.instruments:
            i.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        results = pysat.ssnl.avg.median2D(self.testC, [0., 360., 24.], 'longitude',
                                          [0., 24, 24], 'mlt', ['dummy1', 'dummy2', 'dummy3'])
        dummy_val = results['dummy1']['median']
        dummy_dev = results['dummy1']['avg_abs_dev']

        dummy2_val = results['dummy2']['median']
        dummy2_dev = results['dummy2']['avg_abs_dev']

        dummy3_val = results['dummy3']['median']
        dummy3_dev = results['dummy3']['avg_abs_dev']
        
        dummy_x = results['dummy1']['bin_x']
        dummy_y = results['dummy1']['bin_y']

        # iterate over all y rows, value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, y in enumerate(dummy_y[:-1]):
            check.append(np.all(dummy_val[i, :] == y.astype(int)))
            check.append(np.all(dummy_dev[i, :] == 0))

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy2_val[:, i] == x/15.) )
            check.append(np.all(dummy2_dev[:, i] == 0))

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy3_val[:, i] == x/15.*1000. + dummy_y[:-1]) )
            check.append(np.all(dummy3_dev[:, i] == 0))
                            
        assert np.all(check)


class TestHeterogenousConstellation(TestConstellation):
    def setup(self):
        insts = []
        for i in range(2):
            insts.append(pysat.Instrument('pysat','testing', clean_level='clean', root_date = pysat.datetime(2009,1,i+1)))
        self.testC = pysat.Constellation(instruments=insts)

class Test2DConstellation:
    def setup(self):
        insts = []
        insts.append(pysat.Instrument('pysat','testing2d', clean_level='clean'))
        self.testC = pysat.Constellation(insts)

    def teardown(self):
        del self.testC

    def test_2D_avg(self):
        for i in self.testC.instruments:
            i.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        results = pysat.ssnl.avg.median2D(self.testC, [0., 360., 24.], 'mlt',
                                          [0., 24, 24], 'slt', ['uts'])
        dummy_val = results['uts']['median']
        dummy_dev = results['uts']['avg_abs_dev']

        dummy_x = results['uts']['bin_x']
        dummy_y = results['uts']['bin_y']

        # iterate over all y rows, value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, y in enumerate(dummy_y[:-1]):
            check.append(np.all(dummy_val[i, :] == y.astype(int)))
            check.append(np.all(dummy_dev[i, :] == 0))
