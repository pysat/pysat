import numpy as np
import warnings

from nose.tools import raises
import pandas as pds

import pysat


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing', tag='10',
                                         clean_level='clean')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def add(self, function, kind='add', at_pos='end', *args, **kwargs):
        '''Adds a function to the object's custom queue'''
        self.testInst.custom.add(function, kind, at_pos, *args, **kwargs)

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
            d = 2.0 * inst['mlt']
            d.name = 'doubleMLT'
            return d

        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst['doubleMLT'].values == 2.0 *
                self.testInst['mlt'].values).all()

    def test_single_adding_custom_function_wrong_times(self):
        """Only the data at the correct time should be accepted, otherwise it
        returns nan
        """
        def custom1(inst):
            new_index = inst.index+pds.DateOffset(milliseconds=500)
            d = pds.Series(2.0 * inst['mlt'], index=new_index)
            d.name = 'doubleMLT'
            print(new_index)
            return d

        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        ans = (self.testInst['doubleMLT'].isnull()).all()
        if self.testInst.pandas_format:
            assert ans
        else:
            print("Warning! Xarray doesn't enforce the same times on all " +
                  "parameters in dataset.")

    def test_single_adding_custom_function_that_modifies_passed_data(self):
        """Test if custom function works correctly. Add function that returns
        pandas object but modifies passed satellite object.
        Changes to passed object should not propagate back.
        """
        def custom1(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            inst['mlt'] = 0.
            return inst.data.doubleMLT

        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst.data['doubleMLT'] == 2.0 *
                self.testInst['mlt']).all()

    def test_add_function_tuple_return_style(self):
        """Test if custom function works correctly. Add function that returns
        name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT', 2.0 * inst.data.mlt.values)
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009, 1)
        print(self.testInst['doubleMLT'])
        print(2.0 * self.testInst['mlt'])
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()

    def test_add_multiple_custom_functions_tuple_return_style(self):
        """Test if multiple custom functions that add data work correctly. Add
        function that returns name and numpy array.
        """
        def custom1(inst):
            return (['doubleMLT', 'tripleMLT'], [2.0 * inst.data.mlt.values,
                                                 3.0 * inst.data.mlt.values])
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst.data['doubleMLT'] == 2.0 *
                self.testInst['mlt']).all()
        assert (self.testInst.data['tripleMLT'] == 3.0 *
                self.testInst['mlt']).all()

    @raises(ValueError)
    def test_add_function_tuple_return_style_too_few_elements(self):
        """Test if custom function works correctly. Add function that returns
        name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT', 2.0 * inst.data.mlt.values[0:-5])
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009, 1)
        if not self.testInst.pandas_format:
            print("Warning! Xarray doesn't enforce the same number of " +
                  "elements on all parameters in dataset.")
            raise ValueError

    @raises(ValueError)
    def test_add_function_tuple_return_style_too_many_elements(self):
        """Test if custom function works correctly. Add function that returns
        name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT', np.arange(2.0 * len(inst.data.mlt)))
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009, 1)
        if not self.testInst.pandas_format:
            print("Warning! Xarray doesn't enforce the same number of " +
                  "elements on all parameters in dataset.")
            raise ValueError

    def test_add_dataframe(self):
        def custom1(inst):
            out = pysat.DataFrame({'doubleMLT': inst.data.mlt * 2,
                                   'tripleMLT': inst.data.mlt * 3},
                                  index=inst.index)
            return out
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst.data['doubleMLT'] == 2.0 *
                self.testInst['mlt']).all()
        assert (self.testInst.data['tripleMLT'] == 3.0 *
                self.testInst['mlt']).all()

    def test_add_dataframe_w_meta(self):
        def custom1(inst):
            out = pysat.DataFrame({'doubleMLT': inst.data.mlt * 2,
                                   'tripleMLT': inst.data.mlt * 3},
                                  index=inst.index)
            return {'data': out,
                    'long_name': ['doubleMLTlong', 'tripleMLTlong'],
                    'units': ['hours1', 'hours2']}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert self.testInst.meta['tripleMLT'].units == 'hours2'
        assert self.testInst.meta['tripleMLT'].long_name == 'tripleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert (self.testInst['tripleMLT'] == 3.0 * self.testInst['mlt']).all()

    def test_add_series_w_meta(self):
        def custom1(inst):
            out = pysat.Series(inst.data.mlt * 2,
                               index=inst.index)
            out.name = 'doubleMLT'
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()

    def test_add_series_w_meta_missing_long_name(self):
        def custom1(inst):
            out = pysat.Series(2.0 * inst.data.mlt.values,
                               index=inst.index)
            out.name = 'doubleMLT'
            return {'data': out,
                    'units': 'hours1'}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLT'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()

    def test_add_series_w_meta_name_in_dict(self):
        def custom1(inst):
            out = pysat.Series(2.0 * inst.data.mlt.values,
                               index=inst.index)
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()

    @raises(ValueError)
    def test_add_series_w_meta_no_name(self):
        def custom1(inst):
            out = pysat.Series({'doubleMLT': inst.data.mlt * 2},
                               index=inst.index)
            # out.name = 'doubleMLT'
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)

    def test_add_numpy_array_w_meta_name_in_dict(self):
        def custom1(inst):
            out = 2.*inst['mlt'].values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()

    @raises(ValueError)
    def test_add_numpy_array_w_meta_no_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)

    def test_add_list_w_meta_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values.tolist()
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}
        self.add(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()

    @raises(ValueError)
    def test_add_list_w_meta_no_name_in_dict(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values.tolist()
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.load(2009, 1)

    def test_clear_functions(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.custom.clear()
        assert self.testInst.custom._functions == []
        assert self.testInst.custom._kind == []

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
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}
        self.testInst.custom.add(custom1, 'pass')
        self.testInst.load(2009, 1)

    @raises(AttributeError)
    def test_add_multiple_functions_one_not_at_end(self):
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        def custom2(inst):
            out = (inst.data.mlt * 3).values
            return {'data': out, 'long_name': 'tripleMLTlong',
                    'units': 'hours1', 'name': 'tripleMLT'}

        def custom3(inst):
            out = (inst.data.tripleMLT * 2).values
            return {'data': out, 'long_name': 'quadMLTlong',
                    'units': 'hours1', 'name': 'quadMLT'}
        self.testInst.custom.add(custom1, 'add')
        self.testInst.custom.add(custom2, 'add')
        # if this runs correctly, an error will be thrown
        # since the data required by custom3 won't be present yet
        self.testInst.custom.add(custom3, 'add', at_pos=1)
        self.testInst.load(2009, 1)


class TestBasicsXarray(TestBasics):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray', tag='10',
                                         clean_level='clean')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class ConstellationTestBasics(TestBasics):
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        insts = []
        for i in range(5):
            insts.append(pysat.Instrument('pysat', 'testing', tag='10',
                                          clean_level='clean'))

        self.testConst = pysat.Constellation(insts)

    def teardown(self):
        """ Runs after every method to clean up previous testing"""
        del self.testConst

    def add(self, function, kind='add', at_pos='end', *args, **kwargs):
        """ Add a function to the object's custom queue"""
        self.testConst.data_mod(function, kind, at_pos, *args, **kwargs)

class TestDeprecation():

    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always")

    def teardown(self):
        """Runs after every method to clean up previous testing"""

    def test_deprecation_warning_custom_add(self):
        """Test if custom.add is deprecated"""

        def func():
            """Fake function to attach"""
            print('Hi!')

        testInst = pysat.Instrument(platform='pysat', name='testing')
        with warnings.catch_warnings(record=True) as war:
            try:
                testInst.custom.add(func)
            except AttributeError:
                # Setting inst to None should produce a AttributeError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
