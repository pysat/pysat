#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import copy
import json
import os

from portalocker import Lock

import pysat.utils
from pysat.utils.files import check_and_make_path


class Parameters(object):
    """Stores user parameters used by pysat.

    Also stores custom user parameters provided the keys don't conflict with
    default pysat parameters.

    Parameters
    ----------
    path : str
        If provided, the directory path will be used to load/store a
        parameters file with name 'pysat_settings.json' (default=None)
    create_new : bool
        If True, a new parameters file is created. Will be created at path
        if provided. If not, file will be created in `.pysat` directory
        stored under the user's home directory.

    Attributes
    ----------
    data : dict
        pysat user settings dictionary
    defaults : dict
        Default parameters (keys) and values used by pysat that include
        {'clean_level': 'clean', 'directory_format':
        os.path.join('{platform}', '{name}', '{tag}', '{inst_id}'),
        'ignore_empty_files': False, 'update_files': True,
        'file_timeout': 10, 'user_modules' : {}, 'warn_empty_file_list': False}
    file_path : str
        Location of file used to store settings
    non_defaults : list
        List of pysat parameters (strings) that don't have a defined
        default and are unaffected by `self.restore_defaults()`
    Raises
    ------
    ValueError
        The 'user_modules' parameter may not be set directly by the
        user. Please use the `pysat.utils.regsitry` module to modify
        the packages stored in 'user_modules'.
    OSError
        User provided path does not exist

    Note
    ----
    This method will look for 'pysat_settings.json' file first in the
    current working directory and then in the home '~/.pysat' directory.

    All pysat parameters are automatically stored whenever a parameter is
    assigned or modified. The default parameters and values tracked by this
    class are grouped by type below.

    Values that map to the corresponding keywords on pysat.Instrument:
    clean_level, directory_format, ignore_empty_files, and update_files.  See
    the Instrument docstring for more information on these keywords.

    Values that map to internal pysat settings: file_timeout, user_modules, and
    warn_empty_file_list.

    Stored pysat parameters without a working default value: data_dirs.

    file_timeout -  Time in seconds that pysat will wait to modify a busy file

    user_modules - Stores information on modules registered by pysat

    warn_empty_file_list - Raise a warning when no Instrument files are found

    data_dirs - Directory(ies) where data are stored, in access order

    """

    def __init__(self, path=None, create_new=False):
        """Initialize Parameters object."""

        sfname = 'pysat_settings.json'
        self.data = {}
        self.file_path = None

        # Define default parameters and values
        dir_format = os.path.join('{platform}', '{name}', '{tag}', '{inst_id}')
        defaults = {'clean_level': 'clean',
                    'directory_format': dir_format,
                    'ignore_empty_files': False,
                    'file_timeout': 10,
                    'update_files': True,
                    'user_modules': {},
                    'warn_empty_file_list': False}

        # Attach default parameters and values to object
        self.defaults = defaults

        # Define stored pysat parameters without a default setting
        non_defaults = ['data_dirs']
        self.non_defaults = non_defaults

        # If path provided, use it. Otherwise, iterate through potential
        # locations until file is found.
        if path is not None:
            # Confirm path is valid
            if not os.path.exists(path):
                estr = ''.join(('Supplied path does not exist on the local ',
                                'system. Please create it and try again.'))
                raise OSError(estr)

            # Store full file path including fixed settings file name
            self.file_path = os.path.join(path, sfname)

        else:
            # Cycle through locations and load any pysat parameter files found.
            # First, check current working directory, then pysat user directory.
            # Stop looking once an existing file is found.
            file_locs = [os.path.join('.', sfname),
                         os.path.join(os.path.expanduser('~'), '.pysat',
                                      sfname)]
            for fileloc in file_locs:
                if os.path.isfile(fileloc):
                    self.file_path = fileloc
                    break

            # Ensure we have a valid file if the user isn't creating a new one
            if self.file_path is None and (not create_new):
                estr = ''.join(('pysat is unable to locate a user settings ',
                                'file. Please check the locations, "./" or ',
                                '"~/.pysat" for the file "pysat_settings.json"',
                                '.'))
                raise OSError(estr)

        if create_new:
            # Initialize new settings file. Method below includes a .store call
            self.clear_and_restart()

        # Load parameters in thread-safe manner.
        # Can't use user set file_timeout since we don't know what it is yet.
        # Can't use NetworkLock in pysat.utils either since this object (params)
        # doesn't exist yet.
        with Lock(self.file_path, 'r', timeout=10) as fout:
            self.data = json.load(fout)
            fout.flush()
            try:
                # In case of network file system
                os.fsync(fout.fileno())
            except OSError:
                # Not a network file system
                pass

        return

    def __repr__(self):
        """Describe the `Parameters` instantiation parameters.

        Returns
        -------
        out_str : str
            Simply formatted output string

        """
        dir_path = os.path.split(self.file_path)[0]
        out_str = ''.join(('pysat._params.Parameters(path=r"', dir_path, '")'))
        return out_str

    def __str__(self, long_str=True):
        """Describe the `Parameters` instance, variables, and attributes.

        Parameters
        ----------
        long_str : bool
            Return short version if False and long version if True
            (default=True)

        Returns
        -------
        out_str : str
            Nicely formatted output string

        """

        # Get typical pysat parameters (those with defaults)
        typical = list(self.defaults.keys())

        # Get pysat parameters without working defaults
        pparams = self.non_defaults

        # Get any additional parameters set by the user
        both = typical.copy()
        both.extend(pparams)
        users = [key for key in self.data.keys() if key not in both]

        # Print the short output
        out_str = "pysat Parameters object\n"
        out_str += "----------------------\n"
        out_str += "Tracking {:d} pysat settings\n".format(len(typical))
        out_str += "Tracking {:d} settings (non-default)\n".format(len(pparams))
        out_str += "Tracking {:d} user values\n".format(len(users))

        # Print the longer output
        if long_str:

            out_str += "\nStandard parameters:\n"
            for typ in typical:
                out_str += ''.join((typ, ' : ', self[typ].__str__(), '\n'))

            out_str += "\nStandard parameters (no defaults):\n"
            for typ in pparams:
                out_str += ''.join((typ, ' : ', self[typ].__str__(), '\n'))

            out_str += "\nUser parameters:\n"
            for typ in users:
                out_str += ''.join((typ, ' : ', self[typ].__str__(), '\n'))

        return out_str

    def __getitem__(self, item):
        """Get item from Parameters."""
        return self.data[item]

    def __setitem__(self, key, value):
        """Update current settings in Parameters."""

        # Some parameters require processing before storage
        if key == 'data_dirs':
            self._set_data_dirs(value)

        elif key == 'user_modules':
            estr = ''.join(('The pysat.utils.registry ',
                            'submodule has methods designed to build ',
                            'and work with this pysat attribute. ',
                            '`user_modules` is not modifiable here.'))
            raise ValueError(estr)
        else:
            # General or user parameter, no additional processing
            self.data[key] = value

        # Store updated parameters to disk
        self.store()

    def _set_data_dirs(self, path=None, store=True):
        """Set the top level directories pysat uses to store and load data.

        Parameters
        ----------
        path : string or list-like of str
            Valid path(s) to directory
        store : bool
            Optionally store parameters to disk. Present to support a
            Deprecated method. (default=True)

        """

        paths = pysat.utils.listify(path)

        # Account for a user prefix in the path, such as ~
        paths = [os.path.expanduser(pval) for pval in paths]

        # Account for the presence of $HOME or similar
        paths = [os.path.expandvars(pval) for pval in paths]

        # Make sure paths don't end with path separator for consistency
        paths = [pval if pval[-1] != os.path.sep else pval[:-1]
                 for pval in paths]

        # Ensure all paths are valid, create if not
        for pval in paths:
            check_and_make_path(pval)

        # Assign updated and validated paths
        self.data['data_dirs'] = paths

        # Optionally store information
        if store:
            self.store()

        return

    def clear_and_restart(self):
        """Clear all stored settings and sets pysat defaults.

        Note
        ----
        pysat parameters without a default value are set to []

        """

        # Clear current data and assign a copy of default values
        self.data = copy.deepcopy(self.defaults)

        # Set pysat parameters without a default working value to []
        for key in self.non_defaults:
            self.data[key] = []

        # Trigger a file write
        self.store()

        return

    def restore_defaults(self):
        """Restore default pysat parameters.

        Note
        ----
        Does not modify any stored custom user keys or pysat parameters
        without a default value.

        """

        # Set default values for each of the pysat provided values. Set
        # all but the last parameter directly. Set last using __setitem__
        # to trigger a file write.
        keys = list(self.defaults.keys())
        for key in keys:
            self.data[key] = self.defaults[key]

        # Trigger a file write
        self.store()

        return

    def store(self):
        """Store parameters using the filename specified in `self.file_path`."""

        # Store settings in file
        with Lock(self.file_path, 'w', self['file_timeout']) as fout:
            json.dump(self.data, fout)

            # Ensure write is fully complete even for network file systems
            fout.flush()
            try:
                # In case of network file system
                os.fsync(fout.fileno())
            except OSError:
                # Not a network file system
                pass

        return
