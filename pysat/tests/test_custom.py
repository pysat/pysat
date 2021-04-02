import copy
from io import StringIO
import logging
import pytest

import pysat


def mult_data(inst, mult, dkey="mlt"):
    """Function to add a multiplied data value to an Instrument

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


class TestLogging():
    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=10,
                                         clean_level='clean',
                                         update_files=False)
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
                                    at_pos=3)
        self.out = self.log_capture.getvalue()

        assert self.out.find(
            "unknown position specified, including function at end") >= 0


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.testInst = pysat.Instrument('pysat', 'testing', num_samples=10,
                                         clean_level='clean',
                                         update_files=True)
        self.load_date = pysat.instruments.pysat_testing._test_dates['']['']
        self.testInst.load(date=self.load_date)
        self.custom_args = [2]
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing.
        """
        del self.testInst, self.out, self.custom_args

    def test_basic_str(self):
        """Check for lines from each decision point in str"""
        self.out = self.testInst.__str__()
        assert isinstance(self.out, str)

        # No custom functions
        assert self.out.find('0 applied') > 0

    def test_basic_repr(self):
        """Test __repr__ with a custom method"""

        self.testInst.custom_attach(mult_data, args=self.custom_args)
        self.testInst.custom_attach(mult_data, args=self.custom_args)
        self.out = self.testInst.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("'function'") >= 0

    def test_basic_str_w_function(self):
        """Check for lines from each decision point in str"""

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

    def test_single_modifying_custom_function_error(self):
        """Test for error when custom function loaded as modify returns a value
        """
        def custom_with_return_data(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            return 5.0 * inst.data['mlt']

        self.testInst.custom_attach(custom_with_return_data)
        with pytest.raises(ValueError) as verr:
            self.testInst.load(date=self.load_date)

        estr = 'Custom functions should not return any information via return'
        assert str(verr).find(estr) >= 0

    def test_custom_keyword_instantiation(self):
        """Test adding custom methods at Instrument instantiation
        """

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

    def test_custom_positioning(self):
        """Test custom method ordering specification
        """

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

    def test_custom_keyword_instantiation_poor_format(self):
        """Test for error when custom missing keywords at instantiation
        """
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
        """Test successful clearance of custom functions
        """
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


# Repeat the above tests with xarray
class TestBasicsXarray(TestBasics):
    def setup(self):
        """Runs before every method to create a clean testing setup.
        """
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         num_samples=10, clean_level='clean')
        self.load_date = pysat.instruments.pysat_testing_xarray._test_dates
        self.load_date = self.load_date['']['']
        self.testInst.load(date=self.load_date)
        self.custom_args = [2]

    def teardown(self):
        """Runs after every method to clean up previous testing.
        """
        del self.testInst, self.load_date, self.custom_args


class TestConstellationBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup
        """
        self.testConst = pysat.Constellation(instruments=[
            pysat.Instrument('pysat', 'testing', num_samples=10,
                             clean_level='clean',
                             update_files=True)
            for i in range(5)])
        self.load_date = pysat.instruments.pysat_testing._test_dates['']['']
        self.testConst.load(date=self.load_date)
        self.custom_args = [2]

    def teardown(self):
        """ Runs after every method to clean up previous testing
        """
        del self.testConst, self.load_date, self.custom_args

    def test_basic_repr(self):
        """Test __repr__ with a custom method"""

        self.testConst.custom_attach(mult_data, args=self.custom_args)
        self.out = self.testConst.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("'function'") >= 0

    def test_single_modifying_custom_function_error(self):
        """Test for error when custom function loaded as modify returns a value
        """
        def custom_with_return_data(inst):
            inst.data['doubleMLT'] = 2.0 * inst.data.mlt
            return 5.0 * inst.data['mlt']

        self.testConst.custom_attach(custom_with_return_data)
        with pytest.raises(ValueError) as verr:
            self.testConst.load(date=self.load_date)

        estr = 'Custom functions should not return any information via return'
        assert str(verr).find(estr) >= 0

    def test_custom_keyword_instantiation(self):
        """Test adding custom methods at Instrument instantiation
        """

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
                             clean_level='clean', custom=custom)
            for i in range(5)])

        # Ensure all instruments within both constellations have the same
        # custom_* attributes
        for i, inst in enumerate(self.testConst.instruments):
            inst2 = testConst2.instruments[i]
            assert inst.custom_functions == inst2.custom_functions
            assert inst.custom_args == inst2.custom_args
            assert inst.custom_kwargs == inst2.custom_kwargs

    def test_clear_functions(self):
        """Test successful clearance of custom functions
        """
        self.testConst.custom_attach(lambda inst, imult, out_units='h':
                                     {'data': (inst.data.mlt * imult).values,
                                      'long_name': 'doubleMLTlong',
                                      'units': out_units, 'name': 'doubleMLT'},
                                     args=[2], kwargs={"out_units": "hours1"})

        # Test to see that the custom function was attached
        for inst in self.testConst.instruments:
            assert len(inst.custom_functions) == 1
            assert len(inst.custom_args) == 1
            assert len(inst.custom_kwargs) == 1

        # Test to see that the custom function was cleared
        self.testConst.custom_clear()
        for inst in self.testConst.instruments:
            assert inst.custom_functions == []
            assert inst.custom_args == []
            assert inst.custom_kwargs == []
