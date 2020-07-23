
.. |br| raw:: html

    <br>

Adding a New Instrument
=======================

pysat works by calling modules written for specific instruments
that load and process the data consistent with the pysat standard. The
name of the module corresponds to the combination 'platform_name' provided
when initializing a pysat instrument object. The module should be placed in
the pysat instruments directory or registered (see below) for automatic
discovery. A compatible module may also be supplied directly using

.. code:: Python

    pysat.Instrument(inst_module=python_module_object).

Some data repositories have pysat templates prepared to assist
in integrating a new instrument. See :ref:`supported-data-templates` or the
template instrument module code under `pysat/instruments/templates/` for more.

A compatible module may be supplied directly to :python:`pysat.Instrument(inst_module = myInstrument)`
if it also contains attributes platform and name. Such modules may be registered as
part of pysat's user instrument registry using the following syntax:

.. code-block:: python

  from pysat.utils import registry
  registry.register('my.package.myInstrument')

After registry, the instrument module name is stored in the user's home directory
under :code:`~.pysat/user_modules.txt`. The instrument may then be instantiated with
the instrument's platform and name:

.. code-block:: python

  inst = Instrument('myplatform', 'myname')


Some data repositories have pysat templates prepared to assist in integrating
a new instrument. See Supported Templates for more.

Naming Conventions
------------------

pysat uses a hierarchy of named variables to define each specific data product.
In order, this is

* platform
* name
* sat_id
* tag

The exact usage of these can be tailored to the nature of the mission and data
products.  In general, each combination should point to a unique data file.
Not every data product will need all of these variable names.  Both `sat_id`
and `tag` can be instantiated as an empty string if unused or used to
support a 'default' data set if desired. Examples are given below.

**platform**

In general, this is the name of the mission or observatory.  Examples include
ICON, JRO, COSMIC, and SuperDARN.  Note that this may be a single satellite or
ground-based observatory, a constellation of satellites, or a collaboration of
ground-based observatories.

**name**

In general, this is the name of the instrument or high-level data product.
When combined with the platform, this forms a unique file in the `instruments`
directory.  Examples include the EUV instrument on ICON (icon_euv) and the
Incoherent Scatter Radar at JRO (jro_isr).

**sat_id**

In general, this is a unique identifier for a satellite in a constellation of
identical or similar satellites, or multiple instruments on the same satellite
with different look directions.  For example, the DMSP satellites carry similar
instrument suites across multiple spacecraft.  These are labeled as f11-f18.

Note that sat_id will be updated to inst_id in pysat v3.0.

**tag**

In general, the tag points to a specific data product.  This could be a
specific processing level (such as L1, L2), or a product file (such as the
different profile products for cosmic_gps data, 'ionprf', 'atmprf', ...).

**Naming Requirements in Instrument Module**

Each instrument file must include the platform and name as variables at the
top-code-level of the file.  Additionally, the tags and sat_ids supported by
the module must be stored as dictionaries.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  # dictionary keyed by tag with a string description of that dataset
  tags = {'': 'The standard processing for the data.  Loaded by default',
          'fancy': 'A higher-level processing of the data.'}
  # dictionary keyed by sat_id with a list of supported tags
  # for each key
  sat_ids = {'A': ['', 'fancy'], 'B': ['', 'fancy'], 'C': ['']}

Note that the possible tags that can be invoked are '' and 'fancy'.  The tags
dictionary includes a short description for each of these tags.  A blank tag
will be present by default if the user does not specify a tag.

The supported sat_ids should also stored in a dictionary.  Each key name here
points to a list of the possible tags that can be associated with that
particular `sat_id`. Note that not all satellites in the example support
every level of processing. In this case, the 'fancy' processing is available
for satellites A and B, but not C.

For a dataset that does not need multiple levels of tags and sat_ids, an empty
string can be used. The code below only supports loading a single data set.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  tags = {'': ''}
  sat_ids = {'': ['']}

The DMSP IVM (dmsp_ivm) instrument module is a practical example of
a pysat instrument that uses all levels of variable names.

Required Routines
-----------------

Three methods are required within a new instrument module to
support pysat operations, with functionality to cover finding files,
loading data from specified files, and downloading new files. While
the methods below are sufficient to engage with pysat,
additional optional methods are needed for full pysat support.

Note that these methods are not directly invoked by the user, but by pysat
as needed in response to user inputs.


**list_files**

pysat maintains a list of files to enable data management functionality.
To get this information, pysat expects a module method platform_name.list_files
to return a pandas Series of filenames indexed by time with a method
signature of:

.. code:: python

   def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
       return pandas.Series(files, index=datetime_index)

sat_id and tag are passed in by pysat to select a specific subset of the
available data. The location on the local filesystem to search for the files
is passed in data_path. The list_files method must return
a pandas Series of filenames indexed by datetime objects.

A user is also able to supply a file template string
suitable for locating files on their system at pysat.Instrument instantiation,
passed via format_str, that must be supported. Sometimes users obtain files
from non-traditional sources and format_str makes it easier for those users
to use an existing instrument module to work with those files.

pysat will by default store data in pysat_data_dir/platform/name/tag,
helpfully provided in data_path, where pysat_data_dir is specified by using
`pysat.utils.set_data_dir(pysat_data_dir)`. Note that an alternative
directory structure may be specified using the pysat.Instrument keyword
directory_format at instantiation. The default is recreated using

.. code:: python

    dformat = '{platform}/{name}/{tag}'
    inst=pysat.Instrument(platform, name, directory_format=dformat)

Note that pysat handles the path information thus instrument module developers
do not need to do anything to support the directory_format keyword.

**Pre-Built list_files Methods and Support**

Finding local files is generally similar across data sets thus pysat
includes a variety of methods to make support this functionality easier.
The simplest way to construct a valid list_files method is to use one of these
included pysat methods.

`pysat.Files.from_os` is a convenience constructor provided for filenames that
include time information in the filename and utilize a constant field width
or a consistent delimiter. The location and format of the time information is
specified using standard python formatting and keywords year, month, day, hour,
minute, second. Additionally, both version and revision keywords
are supported. When present, the from_os constructor will filter down the
file list to the latest version and revision combination.

A complete list_files routine could be as simple as

.. code:: python

   def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
       if format_str is None:
           # set default string template consistent with files from
           # the data provider that will be supported by the instrument
           # module download method
           # template string below works for CINDI IVM data that looks like
           # 'cindi-2009310-ivm-v02.hdf'
           # format_str supported keywords: year, month, day,
           # hour, minute, second, version, and revision
           format_str = 'cindi-{year:4d}{day:03d}-ivm-v{version:02d}.hdf'
       return pysat.Files.from_os(data_path=data_path, format_str=format_str)

The constructor presumes the template string is for a fixed width format
unless a delimiter string is supplied. This constructor supports conversion
of years with only 2 digits and expands them to 4 using the
two_digit_year_break keyword. Note the support for format_str.

If the constructor is not appropriate, then lower level methods
within pysat._files may also be used to reduce the workload in adding a new
instrument. Note in pysat 3.0 this module will be renamed pysat.files for
greater visibility.

See pysat.utils.time.create_datetime_index for creating a datetime index for an
array of irregularly sampled times.

pysat will invoke the list_files method the first time a particular instrument
is instantiated. After the first instantiation, by default pysat will not search
for instrument files as some missions can produce a large number of
files which may take time to identify. The list of files associated
with an Instrument may be updated by adding `update_files=True`.

.. code:: python
   inst = pysat.Instrument(platform=platform, name=name, update_files=True)

The output provided by the list_files function that has been pulled into pysat
the Instrument object above can be inspected from within Python by
checking `inst.files.files`.

**load**

Loading data is a fundamental activity for data science and is
required for all pysat instruments. The work invested by the instrument
module author makes it possible for users to work with the data easily.

The load module method signature should appear as:

.. code:: python

   def load(fnames, tag=None, sat_id=None):
       return data, meta

- fnames contains a list of filenames with the complete data path that
  pysat expects the routine to load data for. For most data sets
  the method should return the exact data that is within the file.
  However, pysat is also currently optimized for working with
  data by day. This can present some issues for data sets that are stored
  by month or by year. See `instruments.methods.nasa_cdaweb.py` for an example
  of returning daily data when stored by month.
- tag and sat_id specify the data set to be loaded

- The load routine should return a tuple with (data, pysat metadata object).
- `data` is a pandas DataFrame, column names are the data labels, rows are
  indexed by datetime objects.
- For multi-dimensional data, an xarray can be
  used instead. When returning xarray data, a variable at the instrument module
  top-level must be set,
.. code:: python

   pandas_format = False

- The pandas DataFrame or xarray needs to be indexed with datetime objects. For
  xarray objects this index needs to be named 'Epoch' or 'time'. In a future
  version the supported names for the time index may be reduced. 'Epoch'
  should be used for pandas though wider compatibility is expected.
- `pysat.utils.create_datetime_index` provides for quick generation of an
  appropriate datetime index for irregularly sampled data set with gaps

- A pysat meta object may be obtained from `pysat.Meta()`. The Meta object
  uses a pandas DataFrame indexed by variable name with columns for
  metadata parameters associated with that variable, including items like
  'units' and 'long_name'. A variety of parameters are included by default.
  Additional arbitrary columns allowed. See `pysat.Meta` for more information on
  creating the initial metadata.
- Note that users may opt for a different
  naming scheme for metadata parameters thus the most general code for working
  with metadata uses the attached labels,
.. code:: python

   # update units to meters, 'm' for variable
   inst.meta[variable, inst.units_label] = 'm'

- If metadata is already stored with the file, creating the Meta object is
  generally trivial. If this isn't the case, it can be tedious to fill out all
  information if there are many data parameters. In this case it may be easier
  to fill out a text file. A basic convenience function is provided for this
  situation. See `pysat.Meta.from_csv` for more information.

**download**

Download support significantly lowers the hassle in dealing with any dataset.
Fetch data from the internet.

.. code:: python

   def download(date_array, data_path=None, user=None, password=None):
       return

* date_array, a list of dates to download data for
* data_path, the full path to the directory to store data
* user, string for username
* password, string for password

Routine should download data and write it to disk.


Optional Routines and Support
-----------------------------

**Custom Keywords in load Method**

pysat supports the definition and use of keywords for an instrument module
so that users may trigger optional features, if provided. All custom keywords
for an instrument module must be defined in the `load` method.

.. code:: python

   def load(fnames, tag=None, sat_id=None, custom1=default1, custom2=default2):
       return data, meta

pysat passes any supported custom keywords and values to `load` with every call.
All custom keywords along with the assigned defaults are copied into the
Instrument object itself under inst.kwargs for use in other areas.

.. code:: python

   inst = pysat.Instrument(platform, name, custom1=new_value)
   # show user supplied value for custom1 keyword
   print(inst.kwargs['custom1'])
   # show default value applied for custom2 keyword
   print(inst.kwargs['custom2'])

If a user supplies a keyword that is not supported by pysat or by the
specific instrument module then an error is raised.


**init**

If present, the instrument init method runs once at instrument instantiation.

.. code:: python

   def init(inst):
       return None

inst is a pysat.Instrument() instance. init should modify inst
in-place as needed; equivalent to a 'modify' custom routine.

keywords are not supported within the init module method signature, though
custom keyword support for instruments is available via inst.kwargs.

**default**


First custom function applied, once per instrument load.

.. code:: python

   def default(inst):
       return None

inst is a pysat.Instrument() instance. default should modify inst in-place as
needed; equivalent to a 'modify' custom routine.

**clean**


Cleans instrument for levels supplied in inst.clean_level.
  * 'clean' : expectation of good data
  * 'dusty' : probably good data, use with caution
  * 'dirty' : minimal cleaning, only blatant instrument errors removed
  * 'none'  : no cleaning, routine not called

.. code:: python

   def clean(inst):
       return None

inst is a pysat.Instrument() instance. clean should modify inst in-place as
needed; equivalent to a 'modify' custom routine.

**list_remote_files**

Returns a list of available files on the remote server. This method is required
for the Instrument module to support the `download_updated_files` method, which
makes it trivial for users to ensure they always have the most up to date data.
pysat developers highly encourage the development of this method, when possible.

.. code:: python

    def list_remote_files(inst):
        return list_like

This method is called by several internal `pysat` functions, and can be directly
called by the user through the `inst.remote_file_list` command.  The user can
search for subsets of files through optional keywords, such as

.. code:: python

    inst.remote_file_list(year=2019)
    inst.remote_file_list(year=2019, month=1, day=1)


Testing Support
---------------
All modules defined in the __init__.py for pysat/instruments are automatically
tested when pysat code is tested. To support testing all of the required
routines, additional information is required by pysat.

Example code from dmsp_ivm.py. The attributes are set at the top level simply
by defining variable names with the proper info. The various satellites within
DMSP, F11, F12, F13 are separated out using the sat_id parameter. 'utd' is used
as a tag to delineate that the data contains the UTD developed quality flags.

.. code:: python

   platform = 'dmsp'
   name = 'ivm'
   tags = {'utd': 'UTDallas DMSP data processing',
           '': 'Level 1 data processing'}
   sat_ids = {'f11': ['utd', ''], 'f12': ['utd', ''], 'f13': ['utd', ''],
              'f14': ['utd', ''], 'f15': ['utd', ''], 'f16': [''], 'f17': [''],
              'f18': ['']}
   _test_dates = {'f11': {'utd': pysat.datetime(1998, 1, 2)},
                  'f12': {'utd': pysat.datetime(1998, 1, 2)},
                  'f13': {'utd': pysat.datetime(1998, 1, 2)},
                  'f14': {'utd': pysat.datetime(1998, 1, 2)},
                  'f15': {'utd': pysat.datetime(2017, 12, 30)}}

    # support load routine
    def load(fnames, tag=None, sat_id=None):
        # code normally follows, example terminates here

The rationale behind the variable names is explained above under Naming
Conventions.  What is important here are the _test_dates.  Each of these points
to a specific date for which the unit tests will attempt to download and load
data as part of end-to-end testing.  Make sure that the data exists for the
given date. The tags without test dates will not be tested. The leading
underscore in _test_dates ensures that this information is not added to the
instrument's meta attributes, so it will not be present in IO operations.

Data Acknowledgements
=====================

Acknowledging the source of data is key for scientific collaboration.  This can
generally be put in the `init` function of each instrument.  Relevant
citations should be included in the instrument docstring.


Supported Data Templates
========================


NASA CDAWeb
-----------

A template for NASA CDAWeb pysat support is provided. Several of the routines
within are intended to be used with functools.partial in the new instrument
support code. When writing custom routines with a new instrument file
download support would be added via

.. code:: python

   def download(.....)

Using the CDAWeb template the equivalent action is

.. code:: python

   download = functools.partial(methods.nasa_cdaweb.download,
                                supported_tags)

where supported_tags is defined as dictated by the download function. See the
routines for cnofs_vefi and cnofs_ivm for practical uses of the NASA CDAWeb
support code.
|br|

.. automodule:: pysat.instruments.methods.nasa_cdaweb
   :members:

Madrigal
--------

A template for Madrigal pysat support is provided. Several of the routines
within are intended to be used with functools.partial in the new instrument
support code. When writing custom routines with a new instrument file download
support would be added via

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
|br|

.. automodule:: pysat.instruments.methods.madrigal
  :members:
