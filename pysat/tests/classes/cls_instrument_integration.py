"""Integration tests for pysat.Instrument.

Note
----
Base class stored here, but tests inherited by test_instrument.py

"""

import datetime as dt
import logging
import numpy as np
import os
import tempfile

import pandas as pds
import pytest
import xarray as xr

import pysat
from pysat.utils import testing


class InstIntegrationTests(object):
    """Integration tests for `pysat.Instrument`.

    Note
    ----
    Inherited by classes in test_instrument.py.  Setup and teardown methods are
    specified there.

    See Also
    --------
    `pysat.tests.test_instrument`

    """

    def test_no_stale_data_paths(self, caplog):
        """Ensure stale data paths aren't retained by pysat.Instrument.files."""

        inst_str = repr(self.testInst)
        inst_str = inst_str.replace('update_files=True', 'update_files=False')
        self.testInst = eval(inst_str)

        # There should still be a list of files
        assert len(self.testInst.files.files) > 0

        # Change pysat directory to temporary directory
        tempdir = tempfile.TemporaryDirectory()
        saved_dir = pysat.params['data_dirs']
        pysat.params['data_dirs'] = tempdir.name

        # Make another new instrument now that `data_dirs` changed. Normally,
        # pysat will use whatever directory was stored with the list of
        # files. However, since the data directory has changed, pysat should
        # notice the directory is stale and correct the situation.
        with caplog.at_level(logging.DEBUG, logger='pysat'):
            self.testInst = eval(inst_str)

        # Restore pysat directory before any further assertions
        pysat.params['data_dirs'] = saved_dir

        # Ensure debug message printed for observed change in data directories
        dstr = ' '.join(['`data_path` found',
                         'in stored file list is not in',
                         'current supported `self.data_paths`.',
                         'Ignoring stored path:'])
        assert caplog.text.find(dstr)

        # Confirm the right data_path is present. `data_paths` is longer
        # than tempdir.name by instrument specific directories.
        lim = len(os.path.normpath(tempdir.name))
        assert os.path.normpath(self.testInst.files.data_path)[:lim] \
               == os.path.normpath(tempdir.name)
        assert len(self.testInst.files.files) > 0

        return
