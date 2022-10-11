# -*- coding: utf-8 -*-
"""Produces fake instrument data for testing."""

import datetime as dt
import functools
import numpy as np

import xarray as xr

import pysat
from pysat.instruments.methods import testing as mm_test

platform = 'pysat'
name = 'testmodel'
tags = {'': 'Regular testing data set',
        'pressure_levels': ' '.join(('Testing data with pressure levels as the',
                                     'Z-coordinate instead of altitude.'))}
inst_ids = {'': [tag for tag in tags.keys()]}
pandas_format = False
_test_dates = {'': {tag: dt.datetime(2009, 1, 1) for tag in tags.keys()}}

# Init method
init = mm_test.init

# Clean method
clean = mm_test.clean

# Optional method, preprocess
preprocess = mm_test.preprocess


def load(fnames, tag='', inst_id='', start_time=None, num_samples=96,
         test_load_kwarg=None):
    """Load the test files.

    Parameters
    ----------
    fnames : list
        List of filenames.
    tag : str
        Tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    inst_id : str
        Instrument ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    start_time : dt.timedelta or NoneType
        Offset time of start time since midnight UT. If None, instrument data
        will begin at midnight. (default=None)
    num_samples : int
        Maximum number of times to generate.  Data points will not go beyond the
        current day. (default=96)
    test_load_kwarg : any
        Keyword used for pysat unit testing to ensure that functionality for
        custom keywords defined in instrument support functions is working
        correctly. (default=None)

    Returns
    -------
    data : xr.Dataset
        Testing data
    meta : pysat.Meta
        Metadata

    """

    # Support keyword testing
    pysat.logger.info(''.join(('test_load_kwarg = ', str(test_load_kwarg))))

    # Create an artificial model data set
    freq_str = '900S' if tag == '' else '1H'
    uts, index, dates = mm_test.generate_times(fnames, num_samples,
                                               freq=freq_str,
                                               start_time=start_time)
    epoch_name = 'time'

    # Define range of simulated model as well as data, depending upon tag.
    if tag == '':
        latitude = np.linspace(-50, 50, 21)
        longitude = np.linspace(0, 360, 72, endpoint=False)
        altitude = np.linspace(300, 500, 41)
        data = xr.Dataset({'uts': (('time'), np.mod(uts, 86400.))},
                          coords={epoch_name: index, 'latitude': latitude,
                                  'longitude': longitude, 'altitude': altitude})

    else:
        latitude = np.linspace(-88.75, 88.75, 72)
        longitude = np.linspace(-180., 177.5, 144)
        lev = np.linspace(-7, 7, 57)
        ilev = np.linspace(-6.875, 7.125, 57)

        data = xr.Dataset({'uts': ((epoch_name), np.mod(uts, 86400.))},
                          coords={epoch_name: index, 'latitude': latitude,
                                  'longitude': longitude, 'lev': lev,
                                  'ilev': ilev})

        # Simulate altitude values at the model nodes.
        # Start by initializing the memory.
        dummy0 = (data['uts'] * data['ilev'] * data['latitude']
                  * data['longitude'])
        dummy0 *= 0

        # Provide a 2D linear gradient across latitude and longitude
        inc_arr = (np.linspace(0, 1, 72)[:, np.newaxis]
                   * np.linspace(0, 1, 144)[np.newaxis, :])

        # Calculate and assign altitude values
        for i in np.arange(len(data['ilev'])):
            for j in np.arange(len(data['uts'])):
                dummy0[j, i, :, :] = i * 10. + j + inc_arr
        dummy0.data *= 100000.
        data['altitude'] = ((epoch_name, 'ilev', 'latitude', 'longitude'),
                            dummy0.data)

        # Create fake 4D ion drift data set
        dummy0 = (data['uts'] * data['ilev'] * data['latitude']
                  * data['longitude'])
        dummy0 *= 0

        # Calculate and assign fake data values
        for i in np.arange(len(data['ilev'])):
            for j in np.arange(len(data['uts'])):
                dummy0[j, i, :, :] = 2. * i * (np.sin(2 * np.pi * j / 24.)
                                               + inc_arr)
        data['dummy_drifts'] = ((epoch_name, 'ilev', 'latitude', 'longitude'),
                                dummy0.data)

    slt = np.zeros([len(uts), len(longitude)])
    for i, ut in enumerate(uts):
        for j, long in enumerate(longitude):
            slt[i, j] = np.mod(ut / 3600.0 + long / 15.0, 24.0)
    data['slt'] = ((epoch_name, 'longitude'), slt)
    data['mlt'] = ((epoch_name, 'longitude'), np.mod(slt + 0.2, 24.0))

    # Fake 3D data consisting of non-physical values between 0 and 21 everywhere
    # Used for interpolation routines in pysatModels.
    dummy1 = np.mod(data['uts'] * data['latitude'] * data['longitude'], 21.0)
    data['dummy1'] = ((epoch_name, 'latitude', 'longitude'), dummy1.data)
    data['string_dummy'] = ((epoch_name),
                            ['test'] * len(data.indexes[epoch_name]))
    data['unicode_dummy'] = ((epoch_name),
                             [u'test'] * len(data.indexes[epoch_name]))
    data['int8_dummy'] = ((epoch_name),
                          np.ones(len(data.indexes[epoch_name]), dtype=np.int8))
    data['int16_dummy'] = ((epoch_name),
                           np.ones(len(data.indexes[epoch_name]),
                                   dtype=np.int16))
    data['int32_dummy'] = ((epoch_name),
                           np.ones(len(data.indexes[epoch_name]),
                                   dtype=np.int32))
    data['int64_dummy'] = ((epoch_name),
                           np.ones(len(data.indexes[epoch_name]),
                                   dtype=np.int64))

    if tag == '':
        # Fake 4D data consisting of non-physical values between 0 and 21
        # everywhere. Used for interpolation routines in pysatModels.
        dummy2 = np.mod(data['dummy1'] * data['altitude'], 21.0)
        data['dummy2'] = ((epoch_name, 'latitude', 'longitude', 'altitude'),
                          dummy2.data)

    # Set the meta data
    meta = mm_test.initialize_test_meta(epoch_name, data.keys())

    # Adjust metadata from overall defaults
    meta['dummy1'] = {'value_min': -2**32 + 2, 'value_max': 2**32 - 1,
                      'fill': -2**32 + 1}
    meta['dummy2'] = {'value_min': -2**32 + 2, 'value_max': 2**32 - 1,
                      'fill': -2**32 + 1}

    if tag == 'pressure_levels':
        # Assigning new metadata for altitude since it differs from default info
        meta['altitude'] = {meta.labels.units: 'cm',
                            meta.labels.name: 'altitude',
                            meta.labels.min_val: 0.,
                            meta.labels.max_val: 1E8,
                            meta.labels.desc: ' '.join(('Altitude (fake) for',
                                                        'each pressure level')),
                            meta.labels.notes: '',
                            meta.labels.fill_val: np.nan}

        # Assigning metadata for meridional ion drifts since it differs from
        # default info.
        meta['iv_mer'] = {meta.labels.units: 'm/s',
                          meta.labels.name: 'Meridional Ion Drift',
                          meta.labels.min_val: -250.,
                          meta.labels.max_val: 250.,
                          meta.labels.desc: ' '.join(('Non-physical meridional',
                                                      'ion drifts.')),
                          meta.labels.notes: '',
                          meta.labels.fill_val: np.nan}

        # Assign metadata for the new coordinate axis here, `lev` and `ilev`.
        meta['lev'] = {meta.labels.units: '',
                       meta.labels.name: 'Pressure Level (midpoint)',
                       meta.labels.min_val: -6.875,
                       meta.labels.max_val: 7.125,
                       meta.labels.desc: ' '.join(('Log of atmospheric',
                                                   'pressure level.')),
                       meta.labels.notes: 'p(lev) = p0 * exp(-lev)',
                       meta.labels.fill_val: np.nan}

        meta['ilev'] = {meta.labels.units: '',
                        meta.labels.name: 'Pressure Level Interface',
                        meta.labels.min_val: -6.875,
                        meta.labels.max_val: 7.125,
                        meta.labels.desc: ' '.join(('Log of atmospheric',
                                                    'pressure level.')),
                        meta.labels.notes: 'p(ilev) = p0 * exp(-ilev)',
                        meta.labels.fill_val: np.nan}

    return data, meta


list_files = functools.partial(mm_test.list_files, test_dates=_test_dates)
list_remote_files = functools.partial(mm_test.list_remote_files,
                                      test_dates=_test_dates)
download = functools.partial(mm_test.download)
