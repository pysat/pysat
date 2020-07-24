
Installation
============

**Starting from scratch**

----

Python and associated packages for science are freely available. Convenient
science python package setups are available from `<https://www.python.org/>`_,
`Anaconda <https://www.anaconda.com/distribution/>`_, and other locations
(some platform specific). Anaconda also includes a developer environment
that works well with pysat. Core science packages such as numpy, scipy,
matplotlib, pandas and many others may also be installed directly via pip or
your favorite package manager.

For maximum safety, pysat should be installed into its own virtual
environment to ensure there are no conflicts with any system installed Python
distributions.

For MacOS systems it is recommended that `gcc` is installed via
`HomeBrew <https://brew.sh>`_ for compatibility with Fortran code.

.. code:: bash

    brew install gcc

For Windows systems, please see the following
`instructions <https://github.com/pysat/pysatCDF/blob/master/README.md>`_
for setting up a POSIX compatible C/Fortran environment.

To use Anaconda's tools for creating a suitable virtual environment, for Python
2
.. code:: bash

    conda create -n virt_env_name python=2.7
    conda activate virt_env_name
    conda install numpy -c forge
and for Python 3

.. code:: bash

    conda create -n virt_env_name python=3
    conda activate virt_env_name
    conda install numpy -c forge

**pysat**

----

Pysat itself may be installed from a terminal command line via::

   pip install pysat

Note that pysat requires a number of packages that will be
installed automatically if not already present on a system. The
default behavior for updating required libraries already on a system depends
upon the version of pip present.

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

The upper caps for packages above will be removed for the upcoming pysat
3.0.0 release.

**Development Installation**

----

pysat may also be installed directly from the source repository on github::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   python setup.py install

An advantage to installing through github is access to the development branches.
The latest bugfixes can be found in the ``develop`` branch. However, this
branch is not stable (as the name implies). We recommend using this branch in a
virtual environment or using `python setup.py develop`.::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   git checkout develop
   python setup.py develop

The use of `develop` rather than `install` installs the code 'in-place', so
any changes to the software do not have to be reinstalled to take effect.

The development version for v3.0 can be found in the ``develop-3``
branch (see above for caveats).
