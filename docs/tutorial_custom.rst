
Custom Functions
----------------

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

   def custom_func_modify(inst, optional_param=False):
       """Modify a pysat.Instrument object in place

       Parameters
       ----------
       inst : pysat.Instrument
           Object to be modified
       optional_param : stand-in
           Placeholder to indicate support for custom keywords
           and arguments
       """

       if optional_param:
           inst['double_mlt'] = 2.0 * inst['mlt']
       else:
           inst['double_mlt'= -2.0 * inst['mlt']
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
  dict              Data to be added keyed by data_name
  Iterable          ((name1, name2, ...), (data1, data2, ...))
  Series            Variable name must be in .name
  DataFrame         Columns used as variable names
  DataArray         Variable name must be in .name
===============     ===================================

.. code:: python

   def custom_func_add(inst, optional_param=False):
       """Calculate data to be added to pysat.Instrument object

       Parameters
       ----------
       inst : pysat.Instrument
           pysat will add returned data to this object
       optional_param : stand-in
           Placeholder indicated support for custom keywords
           and arguments
       """

       return ('double_mlt', 2.0 * inst['mlt'])

**Add Function Including Metadata**

Metadata may also be returned when using a dictionary object as the return
type. In this case, the data must be in 'data', with other keys interpreted
as metadata parameters. Multiple data variables may be added in this case
only when using the DataFrame.

.. code:: python

   def custom_func_add(inst, optional_param1=False, optional_param2=False):
       return {'data': 2.*inst['mlt'], 'name': 'double_mlt',
               'long_name': 'doubledouble', 'units': 'hours'}

**Attaching Custom Function**

Custom methods must be attached to an Instrument object for pysat
to automatically apply the method upon every load.

.. code:: python

   ivm.custom.attach(custom_func_modify, 'modify', optional_param2=True)
   ivm.load(2009, 1)
   print(ivm['double_mlt'])
   ivm.custom.attach(custom_func_add, 'add', optional_param2=True)
   # can also set via a string name for method
   ivm.custom.attach('custom_func_add', 'add', optional_param2=False)
   # set bounds limiting the file/date range the Instrument will iterate over
   ivm.bounds = (start, stop)
   # perform analysis. Whatever modifications are enabled by the custom
   # methods are automatically available within the custom analysis
   custom_complicated_analysis_over_season(ivm)

The changes made by custom_func_modify will always be available from instrument
object, regardless of what level the science analysis is performed.

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
    dmsp.custom.attach(filter_dmsp, 'modify')

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
