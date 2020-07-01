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
    data_dir = ''
    if (os.environ.get('TRAVIS') == 'true'):
        data_dir = '/home/travis/build/pysatData'
    with open(os.path.join(pysat_dir, 'data_path.txt'), 'w') as f:
        f.write(data_dir)
    print(''.join(("\nHi there!  Pysat will nominally store data in the "
                   "'pysatData' directory at the user's home directory level. "
                   "Run pysat.utils.set_data_dir to specify a different "
                   "top-level directory to store science data.")))
    # user modules file
    with open(os.path.join(pysat_dir, 'user_modules.txt'), 'w') as f:
        f.write('')
        user_modules = []

else:
    # load up stored data path
    with open(os.path.join(pysat_dir, 'data_path.txt'), 'r') as f:
        data_dir = f.readline()
    # load up stored user modules
    user_modules = []
    modules_file = os.path.join(pysat_dir, 'user_modules.txt')
    if os.path.exists(modules_file):
        with open(modules_file, 'r') as f:
            for _ in f:
                if _ != '' and (_ is not None):
                    user_modules.append(_.strip())
    else:
        # write user modules file
        with open(os.path.join(pysat_dir, 'user_modules.txt'), 'w') as f:
            f.write('')

from pysat import utils
from pysat._constellation import Constellation
from pysat._instrument import Instrument
from pysat._meta import Meta
from pysat.files import Files
from pysat._custom import Custom
from pysat._orbits import Orbits
from pysat import instruments

__all__ = ['instruments', 'utils']
