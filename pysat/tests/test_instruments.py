import pytest

# Make sure to import your instrument library here
import pysat
# Import the test classes from pysat
from pysat.tests.instrument_test_class import generate_instrument_list
from pysat.tests.instrument_test_class import InstTestClass

# Developers for instrument libraries should update the following line to
# point to their own library location
# e.g.,
# instruments = generate_instrument_list(inst_loc=mypackage.instruments)
instruments = generate_instrument_list(inst_loc=pysat.instruments)

# The following lines apply the custom instrument lists to each type of test
method_list = [func for func in dir(InstTestClass)
               if callable(getattr(InstTestClass, func))]
# Search tests for iteration via pytestmark, update instrument list
for method in method_list:
    if hasattr(getattr(InstTestClass, method), 'pytestmark'):
        # Get list of names of pytestmarks
        Nargs = len(getattr(InstTestClass, method).pytestmark)
        names = [getattr(InstTestClass, method).pytestmark[j].name
                 for j in range(0, Nargs)]
        # Add instruments from your library
        if 'all_inst' in names:
            mark = pytest.mark.parametrize("inst_name", instruments['names'])
            getattr(InstTestClass, method).pytestmark.append(mark)
        elif 'download' in names:
            mark = pytest.mark.parametrize("inst_dict", instruments['download'])
            getattr(InstTestClass, method).pytestmark.append(mark)
        elif 'no_download' in names:
            mark = pytest.mark.parametrize("inst_dict",
                                           instruments['no_download'])
            getattr(InstTestClass, method).pytestmark.append(mark)


class TestInstruments(InstTestClass):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # Developers for instrument libraries should update the following line
        # to point to their own library location, e.g.,
        # self.inst_loc = mypackage.instruments
        self.inst_loc = pysat.instruments

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.inst_loc
