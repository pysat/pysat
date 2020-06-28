
Installation
============

**Starting from scratch**

----

Python and associated packages for science are freely available. Convenient science python package setups are available from https://www.python.org/ and `Anaconda <https://www.anaconda.com/distribution/>`_. Anaconda also includes a developer environment. Core science packages such as numpy, scipy, matplotlib, pandas and many others may also be installed directly via pip or your favorite package manager.

For educational users, developer environments from `Jet Brains <https://www.jetbrains.com/student/>`_ are available for free.


**pysat**

----

Pysat itself may be installed from a terminal command line via::

   pip install pysat

Or alternatively through github::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   python setup.py install

An advantage to installing through github is access to the development branches.  The latest bugfixes can be found in the ``develop`` branch::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   git checkout develop
   python setup.py install


Note that pysat requires a number of packages for the install.  The upper caps for packages below have been removed for the upcoming pysat 3.0.0 release, which can be accessed in the ``develop-3`` branch, which can be accessed as discussed above.

     * beautifulsoup4
     * h5py
     * lxml
     * madrigalWeb
     * matplotlib
     * netCDF4
     * numpy (>=1.12)
     * pandas (>=0.23, <0.25)
     * PyForecastTools
     * pysatCDF
     * requests
     * scipy
     * xarray (<0.15)


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
