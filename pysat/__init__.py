"""pysat - Python Satellite Data Analysis Toolkit.

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

try:
    from importlib import metadata
    from importlib import resources
except ImportError:
    import importlib_metadata as metadata
    resources = None

import logging
import os

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

# Import and set user and pysat parameters object
from pysat import _params

# Set version
__version__ = metadata.version('pysat')

# Get home directory
home_dir = os.path.expanduser('~')

# Set pysat directory path in home directory
pysat_dir = os.path.join(home_dir, '.pysat')

# Set directory for test data
if resources is None:
    test_data_path = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                                  'tests', 'test_data')
else:
    test_data_path = str(resources.files(__package__).joinpath('tests',
                                                               'test_data'))

# Create a .pysat directory or parameters file if one doesn't exist.
# pysat_settings did not exist pre v3 thus this provides a check against
# v2 users that are upgrading. Those users need the settings file plus
# new internal directories.
settings_file = os.path.join(pysat_dir, 'pysat_settings.json')
if not os.path.isdir(pysat_dir) or not os.path.isfile(settings_file):

    # Make a .pysat directory if not already present
    if not os.path.isdir(pysat_dir):
        os.mkdir(pysat_dir)
        ostr = ''.join(('Created .pysat directory in home directory to store ',
                        'settings.'))
        logger.info(ostr)

    # Make additional internal directories
    if not os.path.isdir(os.path.join(pysat_dir, 'instruments')):
        os.mkdir(os.path.join(pysat_dir, 'instruments'))

    if not os.path.isdir(os.path.join(pysat_dir, 'instruments', 'archive')):
        os.mkdir(os.path.join(pysat_dir, 'instruments', 'archive'))

    # Create parameters file
    if not os.path.isfile(settings_file):
        params = _params.Parameters(path=pysat_dir, create_new=True)

    print(''.join(("\nHi there!  pysat will nominally store data in a ",
                   "'pysatData' directory which needs to be assigned. ",
                   "Please run `pysat.params['data_dirs'] = path` where path ",
                   "specifies one or more existing top-level directories that ",
                   "may be used to store science data. `path` may either be ",
                   "a single string or a list of strings.")))
else:
    # Load up existing parameters file
    params = _params.Parameters()


from pysat._files import Files
from pysat._instrument import Instrument
from pysat._meta import Meta
from pysat._meta import MetaHeader
from pysat._meta import MetaLabels
from pysat._orbits import Orbits
from pysat import instruments
from pysat import utils

# Import constellation separately
from pysat._constellation import Constellation
__all__ = ['instruments', 'utils']

# Clean up
del settings_file, resources
