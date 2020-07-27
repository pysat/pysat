"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup
# To use a consistent encoding
import codecs
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, 'description.txt'), encoding='utf-8') as f:
    long_description = f.read()
version_filename = os.path.join('pysat', 'version.txt')
with codecs.open(os.path.join(here, version_filename)) as version_file:
    version = version_file.read().strip()

# packages to be installed
# starting with packages common across all setups
install_requires = ['requests', 'beautifulsoup4', 'lxml', 'netCDF4']
# packages with Fortran code
fortran_install = ['pysatCDF', 'madrigalWeb', 'h5py', 'PyForecastTools']
# python version specific support libraries
if sys.version_info.major == 2:
    install_requires.extend(['xarray<0.12', 'pandas>=0.23, <0.25',
                             'numpy>=1.12, <1.17', 'scipy<1.3',
                             'matplotlib<3.0'])
else:
    # python 3+
    install_requires.extend(['xarray<0.15', 'pandas>=0.23, <0.25',
                             'numpy>=1.12', 'scipy', 'matplotlib'])

# flag, True if on readthedocs
on_rtd = os.environ.get('READTHEDOCS') == 'True'

# include Fortran for normal install
# read the docs doesn't do Fortran
if not on_rtd:
    # not on ReadTheDocs, add Fortran
    install_requires.extend(fortran_install)

setup(
    name='pysat',
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    description='Supports science data analysis across measurement platforms',
    long_description=long_description,
    # The project's main homepage.
    url='http://github.com/pysat/pysat',

    # Author details
    author='Russell Stoneback',
    author_email='rstoneba@utdallas.edu',


    package_data={'pysat': ['pysat/version*.txt']},
    include_package_data=True,

    # Choose your license
    license='BSD',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Atmospheric Science',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # What does your project relate to?
    # keywords='sample setuptools development',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['pysat', 'pysat.instruments', 'pysat.ssnl'],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=install_requires,
)
