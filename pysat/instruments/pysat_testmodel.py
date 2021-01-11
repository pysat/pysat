# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""

import datetime as dt
import functools
import logging
import numpy as np
import warnings

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

logger = logging.getLogger(__name__)

platform = 'pysat'
name = 'testmodel'
tags = {'': 'Regular testing data set'}
inst_ids = {'': ['']}
pandas_format = False
_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    self.new_thing = True
    logger.info(mm_test.ackn_str)
    self.acknowledgements = mm_test.ackn_str
    self.references = mm_test.refs
    return


def clean(self):
    """Cleaning function
    """

    pass


def load(fnames, tag=None, inst_id=None, num_samples=None):
    """ Loads the test files

    Parameters
    ----------
    fnames : list
        List of filenames
    tag : str or NoneType
        Instrument tag (accepts '')
    inst_id : str or NoneType
        Instrument satellite ID (accepts '')
    num_samples : int
        Number of samples

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Metadata

    """

    if num_samples is None:
        if inst_id != '':
            estr = ' '.join(('inst_id will no longer be supported',
                             'for setting the number of samples per day.'))
            warnings.warn(estr, DeprecationWarning)
            num_samples = int(inst_id)
        else:
            num_samples = 96
    # create an artifical satellite data set
    uts, index, dates = mm_test.generate_times(fnames, num_samples,
                                               freq='900S')

    # Define range of simulated 3D model
    latitude = np.linspace(-50, 50, 21)
    longitude = np.linspace(0, 360, 73)
    altitude = np.linspace(300, 500, 41)
    data = xr.Dataset({'uts': (('time'), np.mod(uts, 86400.))},
                      coords={'time': index, 'latitude': latitude,
                              'longitude': longitude, 'altitude': altitude})

    slt = np.zeros([len(uts), len(longitude)])
    for i, ut in enumerate(uts):
        for j, long in enumerate(longitude):
            slt[i, j] = np.mod(ut / 3600.0 + long / 15.0, 24.0)
    data['slt'] = (('time', 'longitude'), slt)
    data['mlt'] = (('time', 'longitude'), np.mod(slt + 0.2, 24.0))

    # Fake 3D data consisting of values between 0 and 21 everywhere
    dummy1 = np.mod(data['uts'] * data['latitude'] * data['longitude'], 21.0)
    data['dummy1'] = (('time', 'latitude', 'longitude'), dummy1)

    # Fake 4D data consisting of between 0 and 21 everywhere
    dummy2 = np.mod(data['dummy1'] * data['altitude'], 21.0)
    data['dummy2'] = (('time', 'latitude', 'longitude', 'altitude'), dummy2)

    # Set the metadata
    meta = pysat.Meta()
    meta['uts'] = {'units': 's', 'long_name': 'Universal Time',
                   'custom': False}
    meta['slt'] = {'units': 'hours', 'long_name': 'Solar Local Time',
                   'desc': 'Solar Local Time', 'value_min': 0.0,
                   'value_max': 24.0,
                   'notes': ''.join(['Solar Local Time is the local time ',
                                     '(zenith angle of sun) of the given ',
                                     'locaiton. Overhead noon, +/- 90 is 6, ',
                                     '18 SLT .'])}
    meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
    meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
    meta['altitude'] = {'units': 'km', 'long_name': 'Altitude'}

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
