.. _tutorial-iter:

Iteration
---------

pysat supports iterative loading of data at daily, orbital, and custom
cadances. The examples below show you how this works and how to specify the
loading limits.


Daily Iteration
^^^^^^^^^^^^^^^

By default, pysat will iteratively load data at a daily cadance.

.. code:: python

   import datetime as dt
   import pysat
   import pysatNASA

   # Instantiate Instrument object
   vefi = pysat.Instrument(inst_module=pysatNASA.instruments.cnofs_vefi,
                           tag='dc_b')

   # Set range of dates and create corresponding array.
   start = dt.datetime(2010, 1, 1)
   stop = dt.datetime(2010, 1, 5)
   date_array = pysat.utils.time.create_date_range(start, stop)

   # Download data, if needed.  Download is inclusive of stop time.
   if len(vefi.files[start:stop + dt.timedelta(days=1)]) < 5:
       vefi.download(start=start, stop=stop)

   # Iterate over dates, load data for each date, and determine maximum
   # magnetic perturbation for the day.
   out_str = ''.join(('Maximum meridional magnetic perturbation: ',
                      '{max:3.2f} {units} on {day}'))

   for load_date in date_array:
       vefi.load(date=load_date)
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', vefi.meta.labels.units]),
			      day=vefi.index[0].strftime('%d %b %Y'))


Iteration support is built into the Instrument object to support this and
similar cases. The whole of a data set may be iterated over on a daily basis
using:

.. code:: python

   # Load the first date and set the bounds for consideration
   vefi.load(date=start)
   vefi.bounds = (start, stop)  # `bounds` defaults to all available files

   # Perform the same iteration as the previous block
   for vefi in vefi:
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', vefi.meta.labels.units]),
			      day=vefi.index[0].strftime('%d %b %Y'))


You can also set the bounds to be a range of files:

.. code:: python

   # Load the first date and set the file bounds for consideration
   vefi.load(date=start)
   vefi.bounds = (vefi.files[start], vefi.files[stop])

   for vefi in vefi:
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', vefi.meta.labels.units]),
			      day=vefi.index[0].strftime('%d %b %Y'))


The output in all the above cases is:

.. code:: ipython

   Maximum meridional magnetic perturbation: 30.79 nT on 01 Jan 2010
   Maximum meridional magnetic perturbation: 33.98 nT on 02 Jan 2010
   Maximum meridional magnetic perturbation: 29.94 nT on 03 Jan 2010
   Maximum meridional magnetic perturbation: 29.63 nT on 04 Jan 2010
   Maximum meridional magnetic perturbation: 21.67 nT on 05 Jan 2010

By default, `bounds` is set to the first and last date of the locally available instrument files, all of which are listed in ``vefi.files.files``.


Orbit Iteration
^^^^^^^^^^^^^^^

You can iterate by orbit as well as day.  To do this, be sure to specify what
type of orbit pysat should use.

.. code:: python

   # Instantiate Instrument object with orbit information
   # C/NOFS has a Low Earth Orbit near the equator
   orbit_info = {'kind': 'longitude', 'index': 'longitude'}
   vefi = pysat.Instrument(inst_module=pysatNASA.instruments.cnofs_vefi,
                           tag='dc_b', orbit_info=orbit_info)

   # Load the first date and set the file bounds for consideration
   vefi.load(date=start)
   vefi.bounds = (start, stop)

   # Iterate over each orbit and save the output
   orbit_strs = list()
   for vefi in vefi.orbits:
       orbit_strs.append(
           out_str.format(max=vefi['dB_mer'].max(),
                          units=vefi.meta['dB_mer', vefi.meta.labels.units]),
			  day=vefi.index[0].strftime('%d %b %Y %H:%M')))


A selection of the output looks like:

.. code::

   # Print a selection of the output
   for ostr in orbit_strs[:5]:
       print(ostr)

   Maximum meridional magnetic perturbation: 24.19 nT on 01 Jan 2010 00:00
   Maximum meridional magnetic perturbation: 15.90 nT on 01 Jan 2010 00:47
   Maximum meridional magnetic perturbation: 14.22 nT on 01 Jan 2010 02:31
   Maximum meridional magnetic perturbation: 12.62 nT on 01 Jan 2010 04:16
   Maximum meridional magnetic perturbation: 10.78 nT on 01 Jan 2010 06:01


Non-standard Iteration
^^^^^^^^^^^^^^^^^^^^^^

Non-continuous data iteration is also supported.  This can be useful, for
example, when you want to load data from both the March and September equinoxes
or for several case studies.

.. code:: python

   # Two case studies
   start1 = start
   stop1 = dt.datetime(2010, 1, 2)

   start2 = dt.datetime(2010, 1, 4)
   stop2 = stop
   vefi.bounds = ([start1, start2], [stop1, stop2])

   # Iterate over custom season
   vefi.load(date=start1)
   out_str = ''.join(('Maximum meridional magnetic perturbation: ',
                      '{max:3.2f} {units} on {day}'))
   for vefi in vefi:
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', vefi.meta.labels.units],
			    day=vefi.index[0].strftime('%d %b %Y')))

Now, the output is:

.. code:: ipython

   Maximum meridional magnetic perturbation: 30.79 nT on 01 Jan 2010
   Maximum meridional magnetic perturbation: 33.98 nT on 02 Jan 2010
   Maximum meridional magnetic perturbation: 29.63 nT on 04 Jan 2010
   Maximum meridional magnetic perturbation: 21.67 nT on 05 Jan 2010


pysat iteration also supports loading more than a single day/file of data
at a time as well as stepping through the data in daily increments larger
than a single day. Assignment of the data step size and width is also
set via the bounds attribute.

.. code:: python

   # Set a season with an expanded load range and increased step size. This
   # sets a data width of 2 days
   vefi.bounds = (starts, stops, '2D', dt.timedelta(days=2))

   # Similar behaviour is supported with file bounds. This sets the
   # file width to 2 files and the file step size is 2 files
   vefi.bounds = (start_files, stop_files, 2, 2)

Note that when iterating over date limits the limits are applied to the dates
associated with the files themselves and do not necessarily apply to the
datetimes associated with the data within the files.

The abstraction provided by the iteration support is also used for the next
section on orbit data.
