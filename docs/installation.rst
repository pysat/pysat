.. _inst:


Installation
============

Python and associated packages for science are freely available. Convenient
science python package setups are available from `<https://www.python.org/>`_,
`Anaconda <https://www.anaconda.com/products/individual/>`_, and other locations
(some platform specific). Anaconda also includes a developer environment
that works well with pysat. Core science packages such as numpy, scipy,
matplotlib, pandas and many others may also be installed directly via the
python package installer "pip" or your favorite package manager.

For maximum safety, you can install pysat into its own virtual environment.
This ensures there are no conflicts with any other installed Python
distributions.

To use Anaconda's tools for creating a suitable virtual environment,

.. code:: bash

    conda create -n virt_env_name python=3
    conda activate virt_env_name
    conda install numpy -c conda


Standard installation
---------------------

pysat itself may be installed from a terminal command line via::

   pip install pysat

There are a few packages that pysat depends on that will be installed as
needed by the installer

     * dask
     * netCDF4
     * numpy
     * pandas
     * portalocker
     * scipy
     * toolz
     * xarray


Development Installation
------------------------

pysat may also be installed directly from the source repository on github::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   python setup.py install --user

An advantage to installing through github is access to the development branches.
The latest bugfixes can be found in the ``develop`` branch. However, this
branch is not stable (as the name implies). We recommend using this branch in a
virtual environment and using::

   git clone https://github.com/pysat/pysat.git
   cd pysat
   git checkout develop
   python setup.py develop

The use of `develop` rather than `install` in the setup command installs the
code 'in-place', so any changes to the software do not have to be reinstalled
to take effect. It is not related to changing the pysat working branch from
``main`` to ``develop`` in the preceeding line.
