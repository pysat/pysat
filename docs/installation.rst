
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

For Windows systems, please see the ``Windows`` section below
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

Pysat itself may be installed from a terminal command line via::

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

----

To get pysat installed in Windows you need a POSIX compatible C/ Fortran
compiling environment. This is required to compile the
`pysatCDF <https://github.com/pysat/pysatCDF/>`_ package.

Python environment: Python 2.7.x

#. Install MSYS2 from `<http://repo.msys2.org>`_. The distrib folder contains
   msys2-x86_64-latest.exe (64-bit version) to install MSYS2.
#. Assuming you installed it in its default location ``C:\msys64``, launch
   MSYS2 environment from ``C:\msys64\msys2.exe``. This launches a shell session.
#. Now you need to make sure everything is up to date.  This terminal command
   will run updates::

    pacman -Syuu

#. After running this command, you will be asked to close the terminal window
   using close button and not exit() command. Go ahead and do that.
#. Relaunch and run::

    pacman -Syuu

   again.
#. After the second run, you should be up to date. If you run the update command
   again, you will be informed that there was nothing more to update. Now you
   need to install build tools and your compiler toolchains.::

    pacman -S base-devel git mingw-w64-x86_64-toolchain

   If it prompts you to make a selection and says (default:all), just press enter.  This install may take a bit.
#. Now you need to set up your MSYS2 environment to use whatever python interpreter you want to build pysatCDF for. In my case the path was ``C:\Python27_64``, but yours will be wherever python.exe exists.
#. Update MSYS2 path to include the folders with python binary and Scripts. To do that, navigate to your home directory in MSYS2. Mine is ``C:\msys64\home\gayui``.
#. Edit the .bash_profile file to add the below lines somewhere in the file.::

    # Add System python
    export PATH=$PATH:/c/Python27_64:/c/Python27_64/Scripts

   Note the unix-style paths. So ``C:`` becomes ``/c/``. If your python was in ``C:\foo\bar\python`` you would put ``/c/foo/bar/python`` and ``/c/foo/bar/python/Scripts``
#. Next step is to add the mingw64 bin folder to your windows system path. Right-click on computer, hit properties. Then click advanced system settings, then environment variables. Find the system variable (as opposed to user variables) named PATH. This is a semicolon delimited list of the OS search paths for binaries. Add another semicolon and the path ``C:\msys64\mingw64\bin``
#. Now you should have access to Python from within your MSYS2 environment. And your windows path should have access to the mingw binaries. To verify this, launch the mingw64 MSYS2 environment.::

    C:\msys64\mingw64.exe

   Run the command::

    which python

   and confirm that it points to the correct python version you want to be using.
#. Microsoft Visual C++ 9.0 is required to compile C sources. Download and
   install the right version of Microsoft Visual C++ for Python 2.7
   from `<http://aka.ms/vcpython27>`_
#. We are now getting close to installing pysatCDF. Do the following in the
   shell environment that is already opened.::

		mkdir src
		cd src
		git clone https://github.com/pysat/pysatCDF.git
		cd pysatCDF

#. Using a text editor of your choice, create a file called setup.cfg in::

		C:\msys64\home\gayui\src\pysatCDF


   Put the following in the file before saving and closing it.::

		[build]
		compiler=mingw32

   .. note::

       gayui will need to be replaced with your username

#. In your MSYS2 MINGW64 environment, run::

		python setup.py install

   This should compile and install the package to your site-packages for the python you are using.
#. You should now be able to import pysatCDF in your Python environment. If you get an ImportError, restart Python and import again.
