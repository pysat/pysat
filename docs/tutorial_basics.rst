Basics
------

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

**Basic Instrument Discovery**

----

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
  sat_id		    Label for instrument sub-group
===============     ===================================


All supported pysat Instruments for v2.x are stored in the pysat.instruments
submodule. A listing of all currently supported instruments
is available via help,

.. code:: python

    help(pysat.instruments)

Each instrument listed will support one or more data sets for analysis. The
submodules are named with the convention platform_name. To get
a description of an instrument, along with the supported datasets, use help
again,

.. code:: python

   help(pysat.instruments.dmsp_ivm)

Further, the dictionary::

    pysat.instruments.dmsp_ivm.tags

is keyed by ``tag`` with a description of each type of data
the ``tag`` parameter selects. The dictionary::

    pysat.instruments.dmsp_ivm.sat_ids

indicates which instrument or satellite ids (``sat_id``) support which tag.
The combination of ``tag`` and ``sat_id`` select the particular dataset
a pysat.Instrument object will provide and interact with.


**Instantiation**

----

To create a pysat.Instrument object, select a ``platform``, instrument ``name``,
and potentially a ``tag`` and ``sat_id``, consistent with
the desired data to be analyzed, from one the supported instruments.

To work with plasma data from the
Ion Velocity Meter (IVM) onboard the Defense Meteorological
Satellite Program (DMSP) constellation, use:

.. code:: python

   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd', sat_id='f11')

Behind the scenes pysat uses a python module named dmsp_ivm that understands
how to interact with 'utd' data for 'f11'.


**Download**

----

Let's download some data. DMSP data is hosted by the `Madrigal database
<http://cedar.openmadrigal.org/openmadrigal/>`_, a community resource for
geospace data. The proper process for downloading DMSP and other Madrigal data
is built into the open source
tool `madrigalWeb <http://cedar.openmadrigal.org/docs/name/rr_python.html>`_, which
is invoked appropriately by pysat within the dmsp_ivm module. To get DMSP
data specifically all we have to do is invoke the ``.download()`` method
attached to the DMSP object.

.. code:: python

   # define date range to download data and download
   start = pysat.datetime(2009,5,6)
   stop = pysat.datetime(2009,5,9)
   # download data to local system
   dmsp.download(start, stop)

The data is downloaded to pysat_data_dir/platform/name/tag/, in this case
pysat_data_dir/dmsp/ivm/utd/. At the end of the download, pysat
will update the list of files associated with DMSP.

Note that some datasets, like COSMIC, require registration with a username and
password.  Pysat supports this as well. A user account may be obtained at
the `Cosmic Data Analysis Archival Center <https://cdaac-www.cosmic.ucar.edu>`_.

.. code:: python

  # download COSMIC data, which requires username and password
  cosmic.download(start, stop, user=user, password=password)

Some instruments support an improved download experience that ensures
the local system is fully up to date compared to the data source. The command,

.. code:: python

    dmsp.download_updated_files()

will obtain the full set of files present on the server and compare the
version and revision numbers for the server files with those on the local system.
Any files missing or out of date on the local system are downloaded from the
server. This command downloads, as needed, the entire dataset.


**Load Data**

----

Data is loaded into vefi using the .load method using year, day of year; date; or filename.

.. code:: python

   vefi.load(2009, 126)
   vefi.load(date=start)
   vefi.load(fname='cnofs_vefi_bfield_1sec_20090506_v05.cdf')

When the pysat load routine runs it stores the instrument data into vefi.data. The data structure is a pandas DataFrame_, a highly capable structure with labeled rows and columns. Convenience access to the data is also available at the instrument level.

.. _DataFrame: http://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe

.. code:: python

    # all data
    vefi.data
    # particular magnetic component
    vefi.data.dB_mer

    # Convenience access
    vefi['dB_mer']
    # slicing
    vefi[0:10, 'dB_mer']
    # slicing by date time
    vefi[start:stop, 'dB_mer']

See :any:`Instrument` for more.

To load data over a season, pysat provides a convenience function that returns an array of dates over a season. The season need not be continuous.

.. code:: python

   import matplotlib.pyplot as plt
   import numpy as np
   import pandas

   # create empty series to hold result
   mean_dB = pandas.Series()

   # get list of dates between start and stop
   date_array = pysat.utils.time.create_date_range(start, stop)

   # iterate over season, calculate the mean absolute perturbation in
   # meridional magnetic field
   for date in date_array:
	vefi.load(date=date)
	if not vefi.data.empty:
	    # isolate data to locations near geographic equator
	    idx, = np.where((vefi['latitude'] < 5) & (vefi['latitude'] > -5))
	    vefi.data = vefi.data.iloc[idx]
            # compute mean absolute db_Mer using pandas functions and store
            mean_dB[vefi.date] = vefi['dB_mer'].abs().mean(skipna=True)

   # plot the result using pandas functionality
   mean_dB.plot(title='Mean Absolute Perturbation in Meridional Magnetic Field')
   plt.ylabel('Mean Absolute Perturbation ('+vefi.meta['dB_mer'].units+')')

Note, the numpy.where may be removed using the convenience access to the attached pandas data object.

.. code:: python

   idx, = np.where((vefi['latitude'] < 5) & (vefi['latitude'] > -5))
   vefi.data = vefi.data.iloc[idx]

is equivalent to

.. code:: python

   vefi.data = vefi[(vefi['latitude'] < 5) & (vefi['latitude'] > -5)]


**Clean Data**

-----

Before data is available in .data it passes through an instrument specific cleaning routine. The amount of cleaning is set by the clean_level keyword,

.. code:: python

   vefi = pysat.Instrument(platform='cnofs', name='vefi',
			   tag='dc_b', clean_level='none')

Four levels of cleaning may be specified,

===============     ===================================
**clean_level** 	        **Result**
---------------     -----------------------------------
  clean		    Generally good data
  dusty		    Light cleaning, use with care
  dirty		    Minimal cleaning, use with caution
  none		    No cleaning, use at your own risk
===============     ===================================

**Metadata**

----

Metadata is also stored along with the main science data.

.. code:: python

   # all metadata
   vefi.meta.data

   # dB_mer metadata
   vefi.meta['dB_mer']

   # units
   vefi.meta['dB_mer'].units

   # update units for dB_mer
   vefi.meta['dB_mer'] = {'units':'new_units'}

   # update display name, long_name
   vefi.meta['dB_mer'] = {'long_name':'Fancy Name'}

   # add new meta data
   vefi.meta['new'] = {'units':'fake', 'long_name':'Display'}

Data may be assigned to the instrument, with or without metadata.

.. code:: python

   vefi['new_data'] = new_data

The same activities may be performed for other instruments in the same manner. In particular, for measurements from the Ion Velocity Meter and profiles of electron density from COSMIC, use

.. code:: python

   # assignment with metadata
   ivm = pysat.Instrument(platform='cnofs', name='ivm', tag='')
   ivm.load(date=date)
   ivm['double_mlt'] = {'data': 2.*inst['mlt'], 'long_name': 'Double MLT',
                        'units': 'hours'}

.. code:: python

   cosmic = pysat.Instrument('cosmic', 'gps', tag='ionprf',  clean_level='clean')
   start = pysat.datetime(2009, 1, 2)
   stop = pysat.datetime(2009, 1, 3)

   # requires CDAAC account
   cosmic.download(start, stop, user='', password='')
   cosmic.load(date=start)

   # the profiles column has a DataFrame in each element which stores
   # all relevant profile information indexed by altitude
   # print part of the first profile, selection by integer location
   print(cosmic[0,'profiles'].iloc[55:60, 0:3])

   # print part of profile, selection by altitude value
   print(cosmic[0,'profiles'].iloc[196:207, 0:3])

Output for both print statements:

.. code:: python

                  ELEC_dens    GEO_lat    GEO_lon
   MSL_alt
   196.465454  81807.843750 -15.595786 -73.431015
   198.882019  83305.007812 -15.585764 -73.430191
   201.294342  84696.546875 -15.575747 -73.429382
   203.702469  86303.039062 -15.565735 -73.428589
   206.106354  87460.015625 -15.555729 -73.427803
