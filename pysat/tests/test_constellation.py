from nose.tools import raises

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
