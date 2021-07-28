#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat utils core functions
"""

import contextlib
from io import StringIO
from importlib import reload
import numpy as np
import os
import portalocker
import pytest
import shutil
import tempfile

import pysat
from pysat.tests.registration_test_class import TestWithRegistration
from pysat.utils import testing


def prep_dir(inst=None):
    """Prepare the directory to provide netCDF export file support

    Parameters
    ----------
    inst : pysat.Instrument or NoneType
        Instrument class object or None to use 'pysat_testing.py' (default=None)

    """
    if inst is None:
        inst = pysat.Instrument(platform='pysat', name='testing')

    # Create data directories
    try:
        os.makedirs(inst.files.data_path)
    except OSError:
        pass

    return


def remove_files(inst):
    """Remove files associated with a pysat Instrument

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


class TestCIonly():
    """Tests where we mess with local settings.

    Note
    ----
    These only run in CI environments such as GitHub Actions to avoid breaking
    an end user's setup

    """

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.ci_env = (os.environ.get('CI') == 'true')
        if not self.ci_env:
            pytest.skip("Skipping local tests to avoid breaking user setup")

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.ci_env

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


class TestScaleUnits():
    """Unit tests for `scale_units`."""
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.deg_units = ["deg", "degree", "degrees", "rad", "radian",
                          "radians", "h", "hr", "hrs", "hours"]
        self.dist_units = ["m", "km", "cm"]
        self.vel_units = ["m/s", "cm/s", "km/s", 'm s$^{-1}$', 'cm s$^{-1}$',
                          'km s$^{-1}$', 'm s-1', 'cm s-1', 'km s-1']
        self.scale = 0.0

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.deg_units, self.dist_units, self.vel_units, self.scale

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
        return

    def test_scale_units_same(self):
        """ Test scale_units when both units are the same."""

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
            self.eval_unit_scale(out_unit, 'distance')
        return

    @pytest.mark.parametrize("in_args,err_msg", [
        (['happy', 'm'], 'output unit'), (['m', 'happy'], 'input unit'),
        (['m', 'm/s'], 'unknown units'), (['happy', 'sad'], 'unknown units')])
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


class TestListify():
    """Unit tests for the `listify` function."""

    @pytest.mark.parametrize('iterable,nitem', [
        ('test', 1), (['test'], 1), ([[['test']]], 1), ([[[['test']]]], 1),
        ([['test', 'test']], 2), ([['test', 'test'], ['test', 'test']], 4),
        ([], 0), ([[]], 0)])
    def test_listify_list_string_inputs(self, iterable, nitem):
        """ Test listify with various list levels of a string."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = ['test' for i in range(nitem)]
        testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('iterable', [np.nan, np.full((1, 1), np.nan),
                                          np.full((2, 2), np.nan),
                                          np.full((3, 3, 3), np.nan)])
    def test_listify_nan_arrays(self, iterable):
        """ Test listify with various np.arrays of NaNs."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = [np.nan
                        for i in range(int(np.product(np.shape(iterable))))]
        testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('iterable', [1, np.full((1, 1), 1),
                                          np.full((2, 2), 1),
                                          np.full((3, 3, 3), 1)])
    def test_listify_int_arrays(self, iterable):
        """ Test listify with various np.arrays of NaNs."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = [1 for i in range(int(np.product(np.shape(iterable))))]
        testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('iterable', [
        pysat.Instrument(), np.full((1, 1), pysat.Instrument()),
        np.full((2, 2), pysat.Instrument()),
        np.full((3, 3, 3), pysat.Instrument())])
    def test_listify_class_arrays(self, iterable):
        """ Test listify with various np.arrays of NaNs."""

        new_iterable = pysat.utils.listify(iterable)
        tst_iterable = [pysat.Instrument()
                        for i in range(int(np.product(np.shape(iterable))))]
        testing.assert_lists_equal(new_iterable, tst_iterable)
        return


class TestBasicNetCDF4():
    """Unit tests for `load_netcdf4`."""
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Store current pysat directory
        self.data_path = pysat.params['data_dirs']

        # Create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=100, update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.testInst.pandas_format = True

        # Create testing directory
        prep_dir(self.testInst)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.params['data_dirs'] = self.data_path
        self.tempdir.cleanup()

        del self.testInst, self.stime

    def test_load_netcdf4_empty_filenames(self):
        """Test raises ValueError without any filename input."""
        with pytest.raises(ValueError) as verr:
            pysat.utils.load_netcdf4(fnames=None)

        assert str(verr).find("Must supply a filename/list of filenames") >= 0
        return

    @pytest.mark.parametrize('unlimited', [True, False])
    def test_basic_write_and_read_netcdf4_default_format(self, unlimited):
        """Test writing and loading netcdf4 file, with/out unlimited time dim.
        """
        # Create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst.to_netcdf4(outfile, unlimited_time=unlimited)

        loaded_inst, meta = pysat.utils.load_netcdf4(
            outfile, pandas_format=self.testInst.pandas_format)
        self.testInst.data = self.testInst.data.reindex(
            sorted(self.testInst.data.columns), axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)

        for key in self.testInst.data.columns:
            assert(np.all(self.testInst[key] == loaded_inst[key]))

        return

    def test_basic_write_and_read_netcdf4_mixed_case_format(self):
        """ Test basic netCDF4 read/write with mixed case data variables.
        """
        # Create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)

        # Modify data names in data
        original = sorted(self.testInst.data.columns)
        self.testInst.data = self.testInst.data.rename(str.upper,
                                                       axis='columns')
        self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)
        self.testInst.data = self.testInst.data.reindex(
            sorted(self.testInst.data.columns), axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)

        # Check that names are lower case when written
        assert(np.all(original == loaded_inst.columns))

        for key in self.testInst.data.columns:
            assert(np.all(self.testInst[key] == loaded_inst[key.lower()]))

        # Modify metadata names in data
        self.testInst.meta.data = self.testInst.meta.data.rename(str.upper,
                                                                 axis='index')
        # Write file
        self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

        # Load file
        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)

        # Check that names are upper case when written
        testing.assert_lists_equal(sorted(self.testInst.data.columns),
                                   sorted(loaded_inst.columns))
        return

    def test_write_netcdf4_duplicate_variable_names(self):
        """ Test netCDF4 writing with duplicate variable names."""
        # Create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst['MLT'] = 1
        with pytest.raises(ValueError) as verr:
            self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

        assert str(verr).find("Metadata across filenames is not the same") >= 0
        return

    @pytest.mark.parametrize("in_kwargs", [{"zlib": True},
                                           {"epoch_name": "Santa"}])
    def test_write_and_read_netcdf4_default_format_w_kwargs(self, in_kwargs):
        """Test success of writing and reading a compressed netCDF4 file."""
        # Create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst.to_netcdf4(outfile, **in_kwargs)

        # Load the data that was created
        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)
        self.testInst.data = self.testInst.data.reindex(
            sorted(self.testInst.data.columns), axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)

        # Test that the written and loaded data matches the initial data
        for key in self.testInst.data.columns:
            assert (np.all(self.testInst[key] == loaded_inst[key]))

        return

    def test_write_and_read_netcdf4_default_format_higher_order(self):
        # create a bunch of files by year and doy
        test_inst = pysat.Instrument('pysat', 'testing2d', update_files=True)
        prep_dir(test_inst)
        outfile = os.path.join(test_inst.files.data_path, 'pysat_test_ncdf.nc')
        test_inst.load(2009, 1)
        test_inst.to_netcdf4(outfile)
        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)
        test_inst.data = test_inst.data.reindex(sorted(test_inst.data.columns),
                                                axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)
        prep_dir(test_inst)

        # test Series of DataFrames
        test_list = []
        for frame1, frame2 in zip(test_inst.data['profiles'],
                                  loaded_inst['profiles']):
            test_list.append(np.all((frame1 == frame2).all()))
        loaded_inst.drop('profiles', inplace=True, axis=1)
        test_inst.data.drop('profiles', inplace=True, axis=1)

        # second series of frames
        for frame1, frame2 in zip(test_inst.data['alt_profiles'],
                                  loaded_inst['alt_profiles']):
            test_list.append(np.all((frame1 == frame2).all()))
        loaded_inst.drop('alt_profiles', inplace=True, axis=1)
        test_inst.data.drop('alt_profiles', inplace=True, axis=1)

        # check series of series
        for frame1, frame2 in zip(test_inst.data['series_profiles'],
                                  loaded_inst['series_profiles']):
            test_list.append(np.all((frame1 == frame2).all()))

        loaded_inst.drop('series_profiles', inplace=True, axis=1)
        test_inst.data.drop('series_profiles', inplace=True, axis=1)

        assert(np.all((test_inst.data == loaded_inst).all()))
        assert np.all(test_list)

    def test_write_and_read_netcdf4_default_format_higher_order_w_zlib(self):
        # create a bunch of files by year and doy
        test_inst = pysat.Instrument('pysat', 'testing2d', update_files=True)
        prep_dir(test_inst)
        outfile = os.path.join(test_inst.files.data_path, 'pysat_test_ncdf.nc')
        test_inst.load(2009, 1)
        test_inst.to_netcdf4(outfile, zlib=True)
        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)
        test_inst.data = test_inst.data.reindex(sorted(test_inst.data.columns),
                                                axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)
        prep_dir(test_inst)

        # test Series of DataFrames
        test_list = []
        for frame1, frame2 in zip(test_inst.data['profiles'],
                                  loaded_inst['profiles']):
            test_list.append(np.all((frame1 == frame2).all()))
        loaded_inst.drop('profiles', inplace=True, axis=1)
        test_inst.data.drop('profiles', inplace=True, axis=1)

        # second series of frames
        for frame1, frame2 in zip(test_inst.data['alt_profiles'],
                                  loaded_inst['alt_profiles']):
            test_list.append(np.all((frame1 == frame2).all()))
        loaded_inst.drop('alt_profiles', inplace=True, axis=1)
        test_inst.data.drop('alt_profiles', inplace=True, axis=1)

        # check series of series
        for frame1, frame2 in zip(test_inst.data['series_profiles'],
                                  loaded_inst['series_profiles']):
            test_list.append(np.all((frame1 == frame2).all()))
        loaded_inst.drop('series_profiles', inplace=True, axis=1)
        test_inst.data.drop('series_profiles', inplace=True, axis=1)

        assert (np.all((test_inst.data == loaded_inst).all()))
        assert np.all(test_list)

    def test_netcdf_prevent_attribute_override(self):
        """Test that attributes will not be overridden by default
        """
        self.testInst.load(date=self.stime)

        try:
            assert self.testInst.bespoke  # should raise
        except AttributeError:
            pass

        # instrument meta attributes immutable upon load
        assert not self.testInst.meta.mutable
        try:
            self.testInst.meta.bespoke = True
        except AttributeError:
            pass

    def test_netcdf_attribute_override(self):
        """Test that attributes in netcdf file may be overridden
        """
        self.testInst.load(date=self.stime)
        self.testInst.meta.mutable = True
        self.testInst.meta.bespoke = True

        self.testInst.meta.transfer_attributes_to_instrument(self.testInst)

        # Ensure custom meta attribute assigned to instrument
        assert self.testInst.bespoke

        fname = 'output.nc'
        outfile = os.path.join(self.testInst.files.data_path, fname)
        self.testInst.to_netcdf4(outfile)

        data, meta = pysat.utils.load_netcdf4(outfile)

        # Custom attribute correctly read from file
        assert meta.bespoke


class TestBasicNetCDF4xarray():
    """NOTE: combine with above class as part of #60"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.params['data_dirs']

        # create temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        pysat.params['data_dirs'] = [self.tempdir.name]

        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing2d_xarray',
                                         update_files=True,
                                         num_samples=100)
        self.stime = pysat.instruments.pysat_testing2d_xarray._test_dates[
            '']['']

        # create testing directory
        prep_dir(self.testInst)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        # remove_files(self.testInst)
        pysat.params['data_dirs'] = self.data_path
        self.tempdir.cleanup()
        del self.testInst, self.stime

    def test_basic_write_and_read_netcdf4_default_format(self):
        """ Test basic netCDF4 writing and reading
        """
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst.data.attrs['new_attr'] = 1
        self.testInst.data.to_netcdf(outfile)

        loaded_inst, meta = pysat.utils.load_netcdf4(
            outfile, pandas_format=self.testInst.pandas_format)
        keys = self.testInst.data.data_vars.keys()

        for key in keys:
            assert(np.all(self.testInst[key] == loaded_inst[key]))
        assert meta.new_attr == 1

    def test_load_netcdf4_pandas_3d_error(self):
        """ Test load_netcdf4 error with a pandas 3D file
        """
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst.data.attrs['new_attr'] = 1
        self.testInst.data.to_netcdf(outfile)

        with pytest.raises(ValueError):
            loaded_inst, meta = pysat.utils.load_netcdf4(
                outfile, epoch_name='time', pandas_format=True)


class TestFmtCols():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.in_str = np.arange(0, 40, 1).astype(str)
        self.in_kwargs = {"ncols": 5, "max_num": 40, "lpad": None}
        self.out_str = None
        self.filler_row = -1
        self.ncols = None
        self.nrows = None
        self.lpad = len(self.in_str[-1]) + 1

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.in_str, self.in_kwargs, self.out_str, self.filler_row
        del self.ncols, self.nrows, self.lpad

    def test_output(self):
        """ Test for the expected number of rows, columns, and fillers
        """
        if self.out_str is None and self.ncols is None and self.nrows is None:
            return

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
        """ Test the output if the column number is negative
        """
        self.in_kwargs['ncols'] = -5
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        assert len(self.out_str) == 0

    @pytest.mark.parametrize("key,val,raise_type",
                             [("ncols", 0, ZeroDivisionError),
                              ("max_num", -10, ValueError)])
    def test_fmt_raises(self, key, val, raise_type):
        self.in_kwargs[key] = val
        with pytest.raises(raise_type):
            pysat.utils._core.fmt_output_in_cols(self.in_str, **self.in_kwargs)

    @pytest.mark.parametrize("ncol", [(3), (5), (10)])
    def test_ncols(self, ncol):
        """ Test the output for different number of columns
        """
        # Set the input
        self.in_kwargs['ncols'] = ncol

        # Set the comparison values
        self.ncols = ncol
        self.nrows = int(np.ceil(self.in_kwargs['max_num'] / ncol))

        # Get and test the output
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        self.test_output()

    @pytest.mark.parametrize("max_num,filler,nrow", [(0, 0, 1), (1, 0, 1),
                                                     (10, 1, 3), (50, -1, 8)])
    def test_max_num(self, max_num, filler, nrow):
        """ Test the output for the maximum number of values
        """
        # Set the input
        self.in_kwargs['max_num'] = max_num

        # Set the comparison values
        self.filler_row = filler
        self.ncols = self.in_kwargs['ncols']
        self.nrows = nrow

        # Get and test the output
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        self.test_output()

    @pytest.mark.parametrize("in_pad", [5, 30])
    def test_lpad(self, in_pad):
        """ Test the output for different number of columns
        """
        # Set the input
        self.in_kwargs['lpad'] = in_pad
        self.ncols = self.in_kwargs['ncols']
        self.nrows = int(np.ceil(self.in_kwargs['max_num'] / self.ncols))

        # Set the comparison values
        self.lpad = in_pad

        # Get and test the output
        self.out_str = pysat.utils._core.fmt_output_in_cols(self.in_str,
                                                            **self.in_kwargs)
        self.test_output()


class TestAvailableInst(TestWithRegistration):

    @pytest.mark.parametrize("inst_loc", [None, pysat.instruments])
    @pytest.mark.parametrize("inst_flag, plat_flag",
                             [(None, None), (False, False), (True, True)])
    def test_display_available_instruments(self, inst_loc, inst_flag,
                                           plat_flag):
        """Test display_available_instruments options
        """
        # If using the pysat registry, make sure there is something registered
        if inst_loc is None:
            pysat.utils.registry.register(self.module_names)

        # Initialize the STDOUT stream
        new_stdout = StringIO()

        with contextlib.redirect_stdout(new_stdout):
            pysat.utils.display_available_instruments(
                inst_loc, show_inst_mod=inst_flag, show_platform_name=plat_flag)

        out = new_stdout.getvalue()
        assert out.find("Description") > 0

        if (inst_loc is None and plat_flag is None) or plat_flag:
            assert out.find("Platform") == 0
            assert out.find("Name") > 0

        if (inst_loc is not None and inst_flag is None) or inst_flag:
            assert out.find("Instrument_Module") >= 0

        if inst_loc is not None and inst_flag in [None, True]:
            assert out.find(inst_loc.__name__) > 0

        return

    def test_import_error_in_available_instruments(self):
        """ Test handling of import errors in available_instruments
        """

        idict = pysat.utils.available_instruments(os.path)

        for platform in idict.keys():
            for name in idict[platform].keys():
                assert 'ERROR' in idict[platform][name]['inst_ids_tags'].keys()
                assert 'ERROR' in idict[platform][name][
                    'inst_ids_tags']['ERROR']
        return


class TestNetworkLock():
    def setup(self):
        self.fname = 'temp_lock_file.txt'
        with open(self.fname, 'w') as fh:
            fh.write('spam and eggs')

    def teardown(self):
        os.remove(self.fname)

    def test_with_timeout(self):
        # Open the file 2 times
        with pytest.raises(portalocker.AlreadyLocked):
            with pysat.utils.NetworkLock(self.fname, timeout=0.1):
                with pysat.utils.NetworkLock(self.fname, mode='wb', timeout=0.1,
                                             fail_when_locked=True):
                    pass

    def test_without_timeout(self):
        # Open the file 2 times
        with pytest.raises(portalocker.LockException):
            with pysat.utils.NetworkLock(self.fname, timeout=None):
                with pysat.utils.NetworkLock(self.fname, timeout=None,
                                             mode='w'):
                    pass

    def test_without_fail(self):
        # Open the file 2 times
        with pytest.raises(portalocker.LockException):
            with pysat.utils.NetworkLock(self.fname, timeout=0.1):
                lock = pysat.utils.NetworkLock(self.fname, timeout=0.1)
                lock.acquire(check_interval=0.05, fail_when_locked=False)
