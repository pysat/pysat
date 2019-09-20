# -*- coding: utf-8 -*-
"""
Produces satellite orbit data. Orbit is simulated using
Two Line Elements (TLEs) and SGP4. Satellite position is coupled
to several space science models to simulate the atmosphere the
satellite is in.

"""

from __future__ import print_function
from __future__ import absolute_import

# basestring abstract type is removed in Python 3 and is replaced by str
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str
import os
import warnings

import pandas as pds
import numpy as np
import pysat

# pysat required parameters
platform = 'pysat'
name = 'sgp4'
# dictionary of data 'tags' and corresponding description
tags = {'': 'Satellite simulation data set'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'': ['']}
test_dates = {'': {'': pysat.datetime(2018, 1, 1)}}


def init(self):
    """
    Adds custom calculations to orbit simulation.
    This routine is run once, and only once, upon instantiation.

    Adds quasi-dipole coordiantes, velocity calculation in ECEF coords,
    adds the attitude vectors of spacecraft assuming x is ram pointing and
    z is generally nadir, adds ionospheric parameters from the Interational
    Reference Ionosphere (IRI), as well as simulated winds from the
    Horiontal Wind Model (HWM).

    """

    warnings.warn('pysat_sgp4 is deprecated here')


def load(fnames, tag=None, sat_id=None, obs_long=0., obs_lat=0., obs_alt=0.,
         TLE1=None, TLE2=None):
    """
    Returns data and metadata in the format required by pysat. Finds position
    of satellite in both ECI and ECEF co-ordinates.

    Routine is directly called by pysat and not the user.

    Parameters
    ----------
    fnames : list-like collection
        File name that contains date in its name.
    tag : string
        Identifies a particular subset of satellite data
    sat_id : string
        Satellite ID
    obs_long: float
        Longitude of the observer on the Earth's surface
    obs_lat: float
        Latitude of the observer on the Earth's surface
    obs_alt: float
        Altitude of the observer on the Earth's surface
    TLE1 : string
        First string for Two Line Element. Must be in TLE format
    TLE2 : string
        Second string for Two Line Element. Must be in TLE format

    Example
    -------
      inst = pysat.Instrument('pysat', 'sgp4',
              TLE1='1 25544U 98067A   18135.61844383  .00002728  00000-0  48567-4 0  9998',
              TLE2='2 25544  51.6402 181.0633 0004018  88.8954  22.2246 15.54059185113452')
      inst.load(2018, 1)

    """

    pass


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""

    index = pds.date_range(pysat.datetime(2017, 12, 1),
                           pysat.datetime(2018, 12, 1))
    # file list is effectively just the date in string format - '%D' works
    # only in Mac. '%x' workins in both Windows and Mac
    names = [data_path + date.strftime('%Y-%m-%d') + '.nofile'
             for date in index]
    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None, user=None,
             password=None):
    """ Data is simulated so no download routine is possible. Simple pass
    function"""
    pass
