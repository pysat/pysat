.. _ecosystem:

Ecosystem
#########

The pysat project supports both data-centric packages that primarily support
the retrieval, management, and input/output aspects of the scientific workflow
and analysis packages that provide task-specific tools.

The status of pysat supported packages can be found at the
`ecosystem status chart <https://github.com/pysat/pysat/wiki/Pysat-Ecosystem-Status-Chart>`_.


.. _eco-inst:

Supported Instruments
=====================

pysat supports many different data sets as Instruments and Constellations.
Similar types of data and data from the same data repository are grouped
together into separate packages. This reduces the amount of dependencies you
may need to install, when you only want to use a small subset of the data pysat
currently supports.

.. toctree::
   :maxdepth: 2

   instruments/testing_instruments.rst
   instruments/pysatCDAAC.rst
   instruments/pysatMadrigal.rst
   instruments/pysatMissions.rst
   instruments/pysatModels.rst
   instruments/pysatNASA.rst
   instruments/pysatSpaceWeather.rst
   instruments/pysatIncubator.rst


.. _eco-tools:

Analysis Tools
==============

The packages listed below provide useful tools for data analysis.

.. toctree::
   :maxdepth: 2

   analysis/pysatMissions.rst
   analysis/pysatModels.rst
   analysis/pysatSeasons.rst
   analysis/pysatSpaceWeather.rst
