import datetime as dt
from io import StringIO
import logging
import numpy as np
import pandas as pds
import pytest

import pysat


class TestLogging():
    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=10,
                                         clean_level='clean')
        self.out = ''
        self.log_capture = StringIO()
        pysat.logger.addHandler(logging.StreamHandler(self.log_capture))
        pysat.logger.setLevel(logging.WARNING)

    def teardown(self):
        """Runs after every method to clean up previous testing.
        """
        del self.testInst, self.out, self.log_capture

    def test_custom_pos_warning(self):
        """Test for logging warning if inappropriate position specified
        """

        self.testInst.custom.attach(lambda inst: inst.data['mlt'] * 2.0,
                                    'add', at_pos=3)
        self.out = self.log_capture.getvalue()

        assert self.out.find(
            "unknown position specified, including function at end") >= 0


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=10,
                                         clean_level='clean')
        self.testInst.load(2008, 1)
        self.ncols = len(self.testInst.data.columns)
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing.
        """
        del self.testInst, self.ncols, self.out

    def test_basic_repr(self):
        """The repr output will match the str output"""
        self.out = self.testInst.custom.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("functions applied") > 0

    def test_basic_str(self):
        """Check for lines from each decision point in str"""
        self.out = self.testInst.custom.__str__()
        assert isinstance(self.out, str)
        # No custom functions
        assert self.out.find('0 applied') > 0

    def test_basic_str_w_function(self):
        """Check for lines from each decision point in str"""
        def mult_data(inst, mult, dkey="mlt"):
            out_key = '{:.0f}x{:s}'.format(mult, dkey)
            inst.data[out_key] = mult * inst.data[dkey]
            return

        self.testInst.custom.attach(mult_data, 'modify', args=[2.0],
                                    kwargs={"dkey": "mlt"})
        self.out = self.testInst.custom.__str__()
        assert isinstance(self.out, str)
        # No custom functions
        assert self.out.find('1 applied') > 0
        assert self.out.find('mult_data') > 0
        assert self.out.find('Args') > 0
        assert self.out.find('Kwargs') > 0

    def test_single_modifying_custom_function_error(self):
        """Test for error when custom function loaded as modify returns a value
        """
        def custom1(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            return 5.0 * inst.data['mlt']

        self.testInst.custom.attach(custom1, 'modify')
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)

    def test_single_adding_custom_function(self):
        """Test successful use of custom function loaded as add
        """
        def custom1(inst):
            d = 2.0 * inst['mlt']
            d.name = 'doubleMLT'
            return d

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst['doubleMLT'].values == 2.0
                * self.testInst['mlt'].values).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_single_adding_custom_function_wrong_times(self):
        """Test index alignment with add type custom function
        """
        if not self.testInst.pandas_format:
            pytest.skip('pandas specific test for time index')

        def custom1(inst):
            new_index = inst.index + dt.timedelta(milliseconds=500)
            d = pds.Series(2.0 * inst['mlt'], index=new_index)
            d.name = 'doubleMLT'
            return d

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst['doubleMLT'].isnull()).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_single_adding_custom_function_that_modifies_passed_data(self):
        """Ensure in-function instrument modifications don't propagate with add
        """
        def custom1(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            inst['mlt'] = 0.
            return inst.data.doubleMLT

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst.data['doubleMLT'] == 2.0
                * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_function_tuple_return_style(self):
        """Test success of add function that returns name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT', 2.0 * inst.data.mlt.values)

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_multiple_custom_functions_tuple_return_style(self):
        """Test success of add function with multiple name/array pairs
        """
        def custom1(inst):
            return (['doubleMLT', 'tripleMLT'], [2.0 * inst.data.mlt.values,
                                                 3.0 * inst.data.mlt.values])
        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst.data['doubleMLT'] == 2.0
                * self.testInst['mlt']).all()
        assert (self.testInst.data['tripleMLT'] == 3.0
                * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 2

    def test_add_function_tuple_return_style_too_few_elements(self):
        """Test failure of add function that too few array elements
        """
        if not self.testInst.pandas_format:
            pytest.skip('pandas specific test for time index')

        def custom1(inst):
            return ('doubleMLT', 2.0 * inst.data.mlt.values[0:-5])

        self.testInst.custom.attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)

    def test_add_function_tuple_return_style_too_many_elements(self):
        """Test failure of add function that too many array elements
        """
        if not self.testInst.pandas_format:
            pytest.skip('pandas specific test for time index')

        def custom1(inst):
            return ('doubleMLT', np.arange(2.0 * len(inst.data.mlt)))

        self.testInst.custom.attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)

    def test_add_dataframe(self):
        """Test add function success with pandas DataFrame return
        """
        def custom1(inst):
            out = pds.DataFrame({'doubleMLT': inst.data.mlt * 2,
                                 'tripleMLT': inst.data.mlt * 3},
                                index=inst.index)
            return out

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert (self.testInst.data['doubleMLT'] == 2.0
                * self.testInst['mlt']).all()
        assert (self.testInst.data['tripleMLT'] == 3.0
                * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 2

    def test_add_dataframe_w_meta(self):
        """Test add function success with pandas DataFrame and MetaData return
        """
        def custom1(inst):
            out = pds.DataFrame({'doubleMLT': inst.data.mlt * 2,
                                 'tripleMLT': inst.data.mlt * 3},
                                index=inst.index)
            return {'data': out,
                    'long_name': ['doubleMLTlong', 'tripleMLTlong'],
                    'units': ['hours1', 'hours2']}

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert self.testInst.meta['tripleMLT'].units == 'hours2'
        assert self.testInst.meta['tripleMLT'].long_name == 'tripleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert (self.testInst['tripleMLT'] == 3.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 2

    def test_add_series_w_meta(self):
        """Test add function success with pandas Series return
        """
        def custom1(inst):
            out = pds.Series(inst.data.mlt * 2, index=inst.index)
            out.name = 'doubleMLT'
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_series_w_meta_missing_long_name(self):
        """Test add function success with Series and allowable partial MetaData
        """
        def custom1(inst):
            out = pds.Series(2.0 * inst.data.mlt.values, index=inst.index)
            out.name = 'doubleMLT'
            return {'data': out, 'units': 'hours1'}

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT', 'units'] == 'hours1'
        assert self.testInst.meta['doubleMLT', 'long_name'] == 'doubleMLT'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_series_w_meta_name_in_dict(self):
        """Test add function success with pandas Series and MetaData return
        """
        def custom1(inst):
            out = pds.Series(2.0 * inst.data.mlt.values, index=inst.index)
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_series_w_meta_no_name_error(self):
        """Test add function failure with Series and required MetaData missing
        """
        def custom1(inst):
            out = pds.Series({'doubleMLT': inst.data.mlt * 2}, index=inst.index)
            # out.name = 'doubleMLT'
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}

        self.testInst.custom.attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)

    def test_add_numpy_array_w_meta_name_in_dict(self):
        """Test add function success with array and MetaData
        """
        def custom1(inst):
            out = 2. * inst['mlt'].values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_numpy_array_w_meta_no_name_in_dict_error(self):
        """Test add function failure with array and required MetaData missing
        """
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}

        self.testInst.custom.attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)

    def test_add_list_w_meta_name_in_dict(self):
        """Test add function success with list and full MetaData
        """
        def custom1(inst):
            out = (inst.data.mlt * 2).values.tolist()
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        self.testInst.custom.attach(custom1, 'add')
        self.testInst.load(2009, 1)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_list_w_meta_no_name_in_dict_error(self):
        """Test add function failure with list and required MetaData missing
        """
        def custom1(inst):
            out = (inst.data.mlt * 2).values.tolist()
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}

        self.testInst.custom.attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)

    def test_clear_functions(self):
        """Test successful clearance of custom functions
        """
        self.testInst.custom.attach(lambda inst, imult, out_units='h':
                                    {'data': (inst.data.mlt * imult).values,
                                     'long_name': 'doubleMLTlong',
                                     'units': out_units, 'name': 'doubleMLT'},
                                    'add', args=[2],
                                    kwargs={"out_units": "hours1"})

        # Test to see that the custom function was attached
        assert len(self.testInst.custom._functions) == 1
        assert len(self.testInst.custom._kind) == 1
        assert len(self.testInst.custom._args) == 1
        assert len(self.testInst.custom._kwargs) == 1

        self.testInst.custom.clear()
        # Test to see that the custom function was cleared
        assert self.testInst.custom._functions == []
        assert self.testInst.custom._kind == []
        assert self.testInst.custom._args == []
        assert self.testInst.custom._kwargs == []

    def test_pass_functions(self):
        """ Test success of pass function, will not modify or add to instrument
        """
        def custom1(inst):
            _ = (inst.data.mlt * 2).values
            return

        self.testInst.custom.attach(custom1, 'pass')
        # Test to see that the custom function was attached
        assert len(self.testInst.custom._functions) == 1
        assert len(self.testInst.custom._kind) == 1
        assert len(self.testInst.custom._args) == 1
        assert len(self.testInst.custom._kwargs) == 1

        self.testInst.load(2009, 1)
        # Test that the number of data columns is the same
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols

    def test_pass_functions_no_return_allowed_error(self):
        """Test error when a pass function returns a value
        """
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        self.testInst.custom.attach(custom1, 'pass')
        with pytest.raises(ValueError):
            self.testInst.load(2009, 1)

    def test_add_multiple_functions_one_not_at_end(self):
        """Test for error if custom functions are run in the wrong order
        """
        def custom1(inst, imult):
            out = (inst.data.mlt * imult).values
            return {'data': out, 'long_name': 'MLT x {:d}'.format(int(imult)),
                    'units': 'hours', 'name': 'MLTx{:d}'.format(int(imult))}

        self.testInst.custom.attach(custom1, 'add', args=[4])
        self.testInst.custom.attach(custom1, 'add', args=[2])
        self.testInst.custom.attach(lambda inst, imult:
                                    {'data': (inst.data.MLTx2 * imult).values,
                                     'long_name': 'MLT x {:d}'.format(imult),
                                     'units': 'h',
                                     'name': 'MLTx{:d}'.format(imult)},
                                    'add', args=[2], at_pos=1)

        # An AttributeError should be thrown, since the data required by the
        # last attached function (inst.data.MLTx2) won't be present yet

        with pytest.raises(AttributeError):
            self.testInst.load(2009, 1)


# Repeate the above tests with xarray
class TestBasicsXarray(TestBasics):
    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         num_samples=10, clean_level='clean')
        self.testInst.load(2008, 1)
        self.ncols = len([kk for kk in self.testInst.data.keys()])

    def teardown(self):
        """Runs after every method to clean up previous testing.
        """
        del self.testInst


# Repeat the above tests with a Constellation
class ConstellationTestBasics(TestBasics):
    def setup(self):
        """Runs before every method to create a clean testing setup
        """
        self.testConst = pysat.Constellation([
            pysat.Instrument('pysat', 'testing', num_samples=10,
                             clean_level='clean')
            for i in range(5)])

    def teardown(self):
        """ Runs after every method to clean up previous testing
        """
        del self.testConst

    def add(self, function, kind='add', at_pos='end', args=[], kwargs={}):
        """ Add a function to the object's custom queue
        """
        self.testConst.data_mod(function, kind, at_pos, args, kwargs)
