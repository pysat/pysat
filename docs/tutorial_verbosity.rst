Verbosity
---------

Pysat uses Python's standard
`logging tools <https://docs.python.org/3/library/logging.html>`_
to control the verbosity of output. By default, only logger.warning messages
are shown. For more detailed instrument output, you may change the
logging level.

.. code:: python

   from pysat import logger, logging
   logger.set_level(logging.INFO)

The logging level will be applied to all instruments loaded by pysat.
