import warnings
from nose.tools import raises
import numpy as np

import pysat


class TestConstellation:
    """Test the Constellation class."""
    def setup(self):
        """Create instruments and a constellation for each test."""
        self.instruments = [pysat.Instrument('pysat', 'testing',
                                             clean_level='clean')
                            for i in range(2)]
        self.const = pysat.Constellation(self.instruments)

    def teardown(self):
        """Clean up after each test."""
        del self.const

    def test_construct_by_list(self):
        """Construct a Constellation with a list."""
        const = pysat.Constellation(self.instruments)
        assert len(const.instruments) == 2

    def test_construct_by_name(self):
        """Construct a Constellation by name.

        Should access a predefined Constellation."""
        const = pysat.Constellation(name='testing')
        assert len(const.instruments) == 5

    @raises(ValueError)
    def test_construct_both(self):
        """Attempt to construct a Constellation by name and list.
        Raises an error."""
        pysat.Constellation(
            instruments=self.instruments,
            name='testing')

    @raises(ValueError)
    def test_construct_bad_instruments(self):
        """Attempt to construct a Constellation with
        a bad instrument 'list.'"""
        pysat.Constellation(instruments=42)

    def test_construct_null(self):
        """Attempt to construct a Constellation with
        no arguments."""
        const = pysat.Constellation()
        assert len(const.instruments) == 0

    def test_getitem(self):
        """Test Constellation:__getitem__."""
        assert self.const[0] == self.instruments[0]
        assert self.const[1] == self.instruments[1]
        assert self.const[:] == self.instruments[:]
        assert self.const[1::-1] == self.instruments[1::-1]

    def test_str(self):
        """Test Constellation:__str__."""
        assert str(self.const) == \
            "\npysat Constellation object:\ntesting\ntesting\n"


class TestAdditionIdenticalInstruments:
    def setup(self):
        self.const1 = pysat.Constellation(name='testing')
        self.const2 = pysat.Constellation(name='single_test')

    def teardown(self):
        del self.const1
        del self.const2

    def test_addition_identical(self):
        self.const1.set_bounds(pysat.datetime(2008, 1, 1),
                               pysat.datetime(2008, 2, 1))
        self.const2.set_bounds(pysat.datetime(2008, 1, 1),
                               pysat.datetime(2008, 2, 1))

        bounds1 = [0, 360]
        label1 = 'longitude'
        bounds2 = [-90, 90]
        label2 = 'latitude'
        bins3 = [0, 24, 24]
        label3 = 'mlt'
        data_label = ['dummy1']
        results1 = self.const1.add(bounds1, label1, bounds2, label2, bins3,
                                   label3, data_label)
        results2 = self.const2.add(bounds1, label1, bounds2, label2, bins3,
                                   label3, data_label)
        med1 = results1['dummy1']['median']
        med2 = results2['dummy1']['median']
        for (left, right) in zip(med1, med2):
            assert left == right or \
                   (np.isnan(left) and np.isnan(right))

        # for i in range(len(med1)):
        #    assert med1[i] == med2[i]


class TestAdditionOppositeInstruments:
    def setup(self):
        """
        The data in ascend['dummy1'] is just ascending integers 0 to the
        length of the other data, descend has the same data but negative.
        The addition of these two signals should be zero everywhere.
        """
        self.testC = pysat.Constellation(name='test_add_opposite')

    def teardown(self):
        del self.testC

    def test_addition_opposite_instruments(self):
        self.testC.set_bounds(pysat.datetime(2008, 1, 1),
                              pysat.datetime(2008, 2, 1))
        bounds1 = [0, 360]
        label1 = 'longitude'
        bounds2 = [-90, 90]
        label2 = 'latitude'
        bins3 = [0, 24, 24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results = self.testC.add(bounds1, label1, bounds2, label2, bins3,
                                 label3, data_label)
        med = np.array(results['dummy1']['median'])
        assert abs(med).max() == 0


class TestAdditionSimilarInstruments:
    def setup(self):
        """
        All the data in dummy1 of 'plus10' is the data in default + 10
        So the addition of 'ascend' and 'plus10' should be no
        more than 10 off from the addition of just 'ascend'
        TODO: actually check the math on this
        """
        self.testC = pysat.Constellation(name='test_add_similar')
        self.refC = pysat.Constellation([pysat.Instrument('pysat', 'testing',
                                                          tag='ascend')])

    def teardown(self):
        del self.testC
        del self.refC

    def test_addition_similar_instruments(self):
        self.testC.set_bounds(pysat.datetime(2008, 1, 1),
                              pysat.datetime(2008, 2, 1))
        self.refC.set_bounds(pysat.datetime(2008, 1, 1),
                             pysat.datetime(2008, 2, 1))
        bounds1 = [0, 360]
        label1 = 'longitude'
        bounds2 = [-90, 90]
        label2 = 'latitude'
        bins3 = [0, 24, 24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results = self.testC.add(bounds1, label1, bounds2, label2, bins3,
                                 label3, data_label)
        refresults = self.refC.add(bounds1, label1, bounds2, label2, bins3,
                                   label3, data_label)
        med = np.array(results['dummy1']['median'])
        refmed = np.array(refresults['dummy1']['median'])
        diff = med - refmed
        assert diff.min() >= 0
        assert diff.max() <= 10


class TestAdditionSingleInstrument:
    def setup(self):
        """
        The constellation consists of a single instrument, so performing
        addition on it should just return the instrument's data within
        the bounds
        """
        insts = []
        self.testInst = pysat.Instrument('pysat', 'testing', 'fives',
                                         clean_level='clean')
        insts.append(self.testInst)
        self.testConst = pysat.Constellation(insts)

    def teardown(self):
        del self.testConst

    def test_addition_single_instrument(self):
        for inst in self.testConst:
            inst.bounds = (pysat.datetime(2008, 1, 1),
                           pysat.datetime(2008, 2, 1))
        bounds1 = [0, 360]
        label1 = 'longitude'
        bounds2 = [-90, 90]
        label2 = 'latitude'
        bins3 = [0, 24, 24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results = self.testConst.add(bounds1, label1, bounds2, label2, bins3,
                                     label3, data_label)

        med = results['dummy1']['median']
        for i in med:
            assert i == 5


class TestDifferenceSameInstrument:
    def setup(self):
        self.const = pysat.Constellation(name='test_diff_same')

    def teardown(self):
        del self.const

    def test_diff_same_instruments(self):
        self.const.load(date=pysat.datetime(2008, 1, 1))
        bounds = [('longitude', 'longitude', 0, 360, .5),
                  ('latitude', 'latitude', -90, 90, .5),
                  ('mlt', 'mlt', 0, 24, .1)]
        results = self.const.difference(self.const[0], self.const[1],
                                        bounds, [('dummy1', 'dummy1')],
                                        cost_function)
        diff = results['dummy1']
        dist = results['dist']
        # the instruments are identical, so the difference should be 0
        # everywhere
        assert abs(diff).max() == 0
        assert abs(dist).max() == 0


class TestDifferenceSimilarInstruments:
    def setup(self):
        self.const = pysat.Constellation(name='test_diff_similar')

    def teardown(self):
        del self.const

    def test_diff_similar_instruments(self):
        self.const.load(date=pysat.datetime(2008, 1, 1))
        bounds = [('longitude', 'longitude', 0, 360, .5),
                  ('latitude', 'latitude', -90, 90, .5),
                  ('mlt', 'mlt', 0, 24, .1)]
        results = self.const.difference(self.const[0], self.const[1],
                                        bounds, [('dummy1', 'dummy1')],
                                        cost_function)
        diff = results['dummy1']
        assert np.all(abs(diff - 5)) == 0


# test cost function for testing difference
def cost_function(point1, point2):
    lat_diff = point1['latitude'] - point2['latitude']
    long_diff = point1['longitude'] - point2['longitude']
    return lat_diff*lat_diff + long_diff*long_diff


class TestDataMod:
    """Test adapted from test_custom.py."""
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testConst = \
            pysat.Constellation([pysat.Instrument('pysat', 'testing',
                                                  sat_id='10',
                                                  clean_level='clean')])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testConst

    def add(self, function, kind='add', at_pos='end', *args, **kwargs):
        """Adds a function to the object's custom queue"""
        self.testConst.data_mod(function, kind, at_pos, *args, **kwargs)

    def test_single_adding_custom_function(self):
        """Test if custom function works correctly. Add function that returns
        pandas object."""
        def custom1(inst):
            d = 2. * inst.data.mlt
            d.name = 'doubleMLT'
            return d

        self.add(custom1, 'add')
        self.testConst.load(2009, 1)
        ans = (self.testConst[0].data['doubleMLT'].values ==
               2. * self.testConst[0].data.mlt.values).all()
        assert ans


class TestDeprecation():

    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always")

        instruments = [pysat.Instrument(platform='pysat', name='testing',
                                        sat_id='10', clean_level='clean')
                       for i in range(2)]
        self.testC = pysat.Constellation(instruments)

    def teardown(self):
        """Runs after every method to clean up previous testing"""

        del self.testC

    def test_deprecation_warning_add(self):
        """Test if constellation.add is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                # initiate function with NoneTypes since function does not
                # need to run for DeprecationWarning to be thrown
                # Setting data_label to None should produce a ValueError after
                # warning is generated
                # ==> Save time in unit tests
                self.testC.add(bounds1=None, label1=None, bounds2=None,
                               label2=None, bin3=None, label3=None,
                               data_label=None)
            except ValueError:
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning

    def test_deprecation_warning_difference(self):
        """Test if constellation.difference is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                # initiate function with NoneTypes since function does not
                # need to run for DeprecationWarning to be thrown
                # Setting data_labels to None should produce a TypeError after
                # warning is generated
                # ==> Save time in unit tests
                self.testC.difference(self.testC[0], self.testC[1],
                                      bounds=None, data_labels=None,
                                      cost_function=None)
            except TypeError:
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
