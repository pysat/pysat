
Quick-Start
===========

**Set Data Directory**

----

pysat will maintain organization of data from various platforms. Upon the first

.. code:: python

   import pysat

pysat will remind you to set the top level directory that will hold the data,

.. code:: python


   # Set a single directory to store all data
   pysat.params['data_dirs'] = path

   # Alternately, multiple paths may be registered. For a given Instrument,
   # pysat will iterate through the available options until data files
   # are found. The search will terminate at the first directory with data.
   # If no files are found, the first path is selected by default.
   pysat.params['data_dirs'] = [path_1, path_2, ..., path_n]

Note the directory path supplied must already exist or an error will be raised.
To check the currently set data directory,

.. code:: python

    print(pysat.params['data_dirs'])

To check if pysat and required packages are working, instantiate one of the
test instruments. The test instrument will simulate data when using it to
load data. Loading a day of data will ensure there is no problem with the
underlying pandas installation.

.. code:: python

    inst = pysat.Instrument('pysat', 'testing')
    inst.load(2009, 1)
    print(inst.data)

To verify xarray is working

.. code:: python

    inst = pysat.Instrument('pysat', 'testing_xarray')
    inst.load(2009, 1)
    print(inst.data)

.. note:: pysat will not allow an Instrument to be instantiated without a
   data directory being specified.
