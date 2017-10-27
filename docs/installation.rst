
Installation
============

**Starting from scratch**

----

Python and associated packages for science are freely available. Convenient science python package setups are available from `Enthought <https://store.enthought.com>`_ and `Contiuum Analytics <http://continuum.io/downloads>`_. Enthought also includes an IDE, though there are a number of choices. Core science packages such as numpy, scipy, matplotlib, pandas and many others may also be installed directly via pip or your favorite package manager. 

For educational users, an IDE from `Jet Brains <https://www.jetbrains.com/student/>`_ is available for free.


**pysat**

----

Pysat itself may be installed from a terminal command line via::

   pip install pysat

Pysat requires some external non-python libraries for loading science data sets stored in netCDF and CDF formats.

**Set Data Directory**

----

Pysat will maintain organization of data from various platforms. Upon the first

.. code:: python

   import pysat

pysat will remind you to set the top level directory that will hold the data,

.. code:: python

   pysat.utils.set_data_dir(path=path)


**Common Data Format**

----

The CDF library must be installed, along with python support, before pysat is able to load CDF files.

- pysatCDF contains everything needed by pysat to load CDF files, including the NASA CDF library. At the terminal command line::

   pip install pysatCDF


**netCDF**

----

netCDF libraries must be installed, along with python support, before pysat is able to load netCDF files.

- netCDF C Library from Unidata (http://www.unidata.ucar.edu/downloads/netcdf/index.jsp)
- netCDF4-python
