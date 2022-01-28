.. _tutorial_custom:

Custom Functions
----------------

Science analysis is built upon custom data processing. To simplify this task,
and enable instrument independent analysis, custom functions may be attached to
the :py:class:`Instrument` or :py:class:`Constellation` object. Each function is
run automatically when new data is loaded before it is made available in
:py:attr:`Instrument.data`.

This feature enables a user to hand a :py:class:`Constellation` or
:py:class:`Instrument` object to an independent routine and ensure any desired
customizations required are performed without any additional user intervention.
This feature enables for the transparent modification of a data set in between
its state at rest on disk and when the data becomes available for use in
:py:attr:`Instrument.data`.

.. warning:: Custom arguments and keywords are supported for these functions.
   However, these arguments and keywords are only evaluated initially when the
   function is attached to an Instrument object. Thus the objects passed in must
   be static or capable of updating themselves from within the custom function
   itself.


Example Function
^^^^^^^^^^^^^^^^

If a custom function is attached to an :py:class:`Instrument` or
:py:class:`Constellation` object, the pysat object is passed to function in
place when the data is loaded. There is no :py:class:`Instrument` or
:py:class:`Constellation` copy made in memory. The function is expected to
modify the supplied pysat object directly and the functions are not allowed to
return any information.  The example below is appropriate to be applied to an
:py:class:`Instrument` or a :py:class:`Constellation` at the
:py:class:`Instrument` level.

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


Custom functions can also be applied at the :py:class:`Constellation` level,
which allows data from multiple :py:class:`Instrument` objects to be used by
a single function.  :py:class:`Constellation` level custom functions are applied
after :py:class:`Instrument` level functions.  Note that the Instrument loading
order for this function is important.  An alternate method would be to identify
the desired :py:attr:`instruments` using the :py:attr:`platform`,
:py:attr:`name`, :py:attr:`tag`, and :py:attr:`inst_id` values.


.. code:: python

   def modify_const(const, inst1_param_name, inst2_param_name, dest_ind=0):
       """Modify param_name in inst by multiplying by factor

       Parameters
       ----------
       const : pysat.Constellation
           Object to be modified
       inst1_param_name : str
           Label for variable from the first Constellation Instrument
       inst2_param_name : str
           Label for variable from the seccond Constellation Instrument
       dest_ind : int
           Zero-based index identifying the destination Instrument for the
           modified data variable

       """
       # Ensure there are enough Instruments in the constellation
       min_inst = 2 if dest_ind < 2 else dest_ind + 1
       if len(const.instruments) < min_inst:
           raise ValueError('unexpected number of Instruments in Constellation')

       # Modify the data by adding new a new data variable to the destination
       # Instrument, calculated with data from the first and second Instruments
       new_data = const.instruments[0][inst1_param_name] * \
           const.instruments[1][inst2_param_name]
       new_var = " x ".join([inst1_param_name, inst2_param_name])
       const.instruments[dest_ind][new_var] = new_data

       return



Attaching Custom Function to an Instrument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom functions must be attached to an :py:class:`Instrument` object for pysat
to automatically apply the function upon every load.

.. code:: python

   # Load data
   ivm.load(2009, 1)

   # Establish current values for 'mlt'
   print(ivm['mlt'])
   stored_data = ivm['mlt'].copy()

   # Attach a custom function and demonstrate execution
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

   # Can also set functions via its string name. This example includes
   # both required and optional arguments, and requires output from
   # the prior custom function
   ivm.custom_attach('modify_value', args=['old_mlt'], kwargs={'factor': 3.0})

   # All three functions are executed with each load call in the order they
   # were attached.
   ivm.load(2009, 1)

   # Verify results are present
   print(ivm[['old_mlt', 'old_old_mlt', 'mlt']], stored_result)


The output of from these and other custom functions will always be available
from the :py:class:`Instrument` object, regardless of what level the science
analysis is performed.

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

    # Attach the custom function defined above
    dmsp.custom_attach(filter_dmsp)

    # Attach the first custom function, and declare it should run first
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

Note the same result is obtained. The DMSP :py:class:`Instrument` object and
analysis are performed at the same level, so there is no strict gain by using
the pysat nano-kernel in this simple demonstration. However, we can use the
nano-kernel to translate this daily mean into an versatile
instrument-independent function.


Attaching Custom Function to an Instrument at Instantiation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom functions may also be attached to an :py:class:`Instrument` object
directly at instantiation via the :py:data:`custom` keyword.

.. code:: python

   # Create dictionary for each custom function and associated inputs
   custom_func_1 = {'function': modify_value, 'args': ['mlt'],
                    'kwargs': {'factor': 2.})}
   custom_func_2 = {'function': modify_value, 'args': ['old_mlt'],
                    'kwargs'={'factor': 3.0}}

   # Combine all dicts into a list in order of application and execution.
   # However, if you specify the 'at_pos' kwarg, it will take precedence.
   custom = [custom_func_1, custom_func_2]

   # Instantiate pysat.Instrument
   inst = pysat.Instrument(platform, name, inst_id=inst_id, tag=tag,
                           custom=custom)


Attaching Custom Function to a Constellation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Attaching custom functions to :py:class:`Constellation` objects is done in the
same way as for :py:class:`Instrument` objects. The only difference is the
additional keyword argument :py:var:`apply_inst`, which defaults to
:py:value:`True` and applies the custom function to all of the
:py:class:`Constellation` :py:class:`Instrument` objects. This example assumes
that the :py:mod:`pysatSpaceWeather` ACE Instruments have been registered.

.. code:: python


   import datetime as dt

   # Apply a Constellation-level custom function at initialization
   const = pysat.Constellation(platforms=['ace'], tags=['historic'],
                               custom=[{'function': modify_const,
                                        'apply_inst': False,
                                        'args': ['eflux_38-53', 'bx_gsm'],
                                        'kwargs': {'dest_ind': 2}}])

   # Get and load data
   stime = dt.datetime(2022, 1, 1)
   const.download(start=stime)
   const.load(date=stime)

   # Check that the expected new variable is present
   # Expected output:
   # Index(['jd', 'sec', 'status_10', 'int_pflux_10MeV', 'status_30',
   #       'int_pflux_30MeV', 'eflux_38-53 x bx_gsm'], dtype='object')
   print(const.instruments[2].variables)


   
