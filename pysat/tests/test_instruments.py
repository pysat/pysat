import pytest

import pysat
from pysat.tests.instrument_test_class import generate_instrument_list
from pysat.tests.instrument_test_class import InstTestClass

instruments = generate_instrument_list(pysat.instruments.__all__,
                                       package='pysat.instruments')

method_list = [func for func in dir(InstTestClass)
               if callable(getattr(InstTestClass, func))]
# Search tests for iteration via pytestmark, update instrument list
for method in method_list:
    if hasattr(getattr(InstTestClass, method), 'pytestmark'):
        # Get list of names of pytestmarks
        Nargs =  len(getattr(InstTestClass, method).pytestmark)
        names = [getattr(InstTestClass, method).pytestmark[j].name
                 for j in range(0, Nargs)]
        # Add instruments from your library
        if 'all_inst' in names:
            mark = pytest.mark.parametrize("name", instruments['names'])
            getattr(InstTestClass, method).pytestmark.append(mark)
        elif 'download' in names:
            mark = pytest.mark.parametrize("inst", instruments['download'])
            getattr(InstTestClass, method).pytestmark.append(mark)
        elif 'no_download' in names:
            mark = pytest.mark.parametrize("inst", instruments['no_download'])
            getattr(InstTestClass, method).pytestmark.append(mark)


class TestInstruments(InstTestClass):

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.package = 'pysat.instruments'
        pass

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pass
