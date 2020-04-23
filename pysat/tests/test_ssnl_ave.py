"""
tests the pysat averaging code
"""
from nose.tools import raises
import numpy as np
import pandas as pds
import warnings
import pysat
from pysat.ssnl import avg


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean')
        self.bounds1 = (pysat.datetime(2008, 1, 1), pysat.datetime(2008, 1, 3))
        self.bounds2 = (pysat.datetime(2009, 1, 1), pysat.datetime(2009, 1, 2))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.bounds1, self.bounds2

    def test_basic_seasonal_median2D(self):
        """ Test the basic seasonal 2D median"""
        self.testInst.bounds = self.bounds1
        results = avg.median2D(self.testInst, [0., 360., 24], 'longitude',
                               [0., 24, 24], 'mlt',
                               ['dummy1', 'dummy2', 'dummy3'])
        dummy_val = results['dummy1']['median']
        dummy_dev = results['dummy1']['avg_abs_dev']

        dummy2_val = results['dummy2']['median']
        dummy2_dev = results['dummy2']['avg_abs_dev']

        dummy3_val = results['dummy3']['median']
        dummy3_dev = results['dummy3']['avg_abs_dev']

        dummy_x = results['dummy1']['bin_x']
        dummy_y = results['dummy1']['bin_y']

        # iterate over all y rows
        # value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, y in enumerate(dummy_y[:-1]):
            assert np.all(dummy_val[i, :] == y.astype(int))
            assert np.all(dummy_dev[i, :] == 0)

        for i, x in enumerate(dummy_x[:-1]):
            assert np.all(dummy2_val[:, i] == x/15.0)
            assert np.all(dummy2_dev[:, i] == 0)

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy3_val[:, i] == x/15.0 * 1000.0
                                + dummy_y[:-1]))
            check.append(np.all(dummy3_dev[:, i] == 0))

        # holds here because there are 32 days, no data is discarded,
        # each day holds same amount of data
        assert(self.testInst.data['dummy1'].size*3 ==
               sum([sum(i) for i in results['dummy1']['count']]))

        assert np.all(check)

    def test_basic_daily_mean(self):
        """ Test basic daily mean"""
        self.testInst.bounds = self.bounds1
        ans = avg.mean_by_day(self.testInst, 'dummy4')
        assert np.all(ans == 86399/2.0)

    def test_basic_orbit_mean(self):
        """Test basic orbital mean"""
        orbit_info = {'kind': 'local time', 'index': 'mlt'}
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info=orbit_info)
        self.testInst.bounds = self.bounds2
        ans = avg.mean_by_orbit(self.testInst, 'mlt')
        # note last orbit is incomplete thus not expected to satisfy relation
        assert np.allclose(ans[:-1], np.ones(len(ans)-1)*12.0, 1.0E-2)

    def test_basic_file_mean(self):
        """Test basic file mean"""
        index = pds.date_range(*self.bounds1)
        names = [date.strftime('%Y-%m-%d')+'.nofile' for date in index]
        self.testInst.bounds = (names[0], names[-1])
        ans = avg.mean_by_file(self.testInst, 'dummy4')
        assert np.all(ans == 86399/2.0)


class TestDeprecation():

    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always")

    def teardown(self):
        """Runs after every method to clean up previous testing"""

    def test_median1D_deprecation_warning(self):
        """Test generation of deprecation warning for median1D"""

        with warnings.catch_warnings(record=True) as war:
            try:
                avg.median1D(None, [0., 360., 24],
                             'longitude', ['dummy1'])
            except ValueError:
                # Setting inst to None should produce a ValueError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_median2D_deprecation_warning(self):
        """Test generation of deprecation warning for median1D"""

        with warnings.catch_warnings(record=True) as war:
            try:
                avg.median2D(None, [0., 360., 24], 'longitude',
                             [0., 24., 24], 'mlt', ['dummy1'])
            except ValueError:
                # Setting inst to None should produce a ValueError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_mean_by_day_deprecation_warning(self):
        """Test generation of deprecation warning for mean_by_day"""

        with warnings.catch_warnings(record=True) as war:
            try:
                avg.mean_by_day(None, 'dummy1')
            except TypeError:
                # Setting inst to None should produce a TypeError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_mean_by_orbit_deprecation_warning(self):
        """Test generation of deprecation warning for mean_by_orbit"""

        with warnings.catch_warnings(record=True) as war:
            try:
                avg.mean_by_orbit(None, 'dummy1')
            except AttributeError:
                # Setting inst to None should produce a AttributeError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_mean_by_file_deprecation_warning(self):
        """Test generation of deprecation warning for mean_by_file"""

        with warnings.catch_warnings(record=True) as war:
            try:
                avg.mean_by_file(None, 'dummy1')
            except TypeError:
                # Setting inst to None should produce a TypeError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning


class TestFrameProfileAverages():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing2D',
                                         clean_level='clean')
        self.testInst.bounds = (pysat.datetime(2008, 1, 1),
                                pysat.datetime(2008, 1, 3))
        self.dname = 'alt_profiles'
        self.test_vals = np.arange(50) * 1.2
        self.test_fracs = np.arange(50) / 50.0

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.dname, self.test_vals, self.test_fracs

    def test_basic_seasonal_2Dmedian(self):
        """ Test the basic seasonal 2D median"""

        results = avg.median2D(self.testInst, [0., 360., 24], 'longitude',
                               [0., 24, 24], 'mlt', [self.dname])

        # iterate over all
        # no variation in the median, all values should be the same
        for i, row in enumerate(results[self.dname]['median']):
            for j, item in enumerate(row):
                assert np.all(item['density'] == self.test_vals)
                assert np.all(item['fraction'] == self.test_fracs)

        for i, row in enumerate(results[self.dname]['avg_abs_dev']):
            for j, item in enumerate(row):
                assert np.all(item['density'] == 0)
                assert np.all(item['fraction'] == 0)

    def test_basic_seasonal_1Dmedian(self):
        """ Test the basic seasonal 1D median"""

        results = avg.median1D(self.testInst, [0., 24, 24], 'mlt',
                               [self.dname])

        # iterate over all
        # no variation in the median, all values should be the same
        for i, row in enumerate(results[self.dname]['median']):
            assert np.all(row['density'] == self.test_vals)
            assert np.all(row['fraction'] == self.test_fracs)

        for i, row in enumerate(results[self.dname]['avg_abs_dev']):
            assert np.all(row['density'] == 0)
            assert np.all(row['fraction'] == 0)


class TestSeriesProfileAverages():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument(platform='pysat', name='testing2D',
                                         clean_level='clean')
        self.testInst.bounds = (pysat.datetime(2008, 1, 1),
                                pysat.datetime(2008, 2, 1))
        self.dname = 'series_profiles'

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.dname

    def test_basic_seasonal_median2D(self):
        """ Test basic seasonal 2D median"""
        results = avg.median2D(self.testInst, [0., 360., 24], 'longitude',
                               [0., 24, 24], 'mlt', [self.dname])

        # iterate over all
        # no variation in the median, all values should be the same
        test_vals = np.arange(50) * 1.2
        for i, row in enumerate(results[self.dname]['median']):
            for j, item in enumerate(row):
                assert np.all(item == test_vals)

        for i, row in enumerate(results[self.dname]['avg_abs_dev']):
            for j, item in enumerate(row):
                assert np.all(item == 0)

    def test_basic_seasonal_median1D(self):
        """ Test basic seasonal 1D median"""
        results = avg.median1D(self.testInst, [0., 24, 24], 'mlt',
                               [self.dname])

        # iterate over all
        # no variation in the median, all values should be the same
        test_vals = np.arange(50) * 1.2
        for i, row in enumerate(results[self.dname]['median']):
            assert np.all(row == test_vals)

        for i, row in enumerate(results[self.dname]['avg_abs_dev']):
            assert np.all(row == 0)


class TestConstellation:
    def setup(self):
        insts = []
        for i in range(5):
            insts.append(pysat.Instrument('pysat', 'testing',
                                          clean_level='clean'))
        self.testC = pysat.Constellation(instruments=insts)
        self.testI = pysat.Instrument('pysat', 'testing', clean_level='clean')
        self.bounds = (pysat.datetime(2008, 1, 1), pysat.datetime(2008, 1, 3))

    def teardown(self):
        del self.testC, self.testI, self.bounds

    def test_constellation_median2D(self):
        """ Test constellation implementation of 2D median"""
        for i in self.testC.instruments:
            i.bounds = self.bounds
        self.testI.bounds = self.bounds
        resultsC = avg.median2D(self.testC, [0., 360., 24], 'longitude',
                                [0., 24, 24], 'mlt',
                                ['dummy1', 'dummy2', 'dummy3'])
        resultsI = avg.median2D(self.testI, [0., 360., 24], 'longitude',
                                [0., 24, 24], 'mlt',
                                ['dummy1', 'dummy2', 'dummy3'])
        medC1 = resultsC['dummy1']['median']
        medI1 = resultsI['dummy1']['median']
        medC2 = resultsC['dummy2']['median']
        medI2 = resultsI['dummy2']['median']
        medC3 = resultsC['dummy3']['median']
        medI3 = resultsI['dummy3']['median']

        assert np.array_equal(medC1, medI1)
        assert np.array_equal(medC2, medI2)
        assert np.array_equal(medC3, medI3)

    def test_constellation_median1D(self):
        """ Test constellation implementation of 1D median"""
        for i in self.testC.instruments:
            i.bounds = self.bounds
        self.testI.bounds = self.bounds
        resultsC = avg.median1D(self.testC, [0., 24, 24], 'mlt',
                                ['dummy1', 'dummy2', 'dummy3'])
        resultsI = avg.median1D(self.testI, [0., 24, 24], 'mlt',
                                ['dummy1', 'dummy2', 'dummy3'])
        medC1 = resultsC['dummy1']['median']
        medI1 = resultsI['dummy1']['median']
        medC2 = resultsC['dummy2']['median']
        medI2 = resultsI['dummy2']['median']
        medC3 = resultsC['dummy3']['median']
        medI3 = resultsI['dummy3']['median']

        assert np.array_equal(medC1, medI1)
        assert np.array_equal(medC2, medI2)
        assert np.array_equal(medC3, medI3)


class TestHeterogenousConstellation:
    def setup(self):
        insts = []
        for i in range(2):
            r_date = pysat.datetime(2009, 1, i+1)
            insts.append(pysat.Instrument('pysat', 'testing',
                                          clean_level='clean',
                                          root_date=r_date))
        self.testC = pysat.Constellation(instruments=insts)
        self.bounds = (pysat.datetime(2008, 1, 1), pysat.datetime(2008, 1, 3))

    def teardown(self):
        del self.testC, self.bounds

    def test_heterogenous_constellation_median2D(self):
        """ Test the seasonal 2D median of a heterogeneous constellation """
        for inst in self.testC:
            inst.bounds = self.bounds
        results = avg.median2D(self.testC, [0., 360., 24], 'longitude',
                               [0., 24, 24], 'mlt',
                               ['dummy1', 'dummy2', 'dummy3'])
        dummy_val = results['dummy1']['median']
        dummy_dev = results['dummy1']['avg_abs_dev']

        dummy2_val = results['dummy2']['median']
        dummy2_dev = results['dummy2']['avg_abs_dev']

        dummy3_val = results['dummy3']['median']
        dummy3_dev = results['dummy3']['avg_abs_dev']

        dummy_x = results['dummy1']['bin_x']
        dummy_y = results['dummy1']['bin_y']

        # iterate over all y rows
        # value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, y in enumerate(dummy_y[:-1]):
            check.append(np.all(dummy_val[i, :] == y.astype(int)))
            check.append(np.all(dummy_dev[i, :] == 0))

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy2_val[:, i] == x/15.0))
            check.append(np.all(dummy2_dev[:, i] == 0))

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy3_val[:, i] == x/15.0 * 1000.0
                                + dummy_y[:-1]))
            check.append(np.all(dummy3_dev[:, i] == 0))

        assert np.all(check)

    def test_heterogenous_constellation_median1D(self):
        """ Test the seasonal 1D median of a heterogeneous constellation """
        for inst in self.testC:
            inst.bounds = self.bounds
        results = avg.median1D(self.testC, [0., 24, 24], 'mlt', ['dummy1'])

        # Extract the results
        dummy_val = results['dummy1']['median']
        dummy_dev = results['dummy1']['avg_abs_dev']

        # iterate over all x rows
        # value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, x in enumerate(results['dummy1']['bin_x'][:-1]):
            check.append(np.all(dummy_val[i] == x.astype(int)))
            check.append(np.all(dummy_dev[i] == 0))

        assert np.all(check)


class Test2DConstellation:
    def setup(self):
        insts = []
        insts.append(pysat.Instrument(platform='pysat', name='testing2D',
                                      clean_level='clean'))
        self.testC = pysat.Constellation(insts)
        self.bounds = (pysat.datetime(2008, 1, 1), pysat.datetime(2008, 1, 3))

    def teardown(self):
        del self.testC, self.bounds

    def test_2D_median(self):
        """ Test a 2D median calculation with a constellation"""
        for i in self.testC.instruments:
            i.bounds = self.bounds

        results = avg.median2D(self.testC, [0., 360., 24], 'longitude',
                               [0., 24, 24], 'slt', ['uts'])
        dummy_val = results['uts']['median']
        dummy_dev = results['uts']['avg_abs_dev']

        dummy_y = results['uts']['bin_y']

        # iterate over all y rows
        # value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, y in enumerate(dummy_y[:-1]):
            check.append(np.all(dummy_val[i, :] == y.astype(int)))
            check.append(np.all(dummy_dev[i, :] == 0))

    def test_1D_median(self):
        """ Test a 1D median calculation with a constellation"""
        for i in self.testC.instruments:
            i.bounds = self.bounds

        results = avg.median1D(self.testC, [0., 24, 24], 'slt', ['uts'])
        dummy_val = results['uts']['median']
        dummy_dev = results['uts']['avg_abs_dev']

        dummy_x = results['uts']['bin_x']

        # iterate over all x rows
        # value should be equal to integer value of slt
        # no variation in the median, all values should be the same
        check = []
        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy_val[i] == x.astype(int)))
            check.append(np.all(dummy_dev[i] == 0))


class TestSeasonalAverageUnevenBins:
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean')
        self.testInst.bounds = (pysat.datetime(2008, 1, 1),
                                pysat.datetime(2008, 1, 3))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_seasonal_average_uneven_bins(self):
        """ Test seasonal 2D median with uneven bins"""
        results = avg.median2D(self.testInst, np.linspace(0., 360., 25),
                               'longitude', np.linspace(0., 24., 25), 'mlt',
                               ['dummy1', 'dummy2', 'dummy3'], auto_bin=False)
        dummy_val = results['dummy1']['median']
        dummy_dev = results['dummy1']['avg_abs_dev']

        dummy2_val = results['dummy2']['median']
        dummy2_dev = results['dummy2']['avg_abs_dev']

        dummy3_val = results['dummy3']['median']
        dummy3_dev = results['dummy3']['avg_abs_dev']

        dummy_x = results['dummy1']['bin_x']
        dummy_y = results['dummy1']['bin_y']

        # iterate over all y rows
        # value should be equal to integer value of mlt
        # no variation in the median, all values should be the same
        check = []
        for i, y in enumerate(dummy_y[:-1]):
            assert np.all(dummy_val[i, :] == y.astype(int))
            assert np.all(dummy_dev[i, :] == 0)

        for i, x in enumerate(dummy_x[:-1]):
            assert np.all(dummy2_val[:, i] == x/15.0)
            assert np.all(dummy2_dev[:, i] == 0)

        for i, x in enumerate(dummy_x[:-1]):
            check.append(np.all(dummy3_val[:, i] == x/15.0 * 1000.0
                                + dummy_y[:-1]))
            check.append(np.all(dummy3_dev[:, i] == 0))

        # holds here because there are 32 days, no data is discarded,
        # each day holds same amount of data
        assert(self.testInst.data['dummy1'].size*3 ==
               sum([sum(i) for i in results['dummy1']['count']]))

        assert np.all(check)

    @raises(ValueError)
    def test_nonmonotonic_bins(self):
        """Test 2D median failure when provided with a non-monotonic bins
        """
        avg.median2D(self.testInst, np.array([0., 300., 100.]), 'longitude',
                     np.array([0., 24., 13.]), 'mlt',
                     ['dummy1', 'dummy2', 'dummy3'], auto_bin=False)

    @raises(TypeError)
    def test_bin_data_depth(self):
        """Test failure when an array-like of length 1 is given to median2D
        """
        avg.median2D(self.testInst, 1, 'longitude', 24, 'mlt',
                     ['dummy1', 'dummy2', 'dummy3'], auto_bin=False)

    @raises(TypeError)
    def test_bin_data_type(self):
        """Test failure when a non array-like is given to median2D
        """
        avg.median2D(self.testInst, ['1', 'a', '23', '10'], 'longitude',
                     ['0', 'd', '24', 'c'], 'mlt',
                     ['dummy1', 'dummy2', 'dummy3'], auto_bin=False)


class TestInstMed1D():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         update_files=True)
        self.testInst.bounds = (pysat.datetime(2008, 1, 1),
                                pysat.datetime(2008, 1, 31))
        self.test_bins = [0, 24, 24]
        self.test_label = 'slt'
        self.test_data = ['dummy1', 'dummy2']
        self.out_keys = ['count', 'avg_abs_dev', 'median', 'bin_x']
        self.out_data = {'dummy1':
                         {'count': [111780., 111320., 111780., 111320.,
                                    111780., 111320., 111780., 111320.,
                                    111780., 111320., 111780., 111320.,
                                    111780., 111320., 111918., 111562.,
                                    112023., 111562., 112023., 111412.,
                                    111780., 111320., 111780., 111320.],
                          'avg_abs_dev': np.zeros(shape=24),
                          'median': np.linspace(0.0, 23.0, 24)},
                         'dummy2':
                         {'count': [111780., 111320., 111780., 111320.,
                                    111780., 111320., 111780., 111320.,
                                    111780., 111320., 111780., 111320.,
                                    111780., 111320., 111918., 111562.,
                                    112023., 111562., 112023., 111412.,
                                    111780., 111320., 111780., 111320.],
                          'avg_abs_dev': np.zeros(shape=24) + 6.0,
                          'median': [11., 12., 11., 11., 12., 11., 12., 11.,
                                     12., 12., 11., 12., 11., 12., 11., 11.,
                                     12., 11., 12., 11., 11., 11., 11., 12.]}}

    def teardown(self):
        """Runs after every method to clean up previous testing"""
        del self.testInst, self.test_bins, self.test_label, self.test_data
        del self.out_keys, self.out_data

    def test_median1D_default(self):
        """Test success of median1D with default options"""

        med_dict = avg.median1D(self.testInst, self.test_bins, self.test_label,
                                self.test_data)

        # Test output type
        assert isinstance(med_dict, dict)
        assert len(med_dict.keys()) == len(self.test_data)

        # Test output keys
        for kk in med_dict.keys():
            assert kk in self.test_data
            assert np.all([jj in self.out_keys
                           for jj in med_dict[kk].keys()])

            # Test output values
            for jj in self.out_keys[:-1]:
                assert len(med_dict[kk][jj]) == self.test_bins[-1]
                assert np.all(med_dict[kk][jj] == self.out_data[kk][jj])

            jj = self.out_keys[-1]
            assert len(med_dict[kk][jj]) == self.test_bins[-1]+1
            assert np.all(med_dict[kk][jj] == np.linspace(self.test_bins[0],
                                                          self.test_bins[1],
                                                          self.test_bins[2]+1))
        del med_dict, kk, jj

    @raises(KeyError)
    def test_median1D_bad_data(self):
        """Test failure of median1D with string data instead of list"""

        avg.median1D(self.testInst, self.test_bins, self.test_label,
                     self.test_data[0])

    @raises(KeyError)
    def test_median1D_bad_label(self):
        """Test failure of median1D with unknown label"""

        avg.median1D(self.testInst, self.test_bins, "bad_label",
                     self.test_data)

    @raises(ValueError)
    def test_nonmonotonic_bins(self):
        """Test median1D failure when provided with a non-monotonic bins
        """
        avg.median1D(self.testInst, [0, 13, 5], self.test_label,
                     self.test_data, auto_bin=False)

    @raises(TypeError)
    def test_bin_data_depth(self):
        """Test failure when array-like of length 1 is given to median1D
        """
        avg.median1D(self.testInst, 24, self.test_label, self.test_data,
                     auto_bin=False)

    @raises(TypeError)
    def test_bin_data_type(self):
        """Test failure when median 1D is given non array-like bins
        """
        pysat.ssnl.avg.median2D(self.testInst, ['0', 'd', '24', 'c'],
                                self.test_label, self.test_data,
                                auto_bin=False)
