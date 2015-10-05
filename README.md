#pysat: Python Satellite Data Analysis Toolkit
[![Build Status](https://travis-ci.org/rstoneback/pysat.svg?branch=master)](https://travis-ci.org/rstoneback/pysat)

#What is it
The Python Satellite Data Analysis Toolkit (pysat) is a package providing a simple and flexible interface
for downloading, loading, cleaning, managing, processing, and analyzing scientific 
measurements. Though pysat was initially designed for in-situ
satellite based measurements it aims to support all instruments in space science.

Full [Documenation](http://rstoneback.github.io/pysat/)

#Main Features
* Single interface for downloading and analyzing a wide variety of science data sets.
  * Uses pandas for the underlying underlying data structure;
  capable of handling the many forms scientific measurements take in a consistent manner.
  * Science data pipeline tasks of identifying files, loading, cleaning, and modifying
  data sets are built into the instrument object.
  * Supports metadata consistent with the netCDF CF-1.6 standard. Each variable 
  has a name, long name, and units. Note units are informational only.
* Simplifies data management
  * Iterates by day/file using the for loop, manual next/prev methods, or any iterative
  method.
  * Iterate through a data set orbit-by-orbit; orbits are calculated on the fly
from loaded data and span day/month/year breaks.
  * Iterate over custom seasons
* Supports rigorous time-series calculations. 
* Includes helper functions to reduce the barrier in adding new science instruments to pysat
* Instrument independent analysis routines.

#Installation
##Starting from scratch
* One simple way to get a complete science python package is from [enthought](https://store.enthought.com)
* at command line type
```
pip install pysat
```
* in python, run pysat.utils.set_data_dir('path to top level data dir')
  * Nominal organization of data is top_dir/platform/name/tag/*/files
* NetCDF support
  * Download and install netCDF-4 C [library](http://www.unidata.ucar.edu/downloads/netcdf/index.jsp)
  * Download and install python interface to netCDF using
  ```
  pip install netCDF4
  ```
* CDF Support
  * Download and install NASA CDF [library](http://cdf.gsfc.nasa.gov/html/sw_and_docs.html)  
  * Download and install spacepy which supports python CDF interface using
  ```
  pip install spacepy
  ```
* To get the forked pandas, needed for full support of mixed data types.
```
pip install git+https://github.com/rstoneback/pandas.git
```
