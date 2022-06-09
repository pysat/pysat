.. _rel_notes:

Release Notes
*************


.. _rel-narative:

Narrative
=========

.. _rel-narative-3.0.0:

v3.0.2 Release
--------------
The Python Satellite Data Analysis Toolkit (pysat) v3.0.2 release is a
substantive release intended to further improve support pysat in operational
envrionments as well as improve compatibility with an expanded range of files.
Sharing data is fundamental to a healthy scientific community thus pysat features
significant improvements to file reading, writing, metadata handling,
and filename parsing. Some of the file standards compatibility features have
been in use by active satellite missions but this update makes them accessible
to a broader audience, and consistent across Pandas and Xarray data types.

A future where the sky is filled with space-borne scientific instrumentation
may not be so far away. In preparation, the Constellation class, based
on a collection of Instruments, has a variety of improvements,
from improved compatibility with the Instrument class, as well
as features geared towards working with multiple data sets within the
Constellation. While the Constellation class is still early in its
development the foundation is being solidified here.


.. _rel-narative-3.0.0:

v3.0 Release
------------
The Python Satellite Data Analysis Toolkit (pysat) v3.0.0 release is a
substantive release intended to support pysat in operational environments,
as well as expand community oriented capabilities for space science data
analysis. While v3.0.0 is not backwards compatible due to a reorganization of
some functions and the data storage structure, the user interface is
largely unchanged.

pysat's original design demonstrated its ability to function as a nexus that
integrates the disparate space science data sources and analysis tools. However,
the monolithic configuration encouraged scope creep and obscured pysat's intent
to act as this common nexus, and in more practical terms, limited the frequency
of instrument support updates as data source providers altered systems.

These community oriented limitations have been addressed by breaking pysat up
into an :ref:`ecosystem` of packages. The new ecosystem configuration ensures
pysat has all of the features needed to support external community-developed
packages and decouples updates to instrumentation from the pysat release
schedule. A variety of improvements have been implemented to support use in
operational settings. Finally, pysat's data handling capabilities have been
improved.  pysat's leading file and data handling features significantly
reduces the time and effort required to perform robust state-of-the-art
scientific analyses. We encourage community engagement with pysat v3.0.0, and
look forward to supporting external developers with their pysat-based packages
for data handling or analysis.


.. _rel-narative-2.3.0:

v2.3 Release
------------
The Python Satellite Data Analysis Toolkit (pysat) v2.3.0 release is intended
to be the last release of the v2.x series and the last release to include
support for Python 2.x. pysat v2.3.0 primarily features DeprecationWarnings for
pysat functions that are changing as part of the 3.0.0 release. This version
also includes some of the changes employed for 3.0.0 so that some limited code
bases may work with both pysat 2.3.0 and 3.0.0. These include updating
:py:attr:`sat_id` to :py:attr:`inst_id` within :py:class:`pysat.Instrument`, as
well as including support for both the old and new methods for storing the
pysat data directory, namely :py:attr:`pysat.data_dir` and
:py:attr:`pysat.params['data_dirs']`.

.. mdinclude:: ../CHANGELOG.md
