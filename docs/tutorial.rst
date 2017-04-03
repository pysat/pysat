
Tutorial
========

Basics
------

The core functionality of pysat is exposed through the pysat.Instrument object. The intent of the Instrument object is to offer a single interface for interacting with science data that is independent of measurement platform. The layer of abstraction presented by the Instrument object allows for things to occur in the background that can make science data analysis simpler and more rigorous.

To begin, 

.. code:: python
   
   import pysat

The data directory pysat looks in for data (pysat_data_dir) needs to be set upon the first import,

.. code:: python

   pysat.utils.set_data_dir(path=path_to_existing_directory)

**Instantiation**

----

To create a pysat.Instrument object, select a platform, instrument name, and measurement type to be analyzed from the list of :doc:`supported_instruments`. To work with Magnetometer data from the Vector Electric Field Instrument onboard the Communications/Navigation Outage Forecasting System (C/NOFS), use:

.. code:: python

   vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b')

Behind the scenes pysat uses a python module named cnofs_vefi that understands how to interact with 'dc_b' data. VEFI also measures electric fields in several modes that offer different data products. Though these measurements are not currently supported by the cnofs_vefi module, when they are, they can be selected via the tag string.

To load measurements from a different instrument on C/NOFS, the Ion Velocity Meter, which measures thermal plasma parameters, use:

.. code:: python

   ivm = pysat.Instrument(platform='cnofs', name='ivm')

In the background pysat uses the module cnofs_ivm to handle this data. There is only one measurement option from IVM, so no tag string is required.

Measurements from a constellation of COSMIC satellites are also available. These satellites measure GPS signals as they travel through the atmosphere. A number of different data sets are available from COSMIC, and are also supported by the relevant module.

.. code:: python

   # electron density profiles
   cosmic = pysat.Instrument(platform='cosmic2013', name='gps', tag='ionprf')
   # atmosphere profiles
   cosmic = pysat.Instrument(platform='cosmic2013', name='gps', tag='atmprf')



Though the particulars of VEFI magnetometer data, IVM plasma parameters, and COSMIC atmospheric measurements are going to be quite different, the processes demonstrated below with VEFI also apply equally to IVM and COSMIC.

**Download**

----

Let's download some data. VEFI data is hosted by the NASA Coordinated Data Analysis Web (CDAWeb) at http://cdaweb.gsfc.nasa.gov. The proper process for downloading VEFI data is built into the cnofs_vefi module, which is handled by pysat. All we have to do is invoke the .download method attached to the VEFI object, or any other pysat Instrument.

.. code:: python

   # define date range to download data and download
   start = pysat.datetime(2009,5,6)
   stop = pysat.datetime(2009,5,9)
   vefi.download(start, stop)

   # download COSMIC data, which requires username and password
   cosmic.download(start, stop, user=user, password=password)

The data is downloaded to pysat_data_dir/platform/name/tag/, in this case pysat_data_dir/cnofs/vefi/dc_b/. At the end of the download, pysat will update the list of files associated with VEFI.


**Load Data**

----

Data is loaded into vefi using the .load method using year, day of year; date; or filename.

.. code:: python

   vefi.load(2009,126)
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
   
   import pandas
   import matplotlib.pyplot as plt
   import numpy as np

   # create empty series to hold result
   mean_dB = pandas.Series()
   # get list of dates between start and stop
   date_array = pysat.utils.season_date_range(start, stop)
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
   ivm['double_mlt'] = {'data':2.*inst['mlt'], 'long_name':'Double MLT', 
                        'units':'hours'}

.. code:: python

   cosmic = pysat.Instrument('cosmic2013','gps', tag='ionprf',  clean_level='clean')
   start = pysat.datetime(2009,1,2)
   stop = pysat.datetime(2009,1,3)
   # requires CDAAC account 
   cosmic.download(start, stop, user='', password='')
   cosmic.load(date=start)
   # the profiles column has a DataFrame in each element which stores
   # all relevant profile information indexed by altitude
   # print part of the first profile, selection by integer location
   print(cosmic[0,'profiles'].iloc[55:60, 0:3])
   # print part of profile, selection by altitude value
   print(cosmic[0,'profiles'].ix[196:207, 0:3])

Output for both print statements:

.. code:: python

                  ELEC_dens    GEO_lat    GEO_lon
   MSL_alt                                       
   196.465454  81807.843750 -15.595786 -73.431015
   198.882019  83305.007812 -15.585764 -73.430191
   201.294342  84696.546875 -15.575747 -73.429382
   203.702469  86303.039062 -15.565735 -73.428589
   206.106354  87460.015625 -15.555729 -73.427803
    
Custom Functions
----------------

Science analysis is built upon custom data processing. To simplify this task and enable instrument independent analysis, custom functions may be attached to the Instrument object. Each function is run automatically when new data is loaded before it is made available in .data. 

**Modify Functions**

	The instrument object is passed to function without copying, modify in place.

.. code:: python

   def custom_func_modify(inst, optional_param=False):
       inst['double_mlt'] = 2.*inst['mlt']

**Add Functions**

	A copy of the instrument is passed to function, data to be added is returned.

.. code:: python

   def custom_func_add(inst, optional_param=False):
       return 2.*inst['mlt']

**Add Function Including Metadata**

.. code:: python

   def custom_func_add(inst, optional_param1=False, optional_param2=False):
       return {'data':2.*inst['mlt'], 'name':'double_mlt', 
               'long_name':'doubledouble', 'units':'hours'}

**Attaching Custom Function**

.. code:: python

   ivm.custom.add(custom_func_modify, 'modify', optional_param2=True)
   ivm.load(2009,1)
   print (ivm['double_mlt'])
   ivm.custom.add(custom_func_add, 'add', optional_param2=True)
   ivm.bounds = (start,stop)
   custom_complicated_analysis_over_season(ivm)

The output of custom_func_modify will always be available from instrument object, regardless of what level the science analysis is performed.

We can repeat the earlier VEFI example, this time using nano-kernel functionality.

.. code:: python
   
   import pandas
   import matplotlib.pyplot as plt
   import numpy as np

   vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b')

   def filter_vefi(inst):
       # select data near geographic equator
       idx, = np.where((vefi['latitude'] < 5) & (vefi['latitude'] > -5))
       vefi.data = vefi.data.iloc[idx]
       return
   # attach filter to vefi object, function is run upon every load
   vefi.custom.add(filter_ivm, 'modify')

   # create empty series to hold result
   mean_dB = pandas.Series()
   # get list of dates between start and stop
   date_array = pysat.utils.season_date_range(start, stop)
   # iterate over season, calculate the mean absolute perturbation in
   # meridional magnetic field 
   for date in date_array:
	vefi.load(date=date)
	if not vefi.data.empty:
            # compute mean absolute db_Mer using pandas functions and store
            mean_dB[vefi.date] = vefi['dB_mer'].abs().mean(skipna=True)
   # plot the result using pandas functionality
   mean_dB.plot(title='Mean Absolute Perturbation in Meridional Magnetic Field')
   plt.ylabel('Mean Absolute Perturbation ('+vefi.meta['dB_mer'].units+')')

Note the same result is obtained. The VEFI instrument object and analysis are performed at the same level, so there is no strict gain by using the pysat nano-kernel in this simple demonstration. However, we can  use the nano-kernel to translate this daily mean into an versatile instrument independent function.

**Adding Instrument Independence**

.. code:: python
   
   import pandas
   import matplotlib.pyplot as plt
   import numpy as np

   def daily_mean(inst, start, stop, data_label):

      # create empty series to hold result
      mean_val = pandas.Series()
      # get list of dates between start and stop
      date_array = pysat.utils.season_date_range(start, stop)
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
       idx, = np.where((vefi['latitude'] < 5) & (vefi['latitude'] > -5))
       vefi.data = vefi.data.iloc[idx]
       return
   # attach filter to vefi object, function is run upon every load
   vefi.custom.add(filter_ivm, 'modify')

   # make a plot of daily dB_mer
   mean_dB = daily_mean(vefi, start, stop, 'dB_mer')

   # plot the result using pandas functionality
   mean_dB.plot(title='Absolute Daily Mean of ' 
   	        + vefi.meta['dB_mer'].long_name)
   plt.ylabel('Absolute Daily Mean ('+vefi.meta['dB_mer'].units+')')


The pysat nano-kernel lets you modify any data set as needed so that you can get the daily mean you desire, without having to modify the daily_mean function.

Check the instrument independence using a different instrument. Whatever instrument is supplied may be modified in arbitrary ways by the nano-kernel. 

.. code:: python

   cosmic = pysat.Instrument('cosmic2013','gps', tag='ionprf', clean_level='clean', altitude_bin=3)

   def filter_cosmic(inst):
       cosmic.data = cosmic[(cosmic['edmaxlat'] > -15) & (cosmic['edmaxlat'] < 15)]
       return

   cosmic.custom.add(filter_cosmic, 'modify')
   data_label = 'edmax'
   mean_max_dens = daily_mean(cosmic, start, stop, data_label)

   # plot the result using pandas functionality
   mean_max_dens.plot(title='Absolute Daily Mean of ' + cosmic.meta[data_label].long_name)
   plt.ylabel('Absolute Daily Mean ('+cosmic.meta[data_label].units+')')

daily_mean now works for any instrument, as long as the data to be averaged is 1D. This can be fixed.

**Partial Independence from Dimensionality**

.. code:: python

   import pandas
   import pysat

   def daily_mean(inst, start, stop, data_label):

       # create empty series to hold result
       mean_val = pandas.Series()
       # get list of dates between start and stop
       date_array = pysat.utils.season_date_range(start, stop)
       # iterate over season, calculate the mean
       for date in date_array:
           inst.load(date=date)
	   if not inst.data.empty:
               # compute mean absolute using pandas functions and store
               # data could be an image, or lower dimension, account for 2D and lower
               data = inst[data_label]
               if isinstance(data.iloc[0], pandas.DataFrame):
	           # 3D data, 2D data at every time
                   data_panel = pandas.Panel.from_dict(dict([(i,data.iloc[i]) for i in xrange(len(data))]))
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
       date_array = pysat.utils.season_date_range(start, stop)
       # iterate over season, calculate the mean
       for date in date_array:
           inst.load(date=date)
	   if not inst.data.empty:
               # compute mean absolute using pandas functions and store
               # data could be an image, or lower dimension, account for 2D and lower
               data = inst[data_label]
               data = pysat.utils.computational_form(data)
               mean_val[inst.date] = data.abs().mean(axis=0, skipna=True)
                   
   return mean_val


Time Series Analysis
--------------------

Pending


Iteration
---------

The seasonal analysis loop is repeated commonly:

.. code:: python
   
   date_array = pysat.utils.season_date_range(start,stop)
   for date in date_array:
       vefi.load(date=date)
       print 'Maximum meridional magnetic perturbation ', vefi['dB_mer'].max()

Iteration support is built into the Instrument object to support this and similar cases. The whole VEFI data set may be iterated over on a daily basis using

.. code:: python

    for vefi in vefi:
	print 'Maximum meridional magnetic perturbation ', vefi['dB_mer'].max()

Each loop of the python for iteration initiates a vefi.load() for the next date, starting with the first available date. By default the instrument instance will iterate over all available data. To control the range, set the instrument bounds,

.. code:: python
   
   # multi-season season
   vefi.bounds = ([start1, start2], [stop1, stop2])
   # continuous season
   vefi.bounds = (start, stop)
   # iterate over custom season
   for vefi in vefi:
       print 'Maximum meridional magnetic perturbation ', vefi['dB_mer'].max()

The output is,

.. code:: python

   Returning cnofs vefi dc_b data for 05/09/10
   Maximum meridional magnetic perturbation  19.3937
   Returning cnofs vefi dc_b data for 05/10/10
   Maximum meridional magnetic perturbation  23.745
   Returning cnofs vefi dc_b data for 05/11/10
   Maximum meridional magnetic perturbation  25.673
   Returning cnofs vefi dc_b data for 05/12/10
   Maximum meridional magnetic perturbation  26.583

So far, the iteration support has only saved a single line of code, the .load line. However, this line in the examples above is tied to loading by date. What if we wanted to load by file instead? This would require changing the code. However, with the abstraction provided by the Instrument iteration, that is no longer the case.

.. code:: python

   vefi.bounds( 'filename1', 'filename2')
   for vefi in vefi:
       print 'Maximum meridional magnetic perturbation ', vefi['dB_mer'].max()

For VEFI there is only one file per day so there is no practical difference between the previous example. However, for instruments that have more than one file a day, there is a difference. 

Building support for this iteration into the mean_day example is easy.

.. code:: python

   import pandas
   import pysat

   def daily_mean(inst, data_label):

       # create empty series to hold result
       mean_val = pandas.Series()

       for inst in inst:	
	   if not inst.data.empty:
               # compute mean absolute using pandas functions and store
               # data could be an image, or lower dimension, account for 2D and lower
               data = inst[data_label]
               data = pysat.utils.computational_form(data)
               mean_val[inst.date] = data.abs().mean(axis=0, skipna=True)
                   
       return mean_val

Since bounds are attached to the Instrument object, the start and stop dates for the season are no longer required as inputs. If a user forgets to specify the bounds, the loop will start on the first day of data and end on the last day.

.. code:: python
 
   # make a plot of daily dB_mer
   vefi.bounds = (start, stop)
   mean_dB = daily_mean(vefi, 'dB_mer')

   # plot the result using pandas functionality
   mean_dB.plot(title='Absolute Daily Mean of ' 
   	        + vefi.meta['dB_mer'].long_name)
   plt.ylabel('Absolute Daily Mean ('+vefi.meta['dB_mer'].units+')')

The abstraction provided by the iteration support is also used for the next section on orbit data.   



Orbit Support
-------------

Pysat has functionality to determine orbits on the fly from loaded data. These orbits will span day breaks as needed (generally). Information about the orbit needs to be provided at initialization. The 'index' is the name of the data to be used for determining orbits, and 'kind' indicates type of orbit. See :any:`pysat.Orbits` for latest inputs.

There are several orbits to choose from,

===========   ================
**kind**	**method**
-----------   ----------------
local time     Uses negative gradients to delineate orbits
longitude      Uses negative gradients to delineate orbits
polar	       Uses sign changes to delineate orbits
===========   ================	

Changes in universal time are also used to delineate orbits. Pysat compares any gaps to the supplied orbital period, nominally assumed to be 97 minutes. As orbit periods aren't constant, a 100% success rate is not be guaranteed.

This section of pysat is still under development.  

.. code:: python
    
   info = {'index':'mlt', 'kind':'local time'}
   ivm = pysat.Instrument(platform='cnofs', name='ivm', orbit_info=info, clean_level='None')

Orbit determination acts upon data loaded in the ivm object, so to begin we must load some data.

.. code:: python

   ivm.load(date=start)

Orbits may be selected directly from the attached .orbit class. The data for the orbit is stored in .data. 

.. code:: python

   In [50]: ivm.orbits[1]
   Out[50]:
   Returning cnofs ivm  data for 12/27/12
   Returning cnofs ivm  data for 12/28/12
   Loaded Orbit:1

Note that getting the first orbit caused pysat to load the day previous, and then back to the current day. Orbits are one indexed though this will change. Pysat is checking here if the first orbit for 12/28/2012 actually started on 12/27/2012. In this case it does.

.. code:: ipython
   
   In [51]: ivm[0:5,'mlt']
   Out[51]: 
   2012-12-27 23:05:14.584000    0.002449
   2012-12-27 23:05:15.584000    0.006380
   2012-12-27 23:05:16.584000    0.010313
   2012-12-27 23:05:17.584000    0.014245
   2012-12-27 23:05:18.584000    0.018178
   Name: mlt, dtype: float32

   In [52]: ivm[-5:,'mlt']
   Out[52]: 
   2012-12-28 00:41:50.563000    23.985415
   2012-12-28 00:41:51.563000    23.989031
   2012-12-28 00:41:52.563000    23.992649
   2012-12-28 00:41:53.563000    23.996267
   2012-12-28 00:41:54.563000    23.999886
   Name: mlt, dtype: float32

Let's go back an orbit.

.. code:: ipython

   In [53]: ivm.orbits.prev()
   Out[53]:
   Returning cnofs ivm  data for 12/27/12
   Loaded Orbit:15

   In [54]: ivm[-5:,'mlt']
   Out[54]: 
   2012-12-27 23:05:09.584000    23.982796
   2012-12-27 23:05:10.584000    23.986725
   2012-12-27 23:05:11.584000    23.990656
   2012-12-27 23:05:12.584000    23.994587
   2012-12-27 23:05:13.584000    23.998516
   Name: mlt, dtype: float32

pysat loads the previous day, as needed, and returns the last orbit for 12/27/2012 that does not (or should not) extend into 12/28. 

If we continue to iterate orbits using 

.. code:: python

   ivm.orbits.next()

eventually the next day will be loaded to try and form a complete orbit. You can skip the iteration and just go for the last orbit of a day,

.. code:: ipython
   
   In[] : ivm.orbits[-1]
   Out[]:
   Returning cnofs ivm  data for 12/29/12
   Loaded Orbit:1

.. code:: ipython

   In[72] : ivm[:5,'mlt']
   Out[72]: 
   2012-12-28 23:03:34.160000    0.003109
   2012-12-28 23:03:35.152000    0.007052
   2012-12-28 23:03:36.160000    0.010996
   2012-12-28 23:03:37.152000    0.014940
   2012-12-28 23:03:38.160000    0.018884
   Name: mlt, dtype: float32

   In[73] : ivm[-5:,'mlt']
   Out[73]: 
   2012-12-29 00:40:13.119000    23.982937
   2012-12-29 00:40:14.119000    23.986605
   2012-12-29 00:40:15.119000    23.990273
   2012-12-29 00:40:16.119000    23.993940
   2012-12-29 00:40:17.119000    23.997608
   Name: mlt, dtype: float32

Pysat loads the next day of data to see if the last orbit on 12/28/12 extends into 12/29/12, which it does. Note that the last orbit of 12/28/12 is the same as the first orbit of 12/29/12. Thus, if we ask for the next orbit,

.. code:: ipython

   In[] : ivm.orbits.next()
   Loaded Orbit:2

pysat will indicate it is the second orbit of the day. Going back an orbit gives us orbit 16, but referenced to a different day. Earlier, the same orbit was labeled orbit 1.

.. code:: ipython

   In[] : ivm.orbits.prev()
   Returning cnofs ivm  data for 12/28/12
   Loaded Orbit:16

Orbit iteration is built into ivm.orbits just like iteration by day is built into ivm.

.. code:: python

   start = [pandas.datetime(2009,1,1), pandas.datetime(2010,1,1)]
   stop = [pandas.datetime(2009,4,1), pandas.datetime(2010,4,1)]
   ivm.bounds = (start, stop)
   for ivm in ivm.orbits:
       print 'next available orbit ', ivm.data

Iteration and Instrument Independent Analysis
---------------------------------------------

Now we can generalize daily_mean into two functions, one that averages by day, the other by  orbit. Strictly speaking, the daily_mean above already does this with the right input.

.. code:: python

   mean_daily_val = daily_mean(vefi, 'dB_mer')
   mean_orbit_val = daily_mean(vefi.orbits, 'dB_mer')

However, the output of the by_orbit attempt gets rewritten for most orbits since the output from daily_mean is stored by date. Though this could be fixed, supplying an instrument object/iterator in one case and an orbit iterator in the other might be a bit inconsistent. Even if not, let's try another route. 

We also don't want to maintain two code bases that do almost the same thing. So instead, let's create three functions, two of which simply call a hidden third.

**Iteration Independence**

.. code:: python

   def daily_mean(inst, data_label):
       """Mean of data_label by day/file over Instrument.bounds"""
       return _core_mean(inst, data_label, by_day=True)
    
   def by_orbit_mean(inst, data_label):
       """Mean of data_label by orbit over Instrument.bounds"""
       return _core_mean(inst, data_label, by_orbit=True)

   def _core_mean(inst, data_label, by_orbit=False, by_day=False):
    
       if by_orbit:
           iterator = inst.orbits
       elif by_day:
           iterator = inst
       else:
           raise ValueError('A choice must be made, by day/file, or by orbit')
       if by_orbit and by_day:
           raise ValueError('A choice must be made, by day/file, or by orbit')
             
       # create empty series to hold result
       mean_val = pandas.Series()
       # iterate over season, calculate the mean
       for inst in iterator:
	      if not inst.data.empty:
                  # compute mean absolute using pandas functions and store
                  # data could be an image, or lower dimension, account for 2D and lower
                  data = inst[data_label]
                  data.dropna(inplace=True)
               
                  if by_orbit:
                      date = inst.data.index[0]
                  else:
                      date = inst.date
        
                  data = pysat.utils.computational_form(data)
                  mean_val[date] = data.abs().mean(axis=0, skipna=True)

       del iterator               
       return mean_val

The addition of a few more lines to the daily_mean function adds support for averages by orbit, or by day, for any platform with data 3D or less. The date issue and the type of iteration are solved with simple if else checks. From a practical perspective, the code doesn't really deviate from the first solution of simply passing in vefi.orbits, except for the fact that the .orbits switch is 'hidden' in the code. NaN values are also dropped from the data. If the first element is a NaN, it isn't handled by the simple instance check.

A name change and a couple more dummy functions separates out the orbit vs daily iteration clearly, without having multiple codebases. Iteration by file and by date are handled by the same Instrument iterator, controlled by the settings in Instrument.bounds. A by_file_mean was not created because bounds could be set by date and then by_file_mean applied. Of course this could set up to produce an error. However, the settings on Instrument.bounds controls the iteration type between files and dates, so we maintain this view with the expressed calls. Similarly, the orbit iteration is a separate iterator, with a separate call. This technique above is used by other seasonal analysis routines in pysat.

You may notice that the mean call could also easily be replaced by a median, or even a mode. We might also want to return the standard deviation, or appropriate measure. Perhaps another level of generalization is needed?

Summary Flow Charts
-------------------

.. image:: ./images/pysat_load_flow_chart.png


  