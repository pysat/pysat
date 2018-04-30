from nose.tools import raises
import numpy as np
import pysat
import numpy as np


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

    @raises(ValueError)
    def test_construct_null(self):
        """Attempt to construct a Constellation with
        no arguments."""
        pysat.Constellation()

    def test_getitem(self):
        """Test Constellation:__getitem__."""
        assert self.const[0] == self.instruments[0]
        assert self.const[1] == self.instruments[1]
        assert self.const[:] == self.instruments[:]
        assert self.const[1::-1] == self.instruments[1::-1]

    def test_str(self):
        """Test Constellation:__str__."""
        # FIXME define that string.
        assert str(self.const) == "stringgoeshere"

    def test_repr(self):
        """Test Constellation:__repr__."""
        # FIXME
        print(repr(self.const))
        assert repr(self.const) == "Constellation([..."

    # TODO write tests for add, difference

class TestAdditionIdenticalInstruments:
    def setup(self):
        insts = []
        for _ in range(3):
            insts.append(pysat.Instrument('pysat', 'testing', clean_level='clean'))
        self.const1 = pysat.Constellation(insts)
        self.const2 = pysat.Constellation(
                        [pysat.Instrument('pysat', 'testing', clean_level='clean')])

    def teardown(self):
        del self.const1
        del self.const2

    def test_addition_identical(self):
        for inst in self.const1:
            inst.bounds = (pysat.datetime(2008, 1, 1), pysat.datetime(2008, 2, 1))
        for inst in self.const2:
            inst.bounds = (pysat.datetime(2008, 1, 1), pysat.datetime(2008, 2, 1))

        bounds1 = [0,360]
        label1 = 'longitude'
        bounds2 = [-90,90]
        label2 = 'latitude'
        bins3 = [0,24,24]
        label3 = 'mlt'
        data_label = ['dummy1']
        results1 = self.const1.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        results2 = self.const2.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        med1 = results1['dummy1']['median']
        med2 = results2['dummy1']['median']
        for (left, right) in zip(med1, med2):
            assert left == right or \
                   ( np.isnan(left) and np.isnan(right) )

        #for i in range(len(med1)):
        #    assert med1[i] == med2[i]

class TestAdditionOppositeInstruments:
    def setup(self):
        """
        The data in testadd1['dummy1'] is just ascending integers 0 to the
        length of the other data, testadd2 has the same data but negative.
        The addition of these two signals should be zero everywhere.
        """
        insts = []
        insts.append(pysat.Instrument('pysat', 'testadd1', clean_level='clean'))
        insts.append(pysat.Instrument('pysat', 'testadd2', clean_level='clean'))
        self.testC = pysat.Constellation(insts)

    def teardown(self):
        del self.testC

    def test_addition_opposite_instruments(self):
        for inst in self.testC:
            inst.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        bounds1 = [0,360]
        label1 = 'longitude'
        bounds2 = [-90,90]
        label2 = 'latitude'
        bins3 = [0,24,24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results = self.testC.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        med = results['dummy1']['median']
        for i in med:
            assert i == 0

class TestAdditionSimilarInstruments:
    def setup(self):
        """
        All the data in dummy1 of testadd3 is the data in testadd1 + 10
        So the addition of testadd1 and testadd3 should be no more than 10 off from
        the addition of just testadd1
        TODO: actually check the math on this
        """
        insts = []
        insts.append(pysat.Instrument('pysat', 'testadd1', clean_level='clean'))
        insts.append(pysat.Instrument('pysat', 'testadd3', clean_level='clean'))
        self.testC = pysat.Constellation(insts)
        self.refC = pysat.Constellation([pysat.Instrument('pysat', 'testadd1', clean_level='clean')])

    def teardown(self):
        del self.testC

    def test_addition_similar_instruments(self):
        for inst in self.testC:
            inst.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        for inst in self.refC:
            inst.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        bounds1 = [0,360]
        label1 = 'longitude'
        bounds2 = [-90,90]
        label2 = 'latitude'
        bins3 = [0,24,24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results = self.testC.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        refresults = self.refC.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        med = results['dummy1']['median']
        refmed = refresults['dummy1']['median']
        diff = [med[i] - refmed[i] for i in range(len(med))]
        for i in diff:
            assert i <= 10 and i >= 0

class TestAdditionSingleInstrument:
    def setup(self):
        """
        The constellation consists of a single instrument, so performing
        addition on it should just return the instrument's data within
        the bounds
        """
        insts = []
        self.testInst = pysat.Instrument('pysat', 'testadd4', clean_level='clean')
        insts.append(self.testInst)
        self.testConst = pysat.Constellation(insts)

    def teardown(self):
        del self.testConst

    def test_addition_single_instrument(self):
        for inst in self.testConst:
            inst.bounds = (pysat.datetime(2008, 1, 1), pysat.datetime(2008, 2 ,1))
        bounds1 = [0, 360]
        label1 = 'longitude'
        bounds2 = [-90, 90]
        label2 = 'latitude'
        bins3 = [0, 24, 24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results = self.testConst.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)

        med = results['dummy1']['median']
        for i in med:
            assert  i == 5

    # TODO write tests for add, difference.

class TestDifferenceSameInstrument:
    def setup(self):
        self.const = pysat.Constellation(name='test_diff')

    def teardown(self):
        del self.const

    def test_diff(self):
        self.const.load(date=pysat.datetime(2008,1,1))
        bounds = [('longitude', 'longitude', 0, 360, .5), 
                ('latitude', 'latitude', -90, 90, .5), 
                ('mlt', 'mlt', 0, 24, .1)]
        results = self.const.difference(self.const[0], self.const[1], 
                bounds, [('dummy1','dummy1')], cost_function)
        diff = results['dummy1']
        dist = results['dist']
        for i in diff:
            assert i == 0
        for i in dist:
            assert i == 0

class TestDifferenceSmallInstruments(TestDifferenceSameInstrument):
    def setup(self):
        self.const = pysat.Constellation(name='test_diff_small')

class TestDifferenceSimilarInstruments:
    def setup(self):
        self.const = pysat.Constellation(name='test_diff2')

    def teardown(self):
        del self.const

    def test_diff_similar_instruments(self):
        self.const.load(date=pysat.datetime(2008,1,1))
        bounds = [('longitude', 'longitude', 0, 360, .5), 
                ('latitude', 'latitude', -90, 90, .5), 
                ('mlt', 'mlt', 0, 24, .1)]
        results = self.const.difference(self.const[0], self.const[1], 
                bounds, [('dummy1','dummy1')], cost_function)
        diff = results['dummy1']
        dist = results['dist']
        for i in diff:
            assert i == 5

def cost_function(point1, point2):
    #TODO: actually do lat/long difference correctly.
    #alternatively, let the user supply a cost function.
    lat_diff = point1['latitude'] - point2['latitude']
    long_diff = point1['longitude'] - point2['longitude']
    return lat_diff*lat_diff + long_diff*long_diff



