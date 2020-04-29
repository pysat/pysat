
.. |br| raw:: html

    <br>

.. _pysat-dependency:

Using pysat as a dependency
===========================

Instrument Libraries
--------------------
Say you are developing an instrument library under the name ``pysatLib``,
which has two instrument objects. A minimalist structure for the library
could look something like:

.. code::

  .
  |--pysatLib
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
NEW_INSTRUMENT.  The __init__ file in this folder should import the instruments
and construct a list of instruments to aid in the testing.

.. code:: python

    from pysatLib.instruments import lib_inst1, lib_inst2

    __all__ = ['lib_inst1', 'lib_inst2']

The tests folder contains an empty __init__ file to be compliant with ``pytest``
and the test_instruments script.  Pysat includes a standard suite of instrument
tests to run on instruments.  These are imported from the ``instrument_test_class``
in the main pysat test library.  The ``test_instruments.py`` file can be copied
directly into the library, updating the instrument library name as indicated.

The ``setup.py`` file should include pysat as a dependency, as well as any
other packages required by the instruments.

A more complicated structure could include analysis routines, like the
pysatModels package.  The structure then could look like:

.. code::

  .
  |--pysatLib
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
  |   |   |-- contrast.py
  |   |   `-- test_instruments.py
  |   `-- __init__.py
  |-- README.md
  `-- setup.py
