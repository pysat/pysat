#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the `pysat.utils.coords` functions."""

import datetime as dt
import logging
import numpy as np
import pytest

import pysat
from pysat.utils import coords
from pysat.utils import testing


class TestCyclicData(object):
    """Unit tests for the `adjust_cyclic_data` function."""

    def setup_method(self):
        """Set up the unit test environment."""
        self.ref_angles = np.array([340.0, 348.0, 358.9, 0.5, 5.0, 9.87])
        return

    def teardown_method(self):
        """Clean up the unit test environment."""
        del self.ref_angles
        return

    def test_adjust_cyclic_data_default(self):
        """Test adjust_cyclic_data with default range."""

        ref_rad = np.radians(self.ref_angles) - np.pi
        ref_angles = coords.adjust_cyclic_data(ref_rad)

        assert ref_angles.max() < 2.0 * np.pi
        assert ref_angles.min() >= 0.0
        return

    def test_adjust_cyclic_data_custom(self):
        """Test adjust_cyclic_data with a custom range."""

        ref_angles = coords.adjust_cyclic_data(self.ref_angles,
                                               high=180.0, low=-180.0)

        assert ref_angles.max() < 180.0
        assert ref_angles.min() >= -180.0
        return


class TestUpdateLon(object):
    """Unit tests for the `update_longitude` function."""

    def setup_method(self):
        """Set up the unit test environment."""
        self.py_inst = None
        self.inst_time = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment."""
        del self.py_inst, self.inst_time
        return

    @pytest.mark.parametrize("name", ["testing", "testing_xarray",
                                      "ndtesting", "testmodel"])
    def test_update_longitude(self, name):
        """Test `update_longitude` successful run."""

        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        use_header=True)
        self.py_inst.load(date=self.inst_time)

        # Test instruments initially define longitude between 0-360 deg
        assert np.all(self.py_inst.data['longitude'] < 360.0)
        assert np.all(self.py_inst.data['longitude'] >= 0.0)

        # Longitude defaults to updating range from -180 to 180 deg
        coords.update_longitude(self.py_inst, lon_name="longitude")

        assert np.all(self.py_inst.data['longitude'] < 180.0)
        assert np.all(self.py_inst.data['longitude'] >= -180.0)
        return

    def test_bad_lon_name_update_longitude(self):
        """Test update_longitude with a bad longitude name."""

        self.py_inst = pysat.Instrument(platform='pysat', name="testing",
                                        use_header=True)
        self.py_inst.load(date=self.inst_time)

        testing.eval_bad_input(coords.update_longitude, ValueError,
                               "unknown longitude variable name",
                               [self.py_inst], {'lon_name': "not longitude"})

        return


class TestCalcSLT(object):
    """Unit tests for `calc_solar_local_time`.

    Note
    ----
    Includes integration tests with `update_longitude`.

    """

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.py_inst = None
        self.inst_time = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.py_inst, self.inst_time
        return

    @pytest.mark.parametrize("name", ["testing", "testing_xarray"])
    def test_calc_solar_local_time(self, name):
        """Test SLT calculation with longitudes from 0-360 deg for 0 UTH."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        num_samples=1, use_header=True)
        self.py_inst.load(date=self.inst_time)

        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt')

        # This works because test instrument longitude ranges from 0-360 deg.
        # Testing the difference in periodic space to guard against changes
        # in numerical precision across platforms.
        diff = abs(self.py_inst['slt'].values
                   - self.py_inst['longitude'].values / 15.0)
        diff_radians = diff * np.pi / 12.0
        sin_diff = np.sin(diff_radians)
        cos_diff = np.cos(diff_radians)
        assert np.max(np.abs(sin_diff)) < 1.0e-6
        assert np.min(np.abs(cos_diff)) > 1.0 - 1.0e-6
        return

    @pytest.mark.parametrize("name", ["testing", "testing_xarray"])
    def test_calc_solar_local_time_inconsistent_keywords(self, name, caplog):
        """Test that ref_date only works when apply_modulus=False."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        num_samples=1, use_header=True)
        self.py_inst.load(date=self.inst_time)

        # Apply solar local time method and capture logging output
        with caplog.at_level(logging.INFO, logger='pysat'):
            coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                         slt_name='slt',
                                         ref_date=self.py_inst.date,
                                         apply_modulus=True)
        captured = caplog.text

        # Confirm we have the correct informational message
        assert captured.find('Keyword `ref_date` only supported if') >= 0
        return

    def test_calc_solar_local_time_w_neg_longitude(self):
        """Test calc_solar_local_time with longitudes from -180 to 180 deg."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name="testing",
                                        use_header=True)
        self.py_inst.load(date=self.inst_time)

        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt')
        coords.update_longitude(self.py_inst, lon_name="longitude", low=-180.0,
                                high=180.0)
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt2')

        # Test the output agrees to an acceptable tolerance
        assert (abs(self.py_inst['slt'] - self.py_inst['slt2'])).max() < 1.0e-6
        return

    def test_bad_lon_name_calc_solar_local_time(self):
        """Test raises ValueError with a bad longitude name."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name="testing",
                                        use_header=True)
        self.py_inst.load(date=self.inst_time)

        # Test that the correct Exception and error message are raised
        testing.eval_bad_input(coords.calc_solar_local_time, ValueError,
                               "unknown longitude variable name",
                               [self.py_inst], {"lon_name": "not longitude",
                                                "slt_name": 'slt'})

        return

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "ndtesting"])
    def test_lon_broadcasting_calc_solar_local_time(self, name):
        """Test calc_solar_local_time with longitude coordinates."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        use_header=True)
        self.py_inst.load(date=self.inst_time)
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt')

        # Test the output range
        assert self.py_inst['slt'].max() < 24.0
        assert self.py_inst['slt'].min() >= 0.0
        return

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "ndtesting"])
    def test_lon_broadcasting_calc_solar_local_time_no_mod_multiday(self, name):
        """Test non modulated solar local time output for a 2 day range."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        use_header=True)
        self.py_inst.load(date=self.inst_time,
                          end_date=self.inst_time + dt.timedelta(days=2))
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt', apply_modulus=False)

        # Test the output range
        assert self.py_inst['slt'].max() > 48.0
        assert self.py_inst['slt'].max() < 72.0
        assert self.py_inst['slt'].min() >= 0.0
        return

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "ndtesting"])
    def test_lon_broadcasting_calc_solar_local_time_no_mod_ref_date(self, name):
        """Test non modulated SLT output for a 2 day range with a ref date."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        use_header=True)
        self.py_inst.load(date=self.inst_time, end_date=self.inst_time
                          + dt.timedelta(days=2))
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt', apply_modulus=False,
                                     ref_date=self.inst_time
                                              - dt.timedelta(days=1))

        # Test the output range
        assert self.py_inst['slt'].max() > 72.0
        assert self.py_inst['slt'].max() < 96.0
        assert self.py_inst['slt'].min() >= 24.0
        return

    @pytest.mark.parametrize("name", ["testmodel", "testing2d",
                                      "ndtesting"])
    def test_lon_broadcasting_calc_solar_local_time_no_mod(self, name):
        """Test SLT calc with longitude coordinates and no modulus."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name=name,
                                        use_header=True)
        self.py_inst.load(date=self.inst_time)
        coords.calc_solar_local_time(self.py_inst, lon_name="longitude",
                                     slt_name='slt', apply_modulus=False)

        # Test the output range
        assert self.py_inst['slt'].max() > 24.0
        assert self.py_inst['slt'].max() < 48.0
        assert self.py_inst['slt'].min() >= 0.0
        return

    def test_single_lon_calc_solar_local_time(self):
        """Test calc_solar_local_time with a single longitude value."""

        # Instantiate instrument and load data
        self.py_inst = pysat.Instrument(platform='pysat', name="testing_xarray",
                                        use_header=True)
        self.py_inst.load(date=self.inst_time)
        lon_name = 'lon2'

        # Create a second longitude with a single value
        self.py_inst.data = self.py_inst.data.update({lon_name: (lon_name,
                                                                 [10.0])})
        self.py_inst.data = self.py_inst.data.squeeze(dim=lon_name)

        # Calculate and test the SLT
        coords.calc_solar_local_time(self.py_inst, lon_name=lon_name,
                                     slt_name='slt')

        assert self.py_inst['slt'].max() < 24.0
        assert self.py_inst['slt'].min() >= 0.0
        assert self.py_inst['slt'].shape == self.py_inst.index.shape
        return


class TestEstCommonCoord(object):
    """Unit tests for the `establish_common_coord` function."""

    def setup_method(self):
        """Set up the unit test environment."""
        self.res = 1.0
        self.long_coord = np.arange(0, 360, self.res)
        self.short_coord = np.arange(10, 350, 10.0 * self.res)
        return

    def teardown_method(self):
        """Clean up the unit test environment."""
        del self.long_coord, self.short_coord, self.res
        return

    def test_establish_common_coord_overlap(self):
        """Test `establish_common_coord` with common=True."""

        out = coords.establish_common_coord([self.long_coord, self.short_coord])
        out_res = np.unique(out[1:] - out[:-1])

        assert self.short_coord.min() == out.min(), "unexpected minimum value"
        assert self.short_coord.max() == out.max(), "unexpected maximum value"
        assert len(out_res) == 1, "inconsistend coordinate resolution"
        assert out_res[0] == self.res, "unexpected coordinate resolution"
        return

    def test_establish_common_coord_max_range(self):
        """Test `establish_common_coord` with common=False."""

        out = coords.establish_common_coord([self.short_coord, self.long_coord],
                                            common=False)
        out_res = np.unique(out[1:] - out[:-1])

        assert self.long_coord.min() == out.min(), "unexpected minimum value"
        assert self.long_coord.max() == out.max(), "unexpected maximum value"
        assert len(out_res) == 1, "inconsistend coordinate resolution"
        assert out_res[0] == self.res, "unexpected coordinate resolution"
        return

    def test_establish_common_coord_single_val(self):
        """Test `establish_common_coord` where one coordinate is a value."""

        out = coords.establish_common_coord([self.short_coord[0],
                                             self.long_coord], common=False)
        out_res = np.unique(out[1:] - out[:-1])

        assert self.long_coord.min() == out.min(), "unexpected minimum value"
        assert self.long_coord.max() == out.max(), "unexpected maximum value"
        assert len(out_res) == 1, "inconsistend coordinate resolution"
        assert out_res[0] == self.res, "unexpected coordinate resolution"
        return

    def test_establish_common_coord_single_val_only(self):
        """Test `establish_common_coord` where tje coordinate is a value."""

        out = coords.establish_common_coord([self.short_coord[0]])

        assert self.short_coord[0] == out[0], "unexpected value"
        assert len(out) == 1, "unexpected coordinate length"
        return


class TestExpandXarrayDims(object):
    """Unit tests for the `expand_xarray_dims` function."""

    def setup_method(self):
        """Set up the unit test environment."""
        self.test_inst = pysat.Instrument(
            inst_module=pysat.instruments.pysat_ndtesting, use_header=True)
        self.start_time = pysat.instruments.pysat_ndtesting._test_dates['']['']
        self.data_list = []
        self.out = None
        self.meta = None
        return

    def teardown_method(self):
        """Clean up the unit test environment."""
        del self.test_inst, self.start_time, self.data_list, self.meta, self.out
        return

    def set_data_meta(self, dims_equal):
        """Set the input data list and meta data.

        Parameters
        ----------
        dims_equal : bool
            If True, the dimension variables for the data sets should be the
            same; if False they should have different dimensions apart from
            the 'time' dimension

        """

        self.test_inst.load(date=self.start_time)
        self.data_list.append(self.test_inst.data)
        self.meta = self.test_inst.meta

        # The second data set should have half the time samples
        num_samples = int(self.test_inst.index.shape[0] / 2)

        if dims_equal:
            # Load a second data set with half the time samples
            self.test_inst = pysat.Instrument(
                inst_module=self.test_inst.inst_module,
                num_samples=num_samples, use_header=True)
        else:
            # Load a second data set with different dimensions apart from time
            self.test_inst = pysat.Instrument(
                inst_module=pysat.instruments.pysat_testmodel,
                num_samples=num_samples, use_header=True)

        self.test_inst.load(date=self.start_time + dt.timedelta(days=1))
        self.data_list.append(self.test_inst.data)

        return

    def eval_dims(self, dims_equal, exclude_dims=None, default_fill_val=None):
        """Set the input data list and meta data.

        Parameters
        ----------
        dims_equal : bool
            If True, the dimension variables for the data sets should be the
            same; if False they should have different dimensions apart from
            the 'time' dimension
        exclude_dims : list-like or NoneType
            A list of dimensions that have the same name, but can have different
            values or None if all the dimensions with the same name should
            have the same shape. (default=None)
        default_fill_val : any
            The expected fill value for data variables not present in self.meta
            (default=None)

        """
        if exclude_dims is None:
            exclude_dims = []

        # Define the reference Dataset
        ref_dims = list(self.out[0].dims.keys())

        # Cycle through the remaining Datasets
        for i, xdata in enumerate(self.out[1:]):
            test_dims = list(xdata.dims.keys())

            # Test that the expected dimension names overlap between datasets
            if dims_equal:
                testing.assert_lists_equal(test_dims, ref_dims)
            else:
                for tdim in test_dims:
                    assert (tdim == 'time' if tdim in ref_dims else tdim
                            != 'time'), "unexpected dimension: {:}".format(tdim)

            # Test the dimensions shapes for expected (lack of) differences
            for tdim in test_dims:
                if tdim in ref_dims:
                    if tdim in exclude_dims:
                        assert xdata[tdim].shape != self.out[0][tdim].shape
                    else:
                        assert xdata[tdim].shape == self.out[0][tdim].shape

                        if xdata[tdim].shape != self.data_list[
                                i + 1][tdim].shape:
                            # This data set is smaller, test for fill values
                            for dvar in xdata.data_vars.keys():
                                if tdim in xdata[dvar].dims:
                                    if dvar in self.meta:
                                        fill_val = self.meta[
                                            dvar, self.meta.labels.fill_val]
                                    else:
                                        fill_val = default_fill_val

                                    try:
                                        if np.isnan(fill_val):
                                            assert np.isnan(
                                                xdata[dvar].values).any()
                                        else:
                                            assert np.any(xdata[dvar].values
                                                          == fill_val)
                                    except TypeError:
                                        # This is a string or object
                                        estr = "".join([
                                            "Bad or missing fill values for ",
                                            dvar, ": ({:} not in {:})".format(
                                                fill_val, xdata[dvar].values)])
                                        if fill_val is None:
                                            assert fill_val in xdata[
                                                dvar].values, estr
                                        else:
                                            assert np.any(xdata[dvar].values
                                                          == fill_val), estr

        return

    @pytest.mark.parametrize('dims_equal', [True, False])
    @pytest.mark.parametrize('exclude_dims', [None, ['time']])
    def test_expand_xarray_dims(self, dims_equal, exclude_dims):
        """Test successful padding of dimensions for xarray data.

        Parameters
        ----------
        dims_equal : bool
            If True, the dimension variables for the data sets should be the
            same; if False they should have different dimensions apart from
            the 'time' dimension
        exclude_dims : list-like or NoneType
            A list of dimensions that have the same name, but can have different
            values or None if all the dimensions with the same name should
            have the same shape. (default=None)

        """

        # Set the input parameters
        self.set_data_meta(dims_equal)

        # Run the dimension expansion
        self.out = coords.expand_xarray_dims(self.data_list, self.meta,
                                             dims_equal=dims_equal,
                                             exclude_dims=exclude_dims)

        # Test the results
        self.eval_dims(dims_equal, exclude_dims)

        return

    @pytest.mark.parametrize('new_data_type', [int, float, str, bool, None])
    def test_missing_meta(self, new_data_type):
        """Test success if variable is missing from meta.

        Parameters
        ----------
        new_data_type : type
            Data type for the new data that will be missing from `self.meta`

        """

        # Set the input parameters
        self.set_data_meta(True)

        # Add a data variable to one of the data sets
        self.data_list[1]['new_variable'] = self.data_list[1]['mlt'].astype(
            new_data_type)

        # Run the dimension expansion
        self.out = coords.expand_xarray_dims(self.data_list, self.meta,
                                             dims_equal=True)

        # Test the results
        fill_val = self.meta.labels.default_values_from_type(
            self.meta.labels.label_type['fill_val'], new_data_type)
        self.eval_dims(True, default_fill_val=fill_val)

        return
