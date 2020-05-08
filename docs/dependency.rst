
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
:ref:`new_inst`.  The __init__ file in this folder should import the instruments
and construct a list of instruments to aid in the testing.

.. code:: python

    from customLibrary.instruments import lib_inst1, lib_inst2

    __all__ = ['lib_inst1', 'lib_inst2']

The tests folder contains an empty __init__ file to be compliant with ``pytest``
and the test_instruments script.  Pysat includes a standard suite of instrument
tests to run on instruments.  These are imported from the ``instrument_test_class``
in the main pysat test library.  The ``test_instruments.py`` file can be copied
directly into the library, updating the instrument library name as indicated.

The ``setup.py`` file should include pysat as a dependency, as well as any
other packages required by the instruments.

A more complicated structure could include analysis routines,
like the `pysatModels <https://github.com/pysat/pysatModels>`_ package.
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
  # point to their own library package
  # e.g.,
  # instruments = generate_instrument_list(package=mypackage.instruments)
  instruments = generate_instrument_list(package=customLibrary.instruments)

The above code scans the list of instruments and flags each instrument for one
or more of the test types, as defined below.  This bit of the code should
generally be unchanged.

.. code:: python

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
              mark = pytest.mark.parametrize("name", instruments['names'])
              getattr(InstTestClass, method).pytestmark.append(mark)
          elif 'download' in names:
              mark = pytest.mark.parametrize("inst", instruments['download'])
              getattr(InstTestClass, method).pytestmark.append(mark)
          elif 'no_download' in names:
              mark = pytest.mark.parametrize("inst", instruments['no_download'])
              getattr(InstTestClass, method).pytestmark.append(mark)

Finally, the ``setup`` function under the ``TestInstruments`` class should be
updated with the package name.

.. code:: Python

  class TestInstruments(InstTestClass):

      def setup(self):
          """Runs before every method to create a clean testing setup."""
          # Developers for instrument libraries should update the following line
          # to point to their own library package
          # e.g.,
          # self.package = mypackage.instruments
          self.package = customLibrary.instruments

      def teardown(self):
          """Runs after every method to clean up previous testing."""
          del self.package
