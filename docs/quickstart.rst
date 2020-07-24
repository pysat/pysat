
Quick-Start
===========

**Set Data Directory**

----

Pysat will maintain organization of data from various platforms. Upon the first

.. code:: python

   import pysat

pysat will remind you to set the top level directory that will hold the data,

.. code:: python

   pysat.utils.set_data_dir(path=path)

Note the directory path supplied must already exist or an error will be raised.
To check the currently set data directory,

.. code:: python

    print(pysat.data_dir)

To check if pysat and required packages are working, instantiate one of the
test instruments, and load a day of simulated data. Loading a day of data will
ensure there is no problem with the underlying pandas installation.

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
