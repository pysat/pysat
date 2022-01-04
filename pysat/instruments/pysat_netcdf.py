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
import numpy as np
import warnings

import pysat

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
def list_files(tag='', inst_id='', data_path=None, format_str=None):
    """Produce a list of pysat-written NetCDF files.

    Parameters
    ----------
    tag : str
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    inst_id : str
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    data_path : str or NoneType
        Full path to directory containing files to be loaded. This
        is provided by pysat. The user may specify their own data path
        at Instrument instantiation and it will appear here. (default=None)
    format_str : str or NoneType
        String template used to parse the datasets filenames. If a user
        supplies a template string at Instrument instantiation
        then it will appear here, otherwise defaults to None. If None is
        supplied, expects files with the format 'platform_name_YYYY_MM_DD.nc'
        (default=None)

    Returns
    -------
    pandas.Series
        Series of filename strings, including the path, indexed by datetime.

    """

    if format_str is None:
        # User did not supply an alternative format template string
        format_str = '_'.join([platform, name, '{year:04d}', '{month:02d}',
                               '{day:02d}.nc'])

    # Use the pysat provided function to grab list of files from the
    # local file system that match the format defined above
    file_list = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    return file_list


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
         epoch_name='Epoch', epoch_unit='ms', epoch_origin='unix',
         pandas_format=True, decode_timedelta=False,
         labels={'units': ('units', str), 'name': ('long_name', str),
                 'notes': ('notes', str), 'desc': ('desc', str),
                 'plot': ('plot_label', str), 'axis': ('axis', str),
                 'scale': ('scale', str), 'min_val': ('value_min', np.float64),
                 'max_val': ('value_max', np.float64),
                 'fill_val': ('fill', np.float64)}):
    """Load pysat-created NetCDF data and meta data.

    Parameters
    ----------
    fnames : array-like
        iterable of filename strings, full path, to data files to be loaded.
        This input is nominally provided by pysat itself.
    tag : str
        tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. While
        tag defaults to None here, pysat provides '' as the default
        tag unless specified by user at Instrument instantiation. (default='')
    inst_id : str
        Satellite ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    strict_meta : bool
        Flag that checks if metadata across fnames is the same if True
        (default=False)
    file_format : str
        file_format keyword passed to netCDF4 routine.  Expects one of
        'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', or 'NETCDF4'.
        (default='NETCDF4')
    epoch_name : str
        Data key for epoch variable.  The epoch variable is expected to be an
        array of integer or float values denoting time elapsed from an origin
        specified by `epoch_origin` with units specified by `epoch_unit`. This
        epoch variable will be converted to a `DatetimeIndex` for consistency
        across pysat instruments.  (default='Epoch')
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
    labels : dict
        Dict where keys are the label attribute names and the values are tuples
        that have the label values and value types in that order.
        (default={'units': ('units', str), 'name': ('long_name', str),
        'notes': ('notes', str), 'desc': ('desc', str),
        'min_val': ('value_min', np.float64),
        'max_val': ('value_max', np.float64), 'fill_val': ('fill', np.float64)})

    Returns
    -------
    data : pds.DataFrame or xr.Dataset
        Data to be assigned to the pysat.Instrument.data object.
    mdata : pysat.Meta
        Pysat Meta data for each data variable.

    """

    # netCDF4 files, particularly those produced by pysat can be loaded using a
    # pysat provided function, load_netcdf4.
    data, mdata = pysat.utils.load_netcdf4(fnames, strict_meta=strict_meta,
                                           file_format=file_format,
                                           epoch_name=epoch_name,
                                           epoch_unit=epoch_unit,
                                           epoch_origin=epoch_origin,
                                           pandas_format=pandas_format,
                                           decode_timedelta=decode_timedelta,
                                           labels=labels)

    return data, mdata
