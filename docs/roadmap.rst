.. _roadmap:

Roadmap
=======

The long-term vision for pysat is to make the package suitable for working with
any combination of data. As pysat is intended to support the development of
highly robust and verifiable scientific analysis and processing packages, pysat
must produce each of its features with high quality unit tests and documentation.

This document provides a broad and long term vision of pysat. Specific tasks
associated with this roadmap may be found within the posted
`Issues <https://github.com/pysat/pysat/issues>`_ and
`Projects <https://github.com/pysat/pysat/projects>`_.

An item being on the roadmap does not mean that it will necessarily happen.
During the implementation or testing periods we may discover issues that limit
the feature.

Generality
----------
pysat's data support is currently focused on space-science data sets, however,
pysat's feature set works well on other types of data as well. Where appropriate,
space-science specific features will be generalized for a wider audience.

Data Support
~~~~~~~~~~~~
The Instrument class currently supports both pandas and xarray formats, covering
one and multi-dimensional data that can be loaded into memory. Even larger data
sets would require that pysat integrate a data format such as Dask. To cover the
needs of any potential user, an ideal solution would be for pysat to implement
a clear public mechanism for users to add their own data formats. Commonalities
observed after integrating dask, pandas, and xarray should provide a viable path
forward for this generalization.

Multiple Data Sources
~~~~~~~~~~~~~~~~~~~~~
The Instrument class is designed to work on a single data source at a time. For
multiple data sources pysat is developing a Constellation class that operates
on multiple Instrument objects and will include methods designed to assist in
merging multiple data sets together. The Constellation class will feature
compatibility with the simpler Instrument object when possible. However, given
the additional complexity when working with multiple sources this may not always
be possible. Long term, we intend on providing functionality that can merge a
Constellation into a 'live' Instrument object for greatest compatibility.

Metapackage
~~~~~~~~~~~
The minimal barriers to entry in open source software allows for a large
variety of packages, each with its own approach to a problem. A disadvantage
of the setup is the variety of packages may not have been developed with
interoperability in mind, presenting challenges when attempting to combine
these disparate packages towards a common goal. pysat's versatility when
coupling to data sources may be used to connect these isolated packages
together using pysat an intermediary. Once a package is connected to pysat
then that functionality becomes available to all packages that incorporate
pysat as a source. The value and functionality of this large scale pysat
metapackage increases exponentially with every new connection.

File Support
~~~~~~~~~~~~
pysat currently supports tracking both data and metadata, as well as the ability
to create netCDF4 files, and is capable of maintaining compliance with NASA's
Space Physics Data Facility (SPDF/ISTP) formatting requirements for NASA
satellite missions. Support for creating different types of files, as well as
a variety of file standards, needs to be enhanced to support a broader array of
research areas.

Data Iteration
~~~~~~~~~~~~~~
pysat currently features orbit iteration, a feature that transparently provides
complete orbits (across day/file breaks) calculated in real time. A variety
of orbit types are supported, each of which maps to a method looking for a
particular signal in the data to trigger upon. However, the current variety of
orbit types is insufficient to address community needs. The underlying class is
capable of iterating over a wider variety conditions though this type of
functionality is not currently available to users. Improving access to this
area enables generalized real-time data pagination based upon custom user
supplied conditions. Ensuring good performance under a variety of conditions
requires upgrading and generalizing pysat's data cacheing as well as the orbit
iteration interface.

Performance
~~~~~~~~~~~
While it is critical for scientific outputs to be correct, results that are
equally correct but calculated quicker make it easier for scientists to fully
explore a data set. A benchmarking solution will be implemented and used to
identify areas with slow performance that could potentially be improved upon.

Testing
~~~~~~~
Unit tests confirming pysat behaves as expected is fundamental to the scientific
goals of the project. While unit test coverage is high,  a general review of all
the unit tests needs to be performed. In particular, unit tests written early in
the project need to be brought up to project standards. The test suite needs
additional organization as many files are too long. Further, tests need to be
expanded to ensure that more combinations of features are engaged at once to
ensure interoperability.

User Experience
---------------
Providing a consistent, versatile, and easy to use interface is a core feature
for pysat.

Documentation
~~~~~~~~~~~~~
Robust, accurate, consistent, comprehensive, and easy to understand
documentation is essential for any project presented to the community to build
upon. While great strides were made with the release of pysat v3.0, additional
review and expansion of examples and discussion would be helpful to users.

pysatPenumbra Modules
~~~~~~~~~~~~~~~~~~~~~
The development of analysis packages built on pysat has historically revealed
areas for improvement. Active engagement with these publicly developed packages
helps ensure pysat's solutions are practical and responsive to community
requirements.
