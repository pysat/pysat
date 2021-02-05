
API
===

Instrument
----------

.. autoclass:: pysat.Instrument
   :members:

Instrument Methods
------------------

The following methods support a variety of actions commonly needed by
pysat.Instrument modules regardless of the data source.

.. _rst_general_data_general:

General
^^^^^^^

.. automodule:: pysat.instruments.methods.general
   :members:

.. _api-instrument-template:

Instrument Template
-------------------

.. automodule:: pysat.instruments.templates.template_instrument
   :members: __doc__, init, clean, preprocess, list_files, download, load, list_remote_files

Constellation
-------------

.. autoclass:: pysat.Constellation
   :members:

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

Utilities
---------
.. automodule:: pysat.utils
   :members:

Coordinates
^^^^^^^^^^^
.. automodule:: pysat.utils.coords
   :members:

Files
^^^^^
.. automodule:: pysat.utils.files
  :members:

Registry
^^^^^^^^
.. automodule:: pysat.utils.registry
   :members:

Time
^^^^
.. automodule:: pysat.utils.time
   :members:

Testing
^^^^^^^
.. automodule:: pysat.utils.testing
   :members:

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
