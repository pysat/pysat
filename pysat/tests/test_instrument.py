# -*- coding: utf-8 -*-
#Test some of the basic _core functions
import sys
import pysat
import pandas as pds
from nose.tools import assert_raises, raises
import nose.tools
import pysat.instruments.pysat_testing
import numpy as np
if sys.version_info[0] >= 3:
    if sys.version_info[1] < 4:
        import imp
        reload = imp.reload
    else:
        import importlib
        reload = importlib.reload


class TestBasics:
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '10', 
                                         clean_level='clean',
                                         update_files=True)

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
        testInst = pysat.Instrument(inst_module=test, tag='', clean_level='clean')
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
        testIn = pysat.Instrument(inst_module=test, tag='', clean_level='clean')
        testIn.load(2009,1)

    @raises(AttributeError)
    def test_custom_instrument_load_3(self):
        '''
        Test if an exception is thrown correctly if there is no 
        instrument file and supplied routines are incomplete.
        '''
        import pysat.instruments.pysat_testing as test
        del test.load
        testIn = pysat.Instrument(inst_module=test, tag='', clean_level='clean')
        testIn.load(2009,1)

    def test_data_padding(self):
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        te = pysat.Instrument('pysat','testing', '', pad={'minutes':5})
        te.load(2009,1, verifyPad=True)
        assert ( (te.data.index[0] == te.date - pds.DateOffset(minutes=5)) & 
                (te.data.index[-1] == te.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + 
                                        pds.DateOffset(minutes=5)) )
            
    def test_data_padding_uniqueness(self):
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        te = pysat.Instrument('pysat','testing', '', pad={'minutes':5})
        te.load(2009,1, verifyPad=True)
        assert (te.data.index.is_unique)

    def test_data_padding_all_samples_present(self):
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        te = pysat.Instrument('pysat','testing', '', pad={'minutes':5})
        te.load(2009,1, verifyPad=True)
        test_index = pds.date_range(te.data.index[0], te.data.index[-1], freq='S')
        assert (np.all(te.data.index == test_index))


    def test_data_padding_removal(self):
        reload(pysat.instruments.pysat_testing)
        reload(pysat.instruments)
        te = pysat.Instrument('pysat','testing', '', pad={'minutes':5})
        te.load(2009,1)
        assert (te.data.index[0] == te.date ) & \
                (te.data.index[-1] == te.date + pds.DateOffset(hour=23, minutes=59,seconds=59) )
        
    def test_basic_data_access_by_name(self):
        self.testInst.load(2009,1)
        assert np.all(self.testInst['uts'] == self.testInst.data['uts'])
        
    def test_data_access_by_row_slicing_and_name(self):
        self.testInst.load(2009,1)
        assert np.all(self.testInst[0:10,'uts'] == self.testInst.data.ix[0:10,'uts'])

    def test_data_access_by_row_and_name(self):
        self.testInst.load(2009,1)
        assert np.all(self.testInst[0,'uts'] == self.testInst.data.ix[0,'uts'])

    def test_data_access_by_datetime_and_name(self):
        self.testInst.load(2009,1)
        assert np.all(self.testInst[pysat.datetime(2009,1,1,0,0,0),'uts'] == self.testInst.data.ix[0,'uts'])
       
    def test_data_access_by_datetime_slicing_and_name(self):
        self.testInst.load(2009,1)
        assert np.all(self.testInst[pysat.datetime(2009,1,1,0,0,0):pysat.datetime(2009,1,1,0,0,10),'uts'] == 
                        self.testInst.data.ix[0:11,'uts'])
                        
    def test_setting_data_by_name(self):
        self.testInst.load(2009,1)
        self.testInst['doubleMLT'] = 2.*self.testInst['mlt']
        assert np.all(self.testInst['doubleMLT'] == 2.*self.testInst['mlt'])

    def test_setting_partial_data_by_name(self):
        self.testInst.load(2009,1)
        self.testInst['doubleMLT'] = 2.*self.testInst['mlt']
        self.testInst[0,'doubleMLT'] = 0
        assert np.all(self.testInst[1:,'doubleMLT'] == 2.*self.testInst[1:,'mlt']) & (self.testInst[0,'doubleMLT'] == 0)

    def test_setting_partial_slice_data_by_name(self):
        self.testInst.load(2009,1)
        self.testInst['doubleMLT'] = 2.*self.testInst['mlt']
        self.testInst[0:10,'doubleMLT'] = 0
        assert np.all(self.testInst[10:,'doubleMLT'] == 2.*self.testInst[10:,'mlt']) & np.all(self.testInst[0:10,'doubleMLT'] == 0)
                        
    def test_set_bounds_by_date(self):
        start = pysat.datetime(2009,1,1)
        stop = pysat.datetime(2009,1,15)
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list == pds.date_range(start, stop).tolist())

    def test_iterate_over_bounds_set_by_date(self):
        start = pysat.datetime(2009,1,1)
        stop = pysat.datetime(2009,1,15)
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)            
        out = pds.date_range(start, stop).tolist()
        assert np.all(dates == out)
        
    def test_iterate_over_default_bounds(self):
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2010,12,31)
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)            
        out = pds.date_range(start, stop).tolist()
        assert np.all(dates == out)
        
    def test_set_bounds_by_date_season(self):
        start = [pysat.datetime(2009,1,1), pysat.datetime(2009,2,1)]
        stop = [pysat.datetime(2009,1,15), pysat.datetime(2009,2,15)]
        self.testInst.bounds = (start, stop)
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(self.testInst._iter_list == out)

    def test_iterate_over_bounds_set_by_date_season(self):
        start = [pysat.datetime(2009,1,1), pysat.datetime(2009,2,1)]
        stop = [pysat.datetime(2009,1,15), pysat.datetime(2009,2,15)]
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)            
        out = pds.date_range(start[0], stop[0]).tolist()
        out.extend(pds.date_range(start[1], stop[1]).tolist())
        assert np.all(dates == out)

    def test_set_bounds_by_fname(self):
        start = '01/01/09.nofile'
        stop = '01/03/09.nofile'
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list == 
            ['01/01/09.nofile', '01/02/09.nofile', '01/03/09.nofile'])

    def test_iterate_over_bounds_set_by_fname(self):
        start = '01/01/09.nofile'
        stop = '01/15/09.nofile'
        start_d = pysat.datetime(2009,1,1)
        stop_d = pysat.datetime(2009,1,15)
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)            
        out = pds.date_range(start_d, stop_d).tolist()
        assert np.all(dates == out)

    def test_iterate_over_bounds_set_by_fname_via_next(self):
        start = '01/01/09.nofile'
        stop = '01/15/09.nofile'
        start_d = pysat.datetime(2009,1,1)
        stop_d = pysat.datetime(2009,1,15)
        self.testInst.bounds = (start, stop)
        dates = []
        self.testInst.next()
        dates.append(self.testInst.date) 
        while self.testInst.date < stop_d:
            self.testInst.next()
            dates.append(self.testInst.date)            
        out = pds.date_range(start_d, stop_d).tolist()
        assert np.all(dates == out)

    def test_iterate_over_bounds_set_by_fname_via_prev(self):
        start = '01/01/09.nofile'
        stop = '01/15/09.nofile'
        start_d = pysat.datetime(2009,1,1)
        stop_d = pysat.datetime(2009,1,15)
        self.testInst.bounds = (start, stop)
        dates = []
        self.testInst.prev()
        dates.append(self.testInst.date) 
        while self.testInst.date > start_d:
            self.testInst.prev()
            dates.append(self.testInst.date)            
        out = pds.date_range(start_d, stop_d).tolist()
        assert np.all(dates == out[::-1])

    def test_set_bounds_by_fname_season(self):
        start = ['01/01/09.nofile', '02/01/09.nofile']
        stop = ['01/03/09.nofile', '02/03/09.nofile']
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list == 
            ['01/01/09.nofile', '01/02/09.nofile', '01/03/09.nofile',
            '02/01/09.nofile', '02/02/09.nofile', '02/03/09.nofile'])

    def test_iterate_over_bounds_set_by_fname_season(self):
        start = ['01/01/09.nofile', '02/01/09.nofile']
        stop = ['01/15/09.nofile', '02/15/09.nofile']
        start_d = [pysat.datetime(2009,1,1), pysat.datetime(2009,2,1)]
        stop_d = [pysat.datetime(2009,1,15), pysat.datetime(2009,2,15)]
        self.testInst.bounds = (start, stop)
        dates = []
        for inst in self.testInst:
            dates.append(inst.date)            
        out = pds.date_range(start_d[0], stop_d[0]).tolist()
        out.extend(pds.date_range(start_d[1], stop_d[1]).tolist())
        assert np.all(dates == out)
