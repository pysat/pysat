<div align="center">
        <img height="0" width="0px">
        <img width="20%" src="/logo.png" alt="pysat" title="pysat"</img>
</div>

# pysat: Python Satellite Data Analysis Toolkit
[![Build Status](https://travis-ci.org/rstoneback/pysat.svg?branch=master)](https://travis-ci.org/rstoneback/pysat)
[![Documentation Status](https://readthedocs.org/projects/pysat/badge/?version=latest)](http://pysat.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/rstoneback/pysat/badge.svg?branch=master)](https://coveralls.io/github/rstoneback/pysat?branch=master)
[![DOI](https://zenodo.org/badge/33449914.svg)](https://zenodo.org/badge/latestdoi/33449914)


The Python Satellite Data Analysis Toolkit (pysat) is a package providing a simple and flexible interface
for downloading, loading, cleaning, managing, processing, and analyzing scientific
measurements. Although pysat was initially designed for in situ satellite observations, it now supports many different types of ground- and space-based measurements.

Full [Documentation](http://pysat.readthedocs.io/en/latest/index.html)

JGR-Space Physics [Publication](https://doi.org/10.1029/2018JA025297)

# Main Features
* Instrument independent analysis routines.
* Instrument object providing an interface for downloading and analyzing a wide variety of science data sets.
  * Uses pandas or xarray for the underlying data structure;
  capable of handling the many forms scientific measurements take in a consistent manner.
  * Standard scientific data handling tasks (e.g., identifying, downloading,
  and loading files and cleaning and modifying data) are built into the
  Instrument object.
  * Supports metadata consistent with the netCDF CF-1.6 standard. Each variable
  has a name, long name, and units. Note units are informational only.
* Simplifies data management
  * Iterator support for loading data by day/file/orbit, independent of data storage details.
  * Orbits are calculated on the fly from loaded data and span day breaks.
  * Iterate over custom seasons
* Supports rigorous time-series calculations that require spin up/down time across day, orbit, and file breaks.
* Includes helper functions to reduce the barrier in adding new science instruments to pysat

# Installation
## Starting from scratch
* One simple way to get a complete science python package is from [enthought](https://store.enthought.com)
* at command line type
```
pip install pysat
```
* in python, run pysat.utils.set_data_dir('path to top level data dir')
  * Nominal organization of data is top_dir/platform/name/tag/*/files
* netCDF support
  * netCDF3 is supported by SciPy, no other libraries needed
  * Download and install python interface to netCDF using
  ```
  pip install netCDF4
  ```
