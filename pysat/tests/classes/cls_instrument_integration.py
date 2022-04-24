"""Tests for pysat.Instrument integration tests.

Includes:
* Ensuring no stale data paths after changing pysat.params['data_dirs']

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

logger = pysat.logger


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

    def test_a_no_stale_data_paths(self):
        """Ensure stale data paths are retained by pysat.Instrument.files."""

        inst_str = repr(self.testInst)
        inst_str = inst_str.replace('update_files=True', 'update_files=False')
        self.testInst = eval(inst_str)

        # There should still be a list of files
        assert len(self.testInst.files.files) > 0

        # Change pysat directory to something else
        tempdir = tempfile.TemporaryDirectory()

        saved_dir = pysat.params['data_dirs']
        pysat.params['data_dirs'] = tempdir.name

        # Make another new instrument now that `data_dirs` changed.
        self.testInst = eval(inst_str)

        # Restore pysat directory
        pysat.params['data_dirs'] = saved_dir

        # Confirm the right data_path is present. `data_paths` is longer
        # than tempdir.name by instrument specific directories.
        lim = len(os.path.normpath(tempdir.name))
        assert os.path.normpath(self.testInst.files.data_path)[:lim]\
               == os.path.normpath(tempdir.name)
        assert len(self.testInst.files.files) > 0

        return
