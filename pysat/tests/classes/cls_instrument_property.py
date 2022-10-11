"""Test for instrument properties in the pysat Instrument object and methods.

Note
----
Base class stored here, but tests inherited by test_instrument.py

"""

import datetime as dt
from importlib import reload
import logging
import numpy as np
import warnings

import pandas as pds
import pytest
import xarray as xr

import pysat
from pysat.utils import testing
from pysat.utils.time import filter_datetime_input


class InstPropertyTests(object):
    """Basic tests for `pysat.Instrument` properties.

    Attributes
    ----------
    out : any
        Stores relevant output in a test method for further testing
    ref_time : dt.datetime
        Datetime for testing. Comes from instrument module under test.
    ref_doy : int
        Day of year for testing
    test_inst : pysat.Instrument
        Instrument to test
    testing_kwargs : dict
        Dictionary of kwargs used for testing custom kwarg support across
        the range of `pysat.Instrument` dataset module methods
    xarray_epoch_name : str
        String used within a xarray testing `pysat.Instrument` object

    Note
    ----
    Inherited by classes in test_instrument.py.  Setup and teardown methods are
    specified there.

    See Also
    --------
    `pysat.tests.test_instrument`

    """

    def test_basic_instrument_bad_keyword_init(self):
        """Check for error when instantiating with bad load keywords on init."""

        # Test that the correct error is raised
        testing.eval_bad_input(pysat.Instrument, ValueError,
                               "unknown keyword supplied",
                               input_kwargs={'platform': self.testInst.platform,
                                             'name': self.testInst.name,
                                             'num_samples': 10,
                                             'clean_level': 'clean',
                                             'unsupported_keyword_yeah': True})
        return

    @pytest.mark.parametrize('kwarg', ['supported_tags', 'start', 'stop',
                                       'freq', 'date_array', 'data_path'])
    def test_basic_instrument_reserved_keyword(self, kwarg):
        """Check for error when instantiating with reserved keywords.

        Parameters
        ----------
        kwarg : str
            Name of reserved keyword.

        """
        # Set the input
        in_kwargs = {'platform': self.testInst.platform,
                     'name': self.testInst.name, 'num_samples': 10,
                     'clean_level': 'clean', kwarg: '1s'}

        # Check that the correct error is raised
        estr = ''.join(('Reserved keyword "', kwarg, '" is not ',
                        'allowed at instantiation.'))
        testing.eval_bad_input(pysat.Instrument, ValueError, estr,
                               input_kwargs=in_kwargs)

        return

    @pytest.mark.parametrize('attr', ['_test_download', '_test_download_ci',
                                      '_password_req'])
    @pytest.mark.parametrize('setting', [True, False])
    def test_basic_instrument_download_kwargs(self, attr, setting):
        """Check that download flags are appropriately set.

        Parameters
        ----------
        attr : str
            Name of test attribute to check.
        setting : bool
            Setting to test for attr.

        """

        inst_module = getattr(pysat.instruments,
                              '_'.join((self.testInst.platform,
                                        self.testInst.name)))
        # Update settings for this test
        setattr(inst_module, attr, {'': {'': setting}})
        self.testInst = pysat.Instrument(inst_module=inst_module)

        assert getattr(self.testInst, attr) is setting
        return

    def test_list_files(self):
        """Test that `inst.files.files` returns a pandas series."""

        files = self.testInst.files.files
        assert isinstance(files, pds.Series)
        return

    @pytest.mark.parametrize("remote_func,num", [('remote_file_list', 31),
                                                 ('remote_date_range', 2)])
    def test_remote_functions(self, remote_func, num):
        """Test simulated remote functions for valid list of files.

        Parameters
        ----------
        remote_func : str
            Name of remote function to test.
        num : int
            Number of filenames that should be retrieved by remote_func.

        """

        stop = self.ref_time + dt.timedelta(days=30)
        self.out = getattr(self.testInst, remote_func)(start=self.ref_time,
                                                       stop=stop)
        assert len(self.out) == num

        # Get index if a pds.Series is returned.
        if isinstance(self.out, pds.Series):
            self.out = self.out.index
        assert filter_datetime_input(self.out[0]) == self.ref_time
        assert filter_datetime_input(self.out[-1]) == stop
        return

    @pytest.mark.parametrize("no_remote_files", [True, False])
    @pytest.mark.parametrize("download_keys", [
        (["start"]), (["start", "stop"]), (["date_array"]), ([])])
    def test_download_updated_files(self, caplog, no_remote_files,
                                    download_keys):
        """Test `download_updated_files` and default bounds are updated.

        Parameters
        ----------
        no_remote_files : bool
            If True, `list_remote_files` method is removed from Instrument.
        download_keys : list
            List of keys to set for `download` kwargs.

        """

        dkwargs = {}
        if "start" in download_keys:
            dkwargs["start"] = self.testInst.files.files.index[0] \
                - dt.timedelta(days=1)
        if "stop" in download_keys:
            dkwargs["stop"] = self.testInst.files.files.index[-1] \
                + dt.timedelta(days=1)
        if "date_array" in download_keys:
            dkwargs["date_array"] = pds.date_range(
                self.testInst.files.files.index[0] - dt.timedelta(days=1),
                self.testInst.files.files.index[-1] + dt.timedelta(days=1),
                freq='1D')

        # If desired, test using an Instrument without `list_remote_files`
        if no_remote_files:
            inst_module = self.testInst.inst_module
            del inst_module.list_remote_files
            self.testInst = pysat.Instrument(inst_module=inst_module)

        # Run the method and get the log output
        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download_updated_files(**dkwargs)

        # Test the logging output for the following conditions:
        # - perform a local search,
        # - new files are found,
        # - download new files, and
        # - update local file list.
        assert "local files" in caplog.text
        assert "with new" in caplog.text

        # Test for logging output based on the presence of a remote file
        # listing method
        if no_remote_files:
            assert "No remote file listing method, looking " in caplog.text

            # If no start/stop date is provided and there is no remote method,
            # no files to update will be found since there are no gaps.
            if len(download_keys) == 0:
                assert "Did not find any new or updated files" in caplog.text
                assert "Updating pysat file list" not in caplog.text
            else:
                assert "Downloading data to" in caplog.text
                assert "Updating pysat file list" in caplog.text
        else:
            assert "Downloading data to" in caplog.text
            assert "Updating pysat file list" in caplog.text
            assert "A remote file listing method exists, looking" in caplog.text

        return

    @pytest.mark.parametrize("file_bounds", [True, False])
    @pytest.mark.parametrize("non_default", [True, False])
    def test_download_bounds(self, caplog, file_bounds, non_default):
        """Test `download` with updated bounds.

        Parameters
        ----------
        file_bounds : bool
            If True, check by filename.  If False, check by date.
        non_default : bool
            If True, check that bounds are updated appropriately.

        """

        # Set the Instrument bounds to enable different types of file
        # checking at the download level. This is an integration test and
        # may need to be moved.
        if file_bounds:
            if non_default:
                # Set bounds to second and second to last file
                self.testInst.bounds = (self.testInst.files[1],
                                        self.testInst.files[-2])
            else:
                # Set bounds to first and last file
                self.testInst.bounds = (self.testInst.files[0],
                                        self.testInst.files[-1])
        else:
            if non_default:
                # Set bounds to first and first date
                self.testInst.bounds = (self.testInst.files.start_date,
                                        self.testInst.files.start_date)

        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download()

        # Test for logging output based on the bound setting method
        if non_default:
            assert "Updating instrument object bounds " not in caplog.text
        else:
            text = caplog.text
            if file_bounds:
                assert "Updating instrument object bounds by file" in text
            else:
                assert "Updating instrument object bounds by date" in text
        return

    def test_download_recent_data(self, caplog):
        """Test download of recent data."""

        with caplog.at_level(logging.INFO, logger='pysat'):
            self.testInst.download()

        # Ensure user was told that recent data will be downloaded
        assert "most recent data by default" in caplog.text

        # Ensure user was notified of new files being download
        assert "Downloading data to" in caplog.text

        # Ensure user was notified of updates to the local file list
        assert "Updating pysat file list" in caplog.text

        return

    def test_download_bad_date_range(self, caplog):
        """Test download with bad date input."""

        with caplog.at_level(logging.WARNING, logger='pysat'):
            self.testInst.download(start=self.ref_time,
                                   stop=self.ref_time - dt.timedelta(days=10))

        # Ensure user is warned about not calling download due to bad time input
        assert "Requested download over an empty date range" in caplog.text
        return

    def test_today_yesterday_and_tomorrow(self):
        """Test the correct instantiation of yesterday/today/tomorrow dates."""

        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day)
        assert self.out == self.testInst.today()
        assert self.out - dt.timedelta(days=1) == self.testInst.yesterday()
        assert self.out + dt.timedelta(days=1) == self.testInst.tomorrow()
        return

    def test_filtered_date_attribute(self):
        """Test use of filter during date assignment."""

        self.ref_time = dt.datetime.utcnow()
        self.out = dt.datetime(self.ref_time.year, self.ref_time.month,
                               self.ref_time.day)
        self.testInst.date = self.ref_time
        assert self.out == self.testInst.date
        return

    def test_copy(self):
        """Test `Instrument.copy()`."""

        inst_copy = self.testInst.copy()
        assert inst_copy == self.testInst
        return

    def test_copy_from_reference(self):
        """Test `.copy()` if invoked from a `weakref.proxy` of Instrument."""

        inst_copy = self.testInst.orbits.inst.copy()
        inst_copy2 = self.testInst.files.inst_info['inst'].copy()
        assert inst_copy == self.testInst
        assert inst_copy == inst_copy2
        assert inst_copy2 == self.testInst
        return

    def test_copy_w_inst_module(self):
        """Test `.copy()` with inst_module != None."""

        # Assign module to inst_module
        self.testInst.inst_module = pysat.instruments.pysat_testing

        inst_copy = self.testInst.copy()

        # Confirm equality and that module is still present
        assert inst_copy == self.testInst
        assert inst_copy.inst_module == pysat.instruments.pysat_testing
        assert self.testInst.inst_module == pysat.instruments.pysat_testing

        return

    def test_retrieve_bad_attribute(self):
        """Test that AttributeError is raised if bad attribute is retrieved."""

        with pytest.raises(AttributeError) as aerr:
            self.testInst.bad_attr

        assert str(aerr).find("object has no attribute") >= 0
        return

    def test_base_attr(self):
        """Test retrieval of base attribute."""

        self.testInst._base_attr
        assert '_base_attr' in dir(self.testInst)
        return

    def test_inst_attributes_not_overwritten(self):
        """Test that custom Instrument attributes are preserved on load."""

        greeting = '... listen!'
        self.testInst.hei = greeting
        self.testInst.load(date=self.ref_time, use_header=True)
        assert self.testInst.hei == greeting
        return

    def test_basic_repr(self):
        """The repr output will match the beginning of the str output."""

        self.out = self.testInst.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find("pysat.Instrument(") == 0
        return

    def test_basic_str(self):
        """Check for lines from each decision point in repr."""

        self.out = self.testInst.__str__()
        assert isinstance(self.out, str)
        assert self.out.find('pysat Instrument object') == 0

        # No custom functions
        assert self.out.find('Custom Functions: 0') > 0

        # No orbital info
        assert self.out.find('Orbit Settings') < 0

        # Files exist for test inst
        assert self.out.find('Date Range:') > 0

        # No loaded data
        assert self.out.find('No loaded data') > 0
        assert self.out.find('Number of variables') < 0
        assert self.out.find('uts') < 0
        return

    def test_str_w_orbit(self):
        """Test string output with Orbit data."""

        reload(pysat.instruments.pysat_testing)
        orbit_info = {'index': 'mlt',
                      'kind': 'local time',
                      'period': np.timedelta64(97, 'm')}
        testInst = pysat.Instrument(platform='pysat', name='testing',
                                    num_samples=10,
                                    clean_level='clean',
                                    update_files=True,
                                    orbit_info=orbit_info,
                                    use_header=True)

        self.out = testInst.__str__()

        # Check that orbit info is passed through
        assert self.out.find('Orbit Settings') > 0
        assert self.out.find(orbit_info['kind']) > 0
        assert self.out.find('Loaded Orbit Number: 0') > 0

        # Activate orbits, check that message has changed
        testInst.load(self.ref_time.year, self.ref_doy, use_header=True)
        testInst.orbits.next()
        self.out = testInst.__str__()
        assert self.out.find('Loaded Orbit Number: 1') > 0
        return

    def test_str_w_padding(self):
        """Test string output with data padding."""

        self.testInst.pad = dt.timedelta(minutes=5)
        self.out = self.testInst.__str__()
        assert self.out.find('Data Padding: 0:05:00') > 0
        return

    def test_str_w_custom_func(self):
        """Test string output with custom function."""

        def passfunc(self):
            pass

        self.testInst.custom_attach(passfunc)
        self.out = self.testInst.__str__()
        assert self.out.find('passfunc') > 0
        return

    def test_str_w_load_lots_data(self):
        """Test string output with loaded data with many variables."""

        self.testInst.load(self.ref_time.year, self.ref_doy, use_header=True)
        self.out = self.testInst.__str__()
        assert self.out.find('Number of variables:') > 0
        assert self.out.find('...') > 0
        return

    def test_str_w_load_less_data(self):
        """Test string output with loaded data with few (4) variables."""

        # Load the test data
        self.testInst.load(self.ref_time.year, self.ref_doy, use_header=True)

        # Ensure the desired data variable is present and delete all others
        # 4-6 variables are needed to test all lines; choose the lesser limit
        nvar = 4
        self.testInst.data = self.testInst.data[self.testInst.variables[:nvar]]

        # Test output with one data variable
        self.out = self.testInst.__str__()
        assert self.out.find('Number of variables: 4') > 0
        assert self.out.find('Variable Names') > 0
        for n in range(nvar):
            assert self.out.find(self.testInst.variables[n]) > 0
        return

    def test_instrument_init(self):
        """Test if init function supplied by instrument can modify object."""

        assert self.testInst.new_thing
        return

    @pytest.mark.parametrize('del_routine', ['list_files', 'load'])
    def test_custom_instrument_load_incomplete(self, del_routine):
        """Test if exception is thrown if supplied routines are incomplete.

        Parameters
        ----------
        del_routine : str
            Name of required routine to delete from module.

        """

        import pysat.instruments.pysat_testing as test
        delattr(test, del_routine)

        estr = 'A `{:}` function is required'.format(del_routine)
        testing.eval_bad_input(pysat.Instrument, AttributeError, estr,
                               input_kwargs={'inst_module': test, 'tag': '',
                                             'clean_level': 'clean'})
        return

    @pytest.mark.parametrize("func, kwarg, val", [('init', 'test_init_kwarg',
                                                   True),
                                                  ('clean', 'test_clean_kwarg',
                                                   False),
                                                  ('preprocess',
                                                   'test_preprocess_kwarg',
                                                   'test_phrase'),
                                                  ('load', 'test_load_kwarg',
                                                   'bright_light'),
                                                  ('list_files',
                                                   'test_list_files_kwarg',
                                                   'sleep_tight'),
                                                  ('list_remote_files',
                                                   'test_list_remote_kwarg',
                                                   'one_eye_open'),
                                                  ('download',
                                                   'test_download_kwarg',
                                                   'exit_night')
                                                  ])
    def test_instrument_function_keywords(self, caplog, func, kwarg, val):
        """Test if Instrument function keywords are registered by pysat.

        Parameters
        ----------
        func : str
            Function name to test.
        kwarg : str
            Keyword argument of function to modify.
        val : str
            Replacement value for modified kwarg.

        """

        with caplog.at_level(logging.INFO, logger='pysat'):
            # Trigger load functions
            self.testInst.load(date=self.ref_time, use_header=True)

            # Refresh files to trigger other functions
            self.testInst.files.refresh()

            # Get remote file list
            self.testInst.download_updated_files()

        # Confirm kwargs made it where they should be
        assert kwarg in self.testInst.kwargs[func]
        assert self.testInst.kwargs[func][kwarg] == val

        # Check if function under test can assign attributes, not all can
        live_check = hasattr(self.testInst, kwarg)

        if live_check:
            # Confirm attribute value
            assert getattr(self.testInst, kwarg) == val
        else:
            # Confirm value echoed to log for functions that can't assign
            # attributes. Get log text.
            captured = caplog.text

            # Test for expected string
            test_str = ''.join((kwarg, ' = ', str(val)))
            assert captured.find(test_str) >= 0

        return

    @pytest.mark.parametrize("func, kwarg", [('clean', 'test_clean_kwarg'),
                                             ('preprocess',
                                              'test_preprocess_kwarg'),
                                             ('load',
                                              'test_load_kwarg'),
                                             ('list_files',
                                              'test_list_files_kwarg'),
                                             ('list_remote_files',
                                              'test_list_remote_kwarg'),
                                             ('download',
                                              'test_download_kwarg')
                                             ])
    def test_instrument_function_keyword_liveness(self, caplog, func, kwarg):
        """Test if changed keywords are propagated by pysat to functions.

        Parameters
        ----------
        func : str
            Function name to test.
        kwarg : str
            Keyword argument of function to modify.

        """

        # Assign a new value to a keyword argument
        val = 'live_value'
        self.testInst.kwargs[func][kwarg] = val

        with caplog.at_level(logging.INFO, logger='pysat'):
            # Trigger load functions
            self.testInst.load(date=self.ref_time, use_header=True)

            # Refresh files to trigger other functions
            self.testInst.files.refresh()

            # Get remote file list
            self.testInst.download_updated_files()

        # The passed parameter should be set on Instrument, if a full function
        live_check = hasattr(self.testInst, kwarg)

        # Not all functions are passed the instrument object
        if live_check:
            # Confirm attribute value
            assert getattr(self.testInst, kwarg) == val
        else:
            # Confirm value echoed to log for functions that can't assign
            # attributes.
            captured = caplog.text

            # Confirm presence of test string in log
            test_str = ''.join((kwarg, ' = ', str(val)))
            assert captured.find(test_str) >= 0

        return

    def test_error_undefined_input_keywords(self):
        """Test for error if undefined keywords provided at instantiation."""

        # Add a new keyword
        self.testInst.kwargs['load']['undefined_keyword1'] = True
        self.testInst.kwargs['load']['undefined_keyword2'] = False

        estr = "".join(("unknown keywords supplied: ['undefined_keyword1',",
                        " 'undefined_keyword2']"))
        with pytest.raises(ValueError) as verr:
            eval(repr(self.testInst))

        assert str(verr).find(estr) >= 0, "{:s} not found in {:}".format(
            estr, str(verr))
        return

    def test_supported_input_keywords(self):
        """Test that supported keywords exist."""

        funcs = ['load', 'init', 'list_remote_files', 'list_files', 'download',
                 'preprocess', 'clean']

        # Test instruments all have a supported keyword. Ensure keyword
        # present for all functions.
        for func in funcs:
            assert func in self.testInst.kwargs_supported
            assert len(self.testInst.kwargs_supported[func]) > 0

        # Confirm all user provided keywords are in the supported keywords
        for func in funcs:
            for kwarg in self.testInst.kwargs[func]:
                assert kwarg in self.testInst.kwargs_supported[func]

        return

    def test_optional_unknown_data_dir(self, caplog):
        """Test log warning raised when supplying an optional bad data path."""

        inst_module = getattr(pysat.instruments,
                              '_'.join((self.testInst.platform,
                                        self.testInst.name)))

        # Update settings for this test
        with caplog.at_level(logging.WARNING, logger='pysat'):
            self.testInst = pysat.Instrument(inst_module=inst_module,
                                             data_dir="not_a_directory")

        captured = caplog.text
        assert captured.find("data directory doesn't exist") >= 0
        assert self.testInst.data_dir is None
        return

    @pytest.mark.parametrize(
        "kwargs,estr",
        [({'inst_id': 'invalid_inst_id'},
          "'invalid_inst_id' is not one of the supported inst_ids."),
         ({'inst_id': '', 'tag': 'bad_tag'},
          "'bad_tag' is not one of the supported tags.")])
    def test_error_bad_instrument_object(self, kwargs, estr):
        """Ensure instantiation with invalid inst_id or tag errors.

        Parameters
        ----------
        kwargs : dict
            Dictionary with keys for instrument instantiation.  One of the
            values should be bad to trigger an error message.
        estr : str
            Text that should be contained in the error message.

        """
        kwargs['platform'] = self.testInst.platform
        kwargs['name'] = self.testInst.name

        testing.eval_bad_input(pysat.Instrument, ValueError, estr,
                               input_kwargs=kwargs)
        return

    def test_get_var_type_code_unknown_type(self):
        """Ensure that Error is thrown if unknown type is supplied."""

        testing.eval_bad_input(self.testInst._get_var_type_code, TypeError,
                               'Unknown Variable', [type(None)])
        return

    @pytest.mark.parametrize("kwargs", [{'platform': 'doctor'},
                                        {'name': 'who'},
                                        {'platform': 'doctor', 'name': 'who'}])
    def test_warn_inst_module_platform_name(self, kwargs):
        """Test that warning is raised if multiple specifications provided.

        Parameters
        ----------
        kwargs : dict
            Additional specifications provided that should raise a warning.

        """

        with warnings.catch_warnings(record=True) as war:
            tinst = pysat.Instrument(inst_module=self.testInst.inst_module,
                                     **kwargs)

        default_str = ' '.join(["inst_module supplied along with",
                                "platform/name. Defaulting to"])
        assert len(war) >= 1
        assert war[0].category == UserWarning
        assert default_str in str(war[0].message)

        # Make sure isntrument loaded as inst_module
        assert tinst.inst_module == self.testInst.inst_module

    def test_change_inst_pandas_format(self):
        """Test changing `pandas_format` attribute works."""
        new_format = not self.testInst.pandas_format
        new_type = pds.DataFrame if new_format else xr.Dataset

        # Save current data format hidden attributes
        current_null = self.testInst._null_data
        current_library = self.testInst._data_library

        # Assign inverted `pandas_format` setting
        self.testInst.pandas_format = new_format

        # Confirm assignment of visible and hidden attributes
        assert self.testInst.pandas_format == new_format
        assert not isinstance(self.testInst._null_data, type(current_null))
        assert current_library != self.testInst._data_library

        # Confirm internal consistency
        assert isinstance(self.testInst._null_data, self.testInst._data_library)
        assert isinstance(self.testInst._null_data, new_type)

        return

    def test_change_inst_pandas_format_loaded_data(self):
        """Test changing `pandas_format` attribute when data loaded."""

        # Load data
        self.testInst.load(date=self.ref_time)

        # Get inverted pandas_format setting
        new_format = not self.testInst.pandas_format

        # Assign inverted `pandas_format` setting
        with pytest.raises(ValueError) as err:
            self.testInst.pandas_format = new_format

        estr = "Can't change data type setting while data is "
        assert str(err).find(estr) > 0

        return
