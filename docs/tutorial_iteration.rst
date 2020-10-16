Iteration
---------

The seasonal analysis loop is commonly repeated in data analysis:

.. code:: python

   vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b')
   date_array = pysat.utils.time.create_date_range(start, stop)
   for date in date_array:
       vefi.load(date=date)
       print('Maximum meridional magnetic perturbation ', vefi['dB_mer'].max())

Iteration support is built into the Instrument object to support this and
similar cases. The whole of a data set may be iterated over on a daily basis
using

.. code:: python

    for vefi in vefi:
	    print('Maximum meridional magnetic perturbation ', vefi['dB_mer'].max())

Each loop of the python for iteration initiates a vefi.load() for the next date,
starting with the first available date. By default the instrument instance will
iterate over all available data. To control the range, set the instrument bounds,

.. code:: python

   # multi-season season
   vefi.bounds = ([start1, start2], [stop1, stop2])
   # continuous season
   vefi.bounds = (start, stop)
   # iterate over custom season
   for vefi in vefi:
       print('Maximum meridional magnetic perturbation ', vefi['dB_mer'].max())

The output is,

.. code:: ipython

   Returning cnofs vefi dc_b data for 05/09/10
   Maximum meridional magnetic perturbation  19.3937
   Returning cnofs vefi dc_b data for 05/10/10
   Maximum meridional magnetic perturbation  23.745
   Returning cnofs vefi dc_b data for 05/11/10
   Maximum meridional magnetic perturbation  25.673
   Returning cnofs vefi dc_b data for 05/12/10
   Maximum meridional magnetic perturbation  26.583

So far, the iteration support has only saved a single line of code, the
.load line. However, this line in the examples above is tied to loading by date.
What if we wanted to load by file instead? This would require changing the code.
However, with the abstraction provided by the Instrument iteration, that is no
longer the case.

.. code:: python

   vefi.bounds('filename1', 'filename2')
   for vefi in vefi:
       print('Maximum meridional magnetic perturbation ', vefi['dB_mer'].max())

For VEFI there is only one file per day so there is no practical difference
between the previous example. However, for instruments that have more than one
file a day, there is a difference.

Building support for this iteration into the mean_day example is easy.

.. code:: python

   import pandas
   import pysat

   def daily_mean(inst, data_label):

       # create empty series to hold result
       mean_val = pandas.Series()

       for inst in inst:
	   if not inst.empty:
               # compute mean absolute using pandas functions and store
               # data could be an image, or lower dimension, account for 2D and lower
               data = inst[data_label]
               data = pysat.ssnl.computational_form(data)
               mean_val[inst.date] = data.abs().mean(axis=0, skipna=True)

       return mean_val

Since bounds are attached to the Instrument object, the start and stop dates
for the season are no longer required as inputs. If a user forgets to specify
the bounds, the loop will start on the first day of data and end on the last day.

.. code:: python

   # make a plot of daily dB_mer
   vefi.bounds = (start, stop)
   mean_dB = daily_mean(vefi, 'dB_mer')

   # plot the result using pandas functionality
   variable_str = vefi.meta['dB_mer', vefi.name_label]
   units_str = vefi.meta['dB_mer', vefi.units_label]
   mean_dB.plot(title='Absolute Daily Mean of ' + variable_str)
   plt.ylabel('Absolute Daily Mean ('+ units_str +')')

pysat iteration also supports loading more than a single day/file of data
at a time as well as stepping through the data in daily increments larger
than a single day. Assignment of the data step size and width is also
set via the bounds attribute.

.. code:: python
   # set a season with an expanded load range and increased step size
   # sets a data width of 2 days via the pandas DateOffset
   # sets a data step size of 2 days via the pandas frequency string, '2D'
   vefi.bounds = (starts, stops, '2D', pds.DateOffset(days=2))

   # similarly, iteration over files is supported
   # file width is 2 files
   # file step size is 2 files
   vefi.bounds = (start_files, stop_files, 2, 2)

Note that when iterating over date limits the limits are applied to the dates
associated with the files themselves and do not necessarily apply to the
datetimes associated with the data within the files.

The abstraction provided by the iteration support is also used for the next
section on orbit data.
