Iteration
---------

The seasonal analysis loop is commonly repeated in data analysis:

.. code:: python

   import pysat
   import datetime as dt

   # Instantiate Instrument object
   vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b')

   # Set range of dates and create corresponding array.
   start = dt.datetime(2010, 1, 1)
   stop = dt.datetime(2010, 1, 5)
   date_array = pysat.utils.time.create_date_range(start, stop)

   # download data
   vefi.download(start, stop)

   # Iterate over dates, load data for each date, and determine maximum
   # magnetic perturbation for the day.
   out_str = ''.join(('Maximum meridional magnetic perturbation: ',
                      '{max:3.2f} {units}'))
   for date in date_array:
       vefi.load(date=date)
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', 'units']))


Iteration support is built into the Instrument object to support this and
similar cases. The whole of a data set may be iterated over on a daily basis
using

.. code:: python

   # Iterate over dates, load data for each date, and determine maximum
   # magnetic perturbation for the day.
   out_str = ''.join(('Maximum meridional magnetic perturbation: ',
                      '{max:3.2f} {units}'))
   for vefi in vefi:
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', 'units']))

Each iteration of the "for" loop initiates a vefi.load() for the next date,
starting with the first available date. By default the instrument instance will
iterate over all available data. To control the range, set the instrument bounds,

.. code:: python

   # continuous season
   start = dt.datetime(2010, 1, 1)
   stop = dt.datetime(2010, 1, 5)
   vefi.bounds = (start, stop)

   # iterate over custom season
   out_str = ''.join(('Maximum meridional magnetic perturbation: ',
                      '{max:3.2f} {units}'))
   for vefi in vefi:
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', 'units']))

The output is,

.. code:: ipython

   Maximum meridional magnetic perturbation: 30.79 nT
   Maximum meridional magnetic perturbation: 33.98 nT
   Maximum meridional magnetic perturbation: 29.94 nT
   Maximum meridional magnetic perturbation: 29.63 nT
   Maximum meridional magnetic perturbation: 21.67 nT

Non-continuous seasons are also supported.

.. code:: python

   # multi-season season
   start1 = dt.datetime(2010, 1, 1)
   stop1 = dt.datetime(2010, 1, 2)

   start2 = dt.datetime(2010, 1, 4)
   stop2 = dt.datetime(2010, 1, 5)
   vefi.bounds = ([start1, start2], [stop1, stop2])

   # Update logging for clarity on loaded dates
   pysat.logger.setLevel(pysat.logging.INFO)

   # iterate over custom season
   out_str = ''.join(('Maximum meridional magnetic perturbation: ',
                      '{max:3.2f} {units}'))
   for vefi in vefi:
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', 'units']))

   # Set pysat logging back to standard of only printing information for
   # warnings.
   pysat.logger.setLevel(pysat.logging.WARNING)


The output is,

.. code:: ipython

   pysat INFO: Returning cnofs vefi dc_b data for 01 January 2010
   Maximum meridional magnetic perturbation: 30.79 nT
   pysat INFO: Returning cnofs vefi dc_b data for 02 January 2010
   Maximum meridional magnetic perturbation: 33.98 nT
   pysat INFO: Returning cnofs vefi dc_b data for 04 January 2010
   Maximum meridional magnetic perturbation: 29.63 nT
   pysat INFO: Returning cnofs vefi dc_b data for 05 January 2010
   Maximum meridional magnetic perturbation: 21.67 nT

So far, the iteration support has only saved a single line of code.
What if we wanted to load by file instead? Normally this would require
changing the code. However, with the abstraction provided by the Instrument
iteration, that is no longer the case.

.. code:: python

   vefi.bounds(vefi.files[0], vefi.files[5])
   for vefi in vefi:
       print(out_str.format(max=vefi['dB_mer'].max(),
                            units=vefi.meta['dB_mer', 'units']))

For VEFI there is only one file per day so there is no practical difference
between the previous example. However, for instruments that have more than one
file a day, there is a difference.

Building support for this iteration into the mean_day example is easy.

.. code:: python

   import pandas
   import pysat

   import pysatSeasons

   def daily_mean(inst, data_label):
       """Daily absolute average of data_label over inst.bounds

       Parameters
       ----------
       inst : pysat.Instrument
           Instrument object
       data_label : str
           Label for the variable to be averaged

       Returns
       -------
       pandas.Series
           Average absolute value of `data_label` indexed by day

       """

       # create empty series to hold result
       mean_val = pandas.Series()

       # Iterate over the bounds set by user
       for inst in inst:
           # Check if there is data to be averaged
           if not inst.empty:
               data = inst[data_label]
               # Data could be potentially be 2D or 1D. Process `data`
               # so that the mean absolute value may be calculated using
               # built in pandas functions and then store result.
               data = pysatSeasons.computational_form(data)
               mean_val[inst.date] = data.abs().mean(axis=0, skipna=True)

       return mean_val

Since bounds are attached to the Instrument object, the start and stop dates
for the season are no longer required as inputs. If a user forgets to specify
the bounds, the loop will start on the first day of data and end on the last day.

.. code:: python

   # Make a plot of the daily average perturbation for the meridional
   # component of the geomagnetic field.
   import matplotlib.pyplot as plt

   # Set range of dates for analysis and apply date limits to VEFI object.
   start = dt.datetime(2010, 1, 1)
   stop = dt.datetime(2010, 1, 3)
   vefi.bounds = (start, stop)

   # Calculate the daily mean value for 'dB_mer' over vefi.bounds
   mean_dB = daily_mean(vefi, 'dB_mer')

   # plot the result using pandas functionality
   variable_str = vefi.meta['dB_mer', vefi.name_label]
   units_str = vefi.meta['dB_mer', vefi.units_label]
   mean_dB.plot(title='Absolute Daily Mean of ' + variable_str)
   plt.ylabel('Absolute Daily Mean ('+ units_str +')')
   plt.show()

pysat iteration also supports loading more than a single day/file of data
at a time as well as stepping through the data in daily increments larger
than a single day. Assignment of the data step size and width is also
set via the bounds attribute.

.. code:: python
   # set a season with an expanded load range and increased step size
   # sets a data width of 2 days via the pandas DateOffset
   # sets a data step size of 2 days via the pandas frequency string, '2D'
   vefi.bounds = (starts, stops, '2D', dt.timedelta(days=2))

   # similarly, iteration over files is supported
   # file width is 2 files
   # file step size is 2 files
   vefi.bounds = (start_files, stop_files, 2, 2)

Note that when iterating over date limits the limits are applied to the dates
associated with the files themselves and do not necessarily apply to the
datetimes associated with the data within the files.

The abstraction provided by the iteration support is also used for the next
section on orbit data.
