========================
Supported Data Templates
========================

General
-------

A general instrument template is included with pysat that has the full set
of required and optional methods, and docstrings, that may be used as a
starting point for adding a new instrument to pysat.



NASA CDAWeb
-----------

A template for NASA CDAWeb pysat support is provided. Several of the routines
within are intended to be used with functools.partial in the new instrument
support code. When writing custom routines with a new instrument file
download support would normally be added via

.. code:: python

   def download(.....)

Using the CDAWeb template the equivalent action is

.. code:: python

   download = functools.partial(methods.nasa_cdaweb.download,
                                supported_tags)

where supported_tags is defined as dictated by the download function. See the
routines for cnofs_vefi and cnofs_ivm for practical uses of the NASA CDAWeb
support code.


See :ref:`rst_general_data_cdaweb` for more.

Madrigal
--------

A template for Madrigal pysat support is provided. Several of the routines
within are intended to be used with functools.partial in the new instrument
support code. When writing custom routines with a new instrument file download
support would normally be added via

.. code:: python

    def download(.....)

Using the Madrigal template the equivalent action is

.. code:: python

     def download(date_array, tag='', sat_id='', data_path=None, user=None,
                  password=None):
         methods.madrigal.download(date_array, inst_code=str(madrigal_inst_code),
                                   kindat=str(madrigal_tag[sat_id][tag]),
                                   data_path=data_path, user=user,
                                   password=password)

See the routines for `dmsp_ivm` and `jro_isr` for practical uses of the Madrigal
support code.

Additionally, use of the methods.madrigal class should acknowledge the CEDAR
rules of the road.  This can be done by Adding

.. code:: python

     def init(self):

         print(methods.madrigal.cedar_rules())
         return

to each routine that uses Madrigal data access.


See :ref:`rst_general_data_madrigal` for more.
