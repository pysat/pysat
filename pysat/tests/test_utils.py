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
import warnings

import pysat
from pysat.tests.classes.cls_registration import TestWithRegistration
from pysat import utils


class TestCIonly(object):
    """Tests where we mess with local settings.

    Note
    ----
    These only run in CI environments such as GitHub Actions to avoid breaking
    an end user's setup

    """

    def setup_method(self):
        """Run to set up the test environment."""

        self.ci_env = (os.environ.get('CI') == 'true')
        if not self.ci_env:
            pytest.skip("Skipping local tests to avoid breaking user setup")

        return

    def teardown_method(self):
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

    def setup_method(self):
        """Run to set up the test environment."""

        self.deg_units = ["deg", "degree", "degrees", "rad", "radian",
                          "radians", "h", "hr", "hrs", "hours"]
        self.dist_units = ["m", "km", "cm"]
        self.vel_units = ["m/s", "cm/s", "km/s", 'm s$^{-1}$', 'cm s$^{-1}$',
                          'km s$^{-1}$', 'm s-1', 'cm s-1', 'km s-1']
        self.vol_units = ["m-3", "cm-3", "/cc", 'n/cc', 'm$^{-3}$', 'cm$^{-3}$',
                          "#/cm^3", "#/km^3", "#/m^3", "cm^-3", "km^-3", "m^-3",
                          'cm^{-3}', 'm^{-3}', 'km^{-3}']
        self.scale = 0.0
        return

    def teardown_method(self):
        """Clean up the test environment."""

        del self.deg_units, self.dist_units, self.vel_units, self.scale
        del self.vol_units
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

        estr = "bad {:s} comparison for output unit {:s}".format(scale_type,
                                                                 out_unit)

        if scale_type.lower() == 'angles':
            if out_unit.find("deg") == 0:
                assert self.scale == 1.0, estr
            elif out_unit.find("rad") == 0:
                assert self.scale == np.pi / 180.0, estr
            else:
                assert self.scale == 1.0 / 15.0, estr
        elif scale_type.lower() == 'distance':
            if out_unit == "m":
                assert self.scale == 1.0, estr
            elif out_unit.find("km") == 0:
                assert self.scale == 0.001, estr
            else:
                assert self.scale == 100.0, estr
        elif scale_type.lower() == 'velocity':
            if out_unit.find("m") == 0:
                assert self.scale == 1.0, estr
            elif out_unit.find("km") == 0:
                assert self.scale == 0.001, estr
        elif scale_type.lower() == 'volume':
            if out_unit.find("cm") >= 0 or out_unit.find("cc") > 0:
                assert self.scale == 1000000.0, estr
            elif out_unit.find("km") >= 0:
                assert self.scale == 1.0e-9, estr
            else:
                assert self.scale == 1.0, estr
        return

    def test_scale_units_same(self):
        """Test scale_units when both units are the same."""

        self.scale = utils.scale_units("happy", "happy")

        assert self.scale == 1.0
        return

    def test_scale_units_angles(self):
        """Test scale_units for angles."""
        for out_unit in self.deg_units:
            self.scale = utils.scale_units(out_unit, "deg")
            self.eval_unit_scale(out_unit, 'angles')
        return

    def test_scale_units_dist(self):
        """Test scale_units for distances."""

        for out_unit in self.dist_units:
            self.scale = utils.scale_units(out_unit, "m")
            self.eval_unit_scale(out_unit, 'distance')
        return

    def test_scale_units_vel(self):
        """Test scale_units for velocities."""

        for out_unit in self.vel_units:
            self.scale = utils.scale_units(out_unit, "m/s")
            self.eval_unit_scale(out_unit, 'velocity')
        return

    def test_scale_units_vol(self):
        """Test scale_units for volumes."""

        for out_unit in self.vol_units:
            self.scale = utils.scale_units(out_unit, "m-3")
            self.eval_unit_scale(out_unit, 'volume')
        return

    @pytest.mark.parametrize("in_args,err_msg", [
        (['happy', 'm'], 'output unit'), (['m', 'happy'], 'input unit'),
        (['m', 'm/s'], 'Cannot scale m and m/s'),
        (['happy', 'sad'], 'unknown units')])
    def test_scale_units_bad_input(self, in_args, err_msg):
        """Test raises ValueError for bad input combinations.

        Parameters
        ----------
        in_args : list
            Input arguments
        err_msg : str
            Expected error message

        """

        utils.testing.eval_bad_input(utils.scale_units, ValueError, err_msg,
                                     in_args)
        return

    @pytest.mark.parametrize("unit1,unit2", [("m", "m/s"),
                                             ("m", "deg"),
                                             ("h", "km/s")])
    def test_scale_units_bad_match_pairs(self, unit1, unit2):
        """Test raises ValueError for all mismatched input pairings.

        Parameters
        ----------
        unit1 : str
            First input unit
        unit2 : str
            Second input unit

        """

        utils.testing.eval_bad_input(utils.scale_units, ValueError,
                                     "Cannot scale", [unit1, unit2])

        return


class TestIfyFunctions(object):
    """Unit tests for the various `*ify` functions."""

    @pytest.mark.parametrize('iterable,nitem', [
        ('test', 1), (['test'], 1), ([[['test']]], 1), ([[[['test']]]], 1),
        ([['test', 'test']], 2), ([['test', 'test'], ['test', 'test']], 4),
        ([], 0), ([[]], 0)])
    def test_listify_list_string_inputs(self, iterable, nitem):
        """Test listify with various list levels of a string."""

        new_iterable = utils.listify(iterable)
        tst_iterable = ['test' for i in range(nitem)]
        utils.testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('iterable', [np.nan, np.full((1, 1), np.nan),
                                          np.full((2, 2), np.nan),
                                          np.full((3, 3, 3), np.nan)])
    def test_listify_nan_arrays(self, iterable):
        """Test listify with various np.arrays of NaNs."""

        new_iterable = utils.listify(iterable)
        tst_iterable = [np.nan
                        for i in range(int(np.product(np.shape(iterable))))]
        utils.testing.assert_lists_equal(new_iterable, tst_iterable,
                                         test_nan=True)
        return

    @pytest.mark.parametrize('iterable', [1, np.full((1, 1), 1),
                                          np.full((2, 2), 1),
                                          np.full((3, 3, 3), 1)])
    def test_listify_int_arrays(self, iterable):
        """Test listify with various np.arrays of integers."""

        new_iterable = utils.listify(iterable)
        tst_iterable = [1 for i in range(int(np.product(np.shape(iterable))))]
        utils.testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('iterable', [{'key1': 1, 'key2': 2}.keys(),
                                          {'key1': 1, 'key2': 2}.values()])
    def test_listify_failure_with_dict_iterable(self, iterable):
        """Test listify failes with various dict iterables.

        Parameters
        ----------
        iterable : dict_keys or dict_values
            Iterable dict object

        """

        new_iterable = utils.listify(iterable)
        assert new_iterable[0] == iterable
        return

    @pytest.mark.parametrize('iterable', [
        np.timedelta64(1), np.full((1, 1), np.timedelta64(1)),
        np.full((2, 2), np.timedelta64(1)),
        np.full((3, 3, 3), np.timedelta64(1))])
    def test_listify_class_arrays(self, iterable):
        """Test listify with various np.arrays of classes."""

        new_iterable = utils.listify(iterable)
        tst_iterable = [np.timedelta64(1)
                        for i in range(int(np.product(np.shape(iterable))))]
        utils.testing.assert_lists_equal(new_iterable, tst_iterable)
        return

    @pytest.mark.parametrize('strlike', ['test_string',
                                         b'Les \xc3\x83\xc2\xa9vad\xc3\x83s'])
    def test_stringify(self, strlike):
        """Test stringify returns str with str and byte inputs."""

        output = pysat.utils.stringify(strlike)
        assert isinstance(output, str)
        return

    @pytest.mark.parametrize('astrlike', [[1, 2], (1, 2), np.array([1, 2]), 1])
    def test_stringify_non_str_types(self, astrlike):
        """Test stringify returns type as is for inputs other than str and byte.

        """

        target = type(astrlike)
        output = pysat.utils.stringify(astrlike)
        assert type(output) == target
        return


class TestFmtCols(object):
    """Unit tests for `fmt_output_in_cols`."""

    def setup_method(self):
        """Set up the test environment."""

        self.in_str = np.arange(0, 40, 1).astype(str)
        self.in_kwargs = {"ncols": 5, "max_num": 40, "lpad": None}
        self.out_str = None
        self.filler_row = -1
        self.ncols = None
        self.nrows = None
        self.lpad = len(self.in_str[-1]) + 1

        return

    def teardown_method(self):
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
        self.out_str = utils._core.fmt_output_in_cols(self.in_str,
                                                      **self.in_kwargs)
        assert len(self.out_str) == 0
        return

    @pytest.mark.parametrize("key,val,raise_type,err_msg",
                             [("ncols", 0, ZeroDivisionError,
                               "integer division or modulo by zero"),
                              ("max_num", -10, ValueError,
                               "max() arg is an empty sequence")])
    def test_fmt_raises(self, key, val, raise_type, err_msg):
        """Test raises appropriate Errors for bad input values.

        Parameters
        ----------
        key : str
            Input kwarg dict key to update
        val : any type
            Value to update in the kwarg input
        raise_type : class
            Expected exception or error
        err_msg : str
            Expected error message

        """
        self.in_kwargs[key] = val

        utils.testing.eval_bad_input(utils._core.fmt_output_in_cols,
                                     raise_type, err_msg, [self.in_str],
                                     self.in_kwargs)
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
        self.out_str = utils._core.fmt_output_in_cols(self.in_str,
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
        self.out_str = utils._core.fmt_output_in_cols(self.in_str,
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
        self.out_str = utils._core.fmt_output_in_cols(self.in_str,
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
            utils.registry.register(self.module_names)

        utils.display_available_instruments(
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

    @pytest.mark.parametrize("inst_loc", [None, [pysat.instruments]])
    def test_display_instrument_stats(self, inst_loc, capsys):
        """Test display_instrument_stats options.

        Parameters
        ----------
        inst_loc : any
            Passed to `display_instrument_stats`

        """

        utils.display_instrument_stats(inst_loc)

        captured = capsys.readouterr()
        # Numbers should match supported data products in `pysat.instruments`
        assert captured.out.find("supported data products with download") > 0
        assert captured.out.find("supported data products with local") > 0

        return

    def test_import_error_in_available_instruments(self):
        """Test handling of import errors in available_instruments."""

        idict = utils.available_instruments(os.path)

        for platform in idict.keys():
            for name in idict[platform].keys():
                assert 'ERROR' in idict[platform][name]['inst_ids_tags'].keys()
                assert 'ERROR' in idict[platform][name][
                    'inst_ids_tags']['ERROR']
        return


class TestNetworkLock(object):
    """Unit tests for NetworkLock class."""

    def setup_method(self):
        """Set up the unit test environment."""
        # Create and write a temporary file
        self.fname = 'temp_lock_file.txt'
        with open(self.fname, 'w') as fh:
            fh.write('spam and eggs')
        return

    def teardown_method(self):
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
            with utils.NetworkLock(self.fname, timeout=0.1):
                with utils.NetworkLock(self.fname, mode='wb', timeout=0.1,
                                       fail_when_locked=True):
                    pass
        return

    def test_without_timeout(self):
        """Test network locking without a timeout."""
        # Open the file two times
        with pytest.raises(portalocker.LockException):
            with utils.NetworkLock(self.fname, timeout=None):
                with utils.NetworkLock(self.fname, timeout=None, mode='w'):
                    pass
        return

    def test_without_fail(self):
        """Test network locking without file conditions set."""
        # Open the file two times
        with pytest.raises(portalocker.LockException):
            with utils.NetworkLock(self.fname, timeout=0.1):
                lock = utils.NetworkLock(self.fname, timeout=0.1)
                lock.acquire(check_interval=0.05, fail_when_locked=False)
        return


class TestGenerateInstList(object):
    """Unit tests for `utils.generate_instrument_list`."""

    def setup_method(self):
        """Set up the unit test environment before each method."""

        self.user_info = {'pysat_testmodel': {'user': 'GideonNav',
                                              'password': 'pasSWORD!'}}
        self.inst_list = utils.generate_instrument_list(
            inst_loc=pysat.instruments, user_info=self.user_info)
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.inst_list, self.user_info
        return

    def test_generate_module_names(self):
        """Test generation of module names."""

        utils.testing.assert_lists_equal(self.inst_list['names'],
                                         pysat.instruments.__all__)

    @pytest.mark.parametrize("list_name", [('download'), ('no_download')])
    def test_generate_module_list_attributes(self, list_name):
        """Test that each instrument dict has sufficient information.

        Parameters
        ----------
        list_name : str
            Label to check within `self.inst_list`

        """

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
        """Test that instruments without downloads are sorted properly.

        Parameters
        ----------
        list_name : str
            Label to check within `self.inst_list`
        output : bool
            Boolean value expected from internal test
        """

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


class TestDeprecation(object):
    """Unit test for deprecation warnings."""

    @pytest.mark.parametrize("kwargs,msg_inds",
                             [({'fnames': None}, [0, 1]),
                              ({'fnames': 'no_file', 'file_format': None},
                               [0, 2])])
    def test_load_netcdf4(self, kwargs, msg_inds):
        """Test deprecation warnings from load_netcdf4.

        Parameters
        ----------
        kwargs : dict
            Keyword arguments passed to `load_netcdf4`
        msg_inds : list
            List of indices indicating which warning message is expected

        """
        with warnings.catch_warnings(record=True) as war:
            try:
                # Generate relocation warning and file_format warning
                utils.load_netcdf4(**kwargs)
            except (FileNotFoundError, ValueError):
                pass

        warn_msgs = ["".join(["function moved to `pysat.utils.io`, ",
                              "deprecated wrapper will be removed in ",
                              "pysat 3.2.0+"]),
                     "".join(["`fnames` as a kwarg has been deprecated, ",
                              "must supply a string or list of strings",
                              " in 3.2.0+"]),
                     "".join(["`file_format` must be a string value in ",
                              "3.2.0+, instead of None use 'NETCDF4' ",
                              "for same behavior."])]

        warn_msgs = [warn_msgs[ind] for ind in msg_inds]
        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        utils.testing.eval_warnings(war, warn_msgs)
        return


class TestMappedValue(object):
    """Unit tests for utility `get_mapped_value`."""

    def setup_method(self):
        """Set up a clean testing environment."""
        self.data_vals = ['one', 'two', 'three', 'four']
        return

    def teardown_method(self):
        """Clean up the current testing enviornment."""
        del self.data_vals
        return

    def test_get_mapped_value_dict(self):
        """Test successful mapping from dict input."""

        map_dict = {val: val.upper() for val in self.data_vals}

        for val in self.data_vals:
            assert val.upper() == utils.get_mapped_value(val, map_dict)

        return

    def test_get_mapped_value_func(self):
        """Test successful mapping from an input function."""

        for val in self.data_vals:
            assert val.upper() == utils.get_mapped_value(val, str.upper)

        return
