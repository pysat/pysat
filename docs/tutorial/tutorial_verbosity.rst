.. _tutorial-verb:

Verbosity
---------

:py:mod:`pysat` uses Python's standard
`logging tools <https://docs.python.org/3/library/logging.html>`_
to control the verbosity of output. By default only logger.warning messages
are shown. For more detailed output you may change the logging level.

.. code:: python

  import logging
  import pysat
  pysat.logger.set_level(logging.INFO)

The logging level will be applied to all :py:class:`~pysat.Instrument` data
loaded by :py:mod:`pysat` and to analysis tools run by the pysat penumbra
packages.  If you try to update the logger level after doing anything with
:py:mod:`pysat` in an interactive session, it may not work.
