
Installation
============

**Starting from scratch**

----

Python and associated packages for science are freely available. Convenient
science python package setups are available from `<https://www.python.org/>`_,
`Anaconda <https://www.anaconda.com/distribution/>`_, and other locations
(some platform specific). Anaconda also includes a developer environment
that works well with pysat. Core science packages such as numpy, scipy,
matplotlib, pandas and many others may also be installed directly via the
python package installer "pip" or your favorite package manager.

For maximum safety, pysat should be installed into its own virtual
environment to ensure there are no conflicts with any other installed Python
distributions.

For MacOS and Linux systems make sure that `gcc` is compatible with Fortran
code. In Linux this can be accomplished by installing `gfortran`.  For MacOS
systems it is recommended that `gcc` is installed via 
`HomeBrew <https://brew.sh>`_
for compatibility with Fortran code.

.. code:: bash

    brew install gcc


For Windows systems, please see the Windows section below
for setting up a POSIX compatible C/Fortran environment.

To use Anaconda's tools for creating a suitable virtual environment, for Python
2

.. code:: bash

    conda create -n virt_env_name python=2.7
    conda activate virt_env_name
    conda install numpy -c conda
and for Python 3

.. code:: bash

    conda create -n virt_env_name python=3
    conda activate virt_env_name
    conda install numpy -c conda



**pysat**

----

pysat itself may be installed from a terminal command line via::

   pip install pysat

There are a few packages that pysat depends on that will be installed as
needed by the installer:

     * netCDF4
     * numpy (>=1.12)
     * pandas (>=0.23)
     * scipy
     * xarray



**Development Installation**

----

pysat may also be installed directly from the source repository on github::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   python setup.py install

An advantage to installing through github is access to the development branches.
The latest bugfixes can be found in the ``develop`` branch. However, this
branch is not stable (as the name implies). We recommend using this branch in a
virtual environment and using::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   git checkout develop
   python setup.py develop

The use of `develop` rather than `install` installs the code 'in-place', so
any changes to the software do not have to be reinstalled to take effect.



**Windows**

To get pysat installed in Windows you need a POSIX compatible C/ Fortran
compiling environment. This is required to compile the
`pysatCDF <https://github.com/pysat/pysatCDF/>`_ package.

Python environment: Python 3.x

#. Install Microsoft's Windows Subsystem for Linux (WSL) following
   the directions from `<https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_.
#. Python, and pysat, may now be installed following the instructions
   above.
