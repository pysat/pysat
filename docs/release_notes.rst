
Release Notes
*************

Narrative
=========

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
into an :ref:`ecosystem` of packages.
The new ecosystem configuration ensures pysat has all of the features needed to
support external community-developed packages and decouples updates to
instrumentation from the pysat release schedule. A variety of improvements have
been implemented to support use in operational settings. Finally, pysat's data
handling capabilities have been improved.  pysat's leading file and data
handling features significantly reduces the time and effort required to perform
robust state-of-the-art scientific analyses. We encourage community
engagement with pysat v3.0.0, and look forward to supporting external
developers with their pysat-based packages for data handling or analysis.

v2.3 Release
------------
The Python Satellite Data Analysis Toolkit (pysat) v2.3.0 release is intended
to be the last release of the v2.x series and the last release to
include support for Python 2.x. pysat v2.3.0 primarily features
DeprecationWarnings for pysat functions that are changing as part
of the 3.0.0 release. This version also includes some of the changes
employed for 3.0.0 so that some limited code bases may work with both
pysat 2.3.0 and 3.0.0. These include updating `sat_id` to `inst_id` within
`pysat.Instrument`, as well as including support for both the old and new methods
for storing the pysat data directory, namely `pysat.data_dir` and
`pysat.params['data_dirs']`.

.. mdinclude:: ../CHANGELOG.md
