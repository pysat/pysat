import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np

import pandas as pds
import pytest

import pysat


class TestOrbitsUserInterface():
    def setup(self):
        """ Set up User Interface unit tests
        """
        self.in_args = ['pysat', 'testing']
        self.in_kwargs = {'clean_level': 'clean', 'update_files': True}
        self.testInst = None
        self.stime = dt.datetime(2009, 1, 1)

    def teardown(self):
        """ Tear down user interface tests
        """
        del self.in_args, self.in_kwargs, self.testInst, self.stime

    def test_orbit_w_bad_kind(self):
        """ Test orbit failure with bad 'kind' input
        """
        self.in_kwargs['orbit_info'] = {'index': 'mlt', 'kind': 'cats'}
        with pytest.raises(ValueError):
            self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)

    @pytest.mark.parametrize("info", [({'index': 'magnetic local time',
                                        'kind': 'longitude'}),
                                      (None),
                                      ({'index': 'magnetic local time',
                                        'kind': 'lt'}),
                                      ({'index': 'magnetic local time',
                                       'kind': 'polar'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'orbit'})])
    def test_orbit_w_bad_orbit_info(self, info):
        """ Test orbit failure on iteration with orbit initialization
        """
        self.in_kwargs['orbit_info'] = info
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        self.testInst.load(date=self.stime)

        with pytest.raises(ValueError):
            self.testInst.orbits.next()

    @pytest.mark.parametrize("info", [({'index': 'magnetic local time',
                                        'kind': 'polar'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'orbit'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'longitude'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'lt'})])
    def test_orbit_polar_w_missing_orbit_index(self, info):
        """ Test orbit failure oon iteration with missing orbit index
        """
        self.in_kwargs['orbit_info'] = info
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)

        # Force index to None beforee loading and iterating
        self.testInst.orbits.orbit_index = None
        self.testInst.load(date=self.stime)
        with pytest.raises(ValueError):
            self.testInst.orbits.next()

    def test_orbit_repr(self):
        """ Test the Orbit representation
        """
        self.in_kwargs['orbit_info'] = {'index': 'mlt'}
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        out_str = self.testInst.orbits.__repr__()

        assert out_str.find("Orbits(") >= 0

    def test_orbit_str(self):
        """ Test the Orbit string representation with data
        """
        self.in_kwargs['orbit_info'] = {'index': 'mlt'}
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        self.testInst.load(date=self.stime)
        out_str = self.testInst.orbits.__str__()

        assert out_str.find("Orbit Settings") >= 0
        assert out_str.find("Orbit Lind: local time") < 0


class TestSpecificUTOrbits():
    def setup(self):
        """Runs before every method to create a clean testing setup
        """
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.stime = dt.datetime(2009, 1, 1)
        self.inc_min = 97
        self.etime = None

    def teardown(self):
        """Runs after every method to clean up previous testing
        """
        del self.testInst, self.stime, self.inc_min, self.etime

    @pytest.mark.parametrize('orbit_inc', [(0), (1), (-1), (-2), (14)])
    def test_single_orbit_call_by_index(self, orbit_inc):
        """Test successful orbit call by index
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

    @pytest.mark.parametrize("orbit_ind,raise_err", [(17, Exception),
                                                     (None, TypeError)])
    def test_single_orbit_call_bad_index(self, orbit_ind, raise_err):
        """ Test orbit failure with bad index
        """
        self.testInst.load(date=self.stime)
        with pytest.raises(raise_err):
            self.testInst.orbits[orbit_ind]

    def test_oribt_number_via_current_multiple_orbit_calls_in_day(self):
        """ Test orbit number with mulitple orbits calls in a day
        """
        self.testInst.load(date=self.stime)
        self.testInst.bounds = (self.stime, None)
        true_vals = np.arange(15)
        true_vals[-1] = 0
        test_vals = []
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break
            test_vals.append(self.testInst.orbits.current)

        assert np.all(test_vals == true_vals)

    def test_all_single_orbit_calls_in_day(self):
        """ Test all single orbit calls in a day
        """
        self.testInst.load(date=self.stime)
        self.testInst.bounds = (self.stime, None)
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break

            # Test the start index
            self.etime = self.stime + i * relativedelta(minutes=self.inc_min)
            assert self.testInst.index[0] == self.etime

            # Test the end index
            self.etime += relativedelta(seconds=((self.inc_min * 60) - 1))
            assert self.testInst.index[-1] == self.etime

    def test_orbit_next_call_no_loaded_data(self):
        """ Test orbit next call without loading data
        """
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == dt.datetime(2008, 1, 1))
        assert (self.testInst.index[-1] == dt.datetime(2008, 1, 1, 0, 38, 59))

    def test_orbit_prev_call_no_loaded_data(self):
        """ Test orbit previous call without loading data
        """
        self.testInst.orbits.prev()
        # this isn't a full orbit
        assert (self.testInst.index[-1]
                == dt.datetime(2010, 12, 31, 23, 59, 59))
        assert (self.testInst.index[0] == dt.datetime(2010, 12, 31, 23, 49))

    def test_single_orbit_call_orbit_starts_0_UT_using_next(self):
        """ Test orbit next call with data
        """
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        self.etime = self.stime + dt.timedelta(seconds=(self.inc_min * 60 - 1))
        assert (self.testInst.index[0] == self.stime)
        assert (self.testInst.index[-1] == self.etime)

    def test_single_orbit_call_orbit_starts_0_UT_using_prev(self):
        """ Test orbit prev call with data
        """
        self.testInst.load(date=self.stime)
        self.testInst.orbits.prev()
        self.stime += 14 * relativedelta(minutes=self.inc_min)
        self.etime = self.stime + dt.timedelta(seconds=((self.inc_min * 60)
                                                        - 1))
        assert self.testInst.index[0] == self.stime
        assert self.testInst.index[-1] == self.etime

    def test_single_orbit_call_orbit_starts_off_0_UT_using_next(self):
        """ Test orbit next call with data for previous day
        """
        self.stime -= dt.timedelta(days=1)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == dt.datetime(2008, 12, 30, 23, 45))
        assert (self.testInst.index[-1]
                == (dt.datetime(2008, 12, 30, 23, 45)
                    + relativedelta(seconds=(self.inc_min * 60 - 1))))

    def test_single_orbit_call_orbit_starts_off_0_UT_using_prev(self):
        self.stime -= dt.timedelta(days=1)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.prev()
        assert (self.testInst.index[0]
                == (dt.datetime(2009, 1, 1)
                    - relativedelta(minutes=self.inc_min)))
        assert (self.testInst.index[-1]
                == (dt.datetime(2009, 1, 1) - relativedelta(seconds=1)))


class TestGeneralOrbitsMLT():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_load_orbits_w_empty_data(self):
        self.testInst.load(1958, 31)
        self.testInst.orbits[0]
        with pytest.raises(StopIteration):
            self.testInst.orbits.next()

    def test_less_than_one_orbit_of_data(self):
        def filter_data(inst):
            inst.data = inst[0:20]
        self.testInst.custom.attach(filter_data, 'modify')
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        # a recusion issue has been observed in this area
        # checking for date to limit reintroduction potential
        assert self.testInst.date == dt.datetime(2009, 1, 1)

    def test_less_than_one_orbit_of_data_two_ways(self):
        def filter_data(inst):
            inst.data = inst[0:5]
        self.testInst.custom.attach(filter_data, 'modify')
        self.testInst.load(2009, 1)
        # starting from no orbit calls next loads first orbit
        self.testInst.orbits.next()
        # store comparison data
        saved_data = self.testInst.copy()
        self.testInst.load(2009, 1)
        self.testInst.orbits[0]
        assert all(self.testInst.data == saved_data.data)
        # a recusion issue has been observed in this area
        # checking for date to limit reintroduction potential
        d1check = self.testInst.date == saved_data.date
        assert d1check

    def test_less_than_one_orbit_of_data_four_ways_two_days(self):
        # create situation where the < 1 orbit split across two days
        def filter_data(inst):
            if inst.date == dt.datetime(2009, 1, 5):
                inst.data = inst[0:20]
            elif inst.date == dt.datetime(2009, 1, 4):
                inst.data = inst[-20:]

        self.testInst.custom.attach(filter_data, 'modify')
        self.testInst.load(2009, 4)
        # starting from no orbit calls next loads first orbit
        self.testInst.orbits.next()
        # store comparison data
        saved_data = self.testInst.copy()
        self.testInst.load(2009, 5)
        self.testInst.orbits[0]
        if self.testInst.orbits.num == 1:
            # equivalence only when only one orbit
            # some test settings can violate this assumption
            assert all(self.testInst.data == saved_data.data)
        self.testInst.load(2009, 4)
        self.testInst.orbits[0]
        assert all(self.testInst.data == saved_data.data)

        self.testInst.load(2009, 5)
        self.testInst.orbits.prev()
        if self.testInst.orbits.num == 1:
            assert all(self.testInst.data == saved_data.data)
        # a recusion issue has been observed in this area
        # checking for date to limit reintroduction potential
        d1check = self.testInst.date == saved_data.date
        assert d1check

    def test_repeated_orbit_calls_symmetric_single_day_start_with_last(self):
        self.testInst.load(2009, 1)
        # start on last orbit of last day
        self.testInst.orbits[0]
        self.testInst.orbits.prev()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(10):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_symmetric_single_day_0_UT(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(10):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_symmetric_multi_day_0_UT(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_symmetric_single_day_off_0_UT(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(10):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_symmetric_multi_day_off_0_UT(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_antisymmetric_multi_day_off_0_UT(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        for j in range(10):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_antisymmetric_multi_multi_day_off_0_UT(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(40):
            self.testInst.orbits.prev()
        for j in range(20):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_antisymmetric_multi_day_0_UT(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(10):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        for j in range(10):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data)

    def test_repeated_orbit_calls_antisymmetric_multi_multi_day_0_UT(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(40):
            self.testInst.orbits.prev()
        for j in range(20):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data)

    def test_repeat_orbit_calls_asym_multi_day_0_UT_long_time_gap(self):
        self.testInst.load(2009, 12)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(20):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeat_orbit_calls_asym_multi_day_0_UT_really_long_time_gap(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(400):
            self.testInst.orbits.next()
        for j in range(400):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)

    def test_repeat_orbit_calls_asym_multi_day_0_UT_multiple_time_gaps(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        n_time = []
        p_time = []
        for j in range(40):
            n_time.append(self.testInst.index[0])
            self.testInst.orbits.next()

        for j in range(40):
            self.testInst.orbits.prev()
            p_time.append(self.testInst.index[0])

        check = np.all(p_time == n_time[::-1])
        assert all(control.data == self.testInst.data) & check


class TestGeneralOrbitsMLTxarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLong(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLongxarray(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsOrbitNumber(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsOrbitNumberXarray(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLatitude(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLatitudeXarray(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


def filter_data(inst):
    """Remove data from instrument, simulating gaps"""

    times = [[dt.datetime(2009, 1, 1, 1, 37), dt.datetime(2009, 1, 1, 3, 14)],
             [dt.datetime(2009, 1, 1, 10), dt.datetime(2009, 1, 1, 12)],
             [dt.datetime(2009, 1, 1, 22), dt.datetime(2009, 1, 2, 2)],
             [dt.datetime(2009, 1, 13), dt.datetime(2009, 1, 15)],
             [dt.datetime(2009, 1, 20, 1), dt.datetime(2009, 1, 25, 23)],
             [dt.datetime(2009, 1, 25, 23, 30), dt.datetime(2009, 1, 26, 3)]
             ]
    for time in times:
        idx, = np.where((inst.index > time[1]) | (inst.index < time[0]))
        inst.data = inst[idx]


def filter_data2(inst, times=None):
    """Remove data from instrument, simulating gaps"""

    for time in times:
        idx, = np.where((inst.index > time[1]) | (inst.index < time[0]))
        inst.data = inst[idx]


class TestOrbitsGappyData(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyData2(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'})
        times = [[dt.datetime(2008, 12, 31, 4),
                  dt.datetime(2008, 12, 31, 5, 37)],
                 [dt.datetime(2009, 1, 1),
                  dt.datetime(2009, 1, 1, 1, 37)]]
        for seconds in np.arange(38):
            day = (dt.datetime(2009, 1, 2)
                   + pds.DateOffset(days=int(seconds)))
            times.append([day, day
                          + pds.DateOffset(hours=1, minutes=37,
                                           seconds=int(seconds))
                          - pds.DateOffset(seconds=20)])

        self.testInst.custom.attach(filter_data2, kwargs={'times': times})

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyData2Xarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'})
        times = [[dt.datetime(2008, 12, 31, 4),
                  dt.datetime(2008, 12, 31, 5, 37)],
                 [dt.datetime(2009, 1, 1),
                  dt.datetime(2009, 1, 1, 1, 37)]]
        for seconds in np.arange(38):
            day = (dt.datetime(2009, 1, 2)
                   + pds.DateOffset(days=int(seconds)))
            times.append([day, day
                          + pds.DateOffset(hours=1, minutes=37,
                                           seconds=int(seconds))
                          - pds.DateOffset(seconds=20)])

        self.testInst.custom.attach(filter_data2, kwargs={'times': times})

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyLongData(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'})
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyLongDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'})
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitNumData(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'})
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitNumDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'})
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitLatData(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'})
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitLatDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'})
        self.testInst.custom.attach(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
