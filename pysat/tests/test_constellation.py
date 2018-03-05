import pysat
from nose.tools import assert_raises, raises

# TODO

class TestConstellation:
    def setup(self):
        self.instruments = [ pysat.Instrument('pysat','testing', clean_level='clean') 
                             for i in range(2) ] 
        self.const = pysat.Constellation(self.instruments)

    def teardown(self):
        del self.const

    def test_construct_by_list(self):
        pass

    def test_construct_by_name(self):
        self.const = pysat.Constellation(name='testing')
        assert len(self.const.instruments) == 5

    @raises(ValueError)
    def test_construct_both(self):
        pysat.Constellation(
            instruments = self.instruments,
            name = 'testing');

    @raises(ValueError)
    def test_construct_bad_instruments(self):
        pysat.Constellation(instruments = 42)

    @raises(ValueError)
    def test_construct_null(self):
        pysat.Constellation()

    def test_getitem(self):
        assert self.const[0] == self.instruments[0]
        assert self.const[1] == self.instruments[1]
        assert self.const[:] == self.instruments[:]

    def test_str(self):
        # FIXME define that string.
        assert str(self.const) == "stringgoeshere"

    def test_repr(self):
        # FIXME
        print(repr(self.const))
        assert repr(self.const) == "Constellation([..."

    # TODO write tests for add, difference.
