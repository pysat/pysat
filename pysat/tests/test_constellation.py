from nose.tools import raises
import pysat

# TODO


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
        for i in range(3):
            insts.append(pysat.Instrument('pysat', 'testing', clean_level='clean'))
        self.const1 = Constellation(insts)
        self.const2 = Constellation([pysat.Instrment('pysat', 'testing', clean_level='clean')])

    def teardown(self):
        del self.const1
        del self.const2

    def test_addition_identical(self):
        for inst in self.const1:
            inst.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        for inst in self.const2:
            inst.bounds = (pysat.datetime(2008,1,1), pysat.datetime(2008,2,1))
        
        bounds1 = [0,360]
        label1 = 'longitude'
        bounds2 = [-90,90]
        label2 = 'latitude'
        bins3 = [0,24,24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results1 = self.const1.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        results2 = self.const2.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        med1 = results1['dummy1']['median']
        med2 = results2['dummy1']['median']
        assert array_equal(med1, med2)

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
            for j in i:
                assert j == 0

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
        diff = med - refmed
        for i in diff:
            for j in i:
                assert j <= 10 and j >= 0

class TestAdditionSingleInstrument:
    def setup(self):
        """
        The constellation consists of a single instrument, so performing 
        addition on it should just return the instrument's data within
        the bounds
        """
        insts = []
        testInst = pysat.Instrument('pysat', 'testadd', clean_level='clean'))
        insts.append(testInst)
        self.testConst = pysat,Constellation(insts)

    def teardown(self):
        del self.testConst

    def test_addition_single_instrument(self):
        for inst in self.testConst:
            inst.bounds = (pysat.datatime(2008, 1, 1), pysat.datetime(2008, 2 ,1))
        bounds1 = [0, 360]
        label1 = 'longitude'
        bounds2 = [-90, 90]
        label2 = 'latitude'
        bins3 = [0, 24, 24]
        label3 = 'mlt'
        data_label = 'dummy1'
        results = self.testConst.add(bounds1, label1, bounds2, label2, bins3, label3,
                data_label)
        refresults = pysat.ssnl.avg.median2d(self.testInst, [0, 360, 1], label1, [-90, 90, 1], label2, bins3, label3)

        med = results['dummy1']['median']
        refmed = refresults['dummy1']['median']
        assert array_equal(med, refmed)


