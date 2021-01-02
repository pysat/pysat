import tempfile

import pytest

import pysat
# Make sure to import your instrument package here
# e.g.,
# import mypackage

# Import the test classes from pysat
from pysat.utils import generate_instrument_list
from pysat.tests.instrument_test_class import InstTestClass


# Optional code to pass through user and password info to test instruments
# dict, keyed by pysat instrument, with a list of usernames and passwords
# user_info = {'platform_name': {'user': 'pysat_user',
#                                'password': 'None'}}
user_info = {'pysat_testing': {'user': 'pysat_testing',
                               'password': 'pysat.developers@gmail.com'}}

# Developers for instrument libraries should update the following line to
# point to their own subpackage location
# e.g.,
# instruments = generate_instrument_list(inst_loc=mypackage.inst)
# If user and password info supplied, use the following instead
# instruments = generate_instrument_list(inst_loc=mypackage.inst,
#                                        user_info=user_info)
instruments = generate_instrument_list(inst_loc=pysat.instruments,
                                       user_info=user_info)

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
    """Uses class level setup and teardown so that all tests use the same
    temporary directory. We do not want to geneate a new tempdir for each test,
    as the load tests need to be the same as the download tests.
    """

    def setup_class(self):
        """Runs once before the tests to initialize the testing setup."""
        # Make sure to use a temporary directory so that the user's setup is not
        # altered
        self.tempdir = tempfile.TemporaryDirectory()
        self.saved_path = pysat.params['data_dirs']
        pysat.params['data_dirs'] = self.tempdir.name
        # Developers for instrument libraries should update the following line
        # to point to their own subpackage location, e.g.,
        # self.inst_loc = mypackage.instruments
        self.inst_loc = pysat.instruments

    def teardown_class(self):
        """Runs once to clean up testing from this class."""
        pysat.params['data_dirs'] = self.saved_path
        self.tempdir.cleanup()
        del self.inst_loc, self.saved_path, self.tempdir
