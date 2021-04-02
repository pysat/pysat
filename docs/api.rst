.. _api:

API
===


.. _api-instrument:

Instrument
----------

.. autoclass:: pysat.Instrument
   :members:


.. _api-constellation:

Constellation
-------------

.. autoclass:: pysat.Constellation
   :members:


.. _api-files:

Files
-----

.. autoclass:: pysat.Files
   :members:


.. _api-meta:

Meta
----

.. autoclass:: pysat.Meta
   :members:


.. _api-metalabels:

MetaLabels
----------

.. autoclass:: pysat.MetaLabels
   :members:


.. _api-orbits:

Orbits
------

.. autoclass:: pysat.Orbits
   :members:


.. _api-params:

Parameters
----------

.. autoclass:: pysat._params.Parameters
   :members:



.. _api-instrument-methods:

Instrument Methods
------------------

The following methods support a variety of actions commonly needed by
pysat.Instrument modules regardless of the data source.


.. _api-methods-general:

General
^^^^^^^

.. automodule:: pysat.instruments.methods.general
   :members:


.. _api-methods-testing:

Testing
^^^^^^^

.. automodule:: pysat.instruments.methods.testing
   :members:


.. _api-utilities:

Utilities
---------
The utilites module contains functions used throughout the pysat package.
This includes utilities for determining the available Instruments, loading
files, et cetera.


.. _api-utils-core:

Core Utilities
^^^^^^^^^^^^^^
These utilities are available directly from the ``pysat.utils`` module.

.. automodule:: pysat.utils._core
   :members:


.. _api-utils-coords:

Coordinates
^^^^^^^^^^^
.. automodule:: pysat.utils.coords
   :members:


.. _api-utils-files:

Files
^^^^^
.. automodule:: pysat.utils.files
  :members:


.. _api-pysat-registry:

Registry
^^^^^^^^
.. automodule:: pysat.utils.registry
   :members:


.. _api-utils-time:

Time
^^^^
.. automodule:: pysat.utils.time
   :members:


.. _api-utils-testing:

Testing
^^^^^^^
.. automodule:: pysat.utils.testing
   :members:


.. _api-instrument-template:

Instrument Template
-------------------

.. automodule:: pysat.instruments.templates.template_instrument
   :members: __doc__, init, clean, preprocess, list_files, download, load, list_remote_files


.. _api-testinst:

Test Instruments
----------------

The following Instrument modules support unit and integration testing for
packages that depend on pysat.


.. _api-pysat-testing:

pysat_testing
^^^^^^^^^^^^^

.. automodule:: pysat.instruments.pysat_testing
   :members:


.. _api-pysat-testing_xarray:

pysat_testing_xarray
^^^^^^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.pysat_testing_xarray
   :members:


.. _api-pysat-testing2d:

pysat_testing2d
^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.pysat_testing2d
   :members:


.. _api-pysat-testing2d_xarray:

pysat_testing2d_xarray
^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.pysat_testing2d_xarray
   :members:


.. _api-pysat-testmodel:

pysat_testmodel
^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.pysat_testmodel
   :members:


.. _api-testconst:

Test Constellations
-------------------

The following Constellation modules support unit and integration testing for
packages that depend on pysat.


.. _api-const-testing:

Testing
^^^^^^^

.. automodule:: pysat.constellations.testing
   :members:


.. _api-const-single-test:

Single Test
^^^^^^^^^^^

.. automodule:: pysat.constellations.single_test
   :members:


.. _api-const-empty:

Testing Empty
^^^^^^^^^^^^^

.. automodule:: pysat.constellations.testing_empty
   :members:
