from dateutil.relativedelta import relativedelta as relativedelta
from nose.tools import raises
import numpy as np
import pandas as pds

import pysat


class TestOrbitsUserInterface():

    @raises(ValueError)
    def test_orbit_w_bad_kind(self):
        info = {'index': 'mlt', 'kind': 'cats'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)        

    @raises(ValueError)
    def test_orbit_long_w_bad_variable(self):
        info = {'index': 'magnetic local time', 'kind': 'longitude'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_long_w_missing_orbit_info(self):
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         update_files=True)
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_long_w_missing_orbit_index(self):
        info = {'index': 'magnetic local time', 'kind': 'longitude'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        # force index to None
        self.testInst.orbits.orbit_index = None
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_mlt_w_bad_variable(self):
        info = {'index': 'magnetic local time', 'kind': 'lt'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_mlt_w_missing_orbit_index(self):
        info = {'index': 'magnetic local time', 'kind': 'lt'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        # force index to None
        self.testInst.orbits.orbit_index = None
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_polar_w_bad_variable(self):
        info = {'index': 'magnetic local time', 'kind': 'polar'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_polar_w_missing_orbit_index(self):
        info = {'index': 'magnetic local time', 'kind': 'polar'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        # force index to None
        self.testInst.orbits.orbit_index = None
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_orbibt_w_bad_variable(self):
        info = {'index': 'magnetic local time', 'kind': 'orbit'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()

    @raises(ValueError)
    def test_orbit_orbit_w_missing_orbit_index(self):
        info = {'index': 'magnetic local time', 'kind': 'orbit'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        # force index to None
        self.testInst.orbits.orbit_index = None
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        

class TestSpecificUTOrbits():

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_single_orbit_call_by_0_index(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits[0]
        ans = (self.testInst.index[0] == pds.datetime(2009, 1, 1))
        ans2 = (self.testInst.index[-1] == pds.datetime(2009, 1, 1, 1, 36, 59))
        assert ans & ans2

    def test_single_orbit_call_by_1_index(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits[1]
        ans = (self.testInst.index[0] == pds.datetime(2009, 1, 1, 1, 37))
        ans2 = (self.testInst.index[-1] == pds.datetime(2009, 1, 1, 3, 13, 59))
        assert ans & ans2

    def test_single_orbit_call_by_negative_1_index(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits[-1]
        ans = (self.testInst.index[0] ==
               (pds.datetime(2009, 1, 1)-relativedelta(hours=1, minutes=37)))
        ans2 = (self.testInst.index[-1] ==
                (pds.datetime(2009, 1, 1)-relativedelta(seconds=1)))
        assert ans & ans2

    def test_single_orbit_call_by_last_index(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits[14]
        assert (self.testInst.index[0] ==
                (pds.datetime(2009, 1, 1)-relativedelta(hours=1, minutes=37)))
        assert (self.testInst.index[-1] ==
                (pds.datetime(2009, 1, 1)-relativedelta(seconds=1)))

    @raises(Exception)
    def test_single_orbit_call_too_many(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits[17]

    @raises(Exception)
    def test_single_orbit_no_input(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits[None]

    def test_oribt_number_via_current_multiple_orbit_calls_in_day(self):
        self.testInst.load(2009, 1)
        self.testInst.bounds = (pysat.datetime(2009, 1, 1), None)
        true_vals = np.arange(15)
        true_vals[-1] = 0
        test_vals = []
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break
            test_vals.append(self.testInst.orbits.current)
            print('Loaded orbit ', self.testInst.orbits.current)
 
        assert np.all(test_vals == true_vals)

    def test_all_single_orbit_calls_in_day(self):
        self.testInst.load(2009, 1)
        ans = []
        ans2 = []
        self.testInst.bounds = (pysat.datetime(2009, 1, 1), None)
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break
            print('Loaded orbit ', self.testInst.orbits.current)
            ans.append(self.testInst.index[0] ==
                       (pds.datetime(2009, 1, 1) +
                       i*relativedelta(hours=1, minutes=37)))
            ans2.append(self.testInst.index[-1] ==
                        (pds.datetime(2009, 1, 1) +
                        (i + 1) * relativedelta(hours=1, minutes=37) -
                        relativedelta(seconds=1)))

        assert np.all(ans) & np.all(ans2)

    def test_orbit_next_call_no_loaded_data(self):
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == pds.datetime(2008, 1, 1))
        assert (self.testInst.index[-1] == pds.datetime(2008, 1, 1, 0, 38, 59))

    def test_orbit_prev_call_no_loaded_data(self):
        self.testInst.orbits.prev()
        # this isn't a full orbit
        assert (self.testInst.index[-1] ==
                pds.datetime(2010, 12, 31, 23, 59, 59))
        assert (self.testInst.index[0] == pds.datetime(2010, 12, 31, 23, 49))

    def test_single_orbit_call_orbit_starts_0_UT_using_next(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == pds.datetime(2009, 1, 1))
        assert (self.testInst.index[-1] == pds.datetime(2009, 1, 1, 1, 36, 59))

    def test_single_orbit_call_orbit_starts_0_UT_using_prev(self):
        self.testInst.load(2009, 1)
        self.testInst.orbits.prev()
        assert (self.testInst.index[0] ==
                (pds.datetime(2009, 1, 1) +
                14 * relativedelta(hours=1, minutes=37)))
        assert (self.testInst.index[-1] ==
                (pds.datetime(2009, 1, 1) +
                15 * relativedelta(hours=1, minutes=37) -
                relativedelta(seconds=1)))

    def test_single_orbit_call_orbit_starts_off_0_UT_using_next(self):
        from dateutil.relativedelta import relativedelta as relativedelta
        self.testInst.load(2008, 366)
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == pds.datetime(2008, 12, 30, 23, 45))
        assert (self.testInst.index[-1] ==
                (pds.datetime(2008, 12, 30, 23, 45) +
                relativedelta(hours=1, minutes=36, seconds=59)))

    def test_single_orbit_call_orbit_starts_off_0_UT_using_prev(self):
        self.testInst.load(2008, 366)
        self.testInst.orbits.prev()
        assert (self.testInst.index[0] ==
                (pds.datetime(2009, 1, 1)-relativedelta(hours=1, minutes=37)))
        assert (self.testInst.index[-1] ==
                (pds.datetime(2009, 1, 1)-relativedelta(seconds=1)))


class TestGeneralOrbitsMLT():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    @raises(StopIteration)
    def test_load_orbits_w_empty_data(self):
        self.testInst.load(1958, 31)
        self.testInst.orbits[0]
        self.testInst.orbits.next()

    def test_less_than_one_orbit_of_data(self):
        def filter_data(inst):
            inst.data = inst[0:20]
        self.testInst.custom.add(filter_data, 'modify')
        self.testInst.load(2009, 1)
        self.testInst.orbits.next()
        # a recusion issue has been observed in this area
        # checking for date to limit reintroduction potential
        assert self.testInst.date == pysat.datetime(2009, 1, 1)

    def test_less_than_one_orbit_of_data_two_ways(self):
        def filter_data(inst):
            inst.data = inst[0:5]
        self.testInst.custom.add(filter_data, 'modify')
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
            if inst.date == pysat.datetime(2009, 1, 5):
                inst.data = inst[0:20]
            elif inst.date == pysat.datetime(2009, 1, 4):
                inst.data = inst[-20:]

        self.testInst.custom.add(filter_data, 'modify')
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
        else:
            print('Skipping this part of test.')
        self.testInst.load(2009, 4)
        self.testInst.orbits[0]
        assert all(self.testInst.data == saved_data.data)
        
        self.testInst.load(2009, 5)
        self.testInst.orbits.prev()
        if self.testInst.orbits.num == 1:
            assert all(self.testInst.data == saved_data.data)
        else:
            print('Skipping this part of test.')
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
        info = {'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLong(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'longitude', 'kind': 'longitude'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLongxarray(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'longitude', 'kind': 'longitude'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsOrbitNumber(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'orbit_num', 'kind': 'orbit'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsOrbitNumberXarray(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'orbit_num', 'kind': 'orbit'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLatitude(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'latitude', 'kind': 'polar'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestGeneralOrbitsLatitudeXarray(TestGeneralOrbitsMLT):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'latitude', 'kind': 'polar'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


def filter_data(inst):
    """Remove data from instrument, simulating gaps"""

    times = [[pysat.datetime(2009, 1, 1, 10),
              pysat.datetime(2009, 1, 1, 12)],
             [pysat.datetime(2009, 1, 1, 4),
              pysat.datetime(2009, 1, 2, 5, 37)],
             [pysat.datetime(2009, 1, 1, 1, 37),
              pysat.datetime(2009, 1, 1, 3, 14)],
             [pysat.datetime(2009, 1, 1, 15),
              pysat.datetime(2009, 1, 1, 16)],
             [pysat.datetime(2009, 1, 1, 22),
              pysat.datetime(2009, 1, 2, 2)],
             [pysat.datetime(2009, 1, 13),
              pysat.datetime(2009, 1, 15)],
             [pysat.datetime(2009, 1, 20, 1),
              pysat.datetime(2009, 1, 25, 23)],
             [pysat.datetime(2009, 1, 25, 23, 30),
              pysat.datetime(2009, 1, 26, 3)]
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
        info = {'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info, update_files=True)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""


class TestOrbitsGappyData2(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info)
        times = [[pysat.datetime(2008, 12, 31, 4),
                  pysat.datetime(2008, 12, 31, 5, 37)],
                 [pysat.datetime(2009, 1, 1),
                  pysat.datetime(2009, 1, 1, 1, 37)]
                 ]
        for seconds in np.arange(38):
            day = pysat.datetime(2009, 1, 2) + \
                pds.DateOffset(days=int(seconds))
            times.append([day, day +
                          pds.DateOffset(hours=1, minutes=37,
                                         seconds=int(seconds)) -
                          pds.DateOffset(seconds=20)])

        self.testInst.custom.add(filter_data2, 'modify', times=times)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyData2Xarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info)
        times = [[pysat.datetime(2008, 12, 31, 4),
                  pysat.datetime(2008, 12, 31, 5, 37)],
                 [pysat.datetime(2009, 1, 1),
                  pysat.datetime(2009, 1, 1, 1, 37)]
                 ]
        for seconds in np.arange(38):
            day = pysat.datetime(2009, 1, 2) + \
                pds.DateOffset(days=int(seconds))
            times.append([day, day +
                          pds.DateOffset(hours=1, minutes=37,
                                         seconds=int(seconds)) -
                          pds.DateOffset(seconds=20)])

        self.testInst.custom.add(filter_data2, 'modify', times=times)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyLongData(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'longitude', 'kind': 'longitude'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyLongDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'longitude', 'kind': 'longitude'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitNumData(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'orbit_num', 'kind': 'orbit'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitNumDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'orbit_num', 'kind': 'orbit'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitLatData(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'latitude', 'kind': 'polar'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=info)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst


class TestOrbitsGappyOrbitLatDataXarray(TestGeneralOrbitsMLT):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        info = {'index': 'latitude', 'kind': 'polar'}
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info=info)
        self.testInst.custom.add(filter_data, 'modify')

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
