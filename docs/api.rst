
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

Demeter
^^^^^^^

.. automodule:: pysat.instruments.methods.demeter
   :members: __doc__, download, bytes_to_float, load_general_header, load_location_parameters, load_attitude_parameters, load_binary_file, set_metadata


.. _rst_general_data_general:

General
^^^^^^^

.. automodule:: pysat.instruments.methods.general
   :members:

.. _rst_general_data_cdaweb:

NASA CDAWeb
^^^^^^^^^^^

.. automodule:: pysat.instruments.methods.nasa_cdaweb
   :members: __doc__, load, list_files, list_remote_files, download

.. _rst_general_data_madrigal:

NASA ICON
^^^^^^^^^

.. automodule:: pysat.instruments.methods.icon
   :members:

Madrigal
^^^^^^^^

.. automodule:: pysat.instruments.methods.madrigal
   :members: __doc__, cedar_rules, load, download, filter_data_single_date

Space Weather
^^^^^^^^^^^^^

.. automodule:: pysat.instruments.methods.sw
   :members:

Instrument Templates
--------------------

General Instrument
^^^^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.templates.template_instrument
   :members: __doc__, init, default, load, list_files, list_remote_files, download, clean

Madrigal Pandas
^^^^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.templates.netcdf_pandas
  :members: __doc__, init, load, list_files, download

NASA CDAWeb Instrument
^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pysat.instruments.templates.template_cdaweb_instrument
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

Statistics
^^^^^^^^^^
.. automodule:: pysat.utils.stats
   :members:

Time
^^^^^^^^^^^
.. automodule:: pysat.utils.time
   :members:
