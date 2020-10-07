"""
tests the pysat utils area
"""
from importlib import reload
import numpy as np
import os
import shutil
import tempfile

import pytest

import pysat


# ----------------------------------
# test netCDF export file support
def prep_dir(inst=None):

    if inst is None:
        inst = pysat.Instrument(platform='pysat', name='testing')
    # create data directories
    try:
        os.makedirs(inst.files.data_path)
    except OSError:
        pass


def remove_files(inst):
    # remove any files
    temp_dir = inst.files.data_path
    for the_file in os.listdir(temp_dir):
        if (the_file == 'pysat_test_ncdf.nc'):
            file_path = os.path.join(temp_dir, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.utils.set_data_dir(self.data_path)

    #######################
    # test pysat data dir options
    def test_set_data_dir(self):
        """update data_dir"""
        pysat.utils.set_data_dir('.')
        check1 = (pysat.data_dir == '.')

        # Check if next load of pysat remembers the change
        pysat._files = reload(pysat._files)
        pysat._instrument = reload(pysat._instrument)
        reload(pysat)
        check2 = (pysat.data_dir == '.')

        assert check1 & check2

    def test_set_data_dir_no_store(self):
        """update data_dir without storing"""
        pysat.utils.set_data_dir('.', store=False)
        assert (pysat.data_dir == '.')

        # Check if next load of pysat remembers old settings
        pysat._files = reload(pysat._files)
        pysat._instrument = reload(pysat._instrument)
        reload(pysat)
        assert (pysat.data_dir == self.data_path)

    def test_set_data_dir_wrong_path(self):
        """update data_dir with an invalid path"""
        with pytest.raises(ValueError):
            pysat.utils.set_data_dir('not_a_directory', store=False)

    def test_set_data_dir_bad_directory(self):
        with pytest.raises(ValueError) as excinfo:
            pysat.utils.set_data_dir('/fake/directory/path', store=False)
        assert str(excinfo.value).find('does not lead to a valid dir') >= 0


class TestCIonly():
    """Tests where we mess with local settings.
    These only run in CI environments such as Travis and Appveyor to avoid
    breaking an end user's setup
    """

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.ci_env = (os.environ.get('TRAVIS') == 'true')
        if not self.ci_env:
            pytest.skip("Skipping local tests to avoid breaking user setup")

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.ci_env

    def test_initial_pysat_load(self, capsys):
        """Ensure inital load routines work"""

        # Move settings directory to simulate first load after install
        root = os.path.join(os.getenv('HOME'), '.pysat')
        new_root = os.path.join(os.getenv('HOME'), '.saved_pysat')
        shutil.move(root, new_root)

        reload(pysat)

        captured = capsys.readouterr()
        assert captured.out.find("Hi there!") >= 0

        # Make sure user files are blank
        with open(os.path.join(root, 'data_path.txt'), 'r') as f:
            dir_list = f.readlines()
            assert len(dir_list) == 1
            assert dir_list[0].find('/home/travis/build/pysatData') >= 0
        with open(os.path.join(root, 'user_modules.txt'), 'r') as f:
            assert len(f.readlines()) == 0

        # Move settings back
        shutil.rmtree(root)
        shutil.move(new_root, root)


class TestScaleUnits():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.deg_units = ["deg", "degree", "degrees", "rad", "radian",
                          "radians", "h", "hr", "hrs", "hours"]
        self.dist_units = ["m", "km", "cm"]
        self.vel_units = ["m/s", "cm/s", "km/s", 'm s$^{-1}$', 'cm s$^{-1}$',
                          'km s$^{-1}$', 'm s-1', 'cm s-1', 'km s-1']

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.deg_units, self.dist_units, self.vel_units

    def test_scale_units_same(self):
        """ Test scale_units when both units are the same """

        scale = pysat.utils.scale_units("happy", "happy")

        assert scale == 1.0

    def test_scale_units_angles(self):
        """Test scale_units for angles """

        for out_unit in self.deg_units:
            scale = pysat.utils.scale_units(out_unit, "deg")

            if out_unit.find("deg") == 0:
                assert scale == 1.0
            elif out_unit.find("rad") == 0:
                assert scale == np.pi / 180.0
            else:
                assert scale == 1.0 / 15.0

    def test_scale_units_dist(self):
        """Test scale_units for distances """

        for out_unit in self.dist_units:
            scale = pysat.utils.scale_units(out_unit, "m")

            if out_unit == "m":
                assert scale == 1.0
            elif out_unit.find("km") == 0:
                assert scale == 0.001
            else:
                assert scale == 100.0

    def test_scale_units_vel(self):
        """Test scale_units for velocities """

        for out_unit in self.vel_units:
            scale = pysat.utils.scale_units(out_unit, "m/s")

            if out_unit.find("m") == 0:
                assert scale == 1.0
            elif out_unit.find("km") == 0:
                assert scale == 0.001
            else:
                assert scale == 100.0

    def test_scale_units_bad_output(self):
        """Test scale_units for unknown output unit"""

        with pytest.raises(ValueError) as verr:
            pysat.utils.scale_units('happy', 'm')
        assert str(verr).find('output unit') > 0

    def test_scale_units_bad_input(self):
        """Test scale_units for unknown input unit"""

        with pytest.raises(ValueError) as verr:
            pysat.utils.scale_units('m', 'happy')
        assert str(verr).find('input unit') > 0

    @pytest.mark.parametrize("unit1,unit2", [("m", "m/s"),
                                             ("m", "deg"),
                                             ("h", "km/s")])
    def test_scale_units_bad_match_pairs(self, unit1, unit2):
        """Test scale_units for mismatched input for all pairings"""

        with pytest.raises(ValueError):
            pysat.utils.scale_units(unit1, unit2)

    def test_scale_units_bad_match_message(self):
        """Test scale_units error message for mismatched input"""

        with pytest.raises(ValueError) as verr:
            pysat.utils.scale_units('m', 'm/s')
        assert str(verr).find('Cannot scale') >= 0
        assert str(verr).find('unknown units') < 0

    def test_scale_units_both_bad(self):
        """Test scale_units for bad input and output"""

        with pytest.raises(ValueError) as verr:
            pysat.utils.scale_units('happy', 'sad')
        assert str(verr).find('unknown units') > 0


class TestBasicNetCDF4():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir

        # create temporary directory
        dir_name = tempfile.mkdtemp()
        pysat.utils.set_data_dir(dir_name, store=False)

        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing',
                                         inst_id='100',
                                         clean_level='clean')
        self.testInst.pandas_format = True

        # create testing directory
        prep_dir(self.testInst)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        remove_files(self.testInst)
        pysat.utils.set_data_dir(self.data_path, store=False)
        del self.testInst

    def test_load_netcdf4_empty_filenames(self):
        with pytest.raises(ValueError):
            pysat.utils.load_netcdf4(fnames=None)

    def test_basic_write_and_read_netcdf4_default_format(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst.to_netcdf4(outfile)

        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)
        self.testInst.data = \
            self.testInst.data.reindex(sorted(self.testInst.data.columns),
                                       axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)

        for key in self.testInst.data.columns:
            assert(np.all(self.testInst[key] == loaded_inst[key]))

    def test_basic_write_and_read_netcdf4_mixed_case_format(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        # modify data names in data
        original = sorted(self.testInst.data.columns)
        self.testInst.data = self.testInst.data.rename(str.upper,
                                                       axis='columns')
        self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)
        self.testInst.data = \
            self.testInst.data.reindex(sorted(self.testInst.data.columns),
                                       axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)

        # check that names are lower case when written
        assert(np.all(original == loaded_inst.columns))

        for key in self.testInst.data.columns:
            assert(np.all(self.testInst[key] == loaded_inst[key.lower()]))

        # modify metadata names in data
        self.testInst.meta.data = self.testInst.meta.data.rename(str.upper,
                                                                 axis='index')
        # write file
        self.testInst.to_netcdf4(outfile, preserve_meta_case=True)
        # load file
        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)

        # check that names are upper case when written
        assert np.all(sorted(self.testInst.data.columns)
                      == sorted(loaded_inst.columns))

    def test_write_netcdf4_duplicate_variable_names(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst['MLT'] = 1
        with pytest.raises(ValueError):
            self.testInst.to_netcdf4(outfile, preserve_meta_case=True)

    def test_write_and_read_netcdf4_default_format_w_compression(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst.to_netcdf4(outfile, zlib=True)

        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)
        self.testInst.data = \
            self.testInst.data.reindex(sorted(self.testInst.data.columns),
                                       axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)

        for key in self.testInst.data.columns:
            assert (np.all(self.testInst[key] == loaded_inst[key]))

    def test_write_and_read_netcdf4_default_format_w_weird_epoch_name(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst.to_netcdf4(outfile, epoch_name='Santa')

        loaded_inst, meta = pysat.utils.load_netcdf4(outfile,
                                                     epoch_name='Santa')
        self.testInst.data = \
            self.testInst.data.reindex(sorted(self.testInst.data.columns),
                                       axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns), axis=1)

        for key in self.testInst.data.columns:
            assert (np.all(self.testInst[key] == loaded_inst[key]))

    def test_write_and_read_netcdf4_default_format_higher_order(self):
        # create a bunch of files by year and doy
        test_inst = pysat.Instrument('pysat', 'testing2d')
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
        test_inst = pysat.Instrument('pysat', 'testing2d')
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
        """Test that attributes will not be overridden by default"""
        self.testInst.load(2009, 1)

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
        """Test that attributes in netcdf file may be overridden"""
        self.testInst.load(2009, 1)

        self.testInst.meta.mutable = True
        self.testInst.meta.bespoke = True

        self.testInst.meta.transfer_attributes_to_instrument(self.testInst)

        # ensure custom meta attribute assigned to instrument
        assert self.testInst.bespoke

        fname = 'output.nc'
        outfile = os.path.join(self.testInst.files.data_path, fname)
        self.testInst.to_netcdf4(outfile)

        data, meta = pysat.utils.load_netcdf4(outfile)

        # custom attribute correctly read from file
        assert meta.bespoke


class TestBasicNetCDF4xarray():
    """NOTE: combine with above class as part of #60"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir

        # create temporary directory
        dir_name = tempfile.mkdtemp()
        pysat.utils.set_data_dir(dir_name, store=False)

        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing2d_xarray',
                                         inst_id='100',
                                         clean_level='clean')
        self.testInst.pandas_format = False

        # create testing directory
        prep_dir(self.testInst)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        remove_files(self.testInst)
        pysat.utils.set_data_dir(self.data_path, store=False)
        del self.testInst

    def test_basic_write_and_read_netcdf4_default_format(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst.data.attrs['new_attr'] = 1
        self.testInst.data.to_netcdf(outfile)

        loaded_inst, meta = \
            pysat.utils.load_netcdf4(outfile,
                                     pandas_format=self.testInst.pandas_format)
        keys = self.testInst.data.data_vars.keys()

        for key in keys:
            assert(np.all(self.testInst[key] == loaded_inst[key]))
        assert meta.new_attr == 1

    def test_load_netcdf4_pandas_3d_error(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst.data.attrs['new_attr'] = 1
        self.testInst.data.to_netcdf(outfile)

        with pytest.raises(ValueError):
            loaded_inst, meta = pysat.utils.load_netcdf4(outfile,
                                                         epoch_name='time',
                                                         pandas_format=True)


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
