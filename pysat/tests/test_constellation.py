#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Unit tests for the Constellation class."""

import datetime as dt
import logging
import numpy as np
import pandas as pds
import pytest

import pysat
from pysat import constellations
from pysat.tests.classes.cls_registration import TestWithRegistration
from pysat.utils import testing


class TestConstellationInitReg(TestWithRegistration):
    """Unit tests for the Constellation class with registered Instruments."""

    @pytest.mark.parametrize("ikeys, ivals, ilen",
                             [(["platforms", "tags"], [["platname1"], [""]], 2),
                              (["names", "tags"], [["name2"], [""]], 2),
                              (["names"], [["name1", "name2"]], 15)])
    def test_construct_constellation(self, ikeys, ivals, ilen):
        """Test construction of a Constellation with good input.

        Parameters
        ----------
        ikeys : list
            Strings for keyword arguments in Constellation
        ivals : str
            Keyword arguments values
        ilen : int
            Number of expected Instruments within Constellation

        """

        # Register fake Instrument modules
        pysat.utils.registry.register(self.module_names)

        # Initialize the Constellation using the desired kwargs
        const = pysat.Constellation(
            **{ikey: ivals[i] for i, ikey in enumerate(ikeys)},
            use_header=True)

        # Test that the appropriate number of Instruments were loaded. Each
        # fake Instrument has 5 tags and 1 inst_id.
        assert len(const.instruments) == ilen
        return

    def test_all_bad_construct_constellation(self):
        """Test raises ValueError when all inputs are unregistered."""

        # Register fake Instrument modules
        pysat.utils.registry.register(self.module_names)

        # Evaluate raised error
        testing.eval_bad_input(pysat.Constellation, ValueError,
                               "no registered packages match input",
                               input_kwargs={'platforms': ['Executor']})
        return

    def test_some_bad_construct_constellation(self, caplog):
        """Test partial load and log warning if some inputs are unregistered."""

        # Register fake Instrument modules
        pysat.utils.registry.register(self.module_names)

        # Load the Constellation and capture log output
        with caplog.at_level(logging.WARNING, logger='pysat'):
            const = pysat.Constellation(platforms=['Executor', 'platname1'],
                                        tags=[''], use_header=True)

        # Test the partial Constellation initialization
        assert len(const.instruments) == 2

        # Test the log warning
        assert caplog.text.find("unable to load some platforms") >= 0

        del const
        return


class TestConstellationInit(object):
    """Test the Constellation class."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.instruments = constellations.single_test.instruments
        self.in_kwargs = {"instruments": self.instruments,
                          "const_module": constellations.single_test}
        self.const = None
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.const, self.instruments, self.in_kwargs, self.ref_time
        return

    @pytest.mark.parametrize("ikey,ival,ilen",
                             [("const_module", None, 1),
                              ("instruments", None, 1),
                              (None, None, 2)])
    def test_construct_constellation(self, ikey, ival, ilen):
        """Test construction of a Constellation with good input.

        Parameters
        ----------
        ikey : str
            Keyword argument passed to Constellation
        ival : NoneType
            Value for keyword argument
        ilen : int
            Number of expected Instruments within Constellation

        """

        if ikey is not None:
            self.in_kwargs[ikey] = ival
        self.const = pysat.Constellation(**self.in_kwargs)
        assert len(self.const.instruments) == ilen
        return

    def test_init_constellation_bad_inst_module(self):
        """Test Constellation raises AttributeError with bad inst_module."""

        testing.eval_bad_input(pysat.Constellation, AttributeError,
                               "missing required attribute 'instruments'",
                               input_kwargs={'const_module': self.instruments})
        return

    def test_construct_raises_noniterable_error(self):
        """Test error raised when Constellation non iterable."""

        testing.eval_bad_input(pysat.Constellation, ValueError,
                               "instruments argument must be list-like",
                               input_kwargs={
                                   'instruments': self.instruments[0]})
        return

    def test_construct_non_inst_list(self):
        """Test error raised when Constellation inputs aren't instruments."""

        testing.eval_bad_input(pysat.Constellation, ValueError,
                               "Constellation input is not an Instrument",
                               input_kwargs={'instruments': [
                                   self.instruments[0], 'not an inst']})
        return

    def test_construct_null(self):
        """Test that a Constellation constructed without arguments is empty."""

        self.const = pysat.Constellation()
        assert len(self.const.instruments) == 0
        return

    def test_getitem(self):
        """Test Constellation iteration through instruments attribute."""

        self.in_kwargs['const_module'] = None
        self.const = pysat.Constellation(**self.in_kwargs, use_header=True)
        tst_get_inst = self.const[:]
        pysat.utils.testing.assert_lists_equal(self.instruments, tst_get_inst)
        return

    def test_repr_w_inst(self):
        """Test Constellation string output with instruments loaded."""

        self.in_kwargs['const_module'] = None
        self.const = pysat.Constellation(**self.in_kwargs, use_header=True)
        out_str = self.const.__repr__()

        assert out_str.find("Constellation(instruments") >= 0
        return

    def test_str_w_inst(self):
        """Test Constellation string output with instruments loaded."""

        self.in_kwargs['const_module'] = None
        self.const = pysat.Constellation(**self.in_kwargs, use_header=True)
        out_str = self.const.__str__()

        assert out_str.find("pysat Constellation ") >= 0
        assert out_str.find("Index Platform") > 0
        return

    def test_str_wo_inst(self):
        """Test Constellation string output without instruments."""

        self.const = pysat.Constellation()
        out_str = self.const.__str__()

        assert out_str.find("pysat Constellation ") >= 0
        assert out_str.find("No assigned Instruments") > 0
        return

    @pytest.mark.parametrize("common_index,cstr", [(True, "Common"),
                                                   (False, "Full")])
    def test_str_with_data(self, common_index, cstr):
        """Test Constellation string output with loaded data.

        Parameters
        ----------
        common_index : bool
            Value for 'common_index' passed to Constellation
        cstr : str
            String to test for

        """

        self.in_kwargs["common_index"] = common_index
        self.const = pysat.Constellation(**self.in_kwargs)
        self.const.load(date=self.ref_time, use_header=True)
        out_str = self.const.__str__()

        assert out_str.find("pysat Constellation ") >= 0
        assert out_str.find("{:s} time range".format(cstr)) > 0
        return

    def test_single_attachment_of_custom_function(self):
        """Test successful attachment of custom function."""

        # Define a custom function
        def double_mlt(inst):
            dmlt = 2.0 * inst.data.mlt
            dmlt.name = 'double_mlt'
            inst.data[dmlt.name] = dmlt
            return

        # Initialize the constellation
        self.in_kwargs['const_module'] = None
        self.const = pysat.Constellation(**self.in_kwargs)

        # Add the custom function
        self.const.custom_attach(double_mlt, at_pos='end')
        self.const.load(date=self.ref_time, use_header=True)

        # Test the added value
        for inst in self.const:
            assert 'double_mlt' in inst.variables
            assert (inst['double_mlt'] == 2.0 * inst['mlt']).all()
        return


class TestConstellationFunc(object):
    """Test the Constellation class attributes and methods."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.inst = list(constellations.testing.instruments)
        self.const = pysat.Constellation(instruments=self.inst, use_header=True)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.attrs = ["platforms", "names", "tags", "inst_ids", "instruments",
                      "bounds", "empty", "empty_partial", "index_res",
                      "common_index", "date", "yr", "doy", "yesterday", "today",
                      "tomorrow", "variables"]
        self.inst_attrs = ['platform', 'name', 'tag', 'inst_id', 'clean_level',
                           'pandas_format', "empty", "yr", 'pad', 'date',
                           'doy', 'acknowledgements', 'references']
        self.dims = ['time', 'x', 'y', 'z', 'profile_height', 'latitude',
                     'longitude', 'altitude']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.inst, self.const, self.ref_time, self.attrs, self.dims
        del self.inst_attrs
        return

    def test_has_required_attrs(self):
        """Ensure the instrument has all required attributes present."""

        for req_attr in self.attrs:
            assert hasattr(self.const, req_attr)
        return

    @pytest.mark.parametrize("test_ind", [0, 1, 2, 3])
    def test_equal_length_attrs(self, test_ind):
        """Ensure each instruments-length attribute is the correct length.

        Parameters
        ----------
        test_inst : list
            Index into `self.attrs`

        """
        comp_len = len(self.const.instruments)
        assert len(getattr(self.const, self.attrs[test_ind])) == comp_len
        return

    def test_bounds_passthrough(self):
        """Ensure bounds are applied to each instrument within Constellation."""

        # Set bounds
        stop_date = self.ref_time + dt.timedelta(days=365)
        self.const.bounds = (self.ref_time, stop_date)

        # Ensure constellation reports correct dates
        assert self.const.bounds[0:2] == ([self.ref_time], [stop_date])

        # Test bounds are the same for all instruments
        for instrument in self.const:
            assert instrument.bounds == self.const.bounds
        return

    def test_empty_data_index(self):
        """Test the empty index attribute."""

        # Test the attribute with no loaded data
        assert isinstance(self.const.index, pds.Index)
        assert len(self.const.index) == 0
        return

    def test_empty_data_date(self):
        """Test the date property when no data is loaded."""

        assert self.const.date is None
        return

    def test_empty_variables(self):
        """Test the variables property when no data is loaded."""

        assert len(self.const.variables) == 0
        return

    def test_empty_flag_data_empty(self):
        """Test the status of the empty flag for unloaded data."""

        assert self.const.empty
        assert self.const.empty_partial
        return

    def test_empty_flag_data_empty_partial_load(self):
        """Test the status of the empty flag for partially loaded data."""

        self.const = pysat.Constellation(
            const_module=constellations.testing_partial, use_header=True)
        self.const.load(date=self.ref_time)
        assert self.const.empty_partial
        assert not self.const.empty
        return

    def test_empty_flag_data_not_empty_partial_load(self):
        """Test the alt status of the empty flag for partially loaded data."""

        self.const = pysat.Constellation(
            const_module=constellations.testing_partial, use_header=True)
        self.const.load(date=self.ref_time)
        assert not self.const._empty(all_inst=False)
        return

    def test_empty_flag_data_not_empty(self):
        """Test the status of the empty flag for loaded data."""

        # Load data and test the status flag
        self.const.load(date=self.ref_time, use_header=True)
        assert not self.const.empty
        return

    @pytest.mark.parametrize("ikwarg", [{"common_index": False},
                                        {"index_res": 60.0}])
    def test_full_data_index(self, ikwarg):
        """Test the empty index attribute."""

        # Test the attribute with loaded data
        self.const = pysat.Constellation(instruments=self.inst, **ikwarg)
        self.const.load(date=self.ref_time, use_header=True)
        assert isinstance(self.const.index, pds.Index)
        assert self.const.index[0] == self.ref_time

        if "index_res" in ikwarg.keys():
            assert self.const.index.freq == pds.DateOffset(
                seconds=ikwarg['index_res'])
        return

    def test_today_yesterday_and_tomorrow(self):
        """Test the correct instantiation of yesterday/today/tomorrow dates."""

        for cinst in self.const.instruments:
            assert cinst.today() == self.const.today()
            assert cinst.yesterday() == self.const.yesterday()
            assert cinst.tomorrow() == self.const.tomorrow()
        return

    def test_full_data_date(self):
        """Test the date property when no data is loaded."""

        # Test the attribute with loaded data
        self.const.load(date=self.ref_time, use_header=True)

        assert self.const.date == self.ref_time
        return

    def test_full_variables(self):
        """Test the variables property when no data is loaded."""

        # Test the attribute with loaded data
        self.const.load(date=self.ref_time, use_header=True)

        assert len(self.const.variables) > 0
        assert 'uts_pysat_testing' in self.const.variables
        assert 'x' in self.const.variables
        return

    def test_download(self):
        """Check that instruments are downloadable."""

        self.const.download(self.ref_time, self.ref_time)
        for inst in self.const.instruments:
            assert len(inst.files.files) > 0
        return

    def test_get_unique_attr_vals_bad_attr(self):
        """Test raises AttributeError for bad input value."""

        testing.eval_bad_input(self.const._get_unique_attr_vals, AttributeError,
                               "does not have attribute", ['not_an_attr'])
        return

    def test_get_unique_attr_vals_bad_type(self):
        """Test raises TypeError for bad input attribute type."""

        testing.eval_bad_input(self.const._get_unique_attr_vals, TypeError,
                               "attribute is not list-like", ['empty'])
        return

    def test_bad_call_inst_method(self):
        """Test raises AttributeError for missing Instrument method."""

        testing.eval_bad_input(self.const._call_inst_method, AttributeError,
                               "unknown method", ['not a method'])
        return

    @pytest.mark.parametrize('common_coord', [True, False])
    @pytest.mark.parametrize('fill_method', [None, 'nearest', 'linear'])
    def test_to_inst_xarray(self, common_coord, fill_method):
        """Test conversion of Constellation of mixed type to xarray Instrument.

        Parameters
        ----------
        common_coord : bool
            For Constellations with any xarray.Dataset Instruments, True to
            include locations where all coordinate arrays cover, False to use
            the maximum location range from the list of coordinates
        fill_method : str or NoneType
            Fill method if common data coordinates do not match exactly. If
            one of 'nearest', 'pad'/'ffill', 'backfill'/'bfill', or None then
            no interpolation will occur.  If 'linear', 'zero', 'slinear',
            'quadratic', 'cubic', or 'polynomial' are used, then 1D or ND
            interpolation will be used.

        """

        self.const.load(date=self.ref_time)
        out_inst = self.const.to_inst(common_coord, fill_method)

        # Test the output instrument attributes
        assert not out_inst.pandas_format
        assert out_inst.platform == 'pysat'
        assert out_inst.tag == ''
        assert out_inst.inst_id == ''
        assert out_inst.clean_level == 'clean'
        assert out_inst.pad is None
        assert out_inst.date == self.ref_time
        assert out_inst.doy == int(self.ref_time.strftime('%j'))
        assert np.all([out_inst.name.find(iname) >= 0
                       for iname in self.const.names])

        # Test the output instrument data
        testing.assert_lists_equal(self.dims, list(out_inst.data.dims.keys()))
        testing.assert_list_contains(self.dims,
                                     list(out_inst.data.coords.keys()))
        testing.assert_list_contains(['variable_profile_height', 'image_lon',
                                      'image_lat'],
                                     list(out_inst.data.coords.keys()))

        for cinst in self.const.instruments:
            for var in cinst.variables:
                var_name = '_'.join([var, cinst.platform, cinst.name])
                assert (var in out_inst.variables
                        or var_name in out_inst.variables), \
                    "missing variable: {:s} or {:s}".format(var, var_name)
                assert (var == 'time' or var in out_inst.meta
                        or var_name in out_inst.meta), \
                    "missing variable in metadata: {:s} or {:s}".format(
                        var, var_name)

        # Test the output instrument index
        testing.assert_lists_equal(list(out_inst.index), list(self.const.index))

        return

    def test_to_inst_pandas_w_pad(self):
        """Test Constellation `to_inst` with single, padded pandas Instrument.

        """
        # Redefine the Instrument and constellation
        self.inst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_testing, use_header=True,
            pad=pds.DateOffset(hours=1), num_samples=10)
        self.const = pysat.Constellation(instruments=[self.inst],
                                         use_header=True)

        # Load the data
        self.inst.load(date=self.ref_time)
        self.const.load(date=self.ref_time)

        # Convert the Constellation into an Instrument equivalent to `self.inst`
        out_inst = self.const.to_inst()

        # Test the output instrument attributes
        assert out_inst.pandas_format

        for iattr in self.inst_attrs:
            assert getattr(out_inst, iattr) == getattr(self.inst, iattr), \
                "Unexpected value for Instrument attribute {:}".format(iattr)

        # Test the output instrument data
        testing.assert_lists_equal(self.inst.variables, out_inst.variables)
        assert np.all(out_inst.data == self.inst.data)

        # Test the output instrument metadata
        assert out_inst.meta == self.inst.meta

        # Test the output instrument index
        testing.assert_lists_equal(list(out_inst.index), list(self.inst.index))

        return

    def test_to_inst_mult_pad_clean(self):
        """Test Constellation `to_inst` with multiple clean levels and pads."""
        # Redefine the Instrument and constellation
        clean_level = 'dirty'
        pad = pds.DateOffset(hours=1)
        self.inst = [
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             use_header=True, pad=pad, num_samples=10),
            pysat.Instrument(inst_module=pysat.instruments.pysat_testing,
                             use_header=True, pad=2 * pad,
                             clean_level=clean_level, num_samples=10)]
        self.const = pysat.Constellation(instruments=self.inst, use_header=True)

        # Load the Instrument and Constellation data
        self.inst[-1].load(date=self.ref_time)
        self.const.load(date=self.ref_time)

        # Convert the Constellation into an Instrument equivalent to `self.inst`
        out_inst = self.const.to_inst()

        # Test the output instrument attributes
        assert out_inst.pandas_format

        for iattr in self.inst_attrs:
            assert getattr(out_inst, iattr) == getattr(self.inst[1], iattr), \
                "Unexpected value for Instrument attribute {:}".format(iattr)

        # Test the output instrument data and metadata
        for var in self.inst[1].variables:
            out_var = "_".join([var, self.inst[1].platform, self.inst[1].name])
            assert out_var in out_inst.variables, \
                "missing data variable: {:s}".format(out_var)
            assert out_var in out_inst.meta, \
                "missing metadata variable: {:s}".format(out_var)
            assert np.all(out_inst[out_var] == self.inst[1][var]), \
                "mismatched data for: {:s}".format(var)

        # Test the output instrument index
        testing.assert_lists_equal(list(out_inst.index),
                                   list(self.inst[1].index))

        return
