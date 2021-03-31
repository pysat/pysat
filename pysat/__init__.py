"""
pysat - Python Satellite Data Analysis Toolkit
==============================================

pysat is a package providing a simple and flexible interface for
downloading, loading, cleaning, managing, processing, and analyzing
scientific measurements. Although pysat was initially designed for
in situ satellite observations, it now supports many different types
of ground- and space-based measurements.

Main Features
-------------

- Instrument independent analysis routines.
- Instrument object providing an interface for downloading and analyzing
    a wide variety of science data sets.
    - Uses pandas or xarray for the underlying data structure; capable of
        handling the many forms scientific measurements take in a consistent
        manner.
    - Standard scientific data handling tasks (e.g., identifying, downloading,
        and loading files and cleaning and modifying data) are built into the
        Instrument object.
    - Supports metadata consistent with the netCDF CF-1.6 standard. Each
        variable has a name, long name, and units. Note units are informational
        only.
- Simplifies data management
    - Iterator support for loading data by day/file/orbit, independent of
        data storage details.
    - Orbits are calculated on the fly from loaded data and span day breaks.
    - Iterate over custom seasons
- Supports rigorous time-series calculations that require spin up/down
    time across day, orbit, and file breaks.
- Includes helper functions to reduce the barrier in adding new science
    instruments to pysat


"""

# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
import os

import logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

# set version
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'version.txt')) as version_file:
    __version__ = version_file.read().strip()


# get home directory
home_dir = os.path.expanduser('~')
# Set directory for test data
test_data_path = os.path.join(here, 'tests', 'test_data')
# set pysat directory path in home directory
pysat_dir = os.path.join(home_dir, '.pysat')
# make sure a pysat directory exists
if not os.path.isdir(pysat_dir):
    # create directory
    os.mkdir(pysat_dir)
    print('Created .pysat directory in user home directory to store settings.')
    # create file with default data directory
    if (os.environ.get('TRAVIS') == 'true'):
        _data_dir = '/home/travis/build/pysatData'
    else:
        _data_dir = ''
    with open(os.path.join(pysat_dir, 'data_path.txt'), 'w') as f:
        f.write(_data_dir)
    print(''.join(("\nHi there!  Please inform pysat where you will store "
                   "(or are storing) science data by "
                   "running pysat.utils.set_data_dir and specifying "
                   "a location.")))
else:
    # load up stored data path
    with open(os.path.join(pysat_dir, 'data_path.txt'), 'r') as f:
        _data_dir = f.readline()

import netCDF4
from pandas import Panel, DataFrame, Series, datetime
import sys
import warnings

from . import utils, model_utils

if sys.version_info[0] >= 3:
    from importlib import reload as re_load
else:
    re_load = reload


def pysat_reload():
    """Enable most of the underlying functionality of reload.

    Note
    -----
    To provide a deprecation notice for `pysat.data_dir` the pysat module
    needed to be wrapped within a class. This technique presents a challenge
    for reloading the pysat module since it is no longer a module. As reloading
    shouldn't generally be required by users, but `pysat.data_dir` is,
    we consider this acceptable.

    Examples
    --------
    import pysat

    # Enable reloading of pysat into current namespace
    pysat.pysat_reload()

    # Grab reloaded pysat reference
    pysat = sys.modules['pysat']

    """
    sys.modules['pysat'] = sys.modules['_pysat']
    re_load(sys.modules['pysat'])

    return


class Data_Dir_Wrapper(object):
    """Class wraps pysat module for DeprecationWarnings on `pysat.data_dir`.

    Technique for enabling DeprecationWarnings on data_dir comes from
        https://stackoverflow.com/questions/2447353/getattr-on-a-module/
        7668273#7668273

    """
    def __init__(self):
        sys.modules['pysat'].__init__('pysat')
        self.__class__ = sys.modules['pysat'].__class__
        return

    # def __class__(self):
    #     return sys.modules['_pysat'].__class__

    def __repr__(self):
        return sys.modules['_pysat'].__repr__()

    def __str__(self):
        return sys.modules['_pysat'].__str__()

    def __setattr__(self, key, value):
        """Replace standard __setattr__ to trap out `data_dir`"""
        # Update current settings
        # Some parameters require processing before storage.
        if key == 'data_dir':
            estr = ''.join(('Assignment via `pysat.data_dir = path` has been '
                            'deprecated in pysat 3.0.0 and replaced with ',
                            "`pysat.params['data_dirs'] = path`."))
            warnings.warn(estr, DeprecationWarning, stacklevel=2)
            utils._core._set_data_dir(value)
        else:
            # Assign value to self as standard
            self.__dict__[key] = value
        return

    def __getattr__(self, item):
        """Replace standard __getattr__ to trap out `data_dir`"""
        if item == 'data_dir':
            estr = ''.join(('`pysat.data_dir` has been deprecated in pysat ',
                            "3.0.0 and replaced with ",
                            "`pysat.params['data_dirs']`."))
            warnings.warn(estr, DeprecationWarning, stacklevel=2)
            return self._data_dir
        else:
            try:
                return self.__dict__[item]
            except KeyError:
                # Not in __dict__, go back to original pysat
                return getattr(sys.modules['_pysat'], item)

    __all__ = list(set(vars().keys()) - {'__module__', '__qualname__'})

# Instantiate wrapper class
_wrap = Data_Dir_Wrapper()

# Need to have something for data_dir so the imports below work first time.
# It also appears to work by wrapping the module here, rather than below,
# removing the need to artifically assign data dir below, however
# the wrapped module would need to be modified to include the from terms below.
data_dir = _data_dir

from ._constellation import Constellation
from ._instrument import Instrument
from ._meta import Meta
from ._files import Files
from ._custom import Custom
from ._orbits import Orbits
from ._params import Parameters
from . import instruments
from . import ssnl
from . import tests

# Add simplified Parameters class to support upcoming switch away from
# data_dir in favor of pysat.params['data_dirs']
params = Parameters()

__all__ = ['ssnl', 'instruments', 'utils']

# Make sure everything currently attached to pysat module is transferred
# over to this faux-class
exclude = ['_wrap', 'data_dir']
for key in sys.modules['pysat'].__dict__.copy():
    if key not in exclude:
        if key not in _wrap.__dict__:
            _wrap.__dict__[key] = sys.modules['pysat'].__dict__[key]

# Copy current pysat module to account for the things that aren't in
# __dict__, like apparently __repr__, __str__, and other functions.
_wrap.__repr__ = sys.modules['pysat'].__repr__
_wrap.__str__ = sys.modules['pysat'].__str__

sys.modules['_pysat'] = sys.modules['pysat']

# Replace the pysat entry with the instantiated class that provides the
# warnings on `data_dir` but otherwise replicates normal pysat
sys.modules['pysat'] = _wrap
