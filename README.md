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

The Python Satellite Data Analysis Toolkit (pysat) provides a simple and
flexible interface for robust data analysis from beginning to end - including
downloading, loading, cleaning, managing, processing, and analyzing data.
Pysat's plug-in design allows analysis support for any data, including user
provided data sets. The pysat team provides a variety of plug-ins to support
public scientific data sets in packages such as pysatNASA, pysatMadrigal, and
more, available as part of the general [pysat ecosystem](https://github.com/pysat).

Full [Documentation](http://pysat.readthedocs.io/en/latest/index.html)

JGR-Space Physics [Publication](https://doi.org/10.1029/2018JA025297)

Pysat Ecosystem [Publication](https://www.frontiersin.org/articles/10.3389/fspas.2023.1119775/full)

[Citation Info](https://pysat.readthedocs.io/en/latest/citing.html)

Come join us on Slack! An invitation to the pysat workspace is available
in the 'About' section of the
[pysat GitHub Repository.](https://github.com/pysat/pysat)
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

The following instructions provide a guide for installing pysat and give some
examples on how to use the routines.

## Prerequisites

pysat uses common Python modules, as well as modules developed by and for the
Space Physics community.  This module officially supports Python 3.X+.

| Common modules | Community modules |
| -------------- | ----------------- |
| dask           | netCDF4           |
| numpy >= 1.12  |                   |
| pandas         |                   |
| portalocker    |                   |
| pytest         |                   |
| scipy          |                   |
| toolz          |                   |
| xarray         |                   |


## PyPi Installation
```
pip install pysat
```

## GitHub Installation
```
git clone https://github.com/pysat/pysat.git
```

Change directories into the repository folder and run the pyproject.toml or
setup.py file.  For a local install use the "--user" flag after "install".

```
cd pysat/
python -m build .
pip install .
```

# Using pysat

* The first time pysat is run, you will need to specify a directory to store
  the data. In Python, run:
```
pysat.params['data_dirs'] = 'path/to/directory/that/may/or/may/not/exist'
```
  * Nominal organization of data is top_dir/platform/name/tag/inst_id/files

Detailed examples and tutorials for using pysat are available in the
[documentation](http://pysat.readthedocs.io/en/latest/index.html).
