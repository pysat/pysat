.. _quickstart:

Quick-Start
===========

Helpful programs should not be hard to figure out!  Hopefully this guide will
get you to the important aspects of your scientific analysis quickly.  If you
haven't installed pysat yet, the :ref:`inst` section can help you with that.

Set the Data Directory
----------------------

pysat will maintain organization of data from various platforms. When you import
pysat for the first time, it will remind you that you need to set this variable
for your system.

.. code::

   import pysat

   Hi there!  Pysat will nominally store data in the 'pysatData' directory at
   the user's home directory level. Set `pysat.params['data_dirs']` equal to a
   path that specifies a top-level directory to store science data.

Most people are fine setting a single path for all of their data, but other
people have a LOT of data and need to store it on multiple disks. pysat supports
setting the ``data_dirs`` parameter equal to either a string or a list of
strings, as illustrated in the example below.

.. code:: python

   # Set a single directory to store all data
   path = '/path/to/your/data/directory/that/already/exists'
   pysat.params['data_dirs'] = path

   # Alternately, multiple paths may be registered. For a given Instrument,
   # pysat will iterate through the available options until data files
   # are found. The search will terminate at the first directory with data.
   # If no files are found, the first path is selected by default.
   pysat.params['data_dirs'] = [path_1, path_2, ..., path_n]

To check the currently set data directory,

.. code:: python

    print(pysat.params['data_dirs'])


Load an Instrument
------------------

The best way to see if pysat is working is to load a test instrument. The test
instrument will simulate data when it is asked to load data. Loading a day of
data will ensure there is no problem with the underlying pandas and xarray
installations.

.. code:: python

    # Testing out the pandas installation
    inst = pysat.Instrument('pysat', 'testing')
    inst.load(2009, 1)
    print(inst.data)

    # Testing out the xarray installation
    inst = pysat.Instrument('pysat', 'testing_xarray')
    inst.load(2009, 1)
    print(inst.data)

.. note:: pysat will not allow any Instrument to be instantiated without a
	  data directory being specified.

.. note:: Test instruments have a limited date range over which they will
	  simulate data.


Explore the Possibilities
-------------------------

At this point, you are set up to start exploring the tools and methods pysat
provides.  To start working with some Instruments that manage real space
science data, check out the pysat :ref:`ecosystem`.  For a more detailed dive
into pysat, check out the :ref:`tutorial` and :ref:`examples`.
