# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
import functools
import numpy as np
import os

import pandas as pds
import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

platform = 'pysat'
name = 'testmodel'

tags = {'': 'Regular testing data set'}
sat_ids = {'': ['']}
pandas_format = False
_test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    self.new_thing = True


def load(fnames, tag=None, sat_id=None):
    """ Loads the test files

    Parameters
    ----------
    fnames : list
        List of filenames
    tag : str or NoneType
        Instrument tag (accepts '')
    sat_id : str or NoneType
        Instrument satellite ID (accepts '' or a number (i.e., '10'), which
        specifies the number of data points to include in the test instrument)


    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Metadata

    """

    # create an artifical satellite data set
    uts, index, date = mm_test.generate_times(fnames, sat_id, freq='900S')

    # Define range of simulated 3D model
    latitude = np.linspace(-50, 50, 21)
    longitude = np.linspace(0, 360, 73)
    altitude = np.linspace(300, 500, 41)
    data = xr.Dataset({'uts': (('time'), uts)},
                      coords={'time': index, 'latitude': latitude,
                              'longitude': longitude, 'altitude': altitude})

    slt = np.zeros([len(uts), len(longitude)])
    for i, ut in enumerate(uts):
        for j, long in enumerate(longitude):
            slt[i, j] = np.mod(ut / 3600.0 + long / 15.0, 24.0)
    data['slt'] = (('time', 'longitude'), slt)
    data['mlt'] = (('time', 'longitude'), np.mod(slt+0.2, 24.0))

    # Fake 3D data consisting of values between 0 and 21 everywhere
    dummy1 = np.mod(data['uts'] * data['latitude'] * data['longitude'], 21.0)
    data['dummy1'] = (('time', 'latitude', 'longitude'), dummy1)

    # Fake 4D data consisting of between 0 and 21 everywhere
    dummy2 = np.mod(data['dummy1'] * data['altitude'], 21.0)
    data['dummy2'] = (('time', 'latitude', 'longitude', 'altitude'), dummy2)

    return data, meta.copy()


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
download = functools.partial(mm_test.download)

meta = pysat.Meta()
meta['uts'] = {'units': 's',
               'long_name': 'Universal Time',
               'custom': False}
meta['slt'] = {'units': 'hours',
               'long_name': 'Solar Local Time',
               'label': 'SLT',
               'axis': 'SLT',
               'desc': 'Solar Local Time',
               'value_min': 0.0,
               'value_max': 24.0,
               'notes': ('Solar Local Time is the local time (zenith '
                         'angle of sun) of the given locaiton. Overhead '
                         'noon, +/- 90 is 6, 18 SLT .'),
               'fill': np.nan,
               'scale': 'linear'}
meta['longitude'] = {'units': 'degrees', 'long_name': 'Longitude'}
meta['latitude'] = {'units': 'degrees', 'long_name': 'Latitude'}
meta['altitude'] = {'units': 'km', 'long_name': 'Altitude'}
meta['dummy1'] = {'units': '', 'long_name': 'dummy1'}
meta['dummy2'] = {'units': '', 'long_name': 'dummy2'}
