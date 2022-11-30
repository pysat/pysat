# -*- coding: utf-8 -*-
"""Tests the pysat Instrument object and methods."""

from importlib import reload
import numpy as np
import pytest
import warnings
import xarray as xr

import pysat
import pysat.instruments.pysat_ndtesting
import pysat.instruments.pysat_testing
import pysat.instruments.pysat_testing2d
import pysat.instruments.pysat_testing_xarray

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
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         use_header=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.ref_doy = int(self.ref_time.strftime('%j'))
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


class TestBasicsInstModule(TestBasics):
    """Basic tests for instrument instantiated via inst_module."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        imod = pysat.instruments.pysat_testing
        self.testInst = pysat.Instrument(inst_module=imod,
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         use_header=True,
                                         **self.testing_kwargs)
        self.ref_time = imod._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


# TODO(#908): remove below class when pysat_testing_xarray is removed.
class TestBasicsXarray(TestBasics):
    """Basic tests for xarray `pysat.Instrument`."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing_xarray)
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='testing_xarray',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         use_header=True,
                                         **self.testing_kwargs)
        self.ref_time = \
            pysat.instruments.pysat_testing_xarray._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
        return


# TODO(#908): remove below class when pysat_testing2d is removed.
class TestBasics2D(TestBasics):
    """Basic tests for 2D pandas `pysat.Instrument`."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing2d)
        self.testInst = pysat.Instrument(platform='pysat', name='testing2d',
                                         num_samples=50,
                                         clean_level='clean',
                                         update_files=True,
                                         use_header=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing2d._test_dates['']['']
        self.ref_doy = 1
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
        self.testInst = pysat.Instrument(platform='pysat',
                                         name='ndtesting',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         use_header=True,
                                         **self.testing_kwargs)
        self.ref_time = \
            pysat.instruments.pysat_ndtesting._test_dates['']['']
        self.ref_doy = 1
        self.out = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.out, self.ref_time, self.ref_doy
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

        self.testInst.load(self.ref_time.year, self.ref_doy, use_header=True)
        assert np.all(self.testInst[index, index, 'profiles']
                      == self.testInst.data['profiles'][index, index])
        return

    def test_data_access_by_2d_tuple_indices_and_name(self):
        """Check that variables and be accessed by multi-dim tuple index."""

        self.testInst.load(date=self.ref_time, use_header=True)
        index = ([0, 1, 2, 3], [0, 1, 2, 3])
        assert np.all(self.testInst[index, 'profiles']
                      == self.testInst.data['profiles'][index[0], index[1]])
        return

    def test_data_access_bad_dimension_tuple(self):
        """Test raises ValueError for mismatched tuple index and data dims."""

        self.testInst.load(date=self.ref_time, use_header=True)
        index = ([0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3])

        with pytest.raises(ValueError) as verr:
            self.testInst[index, 'profiles']

        estr = 'not convert tuple'
        assert str(verr).find(estr) > 0
        return

    def test_data_access_bad_dimension_for_multidim(self):
        """Test raises ValueError for mismatched index and data dimensions."""

        self.testInst.load(date=self.ref_time, use_header=True)
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

        self.testInst.load(self.ref_time.year, self.ref_doy, use_header=True)
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


class TestBasicsShiftedFileDates(TestBasics):
    """Basic tests for pandas `pysat.Instrument` with shifted file dates."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        reload(pysat.instruments.pysat_testing)
        self.testInst = pysat.Instrument(platform='pysat', name='testing',
                                         num_samples=10,
                                         clean_level='clean',
                                         update_files=True,
                                         mangle_file_dates=True,
                                         strict_time_flag=True,
                                         use_header=True,
                                         **self.testing_kwargs)
        self.ref_time = pysat.instruments.pysat_testing._test_dates['']['']
        self.ref_doy = 1
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
                                update_files=True, use_header=True)

        obj2 = pysat.Instrument(platform='pysat', name='testing_xarray',
                                num_samples=10, clean_level='clean',
                                update_files=True, use_header=True)
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

    def test_generic_meta_translator(self):
        """Test deprecation of `generic_meta_translator`."""

        # Catch the warnings
        with warnings.catch_warnings(record=True) as self.war:
            tinst = pysat.Instrument(use_header=True, **self.in_kwargs)
            tinst.generic_meta_translator(tinst.meta)

        self.warn_msgs = np.array(["".join(["This function has been deprecated",
                                            ". Please see "])])

        # Evaluate the warning output
        self.eval_warnings()
        return

    def test_download_freq_kwarg(self):
        """Test deprecation of download kwarg `freq`."""

        # Catch the warnings
        with warnings.catch_warnings(record=True) as self.war:
            tinst = pysat.Instrument(use_header=True, **self.in_kwargs)
            tinst.download(start=self.ref_time, freq='D')

        self.warn_msgs = np.array(["".join(["`pysat.Instrument.download` kwarg",
                                            " `freq` has been deprecated and ",
                                            "will be removed in pysat ",
                                            "3.2.0+"])])

        # Evaluate the warning output
        self.eval_warnings()
        return

    def test_download_travis_attr(self):
        """Test deprecation of instrument attribute `_test_download_travis`."""

        inst_module = pysat.instruments.pysat_testing
        # Add deprecated attribute.
        inst_module._test_download_travis = {'': {'': False}}

        self.warn_msgs = np.array([" ".join(["`_test_download_travis` has been",
                                             "deprecated and will be replaced",
                                             "by `_test_download_ci` in",
                                             "3.2.0+"])])

        # Catch the warnings.
        with warnings.catch_warnings(record=True) as self.war:
            tinst = pysat.Instrument(inst_module=inst_module, use_header=True)

        # Ensure attributes set properly.
        assert tinst._test_download_ci is False

        # Evaluate the warning output
        self.eval_warnings()
        return

    def test_filter_netcdf4_metadata(self):
        """Test deprecation warning generated by `_filter_netcdf4_metadata`."""

        # Catch the warnings
        with warnings.catch_warnings(record=True) as self.war:
            tinst = pysat.Instrument(use_header=True, **self.in_kwargs)
            tinst.load(date=self.ref_time, use_header=True)
            mdata_dict = tinst.meta._data.to_dict()
            tinst._filter_netcdf4_metadata(mdata_dict,
                                           coltype='str')

        self.warn_msgs = np.array(["".join(["`pysat.Instrument.",
                                            "_filter_netcdf4_metadata` ",
                                            "has been deprecated and will be ",
                                            "removed in pysat 3.2.0+. Use ",
                                            "`pysat.utils.io.filter_netcdf4_",
                                            "metadata` instead."])])

        # Evaluate the warning output
        self.eval_warnings()
        return

    def test_to_netcdf4(self):
        """Test deprecation warning generated by `to_netcdf4`."""

        # Catch the warnings
        with warnings.catch_warnings(record=True) as self.war:
            tinst = pysat.Instrument(use_header=True, **self.in_kwargs)
            try:
                tinst.to_netcdf4()
            except ValueError:
                pass

        self.warn_msgs = np.array(["".join(["`fname` as a kwarg has been ",
                                            "deprecated, must supply a ",
                                            "filename 3.2.0+"])])

        # Evaluate the warning output
        self.eval_warnings()
        return

    @pytest.mark.parametrize("kwargs", [{'inst_id': None}, {'tag': None}])
    def test_inst_init_with_none(self, kwargs):
        """Check that instantiation with None raises a DeprecationWarning.

        Parameters
        ----------
        kwargs : dict
            Dictionary of optional kwargs to pass through for instrument
            instantiation.

        """

        with warnings.catch_warnings(record=True) as self.war:
            pysat.Instrument('pysat', 'testing', use_header=True, **kwargs)

        self.warn_msgs = np.array(["".join(["The usage of None in `tag` and ",
                                            "`inst_id` has been deprecated ",
                                            "and will be removed in 3.2.0+. ",
                                            "Please use '' instead of None."])])

        # Evaluate the warning output
        self.eval_warnings()
        return

    def test_load_use_header(self):
        """Test that user is informed of MetaHeader on load."""

        # Determine the expected warnings
        self.warn_msgs = np.array(["".join(['Meta now contains a class for ',
                                            'global metadata (MetaHeader). ',
                                            'Default attachment of global ',
                                            'attributes to Instrument will be',
                                            ' Deprecated in pysat 3.2.0+. Set ',
                                            '`use_header=True` in this load ',
                                            'call or on Instrument ',
                                            'instantiation to remove this',
                                            ' warning.'])])

        # Capture the warnings
        with warnings.catch_warnings(record=True) as self.war:
            test_inst = pysat.Instrument(**self.in_kwargs)
            test_inst.load(date=self.ref_time, use_header=False)

        # Evaluate the warning output
        self.eval_warnings()
        return

    def test_set_2d_pandas_data(self):
        """Check that setting 2D data for pandas raises a DeprecationWarning."""

        test_inst = pysat.Instrument('pysat', 'testing2d', use_header=True)
        test_date = pysat.instruments.pysat_testing2d._test_dates['']['']
        test_inst.load(date=test_date)
        with warnings.catch_warnings(record=True) as war:
            test_inst['new_profiles'] = 2 * test_inst['profiles']

        warn_msgs = [" ".join(["Support for 2D pandas instrument",
                               "data has been deprecated and will",
                               "be removed in 3.2.0+."])]

        # Ensure the minimum number of warnings were raised.
        assert len(war) >= len(warn_msgs)

        # Test the warning messages, ensuring each attribute is present.
        testing.eval_warnings(war, warn_msgs)
        return
