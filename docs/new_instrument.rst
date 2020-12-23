.. _rst_new_inst:

Adding a New Instrument
=======================

pysat works by calling modules written for specific instruments
that load and process the data consistent with the pysat standard. The
name of the module corresponds to the combination 'platform_name' provided
when initializing a pysat instrument object. The module should be placed in
the pysat instruments directory or registered (see below) for automatic
discovery. A compatible module may also be supplied directly using

.. code:: Python

    pysat.Instrument(inst_module=python_module_object)


A general template has also been included to make starting any Instrument
module easier at `pysat/instruments/templates/`. Some data repositories have
pysat templates prepared to assist in integrating a new instrument. See
the associated pysat* package for that particular data source, such as
pysatNASA for supporting additional NASA instruments.

External modules may be registered as
part of pysat's user instrument registry using the following syntax:

.. code-block:: python

  from pysat.utils import registry

  # Register single instrument
  registry.register('my.package.myInstrument')

  # register all instrument sub-modules
  import my_package
  registry.register_from_module(my_package.instruments)

After registry the instrument module name is stored in the user's home
directory under :code:`~.pysat/user_modules.txt`. The instrument may then
be instantiated with the instrument's platform and name:

.. code-block:: python

  inst = Instrument('myplatform', 'myname')


Instrument Libraries
--------------------
pysat instruments can reside in external libraries.  The registry methods
described  above can be used to provide links to these instrument libraries
for rapid access.  For instance, pysat instruments which handle the outputs
of geophysical models (such as the TIE-GCM model) reside in the pysatModels
package.

Naming Conventions
------------------

pysat uses a hierarchy of named variables to define each specific data product.
In order this is:

* platform
* name
* inst_id
* tag

The exact usage of these can be tailored to the nature of the mission and data
products.  In general, each combination should point to a unique data file.
Not every data product will need all of these variable names.  Both `inst_id`
and `tag` can be instantiated as an empty string if unused or used to
support a 'default' data set if desired. Examples are given below.

**platform**

In general, this is the name of the mission or observatory.  Examples include
ICON, JRO, COSMIC, and SuperDARN.  Note that this may be a single satellite,
a constellation of satellites, a ground-based observatory, or a collaboration
of ground-based observatories.

**name**

In general, this is the name of the instrument or high-level data product.
When combined with the platform this forms a unique file in the `instruments`
directory.  Examples include the EUV instrument on ICON (icon_euv) and the
Incoherent Scatter Radar at JRO (jro_isr).

**tag**

In general, the tag points to a specific data product.  This could be a
specific processing level (such as L1, L2), or a product file (such as the
different profile products for cosmic_gps data, 'ionprf', 'atmprf', ...).

**inst_id**

In general, this is a unique identifier for a satellite in a constellation of
identical or similar satellites, or multiple instruments on the same satellite
with different look directions.  For example, the DMSP satellites carry similar
instrument suites across multiple spacecraft.  These are labeled as f11-f18.

**Naming Requirements in Instrument Module**

Each instrument file must include the platform and name as variables at the
top-code-level of the file.  Additionally, the tags and inst_ids supported by
the module must be stored as dictionaries.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  # dictionary keyed by tag with a string description of that dataset
  tags = {'': 'The standard processing for the data.  Loaded by default',
          'fancy': 'A higher-level processing of the data.'}

  # Dictionary keyed by inst_id with a list of supported tags for each key
  inst_ids = {'A': ['', 'fancy'], 'B': ['', 'fancy'], 'C': ['']}

Note that the possible tags that can be invoked are '' and 'fancy'.  The tags
dictionary includes a short description for each of these tags.  A blank tag
will be present by default if the user does not specify a tag.

The supported inst_ids should also be stored in a dictionary.  Each key name here
points to a list of the possible tags that can be associated with that
particular `inst_id`. Note that not all satellites in the example support
every level of processing. In this case the 'fancy' processing is available
for satellites A and B, but not C.

For a dataset that does not need multiple levels of tags and inst_ids, an empty
string can be used. The code below only supports loading a single data set.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  tags = {'': ''}
  inst_ids = {'': ['']}

The DMSP IVM (dmsp_ivm) instrument module is a practical example of
a pysat instrument that uses all levels of variable names.

Required Variables
------------------

Because platform, name, tags, and inst_ids are used for loading and maintaining
different data sets they must be defined for every instrument.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  tags = {'': ''}
  inst_ids = {'': ['']}

Pysat also requires that instruments include information pertaining to
acknowledgements and references for an instrument.  These are simply defined as
strings at the instrument level.  In the most basic case, these can be defined
with the data information at the top.

Pysat also requires that a logger handle be defined and instrumentment
information pertaining to acknowledgements and references be included.  These
ensure that people using the data know who to contact with questions and what
they should reference when publishing their results.  The logging handle should
be assigned to the pysat logger handle, while the references and acknowedgements
are defined as instrument attributes within the initalization method.

.. code:: python

  logger = pysat.logger
  platform = 'your_platform_name'
  name = 'name_of_instrument'
  tags = {'tag1': '',
          'tag2': ''}
  inst_ids = {'': ['']}

  def init(self):
      """Initializes the Instrument object with instrument specific values.
      """
      self.acknowledgements = ''.join(['Ancillary data provided under ',
                                       'Radchaai grant PS31612.E3353A83'])
      if self.tag == 'tag1':
          self.references = 'Breq et al, 2013'
      elif self.tag == 'tag2':
          self.references = 'Mianaai and Mianaai, 2014'

      logger.info(self.acknowledgements)
      return

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
To get this information pysat expects a module method platform_name.list_files
to return a pandas Series of filenames indexed by time with a method
signature of:

.. code:: python

   def list_files(tag=None, inst_id=None, data_path=None, format_str=None):
       return pandas.Series(files, index=datetime_index)

inst_id and tag are passed in by pysat to select a specific subset of the
available data. The location on the local filesystem to search for the files
is passed in data_path. The list_files method must return
a pandas Series of filenames indexed by datetime objects.

A user must also supply a file template string suitable for locating files
on their system at pysat.Instrument instantiation, passed via format_str,
that must be supported. Sometimes users obtain files from non-traditional
sources and format_str makes it easier for those users to use an existing
instrument module to work with those files.

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
includes a variety of methods to make supporting this functionality easier.
The simplest way to construct a valid list_files method is to use one of these
included pysat methods.

A complete method is available
in ``pysat.instruments.methods.general.list_files`` that may find broad use.

``pysat.Files.from_os`` is a convenience constructor provided for filenames that
include time information in the filename and utilize a constant field width
or a consistent delimiter. The location and format of the time information is
specified using standard python formatting and keywords year, month, day, hour,
minute, second. Additionally, version, revision, and cycle keywords
are supported. When present, the from_os constructor will filter down the
file list to the latest version/revision/cycle combination.

A complete list_files routine could be as simple as

.. code:: python

   def list_files(tag=None, inst_id=None, data_path=None, format_str=None):
       if format_str is None:
           # set default string template consistent with files from
           # the data provider that will be supported by the instrument
           # module download method
           # template string below works for CINDI IVM data that looks like
           # 'cindi-2009310-ivm-v02.hdf'
           # format_str supported keywords: year, month, day,
           # hour, minute, second, version, revision, and cycle
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
is instantiated. After the first instantiation, by default, pysat will not
search for instrument files as some missions can produce a large number of
files, which may take time to identify. The list of files associated
with an Instrument may be updated by adding `update_files=True` to the kwargs.

.. code:: python

   inst = pysat.Instrument(platform=platform, name=name, update_files=True)

The output provided by the `list_files` function above can be inspected
by calling `inst.files.files`.

**load**

Loading data is a fundamental activity for data science and is
required for all pysat instruments. The work invested by the instrument
module author makes it possible for users to work with the data easily.

The load module method signature should appear as:

.. code:: python

   def load(fnames, tag=None, inst_id=None):
       return data, meta

- fnames contains a list of filenames with the complete data path that
  pysat expects the routine to load data for. With most data sets
  the method should return the exact data that is within the file.
  However, pysat is also currently optimized for working with
  data by day. This can present some issues for data sets that are stored
  by month or by year. See `instruments.methods.nasa_cdaweb.py` for an example
  of returning daily data when stored by month.
- tag and inst_id specify the data set to be loaded

- The load routine should return a tuple with (data, pysat metadata object).
- `data` is a pandas DataFrame, column names are the data labels, rows are
  indexed by datetime objects.
- For multi-dimensional data, an xarray can be
  used instead. When returning xarray data, a variable at the top-level of the
  instrument module must be set:

.. code:: python

   pandas_format = False

- The pandas DataFrame or xarray needs to be indexed with datetime objects. For
  xarray objects this index needs to be named 'Epoch' or 'time'. In a future
  version the supported names for the time index may be reduced. 'Epoch'
  should be used for pandas though wider compatibility is expected.
- `pysat.utils.create_datetime_index` provides quick generation of an
  appropriate datetime index for irregularly sampled data sets with gaps

- A pysat meta object may be obtained from `pysat.Meta()`. The Meta object
  uses a pandas DataFrame indexed by variable name with columns for
  metadata parameters associated with that variable, including items like
  'units' and 'long_name'. A variety of parameters are included by default and
  additional arbitrary columns are allowed. See `pysat.Meta` for more
  information on creating the initial metadata. Any values not set in the load routine will
  be set to the default values for that label type.
- Note that users may opt for a different
  naming scheme for metadata parameters thus the most general code for working
  with metadata uses the attached labels:

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
To fetch data from the internet the download method should have the signature

.. code:: python

   def download(date_array, data_path=None, user=None, password=None):
       return

* date_array, a list of dates to download data for
* data_path, the full path to the directory to store data
* user, string for username
* password, string for password

The routine should download the data and write it to the disk at the data_path.

Optional Routines and Support
-----------------------------

**Custom Keywords in load Method**

If provided, pysat supports the definition and use of keywords for an
instrument module so that users may trigger optional features. All custom
keywords for an instrument module must be defined in the `load` method.

.. code:: python

   def load(fnames, tag=None, inst_id=None, custom1=default1, custom2=default2):
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

Keywords are not supported within the init module method signature, though
custom keyword support for instruments is available via inst.kwargs.

**preprocess**


First custom function applied, once per instrument load.  Designed for standard
instrument preprocessing.

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
===============
All modules defined in the __init__.py for pysat/instruments are automatically
tested when pysat code is tested. To support testing all of the required
routines, additional information is required by pysat.

Below is example code from dmsp_ivm.py. The attributes are set at the top
level simply by defining variable names with the proper info. The various
satellites within DMSP, F11, F12, F13 are separated out using the inst_id
parameter. 'utd' is used as a tag to delineate that the data contains the
UTD developed quality flags.

.. code:: python

   platform = 'dmsp'
   name = 'ivm'
   tags = {'utd': 'UTDallas DMSP data processing',
           '': 'Level 1 data processing'}
   inst_ids = {'f11': ['utd', ''], 'f12': ['utd', ''], 'f13': ['utd', ''],
              'f14': ['utd', ''], 'f15': ['utd', ''], 'f16': [''], 'f17': [''],
              'f18': ['']}
   _test_dates = {'f11': {'utd': dt.datetime(1998, 1, 2)},
                  'f12': {'utd': dt.datetime(1998, 1, 2)},
                  'f13': {'utd': dt.datetime(1998, 1, 2)},
                  'f14': {'utd': dt.datetime(1998, 1, 2)},
                  'f15': {'utd': dt.datetime(2017, 12, 30)}}

    # support load routine
    def load(fnames, tag=None, inst_id=None):
        # code normally follows, example terminates here

The rationale behind the variable names is explained above under Naming
Conventions.  What is important here are the `_test_dates`. Each of these points
to a specific date for which the unit tests will attempt to download and load
data as part of end-to-end testing.  Make sure that the data exists for the
given date. The tags without test dates will not be tested. The leading
underscore in `_test_dates` ensures that this information is not added to the
instrument's meta attributes, so it will not be present in IO operations.

The standardized pysat tests are available in pysat.tests.instrument_test_class.
The test collection test_instruments.py imports this class, collects a list of
all available instruments (including potential tag / inst_id combinations),
and runs the tests using pytestmark.  By default, pysat assumes that your
instrument has a fully functional download  routine, and will run an end-to-end
test.  If this is not the case, see the next section.

Special Test Configurations
---------------------------
**No Download Available**

Some instruments simply don't have download routines available.  It could be
that data is not yet publicly available, or it may be a model run that is
locally generated.  To let the test routines know this is the case, the
`_test_download` flag is used.  This flag uses the same dictionary
structure as `_test_dates`.

For instance, say we have an instrument team that wants to use pysat to
manage their data products.  Level 1 data is locally generated by the team,
and Level 2 data is provided to a public repository.  The instrument should
be set up as follows:

.. code:: python

   platform = 'newsat'
   name = 'data'
   tags = {'Level_1': 'Level 1 data, locally generated',
           'Level_2': 'Level 2 data, available via the web'}
   inst_ids = {'': ['Level_1', 'Level_2']}
   _test_dates = {'': {'Level_1': dt.datetime(2020, 1, 1),
                       'Level_2': dt.datetime(2020, 1, 1)}}
   _test_download = {'': {'Level_1': False,
                          'Level_2': True}}


This tells the test routines to skip the download / load tests for Level 1 data.
Instead, the download function for this flag will be tested to see if it has an
appropriate user warning that downloads are not available.

Note that pysat assumes that this flag is True if no variable is present.
Thus specifying only `_test_download = {'': {'Level_1': False}}` has the
same effect, and Level 2 tests will still be run.

**FTP Access**

Another thing to note about testing is that the Travis CI environment used to
automate the tests is not compatible with FTP downloads.  For this reason,
HTTPS access is preferred whenever possible.  However, if this is not the case,
the `_test_download_travis` flag can be used.  This has a similar function,
except that it skips the download tests if on Travis CI, but will run those
tests if run locally.

.. code:: python

   platform = 'newsat'
   name = 'data'
   tags = {'Level_1': 'Level 1 data, FTP accessible',
           'Level_2': 'Level 2 data, available via the web'}
   inst_ids = {'': ['Level_1', 'Level_2']}
   _test_dates = {'': {'Level_1': dt.datetime(2020, 1, 1),
                       'Level_2': dt.datetime(2020, 1, 1)}}
   _test_download_travis = {'': {'Level_1': False}}

Note that here we use the streamlined flag definition and only call out the
tag that is False.  The other is True by default.

**Password Protected Data**

Another potential issue is that some instruments have download routines,
but should not undergo automated download tests because it would require
the  user to save a password in a potentially public location.  The
`_password_req` flag is used to skip both the download tests and the
download warning message tests, since a functional download routine is
present.

.. code:: python

   platform = 'newsat'
   name = 'data'
   tags = {'Level_1': 'Level 1 data, password protected',
           'Level_2': 'Level 2 data, available via the web'}
   inst_ids = {'': ['Level_1', 'Level_2']}
   _test_dates = {'': {'Level_1': dt.datetime(2020, 1, 1),
                       'Level_2': dt.datetime(2020, 1, 1)}}
   _password_req = {'': {'Level_1': False}}

Data Acknowledgements
---------------------

Acknowledging the source of data is key for scientific collaboration.  This can
generally be put in the `init` function of each instrument.

.. code:: Python

    def init(self):
        """Initializes the Instrument object with instrument specific values.

        Runs once upon instantiation.

        Parameters
        ----------
        inst : (pysat.Instrument)
            Instrument class object

        """

        self.acknowledgements = acknowledgements_string
        self.references = references_string
        logger.info(self.acknowledgements)

        return


Supported Instrument Templates
------------------------------

Instrument templates may be found at ``pysat.instruments.templates``
and supporting methods may be found at ``pysat.instruments.methods``.

General
^^^^^^^

A general instrument template is included with pysat,
``pysat.instruments.templates.template_instrument``,
that has the full set
of required and optional methods and docstrings, which may be used as a
starting point for adding a new instrument to pysat.

Note that there are general supporting methods for adding an Instrument.
See :ref:`rst_general_data_general` for more.
