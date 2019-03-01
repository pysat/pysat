
.. |br| raw:: html

    <br>

Adding a New Instrument
=======================

pysat works by calling modules written for specific instruments
that load and process the data consistent with the pysat standard. The name
of the module corresponds to the combination 'platform_name' provided when
initializing a pysat instrument object. The module should be placed in the
pysat instruments directory or in the user specified location (via
mechanism to be added) for automatic discovery. A compatible module may
also be supplied directly to pysat.Instrument(inst_module=input module) if
it also contains attributes platform and name.

Some data repositories have pysat templates prepared to assist in integrating
a new instrument. See Supported Templates for more.

Three functions are required by pysat for operation, with supporting
information for testing:

List Files
----------

Pysat maintains a list of files to enable data management functionality. It needs a pandas Series of filenames indexed by time. Pysat expects the module method platform_name.list_files to be:

.. code:: python

   def list_files(tag=None, data_path=None):
       return pandas.Series(files, index=datetime_index)

where tag indicates a specific subset of the available data from cnofs_vefi.

See pysat.utils.time.create_datetime_index for creating a datetime index for an array of irregularly sampled times.

Pysat will store data in pysat_data_dir/platform/name/tag, helpfully provided in data_path, where pysat_data_dir is specified by using `pysat.utils.set_data_dir(pysat_data_dir)`.

`pysat.Files.from_os` is a convenience constructor provided for filenames that include time information in the filename and utilize a constant field width. The location and format of the time information is specified using standard python formatting and keywords year, month, day, hour, minute, second. A complete list_files routine could be as simple as

.. code:: python

   def list_files(tag=None, data_path=None):
       return pysat.Files.from_os(data_path=data_path,
                    format_str='cindi-{year:4d}{day:03d}-ivm.hdf')

The list_files function can be invoked from within ipython by calling

.. code:: python

  instrument.files.files

where instrument is the name of the instrument object.  Likewise, files can be directly listed when instantiating an instrument object by adding `update_files=True`.

.. code:: python
    inst = pysat.Instrument(platform=platform, name=name, update_files=True)


Load Data
---------

Loading is a fundamental pysat activity, this routine enables the user to consider loading a hidden implementation 'detail'.

.. code:: python

   def load(fnames, tag=None):
       return data, meta

- The load routine should return a tuple with (data, pysat metadata object).
- `data` is a pandas DataFrame, column names are the data labels, rows are
  indexed by datetime objects.  For multi-dimensional data, an xarray can be
  used.
- `pysat.utils.create_datetime_index` provides for quick generation of an
  appropriate datetime index for irregularly sampled data set with gaps
- pysat meta object obtained from `pysat.Meta()`. Use pandas DataFrame indexed
  by name with columns for 'units' and 'long_name'. Additional arbitrary
  columns allowed. See `pysat.Meta` for more information on creating the
  initial metadata.
- If metadata is already stored with the file, creating the Meta object is
  trivial. If this isn't the case, it can be tedious to fill out all
  information if there are many data parameters. In this case it is easier to
  fill out a text file. A convenience function is provided for this
  situation. See `pysat.Meta.from_csv` for more information.



Download Data
-------------

Download support significantly lowers the hassle in dealing with any dataset.
Fetch data from the internet.

.. code:: python

   def download(date_array, data_path=None, user=None, password=None):
       return

- date_array, a list of dates to download data for
- data_path, the full path to the directory to store data
- user, string for username
- password, string for password

Routine should download data and write it to disk.

Optional Routines
-----------------

**Initialize**


Initialize any specific instrument info. Runs once.

.. code:: python

   def init(inst):
       return None

inst is a pysat.Instrument() instance. init should modify inst in-place as needed; equivalent to a 'modify' custom routine.

**Default**


First custom function applied, once per instrument load.

.. code:: python

   def default(inst):
       return None

inst is a pysat.Instrument() instance. default should modify inst in-place as needed; equivalent to a 'modify' custom routine.

**Clean Data**


Cleans instrument for levels supplied in inst.clean_level.
  * 'clean' : expectation of good data
  * 'dusty' : probably good data, use with caution
  * 'dirty' : minimal cleaning, only blatant instrument errors removed
  * 'none'  : no cleaning, routine not called

.. code:: python

   def clean(inst):
       return None

inst is a pysat.Instrument() instance. clean should modify inst in-place as needed; equivalent to a 'modify' custom routine.

**List Remote Files**

Returns a list of available files on the remote server.

.. code:: python

    def list_remote_files(inst):
        return list_like


Testing Support
---------------
All modules defined in the __init__.py for pysat/instruments are automatically
tested when pyast code is tested. To support testing all of the required routines,
additional information is required by pysat.

The following attributes must be defined.
   - platform : platform name
   - name : instrument name
   - tags : dictionary of all tags supported by routine with a description. Typically these will include different available data products.
   - sat_ids : dictionary of sat_ids, with a list of tags supported by each id. The sat_ids may refer to a specific platform within a multi-satellite constellation, or to a specific instrument for a single satellite with multiple copies of the same instrument looking in different directions.
   - test_dates : dictionary of sat_ids, containing dictionary of available tags for each sat_id, along with a date to download for testing

Note that platform and name must match those used to name the file, platform_name.py

Example code from dmsp_ivm.py. The attributes are set at the top level simply
by defining variable names with the proper info. The various satellites within
DMSP, F11, F12, F13 are separated out using the sat_id parameter. 'utd' is used
as a tag to delineate that the data contains the UTD developed quality flags.

.. code:: python

   platform = 'dmsp'
   name = 'ivm'
   tags = {'utd': 'UTDallas DMSP data processing'}
   sat_ids = {'f11': ['utd'], 'f12': ['utd'], 'f13': ['utd'],
              'f14': ['utd'], 'f15': ['utd']}
   test_dates = {'f11': {'utd': pysat.datetime(1998, 1, 2)},
                 'f12': {'utd': pysat.datetime(1998, 1, 2)},
                 'f13': {'utd': pysat.datetime(1998, 1, 2)},
                 'f14': {'utd': pysat.datetime(1998, 1, 2)},
                 'f15': {'utd': pysat.datetime(2017, 12, 30)}}

    # support load routine
    def load(fnames, tag=None, sat_id=None):
        # code normally follows, example terminates here


Data Acknowledgements
=====================

Acknowledging the source of data is key for scientific collaboration.  This can generally be put in the `init` function of each instrument.  Relevant citations should be included in the instrument docstring.


Supported Data Templates
========================


NASA CDAWeb
-----------

A template for NASA CDAWeb pysat support is provided. Several of the routines within are intended to be used with functools.partial in the new instrument support code. When writing custom routines with a new instrument file download support would be added via

.. code:: python

   def download(.....)

Using the CDAWeb template the equivalent action is

.. code:: python

   download = functools.partial(nasa_cdaweb_methods.download,
                                supported_tags)

where supported_tags is defined as dictated by the download function. See the routines for cnofs_vefi and cnofs_ivm for practical uses of the NASA CDAWeb support code.
|br|

.. automodule:: pysat.instruments.nasa_cdaweb_methods
   :members:

Madrigal
-----------

A template for Madrigal pysat support is provided. Several of the routines within are intended to be used with functools.partial in the new instrument support code. When writing custom routines with a new instrument file download support would be added via

.. code:: python

    def download(.....)

Using the Madrigal template the equivalent action is

.. code:: python

     def download(date_array, tag='', sat_id='', data_path=None, user=None,
                  password=None):
         madrigal_methods.download(date_array, inst_code=str(madrigal_inst_code),
                                   kindat=str(madrigal_tag[sat_id][tag]),
                                   data_path=data_path, user=user,
                                   password=password)

See the routines for `dmsp_ivm` and `jro_isr` for practical uses of the Madrigal support code.

Additionally, use of the madrigal_methods class should acknowledge the CEDAR rules of the road.  This can be done by Adding

.. code:: python

     def init(self):

         print(madrigal_methods.cedar_rules())
         return

to each routine that uses Madrigal data access.
|br|

.. automodule:: pysat.instruments.madrigal_methods
  :members:
