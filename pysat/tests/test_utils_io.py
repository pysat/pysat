#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat utility io routines."""

import numpy as np
import os
import tempfile

import netCDF4
import pytest

import pysat
from pysat.utils import testing


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


class TestLoadNetCDF(object):
    """Unit tests for `utils.io.load_netcdf` and `utils.io.inst_to_netcdf`."""

    def setup(self):
        """Set up the test environment."""

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
        if self.testInst.pandas_format:
            keys = self.testInst.data.columns
            new_keys = self.loaded_inst.columns
        else:
            keys = [key for key in self.testInst.data.variables]
            new_keys = [key for key in self.loaded_inst.variables]

        # Test the data values for each variable
        for dkey in keys:
            lkey = dkey.lower()
            if lkey in ['profiles', 'alt_profiles', 'series_profiles']:
                # Test the loaded higher-dimension data
                for tframe, lframe in zip(self.testInst.data[dkey],
                                          self.loaded_inst[dkey]):
                    assert np.all(tframe == lframe), "unequal {:s} data".format(
                        dkey)
            else:
                # Test the standard data structures
                assert np.all(self.testInst[dkey] == self.loaded_inst[dkey])
        return keys, new_keys

    def test_basic_write_and_read_netcdf_mixed_case_data_format(self):
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
            map_keys = {dkey: dkey.upper()
                        for dkey in self.testInst.data.data_vars.keys()}
            self.testInst.data = self.testInst.data.rename(map_keys)

        # Meta case is preserved and has not been altered
        pysat.utils.io.inst_to_netcdf(self.testInst, fname=outfile,
                                      preserve_meta_case=True)

        self.loaded_inst, meta = pysat.utils.io.load_netcdf(
            outfile, pandas_format=self.testInst.pandas_format)

        # Revert data names to meta case
        if self.testInst.pandas_format:
            map_keys = {mkey.upper(): mkey
                        for mkey in self.testInst.meta.keys()}
            self.testInst.data = self.testInst.data.rename(map_keys,
                                                           axis='columns')
        else:
            new_map_keys = {map_keys[mkey]: mkey
                            for mkey in self.testInst.meta.keys()
                            if mkey in map_keys.keys()}
            self.testInst.data = self.testInst.data.rename(new_map_keys)

        # Test the loaded data
        keys, new_keys = self.eval_loaded_data()

        # Check that names are lower case when written
        pysat.utils.testing.assert_lists_equal(keys, new_keys, test_case=False)

        return

    def test_basic_write_and_read_netcdf_mixed_case_meta_format(self):
        """Test basic netCDF4 read/write with mixed case metadata variables."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)

        # Modify data and metadata names in data
        self.testInst.meta.rename(str.upper)
        if self.testInst.pandas_format:
            self.testInst.data = self.testInst.data.rename(str.upper,
                                                           axis='columns')
        else:
            self.testInst.data = self.testInst.data.rename(
                {dkey: dkey.upper()
                 for dkey in self.testInst.data.data_vars.keys()})

        pysat.utils.io.inst_to_netcdf(self.testInst, fname=outfile,
                                      preserve_meta_case=True)

        self.loaded_inst, meta = pysat.utils.io.load_netcdf(
            outfile, pandas_format=self.testInst.pandas_format)
        keys, new_keys = self.eval_loaded_data()

        # Check that names are in the expected case
        pysat.utils.testing.assert_lists_equal(keys, new_keys)

        return

    def test_write_netcdf4_duplicate_variable_names(self):
        """Test netCDF4 writing with duplicate variable names."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        self.testInst['MLT'] = 1
        with pytest.raises(ValueError) as verr:
            pysat.utils.io.inst_to_netcdf(self.testInst, fname=outfile,
                                          preserve_meta_case=True)

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
        pysat.utils.io.inst_to_netcdf(self.testInst, fname=outfile, **wkwargs)

        # Load the data that was created
        lkwargs['pandas_format'] = self.testInst.pandas_format
        self.loaded_inst, meta = pysat.utils.io.load_netcdf(outfile, **lkwargs)

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
        pysat.utils.io.inst_to_netcdf(self.testInst, fname=outfile)

        _, meta = pysat.utils.io.load_netcdf(
            outfile, pandas_format=self.testInst.pandas_format)

        # Custom attribute correctly read from file
        assert meta.bespoke
        return


class TestLoadNetCDFXArray(TestLoadNetCDF):
    """Unit tests for `load_netcdf` using xarray data."""

    def setup(self):
        """Set up the test environment."""

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

    @pytest.mark.parametrize("kwargs,target", [({}, False),
                                               ({'decode_timedelta': False},
                                                False),
                                               ({'decode_timedelta': True},
                                                True)])
    def test_read_netcdf4_with_time_meta_labels(self, kwargs, target):
        """Test that read_netcdf correctly interprets time labels in meta."""
        # Prepare output test data.
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        # Modify the variable attributes directly before writing to file.
        self.testInst.meta['uts'] = {'units': 'seconds'}
        self.testInst.meta['mlt'] = {'units': 'minutes'}
        self.testInst.meta['slt'] = {'units': 'hours'}
        # Write output test data.
        pysat.utils.io.inst_to_netcdf(self.testInst, fname=outfile)

        # Load the written data
        self.loaded_inst, meta = pysat.utils.io.load_netcdf(
            outfile, pandas_format=self.testInst.pandas_format, **kwargs)

        # Check that labels pass through as correct type.
        vars = ['uts', 'mlt', 'slt']
        for var in vars:
            val = self.loaded_inst[var].values[0]
            assert isinstance(val, np.timedelta64) == target, \
                "Variable {:} not loaded correctly".format(var)
        return

    def test_load_netcdf_pandas_3d_error(self):
        """Test load_netcdf error with a pandas 3D file."""
        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        pysat.utils.io.inst_to_netcdf(self.testInst, fname=outfile)

        with pytest.raises(ValueError) as verr:
            pysat.utils.io.load_netcdf(outfile, epoch_name='time',
                                       pandas_format=True)

        assert str(verr).find("only supports 1D and 2D data in pandas") >= 0
        return


class TestLoadNetCDF2DPandas(TestLoadNetCDF):
    """Unit tests for `load_netcdf` using 2d pandas data."""

    def setup(self):
        """Set up the test environment."""

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


class TestNetCDF4Integration(object):
    """Integration tests for netCDF4 I/O."""

    def setup_class(self):
        """Initialize the testing setup once before all tests are run."""

        # Use a temporary directory so that the user's setup is not altered.
        self.tempdir = tempfile.TemporaryDirectory()
        self.saved_path = pysat.params['data_dirs']
        pysat.params['data_dirs'] = self.tempdir.name
        return

    def teardown_class(self):
        """Clean up downloaded files and parameters from tests."""

        pysat.params['data_dirs'] = self.saved_path
        self.tempdir.cleanup()
        del self.saved_path, self.tempdir
        return

    @pytest.mark.parametrize('use_method', [True, False])
    def test_nan_metadata_filtered_netcdf4(self, use_method):
        """Test that metadata set to NaN is excluded from netCDF output.

        Parameters
        ----------
        use_method : bool
            Use meta method and `export_nan` kwarg if True, use defaults
            if False

        """
        # TODO(#585): consider moving to class with netCDF tests

        # Create an instrument object that has a meta with some
        # variables allowed to be nan within metadata when exporting
        self.testInst = pysat.Instrument('pysat', 'testing')
        stime = self.testInst.inst_module._test_dates['']['']
        self.testInst.load(date=stime)

        # Save the meta object and data variable list
        self.meta = self.testInst.meta

        # Create new variable
        self.testInst['test_nan_variable'] = 1.0

        # Assign additional metadata
        self.testInst.meta['test_nan_variable'] = {'test_nan_export': np.nan}

        # Get the export kwarg and set the evaluation data
        if use_method:
            # Keep a non-standard set of NaN meta labels in the file
            present = self.testInst.meta._export_nan
            missing = [present.pop()]
            present.append('test_nan_export')
            export_nan = list(present)
        else:
            # Keep the standard set of NaN meta labels in the file
            export_nan = None
            present = self.testInst.meta._export_nan
            missing = ['test_nan_export']

        # Write the file
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.to_netcdf4(outfile, export_nan=export_nan)

        # Load file back and test metadata is as expected
        with netCDF4.Dataset(outfile) as open_f:
            test_vars = open_f['test_nan_variable'].ncattrs()

        testing.assert_list_contains(present, test_vars)

        for mvar in missing:
            assert mvar not in test_vars, \
                '{:} was written to the netCDF file'.format(mvar.__repr__())

        return
