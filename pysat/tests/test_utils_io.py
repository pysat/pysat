#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat utility io routines."""

import datetime as dt
import logging
import numpy as np
import os
import tempfile
import warnings

import netCDF4
import pytest

import pysat
from pysat.utils import io
from pysat.utils import testing


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
        testing.prep_dir(self.testInst.files.data_path)

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
        io.inst_to_netcdf(self.testInst, fname=outfile, preserve_meta_case=True)

        self.loaded_inst, meta = io.load_netcdf(
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

        io.inst_to_netcdf(self.testInst, fname=outfile, preserve_meta_case=True)

        self.loaded_inst, meta = io.load_netcdf(
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
            io.inst_to_netcdf(self.testInst, fname=outfile,
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
        io.inst_to_netcdf(self.testInst, fname=outfile, **wkwargs)

        # Load the data that was created
        lkwargs['pandas_format'] = self.testInst.pandas_format
        self.loaded_inst, meta = io.load_netcdf(outfile, **lkwargs)

        # Test the loaded data
        self.eval_loaded_data()
        return

    @pytest.mark.parametrize("kwargs, target", [
        ({}, dt.timedelta(seconds=1)),
        ({'epoch_unit': 'ns'}, dt.timedelta(microseconds=1)),
        ({'epoch_origin': dt.datetime(1980, 1, 6)}, dt.timedelta(seconds=1)),
        ({'epoch_unit': 'ns', 'epoch_origin': dt.datetime(1980, 1, 6)},
         dt.timedelta(microseconds=1))])
    def test_read_netcdf4_w_epoch_kwargs(self, kwargs, target):
        """Test success of writing and reading a netCDF4 file.

        Parameters
        ----------
        kwargs : dict
            Optional kwargs to input into `load_netcdf`. Allows the epoch
            calculation to use custom origin and units.
        target : dt.timedelta
            Expected interpretation of 1 sec of time in loaded data when a given
            epoch unit is specified.  Default unit for pds.to_datetime is 1 ms.

        """

        # TODO(#947) Expand to xarray objects once functionality is updated
        if not self.testInst.pandas_format:
            pytest.skip('Not yet implemented for xarray')

        # Create a bunch of files by year and doy
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(date=self.stime)
        io.inst_to_netcdf(self.testInst, fname=outfile)

        # Load the data that was created
        kwargs['pandas_format'] = self.testInst.pandas_format
        self.loaded_inst, meta = io.load_netcdf(outfile, **kwargs)

        # Check that the step size is expected
        default_delta = (self.testInst.index[1] - self.testInst.index[0])
        loaded_delta = (self.loaded_inst.index[1] - self.loaded_inst.index[0])
        # Ratio of step_sizes should equal ratio of interpreted units
        assert ((default_delta / loaded_delta)
                == (dt.timedelta(seconds=1) / target))

        unix_origin = dt.datetime(1970, 1, 1)
        if 'epoch_origin' in kwargs.keys():
            file_origin = kwargs['epoch_origin']
        else:
            # Use unix origin as default
            file_origin = unix_origin

        # Find distance from origin
        default_uts = (self.testInst.index[0] - unix_origin).total_seconds()
        loaded_uts = (self.loaded_inst.index[0] - file_origin).total_seconds()
        # Ratio of distances should equal ratio of interpreted units
        assert (default_uts / loaded_uts) == (dt.timedelta(seconds=1) / target)
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
        io.inst_to_netcdf(self.testInst, fname=outfile)

        _, meta = io.load_netcdf(
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
        testing.prep_dir(self.testInst.files.data_path)

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
        io.inst_to_netcdf(self.testInst, fname=outfile)

        # Load the written data
        self.loaded_inst, meta = io.load_netcdf(
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
        io.inst_to_netcdf(self.testInst, fname=outfile)

        with pytest.raises(ValueError) as verr:
            io.load_netcdf(outfile, epoch_name='time', pandas_format=True)

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
        testing.prep_dir(self.testInst.files.data_path)

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
    """Integration tests for the netCDF4 I/O utils."""

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

    def setup(self):
        """Create a testing environment."""

        # Create an instrument object that has a meta with some
        # variables allowed to be nan within metadata when exporting
        self.testInst = pysat.Instrument('pysat', 'testing')
        self.testInst.load(date=self.testInst.inst_module._test_dates[''][''])

        return

    def teardown(self):
        """Clean up the test environment."""

        del self.testInst
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
        testing.prep_dir(self.testInst.files.data_path)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.to_netcdf4(outfile, export_nan=export_nan)

        # Load file back and test metadata is as expected
        with netCDF4.Dataset(outfile) as open_f:
            test_vars = open_f['test_nan_variable'].ncattrs()

        testing.assert_list_contains(present, test_vars)

        for mvar in missing:
            assert mvar not in test_vars, \
                '{:} was written to the netCDF file'.format(repr(mvar))

        return

    @pytest.mark.parametrize("remove", [True, False])
    @pytest.mark.parametrize("check_type", [None, ['value_max']])
    @pytest.mark.parametrize("export_nan", [None, ['fill']])
    @pytest.mark.parametrize("dvar", ["uts", "string_dummy", "unicode_dummy",
                                      "int8_dummy", "int64_dummy"])
    def test_filter_netcdf4_metadata(self, remove, check_type, export_nan,
                                     dvar):
        """Test `io.test_filter_netcdf4_metadata`.

        Parameters
        ----------
        remove : bool
            Values for the `remove` kwarg
        check_type : list or NoneType
            Values for the `check_type` kwarg
        export_nan : list or NoneType
            Values for the `export_nan` kwarg
        dval : str
            Data variable for different test Instrument values to be tested

        """

        # Set the input parameters
        mdict = self.testInst.meta[dvar].to_dict()

        if dvar.find('int8') >= 0:
            data_type = bool
        else:
            data_type = type(self.testInst[dvar][0])

        # Get the filtered output
        with warnings.catch_warnings(record=True) as war:
            fdict = io.filter_netcdf4_metadata(self.testInst, mdict, data_type,
                                               export_nan=export_nan,
                                               remove=remove,
                                               check_type=check_type)

        # Evaluate the warnings
        if len(war) > 0:
            assert data_type == str and not remove, \
                "unexpected warning(s). First (of {:d}) warning: {:s}".format(
                    len(war), war[0].message)

            # Test the warning
            testing.eval_warnings(war, ["Unable to cast"],
                                  warn_type=UserWarning)

        # Prepare the input variables to test the filtered output
        if export_nan is None:
            export_nan = []

        if check_type is None:
            check_type = []

        # Test the filtered output
        for mkey in mdict.keys():
            if mkey not in fdict.keys():
                # Determine if the data is NaN
                try:
                    is_nan = np.isnan(mdict[mkey])
                except TypeError:
                    is_nan = False

                if mkey in check_type:
                    assert not isinstance(mdict[mkey], data_type), \
                        "{:} is a {:}, it shouldn't have been removed".format(
                            repr(mkey), repr(data_type))
                    assert (remove | (not remove & len(war) > 0)
                            | ((mdict[mkey] is None) | is_nan)), \
                        "{:} value {:} should have been recast".format(
                            repr(mkey), repr(mdict[mkey]))
                else:

                    assert ((mdict[mkey] is None) | is_nan), \
                        "{:} is not a fill value: {:}".format(repr(mkey),
                                                              repr(mdict[mkey]))

                    assert mkey not in export_nan, \
                        "{:} should have been exported".format(repr(mkey))
            else:
                if mkey in export_nan and np.isnan(mdict[mkey]):
                    assert np.isnan(fdict[mkey])
                else:
                    assert fdict[mkey] == mdict[mkey], \
                        "meta data {:} changed".format(repr(mkey))

        return

    @pytest.mark.parametrize('missing', [True, False])
    def test_add_netcdf4_standards_to_meta(self, caplog, missing):
        """Test for simplified SPDF ISTP/IACG NetCDF standards after update.

        Parameters
        ----------
        missing : bool
            If True, remove data from Meta to create missing data

        """

        # Update the test metadata
        if missing:
            drop_var = self.testInst.variables[0]
            self.testInst.meta.drop(drop_var)

        # Save the un-updated metadata
        init_meta = self.testInst.meta.copy()

        # Test the initial meta data for missing Epoch time
        assert self.testInst.index.name not in init_meta

        # Update the metadata
        with caplog.at_level(logging.INFO, logger='pysat'):
            io.add_netcdf4_standards_to_meta(self.testInst,
                                             self.testInst.index.name)

        # Test the logging message
        captured = caplog.text
        if missing:
            assert captured.find('Unable to find MetaData for {:s}'.format(
                drop_var)) >= 0
        else:
            assert len(captured) == 0

        # Test the metadata update
        new_labels = ['Format', 'Var_Type', 'Time_Base', 'Time_Scale',
                      'MonoTon', 'Depend_0', 'Display_Type']
        assert init_meta != self.testInst.meta
        assert self.testInst.index.name in self.testInst.meta
        for var in init_meta.keys():
            for label in new_labels:
                assert label not in init_meta[var]
                assert label in self.testInst.meta[var]

        return

    def test_add_netcdf4_standards_to_ho_meta(self):
        """Test for SPDF ISTP/IACG NetCDF standards with HO data."""

        # Reset the test instrument
        self.testInst = pysat.Instrument('pysat', 'testing2d')
        self.testInst.load(
            date=pysat.instruments.pysat_testing2d._test_dates[''][''])

        # Save the un-updated metadata
        init_meta = self.testInst.meta.copy()

        # Test the initial meta data for missing Epoch time
        assert self.testInst.index.name not in init_meta

        # Update the metadata
        io.add_netcdf4_standards_to_meta(self.testInst,
                                         self.testInst.index.name)

        # Test the metadata update
        new_labels = ['Format', 'Var_Type', 'Time_Base', 'Time_Scale',
                      'MonoTon', 'Depend_0', 'Depend_1', 'Display_Type']
        assert init_meta != self.testInst.meta
        assert self.testInst.index.name in self.testInst.meta
        for var in init_meta.keys():
            for label in new_labels:
                assert label not in init_meta[var]
                assert label in self.testInst.meta[var]

            assert 'Depend_1' not in init_meta[var]
            if init_meta[var].children is None:
                assert np.isnan(self.testInst.meta[var, 'Depend_1'])
            else:
                assert self.testInst.meta[
                    var, 'Depend_1'] in self.testInst.variables

        return


class TestXarrayIO(object):
    """Unit tests for the Xarray I/O utilities."""

    def setup(self):
        """Create a testing environment."""

        # Create an instrument object that has a meta with some
        # variables allowed to be nan within metadata when exporting
        self.testInst = pysat.Instrument('pysat', 'testing_xarray')
        self.testInst.load(date=self.testInst.inst_module._test_dates[''][''])

        return

    def teardown(self):
        """Clean up the test environment."""

        del self.testInst
        return

    @pytest.mark.parametrize('export_nan', [None, ['fill']])
    def test_pysat_meta_to_xarray_attr(self, export_nan):
        """Test the successful transfer of Meta data to an xarray Dataset.

        Parameters
        ----------
        export_nan : list or NoneType
            Possible values for the `export_nan` kwarg.

        """

        # Ensure there is no meta data attached to the Dataset at this point
        for var in self.testInst.variables:
            assert len(self.testInst.data[var].attrs.keys()) == 0, \
                "Dataset has metadata for {:}".format(var)

        # Run the update routine
        meta = self.testInst.meta
        io.pysat_meta_to_xarray_attr(self.testInst.data, meta, export_nan)

        # Test that the metadata was added
        if export_nan is None:
            export_nan = []

        for var in self.testInst.data.data_vars.keys():
            for label in meta.attrs():
                mval = meta[var, label]
                if label in self.testInst.data[var].attrs.keys():
                    try:
                        assert self.testInst.data[var].attrs[label] == mval
                    except AssertionError:
                        assert np.isnan(self.testInst.data[var].attrs[label]) \
                            & np.isnan(mval), \
                            "unequal meta data for {:}, {:}".format(repr(var),
                                                                    repr(label))
                        assert label in export_nan, \
                            "should not attach a label with a fill value"
                else:
                    assert label not in export_nan, "did not attach {:}".format(
                        repr(label))

                    try:
                        dval = meta.labels.default_values_from_type(type(mval))
                        assert mval == dval
                    except (AssertionError, TypeError):
                        dval = meta.labels.default_values_from_type(float)
                        try:
                            nan_bool = np.isnan(dval) & np.isnan(mval)
                            assert nan_bool, \
                                "didn't transfer meta data for {:}, {:}".format(
                                    repr(var), repr(label))
                        except TypeError:
                            raise AssertionError(
                                'unequal meta data for {:}, {:}'.format(
                                    repr(var), repr(label)))
        return
