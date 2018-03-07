import pysat
import pandas as pds
import numpy as np
from nose.tools import assert_raises, raises
import nose.tools

class TestBasics:
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing', tag='10',
                                         clean_level='clean')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    @raises(ValueError)        
    def test_single_modifying_custom_function(self):
        """Test if custom function works correctly. Modify function that
        returns pandas object. Modify function returns an object which will
        produce an Error.
        """
        def custom1(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            return 5.0 * inst.data['mlt']

        self.testInst.custom.add(custom1, 'modify')
        self.testInst.load(2009, 1)

    def test_single_adding_custom_function(self):
        """Test if custom function works correctly. Add function that returns
        pandas object.
        """
        def custom1(inst):
            d = 2.0 * inst.data.mlt
            d.name='doubleMLT'
            return d

        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'].values == 2.0 *
               self.testInst.data.mlt.values).all()
        assert ans

    def test_single_adding_custom_function_wrong_times(self):
        """Only the data at the correct time should be accepted, otherwise it
        returns nan
        """
        def custom1(inst):
            d = 2.0 * inst.data.mlt
            d.name='doubleMLT'
            d.index += pds.DateOffset(microseconds=10)
            return d

        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'].isnull()).all()
        assert ans

    def test_single_adding_custom_function_that_modifies_passed_data(self):
        """Test if custom function works correctly. Add function that returns
        pandas object but modifies passed satellite object.
        Changes to passed object should not propagate back.
        """
        def custom1(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            inst.data.mlt=0.
            return inst.data.doubleMLT

        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'] == 2.0 *
               self.testInst.data.mlt).all()
        assert ans

    def test_add_function_tuple_return_style(self):
        """Test if custom function works correctly. Add function that returns 
        name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT',2.0 * inst.data.mlt.values)
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (self.testInst.data['doubleMLT'] == 2.0 *
               self.testInst.data.mlt).all()
        assert ans
        
    def test_add_multiple_custom_functions_tuple_return_style(self):
        """Test if multiple custom functions that add data work correctly. Add
        function that returns name and numpy array.
        """
        def custom1(inst):
            return (['doubleMLT', 'tripleMLT'],[2.0 * inst.data.mlt.values,
                                                3.0 * inst.data.mlt.values])
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
        ans = (((self.testInst.data['doubleMLT'] == 2.0 *
                 self.testInst.data.mlt).all()) &
               ((self.testInst.data['tripleMLT'] == 3.0 *
                 self.testInst.data.mlt).all()))
        assert ans

    @raises(ValueError)
    def test_add_function_tuple_return_style_too_few_elements(self):
        """Test if custom function works correctly. Add function that returns
        name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT',2.0 * inst.data.mlt.values[0:-5])
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)

    @raises(ValueError)
    def test_add_function_tuple_return_style_too_many_elements(self):
        """Test if custom function works correctly. Add function that returns
        name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT',np.arange(2.0 * len(inst.data.mlt)))
        self.testInst.custom.add(custom1, 'add')  
        self.testInst.load(2009,1)
                                                        
    def test_add_dataframe(self):
        def custom1(inst):
            out = pysat.DataFrame({'doubleMLT':inst.data.mlt * 2, 
                                'tripleMLT':inst.data.mlt * 3}, 
                                index=inst.data.index)
            return out
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans = (((self.testInst.data['doubleMLT'] == 2.0 *
                 self.testInst.data.mlt).all()) &
               ((self.testInst.data['tripleMLT'] == 3.0 *
                 self.testInst.data.mlt).all()))
        assert ans

    def test_add_dataframe_w_meta(self):
        def custom1(inst):
            out = pysat.DataFrame({'doubleMLT':inst.data.mlt * 2, 
                                'tripleMLT':inst.data.mlt * 3}, 
                                index=inst.data.index)
            return {'data':out, 'long_name':['doubleMLTlong', 'tripleMLTlong'],
                    'units':['hours1', 'hours2']}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        ans3 = self.testInst.meta['tripleMLT'].units == 'hours2'        
        ans4 = self.testInst.meta['tripleMLT'].long_name == 'tripleMLTlong'
        ans5 = (self.testInst['doubleMLT'] == 2.0*self.testInst.data.mlt).all()
        ans6 = (self.testInst['tripleMLT'] == 3.0*self.testInst.data.mlt).all()
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
        ans3 = (self.testInst['doubleMLT'] == 2.0*self.testInst.data.mlt).all()
        assert ans1 & ans2 & ans3

    def test_add_series_w_meta_missing_long_name(self):
        def custom1(inst):
            out = pysat.Series(2.0 * inst.data.mlt.values, 
                                index=inst.data.index)
            out.name = 'doubleMLT'
            return {'data':out, 
                    'units':'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLT'
        ans3 = (self.testInst['doubleMLT'] == 2.0*self.testInst.data.mlt).all()
        assert ans1 & ans2 & ans3        
        
    def test_add_series_w_meta_name_in_dict(self):
        def custom1(inst):
            out = pysat.Series(2.0 * inst.data.mlt.values, 
                               index=inst.data.index)
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1', 'name':'doubleMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009,1)
        ans1 = self.testInst.meta['doubleMLT'].units == 'hours1'
        ans2 = self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        ans3 = (self.testInst['doubleMLT'] == 2.0*self.testInst.data.mlt).all()
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
        ans3 = (self.testInst['doubleMLT'] == 2.0*self.testInst.data.mlt).all()
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
        ans3 = (self.testInst['doubleMLT'] == 2.0*self.testInst.data.mlt).all()
        assert ans1 & ans2 * ans3

    @raises(ValueError)  
    def test_add_list_w_meta_no_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).tolist()
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009, 1)
        
    def test_clear_functions(self):
        def custom1(inst):
            out = (inst.data.mlt*2).values
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1', 'name':'doubleMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.custom.clear()
        check1 = self.testInst.custom._functions == []
        check2 = self.testInst.custom._kind == []
        assert check1 & check2
        
    def test_pass_functions(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return 
        self.testInst.custom.add(custom1, 'pass')
        self.testInst.load(2009, 1)

        assert True
    @raises(ValueError)    
    def test_pass_functions_no_return_allowed(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1', 'name':'doubleMLT'}
        self.testInst.custom.add(custom1, 'pass')
        self.testInst.load(2009, 1)

        assert True
    
    @raises(AttributeError)
    def test_add_multiple_functions_one_not_at_end(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data':out, 'long_name':'doubleMLTlong',
                    'units':'hours1', 'name':'doubleMLT'}
        def custom2(inst):
            out = (inst.data.mlt * 3).values
            return {'data':out, 'long_name':'tripleMLTlong',
                    'units':'hours1', 'name':'tripleMLT'}
        def custom3(inst):
            out = (inst.data.tripleMLT * 2).values
            return {'data':out, 'long_name':'quadMLTlong',
                    'units':'hours1', 'name':'quadMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.custom.add(custom2, 'add')
        # if this runs correctly, an error will be thrown
        # since the data required by custom3 won't be present yet
        self.testInst.custom.add(custom3, 'add', at_pos=1)
        self.testInst.load(2009,1)

class TestOMNICustom:
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.test_angles = [340.0, 348.0, 358.9, 0.5, 5.0, 9.87]
        self.test_nan = [340.0, 348.0, 358.9, 0.5, 5.0, 9.87, np.nan]
        self.circ_kwargs = {"high":360.0, "low":0.0}
        self.testInst = pysat.Instrument('pysat', 'testing', tag='10',
                                         clean_level='clean')
        self.testInst.data['BY_GSM'] = pds.Series(6.0 * \
                    np.random.sample(size=self.testInst.data.index.shape[0]))
        self.testInst.data['BZ_GSM'] = pds.Series(6.0 * \
                    np.random.sample(size=self.testInst.data.index.shape[0]))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.test_angles, self.test_nan, self.circ_kwargs, self.testInst

    def test_circmean(self):
        """ Test custom circular mean."""
        from scipy import stats

        ref_mean = stats.circmean(self.test_angles, self.circ_kwargs)
        test_mean = pysat.instruments.omni_hro.nan_circmean(self.test_angles,
                                                            self.circ_kwargs)
        ans1 = ref_mean == test_mean

        ref_nan = stats.circmean(self.test_nan, self.circ_kwargs)
        test_nan = pysat.instruments.omni_hro.nan_circmean(self.test_nan,
                                                           self.circ_kwargs)

        ans2 = np.isnan(ref_nan)
        ans3 = test_mean == test_nan

        assert ans1 & ans2 & ans3

    def test_circstd(self):
        """ Test custom circular std."""
        from scipy import stats

        ref_std = stats.circstd(self.test_angles, self.circ_kwargs)
        test_std = pysat.instruments.omni_hro.nan_circstd(self.test_angles,
                                                          self.circ_kwargs)
        ans1 = ref_std == test_std

        ref_nan = stats.circstd(self.test_nan, self.circ_kwargs)
        test_nan = pysat.instruments.omni_hro.nan_circstd(self.test_nan,
                                                          self.circ_kwargs)

        ans2 = np.isnan(ref_nan)
        ans3 = test_std == test_nan

        assert ans1 & ans2 & ans3

    def test_clock_angle(self):
        """ Test clock angle."""

        # Run the clock angle routine
        pysat.instruments.omni_hro.calculate_clock_angle(inst)

        # Calculate clock angle
        test_angle = np.degrees(np.arctan2(inst['BY_GSM'], inst['BZ_GSM']))

        # Test the difference.  There may be a 2 pi integer ambiguity
        test_diff = set([aa for aa in (test_angle - inst['clock_angle'])
                         if not np.isnan(aa)])

        ans1 = np.all([aa in [0.0, 360.0, -360.0] for aa in test_diff])

        assert ans1

    def test_yz_plane_mag(self):
        """ Test the Byz plane magnitude calculation."""

        # Run the clock angle routine
        pysat.instruments.omni_hro.calculate_clock_angle(inst)

        # Calculate plane magnitude
        test_mag = np.sqrt(inst['BY_GSM']**2 + inst['BZ_GSM']**2)

        # Test the difference
        test_diff = list(set([mm for mm in (test_mag - inst['BYZ_GSM'])
                              if not np.isnan(mm)]))

        ans1 = test_diff[0] == 0.0
        ans2 = len(test_diff) == 1

        assert ans1 & ans2

    def test_yz_plane_cv(self):
        """ Test the IMF steadiness calculation."""

        # Run the clock angle and steadiness routines
        pysat.instruments.omni_hro.calculate_clock_angle(inst)
        pysat.instruments.omni_hro.calculate_imf_steadiness(inst)

        # Ensure the BYZ coefficient of variation is calculated correctly
        byz_mean = inst['BYZ_GSM'].rolling(min_periods=min_wnum, center=True,
                                           window=steady_window).mean()
        byz_std = inst['BYZ_GSM'].rolling(min_periods=min_wnum, center=True,
                                          window=steady_window).std()
        byz_cv = byz_std / byz_mean

        # Test the difference
        test_diff = list(set([mm for mm in (byz_cv - inst['BYZ_CV'])
                              if not np.isnan(mm)]))

        ans1 = test_diff[0] == 0.0
        ans2 = len(test_diff) == 1

        assert ans1 & ans2

    def test_clock_angle_std(self):
        """ Test the IMF steadiness calculation."""

        # Run the clock angle and steadiness routines
        pysat.instruments.omni_hro.calculate_clock_angle(inst)
        pysat.instruments.omni_hro.calculate_imf_steadiness(inst)

        # Ensure the BYZ coefficient of variation is calculated correctly
        ca_std = inst['clock_angle'].rolling(min_periods=min_wnum, center=True,
                                             window=steady_window).apply( \
                pysat.instrument.omni_hro.nan_circstd, kwargs=self.circ_kwargs)

        # Test the difference
        test_diff = list(set([aa for aa in (ca_std - inst['clock_angle_std'])
                              if not np.isnan(aa)]))

        ans1 = test_diff[0] == 0.0
        ans2 = len(test_diff) == 1

        assert ans1 & ans2
