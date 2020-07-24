
Custom Functions
----------------

Science analysis is built upon custom data processing. To simplify this task and enable instrument independent analysis, custom functions may be attached to the Instrument object. Each function is run automatically when new data is loaded before it is made available in .data.

**Modify Functions**

	The instrument object is passed to function without copying, modify in place.

.. code:: python

   def custom_func_modify(inst, optional_param=False):
       inst['double_mlt'] = 2.0 * inst['mlt']

**Add Functions**

	A copy of the instrument is passed to function, data to be added is returned.

.. code:: python

   def custom_func_add(inst, optional_param=False):
       return 2.0 * inst['mlt']

**Add Function Including Metadata**

.. code:: python

   def custom_func_add(inst, optional_param1=False, optional_param2=False):
       return {'data': 2.*inst['mlt'], 'name': 'double_mlt',
               'long_name': 'doubledouble', 'units': 'hours'}

**Attaching Custom Function**

.. code:: python

   ivm.custom.add(custom_func_modify, 'modify', optional_param2=True)
   ivm.load(2009, 1)
   print(ivm['double_mlt'])
   ivm.custom.add(custom_func_add, 'add', optional_param2=True)
   ivm.bounds = (start, stop)
   custom_complicated_analysis_over_season(ivm)

The output of custom_func_modify will always be available from instrument object, regardless of what level the science analysis is performed.

We can repeat the earlier VEFI example, this time using nano-kernel functionality.

.. code:: python

   import matplotlib.pyplot as plt
   import numpy as np
   import pandas

   vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b')

   def filter_vefi(inst):
       # select data near geographic equator
       idx, = np.where((inst['latitude'] < 5) & (inst['latitude'] > -5))
       inst.data = inst.data.iloc[idx]
       return

   # attach filter to vefi object, function is run upon every load
   vefi.custom.add(filter_vefi, 'modify')

   # create empty series to hold result
   mean_dB = pandas.Series()

   # get list of dates between start and stop
   date_array = pysat.utils.time.create_date_range(start, stop)

   # iterate over season, calculate the mean absolute perturbation in
   # meridional magnetic field
   for date in date_array:
	vefi.load(date=date)
	if not vefi.data.empty:
            # compute mean absolute db_Mer using pandas functions and store
            mean_dB[vefi.date] = vefi['dB_mer'].abs().mean(skipna=True)

   # plot the result using pandas functionality
   mean_dB.plot(title='Mean Absolute Perturbation in Meridional Magnetic Field')
   plt.ylabel('Mean Absolute Perturbation (' + vefi.meta['dB_mer'].units + ')')

Note the same result is obtained. The VEFI instrument object and analysis are performed at the same level, so there is no strict gain by using the pysat nano-kernel in this simple demonstration. However, we can  use the nano-kernel to translate this daily mean into an versatile instrument independent function.
