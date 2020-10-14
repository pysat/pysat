import pytest

import pysat


class TestConstellation:
    """Test the Constellation class."""
    def setup(self):
        """Create instruments and a constellation for each test
        """
        self.instruments = [pysat.Instrument('pysat', 'testing',
                                             clean_level='clean')
                            for i in range(2)]
        self.in_kwargs = {"instruments": self.instruments, "name": "testing"}
        self.const = None

    def teardown(self):
        """Clean up after each test
        """
        del self.const, self.instruments, self.in_kwargs

    @pytest.mark.parametrize("ikey,ival,ilen", [("name", None, 2),
                                                ("instruments", None, 5)])
    def test_construct_constellation(self, ikey, ival, ilen):
        """Construct a Constellation with good input
        """
        self.in_kwargs[ikey] = ival
        self.const = pysat.Constellation(**self.in_kwargs)
        assert len(self.const.instruments) == ilen

    @pytest.mark.parametrize("ikeys,ivals",
                             [([], []), (["instruments", "name"], [42, None])])
    def test_construct_raises_error(self, ikeys, ivals):
        """Attempt to construct a Constellation by name and list
        """
        for i, ikey in enumerate(ikeys):
            self.in_kwargs[ikey] = ivals[i]

        with pytest.raises(ValueError):
            self.const = pysat.Constellation(**self.in_kwargs)

    def test_construct_null(self):
        """Attempt to construct a Constellation with no arguments
        """
        self.const = pysat.Constellation()
        assert len(self.const.instruments) == 0

    def test_getitem(self):
        """Test Constellation:__getitem__
        """
        self.in_kwargs['name'] = None
        self.const = pysat.Constellation(**self.in_kwargs)

        assert self.const[0] == self.instruments[0]
        assert self.const[1] == self.instruments[1]
        assert self.const[:] == self.instruments[:]
        assert self.const[1::-1] == self.instruments[1::-1]

    def test_repr_w_inst(self):
        """Test Constellation string output with instruments loaded
        """
        self.in_kwargs['name'] = None
        self.const = pysat.Constellation(**self.in_kwargs)
        out_str = self.const.__repr__()

        assert out_str.find("Constellation(instruments") >= 0
        assert out_str.find("-> 2 Instruments") > 0

    def test_str_w_inst(self):
        """Test Constellation string output with instruments loaded
        """
        self.in_kwargs['name'] = None
        self.const = pysat.Constellation(**self.in_kwargs)
        out_str = self.const.__str__()

        assert out_str.find("pysat Constellation ") >= 0
        assert out_str.find("Index Platform") > 0

    def test_str_wo_inst(self):
        """Test Constellation string output without instruments loaded
        """
        self.const = pysat.Constellation()
        out_str = self.const.__str__()

        assert out_str.find("pysat Constellation ") >= 0
        assert out_str.find("No loaded Instruments") > 0

    def test_single_adding_custom_function(self):
        """Test successful attachment of custom function
        """
        # Define a custom function
        def double_mlt(inst):
            dmlt = 2.0 * inst.data.mlt
            dmlt.name = 'doubleMLT'
            return dmlt

        # Initialize the constellation
        self.in_kwargs['name'] = None
        self.const = pysat.Constellation(**self.in_kwargs)

        # Add the custom function
        self.const.data_mod(double_mlt, 'add', at_pos='end')
        self.const.load(2009, 1)

        # Test the added value
        for inst in self.const:
            assert 'doubleMLT' in inst.data.columns
            assert (inst['doubleMLT'] == 2.0 * inst['mlt']).all()
