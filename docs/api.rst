
API
===

Instrument
----------

.. autoclass:: pysat.Instrument
   :members:

Instrument Methods
------------------

The following methods support the variety of actions needed
by underlying pysat.Instrument modules.

.. _rst_general_data_general:

General
^^^^^^^

.. automodule:: pysat.instruments.methods.general
   :members:


Instrument Templates
--------------------

General Instrument
^^^^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.templates.template_instrument
   :members: __doc__, init, default, load, list_files, list_remote_files, download, clean

netCDF Pandas
^^^^^^^^^^^^^

.. automodule:: pysat.instruments.templates.netcdf_pandas
  :members: __doc__, init, load, list_files, download

Constellation
-------------

.. autoclass:: pysat.Constellation
   :members:

Custom
------

.. autoclass:: pysat.Custom
   :members:

Files
-----

.. autoclass:: pysat.Files
   :members:

Meta
----

.. autoclass:: pysat.Meta
   :members:

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
^^^^^^^^^^^
.. automodule:: pysat.utils.registry
   :members:

Time
^^^^^^^^^^^
.. automodule:: pysat.utils.time
   :members:

Testing
^^^^^^^^^^^
.. automodule:: pysat.utils.testing
   :members:
