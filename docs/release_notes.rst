
Release Notes
=============

.. toctree::

   CHANGELOG.rst

Narrative
---------

v3.0 Release
^^^^^^^^^^^^
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
into an ecosystem of packages
(https://github.com/pysat/pysat/wiki/Pysat-Ecosystem-Status-Chart).
The new ecosystem configuration ensures pysat has all of the features needed to
support external community-developed packages and decouples updates to
instrumentation from the pysat release schedule. A variety of improvements have
been implemented to support use in operational settings. Finally, pysat's data
handling capabilities have been improved.  pysat's leading file and data
handling features significantly reduces the time and effort required to perform
robust state-of-the-art scientific analyses. We encourage community
engagement with pysat v3.0.0, and look forward to supporting external
developers with their pysat-based packages for data handling or analysis.

Sincerely,

The pysat Development Team

- Dr. Russell Stoneback
- Dr. Angeline G. Burrell
- Dr. Jeff Klenzing
