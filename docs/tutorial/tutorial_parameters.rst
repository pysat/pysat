.. _tutorial-params:

Parameters
==========

The ``pysat.params`` class provides a central location for storing a variety
of parameters used by pysat as well as custom user provided settings. An
overview of currently stored parameters may be found using

.. code:: python

   import pysat
   print(pysat.params)

   Out[]:
   pysat Parameters object
   ----------------------
   Tracking 7 pysat settings
   Tracking 1 settings (non-default)
   Tracking 0 user values

   Standard parameters:
   clean_level : clean
   directory_format : {platform}/{name}/{tag}/{inst_id}
   ignore_empty_files : False
   file_timeout : 10
   update_files : True
   user_modules : {'sw': {'dst': 'pysatSpaceWeather.instruments.sw_dst',
                          'f107': 'pysatSpaceWeather.instruments.sw_f107',
                          'kp': 'pysatSpaceWeather.instruments.sw_kp',
                          'ace': 'pysatSpaceWeather.instruments.sw_ace'}}
   warn_empty_file_list : False

   Standard parameters (no defaults):
   data_dirs : ['/Users/tutorial_users/ScienceData']

   User parameters:

Most parameters may be assigned or updated via standard assignment
and are stored to disk automatically in a thread-safe manner

.. code:: python

   # Update existing file_timeout parameter
   pysat.params['file_timeout'] = 15

   # Add new user parameter
   pysat.params[user_param_str] = user_param_value

All of the standard parameters above may be restored to defaults using

.. code:: python

   pysat.params.restore_defaults()

but this command leaves parameters with no working defaults, like ``data_dirs``
unchanged. To clear all parameters,

.. code:: python

   pysat.params.clear_and_restart()

A description of each of the parameters and its use in pysat may be found
using

.. code::

   help(pysat.params)

   Default parameters and values tracked by this class:
       Values that map to the corresponding keywords on pysat.Instrument.
            'clean_level' : 'clean'
            'directory_format' : os.path.join('{platform}', '{name}',
                                              '{tag}', '{inst_id}')
            'ignore_empty_files': False
            'update_files': True

       Values that map to internal pysat settings:
            'file_timeout': 10; Window in time (seconds) that pysat will wait
                to load/write a file while another thread uses that file
                before giving up.
            'user_modules' : {}; Stores information on modules registered within
                pysat. Used by `pysat.utils.registry`
            'warn_empty_file_list' : False; Raises a warning if no files are
                found for a given pysat.Instrument.

       Stored pysat parameters without a working default value:
            'data_dirs': Stores locations of top-level directories pysat uses to
                store and load data.



The ``data_dirs`` setting is required to
successfully instantiate a ``pysat.Instrument`` object.

The ``user_modules`` parameter is used by the ``pysat.utils.registry`` submodule
and may not be modified via assignment.
