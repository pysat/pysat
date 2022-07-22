<div align="center">
        <img height="0" width="0px">
        <img width="20%" src="https://raw.githubusercontent.com/pysat/pysat/main/docs/images/logo.png" alt="The pysat logo: A snake orbiting a blue sphere" title="pysat"</img>
</div>

# pysat: Python Satellite Data Analysis Toolkit
[![PyPI Package latest release](https://img.shields.io/pypi/v/pysat.svg)](https://pypi.python.org/pypi/pysat)
[![Build Status](https://github.com/pysat/pysat/actions/workflows/main.yml/badge.svg)](https://github.com/pysat/pysat/actions/workflows/main.yml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/pysat/badge/?version=latest)](http://pysat.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/pysat/pysat/badge.svg?branch=main)](https://coveralls.io/github/pysat/pysat?branch=main)
[![DOI](https://zenodo.org/badge/33449914.svg)](https://zenodo.org/badge/latestdoi/33449914)

The Python Satellite Data Analysis Toolkit (pysat) is a package providing a
simple and flexible interface for downloading, loading, cleaning, managing,
processing, and analyzing scientific measurements. Although pysat was initially
designed for in situ satellite observations, it now supports many different
types of ground- and space-based measurements.

Full [Documentation](http://pysat.readthedocs.io/en/latest/index.html)

JGR-Space Physics [Publication](https://doi.org/10.1029/2018JA025297)

[Citation Info](https://pysat.readthedocs.io/en/latest/citing.html)

Come join us on Slack! An invitation to the pysat workspace is available 
in the 'About' section of the [pysat GitHub Repository.](https://github.com/pysat/pysat)
Development meetings are generally held fortnightly.

# Main Features
* Instrument independent analysis routines.
* Instrument object providing an interface for downloading and analyzing a wide
  variety of science data sets.
  * Uses pandas or xarray for the underlying data structure;
    capable of handling the many forms scientific measurements take in a
    consistent manner.
  * Standard scientific data handling tasks (e.g., identifying, downloading,
    and loading files and cleaning and modifying data) are built into the
    Instrument object.
  * Supports metadata consistent with the netCDF CF-1.6 standard. Each variable
    has a name, long name, and units. Note units are informational only.
* Simplifies data management
  * Iterator support for loading data by day/file/orbit, independent of data
    storage details.
  * Orbits are calculated on the fly from loaded data and span day breaks.
  * Iterate over custom seasons
* Supports rigorous time-series calculations that require spin up/down time
  across day, orbit, and file breaks.
* Includes helper functions to reduce the barrier in adding new science
  instruments to pysat

# Installation
## Starting from scratch
* Python and associated packages for science are freely available. Convenient
  science python package setups are available from https://www.python.org/,
  [Anaconda](https://www.anaconda.com/distribution/), and other locations
  (some platform specific). Anaconda also includes a developer environment that
  works well with pysat. Core science packages such as numpy, scipy, matplotlib,
  pandas and many others may also be installed directly via pip or your
  favorite package manager.

* Installation through pip
```
pip install pysat
```
* Installation through github
```
git clone https://github.com/pysat/pysat.git
cd pysat
python setup.py install
```
An advantage to installing through github is access to the development branches.
The latest bugfixes can be found in the `develop` branch.  However, this branch
is not stable (as the name implies).  We recommend using this branch in a
virtual environment or using `python setup.py develop`.
```
git clone https://github.com/pysat/pysat.git
cd pysat
git checkout develop
python setup.py develop
```
* Note that pysat requires a number of packages for the install.  
  * dask
  * netCDF4
  * numpy
  * pandas
  * portalocker
  * scipy
  * toolz
  * xarray
* The first time the package is run, you will need to specify a directory to
  store data. In python, run:
```
pysat.params['data_dirs'] = 'path/to/directory/that/may/or/may/not/exist'
```
  * Nominal organization of data is top_dir/platform/name/tag/inst_id/files
