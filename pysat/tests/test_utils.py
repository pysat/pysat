#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat utils core functions."""

import contextlib
from importlib import reload
import inspect
import numpy as np
import os
import portalocker
import pytest
import shutil
import tempfile

import pysat
from pysat.tests.registration_test_class import TestWithRegistration
from pysat.utils import generate_instrument_list


def prep_dir(inst):
    """Prepare the directory to provide netCDF export file support.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument class object

    Returns
    -------
    bool
        True if directories create, False if not

    """
    # Create data directories
    try:
        os.makedirs(inst.files.data_path)
        return True
    except OSError:
        return False


def remove_files(inst):
    """Remove files associated with a pysat Instrument.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument class object

    """
    # Determine the directory where files are located
    temp_dir = inst.files.data_path

    # Iteritavely remove files
    for the_file in os.listdir(temp_dir):
        if the_file == 'pysat_test_ncdf.nc':
            file_path = os.path.join(temp_dir, the_file)

            if os.path.isfile(file_path):
                os.unlink(file_path)

    return


class TestCIonly(object):
    """Tests where we mess with local settings.

    Note
    ----
    These only run in CI environments such as GitHub Actions to avoid breaking
    an end user's setup

    """

    def setup(self):
        """Run to set up the test environment."""

        self.ci_env = (os.environ.get('CI') == 'true')
        if not self.ci_env:
            pytest.skip("Skipping local tests to avoid breaking user setup")

        return

    def teardown(self):
        """Clean up the test environment."""
        del self.ci_env
        return

    def test_initial_pysat_load(self, capsys):
        """Ensure initial load routines works."""

        # Move settings directory to simulate first load after install
        root = os.path.join(os.path.expanduser("~"), '.pysat')
        new_root = os.path.join(os.path.expanduser("~"), '.saved_pysat')
        shutil.move(root, new_root)

        reload(pysat)

        captured = capsys.readouterr()
        assert captured.out.find("Hi there!") >= 0

        # Make sure settings file created
        assert os.path.isfile(os.path.join(root, 'pysat_settings.json'))
        assert os.path.isdir(os.path.join(root, 'instruments'))
        assert os.path.isdir(os.path.join(root, 'instruments', 'archive'))

        # Move settings back
        shutil.rmtree(root)
        shutil.move(new_root, root)

        # Make sure pysat reloads settings
        reload(pysat)
        return


class TestScaleUnits(object):
    """Unit tests for `scale_units`."""

    def setup(self):
        """Run to set up the test environment."""

        self.deg_units = ["deg", "degree", "degrees", "rad", "radian",
                          "radians", "h", "hr", "hrs", "hours"]
        self.dist_units = ["m", "km", "cm"]
        self.vel_units = ["m/s", "cm/s", "km/s", 'm s$^{-1}$', 'cm s$^{-1}$',
                          'km s$^{-1}$', 'm s-1', 'cm s-1', 'km s-1']
        self.scale = 0.0
        return

    def teardown(self):
        """Clean up the test environment."""

        del self.deg_units, self.dist_units, self.vel_units, self.scale
        return

    def eval_unit_scale(self, out_unit, scale_type):
        """Evaluate the unit scaling.

        Parameters
        ----------
        out_unit : str
            Output unit name string
        scale_type : str
            String specifying 'angles' or 'distance'

        """

        if scale_type.lower() == 'angles':
            if out_unit.find("deg") == 0:
                assert self.scale == 1.0
            elif out_unit.find("rad") == 0:
                assert self.scale == np.pi / 180.0
            else:
                assert self.scale == 1.0 / 15.0
        elif scale_type.lower() == 'distance':
            if out_unit == "m":
                assert self.scale == 1.0
            elif out_unit.find("km") == 0:
                assert self.scale == 0.001
            else:
                assert self.scale == 100.0
        elif scale_type.lower() == 'velocity':
            if out_unit.find("m") == 0:
                assert self.scale == 1.0
            elif out_unit.find("km") == 0:
                assert self.scale == 0.001
        return

    def test_scale_units_same(self):
        """Test scale_units when both units are the same."""

        self.scale = pysat.utils.scale_units("happy", "happy")

        assert self.scale == 1.0
        return

    def test_scale_units_angles(self):
        """Test scale_units for angles."""
        for out_unit in self.deg_units:
            self.scale = pysat.utils.scale_units(out_unit, "deg")
            self.eval_unit_scale(out_unit, 'angles')
        return

    def test_scale_units_dist(self):
        """Test scale_units for distances."""

        for out_unit in self.dist_units:
            self.scale = pysat.utils.scale_units(out_unit, "m")
            self.eval_unit_scale(out_unit, 'distance')
        return

    def test_scale_units_vel(self):
        """Test scale_units for velocities."""

        for out_unit in self.vel_units:
            self.scale = pysat.utils.scale_units(out_unit, "m/s")
            self.eval_unit_scale(out_unit, 'velocity')
        return

    @pytest.mark.parametrize("in_args,err_msg", [
        (['happy', 'm'], 'output unit'), (['m', 'happy'], 'input unit'),
        (['m', 'm/s'], 'Cannot scale m and m/s'),
        (['happy', 'sad'], 'unknown units')])
    def test_scale_units_bad_input(self, in_args, err_msg):
        """Test raises ValueError for bad input combinations."""

        with pytest.raises(ValueError) as verr:
            pysat.utils.scale_units(*in_args)

        assert str(verr).find(err_msg) > 0
        return

    @pytest.mark.parametrize("unit1,unit2", [("m", "m/s"),
                                             ("m", "deg"),
                                             ("h", "km/s")])
    def test_scale_units_bad_match_pairs(self, unit1, unit2):
        """Test raises ValueError for all mismatched input pairings."""

        with pytest.raises(ValueError):
            pysat.utils.scale_units(unit1, unit2)

        return


class TestListify(object):
    """Unit tests for the `listify` function."""

    @pytest.mark.parametrize('iterable,nitem', [
        ('test', 1), (['test'], 1), ([[['test']]], 1), ([[[['test']]]], 1),
        ([['test', 'test']], 2), ([['test', 'test'], ['test', 'test']], 4),
        ([], 0), ([[]], 0)])
    def test_listify_list_string_inputs(self, iterable, nitem):
        """Test listify with various list levels of a string."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = ['test' for i in range(nitem)]
        pysat.utils.testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('iterable', [np.nan, np.full((1, 1), np.nan),
                                          np.full((2, 2), np.nan),
                                          np.full((3, 3, 3), np.nan)])
    def test_listify_nan_arrays(self, iterable):
        """Test listify with various np.arrays of NaNs."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = [np.nan
                        for i in range(int(np.product(np.shape(iterable))))]
        pysat.utils.testing.assert_lists_equal(new_iterable, tst_iterable,
                                               test_nan=True)
        return

    @pytest.mark.parametrize('iterable', [1, np.full((1, 1), 1),
                                          np.full((2, 2), 1),
                                          np.full((3, 3, 3), 1)])
    def test_listify_int_arrays(self, iterable):
        """Test listify with various np.arrays of integers."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = [1 for i in range(int(np.product(np.shape(iterable))))]
        pysat.utils.testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('iterable', [
        np.timedelta64(1), np.full((1, 1), np.timedelta64(1)),
        np.full((2, 2), np.timedelta64(1)),
        np.full((3, 3, 3), np.timedelta64(1))])
    def test_listify_class_arrays(self, iterable):
        """Test listify with various np.arrays of classes."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = [np.timedelta64(1)
                        for i in range(int(np.product(np.shape(iterable))))]
        pysat.utils.testing.assert_lists_equal(new_iterable, tst_iterable)
        return


class TestLoadNetCDF4(object):
    """Unit tests for `load_netcdf4`."""

    def setup(self):
        """Run to set up the test environment."""

        # Store current pysat directory
        self.data_path = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=100, update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']

        # Create testing directory
        prep_dir(self.testInst)

        # Initalize the loaded data
        self.loaded_inst = None
        return

    def teardown(self):
        """Clean up the test environment."""

        # Clear the attributes with data in them
        del self.loaded_inst, self.testInst, self.stime

        # Reset the pysat parameters
        pysat.params['data_dirs'] = self.data_path

        # Remove the temporary directory
        self.tempdir.cleanup()

        # Clear the directory attributes
        del self.data_path, self.tempdir
        return

    def eval_loaded_data(self):
        """Evaluate loaded test data."""
        # Test that the written and loaded data matches the initial data
        for dkey in self.testInst.data.columns:
            lkey = dkey.lower()
            if lkey in ['profiles', 'alt_profiles', 'series_profiles']:
                # Test the loaded higher-dimension data
                for tframe, lframe in zip(self.testInst.data[dkey],
                                          self.loaded_inst[lkey]):
                    assert np.all(tframe == lframe), "unequal {:s} data".format(
                        dkey)
            else:
                assert np.all(self.testInst[dkey] == self.loaded_inst[lkey])
        return

    def test_load_netcdf4_empty_filenames(self):
        """Test raises ValueError without any filename input."""
        with pytest.raises(ValueError) as verr:
            pysat.utils.load_netcdf4(fnames=None,
                                     pandas_format=self.testInst.pandas_format)

        assert str(verr).find("Must supply a filename/list of filenames") >= 0
        return

    def test_basic_write_and_read_netcdf4_mixed_case_data_format(self):
        """Test basic netCDF4 read/write with mixed case data variables."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)

        # Modify data names in data
        if self.testInst.pandas_format:
            self.testInst.data = self.testInst.data.rename(str.upper,
                                                           axis='columns')
        else:
            self.testInst.data = self.testInst.data.rename(
                {dkey: dkey.upper()
                 for dkey in self.testInst.data.data_vars.keys()})

        self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

        self.loaded_inst, meta = pysat.utils.load_netcdf4(
            outfile, pandas_format=self.testInst.pandas_format)
        self.testInst.data = self.testInst.data.reindex(
            sorted(self.testInst.data.columns), axis=1)
        self.loaded_inst = self.loaded_inst.reindex(
            sorted(self.loaded_inst.columns), axis=1)

        # Check that names are lower case when written
        pysat.utils.testing.assert_lists_equal(self.loaded_inst.columns,
                                               self.testInst.data.columns,
                                               test_case=False)

        # Test the loaded data
        self.eval_loaded_data()
        return

    def test_basic_write_and_read_netcdf4_mixed_case_meta_format(self):
        """Test basic netCDF4 read/write with mixed case metadata variables."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)

        # Modify data and metadata names in data
        self.testInst.meta.data = self.testInst.meta.data.rename(str.upper,
                                                                 axis='index')
        if self.testInst.pandas_format:
            self.testInst.data = self.testInst.data.rename(str.upper,
                                                           axis='columns')
        else:
            self.testInst.data = self.testInst.data.rename(
                {dkey: dkey.upper()
                 for dkey in self.testInst.data.data_vars.keys()})

        self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

        self.loaded_inst, meta = pysat.utils.load_netcdf4(
            outfile, pandas_format=self.testInst.pandas_format)
        self.testInst.data = self.testInst.data.reindex(
            sorted(self.testInst.data.columns), axis=1)
        self.loaded_inst = self.loaded_inst.reindex(
            sorted(self.loaded_inst.columns), axis=1)

        # Check that names are in the expected case
        pysat.utils.testing.assert_lists_equal(self.loaded_inst.columns,
                                               self.testInst.data.columns)

        return

    def test_write_netcdf4_duplicate_variable_names(self):
        """Test netCDF4 writing with duplicate variable names."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst['MLT'] = 1
        with pytest.raises(ValueError) as verr:
            self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

        assert str(verr).find("multiple variables") >= 0
        return

    @pytest.mark.parametrize("wkwargs, lkwargs", [
        ({"zlib": True}, {}), ({}, {}), ({"unlimited_time": False}, {}),
        ({"epoch_name": "Santa"}, {"epoch_name": "Santa"})])
    def test_write_and_read_netcdf4_w_kwargs(self, wkwargs, lkwargs):
        """Test success of writing and reading a netCDF4 file."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst.to_netcdf4(outfile, **wkwargs)

        # Load the data that was created
        lkwargs['pandas_format'] = self.testInst.pandas_format
        self.loaded_inst, meta = pysat.utils.load_netcdf4(outfile, **lkwargs)
        self.testInst.data = self.testInst.data.reindex(
            sorted(self.testInst.data.columns), axis=1)
        self.loaded_inst = self.loaded_inst.reindex(
            sorted(self.loaded_inst.columns), axis=1)

        # Test the loaded data
        self.eval_loaded_data()
        return

    def test_netcdf_prevent_attribute_override(self):
        """Test that attributes will not be overridden by default."""
        self.testInst.load(date=self.stime)

        # Test that `bespoke` attribute is initially missing
        assert not hasattr(self.testInst, 'bespoke')

        # Instrument meta attributes immutable upon load
        assert not self.testInst.meta.mutable
        try:
            self.testInst.meta.bespoke = True
        except AttributeError:
            pass

        # Test that `bespoke` attribute is still missing
        assert not hasattr(self.testInst, 'bespoke')
        return

    def test_netcdf_attribute_override(self):
        """Test that attributes in the netCDF file may be overridden."""
        self.testInst.load(date=self.stime)
        self.testInst.meta.mutable = True
        self.testInst.meta.bespoke = True

        self.testInst.meta.transfer_attributes_to_instrument(self.testInst)

        # Ensure custom meta attribute assigned to instrument
        assert self.testInst.bespoke

        fname = 'output.nc'
        outfile = os.path.join(self.testInst.files.data_path, fname)
        self.testInst.to_netcdf4(outfile)

        _, meta = pysat.utils.load_netcdf4(
            outfile, pandas_format=self.testInst.pandas_format)

        # Custom attribute correctly read from file
        assert meta.bespoke
        return


class TestLoadNetCDF4XArray(object):
    """Unit tests for `load_netcdf4` using xarray data.

    Note
    ----
    Make this a TestLoadNetCDF4 class test as a part of fixing #60.

    """

    def setup(self):
        """Run to set up the test environment."""

        # Store current pysat directory
        self.data_path = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing2d_xarray',
                                         update_files=True, num_samples=100)
        self.stime = pysat.instruments.pysat_testing2d_xarray._test_dates[
            '']['']

        # Create testing directory
        prep_dir(self.testInst)

        # Initalize the loaded data
        self.loaded_inst = None
        return

    def teardown(self):
        """Clean up the test environment."""

        # Clear the attributes with data in them
        del self.loaded_inst, self.testInst, self.stime

        # Reset the pysat parameters
        pysat.params['data_dirs'] = self.data_path

        # Remove the temporary directory
        self.tempdir.cleanup()

        # Clear the directory attributes
        del self.data_path, self.tempdir
        return

    def test_basic_write_and_read_netcdf4_default_format(self):
        """Test basic netCDF4 writing and reading."""
        # Write the output test data
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst.data.to_netcdf(outfile)

        # Load the written data
        self.loaded_inst, meta = pysat.utils.load_netcdf4(
            outfile, pandas_format=self.testInst.pandas_format)

        # Compare the initial and loaded data
        for key in self.testInst.data.data_vars.keys():
            assert(np.all(self.testInst[key] == self.loaded_inst[key]))

        return

    @pytest.mark.parametrize("kwargs,target", [({}, False),
                                               ({'decode_timedelta': False},
                                                False),
                                               ({'decode_timedelta': True},
                                                True)])
    def test_read_netcdf4_with_time_meta_labels(self, kwargs, target):
        """Test that read_netcdf correctly interprets time labels in meta."""
        # Write the output test data
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        # Modify the variable attributes directly before writing to file.
        self.testInst.data['uts'].attrs = {'units': 'seconds'}
        self.testInst.data['mlt'].attrs = {'units': 'minutes'}
        self.testInst.data['slt'].attrs = {'units': 'hours'}
        self.testInst.data.to_netcdf(outfile)

        # Load the written data
        self.loaded_inst, meta = pysat.utils.load_netcdf4(
            outfile, pandas_format=self.testInst.pandas_format, **kwargs)

        # Check that labels pass through as correct type.
        vars = ['uts', 'mlt', 'slt']
        for var in vars:
            val = self.loaded_inst[var].values[0]
            assert isinstance(val, np.timedelta64) == target, \
                "Variable {:} not loaded correctly".format(var)
        return

    def test_load_netcdf4_pandas_3d_error(self):
        """Test load_netcdf4 error with a pandas 3D file."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst.data.to_netcdf(outfile)

        with pytest.raises(ValueError) as verr:
            pysat.utils.load_netcdf4(outfile, epoch_name='time',
                                     pandas_format=True)

        assert str(verr).find("only supports 1D and 2D data in pandas") >= 0
        return


class TestLoadNetCDF42DPandas(TestLoadNetCDF4):
    """Unit tests for `load_netcdf4` using 2d pandas data."""

    def setup(self):
        """Run to set up the test environment."""

        # Store current pysat directory
        self.data_path = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.testInst = pysat.Instrument(platform='pysat', name='testing2d',
                                         update_files=True, num_samples=100)
        self.stime = pysat.instruments.pysat_testing2d._test_dates['']['']

        # Create testing directory
        prep_dir(self.testInst)

        # Initialize the loaded data object
        self.loaded_inst = None
        return

    def teardown(self):
        """Clean up the test environment."""

        # Clear the attributes with data in them
        del self.loaded_inst, self.testInst, self.stime

        # Reset the pysat parameters
        pysat.params['data_dirs'] = self.data_path

        # Remove the temporary directory
        self.tempdir.cleanup()

        # Clear the directory attributes
        del self.data_path, self.tempdir
        return


class TestFmtCols(object):
    """Unit tests for `fmt_output_in_cols`."""

    def setup(self):
        """Run to set up the test environment."""

        self.in_str = np.arange(0, 40, 1).astype(str)
        self.in_kwargs = {"ncols": 5, "max_num": 40, "lpad": None}
        self.out_str = None
        self.filler_row = -1
        self.ncols = None
        self.nrows = None
        self.lpad = len(self.in_str[-1]) + 1

        return

    def teardown(self):
        """Clean up the test environment."""

        del self.in_str, self.in_kwargs, self.out_str, self.filler_row
        del self.ncols, self.nrows, self.lpad
        return

    def eval_output(self):
        """Evaluate the expected number of rows, columns, and fillers."""

        # Test the number of rows
        out_rows = self.out_str.split('\n')[:-1]
        assert len(out_rows) == self.nrows

        # Test the number of columns
        for i, row in enumerate(out_rows):
            split_row = row.split()

            # Test for filler ellipses and standard row length
            if i == self.filler_row:
                assert '...' in split_row
                if i > 0:
                    assert len(split_row) == 1
                    assert len(row) == self.lpad * self.ncols
            else:
                assert len(row) == self.lpad * len(split_row)

                if i == len(out_rows) - 1:
                    assert len(split_row) <= self.ncols
                else:
                    assert len(split_row) == self.ncols

        return

    def test_neg_ncols(self):
        """Test the output if the column number is negative."""
        self.in_kwargs['ncols'] = -5
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        assert len(self.out_str) == 0
        return

    @pytest.mark.parametrize("key,val,raise_type",
                             [("ncols", 0, ZeroDivisionError),
                              ("max_num", -10, ValueError)])
    def test_fmt_raises(self, key, val, raise_type):
        """Test raises appropriate Errors for bad input values."""
        self.in_kwargs[key] = val
        with pytest.raises(raise_type):
            pysat.utils._core.fmt_output_in_cols(self.in_str, **self.in_kwargs)
        return

    @pytest.mark.parametrize("ncol", [(3), (5), (10)])
    def test_ncols(self, ncol):
        """Test the output for different number of columns."""
        # Set the input
        self.in_kwargs['ncols'] = ncol

        # Set the comparison values
        self.ncols = ncol
        self.nrows = int(np.ceil(self.in_kwargs['max_num'] / ncol))

        # Get and test the output
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        self.eval_output()
        return

    @pytest.mark.parametrize("max_num,filler,nrow", [(0, 0, 1), (1, 0, 1),
                                                     (10, 1, 3), (50, -1, 8)])
    def test_max_num(self, max_num, filler, nrow):
        """Test the output for the maximum number of values."""
        # Set the input
        self.in_kwargs['max_num'] = max_num

        # Set the comparison values
        self.filler_row = filler
        self.ncols = self.in_kwargs['ncols']
        self.nrows = nrow

        # Get and test the output
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        self.eval_output()
        return

    @pytest.mark.parametrize("in_pad", [5, 30])
    def test_lpad(self, in_pad):
        """Test the output for different number of columns."""
        # Set the input
        self.in_kwargs['lpad'] = in_pad
        self.ncols = self.in_kwargs['ncols']
        self.nrows = int(np.ceil(self.in_kwargs['max_num'] / self.ncols))

        # Set the comparison values
        self.lpad = in_pad

        # Get and test the output
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        self.eval_output()
        return


class TestAvailableInst(TestWithRegistration):
    """Tests for `available_instruments`, `display_avialable_instruments`."""

    @pytest.mark.parametrize("inst_loc", [None, pysat.instruments])
    @pytest.mark.parametrize("inst_flag, plat_flag",
                             [(None, None), (False, False), (True, True)])
    def test_display_available_instruments(self, inst_loc, inst_flag,
                                           plat_flag, capsys):
        """Test display_available_instruments options."""
        # If using the pysat registry, make sure there is something registered
        if inst_loc is None:
            pysat.utils.registry.register(self.module_names)

        pysat.utils.display_available_instruments(
            inst_loc, show_inst_mod=inst_flag, show_platform_name=plat_flag)

        captured = capsys.readouterr()
        assert captured.out.find("Description") > 0

        if (inst_loc is None and plat_flag is None) or plat_flag:
            assert captured.out.find("Platform") == 0
            assert captured.out.find("Name") > 0

        if (inst_loc is not None and inst_flag is None) or inst_flag:
            assert captured.out.find("Instrument_Module") >= 0

        if inst_loc is not None and inst_flag in [None, True]:
            assert captured.out.find(inst_loc.__name__) > 0

        return

    def test_import_error_in_available_instruments(self):
        """Test handling of import errors in available_instruments."""

        idict = pysat.utils.available_instruments(os.path)

        for platform in idict.keys():
            for name in idict[platform].keys():
                assert 'ERROR' in idict[platform][name]['inst_ids_tags'].keys()
                assert 'ERROR' in idict[platform][name][
                    'inst_ids_tags']['ERROR']
        return


class TestNetworkLock(object):
    """Unit tests for NetworkLock class."""

    def setup(self):
        """Set up the unit test environment."""
        # Create and write a temporary file
        self.fname = 'temp_lock_file.txt'
        with open(self.fname, 'w') as fh:
            fh.write('spam and eggs')
        return

    def teardown(self):
        """Clean up the unit test environment."""
        # Remove the temporary file
        os.remove(self.fname)

        # Delete the test class attributes
        del self.fname
        return

    def test_with_timeout(self):
        """Test network locking with a timeout."""
        # Open the file two times
        with pytest.raises(portalocker.AlreadyLocked):
            with pysat.utils.NetworkLock(self.fname, timeout=0.1):
                with pysat.utils.NetworkLock(self.fname, mode='wb', timeout=0.1,
                                             fail_when_locked=True):
                    pass
        return

    def test_without_timeout(self):
        """Test network locking without a timeout."""
        # Open the file two times
        with pytest.raises(portalocker.LockException):
            with pysat.utils.NetworkLock(self.fname, timeout=None):
                with pysat.utils.NetworkLock(self.fname, timeout=None,
                                             mode='w'):
                    pass
        return

    def test_without_fail(self):
        """Test network locking without file conditions set."""
        # Open the file two times
        with pytest.raises(portalocker.LockException):
            with pysat.utils.NetworkLock(self.fname, timeout=0.1):
                lock = pysat.utils.NetworkLock(self.fname, timeout=0.1)
                lock.acquire(check_interval=0.05, fail_when_locked=False)
        return


class TestGenerateInstList(object):
    """Unit tests for `utils.generate_instrument_list`."""

    def setup(self):
        """Set up the unit test environment before each method."""

        self.user_info = {'pysat_testmodel': {'user': 'GideonNav',
                                              'password': 'pasSWORD!'}}
        self.inst_list = generate_instrument_list(inst_loc=pysat.instruments,
                                                  user_info=self.user_info)
        return

    def teardown(self):
        """Clean up the unit test environment after each method."""

        del self.inst_list, self.user_info
        return

    def test_generate_module_names(self):
        """Test generation of module names."""

        pysat.utils.testing.assert_lists_equal(self.inst_list['names'],
                                               pysat.instruments.__all__)

    @pytest.mark.parametrize("list_name", [('download'), ('no_download')])
    def test_generate_module_list_attributes(self, list_name):
        """Test that each instrument dict has sufficient information."""

        for inst_dict in self.inst_list[list_name]:
            for item in ['inst_module', 'tag', 'inst_id']:
                assert item in inst_dict.keys()
            assert inspect.ismodule(inst_dict['inst_module'])
            assert isinstance(inst_dict['tag'], str)
            assert isinstance(inst_dict['inst_id'], str)
        return

    @pytest.mark.parametrize("list_name,output", [('download', False),
                                                  ('no_download', True)])
    def test_proper_sorting_of_no_download(self, list_name, output):
        """Test that instruments without downloads are sorted properly."""

        tags = [inst['tag'] for inst in self.inst_list[list_name]]
        assert ('no_download' in tags) == output
        return

    def test_user_info_pass_through(self):
        """Test that user info passes through to correct instruments."""

        for inst in self.inst_list['download']:
            # `user_info` should only be in `pysat_testmodel`
            assert (('user_info' in inst.keys())
                    == ('pysat_testmodel' in str(inst['inst_module'])))
            if 'user_info' in inst.keys():
                # User info should be correct
                assert inst['user_info'] == self.user_info['pysat_testmodel']
        for inst in self.inst_list['no_download']:
            # `user_info` should not be in any of these
            assert ('user_info' not in inst.keys())
        return
