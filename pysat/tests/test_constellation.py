import warnings
from nose.tools import raises
import numpy as np

import pysat


class TestConstellation:
    """Test the Constellation class."""
    def setup(self):
        """Create instruments and a constellation for each test."""
        self.instruments = [pysat.Instrument('pysat', 'testing',
                                             clean_level='clean')
                            for i in range(2)]
        self.const = pysat.Constellation(self.instruments)

    def teardown(self):
        """Clean up after each test."""
        del self.const

    def test_construct_by_list(self):
        """Construct a Constellation with a list."""
        const = pysat.Constellation(self.instruments)
        assert len(const.instruments) == 2

    def test_construct_by_name(self):
        """Construct a Constellation by name.

        Should access a predefined Constellation."""
        const = pysat.Constellation(name='testing')
        assert len(const.instruments) == 5

    @raises(ValueError)
    def test_construct_both(self):
        """Attempt to construct a Constellation by name and list.
        Raises an error."""
        pysat.Constellation(
            instruments=self.instruments,
            name='testing')

    @raises(ValueError)
    def test_construct_bad_instruments(self):
        """Attempt to construct a Constellation with
        a bad instrument 'list.'"""
        pysat.Constellation(instruments=42)

    def test_construct_null(self):
        """Attempt to construct a Constellation with
        no arguments."""
        const = pysat.Constellation()
        assert len(const.instruments) == 0

    def test_getitem(self):
        """Test Constellation:__getitem__."""
        assert self.const[0] == self.instruments[0]
        assert self.const[1] == self.instruments[1]
        assert self.const[:] == self.instruments[:]
        assert self.const[1::-1] == self.instruments[1::-1]

    def test_str(self):
        """Test Constellation:__str__."""
        assert str(self.const) == \
            "\npysat Constellation object:\ntesting\ntesting\n"


class TestAdditionIdenticalInstruments:
    def setup(self):
        self.const1 = pysat.Constellation(name='testing')
        self.const2 = pysat.Constellation(name='single_test')

    def teardown(self):
        del self.const1
        del self.const2



class TestDataMod:
    """Test adapted from test_custom.py."""
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testConst = \
            pysat.Constellation([pysat.Instrument('pysat', 'testing',
                                                  sat_id='10',
                                                  clean_level='clean')])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testConst

    def attach(self, function, kind='add', at_pos='end', *args, **kwargs):
        """Adds a function to the object's custom queue"""
        self.testConst.data_mod(function, kind, at_pos, *args, **kwargs)

    def test_single_adding_custom_function(self):
        """Test if custom function works correctly. Add function that returns
        pandas object."""
        def custom1(inst):
            d = 2. * inst.data.mlt
            d.name = 'doubleMLT'
            return d

        self.attach(custom1, 'add')
        self.testConst.load(2009, 1)
        ans = (self.testConst[0].data['doubleMLT'].values ==
               2. * self.testConst[0].data.mlt.values).all()
        assert ans


class TestDeprecation():

    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always")

        instruments = [pysat.Instrument(platform='pysat', name='testing',
                                        sat_id='10', clean_level='clean')
                       for i in range(2)]
        self.testC = pysat.Constellation(instruments)

    def teardown(self):
        """Runs after every method to clean up previous testing"""

        del self.testC

    def test_deprecation_warning_add(self):
        """Test if constellation.add is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                # initiate function with NoneTypes since function does not
                # need to run for DeprecationWarning to be thrown
                # Setting data_label to None should produce a ValueError after
                # warning is generated
                # ==> Save time in unit tests
                self.testC.add(bounds1=None, label1=None, bounds2=None,
                               label2=None, bin3=None, label3=None,
                               data_label=None)
            except ValueError:
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_deprecation_warning_difference(self):
        """Test if constellation.difference is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                # initiate function with NoneTypes since function does not
                # need to run for DeprecationWarning to be thrown
                # Setting data_labels to None should produce a TypeError after
                # warning is generated
                # ==> Save time in unit tests
                self.testC.difference(self.testC[0], self.testC[1],
                                      bounds=None, data_labels=None,
                                      cost_function=None)
            except TypeError:
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
