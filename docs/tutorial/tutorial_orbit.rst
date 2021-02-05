Orbit Support
=============

pysat has functionality to determine orbits on the fly from loaded data.
These orbits will span day breaks as needed (generally). To use any of
these orbit features, information about
the orbit needs to be provided at initialization. The 'index' is the name of
the data to be used for determining orbits, and 'kind' indicates type of orbit.
See :any:`pysat.Orbits` for latest inputs.

There are several orbits to choose from,

===========   ================
**kind**	**method**
-----------   ----------------
local time     Uses negative gradients to delineate orbits
longitude      Uses negative gradients to delineate orbits
polar	       Uses sign changes to delineate orbits
orbit          Uses any change in value to delineate orbits
===========   ================

Changes in universal time are also used to delineate orbits. pysat compares any
gaps to the supplied orbital period, nominally assumed to be 97 minutes. As
orbit periods aren't constant, a 100% success rate is not be guaranteed.

.. code:: python

   info = {'index': 'mlt', 'kind': 'local time'}
   ivm = pysat.Instrument(platform='cnofs', name='ivm', orbit_info=info,
                          clean_level='None')

Orbit determination acts upon data loaded in the ivm object, so to begin we
must load some data.

.. code:: python

   ivm.load(date=start)

Orbits may be selected directly from the attached ``ivm.orbits`` class.
The data for the orbit is stored in ``ivm.data``.

.. code:: ipython

   ivm.orbits[1]

   Returning cnofs ivm  data for 12/27/12
   Returning cnofs ivm  data for 12/28/12
   Loaded Orbit:0

Note that getting the first orbit caused pysat to load the day previous, and
then back to the current day. Orbits are zero indexed.
pysat is checking here if the first orbit for 12/28/2012 actually started on
12/27/2012. In this case it does.

.. code:: ipython

   ivm[0:5, 'mlt']

   2012-12-27 23:05:14.584000    0.002449
   2012-12-27 23:05:15.584000    0.006380
   2012-12-27 23:05:16.584000    0.010313
   2012-12-27 23:05:17.584000    0.014245
   2012-12-27 23:05:18.584000    0.018178
   Name: mlt, dtype: float32

   ivm[-5:, 'mlt']

   2012-12-28 00:41:50.563000    23.985415
   2012-12-28 00:41:51.563000    23.989031
   2012-12-28 00:41:52.563000    23.992649
   2012-12-28 00:41:53.563000    23.996267
   2012-12-28 00:41:54.563000    23.999886
   Name: mlt, dtype: float32

You can also go back an orbit.

.. code:: ipython

   ivm.orbits.prev()

   Returning cnofs ivm  data for 12/27/12
   Loaded Orbit:15

   ivm[-5:, 'mlt']

   2012-12-27 23:05:09.584000    23.982796
   2012-12-27 23:05:10.584000    23.986725
   2012-12-27 23:05:11.584000    23.990656
   2012-12-27 23:05:12.584000    23.994587
   2012-12-27 23:05:13.584000    23.998516
   Name: mlt, dtype: float32

pysat loads the previous day, as needed, and returns the last orbit for
12/27/2012 that does not (or should not) extend into 12/28.

If we continue to iterate orbits using

.. code:: python

   ivm.orbits.next()

eventually the next day will be loaded to try and form a complete orbit. You
can skip the iteration and just go for the last orbit of a day,

.. code:: ipython

   ivm.orbits[-1]

   Returning cnofs ivm  data for 12/29/12
   Loaded Orbit:1

.. code:: ipython

   ivm[:5, 'mlt']

   2012-12-28 23:03:34.160000    0.003109
   2012-12-28 23:03:35.152000    0.007052
   2012-12-28 23:03:36.160000    0.010996
   2012-12-28 23:03:37.152000    0.014940
   2012-12-28 23:03:38.160000    0.018884
   Name: mlt, dtype: float32

   ivm[-5:, 'mlt']

   2012-12-29 00:40:13.119000    23.982937
   2012-12-29 00:40:14.119000    23.986605
   2012-12-29 00:40:15.119000    23.990273
   2012-12-29 00:40:16.119000    23.993940
   2012-12-29 00:40:17.119000    23.997608
   Name: mlt, dtype: float32

pysat loads the next day of data to see if the last orbit on 12/28/12 extends
into 12/29/12, which it does. Note that the last orbit of 12/28/12 is the same
as the first orbit of 12/29/12. Thus, if we ask for the next orbit,

.. code:: ipython

   ivm.orbits.next()

   Loaded Orbit:2

pysat will indicate it is the second orbit of the day. Going back an orbit
gives us orbit 16, but referenced to a different day. Earlier, the same orbit
was labeled orbit 1.

.. code:: ipython

   ivm.orbits.prev()

   Returning cnofs ivm  data for 12/28/12
   Loaded Orbit:16

Orbit iteration is built into ivm.orbits just like iteration by day is built
into ivm.

.. code:: python

   start = [pandas.datetime(2009, 1, 1), pandas.datetime(2010, 1, 1)]
   stop = [pandas.datetime(2009, 4, 1), pandas.datetime(2010, 4, 1)]
   ivm.bounds = (start, stop)
   for ivm in ivm.orbits:
       print 'next available orbit ', ivm.data

Ground Based Instruments
------------------------

The nominal breakdown of satellite data into discrete orbits isn't typically
as applicable for ground based instruments, each of which makes exactly one
orbit per day. However, as the orbit iterator triggers off of
negative gradients in a variable, a change in sign, or any change
in a value, this functionality may be used to break a ground based data set
into alternative groupings, as appropriate and desired.

As the orbit iterator defaults to an orbit period consistent with Low
Earth Orbit, the expected period of the 'orbits' must be provided at
Instrument instantiation. Given the orbit heritage, it is assumed that
there is a small amount of variation in the orbit period. pysat will actively
filter 'orbits' that are inconsistent with the prescribed orbit period.
