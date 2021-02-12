#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import datetime as dt
import pytest

import pysat
from pysat import constellations


class TestConstellation:
    """Test the Constellation class."""
    def setup(self):
        """Create instruments and a constellation for each test
        """
        self.instruments = constellations.testing.instruments
        self.in_kwargs = {"instruments": self.instruments,
                          "const_module": pysat.constellations.single_test}
        self.const = None

    def teardown(self):
        """Clean up after each test
        """
        del self.const, self.instruments, self.in_kwargs

    @pytest.mark.parametrize("ikey,ival,ilen",
                             [("const_module", None, 5),
                              ("instruments", None, 1),
                              (None, None, 6)])
    def test_construct_constellation(self, ikey, ival, ilen):
        """Construct a Constellation with good input
        """
        if ikey is not None:
            self.in_kwargs[ikey] = ival
        self.const = pysat.Constellation(**self.in_kwargs)
        assert len(self.const.instruments) == ilen

    def test_construct_raises_noniterable_error(self):
        """Attempt to construct a Constellation by const_module and list
        """
        with pytest.raises(ValueError) as verr:
            self.const = pysat.Constellation(instruments=self.instruments[0])

        assert str(verr).find("instruments argument must be list-like")

    def test_construct_null(self):
        """Attempt to construct a Constellation with no arguments
        """
        self.const = pysat.Constellation()
        assert len(self.const.instruments) == 0

    def test_getitem(self):
        """Test Constellation iteration through instruments attribute
        """
        self.in_kwargs['const_module'] = None
        self.const = pysat.Constellation(**self.in_kwargs)
        tst_get_inst = self.const[:]
        pysat.utils.testing.assert_lists_equal(self.instruments, tst_get_inst)

    def test_repr_w_inst(self):
        """Test Constellation string output with instruments loaded
        """
        self.in_kwargs['const_module'] = None
        self.const = pysat.Constellation(**self.in_kwargs)
        out_str = self.const.__repr__()

        assert out_str.find("Constellation(instruments") >= 0

    def test_str_w_inst(self):
        """Test Constellation string output with instruments loaded
        """
        self.in_kwargs['const_module'] = None
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

    def test_single_attachment_of_custom_function(self):
        """Test successful attachment of custom function
        """
        # Define a custom function
        def double_mlt(inst):
            dmlt = 2.0 * inst.data.mlt
            dmlt.name = 'doubleMLT'
            inst.data[dmlt.name] = dmlt
            return

        # Initialize the constellation
        self.in_kwargs['const_module'] = None
        self.const = pysat.Constellation(**self.in_kwargs)

        # Add the custom function
        self.const.custom_attach(double_mlt, at_pos='end')
        self.const.load(2009, 1)

        # Test the added value
        for inst in self.const:
            assert 'doubleMLT' in inst.data.columns
            assert (inst['doubleMLT'] == 2.0 * inst['mlt']).all()

    def test_bounds_passthrough(self):
        """Ensure bounds are applied to each instrument within Constellation"""

        # Create costellation
        self.const = pysat.Constellation(instruments=self.instruments)

        # Set bounds
        self.start_date = dt.datetime(2009, 1, 1)
        self.stop_date = dt.datetime(2010, 1, 1)
        self.const.bounds = (self.start_date, self.stop_date)

        # Ensure constellation reports correct dates
        assert self.const.bounds[0:2] == ([self.start_date], [self.stop_date])

        # Test bounds are the same for all instruments
        for instrument in self.const:
            assert instrument.bounds == self.const.bounds
