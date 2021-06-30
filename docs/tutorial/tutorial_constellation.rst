.. _tutorial-const:

Using Constellations
====================

The :py:class:`pysat.Constellation` class is an alternative to the
:py:class:`pysat.Instrument` class.  It contains multiple
:py:class:`pysat.Instrument` objects and allows quicker processing and analysis
on multiple data sets.

Initialization
--------------

There are several ways of initializing a
:py:class:`~pysat._constellation.Constellation` object, which may be used
individually or in combination.

Specify Registered Instruments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One way to initialize a :py:class:`~pysat._constellation.Constellation` is to
specify lists of desired common :py:class:`~pysat._instrument.Instrument`
:py:attr:`platform`, :py:attr:`name`, :py:attr:`tag`, and :py:attr:`inst_id`
values.  pysat will search the directory of registered (see
:ref:`api-pysat-registry`) :py:class:`~pysat._instrument.Instrument` modules and
load all possible matches.  This example uses the
`pysatSpaceWeather ACE Instruments <https://pysatspaceweather.readthedocs.io/en/latest/supported_instruments.html#ace>`_
to create a Constellation of real-time solar wind data.

.. code:: python

          import pysat
          import pysatSpaceWeather

          # If you haven't registered this module before, do it now
          pysat.utils.registry.register_by_module(pysatSpaceWeather.instruments)

          # Now initialize the ACE real-time Constellation
          ace_rt = pysat.Constellation(platforms=['ace'], tags=['realtime'])

          # Display the results
          print(ace_rt)

This last command will show that four :py:class:`~pysat._instrument.Instrument`
objects match the desired :py:attr:`platform` and :py:attr:`tag` criteria.
The :py:attr:`~pysat._instrument.Instrument.name` values are: :py:data:`epam`,
:py:data:`mag`, :py:data:`sis`, and :py:data:`swepam`.
