.. _instruments-testing:


Test Instruments
----------------

The following Instrument modules support unit and integration testing for
packages that depend on pysat.


pysat_testing
^^^^^^^^^^^^^
An instrument with satellite-like data as a function of latitude, longitude,
and altitude in a pandas format. See :ref:`api-pysat-testing` for more details.


pysat_ndtesting
^^^^^^^^^^^^^^^
An instrument with satellite-like data like :py:mod:`pysat_testing` that
also has an imager-like 3D data variable. See :ref:`api-pysat-ndtesting`
for more details.


pysat_testmodel
^^^^^^^^^^^^^^^
An instrument with model-like data that returns a 4D object as a function of
latitude, longitude, altitude, and time. See :ref:`api-pysat-testmodel` for more
details.
