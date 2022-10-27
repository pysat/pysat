#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Test the pysat routines for the orbits class."""

import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np

import pandas as pds
# Orbits period is a pandas.Timedelta kwarg, and the pandas repr
# does not include a module name. Import required to run eval
# on Orbit representation
from pandas import Timedelta  # noqa: F401
import pytest

import pysat
from pysat.utils import testing


def filter_data(inst, times):
    """Remove data from instrument, simulating gaps in the data set.

    Parameters
    ----------
    inst : pysat.Instrument
        The instrument to be filtered
    times : array of dt.datetimes
        A (2, N) array consisting of the start and stop of each gap in a list of
        N gaps

    """

    for time in times:
        idx, = np.where((inst.index > time[1]) | (inst.index < time[0]))
        inst.data = inst[idx]
    return


def assert_reversible_orbit(inst, iterations):
    """Check that an orbit breaks at the same points in both directions.

    Parameters
    ----------
    inst : pysat.Instrument
        The instrument to be checked
    iterations : int
        The number of orbits to check in each direction

    """

    n_time = []
    p_time = []
    control = inst.copy()
    for j in range(iterations):
        n_time.append(inst.index[0])
        inst.orbits.next()
    for j in range(iterations):
        inst.orbits.prev()
        p_time.append(inst.index[0])

    assert all(control.data == inst.data)

    # Don't check breaks for long gap.  See #861
    if iterations < 30:
        assert np.all(p_time == n_time[::-1])
    return


def assert_reversible_orbit_symmetric(inst, iterations):
    """Check that an orbit breaks at the same points around a day cutoff.

    Parameters
    ----------
    inst : pysat.Instrument
        The instrument to be checked
    iterations : int
        The number of orbits to check in each direction

    """

    control = inst.copy()
    for j in range(iterations):
        inst.orbits.next()

    for j in range(2 * iterations):
        inst.orbits.prev()

    for j in range(iterations):
        inst.orbits.next()
    assert all(control.data == inst.data)
    return


class TestOrbitsUserInterface(object):
    """Tests the user interface for orbits, including error handling."""

    def setup_method(self):
        """Set up User Interface unit tests."""

        self.in_args = ['pysat', 'testing']
        self.in_kwargs = {'clean_level': 'clean', 'update_files': True}
        self.testInst = None
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Tear down User Interface tests."""

        del self.in_args, self.in_kwargs, self.testInst, self.stime
        return

    def test_orbit_w_bad_kind(self):
        """Test orbit failure with bad 'kind' input."""

        self.in_kwargs['orbit_info'] = {'index': 'mlt', 'kind': 'cats'}

        testing.eval_bad_input(pysat.Instrument, ValueError,
                               "Unknown kind of orbit requested", self.in_args,
                               self.in_kwargs)
        return

    @pytest.mark.parametrize("info", [({'index': 'magnetic local time',
                                        'kind': 'longitude'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'lt'}),
                                      ({'index': 'magnetic local time',
                                       'kind': 'polar'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'orbit'})])
    def test_orbit_w_bad_orbit_info(self, info):
        """Test orbit failure on iteration with orbit initialization.

        Parameters
        ----------
        info : dict
            Passed to Instrument as `orbit_info`
        """

        self.in_kwargs['orbit_info'] = info
        self.in_kwargs['use_header'] = True
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        self.testInst.load(date=self.stime)

        testing.eval_bad_input(self.testInst.orbits.next, ValueError,
                               "Provided orbit index does not exist")
        return

    @pytest.mark.parametrize("info", [(None),
                                      ({'index': 'magnetic local time',
                                        'kind': 'polar'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'orbit'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'longitude'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'lt'})])
    def test_orbit_polar_w_missing_orbit_index(self, info):
        """Test orbit failure on iteration with missing orbit index.

        Parameters
        ----------
        info : dict
            Updated value information for Instrument kwarg 'orbit_info'

        """

        self.in_kwargs['orbit_info'] = info
        self.in_kwargs['use_header'] = True
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)

        # Force index to None beforee loading and iterating
        self.testInst.orbits.orbit_index = None
        self.testInst.load(date=self.stime)
        testing.eval_bad_input(self.testInst.orbits.next, ValueError,
                               "Orbit properties must be defined")
        return

    def test_orbit_repr(self):
        """Test the Orbit representation."""

        self.in_kwargs['orbit_info'] = {'index': 'mlt'}
        self.in_kwargs['use_header'] = True
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        out_str = self.testInst.orbits.__repr__()

        assert out_str.find("Orbits(") >= 0
        return

    def test_orbit_str(self):
        """Test the Orbit string representation with data."""

        self.in_kwargs['orbit_info'] = {'index': 'mlt'}
        self.in_kwargs['use_header'] = True
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        self.testInst.load(date=self.stime)
        out_str = self.testInst.orbits.__str__()

        assert out_str.find("Orbit Settings") >= 0
        assert out_str.find("Orbit Lind: local time") < 0
        return


class TestSpecificUTOrbits(object):
    """Run the tests for specific behaviour in the MLT orbits."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.inc_min = 97
        self.etime = None
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.inc_min, self.etime
        return

    @pytest.mark.parametrize('orbit_inc', [(0), (1), (-1), (-2), (14)])
    def test_single_orbit_call_by_index(self, orbit_inc):
        """Test successful orbit call by index.

        Parameters
        ----------
        orbit_inc : int
            Orbit index value

        """

        # Load the data
        self.testInst.load(date=self.stime)
        self.testInst.orbits[orbit_inc]

        # Increment the time
        if orbit_inc >= 0:
            self.stime += dt.timedelta(minutes=orbit_inc * self.inc_min)
        else:
            self.stime += dt.timedelta(minutes=self.inc_min
                                       * (np.ceil(1440.0 / self.inc_min)
                                          + orbit_inc))
        self.etime = self.stime + dt.timedelta(seconds=(self.inc_min * 60 - 1))

        # Test the time
        assert (self.testInst.index[0] == self.stime)
        assert (self.testInst.index[-1] == self.etime)
        return

    @pytest.mark.parametrize("orbit_ind,raise_err,err_msg", [
        (17, ValueError, 'Requested an orbit past total'),
        (None, TypeError, 'not supported between instances of')])
    def test_single_orbit_call_bad_index(self, orbit_ind, raise_err, err_msg):
        """Test orbit failure with bad index.

        Parameters
        ----------
        orbit_ind : int
            Orbit index value
        raise_err : Error
            Error that should be raised
        err_msg : str
            Error string that should be raised
        """

        self.testInst.load(date=self.stime)
        with pytest.raises(raise_err) as err:
            self.testInst.orbits[orbit_ind]

        assert str(err).find(err_msg) >= 0, '{:s} not found in {:s}'.format(
            err_msg, str(err))
        return

    def test_orbit_number_via_current_multiple_orbit_calls_in_day(self):
        """Test orbit number with multiple orbits calls in a day."""

        self.testInst.load(date=self.stime)
        self.testInst.bounds = (self.stime, None)
        true_vals = np.arange(15)
        true_vals[-1] = 0
        test_vals = []
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break
            test_vals.append(inst.orbits.current)
            assert inst.orbits.current == self.testInst.orbits.current

        assert np.all(test_vals == true_vals)
        return

    def test_all_single_orbit_calls_in_day(self):
        """Test all single orbit calls in a day."""

        self.testInst.load(date=self.stime)
        self.testInst.bounds = (self.stime, None)
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break

            # Test the start index
            self.etime = self.stime + i * relativedelta(minutes=self.inc_min)
            assert inst.index[0] == self.etime
            assert self.testInst.index[0] == self.etime

            # Test the end index
            self.etime += relativedelta(seconds=((self.inc_min * 60) - 1))
            assert inst.index[-1] == self.etime
            assert self.testInst.index[-1] == self.etime
        return

    def test_orbit_next_call_no_loaded_data(self):
        """Test orbit next call without loading data."""

        self.testInst.orbits.next()
        assert (self.testInst.index[0] == dt.datetime(2008, 1, 1))
        assert (self.testInst.index[-1] == dt.datetime(2008, 1, 1, 0, 38, 59))
        return

    def test_orbit_prev_call_no_loaded_data(self):
        """Test orbit previous call without loading data."""

        self.testInst.orbits.prev()

        # This isn't a full orbit
        assert (self.testInst.index[-1]
                == dt.datetime(2010, 12, 31, 23, 59, 59))
        assert (self.testInst.index[0] == dt.datetime(2010, 12, 31, 23, 49))
        return

    def test_single_orbit_call_orbit_starts_0_UT_using_next(self):
        """Test orbit next call with data."""

        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        self.etime = self.stime + dt.timedelta(seconds=(self.inc_min * 60 - 1))
        assert (self.testInst.index[0] == self.stime)
        assert (self.testInst.index[-1] == self.etime)
        return

    def test_single_orbit_call_orbit_starts_0_UT_using_prev(self):
        """Test orbit prev call with data."""

        self.testInst.load(date=self.stime)
        self.testInst.orbits.prev()
        self.stime += 14 * relativedelta(minutes=self.inc_min)
        self.etime = self.stime + dt.timedelta(seconds=((self.inc_min * 60)
                                                        - 1))
        assert self.testInst.index[0] == self.stime
        assert self.testInst.index[-1] == self.etime
        return

    def test_single_orbit_call_orbit_starts_off_0_UT_using_next(self):
        """Test orbit next call with data for previous day."""

        self.stime -= dt.timedelta(days=1)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == dt.datetime(2008, 12, 30, 23, 45))
        assert (self.testInst.index[-1]
                == (dt.datetime(2008, 12, 30, 23, 45)
                    + relativedelta(seconds=(self.inc_min * 60 - 1))))
        return

    def test_single_orbit_call_orbit_starts_off_0_UT_using_prev(self):
        """Test orbit previous call with data for previous day."""

        self.stime -= dt.timedelta(days=1)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.prev()
        assert (self.testInst.index[0]
                == (dt.datetime(2009, 1, 1)
                    - relativedelta(minutes=self.inc_min)))
        assert (self.testInst.index[-1]
                == (dt.datetime(2009, 1, 1) - relativedelta(seconds=1)))
        return


class TestGeneralOrbitsMLT(object):
    """Run the general orbit tests by MLT for pandas."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return

    def test_equality_with_copy(self):
        """Test that copy is the same as original."""

        self.out = self.testInst.orbits.copy()
        assert self.out == self.testInst.orbits
        return

    def test_equality_with_data_with_copy(self):
        """Test that copy is the same as original if data is loaded."""

        # Load data
        self.testInst.load(date=self.stime)

        # Load up an orbit
        self.testInst.orbits[0]
        self.out = self.testInst.orbits.copy()

        assert self.out == self.testInst.orbits
        return

    def test_inequality_different_data(self):
        """Test that equality is false if different data."""

        # Load data
        self.testInst.load(date=self.stime)

        # Load up an orbit
        self.testInst.orbits[0]

        # Make copy
        self.out = self.testInst.orbits.copy()

        # Modify data
        self.out._full_day_data = self.testInst._null_data

        assert self.out != self.testInst.orbits
        return

    def test_inequality_modified_object(self):
        """Test that equality is false if other missing attributes."""

        self.out = self.testInst.orbits.copy()

        # Remove attribute
        del self.out.orbit_index

        assert self.testInst.orbits != self.out
        return

    def test_inequality_reduced_object(self):
        """Test that equality is false if self missing attributes."""

        self.out = self.testInst.orbits.copy()
        self.out.hi_there = 'hi'
        assert self.testInst.orbits != self.out
        return

    def test_inequality_different_type(self):
        """Test that equality is false if different type."""

        assert self.testInst.orbits != self.testInst
        return

    def test_eval_repr(self):
        """Test eval of repr recreates object."""

        # Eval and repr don't play nice for custom functions
        if len(self.testInst.custom_functions) != 0:
            self.testInst.custom_clear()

        self.out = eval(self.testInst.orbits.__repr__())
        assert self.out == self.testInst.orbits
        return

    def test_repr_and_copy(self):
        """Test repr consistent with object copy."""

        # Not tested with eval due to issues with datetime
        self.out = self.testInst.orbits.__repr__()
        second_out = self.testInst.orbits.copy().__repr__()
        assert self.out == second_out
        return

    def test_load_orbits_w_empty_data(self):
        """Test orbit loading outside of the instrument data range."""

        # Set up tine instrument
        self.stime -= dt.timedelta(days=365 * 100)
        self.testInst.load(date=self.stime)
        self.testInst.orbits[0]

        # Trigger the StopIteration exception
        testing.eval_bad_input(self.testInst.orbits.next, StopIteration,
                               'Unable to find loaded date')
        return

    def test_less_than_one_orbit_of_data(self):
        """Test successful load with less than one orbit of data."""

        def truncate_data(inst):
            """Local helper function to reduce available data."""
            inst.data = inst[0:20]

        self.testInst.custom_attach(truncate_data)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()

        # A recursion issue has been observed in this area.
        # Checking for date to limit reintroduction potential.
        assert self.testInst.date == self.stime
        # Store comparison data
        saved_data = self.testInst.copy()
        self.testInst.load(date=self.stime)
        self.testInst.orbits[0]
        assert all(self.testInst.data == saved_data.data)
        d1check = self.testInst.date == saved_data.date
        assert d1check
        return

    def test_less_than_one_orbit_of_data_four_ways_two_days(self):
        """Test successful loading of different partial orbits."""

        # Create situation where the < 1 orbit split across two days
        def manual_orbits(inst):
            """Local function for breaking up orbits."""
            if inst.date == dt.datetime(2009, 1, 5):
                inst.data = inst[0:20]
            elif inst.date == dt.datetime(2009, 1, 4):
                inst.data = inst[-20:]
            return

        self.testInst.custom_attach(manual_orbits)
        self.stime += dt.timedelta(days=3)
        self.testInst.load(date=self.stime)

        # Starting from no orbit calls next loads first orbit
        self.testInst.orbits.next()

        # Store comparison data
        saved_data = self.testInst.copy()
        self.testInst.load(date=self.stime + dt.timedelta(days=1))
        self.testInst.orbits[0]
        if self.testInst.orbits.num == 1:
            # Equivalence occurs only when there is one orbit,
            # some test settings can violate this assumption.
            assert all(self.testInst.data == saved_data.data)

        self.testInst.load(date=self.stime)
        self.testInst.orbits[0]
        assert all(self.testInst.data == saved_data.data)

        self.testInst.load(date=self.stime + dt.timedelta(days=1))
        self.testInst.orbits.prev()
        if self.testInst.orbits.num == 1:
            assert all(self.testInst.data == saved_data.data)

        # A recursion issue has been observed in this area.
        # Checking for date to limit reintroduction potential.
        d1check = self.testInst.date == saved_data.date
        assert d1check
        return

    @pytest.mark.parametrize("iterations", [(10), (20)])
    def test_repeated_orbit_calls(self, iterations):
        """Test that repeated orbit calls are reversible."""

        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        assert_reversible_orbit(self.testInst, iterations)
        return

    @pytest.mark.parametrize("iterations", [(10), (20)])
    def test_repeated_orbit_calls_alternative(self, iterations):
        """Test repeated orbit calls are reversible using alternate pattern."""

        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        assert_reversible_orbit_symmetric(self.testInst, iterations)
        return


class TestGeneralOrbitsMLTxarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests by MLT for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestGeneralOrbitsNonStandardIteration(object):
    """Test for non standard data setups.

    Note
    ----
    Create an iteration window that is larger than step size.
    Ensure the overlapping data doesn't end up in the orbit iteration.

    """

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True,
                                         use_header=True)
        self.testInst.bounds = (self.testInst.files.files.index[0],
                                self.testInst.files.files.index[11],
                                '2D', dt.timedelta(days=3))
        self.orbit_starts = []
        self.orbit_stops = []
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.orbit_starts, self.orbit_stops
        return

    def test_no_orbit_overlap_with_overlapping_iteration(self):
        """Ensure error when overlap in iteration data."""

        testing.eval_bad_input(self.testInst.orbits.next, ValueError,
                               'Orbit iteration is not currently supported ')

        return

    @pytest.mark.parametrize("bounds_type", ['by_date', 'by_file'])
    def test_no_orbit_overlap_with_nonoverlapping_iteration(self, bounds_type):
        """Ensure orbit data does not overlap when overlap in iteration data.

        Parameters
        ----------
        bounds_type : str
            Enforce bounds `by_date` or `by_file`

        """

        if bounds_type == 'by_date':
            bounds = (self.testInst.files.files.index[0],
                      self.testInst.files.files.index[11],
                      '2D', dt.timedelta(days=2))
        elif bounds_type == 'by_file':
            bounds = (self.testInst.files[0], self.testInst.files[11], 2, 2)

        self.testInst.bounds = bounds

        for inst in self.testInst.orbits:
            self.orbit_starts.append(inst.index[0])
            self.orbit_stops.append(inst.index[-1])
        self.orbit_starts = pds.Series(self.orbit_starts)
        self.orbit_stops = pds.Series(self.orbit_stops)
        assert self.orbit_starts.is_monotonic_increasing
        assert self.orbit_stops.is_monotonic_increasing
        return


class TestGeneralOrbitsLong(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Longitude for pandas."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestGeneralOrbitsLongXarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Longitude for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestGeneralOrbitsOrbitNumber(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Orbit Number for pandas."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestGeneralOrbitsOrbitNumberXarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Orbit Number for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestGeneralOrbitsLatitude(TestGeneralOrbitsMLT):
    """Run the general orbit tests for orbits defined by Latitude for pandas."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestGeneralOrbitsLatitudeXarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests for orbits defined by Latitude for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestOrbitsGappyData(object):
    """Gappy orbit tests defined  for orbits defined by MLT for pandas."""

    def setup_class(self):
        """Set up variables inherited by all classes."""

        self.deltime = np.array([[dt.timedelta(hours=1, minutes=37),
                                  dt.timedelta(hours=3, minutes=14)],
                                 [dt.timedelta(hours=10),
                                  dt.timedelta(hours=12)],
                                 [dt.timedelta(hours=22),
                                  dt.timedelta(days=1, hours=2)],
                                 [dt.timedelta(days=12),
                                  dt.timedelta(days=14)],
                                 [dt.timedelta(days=19, hours=1),
                                  dt.timedelta(days=24, hours=23)],
                                 [dt.timedelta(days=24, hours=23, minutes=30),
                                  dt.timedelta(days=25, hours=3)]])

    def teardown_class(self):
        """Clean up variables inherited by all classes."""

        del self.deltime

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return

    @pytest.mark.parametrize("day,iterations", [(1, 20), (19, 45), (25, 20)])
    def test_repeat_orbit_calls_cutoffs_with_gaps(self, day, iterations):
        """Test that orbits are selected at same cutoffs when reversed.

        Parameters
        ----------
        day : int
            Loads data for `self.stime` + `day` - 1
        iterations : int
            Number of iterations to test, passed to `assert_reversible_orbit`

        """

        # Start date offsets aligned to times defined in TestOrbitsGappyData
        self.testInst.load(date=(self.stime + dt.timedelta(days=(day - 1))))
        self.testInst.orbits.next()
        assert_reversible_orbit(self.testInst, iterations)
        return


class TestOrbitsGappyDataXarray(TestOrbitsGappyData):
    """Gappy orbit tests defined  for orbits defined by MLT for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True,
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return


class TestOrbitsGappyData2(object):
    """Additional gappy orbit tests for orbits defined by MLT for pandas."""

    def setup_class(self):
        """Set up variables inherited by all classes."""

        self.times = [[dt.datetime(2008, 12, 31, 4),
                       dt.datetime(2008, 12, 31, 5, 37)],
                      [dt.datetime(2009, 1, 1),
                       dt.datetime(2009, 1, 1, 1, 37)]]
        for seconds in np.arange(38):
            day = (dt.datetime(2009, 1, 2)
                   + dt.timedelta(days=int(seconds)))
            self.times.append([day, day
                               + dt.timedelta(hours=1, minutes=37,
                                              seconds=int(seconds))
                               - dt.timedelta(seconds=20)])

    def teardown_class(self):
        """Clean up variables inherited by all classes."""

        del self.times

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.testInst.custom_attach(filter_data, kwargs={'times': self.times})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return

    def test_repeated_orbit_calls_alternative(self):
        """Test repeated orbit calls are reversible."""

        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        assert_reversible_orbit_symmetric(self.testInst, 20)
        return


class TestOrbitsGappyData2Xarray(TestOrbitsGappyData2):
    """Run additional gappy orbit tests for orbits defined by MLT for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.testInst.custom_attach(filter_data, kwargs={'times': self.times})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime
        return


class TestOrbitsGappyLongData(TestOrbitsGappyData):
    """Gappy orbit tests defined  for orbits defined by Longitude for pandas."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         use_header=True)

        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return


class TestOrbitsGappyLongDataXarray(TestOrbitsGappyData):
    """Gappy orbit tests defined  for orbits defined by Longitude for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return


class TestOrbitsGappyOrbitNumData(TestOrbitsGappyData):
    """Gappy orbit tests defined  by Orbit Number for pandas."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return


class TestOrbitsGappyOrbitNumDataXarray(TestOrbitsGappyData):
    """Gappy orbit tests defined  by Orbit Number for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         use_header=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return


class TestOrbitsGappyOrbitLatData(TestOrbitsGappyData):
    """Gappy orbit tests defined  by Latitude for pandas."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         use_header=True)

        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return


class TestOrbitsGappyOrbitLatDataXarray(TestOrbitsGappyData):
    """Gappy orbit tests defined by Latitude for xarray."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         use_header=True)

        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.gaps = self.stime + self.deltime
        self.testInst.custom_attach(filter_data, kwargs={'times': self.gaps})
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.testInst, self.stime, self.gaps
        return
