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

###########################
    # basic loading tests, by date, filename, file id 
    # and checks for .next and .prev data loading   
    def test_basic_instrument_load(self):
        '''Test if the correct day is being loaded (checking object date and data).'''
        self.testInst.load(2009,1)
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert (test_date == pds.datetime(2009,1,1)) & (test_date == self.testInst.date)

    def test_basic_instrument_load_data(self):
        '''Test if the correct day is being loaded (checking data down to the second).'''
        self.testInst.load(2009,1)
        assert self.testInst.data.index[0] == pds.datetime(2009,1,1,0,0,0)

    def test_basic_instrument_load_leap_year(self):
        '''Test if the correct day is being loaded (Leap-Year).'''
        self.testInst.load(2008,366)
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert (test_date == pds.datetime(2008,12,31))  & (test_date == self.testInst.date)

    def test_next_load_default(self):
        '''Test if first day is loaded by default when first invoking .next.'''
        self.testInst.next()
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert test_date == pds.datetime(2008,1,1)

    def test_prev_load_default(self):
        '''Test if last day is loaded by default when first invoking .prev.'''
        self.testInst.prev()
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert test_date == pds.datetime(2010,12,31)
        
    def test_basic_fid_instrument_load(self):
        '''Test if first day is loaded by default when first invoking .next.'''
        self.testInst.load(fid=0)
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert (test_date == pds.datetime(2008,1,1)) & (test_date == self.testInst.date)

    def test_next_fid_load_default(self):
        '''Test next day is being loaded (checking object date).'''
        self.testInst.load(fid=0)
        self.testInst.next()
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert (test_date == pds.datetime(2008,1,2)) & (test_date == self.testInst.date)

    def test_prev_fid_load_default(self):
        '''Test prev day is loaded when invoking .prev.'''
        self.testInst.load(fid=3)
        self.testInst.prev()
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert (test_date == pds.datetime(2008,1,3))  & (test_date == self.testInst.date)
         
    def test_filename_load(self):
        '''Test if file is loadable by filename, relative to top_data_dir/platform/name/tag'''
        self.testInst.load(fname='12/31/10.nofile')
        assert self.testInst.data.index[0] == pds.datetime(2010,12,31)

    def test_next_filename_load_default(self):
        '''Test next day is being loaded (checking object date).'''
        self.testInst.load(fname='12/30/10.nofile')
        self.testInst.next()
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert (test_date == pds.datetime(2010,12,31)) & (test_date == self.testInst.date)

    def test_prev_filename_load_default(self):
        '''Test prev day is loaded when invoking .prev.'''
        self.testInst.load(fname='01/04/09.nofile')
        # print(self.testInst.date)
        self.testInst.prev()
        test_date = self.testInst.data.index[0]
        test_date = pysat.datetime(test_date.year, test_date.month, test_date.day)
        assert (test_date == pds.datetime(2009,1,3))  & (test_date == self.testInst.date)

    ###########################
    # test flags
    def test_empty_flag_data_empty(self):
        assert self.testInst.empty

    def test_empty_flag_data_not_empty(self):
        self.testInst.load(2009, 1)
        assert not self.testInst.empty

    ############################
    # test the textual representation
    def test_basic_repr(self):
        print(self.testInst)
        assert True

    def test_repr_w_orbit(self):
        self.testInst.orbit_info = {'index': 'mlt', 'kind': 'local time', 'period': np.timedelta64(97, 'm')}
        self.testInst.orbits.num = 10
        print(self.testInst)
        assert True

    def test_repr_w_padding(self):
        self.testInst.pad = pds.DateOffset(minutes=5)
        print(self.testInst)
        assert True

    def test_repr_w_custom_func(self):
        def testfunc(self):
            pass
        self.testInst.custom.add(testfunc, 'modify')
        print(self.testInst)
        assert True

    def test_repr_w_load_data(self):
        self.testInst.load(2009,1)
        print(self.testInst)
        assert True

### testing init functions

###### need to check with default1!!!!!                        
    def test_instrument_init(self):
        """Test if init function supplied by instrument can modify object"""
        assert self.testInst.new_thing==True



#     def test_getyrdoy_1(self):
#         '''Test the date to year, day of year code functionality'''
#         date = pds.datetime(2009,1,1)
#         yr, doy = pysat.utils.getyrdoy(date)
#         assert ((yr == 2009) & (doy == 1))
# 
#     def test_getyrdoy_leap_year(self):
#         '''Test the date to year, day of year code functionality (leap_year)'''
#         date = pds.datetime(2008,12,31)
#         yr, doy = pysat.utils.getyrdoy(date)
#         assert ((yr == 2008) & (doy == 366)) 

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

###################3
        # test data access features        
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

    def test_setting_data_by_name_with_meta(self):
        self.testInst.load(2009,1)
        self.testInst['doubleMLT'] = {'data':2.*self.testInst['mlt'],
                                      'units':'hours',
                                      'long_name':'double trouble'}
        check1 = np.all(self.testInst['doubleMLT'] == 2.*self.testInst['mlt'])
        check2 = self.testInst.meta['doubleMLT'].units == 'hours'
        check3 = self.testInst.meta['doubleMLT'].long_name == 'double trouble'                               
        assert check1 & check2 & check3

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

#######################
######
#### check iteration behavior                        
    @raises(StopIteration)
    def test_left_bounds_with_prev(self):
        '''Test if passing bounds raises StopIteration.'''
        # load first data
        self.testInst.next()
        # go back to no data
        self.testInst.prev()
        # self.testInst.prev()        
        
    @raises(StopIteration)
    def test_right_bounds_with_next(self):
        '''Test if passing bounds raises StopIteration.'''
        # load last data
        self.testInst.prev()
        # move on to future data that doesn't exist
        self.testInst.next()
        # self.testInst.next()        
                                                                                                                                         
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
        
    def test_creating_empty_instrument_object(self):
        null = pysat.Instrument()
        
        assert isinstance(null, pysat.Instrument)

    @raises(ValueError)
    def test_incorrect_creation_empty_instrument_object(self):
        # both name and platform should be empty
        null = pysat.Instrument(platform='cnofs')
        
    @raises(AttributeError)        
    def test_supplying_instrument_module_requires_name_and_platform(self):
        class Dummy: pass
        Dummy.name = 'help'
        
        temp = pysat.Instrument(inst_module=Dummy)


class TestDataPaddingbyFile():
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         pad={'minutes':5},
                                         update_files=True)
        self.testInst.bounds = ('01/01/08.nofile','12/31/10.nofile')
        
        self.rawInst = pysat.Instrument('pysat', 'testing', '', 
                                    clean_level='clean',
                                    update_files=True)
        self.rawInst.bounds = self.testInst.bounds


    def test_fid_data_padding(self):
        self.testInst.load(fid=1, verifyPad=True)
        self.rawInst.load(fid=1)
        assert ( (self.testInst.data.index[0] == self.rawInst.data.index[0] - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.rawInst.data.index[-1] + pds.DateOffset(minutes=5)) )

    def test_fid_data_padding_next(self):
        self.testInst.load(fid=1, verifyPad=True)
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fid=2)
        assert ( (self.testInst.data.index[0] == self.rawInst.data.index[0] - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.rawInst.data.index[-1] + pds.DateOffset(minutes=5)) )

    def test_fid_data_padding_multi_next(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(fid=1)
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        self.rawInst.load(fid=3)
        assert ( (self.testInst.data.index[0] == self.rawInst.data.index[0] - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.rawInst.data.index[-1] + pds.DateOffset(minutes=5)) )

    def test_fid_data_padding_prev(self):
        self.testInst.load(fid=2, verifyPad=True)
        self.testInst.prev(verifyPad=True)
        #print(self.testInst.data.index)
        self.rawInst.load(fid=1)
        #print(self.rawInst.data.index)
        #print(self.testInst.data.index[0], self.rawInst.data.index[0] - pds.DateOffset(minutes=5),
        #   self.testInst.data.index[-1],  self.rawInst.data.index[-1] + pds.DateOffset(minutes=5))
        assert ( (self.testInst.data.index[0] == self.rawInst.data.index[0] - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.rawInst.data.index[-1] + pds.DateOffset(minutes=5)) )

    def test_fid_data_padding_multi_prev(self):
        """This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(fid=10)
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        self.rawInst.load(fid=8)
        assert ( (self.testInst.data.index[0] == self.rawInst.data.index[0] - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.rawInst.data.index[-1] + pds.DateOffset(minutes=5)) )

    def test_fid_data_padding_jump(self):
        self.testInst.load(fid=1, verifyPad=True)
        self.testInst.load(fid=10, verifyPad=True)
        self.rawInst.load(fid=10)
        assert ( (self.testInst.data.index[0] == self.rawInst.data.index[0] - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.rawInst.data.index[-1] + pds.DateOffset(minutes=5)) )
                
    def test_fid_data_padding_uniqueness(self):
        self.testInst.load(fid=1, verifyPad=True)
        assert (self.testInst.data.index.is_unique)

    def test_fid_data_padding_all_samples_present(self):
        self.testInst.load(fid=1, verifyPad=True)
        test_index = pds.date_range(self.testInst.data.index[0], self.testInst.data.index[-1], freq='S')
        #print (test_index[0], test_index[-1], len(test_index))
        #print(self.testInst.data.index[0], self.testInst.data.index[-1], len(self.testInst.data))
        assert (np.all(self.testInst.data.index == test_index))

    def test_fid_data_padding_removal(self):
        self.testInst.load(fid=1)
        self.rawInst.load(fid=1)
        #print(self.testInst.data.index)
        #print(new_inst.data.index)
        assert (self.testInst.data.index[0] == self.rawInst.data.index[0] ) & \
                (self.testInst.data.index[-1] == self.rawInst.data.index[-1]) & \
                (len(self.rawInst.data) == len(self.testInst.data))


class TestOffsetRightFileDataPaddingBasics(TestDataPaddingbyFile):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes':5})
        self.rawInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True)
        self.testInst.bounds = ('01/01/08.nofile','12/31/10.nofile')
        self.rawInst.bounds = self.testInst.bounds

class TestOffsetLeftFileDataPaddingBasics(TestDataPaddingbyFile):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes':5})
        self.rawInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True)
        self.testInst.bounds = ('01/01/08.nofile','12/31/10.nofile')
        self.rawInst.bounds = self.testInst.bounds

class TestDataPadding():
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         pad={'minutes':5},
                                         update_files=True)

    def test_data_padding(self):
        self.testInst.load(2009,2, verifyPad=True)
        assert ( (self.testInst.data.index[0] == self.testInst.date - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.testInst.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + 
                                        pds.DateOffset(minutes=5)) )

    def test_yrdoy_data_padding_missing_days(self):
        self.testInst.load(2008,1)
        # test load
        self.testInst.load(2008,0)
        # reset buffer data
        self.testInst.load(2008,-5)
        # test load, prev day empty, current and next has data
        self.testInst.load(2008,1)
        # reset
        self.testInst.load(2008,-4)
        # etc
        self.testInst.load(2008,2)
        self.testInst.load(2008,-3)
        self.testInst.load(2008,3)
        # switch to missing data on the right
        self.testInst.load(2010,365)
        self.testInst.load(2010,360)
        self.testInst.load(2010,366)
        self.testInst.load(2010,360)
        self.testInst.load(2010,367)
        assert True

    def test_data_padding_next(self):
        self.testInst.load(2009,2, verifyPad=True)
        self.testInst.next(verifyPad=True)
        assert ( (self.testInst.data.index[0] == self.testInst.date - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.testInst.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + 
                                        pds.DateOffset(minutes=5)) )

    def test_data_padding_multi_next(self):
        #"""This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(2009,2)
        self.testInst.next()
        self.testInst.next(verifyPad=True)
        assert ( (self.testInst.data.index[0] == self.testInst.date - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.testInst.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + 
                                        pds.DateOffset(minutes=5)) )

    def test_data_padding_prev(self):
        self.testInst.load(2009, 2, verifyPad=True)
        self.testInst.prev(verifyPad=True)
        print(self.testInst.data.index)
        assert ( (self.testInst.data.index[0] == self.testInst.date - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.testInst.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + 
                                        pds.DateOffset(minutes=5)) )

    def test_data_padding_multi_prev(self):
        #"""This also tests that _prev_data and _next_data cacheing"""
        self.testInst.load(2009, 10)
        self.testInst.prev()
        self.testInst.prev(verifyPad=True)
        assert ( (self.testInst.data.index[0] == self.testInst.date - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.testInst.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + 
                                        pds.DateOffset(minutes=5)) )

    def test_data_padding_jump(self):
        self.testInst.load(2009, 2, verifyPad=True)
        self.testInst.load(2009, 11, verifyPad=True)
        assert ( (self.testInst.data.index[0] == self.testInst.date - pds.DateOffset(minutes=5)) & 
                (self.testInst.data.index[-1] == self.testInst.date + pds.DateOffset(hours=23,minutes=59,seconds=59) + 
                                        pds.DateOffset(minutes=5)) )
                     
    def test_data_padding_uniqueness(self):
        self.testInst.load(2009,1, verifyPad=True)
        assert (self.testInst.data.index.is_unique)

    def test_data_padding_all_samples_present(self):
        self.testInst.load(2009,1, verifyPad=True)
        test_index = pds.date_range(self.testInst.data.index[0], self.testInst.data.index[-1], freq='S')
        assert (np.all(self.testInst.data.index == test_index))

    def test_data_padding_removal(self):
        self.testInst.load(2009,1)
        #print(self.testInst.data.index)
        assert (self.testInst.data.index[0] == self.testInst.date) & \
               (self.testInst.data.index[-1] == self.testInst.date + pds.DateOffset(hour=23, minutes=59,seconds=59))
                
                                
class TestMultiFileRightDataPaddingBasics(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_right=True,
                                         pad={'minutes':5},
                                         multi_file_day=True)
       
class TestMultiFileLeftDataPaddingBasics(TestDataPadding):
    def setup(self):
        reload(pysat.instruments.pysat_testing)
        '''Runs before every method to create a clean testing setup.'''
        self.testInst = pysat.Instrument('pysat', 'testing', '', 
                                         clean_level='clean',
                                         update_files=True,
                                         sim_multi_file_left=True,
                                         pad={'minutes':5},
                                         multi_file_day=True)
        

