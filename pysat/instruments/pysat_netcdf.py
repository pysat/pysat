#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""General Instrument for loading pysat-written netCDF files.

Properties
----------
platform
    'pysat', will be updated if file contains a platform attribute
name
    'netcdf', will be updated if file contains a name attribute
tag
   '', will be updated if file contains a tag attribute
inst_id
   '', will be updated if file contains an inst_id attribute

Note
----
Only tested against pysat created netCDF files

Examples
--------
::

    import pysat

    # Load a test Instrument
    inst = pysat.Instrument("pysat", "testing")
    inst.load(date=inst.inst_module._test_dates[''][''])

    # Create a NetCDF file
    fname = "test_pysat_file_%Y%j.nc"
    inst.to_netcdf4(fname=inst.date.strftime(fname))

    # Load the NetCDF file
    file_inst = pysat.Instrument(
        "pysat", "netcdf", temporary_file_list=True, directory_format="./",
        file_format="test_pysat_file_{year:04}{day:03}.nc")
    file_inst.load(date=inst.inst_module._test_dates[''][''])

"""

import datetime as dt
import functools
import numpy as np
import warnings

import pysat
from pysat.instruments.methods import general

logger = pysat.logger

# ----------------------------------------------------------------------------
# Instrument attributes
platform = 'pysat'
name = 'netcdf'
tags = {'': ''}
inst_ids = {'': tag for tag in tags.keys()}

# ----------------------------------------------------------------------------
# Instrument testing attributes

_test_dates = {'': {'': dt.datetime(2009, 1, 1)}}
_test_download = {'': {'': False}}
_test_download_ci = {'': {'': False}}


# ----------------------------------------------------------------------------
# Instrument methods
def init(self, pandas_format=True):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = "Acknowledgements missing from file"
    self.references = "References missing from file"
    self.pandas_format = pandas_format

    return


def clean(self):
    """Clean the file data."""
    return


def preprocess(self):
    """Extract Instrument attrs from file attrs loaded to `Meta.header`."""

    if hasattr(self.meta, "header"):
        for iattr in ['platform', 'name', 'tag', 'inst_id', 'acknowledgements',
                      'references']:
            if hasattr(self.meta.header, iattr):
                setattr(self, iattr, getattr(self.meta.header, iattr))

    return


# ----------------------------------------------------------------------------
# Instrument functions
format_str = '_'.join([platform, name, '{year:04d}', '{month:02d}',
                       '{day:02d}.nc'])
supported_tags = {inst_id: {tag: format_str for tag in tags.keys()}
                  for inst_id in inst_ids.keys()}
list_files = functools.partial(general.list_files, format_str=format_str,
                               supported_tags=supported_tags)


def download(date_array, tag, inst_id, data_path=None):
    """Download data from the remote repository; not supported.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : str
        Tag identifier used for particular dataset. This input is provided by
        pysat. (default='')
    inst_id : str
        Satellite ID string identifier used for particular dataset. This input
        is provided by pysat. (default='')
    data_path : str or NoneType
        Path to directory to download data to. (default=None)

    """

    warnings.warn("".join(["Downloads are not currently supported for ",
                           "pysat netCDF files"]))
    return


def load(fnames, tag='', inst_id='', strict_meta=False, file_format='NETCDF4',
         epoch_name=None, epoch_unit='ms', epoch_origin='unix',
         pandas_format=True, decode_timedelta=False,
         load_labels={'units': ('units', str), 'name': ('long_name', str),
                      'notes': ('notes', str), 'desc': ('desc', str),
                      'plot': ('plot_label', str), 'axis': ('axis', str),
                      'scale': ('scale', str),
                      'min_val': ('value_min', np.float64),
                      'max_val': ('value_max', np.float64),
                      'fill_val': ('fill', np.float64)},
         meta_processor=None,
         meta_translation=None, drop_meta_labels=None, decode_times=None):
    """Load pysat-created NetCDF data and meta data.

    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : str
        Tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    inst_id : str
        Instrument ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    strict_meta : bool
        Flag that checks if metadata across fnames is the same if True
        (default=False)
    file_format : str
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        (default='NETCDF4')
    epoch_name : str or NoneType
        Data key for epoch variable.  The epoch variable is expected to be an
        array of integer or float values denoting time elapsed from an origin
        specified by `epoch_origin` with units specified by `epoch_unit`. This
        epoch variable will be converted to a `DatetimeIndex` for consistency
        across pysat instruments.  (default=None)
    epoch_unit : str
        The pandas-defined unit of the epoch variable ('D', 's', 'ms', 'us',
        'ns'). (default='ms')
    epoch_origin : str or timestamp-convertable
        Origin of epoch calculation, following convention for
        `pandas.to_datetime`.  Accepts timestamp-convertable objects, as well as
        two specific strings for commonly used calendars.  These conversions are
        handled by `pandas.to_datetime`.
        If ‘unix’ (or POSIX) time; origin is set to 1970-01-01.
        If ‘julian’, `epoch_unit` must be ‘D’, and origin is set to beginning of
        Julian Calendar. Julian day number 0 is assigned to the day starting at
        noon on January 1, 4713 BC. (default='unix')
    pandas_format : bool
        Flag specifying if data is stored in a pandas DataFrame (True) or
        xarray Dataset (False). (default=False)
    decode_timedelta : bool
        Used for xarray data (`pandas_format` is False).  If True, variables
        with unit attributes that  are 'timelike' ('hours', 'minutes', etc) are
        converted to `np.timedelta64`. (default=False)
    load_labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})
    meta_processor : function or NoneType
        If not None, a dict containing all of the loaded metadata will be
        passed to `meta_processor` which should return a filtered version
        of the input dict. The returned dict is loaded into a pysat.Meta
        instance and returned as `meta`. (default=None)
    meta_translation : dict or NoneType
        Translation table used to map metadata labels in the file to
        those used by the returned `meta`. Keys are labels from file
        and values are labels in `meta`. Redundant file labels may be
        mapped to a single pysat label. If None, will use
        `default_from_netcdf_translation_table`. This feature
        is maintained for file compatibility. To disable all translation,
        input an empty dict. (default=None)
    drop_meta_labels : list or NoneType
        List of variable metadata labels that should be dropped. Applied
        to metadata as loaded from the file. (default=None)
    decode_times : bool or NoneType
        If True, variables with unit attributes that are 'timelike' ('hours',
        'minutes', etc) are converted to `np.timedelta64` by xarray. If False,
        then `epoch_name` will be converted to datetime using `epoch_unit`
        and `epoch_origin`. If None, will be set to False for backwards
        compatibility. For xarray only. (default=None)

    Returns
    -------
    data : pds.DataFrame or xr.Dataset
        Data to be assigned to the pysat.Instrument.data object.
    mdata : pysat.Meta
        Pysat Meta data for each data variable.

    """
    # netCDF4 files, particularly those produced by pysat can be loaded using a
    # pysat provided function, load_netcdf4.
    data, mdata = pysat.utils.io.load_netcdf(fnames, strict_meta=strict_meta,
                                             file_format=file_format,
                                             epoch_name=epoch_name,
                                             epoch_unit=epoch_unit,
                                             epoch_origin=epoch_origin,
                                             pandas_format=pandas_format,
                                             decode_timedelta=decode_timedelta,
                                             labels=load_labels,
                                             meta_processor=meta_processor,
                                             meta_translation=meta_translation,
                                             drop_meta_labels=drop_meta_labels,
                                             decode_times=decode_times)

    return data, mdata
