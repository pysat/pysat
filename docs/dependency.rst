
.. |br| raw:: html

    <br>

.. _pysat-dependency:

Using pysat as a dependency
===========================

Instrument Libraries
--------------------
Say you are developing an instrument library under the name ``customLibrary``,
which has two instrument objects. A minimalist structure for the library
could look something like:

.. code::

  .
  |--customLibrary
  |   |-- docs
  |   |   `-- tutorial.rst
  |   |-- instruments
  |   |   |-- __init__.py
  |   |   |-- lib_inst1.py
  |   |   |-- lib_inst2.py
  |   |-- tests
  |   |   |-- __init__.py
  |   |   `-- test_instruments.py
  |   `-- __init__.py
  |-- README.md
  `-- setup.py


The instruments folder includes a file for each instrument object.  The
requirements for structuring each of the instruments is discussed in
:ref:`rst_new_inst`.  The __init__ file in this folder should import the
instruments and construct a list of instruments to aid in the testing.

.. code:: python

    from customLibrary.instruments import lib_inst1, lib_inst2

    __all__ = ['lib_inst1', 'lib_inst2']

The tests folder contains an empty __init__ file to be compliant with ``pytest``
and the test_instruments script.  pysat includes a standard suite of instrument
tests to run on instruments.  These are imported from the
``instrument_test_class`` in the main pysat test library.  The
``test_instruments.py`` file can be copied directly into the library, updating
the instrument library name as indicated.

The ``setup.py`` file should include pysat as a dependency, as well as any
other packages required by the instruments.

A more complicated structure could include analysis routines,
like the `pysatModels <https://github.com/pysat/pysatModels>`_ package, or
methods for common analysis routines used for a specific data set, like
the `pysatMadrigal <https://github.com/pysat/pysatMadrigal>`_ package.
The structure then could look like:

.. code::

  .
  |--customLibrary
  |   |-- docs
  |   |   `-- tutorial.rst
  |   |-- instruments
  |   |   |-- __init__.py
  |   |   |-- lib_inst1.py
  |   |   |-- lib_inst2.py
  |   |   |-- methods
  |   |   |   |-- __init__.py
  |   |   |   |-- general.py
  |   |   |   `-- inst1.py
  |   |-- tests
  |   |   |-- __init__.py
  |   |   `-- test_instruments.py
  |   |-- utils
  |   |   |-- __init__.py
  |   |   |-- compare.py
  |   |   `-- contrast.py
  |   `-- __init__.py
  |-- README.md
  `-- setup.py

Using pysat to test your instruments
------------------------------------

A generalized instrument test class is provided under ``pysat.tests`` for
developers.  Continuing the above example, developers may copy over the
``test_instruments.py`` file and update it in a few locations.  For example

.. code:: python

  # Make sure to import your instrument library here
  import customLibrary

  # Import the test classes from pysat
  from pysat.tests.instrument_test_class import generate_instrument_list
  from pysat.tests.instrument_test_class import InstTestClass

  # Developers for instrument libraries should update the following line to
  # point to their own library location. For example,
  # instruments = generate_instrument_list(inst_loc=mypackage.instruments)
  instruments = generate_instrument_list(inst_loc=customLibrary.instruments)

The above code scans the list of instruments and flags each instrument for one
or more of the test types, as defined below.  This bit of the code should
generally be unchanged.  Instruments are grouped in three lists:

* instruments['names']: A list of all module names to check for
  standardization
* instruments['download']: A list of dicts containing info to initialize
  instruments for end-to-end testing
* instruments['no_download']: A list of dicts containing info to initialize
  instruments without download support for specialized local tests

.. code:: python

  # The following lines apply the custom instrument lists to each type of test
  method_list = [func for func in dir(InstTestClass)
                 if callable(getattr(InstTestClass, func))]
  # Search tests for iteration via pytestmark, update instrument list
  for method in method_list:
      if hasattr(getattr(InstTestClass, method), 'pytestmark'):
          # Get list of names of pytestmarks
          nargs = len(getattr(InstTestClass, method).pytestmark)
          names = [getattr(InstTestClass, method).pytestmark[j].name
                   for j in range(0, nargs)]
          # Add instruments from your library
          if 'all_inst' in names:
              mark = pytest.mark.parametrize("inst_name", instruments['names'])
              getattr(InstTestClass, method).pytestmark.append(mark)
          elif 'download' in names:
              mark = pytest.mark.parametrize("inst_dict",
	                                        instruments['download'])
              getattr(InstTestClass, method).pytestmark.append(mark)
          elif 'no_download' in names:
              mark = pytest.mark.parametrize("inst_dict",
                                             instruments['no_download'])
              getattr(InstTestClass, method).pytestmark.append(mark)

Finally, the ``setup_class`` function under the ``TestInstruments`` class should be
updated with the location of the instrument subpackage.  Note that the routine uses 
temporary directories to store downloaded files to avoid breaking user's directory 
structure.

.. code:: Python

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


Testing custom analysis routines
--------------------------------

What if you are developing analysis routines or instruments with special
functions?  pysat includes a series of test instrument objects that can be
imported by other packages to test those functions.  For instance,
`pysatModels <https://github.com/pysat/pysatModels>`_ contains a series of
routines to collect similar measurements between instruments and models.
The test instruments are used as part of the unit tests.  This allows us to
thoroughly test routines without including a large volume of data as part of
the package.

pysat_testing
^^^^^^^^^^^^^
:ref:`api-pysat-testing` is the basic test object.  It returns a satellite-like
object with 1D data as a function of latitude, longitude, and altitude in a
pandas format.  Most similar to in situ data.

pysat_testing_xarray
^^^^^^^^^^^^^^^^^^^^
:ref:`api-pysat-testing_xarray` returns a satellite-like object with 1D data as
a function of latitude, longitude, and altitude in a xarray format.

pysat_testing2d
^^^^^^^^^^^^^^^
:ref:`api-pysat-testing2d` is another satellite-like object that also returns
profile data as a function of altitude at some distance from the satellite. It
is similar to a Radio Occultation or other instruments that have altitude
profiles.

pysat_testing2d_xarray
^^^^^^^^^^^^^^^^^^^^^^
:ref:`api-pysat-testing2d_xarray` is a satellite-like object that returns all
of the above plus an imager-like data set, ie, remote data that is a function
of time and two spatial dimensions.

pysat_testmodel
^^^^^^^^^^^^^^^
:ref:`api-pysat-testmodel` is an xarray object that returns a 4D object as a
function of latitude, longitude, altitude, and time.  It most closely resembles
data sets from geophysical models.

All of these objects return dummy `data` values that are either constants or
small periodic variations.  The intent of these objects are to return data sets
that resemble instrument data in scope.

A very basic example is shown below.  Here a `stats` library is imported from
the custom instrument.  The `dummy1` variable is a simple data set that returns
values between 0 and 20.

.. code:: python

  import pysat

  from customLibrary import stats

  class TestCompare:

    def setup(self):
        self.inst = pysat.Instrument(platform='pysat', name='testing')
        self.inst.load(2009, 1)

    def teardown(self):
        del self.inst

    def test_stats_mean(self):
        mean_val = stats.mean(inst['dummy1'])
        assert mean_val == 11.3785

The ``setup`` function is used to define and load a fresh instrument for each
test.  While data are automatically generated, limits on the usable range have
been imposed for testing purposes.  The test instruments generate dates between
1 Jan 2008 and 31 Dec 2010 for use in the pysat ecosystem.  This allows for
coverage for year changes both with and without leap days.

Tips and Tricks
---------------

Remember to include pysat as a dependency in your setup.py or setup.cfg file.

The CI environment will also need to be configured to install pysat and its
dependencies.  You may need to install pysat from github rather than pip if
you need to test against a specific development branch.
