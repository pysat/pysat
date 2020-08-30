
Installation
============

**Starting from scratch**

----

Python and associated packages for science are freely available. Convenient science python package setups are available from https://www.python.org/, [Anaconda](https://www.anaconda.com/distribution/), and other locations (some platform specific). Anaconda also includes a developer environment that works well with pysat. Core science packages such as numpy, scipy, matplotlib, pandas and many others may also be installed directly via pip or your favorite package manager.


**pysat**

----

Pysat itself may be installed from a terminal command line via::

   pip install pysat

Or alternatively through github::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   python setup.py install

An advantage to installing through github is access to the development branches.  The latest bugfixes can be found in the ``develop`` branch.   However, this branch is not stable (as the name implies). We recommend using this branch in a virtual environment or using `python setup.py develop`.::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   git checkout develop
   python setup.py develop


Note that pysat requires a number of packages for the install.

    * netCDF4
    * numpy (>=1.12)
    * pandas (>=0.23)
    * scipy
    * xarray


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
