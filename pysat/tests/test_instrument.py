#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Tests the pysat Instrument object and methods."""

import datetime as dt
from importlib import reload
import numpy as np
import pandas as pds
import pytest
import warnings
import xarray as xr

import pysat
import pysat.instruments.pysat_ndtesting
import pysat.instruments.pysat_testing

from pysat.tests.classes.cls_instrument_access import InstAccessTests
from pysat.tests.classes.cls_instrument_integration import InstIntegrationTests
from pysat.tests.classes.cls_instrument_iteration import InstIterationTests
from pysat.tests.classes.cls_instrument_property import InstPropertyTests
from pysat.utils import testing


class TestBasics(InstAccessTests, InstIntegrationTests, InstIterationTests,
                 InstPropertyTests):
    """Unit tests for pysat.Instrument object."""

    def setup_class(self):
        """Set up class-level variables once before all methods."""

        self.xarray_epoch_name = 'time'
        self.testing_kwargs = {'test_init_kwarg': True,
                               'test_clean_kwarg': False,
                               'test_preprocess_kwarg': 'test_phrase',
                               'test_load_kwarg': 'bright_light',
                               'test_list_files_kwarg': 'sleep_tight',
                               'test_list_remote_kwarg': 'one_eye_open',
                               'test_download_kwarg': 'exit_night'}
        return

    def teardown_class(self):
        """Clean up class-level variables once after all methods."""

        del self.testing_kwargs, self.xarray_epoch_name
        return

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10, clean_level='clean',
                                         update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return

    def check_nonstandard_cadence(self):
        """Check for nonstandard cadence in tests."""

        if hasattr(self, 'freq'):
            min_freq = pds.tseries.frequencies.to_offset('D')
            return pds.tseries.frequencies.to_offset(self.freq) != min_freq
        else:
            # Uses standard frequency
            return False


class TestInstCadence(TestBasics):
    """Unit tests for pysat.Instrument objects with the default file cadance."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.freq = 'D'

        date_range = pds.date_range(self.ref_time - pds.DateOffset(years=1),
                                    self.ref_time + pds.DateOffset(years=2)
                                    - pds.DateOffset(days=1), freq=self.freq)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10, clean_level='clean',
                                         update_files=True,
                                         file_date_range=date_range,
                                         **self.testing_kwargs)
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy, self.freq
        return


class TestInstMonthlyCadence(TestInstCadence):
    """Unit tests for pysat.Instrument objects with a monthly file cadance."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.freq = 'MS'

        date_range = pds.date_range(self.ref_time - pds.DateOffset(years=1),
                                    self.ref_time
                                    + pds.DateOffset(years=2, days=-1),
                                    freq=self.freq)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10, clean_level='clean',
                                         update_files=True,
                                         file_date_range=date_range,
                                         **self.testing_kwargs)
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy, self.freq
        return


class TestInstYearlyCadence(TestInstCadence):
    """Unit tests for pysat.Instrument objects with a monthly file cadance."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.freq = 'YS'

        # Since these are yearly files, use a longer date range
        date_range = pds.date_range(self.ref_time - pds.DateOffset(years=1),
                                    self.ref_time
                                    + pds.DateOffset(years=5, days=-1),
                                    freq=self.freq)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10, clean_level='clean',
                                         update_files=True,
                                         file_date_range=date_range,
                                         **self.testing_kwargs)
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy, self.freq
        return


class TestBasicsInstModule(TestBasics):
    """Basic tests for instrument instantiated via inst_module."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        imod = pysat.instruments.pysat_testing
        self.testInst = pysat.Instrument(inst_module=imod, num_samples=10,
                                         clean_level='clean', update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = imod._test_dates['']['']
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


class TestBasicsNDXarray(TestBasics):
    """Basic tests for ND xarray `pysat.Instrument`.

    Note
    ----
    Includes additional tests for multidimensional objects.

    """

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_ndtesting)
        self.testInst = pysat.Instrument(platform='pysat', name='ndtesting',
                                         num_samples=10, clean_level='clean',
                                         update_files=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_ndtesting._test_dates['']['']
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return

    def test_setting_data_as_tuple(self):
        """Test setting data as a tuple."""

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleMLT'] = ('time', 2. * self.testInst['mlt'].values)
        assert np.all(self.testInst['doubleMLT'] == 2. * self.testInst['mlt'])
        return

    def test_xarray_not_empty_notime(self):
        """Test that xarray empty is False even if there is no time data."""
        # Load data and confirm it exists
        self.testInst.load(date=self.ref_time)
        assert not self.testInst.empty

        # Downselect to no time data
        self.testInst.data = self.testInst[self.ref_time + dt.timedelta(days=1):
                                           self.ref_time + dt.timedelta(days=2)]
        assert not self.testInst.empty
        assert len(self.testInst.index) == 0
        for dim in self.testInst.data.dims:
            if dim != 'time':
                assert len(self.testInst[dim]) > 0
        return

    @pytest.mark.parametrize("index", [(0),
                                       ([0, 1, 2, 3]),
                                       (slice(0, 10)),
                                       (np.array([0, 1, 2, 3]))])
    def test_data_access_by_2d_indices_and_name(self, index):
        """Check that variables and be accessed by each supported index type.

        Parameters
        ----------
        index : iterable
            Indexing iterable to test, such as lists, arrays, slices

        """

        self.testInst.load(self.ref_time.year, self.ref_doy)
        assert np.all(self.testInst[index, index, 'profiles']
                      == self.testInst.data['profiles'][index, index])
        return

    def test_data_access_by_2d_tuple_indices_and_name(self):
        """Check that variables and be accessed by multi-dim tuple index."""

        self.testInst.load(date=self.ref_time)
        index = ([0, 1, 2, 3], [0, 1, 2, 3])
        assert np.all(self.testInst[index, 'profiles']
                      == self.testInst.data['profiles'][index[0], index[1]])
        return

    def test_data_access_bad_dimension_tuple(self):
        """Test raises ValueError for mismatched tuple index and data dims."""

        self.testInst.load(date=self.ref_time)
        index = ([0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3])

        with pytest.raises(ValueError) as verr:
            self.testInst[index, 'profiles']

        estr = 'not convert tuple'
        assert str(verr).find(estr) > 0
        return

    def test_data_access_bad_dimension_for_multidim(self):
        """Test raises ValueError for mismatched index and data dimensions."""

        self.testInst.load(date=self.ref_time)
        index = [0, 1, 2, 3]

        with pytest.raises(ValueError) as verr:
            self.testInst[index, index, index, 'profiles']

        estr = "don't match data"
        assert str(verr).find(estr) > 0
        return

    @pytest.mark.parametrize("changed,fixed",
                             [(0, slice(1, None)),
                              ([0, 1, 2, 3], slice(4, None)),
                              (slice(0, 10), slice(10, None)),
                              (np.array([0, 1, 2, 3]), slice(4, None))])
    def test_setting_partial_data_by_2d_indices_and_name(self, changed, fixed):
        """Check that data can be set using each supported index type.

        Parameters
        ----------
        changed : int, list, slice, or np.array
            Index locations to change within test
        fixed : slice
            Index slice for locations unaffected

        """

        self.testInst.load(self.ref_time.year, self.ref_doy)
        self.testInst['doubleProfile'] = 2. * self.testInst['profiles']
        self.testInst[changed, changed, 'doubleProfile'] = 0
        assert np.all(np.all(self.testInst[fixed, fixed, 'doubleProfile']
                             == 2. * self.testInst[fixed, 'profiles']))
        assert np.all(np.all(self.testInst[changed, changed, 'doubleProfile']
                             == 0))
        return

    @pytest.mark.parametrize("data,target",
                             [(xr.Dataset(), True),
                              (xr.Dataset({'time': []}), True),
                              (xr.Dataset({'lat': [], 'lon': []}), True),
                              (xr.Dataset({'time': [], 'lon': [0.]}), False),
                              (xr.Dataset({'lat': [0.], 'lon': [0.]}), False)])
    def test_xarray_empty_conditions(self, data, target):
        """Test that multiple xarray empty conditions are satisfied.

        Parameters
        ----------
        data : xr.Dataset
            Sample data object to check for emptiness.
        target : bool
            Target response for `self.testInst.empty`.

        """

        self.testInst.data = data
        assert self.testInst.empty == target
        return

    @pytest.mark.parametrize("val,warn_msg",
                             [([], "broadcast as NaN"),
                              (27., "Broadcast over epoch"),
                              (np.array([27.]), "Broadcast over epoch")])
    def test_set_xarray_single_value_warnings(self, val, warn_msg):
        """Check for warning messages when setting xarray values.

        Parameters
        ----------
        val : float or iterable
            Value to be added as a new data variable.
        warn_msg : str
            Excerpt from expected warning message.

        """

        warnings.simplefilter("always")

        self.testInst.load(date=self.ref_time)

        with warnings.catch_warnings(record=True) as self.war:
            self.testInst["new_val"] = val
        testing.eval_warnings(self.war, warn_msg, warn_type=UserWarning)

    def test_set_xarray_single_value_errors(self):
        """Check for warning messages when setting xarray values.

        Parameters
        ----------
        val : float or iterable
            Value to be added as a new data variable.
        warn_msg : str
            Excerpt from expected warning message.

        """

        self.testInst.load(date=self.ref_time)
        self.testInst.data = self.testInst.data.assign_coords(
            {'preset_val': np.array([1.0, 2.0])})

        with pytest.raises(ValueError) as verr:
            self.testInst['preset_val'] = 1.0

        estr = 'Shape of input does not match'
        assert str(verr).find(estr) > 0
        return

    @pytest.mark.parametrize("new_val", [3.0, np.array([3.0])])
    def test_set_xarray_single_value_broadcast(self, new_val):
        """Check that single values are correctly broadcast.

        Parameters
        ----------
        new_val : float or iterable
            Should be a single value, potentially an array with one element.

        """

        self.testInst.load(date=self.ref_time)
        self.testInst.data = self.testInst.data.assign_coords(
            {'preset_val': 1.0})

        self.testInst['preset_val'] = new_val
        self.testInst['new_val'] = new_val
        # Existing coords should be not be broadcast
        assert self.testInst['preset_val'].size == 1
        # New variables broadcast over time
        assert len(self.testInst['new_val']) == len(self.testInst.index)


class TestBasicsShiftedFileDates(TestBasics):
    """Basic tests for pandas `pysat.Instrument` with shifted file dates."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10, clean_level='clean',
                                         update_files=True,
                                         mangle_file_dates=True,
                                         strict_time_flag=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


class TestInstGeneral(object):
    """Unit tests for empty instrument objects."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.empty_inst = pysat.Instrument()
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.empty_inst
        return

    def test_creating_empty_instrument_object(self):
        """Ensure empty Instrument instantiation runs."""

        assert isinstance(self.empty_inst, pysat.Instrument)
        return

    def test_load_empty_instrument_no_files_error(self):
        """Ensure error loading Instrument with no files."""

        # Trying to load when there are no files produces multiple warnings
        # and one Error.
        with warnings.catch_warnings(record=True) as self.war:
            testing.eval_bad_input(self.empty_inst.load, IndexError,
                                   'index 0 is out of bounds')
        estr = ['No files found for Instrument', 'IndexError will not be']
        testing.eval_warnings(self.war, estr, warn_type=[UserWarning,
                                                         DeprecationWarning])
        return

    def test_empty_repr_eval(self):
        """Test that repr functions on empty `Instrument`."""

        self.out = eval(repr(self.empty_inst))
        assert isinstance(self.out, pysat.Instrument)
        assert self.out.platform == ''
        assert self.out.name == ''
        assert self.out.inst_module is None
        return

    @pytest.mark.parametrize("kwargs", [{'platform': 'cnofs'},
                                        {'name': 'ivm'}])
    def test_incorrect_creation_empty_instrument_object(self, kwargs):
        """Ensure instantiation with missing name errors.

        Parameters
        ----------
        kwargs : dict
            Kwargs to pass through for instrument instantiation.

        """

        testing.eval_bad_input(pysat.Instrument, ValueError,
                               'Inputs platform and name must both',
                               input_kwargs=kwargs)
        return

    def test_supplying_instrument_module_requires_name_and_platform(self):
        """Ensure instantiation via inst_module with missing name errors."""

        class Dummy(object):
            pass
        Dummy.name = 'help'

        testing.eval_bad_input(pysat.Instrument, AttributeError,
                               'Supplied module ',
                               input_kwargs={'inst_module': Dummy})
        return

    def test_eq_different_object(self):
        """Test equality using different `pysat.Instrument` objects."""

        obj1 = pysat.Instrument(platform='pysat', name='testing',
                                num_samples=10, clean_level='clean',
                                update_files=True)

        obj2 = pysat.Instrument(platform='pysat', name='ndtesting',
                                num_samples=10, clean_level='clean',
                                update_files=True)
        assert not (obj1 == obj2)
        return


class TestDeprecation(object):
    """Unit test for deprecation warnings."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        self.in_kwargs = {"platform": 'pysat', "name": 'testing',
                          "clean_level": 'clean'}
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.warn_msgs = []
        self.war = ""
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        reload(pysat.instruments.pysat_testing)
        del self.in_kwargs, self.ref_time, self.warn_msgs, self.war
        return

    def eval_warnings(self):
        """Evaluate the number and message of the raised warnings."""

        # Ensure the minimum number of warnings were raised.
        assert len(self.war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present.
        testing.eval_warnings(self.war, self.warn_msgs)
        return

    # TODO(#1020): Remove test when keyword `use_header` is removed.
    def test_load_use_header(self):
        """Test that user is informed of MetaHeader on load."""

        # Determine the expected warnings
        self.warn_msgs = np.array(["".join(['Meta now contains a class for ',
                                            'global metadata (MetaHeader). ',
                                            'Allowing attachment of global ',
                                            'attributes to Instrument through',
                                            ' `use_header=False` will be ',
                                            'Deprecated in pysat 3.3.0+. ',
                                            'Remove `use_header` kwarg (now ',
                                            'same as `use_header=True`) to ',
                                            'stop this warning.'])])

        # Capture the warnings
        with warnings.catch_warnings(record=True) as self.war:
            test_inst = pysat.Instrument(**self.in_kwargs)
            test_inst.load(date=self.ref_time, use_header=False)

        # Evaluate the warning output
        self.eval_warnings()
        return
