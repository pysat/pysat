"""Unit tests for the `custom_attach` methods for `pysat.Instrument`."""

import copy
import logging
import pytest

import pysat
from pysat.utils import testing


def mult_data(inst, mult, dkey="mlt"):
    """Add a multiplied data value to an Instrument.

    Parameters
    ----------
    inst : pysat.Instrument
        pysat Instrument object
    mult : float or int
        Multiplicative value
    dkey : str
        Key for data that will be multiplied (default='mlt')

    Note
    ----
    Adds multiplied data to Instrument using a key name with the format
    {mult}x{dkey}

    """
    # Construct the new data key
    out_key = '{:.0f}x{:s}'.format(mult, dkey)

    # Add the new data to the instrument
    inst.data[out_key] = mult * inst.data[dkey]

    return


class TestLogging(object):
    """Unit tests for logging interface with custom functions."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=10,
                                         clean_level='clean',
                                         update_files=False, use_header=True)
        self.out = ''
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out
        return

    def test_custom_pos_warning(self, caplog):
        """Test for logging warning if inappropriate position specified."""

        with caplog.at_level(logging.WARNING, logger='pysat'):
            self.testInst.custom_attach(lambda inst: inst.data['mlt'] * 2.0,
                                        at_pos=3)
        self.out = caplog.text

        assert self.out.find(
            "unknown position specified, including function at end") >= 0
        return


class TestBasics(object):
    """Unit tests for `pysat.instrument.custom_attach` with pandas data."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         use_header=True)
        self.load_date = pysat.instruments.pysat_testing._test_dates['']['']
        self.testInst.load(date=self.load_date)
        self.custom_args = [2]
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.custom_args
        return

    def test_basic_str(self):
        """Check for lines from each decision point in str."""

        self.out = self.testInst.__str__()
        assert isinstance(self.out, str)

        # No custom functions
        assert self.out.find('0 applied') > 0
        return

    def test_basic_repr(self):
        """Test `__repr__` with a custom method."""

        self.testInst.custom_attach(mult_data, args=self.custom_args)
        self.testInst.custom_attach(mult_data, args=self.custom_args)
        self.out = self.testInst.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("'function'") >= 0
        return

    def test_basic_str_w_function(self):
        """Check for lines from each decision point in str."""

        self.testInst.custom_attach(mult_data, args=self.custom_args,
                                    kwargs={'dkey': 'mlt'})

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
        return

    def test_single_custom_function_error(self):
        """Test for error if custom function returns a value."""

        def custom_with_return_data(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            return 5.0 * inst.data['mlt']

        estr = 'Custom functions should not return any information via return'
        self.testInst.custom_attach(custom_with_return_data)

        testing.eval_bad_input(self.testInst.load, ValueError, estr,
                               input_kwargs={'date': self.load_date})
        return

    def test_custom_keyword_instantiation(self):
        """Test adding custom methods at Instrument instantiation."""

        self.testInst.custom_attach(mult_data, args=self.custom_args,
                                    kwargs={'dkey': 'mlt'})
        self.testInst.custom_attach(mult_data, args=self.custom_args)

        # Create another instance of pysat.Instrument and add custom
        # via the input keyword
        custom = [{'function': mult_data, 'args': self.custom_args,
                   'kwargs': {'dkey': 'mlt'}},
                  {'function': mult_data, 'args': self.custom_args}]
        testInst2 = pysat.Instrument('pysat', 'testing', custom=custom)

        # Ensure both instruments have the same custom_* attributes
        assert self.testInst.custom_functions == testInst2.custom_functions
        assert self.testInst.custom_args == testInst2.custom_args
        assert self.testInst.custom_kwargs == testInst2.custom_kwargs
        return

    def test_custom_positioning(self):
        """Test custom method ordering specification."""

        self.testInst.custom_attach(mult_data, args=[3],
                                    kwargs={'dkey': '2xmlt'})
        self.testInst.custom_attach(mult_data, at_pos=0, args=self.custom_args)

        # Create another instance of pysat.Instrument and add custom
        # via the input keyword
        custom = [{'function': mult_data, 'args': [3],
                   'kwargs': {'dkey': '2xmlt'}},
                  {'function': mult_data, 'at_pos': 0,
                   'args': self.custom_args}]
        testInst2 = pysat.Instrument('pysat', 'testing', custom=custom)

        # Ensure both Instruments have the same custom_* attributes
        assert self.testInst.custom_functions == testInst2.custom_functions
        assert self.testInst.custom_args == testInst2.custom_args
        assert self.testInst.custom_kwargs == testInst2.custom_kwargs

        # Ensure the run order was correct
        assert self.testInst.custom_args[0] == self.custom_args
        assert self.testInst.custom_args[1] == [3]
        return

    def test_custom_keyword_instantiation_poor_format(self):
        """Test for error when custom missing keywords at instantiation."""

        req_words = ['function']
        real_custom = [{'function': 1, 'args': [0, 1],
                        'kwargs': {'kwarg1': True, 'kwarg2': False}}]
        for i, word in enumerate(req_words):
            custom = copy.deepcopy(real_custom)
            custom[0].pop(word)

            # Ensure that any of the missing required words raises an error
            with pytest.raises(ValueError) as err:
                pysat.Instrument('pysat', 'testing', custom=custom)

            # Ensure correct error for the missing parameter (word)
            assert str(err).find(word) >= 0
            assert str(err).find('Input dict to custom is missing') >= 0

        return

    def test_clear_functions(self):
        """Test successful clearance of custom functions."""

        self.testInst.custom_attach(lambda inst, imult, out_units='h':
                                    {'data': (inst.data.mlt * imult).values,
                                     'long_name': 'doubleMLTlong',
                                     'units': out_units, 'name': 'doubleMLT'},
                                    args=[2], kwargs={"out_units": "hours1"})

        # Test to see that the custom function was attached
        assert len(self.testInst.custom_functions) == 1
        assert len(self.testInst.custom_args) == 1
        assert len(self.testInst.custom_kwargs) == 1

        self.testInst.custom_clear()
        # Test to see that the custom function was cleared
        assert self.testInst.custom_functions == []
        assert self.testInst.custom_args == []
        assert self.testInst.custom_kwargs == []
        return


class TestBasicsXarray(TestBasics):
    """Unit tests for `pysat.instrument.custom_attach` with an xarray inst."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         num_samples=10, clean_level='clean',
                                         use_header=True)
        self.load_date = pysat.instruments.pysat_testing_xarray._test_dates
        self.load_date = self.load_date['']['']
        self.testInst.load(date=self.load_date)
        self.custom_args = [2]
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.load_date, self.custom_args
        return


class TestConstellationBasics(object):
    """Unit tests for `pysat.instrument.custom_attach` with a constellation."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testConst = pysat.Constellation(instruments=[
            pysat.Instrument('pysat', 'testing', num_samples=10,
                             clean_level='clean', update_files=True,
                             use_header=True)
            for i in range(5)])
        self.load_date = pysat.instruments.pysat_testing._test_dates['']['']
        self.testConst.load(date=self.load_date)
        self.custom_args = [2]
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testConst, self.load_date, self.custom_args
        return

    @pytest.mark.parametrize("apply_inst", [False, True])
    def test_bad_set_custom(self, apply_inst):
        """Test ValueError raised when not setting custom functions correctly.

        Parameters
        ----------
        apply_inst : bool
            Apply custom function at Instrument level (True) or Constellation
            level (False)

        """

        inst = pysat.Instrument('pysat', 'testing', num_samples=10,
                                clean_level='clean')

        testing.eval_bad_input(pysat.Constellation, ValueError,
                               "Input dict to custom is missing the",
                               input_kwargs={
                                   'custom': [{'apply_inst': apply_inst}],
                                   'instruments': [inst for i in range(5)]})
        return

    @pytest.mark.parametrize("apply_inst", [False, True])
    def test_repr(self, apply_inst):
        """Test `__repr__` with custom method.

        Parameters
        ----------
        apply_inst : bool
            Apply custom function at Instrument level (True) or Constellation
            level (False)

        """

        self.testConst.custom_attach(mult_data, apply_inst=apply_inst,
                                     args=self.custom_args)
        self.out = repr(self.testConst)
        assert isinstance(self.out, str)
        assert self.out.find("custom=[{'function'") >= 0
        return

    @pytest.mark.parametrize("apply_inst, num_func", [(False, 1), (True, 0)])
    def test_str(self, apply_inst, num_func):
        """Test `__str__` with Constellation-level custom methods.

        Parameters
        ----------
        apply_inst : bool
            Apply custom function at Instrument level (True) or Constellation
            level (False)
        num_func : int
            Number of constellation-level functions applied

        """

        self.testConst.custom_attach(mult_data, apply_inst=apply_inst,
                                     args=self.custom_args,
                                     kwargs={'dkey': 'mlt'})
        self.out = self.testConst.__str__()
        assert isinstance(self.out, str)
        assert self.out.find("Constellation-level Data Processing") >= 0
        assert self.out.find(
            "Custom Functions: {:d} applied".format(num_func)) >= 0

        if num_func > 0:
            assert self.out.find("Args=") >= 0
            assert self.out.find("Kwargs=") >= 0
        return

    def test_single_custom_function_error(self):
        """Test for error when custom function returns a value."""

        def custom_with_return_data(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            return 5.0 * inst.data['mlt']

        self.testConst.custom_attach(custom_with_return_data)

        # Evaluate the error raised and its message
        estr = 'Custom functions should not return any information via return'
        testing.eval_bad_input(self.testConst.load, ValueError, estr,
                               input_kwargs={'date': self.load_date})
        return

    def test_custom_inst_keyword_instantiation(self):
        """Test adding Instrument-level custom methods at instantiation."""

        self.testConst.custom_attach(mult_data, args=self.custom_args,
                                     kwargs={'dkey': 'mlt'})
        self.testConst.custom_attach(mult_data, args=self.custom_args)

        # Create another instance of pysat.Instrument and add custom
        # via the input keyword
        custom = [{'function': mult_data, 'args': self.custom_args,
                   'kwargs': {'dkey': 'mlt'}},
                  {'function': mult_data, 'args': self.custom_args}]
        testConst2 = pysat.Constellation(instruments=[
            pysat.Instrument('pysat', 'testing', num_samples=10,
                             clean_level='clean', custom=custom,
                             use_header=True)
            for i in range(5)])

        # Ensure all instruments within both constellations have the same
        # custom_* attributes
        for i, inst in enumerate(self.testConst.instruments):
            inst2 = testConst2.instruments[i]
            assert inst.custom_functions == inst2.custom_functions
            assert inst.custom_args == inst2.custom_args
            assert inst.custom_kwargs == inst2.custom_kwargs
        return

    def test_custom_const_keyword_instantiation(self):
        """Test adding Constallation-level custom methods at instantiation."""

        self.testConst.custom_attach(mult_data, args=self.custom_args,
                                     kwargs={'dkey': 'mlt'}, apply_inst=False)
        self.testConst.custom_attach(mult_data, args=self.custom_args,
                                     apply_inst=False)

        # Create another instance of pysat.Instrument and add custom
        # via the input keyword
        custom = [{'function': mult_data, 'args': self.custom_args,
                   'kwargs': {'dkey': 'mlt'}, 'apply_inst': False},
                  {'function': mult_data, 'args': self.custom_args,
                   'apply_inst': False}]
        testConst2 = pysat.Constellation(
            instruments=[pysat.Instrument('pysat', 'testing', num_samples=10,
                                          clean_level='clean', use_header=True)
                         for i in range(5)], custom=custom)

        # Ensure both constellations have the same custom_* attributes
        assert self.testConst.custom_functions == testConst2.custom_functions
        assert self.testConst.custom_args == testConst2.custom_args
        assert self.testConst.custom_kwargs == testConst2.custom_kwargs
        return

    @pytest.mark.parametrize("apply_inst", [False, True])
    def test_clear_functions(self, apply_inst):
        """Test successful clearance of custom functions.

        Parameters
        ----------
        apply_inst : bool
            Apply custom function at Instrument level (True) or Constellation
            level (False)

        """

        self.testConst.custom_attach(lambda inst, imult, out_units='h':
                                     {'data': (inst.data.mlt * imult).values,
                                      'long_name': 'doubleMLTlong',
                                      'units': out_units, 'name': 'doubleMLT'},
                                     args=[2], kwargs={"out_units": "hours1"},
                                     apply_inst=apply_inst)

        inst_num = 1 if apply_inst else 0
        const_num = 0 if apply_inst else 1

        # Test to see that the custom function was attached to each Instrument
        assert len(self.testConst.custom_functions) == const_num
        assert len(self.testConst.custom_args) == const_num
        assert len(self.testConst.custom_kwargs) == const_num

        for inst in self.testConst.instruments:
            assert len(inst.custom_functions) == inst_num
            assert len(inst.custom_args) == inst_num
            assert len(inst.custom_kwargs) == inst_num

        # Test to see that the custom function was cleared
        self.testConst.custom_clear()
        assert self.testConst.custom_functions == []
        assert self.testConst.custom_args == []
        assert self.testConst.custom_kwargs == []

        for inst in self.testConst.instruments:
            assert inst.custom_functions == []
            assert inst.custom_args == []
            assert inst.custom_kwargs == []
        return
