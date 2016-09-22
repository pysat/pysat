"""
tests the pysat meta object and code
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

def prep_dir(inst=None):
    import os
    import shutil

    if inst is None:
        inst = pysat.Instrument(platform='pysat', name='testing')
    # create data directories
    try:
        os.makedirs(inst.files.data_path)
        #print ('Made Directory')
    except OSError:
        pass
    #dir = os.path.join(pysat.data_dir, inst.platform)
    #if not os.path.isdir(dir):
    #    os.mkdir(dir)
    #dir = os.path.join(pysat.data_dir, inst.platform, inst.name)
    #if not os.path.isdir(dir):
    #    os.mkdir(dir)

    # remove any files
    dir = inst.files.data_path
    for the_file in os.listdir(dir):
        if (the_file[0:13] == 'pysat_testing') & (the_file[-19:] == '.pysat_testing_file'):
            file_path = os.path.join(dir, the_file)
            if os.path.isfile(file_path):
                #print(file_path)
                os.unlink(file_path)
                #elif os.path.isdir(file_path): shutil.rmtree(file_path)


# create year doy file set
def create_files(inst, start=None, stop=None, freq='1D', use_doy=True,
                 root_fname=None):

    # create a bunch of files
    if start is None:
        start = pysat.datetime(2009, 1, 1)
    if stop is None:
        stop = pysat.datetime(2013, 12, 31)
    dates = pysat.utils.season_date_range(start, stop, freq=freq)
    
    if root_fname is None:
        root_fname = 'pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff.pysat_testing_file'
    
    # check that directory exists
    
            
    for date in dates:
        yr, doy = pysat.utils.getyrdoy(date)
        if use_doy:
            doy = doy
        else:
            doy = date.day        
            
        fname = os.path.join(inst.files.data_path, root_fname.format(year=yr, 
                             day=doy, month=date.month, hour=date.hour, min=date.minute, sec=date.second))
        with open(fname, 'w') as f:
            pass
        #f.close()

def list_year_doy_files(tag=None, data_path=None, format_str=None):
    if data_path is not None:
        return pysat.Files.from_os(data_path=data_path,
            format_str='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff.pysat_testing_file')
    else:
        raise ValueError ('A directory must be passed to the loading routine.')

def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data"""        
    if tag is not None:
        if tag == '':
            return pysat.Files.from_os(data_path=data_path, 
                format_str='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}_{hour:02d}_{min:02d}_{sec:02d}.pysat_testing_file')
        else:
            raise ValueError('Unrecognized tag name')                  
    else:
        raise ValueError ('A tag name must be passed ')


class TestBasics:
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        prep_dir()
        t_module = pysat.instruments.pysat_testing
        #t_module.list_files = list_year_doy_files
        self.testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing, clean_level='clean')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        prep_dir()
        del self.testInst
    
    def test_year_doy_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2009,12,31)
        create_files(self.testInst, start, stop, freq='1D')
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
            format_str='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff.pysat_testing_file')
        # check overall length
        check1 = len(files) == (365+366)  
        # check specific dates
        check2 = files.index[0].to_datetime() == pysat.datetime(2008,1,1)
        check3 = files.index[365].to_datetime() == pysat.datetime(2008,12,31)
        check4 = files.index[-1].to_datetime() == pysat.datetime(2009,12,31)

        assert(check1 & check2 & check3 & check4)

    def test_year_doy_files_no_gap_in_name_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2009,12,31)
        create_files(self.testInst, start, stop, freq='1D', 
                     root_fname='pysat_testing_junk_{year:04d}{day:03d}_stuff.pysat_testing_file')
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
            format_str='pysat_testing_junk_{year:04d}{day:03d}_stuff.pysat_testing_file')
        # check overall length
        check1 = len(files) == (365+366)  
        # check specific dates
        check2 = files.index[0].to_datetime() == pysat.datetime(2008,1,1)
        check3 = files.index[365].to_datetime() == pysat.datetime(2008,12,31)
        check4 = files.index[-1].to_datetime() == pysat.datetime(2009,12,31)

        assert(check1 & check2 & check3 & check4)

    def test_year_month_day_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2009,12,31)
        create_files(self.testInst, start, stop, freq='1D', use_doy=False,
                     root_fname='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}.pysat_testing_file')
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
            format_str='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}.pysat_testing_file')
        # check overall length
        check1 = len(files) == (365+366)  
        # check specific dates
        check2 = files.index[0].to_datetime() == pysat.datetime(2008,1,1)
        check3 = files.index[365].to_datetime() == pysat.datetime(2008,12,31)
        check4 = files.index[-1].to_datetime() == pysat.datetime(2009,12,31)

        assert(check1 & check2 & check3 & check4)

    def test_year_month_day_hour_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2009,12,31)
        create_files(self.testInst, start, stop, freq='6h',  
                     use_doy=False,
                     root_fname='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}_{hour:02d}.pysat_testing_file')
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
            format_str='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}_{hour:02d}.pysat_testing_file')
        # check overall length
        check1 = len(files) == (365+366)*4-3 
        # check specific dates
        check2 = files.index[0].to_datetime() == pysat.datetime(2008,1,1)
        check3 = files.index[1460].to_datetime() == pysat.datetime(2008,12,31)
        check4 = files.index[-1].to_datetime() == pysat.datetime(2009,12,31)
        assert(check1 & check2 & check3 & check4)

    def test_year_month_day_hour_minute_files_direct_call_to_from_os(self):
        root_fname='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}_{hour:02d}{min:02d}.pysat_testing_file'
        # create a bunch of files by year and doy
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2008,1,4)
        create_files(self.testInst, start, stop, freq='30min', 
                     use_doy=False,
                     root_fname=root_fname)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
            format_str=root_fname)
        # check overall length
        check1 = len(files) == 145 
        # check specific dates
        check2 = files.index[0].to_datetime() == pysat.datetime(2008,1,1)
        check3 = files.index[1].to_datetime() == pysat.datetime(2008,1,1,0,30)
        check4 = files.index[10].to_datetime() == pysat.datetime(2008,1,1,5,0)
        check5 = files.index[-1].to_datetime() == pysat.datetime(2008,1,4)

        assert(check1 & check2 & check3 & check4 & check5)

    def test_year_month_day_hour_minute_second_files_direct_call_to_from_os(self):
        root_fname='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}_{hour:02d}_{min:02d}_{sec:02d}.pysat_testing_file'
        # create a bunch of files by year and doy
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2008,1,3)
        create_files(self.testInst, start, stop, freq='30s',  
                     use_doy=False, 
                     root_fname = root_fname)
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
            format_str=root_fname)
        # check overall length
        check1 = len(files) == 5761 
        # check specific dates
        check2 = files.index[0].to_datetime() == pysat.datetime(2008,1,1)
        check3 = files.index[1].to_datetime() == pysat.datetime(2008,1,1,0,0,30)
        check4 = files.index[-1].to_datetime() == pysat.datetime(2008,1,3)

        assert(check1 & check2 & check3 & check4)

    def test_year_month_files_direct_call_to_from_os(self):
        # create a bunch of files by year and doy
        start = pysat.datetime(2008,1,1)
        stop = pysat.datetime(2009,12,31)
        create_files(self.testInst, start, stop, freq='1MS',  
                     root_fname='pysat_testing_junk_{year:04d}_gold_stuff_{month:02d}.pysat_testing_file')
        # use from_os function to get pandas Series of files and dates
        files = pysat.Files.from_os(data_path=self.testInst.files.data_path,
            format_str='pysat_testing_junk_{year:04d}_gold_stuff_{month:02d}.pysat_testing_file')
        # check overall length
        check1 = len(files) == 24
        # check specific dates
        check2 = files.index[0].to_datetime() == pysat.datetime(2008,1,1)
        check3 = files.index[11].to_datetime() == pysat.datetime(2008,12,1)
        check4 = files.index[-1].to_datetime() == pysat.datetime(2009,12,1)
        assert(check1 & check2 & check3 & check4)

    def test_instrument_has_no_files(self):
        import pysat.instruments.pysat_testing

        pysat.instruments.pysat_testing.list_files = list_files
        inst = pysat.Instrument(platform='pysat', name='testing', update_files=True)
        re_load(pysat.instruments.pysat_testing)
        assert(inst.files.files.empty)
        
    def test_instrument_has_files(self):
        import pysat.instruments.pysat_testing

        root_fname='pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}_{hour:02d}_{min:02d}_{sec:02d}.pysat_testing_file'
        # create a bunch of files by year and doy
        start = pysat.datetime(2007,12,31)
        stop = pysat.datetime(2008,1,10)
        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = root_fname)
        # create the same range of dates
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        pysat.instruments.pysat_testing.list_files = list_files
        inst = pysat.Instrument(platform='pysat', name='testing', update_files=True)
        re_load(pysat.instruments.pysat_testing)
        assert (np.all(inst.files.files.index == dates))



class TestInstrumentWithFiles:
        
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        prep_dir()
        # create a test instrument, make sure it is getting files fmor filesystem
        #import pysat.instruments.pysat_testing
        re_load(pysat.instruments.pysat_testing)
        #self.stored_files_fcn = pysat.instruments.pysat_testing.list_files
        pysat.instruments.pysat_testing.list_files = list_files
        # create a bunch of files by year and doy
        self.testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing, 
                                         clean_level='clean')

        self.root_fname = 'pysat_testing_junk_{year:04d}_gold_{day:03d}_stuff_{month:02d}_{hour:02d}_{min:02d}_{sec:02d}.pysat_testing_file'
        start = pysat.datetime(2007,12,31)
        stop = pysat.datetime(2008,1,10)
        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)

        self.testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing, 
                                         clean_level='clean', update_files=True)
        
    def teardown(self):
        """Runs after every method to clean up previous testing."""
        prep_dir(self.testInst)
        del self.testInst
        #pysat.instruments.pysat_testing = self.stored_files_fcn
        re_load(pysat.instruments.pysat_testing)
        re_load(pysat.instruments)
        # make sure everything about instrument state is restored
        # restore original file list
        pysat.Instrument(inst_module=pysat.instruments.pysat_testing, 
                                         clean_level='clean', update_files=True)

    def test_refresh(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008,1,10)
        stop = pysat.datetime(2008,1,12)

        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)
        start = pysat.datetime(2007,12,31)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))

    def test_refresh_on_unchanged_files(self):

        start = pysat.datetime(2007,12,31)
        stop = pysat.datetime(2008,1,10)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        assert (np.all(self.testInst.files.files.index == dates))
        
    def test_get_new_files_after_refresh(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008,1,11)
        stop = pysat.datetime(2008,1,12)

        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))
        
    def test_get_new_files_after_multiple_refreshes(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008,1,11)
        stop = pysat.datetime(2008,1,12)

        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        self.testInst.files.refresh()
        self.testInst.files.refresh()
        self.testInst.files.refresh()        
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates))
        
    def test_get_new_files_after_adding_files(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008,1,11)
        stop = pysat.datetime(2008,1,12)

        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        new_files = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates))

    def test_get_new_files_after_adding_files_and_adding_file(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008,1,11)
        stop = pysat.datetime(2008,1,12)

        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        new_files = self.testInst.files.get_new()

        start = pysat.datetime(2008,1,15)
        stop = pysat.datetime(2008,1,18)

        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)
        dates2 = pysat.utils.season_date_range(start, stop, freq='100min')
        new_files2 = self.testInst.files.get_new()
        assert (np.all(new_files.index == dates) & np.all(new_files2.index == dates2))

    def test_get_new_files_after_deleting_files_and_adding_files(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008,1,11)
        stop = pysat.datetime(2008,1,12)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        
        # remove files, same number as will be added
        to_be_removed = len(dates)
        for the_file in os.listdir(self.testInst.files.data_path):
            if (the_file[0:13] == 'pysat_testing') & (the_file[-19:] == '.pysat_testing_file'):
                file_path = os.path.join(self.testInst.files.data_path, the_file)
                if os.path.isfile(file_path) & (to_be_removed > 0):
                    #print(file_path)
                    to_be_removed -= 1
                    os.unlink(file_path)
                    
        # add new files
        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)
                     
        # get new files   
        new_files = self.testInst.files.get_new()

        assert (np.all(new_files.index == dates) )

    def test_files_non_standard_pysat_directory(self):
        # create new files and make sure that new files are captured
        start = pysat.datetime(2008,1,11)
        stop = pysat.datetime(2008,1,15)
        dates = pysat.utils.season_date_range(start, stop, freq='100min')
        
        self.testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing, 
                                         clean_level='clean',
                                         sat_id='hello',
                                         directory_format='pysat_testing_{tag}_{sat_id}',
                                         update_files=True)                    
        # add new files
        prep_dir(self.testInst)
        create_files(self.testInst, start, stop, freq='100min',  
                     use_doy=False, 
                     root_fname = self.root_fname)

        self.testInst = pysat.Instrument(inst_module=pysat.instruments.pysat_testing, 
                                clean_level='clean',
                                sat_id='hello',
                                directory_format='pysat_testing_{tag}_{sat_id}',
                                update_files=True)                    
                     
        # get new files   
        new_files = self.testInst.files.get_new()
        #print (dates)
        #print(self.testInst.files.files.index)
        #print('new_files ', new_files.index)
        assert (np.all(self.testInst.files.files.index == dates) & 
                np.all(new_files.index == dates) )
