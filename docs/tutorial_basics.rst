Basics
======

The core functionality of pysat is exposed through the pysat.Instrument object.
The intent of the Instrument object is to offer a single interface for
interacting with science data that is independent of measurement platform.
The layer of abstraction presented by the Instrument object allows for things
to occur in the background that can make science data analysis simpler and more
rigorous.

To begin,

.. code:: python

   import pysat

The data directory pysat looks in for data (pysat_data_dir) needs to be set
upon the first import,

.. code:: python

   pysat.utils.set_data_dir(path=path_to_existing_directory)

.. note:: A data directory must be set before any pysat.Instruments may be used
   or an error will be raised.

Basic Instrument Discovery
--------------------------

Support for each instrument in pysat is enabled by a suite of methods that
interact with the particular files for that dataset and supply the data within
in a pysat compatible format. A particular data set is identified using
up to four parameters

===============     ===================================
**Identifier** 	        **Description**
---------------     -----------------------------------
  platform		    General platform instrument is on
  name		        Name of the instrument
  tag		        Label for a subset of total data
  inst_id		    Label for instrument sub-group
===============     ===================================


All supported pysat Instruments for v2.x are stored in the pysat.instruments
submodule. A listing of all currently supported instruments
is available via help,

.. code:: python

    help(pysat.instruments)

Each instrument listed will support one or more data sets for analysis. The
submodules are named with the convention platform_name. To get
a description of an instrument from a pysat package, you can use a searching
function.  This example uses the ``pysatMadrigal`` package.

.. code:: python

   import pysatMadrigal as pysatMad
   mad_inst = pysat.utils.generate_instrument_list(pysatMad.instruments)
   print(mad_inst['names'])


Further, the dictionary::

    pysatMadrigal.instruments.dmsp_ivm.tags

is keyed by ``tag`` with a description of each type of data
the ``tag`` parameter selects. The dictionary::

    pysatMadrigal.instruments.dmsp_ivm.inst_ids

indicates which instrument or satellite ids (``inst_id``) support which tag.
The combination of ``tag`` and ``inst_id`` select the particular dataset
a pysat.Instrument object will provide and interact with.


Instantiation
-------------

To create a pysat.Instrument object, select a ``platform`` and instrument
``name`` or an ``inst_module`` along side (potentially) a ``tag`` and
``inst_id``, consistent with the desired data from a supported instrument.

To work with plasma velocity data from the Ion Velocity Meter (IVM) onboard the
Defense Meteorological Satellite Program (DMSP) constellation (specifically, the
F12 spacecraft), use:

.. code:: python

   import pysatMadrigal as pysatMad
   dmsp = pysat.Instrument(inst_module=pysatMad.instruments.dmsp_ivm, tag='utd', inst_id='f12')

Behind the scenes pysat uses a python module named dmsp_ivm that understands
how to interact with 'utd' data for 'f12'.

If you have previously registered the instruments in ``pysatMadrigal``, you
can specify the desired Instrument using the ``platform`` and ``name`` keywords.

.. code:: python

   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd', inst_id='f12')

You can also specify the specific keyword arguements needed for the standard
``pysat`` methods.  DMSP data is hosted by the `Madrigal database
<http://cedar.openmadrigal.org/openmadrigal/>`_, a community resource for
geospace data. The proper process for downloading DMSP and other Madrigal data
is built into the open source
tool `madrigalWeb <http://cedar.openmadrigal.org/docs/name/rr_python.html>`_,
which is invoked appropriately by ``pysat`` within the
``pysatMadrigal.instruments.dmsp_ivm`` sub-module. Madrigal requires that users
provide their name and email address as their username and password.

.. code:: python

   # set user and password for Madrigal
   username = 'Firstname+Lastname'
   password = 'email@address.com'

   # Initalize the instrument, passing the username and password to the
   # standard routines that need it
   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd', inst_id='f12', user=username, password=password)

Download
--------

Let's download some data. To get DMSP data specifically all we have to do is
invoke the ``.download()`` method attached to the DMSP object. If the username
and password have't been provided to the instrument already, be sure to
include them here.

.. code:: python


   import datetime as dt

   # define date range to download data
   start = dt.datetime(2001, 1, 1)
   stop = dt.datetime(2001, 1, 2)

   # download data, assuming username and password were not set
   dmsp.download(start, stop, user=username, password=password)

The data is downloaded to pysat_data_dir/platform/name/tag/, in this case
pysat_data_dir/dmsp/ivm/utd/. At the end of the download, pysat
will update the list of files associated with DMSP.

Some instruments support an improved download experience that ensures
the local system is fully up to date compared to the data source. The command,

.. code:: python

    dmsp.download_updated_files()

will obtain the full set of files present on the server and compare the
version and revision numbers for the server files with those on the local
system.  Any files missing or out of date on the local system are downloaded
from the server. This command downloads, as needed, the entire dataset.

.. note:: Science data servers may not have the same reliability and
   bandwidth as commercial providers

Load Data
---------

Data is loaded into a pysat.Instrument object, in this case dmsp, using the
``.load`` method using year, day of year; date; or filename.

.. code:: python

   # load by year, day of year
   dmsp.load(2001, 1)
   # load by datetime
   dmsp.load(date=dt.datetime(2001, 1, 1))
   # load by filename
   dmsp.load(fname='dms_ut_20010101_12.002.hdf5')
   # load by filename
   dmsp.load(fname=dmsp.files[0])
   # load by filename
   dmsp.load(fname=dmsp.files[dt.datetime(2001, 1, 1)])

When the pysat load routine runs it stores the instrument data into dmsp.data.
pysat supports the use of two different data structures,
either a pandas DataFrame_, a highly capable structure with
labeled rows and columns, or an xarray DataSet_ for data sets with
more dimensions. Either way, the full data structure is available at::

   # all data
   dmsp.data

providing full access to the underlying data library functionality. The
type of data structure is flagged at the instrument level with the attribute
``inst.pandas_format``, True if a DataFrame is returned by the corresponding
instrument module load method.

pysat also supports loading data from a range of files/file dates. Keywords
in pysat with `end_*` are an exclusive bound, similar to slicing numpy arrays,
while those with `stop_*` are an inclusive bound.

Loading data by year and day of year.

.. code:: python

   # load by year, day of year from 2001, 1 up to but not including 2001, 3
   dmsp.load(2001, 1, end_yr=2001, end_doy=3)

   # the following two load commands are equivalent
   dmsp.load(2001, 1, end_yr=2001, end_doy2=2)
   dmsp.load(2001, 1)

Loading data using datetimes.

.. code:: python

   # load by datetimes
   dmsp.load(date=dt.datetime(2001, 1, 1),
             end_date=dt.datetime(2001, 1, 3))

   # the following two load commands are equivalent
   dmsp.load(date=dt.datetime(2001, 1, 1),
             end_date=dt.datetime(2001, 1, 2))
   dmsp.load(date=dt.datetime(2001, 1, 1))

Loading data using filenames.

.. code:: python

   # load a single file
   dmsp.load(fname='dms_ut_20010101_12.002.hdf5')

   # load by filename, from fname up to and including stop_fname
   dmsp.load(fname='dms_ut_20010101_12.002.hdf5',
             stop_fname='dms_ut_20010102_12.002.hdf5')

   # load by filenames using the DMSP object to get valid filenames
   dmsp.load(fname=dmsp.files[0], stop_fname=dmsp.files[1])

   # load by filenames. Includes data from 2001, 1 up to but not
   # including 2001, 3
   dmsp.load(fname=dmsp.files[dt.datetime(2001, 1, 1)],
             stop_fname=dmsp.files[dt.datetime(2001, 1, 2)])

For small size data sets, such as space weather indices, pysat also supports
loading all data at once.

.. code:: python

   # F10.7 data
   import pysatSpaceWeather
   f107 = pysat.Instrument(inst_module=pysatSpaceWeather.instruments.sw_f107)
   # Load all F10.7 solar flux data, from beginning to end.
   f107.load()

In addition, convenience access to the data is also available at
the instrument level.

.. _DataFrame: http://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe

.. _DataSet: http://xarray.pydata.org/en/v0.11.3/generated/xarray.Dataset.html

.. code:: python

    # Convenience access
    dmsp['ti']
    # slicing
    dmsp[0:10, 'ti']
    # slicing by date time
    dmsp[start:stop, 'ti']

    # Convenience assignment
    dmsp['ti'] = new_array
    # exploit broadcasting, single value assigned to all times
    dmsp['ti'] = single_value
    # slicing
    dmsp[0:10, 'ti'] = sub_array
    # slicing by date time
    dmsp[start:stop, 'ti'] = sub_array

See :any:`Instrument` for more.

To load data over a season, pysat provides a convenience function that returns
an array of dates over a specfied period of time. This time period does not
need to be continuous (e.g., load both the vernal and autumnal equinoxes).

.. code:: python

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pds

    # create empty series to hold result
    mean_ti = pds.Series()

    # get list of dates between start and stop
    start = dt.datetime(2001, 1, 1)
    stop = dt.datetime(2001, 1, 10)
    date_array = pysat.utils.time.create_date_range(start, stop)

    # iterate over season, calculate the mean Ion Temperature
    for date in date_array:
       # load data into dmsp.data
       dmsp.load(date=date)
       # check if data present
       if not dmsp.empty:
           # isolate data to locations near geomagnetic equator
           idx, = np.where((dmsp['mlat'] < 5) & (dmsp['mlat'] > -5))
           # downselect data
           dmsp.data = dmsp[idx]
           # compute mean ion temperature using pandas functions and store
           mean_ti[dmsp.date] = dmsp['ti'].abs().mean(skipna=True)

    # plot the result using pandas functionality
    mean_ti.plot(title='Mean Ion Temperature near Magnetic Equator')
    plt.ylabel(dmsp.meta['ti', dmsp.meta.name_label] + ' (' +
               dmsp.meta['ti', dmsp.meta.units_label] + ')')

Note, the numpy.where may be removed using the convenience access to the
attached pandas data object.

.. code:: python

   idx, = np.where((dmsp['mlat'] < 5) & (dmsp['mlat'] > -5))
   dmsp.data = dmsp[idx] = dmsp.data.iloc[idx

is equivalent to

.. code:: python

   dmsp.data = vefi[(dmsp['mlat'] < 5) & (dmsp['mlat'] > -5)]


Clean Data
----------

Before data is available in .data it passes through an instrument specific
cleaning routine. The amount of cleaning is set by the clean_level keyword,
provided at instantiation. The level defaults to 'clean'.

.. code:: python

   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd', inst_id='f12',
                           clean_level=None)
   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd', inst_id='f12',
                           clean_level='clean')

Four levels of cleaning may be specified,

===============     ===================================
**clean_level** 	        **Result**
---------------     -----------------------------------
  clean		        Generally good data
  dusty		        Light cleaning, use with care
  dirty		        Minimal cleaning, use with caution
  none		        No cleaning, use at your own risk
===============     ===================================

The user provided cleaning level is stored on the Instrument object at
``dmsp.clean_level``. The details of the cleaning will generally vary greatly
between instruments.

Metadata
--------

Metadata is also stored along with the main science data. pysat presumes
a minimum default set of metadata that may be arbitrarily expanded.
The default parameters are driven by the attributes required by public science
data files, like those produced by the Ionospheric Connections Explorer
`(ICON) <http://icon.ssl.berkeley.edu>`_.

===============     ===================================
**Metadata** 	        **Description**
---------------     -----------------------------------
  axis              Label for plot axes
  desc              Description of variable
  fill              Fill value for bad data points
  label             Label used for plots
  name              Name of variable, or long_name
  notes             Notes about variable
  max               Maximum valid value
  min               Minimum valid value
  scale             Axis scale, linear or log
  units             Variable units
===============     ===================================

.. code:: python

   # all metadata
   dmsp.meta.data
   # variable metadata
   dmsp.meta['ti']
   # units using standard labels
   dmsp.meta['ti'].units
   # units using general labels
   dmsp.meta['ti', dmsp.units_label]
   # update units for ti
   dmsp.meta['ti'] = {'units':'new_units'}
   # update display name, long_name
   dmsp.meta['ti'] = {'long_name':'Fancy Name'}
   # add new meta data
   dmsp.meta['new'] = {dmsp.units_label:'fake',
                       dmsp.name_label:'Display'}

The string values used within metadata to identify the parameters above
are all attached to the instrument object as dmsp.*_label, or
``dmsp.units_label``, ``dmsp.min_label``, and ``dmsp.notes_label``, etc.

All variables must have the same metadata parameters. If a new parameter
is added for only one data variable, then the remaining data variables will get
a null value for that metadata parameter.

Data may be assigned to the instrument, with or without metadata.

.. code:: python

   # assign data alone
   dmsp['new_data'] = new_data
   # assign data with metadata
   # the data must be keyed under 'data'
   # all other dictionary inputs are presumed to be metadata
   dmsp['new_data'] = {'data': new_data,
                       dmsp.units_label: new_unit,
                       'new_meta_data': new_value}
   # alter assigned metadata
   dmsp.meta['new_data', 'new_meta_data'] = even_newer_value


The labels used for identifying metadata may be provided by the user at
Instrument instantiation and do not need to conform with what is in the file::

   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd', inst_id='f12',
                           clean_level='dirty', units_label='new_units')
   dmsp.load(2001, 1)
   dmsp.meta['ti', 'new_units']
   dmsp.meta['ti', dmsp.units_label]

While this feature doesn't require explicit support on the part of an instrument
module developer, code that does not use the metadata labels may not always
work when a user invokes this functionality.

pysat's metadata object is case insensitive but case preserving. Thus, if
a particular Instrument uses 'units' for units metadata, but a separate
package that operates via pysat but uses 'Units' or even 'UNITS', the code
will still function::

   # the following are all equivalent
   dmsp.meta['TI', 'Long_Name']
   dmsp.meta['Ti', 'long_Name']
   dmsp.meta['ti', 'Long_NAME']

.. note:: While metadata access is case-insensitive, data access is case-sensitive.
