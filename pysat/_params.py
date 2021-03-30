#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import pysat


class Parameters(object):
    """Will Store user parameters used by pysat in v3.0.

    Current implementation supports the transition from `pysat.data_dir`
    to the `pysat.params['data_dirs'] = [path1, path2, ..., path_n]`
    or `pysat.params['data_dirs'] = path` format that will be used in
    pysat v3.0.

    Raises
    ------
    NotImplementedError
        Support is only provided for 'data_dirs'


    """

    def __init__(self):

        self.data = {}

        return

    def __repr__(self):
        """String describing Parameters instantiation parameters

        Returns
        -------
        out_str : str
            Simply formatted output string

        """
        out_str = 'pysat._params.Parameters()'
        return out_str

    def __str__(self):
        """String describing Parameters instance, variables, and attributes

        Returns
        -------
        out_str : str
            Nicely formatted output string

        """

        out_str = ''

        return out_str

    def __getitem__(self, item):
        if item == 'data_dirs':
            return [pysat.data_dir]
        else:
            estr = ''.join(('This class will be fully implemented in '
                            'pysat v3.0'))
            raise NotImplementedError(estr)

        return

    def __setitem__(self, key, value):
        # Update current settings
        # Some parameters require processing before storage.
        if key == 'data_dirs':
            pysat.utils._core._set_data_dir(value)
        else:
            estr = ''.join(('This class will be fully implemented in '
                            'pysat v3.0'))
            raise NotImplementedError(estr)
        return
