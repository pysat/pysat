
.. |br| raw:: html

    <br>

.. _pysat-dependency:

Using pysat as a dependency
===========================


.. _pysat-dep-instlib:

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
:ref:`rst_new_inst`.  The ``__init__.py`` file in this folder should import the
instruments and construct a list of instruments to aid in the testing.

.. code:: python

    from customLibrary.instruments import lib_inst1, lib_inst2

    __all__ = ['lib_inst1', 'lib_inst2']

The tests folder contains an empty ``__init__.py`` file to be compliant with
:py:mod:`pytest` and the test_instruments script.  pysat includes a standard
suite of instrument tests to run on instruments.  These are imported from the
:py:mod:`pysat.tests.instrument_test_class` in the main pysat test library.  The
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


.. _pysat-dep-testinst:

Using pysat to test your instruments
------------------------------------

A generalized instrument test class is provided under :py:mod:`pysat.tests` for
developers.  Continuing the above example, developers may copy over the
``test_instruments.py`` file and update it in a few locations.  For example

.. code:: python

  # Make sure to import your instrument library here
  import customLibrary

  # Import the test classes from pysat
  from pysat.tests.classes.cls_instrument_library import InstLibTests

Before creating a test class that will inherit from ``InstLibTests``, the class
should be told which tests to run on which instruments.  This can be done by
using the ``initialize_test_package`` method in the core class.

.. code:: python

  InstLibTests.initialize_test_package(InstLibTests,
                                       inst_loc=customLibrary.instruments)

If custom info such as a username is required, it should be specified as part of
this command so it is attached to each instrument for the tests.

.. code:: python

 user_info = {'pysat_testing': {'user': 'pysat_testing',
                                'password': 'pysat.developers@gmail.com'}}
 InstLibTests.initialize_test_package(InstLibTests,
                                      inst_loc=customLibrary.instruments,
                                      user_info=user_info)


Now a class that pytest can run should be created, inheriting the tests and
instrument instructions from the standard test class above.  Note that pytest
will only run classes that begin with the word "Test".

.. code:: Python

  class TestInstruments(InstLibTests):
  """Main class for instrument tests.

  Note
  ----
  All standard tests, setup, and teardown inherited from the core pysat
  instrument test class.

  """

All setup and teardown routines are inherited from the core class. Note that the
test methods use temporary directories to store downloaded files to avoid
breaking a user's directory structure.


.. _pysat-dep-options:

Adding custom kwargs to load tests
----------------------------------

If an instrument in a custom library has a custom kwarg, this can be added as
part of the standard load tests.  When writing the instrument module, simply add
the options as a dict of kwargs with the name `_test_load_opt`:

.. code:: python

   _test_dates = {'': {'Level_1': dt.datetime(2020, 1, 1),
                       'Level_2': dt.datetime(2020, 1, 1)}}
   _test_load_opt = {'': {'Level_1': {'myoption': True}}}

The structure of the dict should be similar to the `_test_dates` construction.
See :ref:`rst_test-temp` for more information on structuring test attributes
for custom instrument libraries. For multiple options, a list of dicts should
be used.

.. code:: python

   _test_dates = {'': {'Level_1': dt.datetime(2020, 1, 1),
                       'Level_2': dt.datetime(2020, 1, 1)}}
   _test_load_opt = {'': {'Level_1': [{'myoption': True},
                                      {'myoption': False, 'num_samples': 30}]}}

Note that this test only verifies that the instrument can be loaded with that
option.  To test for specific outcomes, see the following section.


.. _pysat-dep-addtests:

Adding custom tests in pysat
----------------------------

If the instrument library has custom routines that need testing, you can add
additional test methods routines after the class declaration.  For instance,
you may want to test that a specific instrument generates an error message
when initialized improperly.

.. code:: Python

  @pytest.mark.parametrize("kw_dict", [{'inclination': 13, 'alt_apoapsis': 850},
                                       {'TLE1': 'abc'}])
  def test_sgp4_options_errors(self, kw_dict):
      """Test optional keyword combos for sgp4 that generate errors."""

      with pytest.raises(KeyError) as kerr:
          self.test_inst = pysat.Instrument(
              inst_module=pysatMissions.instruments.missions_sgp4,
              **kw_dict)
      assert str(kerr).find('Insufficient kwargs') >= 0
      return


Other times you may need to run a new test across all instruments.  For applying
``@pytest.mark.parametrize`` across multiple instruments, you can use the
instrument lists generated by ``initialize_test_package``.  When running this
routine, make sure to use the optional output for the custom instrument lists:

.. code:: Python

  instruments = InstLibTests.initialize_test_package(
    InstLibTests, inst_loc=customLibrary.instruments)

The instruments in the custom library will be grouped into four lists:

* instruments['names']: A list of all module names to check for
  standardization
* instruments['download']: A list of dicts containing info to initialize
  instruments for end-to-end testing.  Used to access instruments on remote
  servers.
* instruments['load_options']: A list of dicts containing info to initialize
  instruments for end-to-end testing.  Includes all items in
  instruments['download'] along with alternate instruments with optional
  kwarg inputs. Used to load data products that have already been downloaded.
* instruments['no_download']: A list of dicts containing info to initialize
  instruments without download support for specialized local tests.  Used for
  limited testing since remote data access is not available.

Then, the new test may be created under the ``TestInstruments`` class as before.

.. code:: Python

  @pytest.mark.parametrize("inst_dict", instruments['download'])
  def test_inst_file_date_range(self, inst_dict):
      """Test operation of file_date_range keyword."""

      file_date_range = pds.date_range(dt.datetime(2021, 1, 1),
                                       dt.datetime(2021, 12, 31))
      _, date = initialize_test_inst_and_date(inst_dict)
      self.test_inst = pysat.Instrument(inst_module=inst_dict['inst_module'],
                                        file_date_range=file_date_range)
      file_list = self.test_inst.files.files

      assert all(file_date_range == file_list.index)
      return


.. _pysat-dep-testcust:

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

    def setup_method(self):
        self.inst = pysat.Instrument(platform='pysat', name='testing')
        self.inst.load(2009, 1)

    def teardown_method(self):
        del self.inst

    def test_stats_mean(self):
        mean_val = stats.mean(inst['dummy1'])
        assert mean_val == 11.3785

The :py:meth:`TestCompare.setup` method is used to define and load a fresh
instrument for each test.  While data are automatically generated, limits on
the usable range have been imposed for testing purposes.  The test instruments
generate dates between 1 Jan 2008 and 31 Dec 2010 for use in the pysat
ecosystem.  This allows for coverage for year changes both with and without
leap days.

.. _pysat-dep-tips:

Tips and Tricks
---------------

Remember to include pysat as a dependency in your setup.py or setup.cfg file.

The CI environment will also need to be configured to install pysat and its
dependencies.  You may need to install pysat from github rather than pip if
you need to test against a specific development branch.

If the pysat API is changing for an upcoming release, you can use :py:mod:`packaging`
to quickly determine the pysat version and potentially skip tests that are only
necessary for a limited range of pysat versions.

.. code:: python

  from packaging.version import Version
  import pysat
  import pytest

  @pytest.mark.skipif(Version(pysat.__version__) <= Version('3.0.1'),
                      reason=''.join(('Requires test model in pysat ',
                                      ' v3.0.2 or later.')))
  def test_new_feature(self):
     """Check a new feature that requires the develop pysat."""

  
