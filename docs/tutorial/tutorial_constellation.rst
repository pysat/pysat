.. _tutorial-const:

Using Constellations
====================

The :py:class:`pysat.Constellation` class is an alternative to the
:py:class:`pysat.Instrument` class.  It contains multiple
:py:class:`pysat.Instrument` objects and allows quicker processing and analysis
on multiple data sets.

.. _tutorial-const-init:

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
:py:data:`mag`, :py:data:`sis`, and :py:data:`swepam`.  The only
:py:class:`~pysat._instrument.Instrument` defining attributes that are not
unique are the :py:attr:`~pysat._instrument.Instrument.name` values.

Use a Constellation sub-module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some pysatEcosystem packages, such as :py:mod:`pysatNASA`, contain sub-modules
that specify commonly-used Constellations. This example uses the
`DE2 Instruments <https://pysatnasa.readthedocs.io/en/latest/supported_constellations.html#de2>`_
to create a Constellation of Dynamics Explorer 2 LANG, NACS, RPA, and WATS
instruments.

.. code:: python

    import pysat
    import pysatNASA

    # Initalize the DE2 Constellation using the DE2 constellation module
    de2 = pysat.Constellation(const_module=pysatNASA.constellations.de2)

    # Display the results
    print(de2)

The last command will show that nine :py:class:`~pysat._instrument.Instrument`
objects were loaded by the module.


.. _tutorial-const-shared:

Properties shared with Instruments
----------------------------------

Just as with a :py:class:`~pysat._instrument.Instrument` object, a
:py:class:`~pysat._constellation.Constellation` object will download and load
data using the :py:meth:`~pysat._constellation.Constellation.download` and
:py:meth:`~pysat._constellation.Constellation.load` methods.

.. code:: python
  
    # Download today's data and load it into the Constellation
    ace_rt.download()
    ace_rt.load(date=ace_rt.today())

This will download data for all :py:class:`~pysat._constellation.Constellation`
:py:class:`~pysat._instrument.Instrument` objects into their appropriate
directories and then load the data for each
:py:class:`~pysat._instrument.Instrument`.

Other :py:class:`~pysat._instrument.Instrument` properties and methods, such as
the loaded date, list of variables, custom function methods, and bounds behave
the same for the :py:class:`~pysat._constellation.Constellation` object.


.. _tutorial-const-unique:

Properties differing from Instruments
-------------------------------------
:py:class:`~pysat._constellation.Constellation` also contains attributes that
are unique to this object or differ slightly from their
:py:class:`~pysat._instrument.Instrument` counterparts due to differing needs.

Time index
^^^^^^^^^^
For example, there is an :py:attr:`~pysat._constellation.Constellation.index`
attribute, but as this must represent times for all the desired
:py:class:`~pysat._instrument.Instrument` objects, this may not exactly match
the individual :py:attr:`~pysat._instrument.Instrument.index` objects.  There
are two additional attributes that inform how this time index is constructed:
:py:attr:`~pysat._constellation.Constellation.common_index` and
:py:attr:`~pysat._constellation.Constellation.index_res`. If
:py:attr:`~pysat._constellation.Constellation.common_index` is ``True``,
only times present in all :py:class:`~pysat._instrument.Instrument` objects
are included in :py:attr:`~pysat._constellation.Constellation.index`.  If
:py:attr:`~pysat._constellation.Constellation.common_index` is ``False``,
the maximum time range is used instead.
:py:attr:`~pysat._constellation.Constellation.index_res` provides the
:py:attr:`~pysat._constellation.Constellation.index` resolution, if it is not
``None``.  If it is ``None``, then an appropriate resolution is established from
the individual :py:attr:`~pysat._instrument.Instrument.index` objects.  It is
standard to have :py:attr:`~pysat._constellation.Constellation.common_index` be
``True`` and :py:attr:`~pysat._constellation.Constellation.index_res` set to
``None``.

Empty flags
^^^^^^^^^^^
A :py:class:`~pysat._constellation.Constellation` has more states of having
data loaded than merely ``True`` or ``False``; it is possible for only some of
the desired :py:class:`~pysat._instrument.Instrument` objects to have data.
To address this issue, there are two
:py:class:`~pysat._constellation.Constellation` attributes that address the
presence of loaded data: :py:attr:`~pysat._constellation.Constellation.empty`
and :py:attr:`~pysat._constellation.Constellation.empty_partial`.  If ``True``,
:py:attr:`~pysat._constellation.Constellation.empty` indicates that no data
is loaded.  If :py:attr:`~pysat._constellation.Constellation.empty_partial`
is ``True`` and :py:attr:`~pysat._constellation.Constellation.empty` is
``False``, some data is loaded.  If both
:py:attr:`~pysat._constellation.Constellation.empty_partial` and
:py:attr:`~pysat._constellation.Constellation.empty` are ``False``, then all
:py:class:`~pysat._instrument.Instrument` objects have data.

Instrument access
^^^^^^^^^^^^^^^^^
You can access all the standard :py:class:`~pysat._instrument.Instrument`
attributes through the
:py:attr:`~pysat._constellation.Constellation.instruments` attribute.

.. code:: python

    # Cycle through each ACE Real Time Instrument and print the most recent
    # filename
    for i, inst in enumerate(ace_rt.instruments):
        print(ace_rt.names[i], inst.files.files[-1])

This should yield a list of ACE :py:attr:`~pysat._instrument.Instrument.name`
attributes and their files with the current or tomorrow's date. List attributes
that provide information about the individual
:py:class:`~pysat._constellation.Constellation`
:py:class:`~pysat._instrument.Instrument` objects include:
:py:attr:`~pysat._constellation.Constellation.platforms`,
:py:attr:`~pysat._constellation.Constellation.names`,
:py:attr:`~pysat._constellation.Constellation.tags`, and
:py:attr:`~pysat._constellation.Constellation.inst_ids`.

.. _tutorial-const-to-inst:

Converting to an Instrument
---------------------------

At a certain point in your data analysis, it may be desirable to convert your
:py:class:`~pysat._constellation.Constellation` into an
:py:class:`~pysat._instrument.Instrument`. This functionality is supported by
the class method :py:meth:`~pysat._constellation.Constellation.to_inst`.  Let
us use the ACE realtime data Constellation in this example.

.. code:: python

    # Convert the output to an Instrument
    rt_inst = ace_rt.to_inst()
    print(rt_inst)

This yields:
::

  pysat Instrument object
  -----------------------
  Platform: 'ace'
  Name: 'swepam_mag_epam_sis'
  Tag: 'realtime'
  Instrument id: ''

  Data Processing
  ---------------
  Cleaning Level: 'clean'
  Data Padding: None
  Keyword Arguments Passed to list_files: {}
  Keyword Arguments Passed to load: {}
  Keyword Arguments Passed to preprocess: {}
  Keyword Arguments Passed to download: {}
  Keyword Arguments Passed to list_remote_files: {}
  Keyword Arguments Passed to clean: {}
  Keyword Arguments Passed to init: {}
  Custom Functions: 0 applied

  Local File Statistics
  ---------------------
  Number of files: 0


  Loaded Data Statistics
  ----------------------
  Date: 09 January 2023
  DOY: 009
  Time range: 09 January 2023 15:15:00 --- 09 January 2023 16:45:00
  Number of Times: 91
  Number of variables: 33

  Variable Names:
  jd_ace_epam_realtime  sec_ace_epam_realtime status_e              
                               ...                                
  sw_proton_dens        sw_bulk_speed         sw_ion_temp           

  pysat Meta object
  -----------------
  Tracking 7 metadata values
  Metadata for 33 standard variables
  Metadata for 0 ND variables
  Metadata for 0 global attributes

Currently, if you wish to save your modified
:py:class:`~pysat._constallation.Constallation` data to a NetCDF file, you must
first convert it to an :py:class:`~pysat._instrument.Instrument` using
:py:meth:`~pysat._constallation.Constallation.to_inst`.  From there, you may
use :py:meth:`~pysat._instrument.Instrument.to_netcdf4` to create a NetCDF file.
