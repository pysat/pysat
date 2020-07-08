"""
tests the pysat utils area
"""
import os
import tempfile
import warnings

from nose.tools import assert_raises, raises
import numpy as np
import pandas as pds

import pysat

import sys
if sys.version_info[0] >= 3:
    from importlib import reload as re_load
else:
    re_load = reload


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


def test_deprecation_warning_computational_form():
    """Test if computational form in utils is deprecated"""

    data = pds.Series([0, 1, 2])
    warnings.simplefilter("always")
    dslice1 = pysat.ssnl.computational_form(data)
    with warnings.catch_warnings(record=True) as war:
        dslice2 = pysat.utils.computational_form(data)

    assert (dslice1 == dslice2).all()
    assert len(war) >= 1
    assert war[0].category == DeprecationWarning


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
        pysat._files = re_load(pysat._files)
        pysat._instrument = re_load(pysat._instrument)
        re_load(pysat)
        check2 = (pysat.data_dir == '.')

        assert check1 & check2

    def test_set_data_dir_no_store(self):
        """update data_dir without storing"""
        pysat.utils.set_data_dir('.', store=False)
        check1 = (pysat.data_dir == '.')

        # Check if next load of pysat remembers old settings
        pysat._files = re_load(pysat._files)
        pysat._instrument = re_load(pysat._instrument)
        re_load(pysat)
        check2 = (pysat.data_dir == self.data_path)

        assert check1 & check2

    @raises(ValueError)
    def test_set_data_dir_wrong_path(self):
        """update data_dir with an invalid path"""
        pysat.utils.set_data_dir('not_a_directory', store=False)

    def test_initial_pysat_load(self):
        import shutil
        saved = False
        try:
            root = os.path.join(os.getenv('HOME'), '.pysat')
            new_root = os.path.join(os.getenv('HOME'), '.saved_pysat')
            shutil.move(root, new_root)
            saved = True
        except:
            pass

        re_load(pysat)

        try:
            if saved:
                # remove directory, trying to be careful
                os.remove(os.path.join(root, 'data_path.txt'))
                os.rmdir(root)
                shutil.move(new_root, root)
        except:
            pass

        assert True


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

        assert_raises(ValueError, pysat.utils.scale_units, "happy", "m")
        try:
            pysat.utils.scale_units('happy', 'm')
        except ValueError as verr:
            assert str(verr).find('output unit') > 0

    def test_scale_units_bad_input(self):
        """Test scale_units for unknown input unit"""

        assert_raises(ValueError, pysat.utils.scale_units, "m", "happy")
        try:
            pysat.utils.scale_units('m', 'happy')
        except ValueError as verr:
            assert str(verr).find('input unit') > 0

    def test_scale_units_bad_match_pairs(self):
        """Test scale_units for mismatched input for all pairings"""

        assert_raises(ValueError, pysat.utils.scale_units, "m", "m/s")
        assert_raises(ValueError, pysat.utils.scale_units, "m", "deg")
        assert_raises(ValueError, pysat.utils.scale_units, "h", "km/s")

    def test_scale_units_bad_match_message(self):
        """Test scale_units error message for mismatched input"""

        assert_raises(ValueError, pysat.utils.scale_units, "m", "m/s")
        try:
            pysat.utils.scale_units('m', 'm/s')
        except ValueError as verr:
            assert str(verr).find('Cannot scale') >= 0
            assert str(verr).find('unknown units') < 0

    def test_scale_units_both_bad(self):
        """Test scale_units for bad input and output"""

        assert_raises(ValueError, pysat.utils.scale_units, "happy", "sad")
        try:
            pysat.utils.scale_units('happy', 'sad')
        except ValueError as verr:
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
                                         sat_id='100',
                                         clean_level='clean')
        self.testInst.pandas_format = True

        # create testing directory
        prep_dir(self.testInst)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        remove_files(self.testInst)
        pysat.utils.set_data_dir(self.data_path, store=False)
        del self.testInst

    @raises(ValueError)
    def test_load_netcdf4_empty_filenames(self):
        pysat.utils.load_netcdf4(fnames=None)

    def test_basic_write_and_read_netcdf4_default_format(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst.to_netcdf4(outfile)

        loaded_inst, meta = \
            pysat.utils.load_netcdf4(outfile,
                                     pandas_format=self.testInst.pandas_format)
        self.testInst.data = \
            self.testInst.data.reindex(sorted(self.testInst.data.columns),
                                       axis=1)
        loaded_inst = loaded_inst.reindex(sorted(loaded_inst.columns),
                                          axis=1)
        keys = self.testInst.data.columns

        for key in keys:
            assert(np.all(self.testInst[key] == loaded_inst[key]))

    def test_basic_write_and_read_netcdf4_mixed_case_format(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        # modify data names in data
        original = sorted(self.testInst.data.columns)
        self.testInst.data = self.testInst.data.rename(str.upper, axis='columns')
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
        self.testInst.meta.data = self.testInst.meta.data.rename(str.upper, axis='index')
        # write file
        self.testInst.to_netcdf4(outfile, preserve_meta_case=True)
        # load file
        loaded_inst, meta = pysat.utils.load_netcdf4(outfile)

        # check that names are upper case when written
        assert(np.all(sorted(self.testInst.data.columns) == sorted(loaded_inst.columns)))

    @raises(Exception)
    def test_write_netcdf4_duplicate_variable_names(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst['MLT'] = 1
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
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.data_path = pysat.data_dir

        # create temporary directory
        dir_name = tempfile.mkdtemp()
        pysat.utils.set_data_dir(dir_name, store=False)

        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing2d_xarray',
                                         sat_id='100',
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

    def test_load_netcdf4_pandas_3d_deprecation_warning(self):
        # create a bunch of files by year and doy
        prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.load(2009, 1)
        self.testInst.data.attrs['new_attr'] = 1
        self.testInst.data.to_netcdf(outfile)

        warnings.simplefilter("always")
        with warnings.catch_warnings(record=True) as war:
            loaded_inst, meta = pysat.utils.load_netcdf4(outfile,
                                                         epoch_name='time',
                                                         pandas_format=True)
        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
