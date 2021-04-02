.. _tutorial_custom:

Custom Functions
================

Science analysis is built upon custom data processing. To simplify this task,
and enable instrument independent analysis, custom functions may be attached to
the Instrument object. Each function is run automatically when new data is
loaded before it is made available in ``inst.data``.

This feature enables a user to hand an Instrument object to an independent
routine and ensure any desired customizations required are performed without
any additional user intervention. This feature enables for the transparent
modification of a dataset in between its state at rest on disk and when the data
becomes available for use in  ``inst.data``.

.. warning:: Custom arguments and keywords are supported for these methods.
   However, these arguments and keywords are only evaluated initially when the
   method is attached to an Instrument object. Thus the objects passed in must
   be static or capable of updating themselves from within the custom method
   itself.


Example Function
^^^^^^^^^^^^^^^^

If a custom function is attached to an Instrument, when asking to load data
into the Instrument, the Instrument object is passed to function in place. There
is no Instrument copy made in memory. The method is expected to modify the
supplied Instrument object directly and the funtions are not allowed to return
any information.

.. code:: python

   def modify_value(inst, param_name, factor=1.):
       """Modify param_name in inst by multiplying by factor

       Parameters
       ----------
       inst : pysat.Instrument
           Object to be modified
       param_name : str
           Label for variable to be multiplied by factor
       factor : int or float
           Value to apply to param_name via multiplication (default=1.)

       """
       # Save the old data
       inst['old_{:s}'.format(param_name)] = inst[param_name]

       # Modify the data by multiplying it by a specified value
       inst[param_name] = inst[param_name] * factor

       # Changes to the instrument object are retained
       inst.modify_value_was_here = True

       return

Attaching Custom Function
^^^^^^^^^^^^^^^^^^^^^^^^^

Custom methods must be attached to an Instrument object for pysat
to automatically apply the method upon every load.

.. code:: python

   # Load data
   ivm.load(2009, 1)

   # Establish current values for 'mlt'
   print(ivm['mlt'])
   stored_data = ivm['mlt'].copy()

   # Attach a custom method and demonstrate execution
   ivm.custom_attach(modify_value, args=['mlt'], kwargs={'factor': 2.})

   # `modify_value` is executed as part of the `ivm.load` call.
   ivm.load(2009, 1)

   # Verify result is present
   print(ivm['mlt'], stored_result)

   # Check for attribute added to ivm
   print(ivm.modify_value_was_here)

   # `modify_vaule` is executed by `ivm.load` call.
   ivm.load(2009, 1)

   # Verify results are present
   print(ivm[['old_mlt', 'mlt']], stored_result)

   # Can also set methods via its string name. This example includes
   # both required and optional arguments, and requires output from
   # the prior custom function
   ivm.custom_attach('modify_value', args=['old_mlt'], kwargs={'factor': 3.0})

   # All three methods are executed with each load call in the order they
   # were attached.
   ivm.load(2009, 1)

   # Verify results are present
   print(ivm[['old_mlt', 'old_old_mlt', 'mlt']], stored_result)


The output of from these and other custom methods will always be available
from the instrument object, regardless of what level the science analysis
is performed.

We can repeat the earlier DMSP example, this time using nano-kernel
functionality.

.. code:: python

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas

    # Create custom function
    def filter_dmsp(inst, limit=None):
        # Isolate data to locations near geomagnetic equator
        idx, = np.where((dmsp['mlat'] < 5) & (dmsp['mlat'] > -5))

        # Downselect data
        dmsp.data = dmsp[idx]
	return

    # Get a list of dates between start and stop
    start = dt.datetime(2001, 1, 1)
    stop = dt.datetime(2001, 1, 10)
    date_array = pysat.utils.time.create_date_range(start, stop)

    # Create empty series to hold result
    mean_ti = pandas.Series()

    # Instantiate the pysat.Instrument
    dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd',
                            inst_id='f12')

    # Attach the custom method defined above
    dmsp.custom_attach(filter_dmsp)

    # Attach the first custom method, and declare it should run first
    dmsp.custom_attach('modify_value', at_pos=0, args=['ti'],
                        kwargs={'factor': 2.0})

    # Iterate over season, calculate the mean Ion Temperature
    for date in date_array:
       # Load data into dmsp.data
       dmsp.load(date=date)

       # Compute mean ion temperature using pandas functions and store
       if not dmsp.empty:
           mean_ti[dmsp.date] = dmsp['old_ti'].mean(skipna=True)

    # Plot the result using pandas functionality
    mean_ti.plot(title='Mean Ion Temperature near Magnetic Equator')

    # Because the custom function didn't add metadata, use the old data name
    plt.ylabel(dmsp.meta['ti', dmsp.desc_label] + ' (' +
               dmsp.meta['ti', dmsp.units_label] + ')')

Note the same result is obtained. The DMSP instrument object and analysis are
performed at the same level, so there is no strict gain by using the pysat
nano-kernel in this simple demonstration. However, we can  use the nano-kernel
to translate this daily mean into an versatile instrument independent function.

Attaching Custom Function at Instantiation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom methods may also be attached to an Instrument object directly
at instantiation via the `custom` keyword.

.. code:: python

   # Create dictionary for each custom method and associated inputs
   custom_func_1 = {'function': modify_value, 'args': ['mlt'],
                    'kwargs': {'factor': 2.})}
   custom_func_2 = {'function': modify_value, 'args': ['old_mlt'],
                    'kwargs'={'factor': 3.0}}

   # Combine all dicts into a list in order of application and execution.
   # If you specify the 'at_pos' kwarg, however, it will take precedence.
   custom = [custom_func_1, custom_func_2]

   # Instantiate pysat.Instrument
   inst = pysat.Instrument(platform, name, inst_id=inst_id, tag=tag,
                           custom=custom)
