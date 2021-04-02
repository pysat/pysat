Transition to v3.0
==================

pysat release v3.0 introduces some backwards incompatible changes from
v2.x to ensure a strong foundation for future development. Many of the changes
needed to update existing pysat v2.x analysis codes are relatively trivial
and relate to an updated restructuring of supporting pysat functions. However,
there are some changes with how pysat stores package information as well as how
pysat interacts with the local file system to find files that may require some
setup work for systems with an existing pysat v2.x install.

pysat v3.0 now supports a single internal interface for storing and retrieving
package data that also makes it possible for users to set values for a
variety of pysat defaults. pysat stores all of this information in the user's
home directory under ``~/.pysat``. To get the most benefit from this internal
reorganization we recommend that you remove any existing ``.pysat`` directories.
See :ref:`tutorial-params` for more.

.. note:: Removing the existing .pysat directory will erase all internal
   pysat information and requires resetting user parameters such as the
   top-level directory that stores relevant science data. To set this top-level
   directory run ``pysat.params['data_dirs'] = new_path`` where ``new_path``
   is a string or list of strings for directories that pysat
   can use to store science data.

pysat v3.0 now supports more than one top-level directory to store science
data as well as updates the default sub-directory structure for storing data.
pysat v2.x employed an internal directory template of ``platform/name/tag``
for organizing data while pysat v3.0 begins with a default of
``platform/name/tag/inst_id``. Thus, by default, a pysat v3.0 install will
generally not find all existing data files that were managed by pysat v2.x.

Additionally, support for individual instruments has been moved out of
pysat and into a penumbra of supporting packages. These supporting
packages must be installed and registered with pysat before data may
be loaded. See :ref:`ecosystem` and :ref:`api-pysat-registry` for more.

.. note:: pysat will only recognize registered instrument modules
   when running the ``update_data_directory_structure`` function.
   Files associated with unregistered instruments will not be moved.

There are two main paths forward for restoring access to all data after
registering the necessary packages:

- Update pysat's directory template to match the structure on the current
  install.

.. code:: python

   import os
   import pysat

   templ_str = os.path.sep.join(('{platform}', '{name}', '{tag}'))
   pysat.params['directory_format'] = templ_str


- Alternately, existing files may be moved to match a new
  directory structure using pysat functionality.

.. code:: python

   import os
   import pysat

   # Update pysat's directory setting to match current file distribution.
   # Presuming the standard pysat v2.x distribution from above.
   pysat.params['directory_format'] = templ_str

   # Define the new directory template (using pysat v3.0 default)
   new_templ_str = os.path.sep.join(('{platform}', '{name}', '{tag}',
                                     '{inst_id}'))

   # Perform a test-run for moving existing files to new structure with enhanced
   # user feedback.
   pysat.utils.files.update_data_directory_structure(new_templ_str,
                                                     test_run=True,
                                                     full_breakdown=True)

   # If happy with the listed changes to be made, move the files.
   # Flag set to remove empty directories after files are moved.
   pysat.utils.files.update_data_directory_structure(new_templ_str,
                                                     test_run=False,
                                                     full_breakdown=True,
                                                     remove_empty_dirs=True)

   # After the files have been moved, update the directory structure setting
   pysat.params['directory_format'] = new_templ_str

.. note:: By default the `update_data_directory_structure` function runs in test mode.
