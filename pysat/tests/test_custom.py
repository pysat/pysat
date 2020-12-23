import copy
import datetime as dt
from io import StringIO
import logging
import numpy as np
import pandas as pds
import pytest
import xarray as xr

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

        self.testInst.custom_attach(lambda inst: inst.data['mlt'] * 2.0,
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
        self.load_date = dt.datetime(2009, 1, 1)
        self.testInst.load(date=self.load_date)
        self.ncols = len(self.testInst.data.columns)
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing.
        """
        del self.testInst, self.ncols, self.out

    def test_basic_str(self):
        """Check for lines from each decision point in str"""
        self.out = self.testInst.__str__()
        assert isinstance(self.out, str)
        # No custom functions
        assert self.out.find('0 applied') > 0

    def test_basic_str_w_function(self):
        """Check for lines from each decision point in str"""
        def mult_data(inst, mult, dkey="mlt"):
            out_key = '{:.0f}x{:s}'.format(mult, dkey)
            inst.data[out_key] = mult * inst.data[dkey]
            return

        self.testInst.custom_attach(mult_data, 'modify', args=[2.0],
                                    kwargs={"dkey": "mlt"})
        # Execute custom method
        self.testInst.load(date=self.load_date)
        # Store output to be tested
        self.out = self.testInst.__str__()
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

        self.testInst.custom_attach(custom1, 'modify')
        with pytest.raises(ValueError):
            self.testInst.load(date=self.load_date)

    def test_single_adding_custom_function(self):
        """Test successful use of custom function loaded as add
        """
        def custom1(inst):
            d = 2.0 * inst['mlt']
            d.name = 'doubleMLT'
            return d

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
        assert (self.testInst['doubleMLT'].isnull()).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_single_adding_custom_function_that_modifies_passed_data(self):
        """Ensure in-function instrument modifications don't propagate with add
        """
        def custom1(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            inst['mlt'] = 0.
            return inst.data.doubleMLT

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
        assert (self.testInst.data['doubleMLT'] == 2.0
                * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_custom_keyword_instantiation(self):
        """Test adding custom methods at Instrument instantiation
        """
        def custom_add(inst, arg1, arg2, kwarg1=False, kwarg2=True):
            return

        def custom_modify(inst, arg1, arg2, kwarg1=False, kwarg2=True):
            return

        self.testInst.custom_attach(custom_add, 'add', args=[0, 1],
                                    kwargs={'kwarg1': True, 'kwarg2': False})
        self.testInst.custom_attach(custom_modify, 'modify', args=[5, 10],
                                    kwargs={'kwarg1': True, 'kwarg2': True})
        self.testInst.custom_attach(custom_modify, 'modify')

        # create another instance of pysat.Instrument and add custom
        # via the input keyword
        custom = [{'function': custom_add, 'kind': 'add', 'args': [0, 1],
                   'kwargs': {'kwarg1': True, 'kwarg2': False}},
                  {'function': custom_modify, 'kind': 'modify', 'args': [5, 10],
                   'kwargs': {'kwarg1': True, 'kwarg2': True}},
                  {'function': custom_modify, 'kind': 'modify'}
                  ]
        testInst2 = pysat.Instrument('pysat', 'testing', custom=custom)

        # ensure both instruments have the same custom_* attributes
        assert self.testInst.custom_functions == testInst2.custom_functions
        assert self.testInst.custom_kind == testInst2.custom_kind
        assert self.testInst.custom_args == testInst2.custom_args
        assert self.testInst.custom_kwargs == testInst2.custom_kwargs

    def test_custom_keyword_instantiation_poor_format(self):
        """Test for error when custom missing keywords at instantiation
        """
        req_words = ['function', 'kind']
        real_custom = [{'function': 1, 'kind': 'add', 'args': [0, 1],
                        'kwargs': {'kwarg1': True, 'kwarg2': False}}]
        for i, word in enumerate(req_words):
            custom = copy.deepcopy(real_custom)
            custom[0].pop(word)

            # Ensure that any of the missing required words raises an error
            with pytest.raises(ValueError) as err:
                pysat.Instrument('pysat', 'testing', custom=custom)

            # ensure correct error for the missing parameter (word)
            assert str(err).find(word) >= 0
            assert str(err).find('Input dict to custom is missing') >= 0

        return

    def test_add_function_tuple_return_style(self):
        """Test success of add function that returns name and numpy array.
        """
        def custom1(inst):
            return ('doubleMLT', 2.0 * inst.data.mlt.values)

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_multiple_custom_functions_tuple_return_style(self):
        """Test success of add function with multiple name/array pairs
        """
        def custom1(inst):
            return (['doubleMLT', 'tripleMLT'], [2.0 * inst.data.mlt.values,
                                                 3.0 * inst.data.mlt.values])
        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(date=self.load_date)

    def test_add_function_tuple_return_style_too_many_elements(self):
        """Test failure of add function that too many array elements
        """
        if not self.testInst.pandas_format:
            pytest.skip('pandas specific test for time index')

        def custom1(inst):
            return ('doubleMLT', np.arange(2.0 * len(inst.data.mlt)))

        self.testInst.custom_attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(date=self.load_date)

    def test_add_dataframe(self):
        """Test add function success with pandas DataFrame return
        """
        def custom1(inst):
            out = pds.DataFrame({'doubleMLT': inst.data.mlt * 2,
                                 'tripleMLT': inst.data.mlt * 3},
                                index=inst.index)
            return out

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
        assert self.testInst.meta['doubleMLT'].units == 'hours1'
        assert self.testInst.meta['doubleMLT'].long_name == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_series_w_meta_no_name_error(self):
        """Test add function failure with Series and required MetaData missing
        """
        def custom1(inst):
            out = pds.Series({'doubleMLT': inst.data.mlt * 2}, index=inst.index)
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1'}

        self.testInst.custom_attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(date=self.load_date)

    def test_add_xarray_dataarray(self):
        """Test add function success with xarray"""
        def custom1(inst):
            out = xr.DataArray(inst.data.mlt * 2, dims=['time'],
                               coords=[inst.index])
            out.name = 'doubleMLT'
            return {'data': out, inst.meta.labels.name: 'doubleMLTlong',
                    inst.meta.labels.units: 'hours1'}

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
        units = self.testInst.meta.labels.units
        lname = self.testInst.meta.labels.name
        assert self.testInst.meta['doubleMLT', units] == 'hours1'
        assert self.testInst.meta['doubleMLT', lname] == 'doubleMLTlong'
        assert (self.testInst['doubleMLT'] == 2.0 * self.testInst['mlt']).all()
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols + 1

    def test_add_xarray_dataset(self):
        """Test add function success with xarray"""
        def custom_set(inst):
            out1 = xr.DataArray(inst.data.mlt * 2, dims=['time'],
                                coords=[inst.index])
            out1.name = 'doubleMLT'

            out2 = xr.DataArray(inst.data.mlt * 3, dims=['time'],
                                coords=[inst.index])
            out2.name = 'tripleMLT'

            out = xr.Dataset({'doubleMLT': out1, 'tripleMLT': out2})

            return {'data': out, inst.meta.labels.name: ['doubleMLTlong',
                                                         'tripleMLTyo'],
                    inst.meta.labels.units: ['hours1', 'hours2']}

        if not self.testInst.pandas_format:
            self.testInst.custom_attach(custom_set, 'add')
            self.testInst.load(date=self.load_date)
            units = self.testInst.meta.labels.units
            lname = self.testInst.meta.labels.name
            assert self.testInst.meta['doubleMLT', units] == 'hours1'
            assert self.testInst.meta['tripleMLT', units] == 'hours2'
            assert self.testInst.meta['doubleMLT', lname] == 'doubleMLTlong'
            assert self.testInst.meta['tripleMLT', lname] == 'tripleMLTyo'
            assert (self.testInst['doubleMLT']
                    == 2.0 * self.testInst['mlt']).all()
            assert (self.testInst['tripleMLT']
                    == 3.0 * self.testInst['mlt']).all()
            tlen = self.ncols + 2
            assert len([kk for kk in self.testInst.data.keys()]) == tlen

    def test_add_numpy_array_w_meta_name_in_dict(self):
        """Test add function success with array and MetaData
        """
        def custom1(inst):
            out = 2. * inst['mlt'].values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(date=self.load_date)

    def test_add_list_w_meta_name_in_dict(self):
        """Test add function success with list and full MetaData
        """
        def custom1(inst):
            out = (inst.data.mlt * 2).values.tolist()
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        self.testInst.custom_attach(custom1, 'add')
        self.testInst.load(date=self.load_date)
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

        self.testInst.custom_attach(custom1, 'add')
        with pytest.raises(ValueError):
            self.testInst.load(date=self.load_date)

    def test_clear_functions(self):
        """Test successful clearance of custom functions
        """
        self.testInst.custom_attach(lambda inst, imult, out_units='h':
                                    {'data': (inst.data.mlt * imult).values,
                                     'long_name': 'doubleMLTlong',
                                     'units': out_units, 'name': 'doubleMLT'},
                                    'add', args=[2],
                                    kwargs={"out_units": "hours1"})

        # Test to see that the custom function was attached
        assert len(self.testInst.custom_functions) == 1
        assert len(self.testInst.custom_kind) == 1
        assert len(self.testInst.custom_args) == 1
        assert len(self.testInst.custom_kwargs) == 1

        self.testInst.custom_clear()
        # Test to see that the custom function was cleared
        assert self.testInst.custom_functions == []
        assert self.testInst.custom_kind == []
        assert self.testInst.custom_args == []
        assert self.testInst.custom_kwargs == []

    def test_pass_functions(self):
        """ Test success of pass function, will not modify or add to instrument
        """
        def custom1(inst):
            _ = (inst.data.mlt * 2).values
            return

        self.testInst.custom_attach(custom1, 'pass')
        # Test to see that the custom function was attached
        assert len(self.testInst.custom_functions) == 1
        assert len(self.testInst.custom_kind) == 1
        assert len(self.testInst.custom_args) == 1
        assert len(self.testInst.custom_kwargs) == 1

        self.testInst.load(date=self.load_date)
        # Test that the number of data columns is the same
        assert len([kk for kk in self.testInst.data.keys()]) == self.ncols

    def test_pass_functions_no_return_allowed_error(self):
        """Test error when a pass function returns a value
        """
        def custom1(inst):
            out = (inst.data.mlt * 2).values
            return {'data': out, 'long_name': 'doubleMLTlong',
                    'units': 'hours1', 'name': 'doubleMLT'}

        self.testInst.custom_attach(custom1, 'pass')
        with pytest.raises(ValueError):
            self.testInst.load(date=self.load_date)

    def test_add_multiple_functions_one_not_at_end(self):
        """Test for error if custom functions are run in the wrong order
        """
        def custom1(inst, imult):
            out = (inst.data.mlt * imult).values
            return {'data': out, 'long_name': 'MLT x {:d}'.format(int(imult)),
                    'units': 'hours', 'name': 'MLTx{:d}'.format(int(imult))}

        self.testInst.custom_attach(custom1, 'add', args=[4])
        self.testInst.custom_attach(custom1, 'add', args=[2])
        self.testInst.custom_attach(lambda inst, imult:
                                    {'data': (inst.data.MLTx2 * imult).values,
                                     'long_name': 'MLT x {:d}'.format(imult),
                                     'units': 'h',
                                     'name': 'MLTx{:d}'.format(imult)},
                                    'add', args=[2], at_pos=1)

        # An AttributeError should be thrown, since the data required by the
        # last attached function (inst.data.MLTx2) won't be present yet

        with pytest.raises(AttributeError):
            self.testInst.load(date=self.load_date)


# Repeate the above tests with xarray
class TestBasicsXarray(TestBasics):
    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         num_samples=10, clean_level='clean')
        self.load_date = dt.datetime(2009, 1, 1)
        self.testInst.load(date=self.load_date)
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

    def test_add(self, function, kind='add', at_pos='end', args=[], kwargs={}):
        """ Add a function to the object's custom queue
        """
        self.testConst.custom_attach(function, kind, at_pos, args, kwargs)
