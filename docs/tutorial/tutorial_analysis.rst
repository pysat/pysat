.. _tutorial-analysis:

Analysis
--------

Because pysat allows you to load and cycle through data from different
instruments in similar manners, it's easy to write instrument-independent
analysis routines.  Here we provide a simple example where a mean value is
calculated for the loaded data from an instrument.  As pysat allows data to be
iteratively loaded by the day or by orbit, the same method can produce different
results for the same instrument.

Sample Period Mean Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The code below creates a function called ``periodic_mean`` that takes either
a pysat Instrument or Orbits object connected to an Instrument and calculates
the mean every day or every orbit over the period of time supplied by
`bounds`.

.. code:: python

   import datetime as dt
   import pysat
   import pandas as pds

   def periodic_mean(inst_iterator, data_label):
       """ Calculate the periodic mean over a range of dates

       Parameters
       ----------
       inst_iterator : pysat.Instrument iterator
           Expecting either pysat.Instrument for daily or pysat.Orbits for
	     orbital periods
       data_label : str
           Instrument data label

       Returns
       -------
       mean_val : pds.Series
           Pandas time series containing periodic means of the desired value

       """
       # Create empty series to hold result
       mean_val = pds.Series()

       # Iterate over season, calculate the mean
       for inst in inst_iterator:
           if not inst.empty:
               # Compute mean absolute using pandas functions and store.  The
               # data could be an image, or lower dimension, account for 2D and
	           # lower
               data = inst[data_label].dropna()
               data_date = inst.data.index[0]
               mean_val[data_date] = data.mean()

       return mean_val

You may apply this function as demonstrated below.

.. code:: python

   import datetime as dt
   import pysatMadrigal

   stime = dt.datetime(2011, 12, 31)
   etime = dt.datetime(2012, 1, 2)
   orbit_info = {'kind': 'polar', 'index': 'gdlat'}
   f15 = pysat.Instrument(inst_module=pysatMadrigal.instruments.dmsp_ivm,
                          tag='utd', inst_id='f15', orbit_info=orbit_info,
			   clean_level='none', update_files=True)

   # Ensure the data is downloaded
   if len(f15.files[stime:etime + dt.timedelta(days=1)]) < 3:
       f15.download(start=stime, stop=etime, user='name', password='email')

   # Load and process the daily mean of the ion temperature
   f15.load(date=stime)
   f15.bounds = (stime, etime)
   daily_mean_ti = periodic_mean(f15, 'ti')
   print(daily_mean_ti)

   2011-12-31 00:00:05    2153.001641
   2012-01-01 00:02:09    2111.060398
   2012-01-02 00:00:05    2137.508402
   dtype: float64

   # Before running the orbital data, reload to start at the same place
   f15.load(date=stime)
   orbital_mean_ti = periodic_mean(f15.orbits, 'ti')
   print(orbital_mean_ti[:5])

   2011-12-31 00:00:05    2460.273183
   2011-12-31 00:28:05    2151.918103
   2011-12-31 01:18:57    2255.243570
   2011-12-31 02:09:49    1976.928571
   2011-12-31 03:00:41    2247.152299
   dtype: float64

   print(orbital_mean_ti[-5:])

   2012-01-02 20:17:25    2014.417630
   2012-01-02 21:08:17    2371.601671
   2012-01-02 21:59:09    2075.554252
   2012-01-02 22:50:05    2414.907781
   2012-01-02 23:40:57    2387.694853
   dtype: float64


The addition of a few more lines to the periodic_mean function could add
support for other types of statistics, or more complex processing.
