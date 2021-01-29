.. _tutorial_custom:

Custom Functions
================

Science analysis is built upon custom data processing. To simplify this task, and
enable instrument independent analysis, custom functions may be attached to the
Instrument object. Each function is run automatically when new data is loaded
before it is made available in ``inst.data``.

This feature enables a user to hand an Instrument object to an independent
routine and ensure any desired customizations required are performed without
any additional user intervention. This feature enables for the transparent
modification of a dataset in between its state at rest on disk and when the data
becomes available for use in  ``inst.data``.

.. warning:: Custom arguments and keywords are supported for these methods.
   However, these arguments and keywords are only evaluated initially when the
   method is attached to an Instrument object. Thus the objects passed in must be
   static or capable of updating themselves from within the custom method itself.


**The Modify Functions**

The instrument object is passed to function in place, there
is no Instrument copy made in memory. The method is expected to modify the
supplied Instrument object directly. 'Modify' methods are not allowed to return
any information via the method itself.

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

       inst[param_name] = inst[param_name] * factor

       # Changes to the instrument object are retained
       inst.modify_value_was_here = True

       return

**The Add Functions**

A copy of the Instrument is passed to the method thus any changes made
directly to the object are lost. The data to be added must be returned via
'return' in the method and is added to the true Instrument object by pysat.

Multiple return types are supported:

===============     ===================================
**Type** 	        **Notes**
---------------     -----------------------------------
  tuple             (data_name, data_to_be_added)
  dict              Data to be added keyed under 'data'
  Iterable          ((name1, name2, ...), (data1, data2, ...))
  Series            Variable name must be in .name
  DataFrame         Columns used as variable names
  DataArray         Variable name must be in .name
  Dataset           Merged into existing Instrument.data
===============     ===================================

Metadata may also be returned when using a dictionary object as the return
type. In this case, the data must be in 'data', with other keys interpreted
as metadata parameters. Multiple data variables may be added in this case
only when using the DataFrame.

.. code:: python

   def add_scaled_value(inst, factor, param_name, output_name=None):
       """Scales param_name in Instrument by factor and adds as output_name

       Parameters
       ----------
       inst : pysat.Instrument
       factor : int or float
           Multiplicative scalar applied to `param_name`
       param_name : str
           Label for variable to be multiplied by factor
       output_name : str or None
           Label the result will be stored as in `inst`. If None,
           the output label will be generated as 'scaled_' + `param_name`
           (default=None).

       """

       if output_name is None:
           output_name = '_'.join(('scaled', param_name))

       # Calculate result
       output_data = factor * inst[param_name]

       # Get units from input variable
       output_units = inst.meta[param_name, inst.meta.labels.units]

       # Generate a longer name using param_name's longer descriptive name
       output_longname = ' * '.join(('{num:.2f}'.format(num=factor),
                                     inst.meta[param_name,
                                               inst.meta.labels.name]))

       # Changes to the instrument object are NOT retained after method exits
       inst.add_value_was_here = True

       # Variable name used to identify and access output is provided
       # by user in output_name.
       return {'data': output_data,
               'name': output_name,
               inst.meta.labels.name: output_longname,
               inst.meta.labels.units: output_units}

**Attaching Custom Function**

Custom methods must be attached to an Instrument object for pysat
to automatically apply the method upon every load.

.. code:: python

   # Load data
   ivm.load(2009, 1)

   # Establish current values for 'mlt'
   print(ivm['mlt'])
   stored_data = ivm['mlt'].copy()

   # Attach a 'modify' method and demonstrate execution
   ivm.custom_attach(modify_value, 'modify',
                     args=['mlt'],
                     kwargs={'factor': 2.})

   # `modify_value` is executed as part of the `ivm.load` call.
   ivm.load(2009, 1)

   # Verify result is present
   print(ivm['mlt'], stored_result)

   # Check for attribute added to ivm
   print(ivm.modify_value_was_here)

   # Attach an 'add' method
   ivm.custom_attach(add_scaled_value, 'add', args=[2., 'mlt'],
                     kwargs={'output_name': 'double_mlt'})

   # Both `modify_vaule` and `add_scaled_value` are executed by `ivm.load` call.
   ivm.load(2009, 1)

   # Verify results are present
   print(ivm[['double_mlt', 'mlt']], stored_result)

   # Can also set methods via its string name. This example includes
   # both required and optional arguments.
   ivm.custom_attach('add_scaled_value', 'add', args=[3., 'mlt'],
                     kwargs={'output_name': 'triple_mlt'})

   # All three methods are executed with each load call.
   ivm.load(2009, 1)

   # Verify results are present
   print(ivm[['triple_mlt', 'double_mlt', 'mlt']], stored_result)

   # set bounds limiting the file/date range the Instrument will iterate over
   ivm.bounds = (start, stop)

   # Perform analysis. Whatever modifications are enabled by the custom
   # methods are automatically available within the custom analysis.
   custom_complicated_analysis_over_season(ivm)


The output of from these and other custom methods will always be available
from the instrument object, regardless of what level the science analysis
is performed.

We can repeat the earlier DMSP example, this time using nano-kernel
functionality.

.. code:: python

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas

    # create custom function
    def filter_dmsp(inst, limit=None):
        # isolate data to locations near geomagnetic equator
        idx, = np.where((dmsp['mlat'] < 5) & (dmsp['mlat'] > -5))
        # downselect data
        dmsp.data = dmsp[idx]

    # get list of dates between start and stop
    start = dt.datetime(2001, 1, 1)
    stop = dt.datetime(2001, 1, 10)
    date_array = pysat.utils.time.create_date_range(start, stop)

    # create empty series to hold result
    mean_ti = pandas.Series()

    # instantiate pysat.Instrument
    dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd',
                            inst_id='f12')
    # attach custom method from above
    dmsp.custom_attach(filter_dmsp, 'modify')

    # iterate over season, calculate the mean Ion Temperature
    for date in date_array:
       # load data into dmsp.data
       dmsp.load(date=date)
       # check if data present
       if not dmsp.empty:
           # compute mean ion temperature using pandas functions and store
           mean_ti[dmsp.date] = dmsp['ti'].mean(skipna=True)

    # plot the result using pandas functionality
    mean_ti.plot(title='Mean Ion Temperature near Magnetic Equator')
    plt.ylabel(dmsp.meta['ti', dmsp.desc_label] + ' (' +
               dmsp.meta['ti', dmsp.units_label] + ')')

Note the same result is obtained. The DMSP instrument object and analysis are
performed at the same level, so there is no strict gain by using the pysat
nano-kernel in this simple demonstration. However, we can  use the nano-kernel
to translate this daily mean into an versatile instrument independent function.

**Attaching Custom Function at Instantiation**

Custom methods may also be attached to an Instrument object directly
at instantiation via the `custom` keyword.

.. code:: python

   # Create dictionary for each custom method and associated inputs
   custom_func_1 = {'function': modify_value, 'kind': 'modify',
                    'args': ['mlt'], 'kwargs': {'factor': 2.})}
   custom_func_2 = {'function': add_scaled_value, 'kind': 'add',
                    'args': [2., 'mlt'], 'kwargs'={'output_name': 'double_mlt'}}
   custom_func_3 = {'function': add_scaled_value, 'kind': 'add',
                    'args': [3., 'mlt'], 'kwargs'={'output_name': 'triple_mlt'}}

   # Combine all dicts into a list in order of application and execution.
   custom = [custom_func_1, custom_func_2, custom_func_3]

   # Instantiate pysat.Instrument
   inst = pysat.Instrument(platform, name, inst_id=inst_id, tag=tag,
                           custom=custom)
