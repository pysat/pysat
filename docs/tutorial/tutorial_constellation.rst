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
:py:data:`mag`, :py:data:`sis`, and :py:data:`swepam`.  The only
:py:class:`~pysat._instrument.Instrument` defining attributes that are not
unique are the :py:attr:`~pysat._instrument.Instrument.name` values.

Use a Constellation sub-module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some pysatEcosystem packages, such as :py:mod:`pysatNASA`, contain sub-modules
that specify commonly-used Constellations. This example uses the
`ICON Instruments <https://pysatnasa.readthedocs.io/en/latest/supported_constellations.html#icon>`_
to create a Constellation of ICON EUV, FUV, IVM, and MIGHTI data (excluding the
line-of-sight winds).

.. code:: python

          import pysat
          import pysatNASA

	  # Initalize the ICON Constellation using the ICON module
	  icon = pysat.Constellation(cont_module=pysatNASA.constellations.icon)

	  # Display the results
	  print(icon)

The last command will show that nine :py:class:`~pysat._instrument.Instrument`
objects were loaded by the module: both IVM instruments, the EUV instrument, the
day- and night-time FUV data, and four of the MIGHTI data products.

Converting to an Instrument
---------------------------

At a certain point in your data analysis, it may be desirable to convert your
:py:class:`~pysat._constellation.Constellation` into an
:py:class:`~pysat._instrument.Instrument`. This functionality is supported by
the class method :py:meth:`~pysat._constellation.Constellation.to_inst`.  Let
us use the ACE realtime data Constellation in this example.

.. code:: python

	  # Download today's data and load it into the Constellation
	  ace_rt.download()
	  ace_rt.load(date=ace_rt.today())

	  # Convert the output to an Instrument
	  rt_inst = ace_rt.to_inst()
	  print(rt_inst)

This yeilds:
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
