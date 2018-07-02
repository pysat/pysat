"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
from setuptools import setup
# To use a consistent encoding
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))

version_filename = os.path.join('pysat', 'version.txt')
with open(os.path.join(here, version_filename)) as version_file:
    version = version_file.read().strip()

setup(
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,
    
    # The project's main homepage.
    url='http://github.com/rstoneback/pysat',

    package_data = {'pysat': ['pysat/version*.txt']},

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['pysat', 'pysat.instruments', 'pysat.ssnl'],
)
