Initial Instrument Independence
-------------------------------

**Adding Instrument Independence**

.. code:: python

   import matplotlib.pyplot as plt
   import numpy as np
   import pandas

   def daily_mean(inst, start, stop, data_label):

      # create empty series to hold result
      mean_val = pandas.Series()

      # get list of dates between start and stop
      date_array = pysat.utils.time.create_date_range(start, stop)

      # iterate over season, calculate the mean
      for date in date_array:
	   inst.load(date=date)
	   if not inst.data.empty:
               # compute mean absolute db_Mer using pandas functions and store
               mean_val[inst.date] = inst[data_label].abs().mean(skipna=True)
      return mean_val

   vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b')

   def filter_vefi(inst):
       # select data near geographic equator
       idx, = np.where((inst['latitude'] < 5) & (inst['latitude'] > -5))
       inst.data = inst.data.iloc[idx]
       return

   # attach filter to vefi object, function is run upon every load
   vefi.custom.add(filter_vefi, 'modify')

   # make a plot of daily dB_mer
   mean_dB = daily_mean(vefi, start, stop, 'dB_mer')

   # plot the result using pandas functionality
   mean_dB.plot(title='Absolute Daily Mean of '
   	        + vefi.meta['dB_mer'].long_name)
   plt.ylabel('Absolute Daily Mean (' + vefi.meta['dB_mer'].units + ')')


The pysat nano-kernel lets you modify any data set as needed so that you can get the daily mean you desire, without having to modify the daily_mean function.

Check the instrument independence using a different instrument. Whatever instrument is supplied may be modified in arbitrary ways by the nano-kernel.

.. code:: python

   cosmic = pysat.Instrument('cosmic', 'gps', tag='ionprf', clean_level='clean', altitude_bin=3)

   def filter_cosmic(inst):
       inst.data = inst[(inst['edmaxlat'] > -15) & (inst['edmaxlat'] < 15)]
       return

   cosmic.custom.add(filter_cosmic, 'modify')
   data_label = 'edmax'
   mean_max_dens = daily_mean(cosmic, start, stop, data_label)

   # plot the result using pandas functionality
   mean_max_dens.plot(title='Absolute Daily Mean of ' + cosmic.meta[data_label].long_name)
   plt.ylabel('Absolute Daily Mean (' + cosmic.meta[data_label].units + ')')

daily_mean now works for any instrument, as long as the data to be averaged is 1D. This can be fixed.

**Partial Independence from Dimensionality**

.. code:: python

   import pandas
   import pysat

   def daily_mean(inst, start, stop, data_label):

       # create empty series to hold result
       mean_val = pandas.Series()
       # get list of dates between start and stop
       date_array = pysat.utils.time.create_date_range(start, stop)
       # iterate over season, calculate the mean
       for date in date_array:
           inst.load(date=date)
	   if not inst.data.empty:
               # compute mean absolute using pandas functions and store
               # data could be an image, or lower dimension, account for 2D and lower
               data = inst[data_label]
               if isinstance(data.iloc[0], pandas.DataFrame):
	           # 3D data, 2D data at every time
                   data_panel = pandas.Panel.from_dict(dict([(i, data.iloc[i]) for i in xrange(len(data))]))
                   mean_val[inst.date] = data_panel.abs().mean(axis=0,skipna=True)
               elif isinstance(data.iloc[0], pandas.Series):
	           # 2D data, 1D data for each time
                   data_frame = pandas.DataFrame(data.tolist())
                   data_frame.index = data.index
                   mean_val[inst.date] = data_frame.abs().mean(axis=0, skipna=True)
               else:
		  # 1D data
                   mean_val[inst.date] = inst[data_label].abs().mean(axis=0,skipna=True)

   return mean_val

This code works for 1D, 2D, and 3D datasets, regardless of instrument platform, with only some minor changes from the initial VEFI specific code. In-situ measurements, remote profiles, and remote images. It is true the nested if statements aren't the most elegant. Particularly the 3D case. However this code puts the data into an appropriate structure for pandas to align each of the profiles/images by their respective indices before performing the average. Note that the line to obtain the arithmetic mean is the same in all cases, .mean(axis=0, skipna=True). There is an opportunity here for pysat to clean up the little mess caused by dimensionality.

.. code:: python

   import pandas
   import pysat

   def daily_mean(inst, start, stop, data_label):

       # create empty series to hold result
       mean_val = pandas.Series()
       # get list of dates between start and stop
       date_array = pysat.utils.time.create_date_range(start, stop)
       # iterate over season, calculate the mean
       for date in date_array:
           inst.load(date=date)
	   if not inst.data.empty:
               # compute mean absolute using pandas functions and store
               # data could be an image, or lower dimension, account for 2D and lower
               data = inst[data_label]
               data = pysat.ssnl.computational_form(data)
               mean_val[inst.date] = data.abs().mean(axis=0, skipna=True)

   return mean_val
