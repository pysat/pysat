.. _tutorial-orbit:

Orbit Support
=============

pysat can break satellite data into single orbits on the fly.
These orbits will typically span day breaks, if  needed.  The :ref:`api-orbits`
class, which is treated as a subclass of the Instrument object performs these
operations.

pysat, by default, does not bother to calculate any type of orbit.  To use the
orbital methods, information about the orbit needs to be provided at Instrument
initialization. The 'index' is the name of the data to be used for determining
orbits, and 'kind' indicates type of orbit. There are several orbits to choose
from.

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
orbit periods aren't constant, a 100% success rate cannot be guaranteed.

.. code:: python

   import datetime as dt
   import pysat
   import pysatMadrigal

   # Set the type of orbit we want in the Instrument
   orbit_info = {'index': 'gdlat', 'kind': 'polar'}
   f15 = pysat.Instrument(inst_module=pysatMadrigal.instruments.dmsp_ivm,
                          tag='utd', inst_id='f15', orbit_info=orbit_info,
                          clean_level='none')


Orbit determination acts upon data loaded in the ivm object, so to begin we
must load some data (first downloading it if necessary).

.. code:: python

   day1 = dt.datetime(2011, 12, 31)
   day2 = day1 + dt.timedelta(days=1)
   if len(f15.files[day1:day2 + dt.timedelta(days=2)]) < 3:
       # Download stop time is inclusive
       f15.download(start=day1, stop=day2 + dt.timedelta(days=1),
                    user="Name", password="email")

   # To ensure we have a complete first orbit
   f15.load(date=day2)
   print(f15.index[0], f15.index[-1])

   2012-01-01 00:02:09 2012-01-02 00:00:01


Orbits may be selected directly from the attached ``f15.orbits`` class.
The data for the orbit is stored in ``f15.data``.

.. code:: ipython

   f15.orbits[0]
   print(f15.index[0], f15.index[-1])

   2011-12-31 22:30:37 2011-12-31 22:31:05

   f15.orbits[1]
   print(f15.index[0], f15.index[-1])

   2012-01-01 00:02:09 2012-01-01 00:12:17


Note that getting the first orbit caused pysat to load the day previous, and
then back to the current day.  There is also a data gap over the change of the
year that makes these first two orbits shorter than expected.

Now, you can also move forward an orbit using the ``next`` command:

.. code:: ipython

   f15.orbits.next()
   print(f15.index[0], f15.index[-1])

   2012-01-01 01:03:13 2012-01-01 01:54:01

And back an orbit using the ``prev`` command:

.. code:: ipython

   f15.orbits.prev()
   print(f15.index[0], f15.index[-1])

   2012-01-01 00:12:21 2012-01-01 01:03:09

If we continue to iterate orbits using ``f15.orbits.next()`` the next day will
eventually be loaded to try and form a complete orbit. You can skip the
iteration and just go for the last orbit of a day using indexing:

.. code:: ipython

   f15.orbits[-1]
   print(f15.index[0], f15.index[-1])

   2012-01-01 23:56:41 2012-01-02 00:47:25


pysat loads the next day of data to see if the last orbit on 1 Jan 2012 extends
into 2 Jan 2012, which it does. Note that the last orbit of 1 Jan 2012 is the
same as the first orbit of 2 Jan 2012. Thus, if we ask for the next orbit,

.. code:: ipython

   f15.orbits.next()
   print(f15.orbits)

   Orbit Settings
   --------------
   Orbit Kind: 'polar'
   Orbit Index: 'gdlat'
   Orbit Period: Timedelta('0 days 01:37:00')
   Number of Orbits: 29
   Loaded Orbit Number: 2


pysat will indicate it is the second orbit of the day. Going back an orbit
gives us orbit 30, but referenced to a different day. If 2 Jan 2012 had been
loaded, this would be labeled orbit 1.

.. code:: ipython

   f15.orbits.prev()
   print(f15.orbits)

   Orbit Settings
   --------------
   Orbit Kind: 'polar'
   Orbit Index: 'gdlat'
   Orbit Period: Timedelta('0 days 01:37:00')
   Number of Orbits: 30
   Loaded Orbit Number: 30

Orbit iteration is built into f15.orbits just like daily iteration is built
into f15 (see :ref:`tutorial-iter`).

.. code:: python

   f15.load(dat=day1)
   f15.bounds = (day1, day2)
   for f15 in f15.orbits:
       print('next available orbit ', f15.data)

   next available orbit starts at:  2011-12-31 00:00:05
   next available orbit starts at:  2011-12-31 00:28:05
   next available orbit starts at:  2011-12-31 01:18:57
   next available orbit starts at:  2011-12-31 02:09:49
   next available orbit starts at:  2011-12-31 03:00:41
   next available orbit starts at:  2011-12-31 03:51:33
   next available orbit starts at:  2011-12-31 04:42:25
   next available orbit starts at:  2011-12-31 05:33:17
   next available orbit starts at:  2011-12-31 06:24:09
   next available orbit starts at:  2011-12-31 07:15:01
   next available orbit starts at:  2011-12-31 08:05:57
   next available orbit starts at:  2011-12-31 08:56:45
   next available orbit starts at:  2011-12-31 09:47:37
   next available orbit starts at:  2011-12-31 10:38:29
   next available orbit starts at:  2011-12-31 11:29:21
   next available orbit starts at:  2011-12-31 12:20:13
   next available orbit starts at:  2011-12-31 13:11:05
   next available orbit starts at:  2011-12-31 14:01:57
   next available orbit starts at:  2011-12-31 14:52:53
   next available orbit starts at:  2011-12-31 15:43:41
   next available orbit starts at:  2011-12-31 16:34:33
   next available orbit starts at:  2011-12-31 17:25:25
   next available orbit starts at:  2011-12-31 18:16:17
   next available orbit starts at:  2011-12-31 19:07:09
   next available orbit starts at:  2011-12-31 19:58:05
   next available orbit starts at:  2011-12-31 20:48:57
   next available orbit starts at:  2011-12-31 21:39:45
   next available orbit starts at:  2011-12-31 22:30:37
   next available orbit starts at:  2012-01-01 00:02:09
   next available orbit starts at:  2012-01-01 00:12:21
   next available orbit starts at:  2012-01-01 01:03:13
   next available orbit starts at:  2012-01-01 01:54:05
   next available orbit starts at:  2012-01-01 02:44:57
   next available orbit starts at:  2012-01-01 03:35:49
   next available orbit starts at:  2012-01-01 04:26:41
   next available orbit starts at:  2012-01-01 05:17:33
   next available orbit starts at:  2012-01-01 06:08:29
   next available orbit starts at:  2012-01-01 06:59:17
   next available orbit starts at:  2012-01-01 07:50:09
   next available orbit starts at:  2012-01-01 08:41:01
   next available orbit starts at:  2012-01-01 09:31:57
   next available orbit starts at:  2012-01-01 10:22:45
   next available orbit starts at:  2012-01-01 11:13:41
   next available orbit starts at:  2012-01-01 12:04:29
   next available orbit starts at:  2012-01-01 12:55:21
   next available orbit starts at:  2012-01-01 13:46:13
   next available orbit starts at:  2012-01-01 14:37:05
   next available orbit starts at:  2012-01-01 15:27:57
   next available orbit starts at:  2012-01-01 16:18:53
   next available orbit starts at:  2012-01-01 17:09:41
   next available orbit starts at:  2012-01-01 18:00:33
   next available orbit starts at:  2012-01-01 18:51:25
   next available orbit starts at:  2012-01-01 19:42:17
   next available orbit starts at:  2012-01-01 20:33:09
   next available orbit starts at:  2012-01-01 21:24:05
   next available orbit starts at:  2012-01-01 22:14:57
   next available orbit starts at:  2012-01-01 23:05:49
   next available orbit starts at:  2012-01-01 23:56:41


Ground-Based Instruments
------------------------

The nominal breakdown of satellite data into discrete orbits isn't typically
as applicable for ground based instruments, each of which makes exactly one
geostationary orbit per day. However, as the orbit iterator triggers off of
negative gradients in a variable, a change in sign, or any change
in a value, this functionality may be used to break a ground based data set
into alternative groupings, as appropriate and desired.

However, should you decide to try and use the Orbit class to break up
ground-based data, keep in mind that the orbit iterator defaults to an orbit
period consistent with Low Earth Orbit at Earth.  This means that the expected
period of the 'orbits' must be provided at Instrument instantiation. Given the
orbit heritage, it is assumed that there is a small amount of variation in the
orbit period. pysat will actively filter 'orbits' that are inconsistent with
the prescribed orbit period.
