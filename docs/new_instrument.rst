.. _rst_new_inst:

Adding a New Instrument
=======================

:py:mod:`pysat` works by calling modules written for specific instruments that
load and process the data consistent with the :py:mod:`pysat` standard. The
name of the module corresponds to the combination 'platform_name' provided
when initializing a :py:mod:`pysat` instrument object. The module should be
placed in the :py:mod:`pysat` instruments directory or registered (see below)
for automatic discovery. A compatible module may also be supplied directly using

.. code:: Python

    pysat.Instrument(inst_module=python_module_object)


A general template has also been included to make starting any Instrument
module easier at :py:mod:`pysat.instruments.templates.template_instrument`.
Some data repositories have :py:mod:`pysat` templates prepared to assist in
integrating a new instrument. See the associated pysat* package for that
particular data source, such as :py:mod:`pysatNASA` for supporting additional
NASA instruments.

External modules may be registered as part of the :py:mod:`pysat` user
instrument registry using the following syntax:

.. code-block:: python

  from pysat.utils import registry

  # Register single instrument
  registry.register('my.package.myInstrument')

  # register all instrument sub-modules
  import my_package
  registry.register_from_module(my_package.instruments)

After registry the instrument module name is stored in the user's home
directory in a hidden directory named :code:`~.pysat`. The instrument may then
be instantiated with the instrument's platform and name:

.. code-block:: python

  inst = pysat.Instrument('myplatform', 'myname')


.. _rst_new_inst-libs:

Instrument Libraries
--------------------
:py:mod:`pysat` instruments can reside in external libraries.  The registry
methods described above can be used to provide links to these instrument
libraries for rapid access. For instance, :py:mod:`pysat` instruments that
handle the outputs of geophysical models (such as the TIE-GCM model) reside in
the :py:mod:`pysatModels` package.


.. _rst_new_inst-naming:

Naming Conventions
------------------

:py:mod:`pysat` uses a hierarchy of named variables to define each specific
data product. In order this is:

* platform
* name
* tag
* inst_id

The exact usage of these can be tailored to the nature of the mission and data
products.  In general, each combination should point to a unique data file.
Not every data product will need all of these variable names.  Both
:py:attr:`inst_id` and :py:attr:`tag` can be instantiated as an empty string if
unused or used to support a 'default' data set if desired. Examples are given
below.

platform
^^^^^^^^

In general, this is the name of the mission or observatory.  Examples include
ICON, JRO, COSMIC, and SuperDARN.  Note that this may be a single satellite,
a constellation of satellites, a ground-based observatory, or a collaboration
of ground-based observatories.

Sometimes it is not practical to set a unique platform name for a data set. An
example of this are many of the space weather indices managed by
:py:mod:`pysatSpaceWeather`. In this case, the solar and geomagnetic indices are
included in a common 'Space Weather' platform (sw), regardless of their origin.
This allows users to access a given index using different :py:attr:`inst_id`
and :py:attr:`tag` values, even if the mission or observatory that produced the
indices differ.

name
^^^^

In general, this is the name of the instrument or high-level data product.
When combined with the platform this forms a unique file in the ``instruments``
directory.  Examples include the EUV instrument on ICON (icon_euv) and the
Incoherent Scatter Radar at JRO (jro_isr).

tag
^^^

In general, the tag points to a specific data product.  This could be a
specific processing level (such as L1, L2), or a product file (such as the
different profile products for :py:mod:`pysatCDDAC.instruments.cosmic_gps` data,
'ionprf', 'atmprf', ...).

inst_id
^^^^^^^

In general, this is a unique identifier for a satellite in a constellation of
identical or similar satellites, or multiple instruments on the same satellite
with different look directions.  For example, the DMSP satellites carry similar
instrument suites across multiple spacecraft.  These are labeled as f11-f18.

:py:attr:`inst_id` is also commonly used to distinguish between the same data
product at different sample rates. An example of this may be seen in the
:py:mod:`pysatNASA.instruments.timed_guvi` data for the 'sdr-imaging' and
'sdr-spectrograph' :py:attr:`tag` values. As a rule, when trying to decide if
a characteristic should be assigned as a :py:attr:`tag` or :py:attr:`inst_id`
attribute, the :py:attr:`inst_id` value should subdivide the :py:attr:`tag`
data set in a clear way that does not require a long description.

Naming Requirements in Instrument Module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each instrument file must include the platform and name as variables at the
top-code-level of the file.  Additionally, the tags and inst_ids supported by
the module must be stored as dictionaries. Note that all required names should
be lowercase when defined in the instrument module.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'

  # Dictionary keyed by tag with a string description of that data set
  tags = {'': 'The standard processing for the data.  Loaded by default',
          'fancy': 'A higher-level processing of the data.'}

  # Dictionary keyed by inst_id with a list of supported tags for each key
  inst_ids = {'sat-a': ['', 'fancy'], 'sat-b': ['', 'fancy'], 'sat-c': ['']}

Note that the possible tags that can be invoked are '' and 'fancy'.  The tags
dictionary includes a short description for each of these tags.  A blank tag
will be present by default if the user does not specify a tag.

The supported inst_ids should also be stored in a dictionary.  Each key name
here points to a list of the possible tags that can be associated with that
particular :py:attr:`inst_id`. Note that not all satellites in the example
support every level of processing. In this case the 'fancy' processing is
available for satellites 'sat-a' and 'sat-b', but not 'sat-c'.

For a data set that does not need multiple levels of :py:attr:`tag` and
:py:attr:`inst_id` attributes, an empty string can be used. The code below only
supports loading a single data set.  However, using an empty string for the
:py:attr:`tag` is discouraged if it is possible for the same platform to have
another distinct version of this data set in the future. This is unlikely to
be an issue for satellite data sets, but should be taken into account for
ground-based platforms.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  tags = {'': ''}
  inst_ids = {'': ['']}

The DMSP IVM (dmsp_ivm) instrument module in :py:mod:`pysatMadrigal` is a
practical example of a :py:mod:`pysat` instrument that uses all levels of
variable names. An :ref:`api-instrument-template` is also provided within
:py:mod:`pysat`.

Note that during instantiation of a :py:class:`pysat.Instrument`,
:py:mod:`pysat` uses the :py:attr:`tags` and :py:attr:`inst_ids` above to
determine if the values provided by a user are supported by the code.

.. _rst_new_inst-reqattrs:

Required Attributes
-------------------

Because :py:attr:`platform`, :py:attr:`name`, :py:attr:`tags`, and
:py:attr:`inst_ids` are used for loading and maintaining different data sets
they must be defined for every instrument.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  tags = {'': ''}
  inst_ids = {'': ['']}

:py:mod:`pysat` also requires that instruments include information pertaining to
acknowledgements and references for an instrument.  These are simply defined as
strings at the instrument level.  In the most basic case, these can be defined
with the data information at the top.

:py:mod:`pysat` also requires that a logger handle be defined and instrument
information pertaining to acknowledgements and references be included.  These
ensure that people using the data know who to contact with questions and what
they should reference when publishing their results.  The logging handle should
be assigned to the :py:mod:`pysat` logger handle, while the references and
acknowledgments are defined as instrument attributes within the initialization
method.

.. code:: python

  platform = 'your_platform_name'
  name = 'name_of_instrument'
  tags = {'tag1': 'tag1 Description',
          'tag2': 'tag2 Description'}
  inst_ids = {'': [tag for tag in tags.keys()]}

  def init(self):
      """Initializes the Instrument object with instrument specific values."""

      self.acknowledgements = ''.join(['Ancillary data provided under ',
                                       'Radchaai grant PS31612.E3353A83'])
      if self.tag == 'tag1':
          self.references = 'Breq et al, 2013'
      elif self.tag == 'tag2':
          self.references = 'Mianaai and Mianaai, 2014'

      pysat.logger.info(self.acknowledgements)
      return


.. _rst_new_inst-reqrout:

Required Routines
-----------------

Three methods are required within a new instrument module to support
:py:mod:`pysat` operations, with functionality to cover finding files, loading
data from specified files, and downloading new files. While the methods below
are sufficient to engage with :py:mod:`pysat`, additional optional methods are
needed for full :py:mod:`pysat` support.

Note that these methods are not directly invoked by the user, but by
:py:mod:`pysat` as needed in response to user inputs.


init
^^^^

The instrument :py:meth:`init` method runs once at instrument instantiation,
and handles the acknowledgement of the source of data.  Because this is key for
scientific collaboration, acknowledgements and references are required for all
:py:mod:`pysat` instruments.

.. code:: Python

    def init(self):
        """Initializes the Instrument object with instrument specific values."""

        self.acknowledgements = 'Follow the rules of the road by contacting PI'
        self.references = '2001: A Space Oddessy (1968)'
        pysat.logger.info(self.acknowledgements)

        return

``self`` is a  :py:class:`pysat.Instrument` object. :py:func:`init` should
modify ``self`` in-place as needed; equivalent to a custom routine.  It is
expected to attach the :py:attr:`acknowledgements` and :py:attr:`references`
attributes to ``self``.


list_files
^^^^^^^^^^

:py:mod:`pysat` maintains a list of files to enable data management
functionality. To get this information :py:mod:`pysat` expects a module function
:py:func:`platform_name.list_files` to return a :py:class:`pandas.Series` of
filenames indexed by time with a method signature of:

.. code:: python

   def list_files(tag='', inst_id='', data_path='', format_str=None):
       return pandas.Series(files, index=datetime_index)

:py:attr:`inst_id` and :py:attr:`tag` are passed in by :py:mod:`pysat` to
select a specific subset of the available data. The location on the local
filesystem to search for the files is passed in ``data_path``. The
:py:meth:`list_files` method must return a :py:class:`pandas.Series` of
filenames indexed by datetime objects.

A user must also supply a file template string suitable for locating files
on their system at pysat.Instrument instantiation, passed via ``format_str``,
that must be supported. Sometimes users obtain files from non-traditional
sources and ``format_str`` makes it easier for those users to use an existing
instrument module to work with those files.

:py:mod:`pysat` will by default store data in
``pysat_data_dir/platform/name/tag/inst_id``, helpfully provided in
``data_path``, where pysat_data_dir is specified by using
``pysat.params['data_dirs'] = pysat_data_dir``. Note that an alternative
directory structure may be specified using the :py:class:`pysat.Instrument`
keyword ``directory_format`` at instantiation. The default is recreated using

.. code:: python

    dformat = '{platform}/{name}/{tag}/{inst_id}'
    inst=pysat.Instrument(platform, name, directory_format=dformat)

Note that :py:mod:`pysat` handles the path information thus instrument module
developers do not need to do anything to support the ``directory_format``
keyword.

Pre-Built list_files Methods and Support
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Finding local files is generally similar across data sets thus :py:mod:`pysat`
includes a variety of methods to make supporting this functionality easier.
The simplest way to construct a valid list_files method is to use one of these
included :py:mod:`pysat` methods.

A complete method is available in
:py:func:`pysat.instruments.methods.general.list_files` that may find broad use.

:py:meth:`pysat.Files.from_os` is a convenience constructor provided for
filenames that include time information in the filename and utilize a constant
field width or a consistent delimiter. The location and format of the time
information is specified using standard python formatting and keywords ``year``,
``month``, ``day`` of month (year), ``hour``, ``minute``, ``second``.
Additionally, ``version``, ``revision``, and ``cycle`` keywords are supported.
When present, the :py:meth:`pysat.Files.from_os` constructor will filter down
the file list to the latest version/revision/cycle combination. Additional
user specified template variables are supported though they will not be used
to extract date information.

A complete list_files routine could be as simple as

.. code:: python

   def list_files(tag='', inst_id='', data_path='', format_str=None):
       if format_str is None:
           # Set default string template consistent with files from
           # the data provider that will be supported by the instrument
           # module download method.
           # Template string below works for CINDI IVM data that looks like
           # 'cindi-2009310-ivm-v02.hdf'
           # format_str supported keywords: year, month, day,
           # hour, minute, second, version, revision, and cycle
           # Note that `day` is interpreted is day of month if `month` also
           # present, otherwise `day` will be treated as day of year.
           format_str = 'cindi-{year:4d}{day:03d}-ivm-v{version:02d}.hdf'
       return pysat.Files.from_os(data_path=data_path, format_str=format_str)

The constructor presumes the template string is for a fixed width format
unless a delimiter string is supplied. This constructor supports conversion
of years with only 2 digits and expands them to 4 using the
``two_digit_year_break`` keyword. Note the support for a user provided
``format_str`` at runtime.

Given the range of compliance of filenames to a strict standard across the
decades of space science parsing filenames with and without a ``delimiter``
can typically generate the same results, even for filenames without a
consistently applied delimiter. As such either parser will function for most
situations however both remain within :py:mod:`pysat` to support currently
unknown edge cases that users may encounter. More practically, parsing with a
delimiter offers more support for the ``*`` wildcard than the fixed width
parser. It is generally advised to limit use of the ``*`` wildcard to prevent
potential false positives if a directory has more than one instrument within.

If the constructor is not appropriate, then lower level methods within
:py:class:`pysat.Files` may also be used to reduce the workload in adding a new
instrument. Access to the values of user provided template variables is not
available via :py:meth:`pysat.Files.from_os` and thus requires use of the
same lower level methods in :py:mod:`pysat.utils.files`.

See :py:func:`pysat.utils.time.create_datetime_index` for creating a datetime
index for an array of irregularly sampled times.

:py:mod:`pysat` will invoke the list_files method the first time a particular
instrument is instantiated. After the first instantiation, by default
:ref:`tutorial-params`, :py:mod:`pysat` will not search for instrument files as
some missions can produce a large number of files, which may take time to
identify. The list of files associated with an Instrument may be updated by
adding ``update_files=True`` to the kwargs.

.. code:: python

   inst = pysat.Instrument(platform=platform, name=name, update_files=True)

The output provided by the :py:func:`list_files` function above can be inspected
by calling :py:attr:`inst.files.files`.

load
^^^^

Loading data is a fundamental activity for data science and is required for all
:py:mod:`pysat` instruments. The work invested by the instrument module author
makes it possible for users to work with the data easily.

The load module method signature should appear as:

.. code:: python

   def load(fnames, tag='', inst_id=''):
       return data, meta

- :py:data:`fnames` contains a list of filenames with the complete data path
  that :py:mod:`pysat` expects the routine to load data for. With most data sets
  the method should return the exact data that is within the file.
  However, :py:mod:`pysat` is also currently optimized for working with
  data by day. This can present some issues for data sets that are stored
  by month or by year. See :ref:`instruments-sw` for examples of data sets
  stored by month(s).
- :py:data:`tag` and :py:data:`inst_id` are always available as inputs, as they
  commmonly specify the data set to be loaded
- The :py:func:`load` routine should return a tuple with :py:attr:`data` as the
  first element and a :py:class:`pysat.Meta` object as the second element.
- For simple time-series data sets, :py:attr:`data` is a
  :py:class:`pandas.DataFrame`, column names are the data labels, rows are
  indexed by :py:class:`datetime.datetime` objects.
- For multi-dimensional data, :py:attr:`data` can be set to an
  :py:class:`xarray.Dataset` instead. When returning xarray data, a variable
  at the top-level of the instrument module must be set:

.. code:: python

   pandas_format = False

- The :py:class:`pandas.DataFrame` or :py:class:`xarray.Dataset` needs to be
  indexed with :py:class:`datetime.datetime` objects. This index needs to be
  named either :py:data:`Epoch` for :py:class:`pandas.DataFrame` and
  :py:data:`time` for :py:class:`xarray.Dataset`.
- :py:func:`pysat.utils.create_datetime_index` provides quick generation of an
  appropriate datetime index for irregularly sampled data sets with gaps
- If your data is a CSV formatted file, you can incorporate the
  :py:func:`pysat.instruments.methods.general.load_csv_data` routine (see
  :ref:`api-methods-general`) into your :py:func:`load` method.
- The :py:class:`pysat.Meta` class holds metadata.  The :ref:`api-meta` object
  uses a :py:class:`pandas.DataFrame` indexed by variable name with columns
  for metadata parameters associated with that variable, including items like
  :py:data:`units` and :py:data:`long_name`. A variety of parameters are
  included by default and additional arbitrary columns are allowed. See
  :ref:`api-meta` for more information on creating the initial metadata. Any
  values not set in the load routine will be set to the default values for that
  label type.
- Note that users may opt for a different naming scheme for metadata parameters
  thus the most general code for working with metadata uses the attached labels:

.. code:: python

   # Update units to meters, 'm' for variable `var`, other metadata are set to
   # the defaults for this data type and label type
   inst.meta[var] = {inst.meta.labels.units: 'm'}

- If metadata is already stored with the file, creating the :py:class:`Meta`
  object is generally trivial. If this isn't the case, it can be tedious to
  fill out all information if there are many data parameters. In this case it
  may be easier to create a text file, though in many cases a separate function
  is defined to provide metadata for specific data types (see
  :py:func:`pysatSpaceWeather.instruments.methods.kp_ap.initialize_kp_metadata`).
  A basic convenience function is provided if you decide to use a text file.
  See :py:meth:`pysat.Meta.from_csv` for more information.

download
^^^^^^^^

Download support significantly lowers the hassle in dealing with any data set.
To fetch data from the internet the download method should have the signature

.. code:: python

   def download(date_array, data_path='', user=None, password=None):
       return

* :py:data:`date_array`, a list of dates for which data will be downloaded
* :py:data:`data_path`, the full path to the directory to store data
* :py:data:`user`, an optional string for the remote database username
* :py:data:`password`, an optional string for the remote database password

The routine should download the data and write it to the disk at the location
provided by 'data_path', which will be supplied by :py:mod:`pysat`.


.. _rst_new_inst-optattr:

Optional Attributes
-------------------

Several attributes have default values that you may need to change depending on
how your data and files are structured.

directory_format
^^^^^^^^^^^^^^^^

Allows the specification of a custom directory naming structure, where the files
for this Instrument will be stored within the :py:mod:`pysat` data directory.
If not set or if set to ``None``, it defaults to
``os.path.join('{platform}', '{name}', '{tag}', '{inst_id}')``. The string
format understands the keys :py:data:`platform`, :py:data:`name`,
:py:data:`tag`, and :py:data:`inst_id`. This may also be a function that takes
:py:data:`tag` and :py:data:`inst_id` as input parameters and returns an
appropriate string.

file_format
^^^^^^^^^^^

Allows the specification of a custom file naming format. If not specified or set
to ``None``, the file naming provided by the :py:meth:`list_files` method will
be used. The filename must have some sort of time dependence in the name, and
accepts all of the datetime temporal attributes in additon to
:py:data:`version`, :py:data:`revision`, and :py:data:`cycle`.  Wildcards
(e.g., ``'?'``) may also be included in the filename.

multi_file_day
^^^^^^^^^^^^^^

This defaults to ``False``, which means that the files for this data set have
one or less per day.  If your data set consists of multiple files per day, and
the files contain data across daybreaks, this attribute should be set to
``True``.

orbit_info
^^^^^^^^^^

A dictionary of with keys :py:data:`index`, :py:data:`kind`, and
:py:data:`period` that specify the information needed to create orbits for a
satellite Instrument.  See :ref:`api-orbits` for more information.

pandas_format
^^^^^^^^^^^^^

This defaults to ``True`` and assumes the data are organized as a time series,
allowing them to be stored as a :py:class:`pandas.DataFrame`. Setting this
attribute to ``False`` tells :py:mod:`pysat` that the data will be stored in an
:py:class:`xarray.Dataset`.


.. _rst_new_inst-optrout:

Optional Routines and Support
-----------------------------

Custom Keywords in Support Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If provided, :py:mod:`pysat` supports the definition and use of keywords for an
instrument module so that users may define their preferred default values. A
custom keyword for an instrument module must be defined in each function that
will receive that keyword argument if provided by the user. All instrument
functions, :py:func:`init`, :py:func:`preprocess`, :py:func:`load`,
:py:func:`clean`, :py:func:`list_files`, :py:func:`list_remote_files`, and
:py:func:`download` support custom keywords. The same keyword may be used in
more than one function but the same value will be passed to each.

An example :py:func:`load` function definition with two custom keyword
arguments.

.. code:: python

   def load(fnames, tag='', inst_id='', custom1=default1, custom2=default2):
       return data, meta

If a user provides :py:data:`custom1` or :py:data:`custom2` at instantiation,
then :py:mod:`pysat` will pass those custom keyword arguments to :py:func:`load`
with every call. All user provided custom keywords are copied into the
:py:class:`~pysat.Instrument` object itself under :py:attr:`inst.kwargs` for
use in other areas. All available keywords, including default values, are also
grouped by relevant function in a dictionary, :py:attr:`inst.kwargs_supported`,
attached to the :py:class:`Instrument` object. Updates to values in
:py:attr:`inst.kwargs` will be propagated to the relevant function the next
time that function is invoked.

.. code:: python

   inst = pysat.Instrument(platform, name, custom1=new_value)

   # Show user supplied value for custom1 keyword for the 'load' function
   print(inst.kwargs['load']['custom1'])

   # Show default value applied for custom2 keyword
   print(inst.kwargs_supported['load']['custom2'])

   # Show keywords reserved for use by pysat
   print(inst.kwargs_reserved)

If a user supplies a keyword that is reserved or not supported by
:py:mod:`pysat`, or by any specific instrument module function, then an error is
raised. Reserved keywords are :py:data:`fnames`, :py:data:`inst_id`,
:py:data:`tag`, :py:data:`date_array`, :py:data:`data_path`,
:py:data:`format_str`, :py:data:`supported_tags`, :py:data:`start`,
:py:data:`stop`, and :py:data:`freq`.

preprocess
^^^^^^^^^^

First custom function applied, once per instrument load.  Designed for standard
instrument preprocessing.

.. code:: python

   def preprocess(self):
       return

``self`` is a :py:class:`pysat.Instrument` object. :py:func:`preprocess` should
modify ``self`` in-place as needed; equivalent to a custom routine.

clean
^^^^^

Cleans instrument for levels supplied in inst.clean_level.
  * 'clean' : expectation of good data
  * 'dusty' : probably good data, use with caution
  * 'dirty' : minimal cleaning, only blatant instrument errors removed
  * 'none'  : no cleaning, routine not called

.. code:: python

   def clean(self):
       return

``self`` is a :py:class:`pysat.Instrument` object. :py:func:`clean` should
modify ``self`` in-place as needed; equivalent to a custom routine.
:py:func:`clean` is allowed to raise logger messages, warnings, and errors. If
the routine does this, be sure to test them by assigning the necessary
information to the :py:attr:`_clean_warn` attribute, described in
:ref:`Testing Support <rst_new_inst-test>`. :py:func:`clean` may also
re-assign the cleaning level if appropriate. If you do this, be sure to raise a
logging warning, so that users are aware that this change is happening and why
the clean level they requested is not appropriate.

list_remote_files
^^^^^^^^^^^^^^^^^

Returns a list of available files on the remote server. This method is required
for the Instrument module to support the :py:meth:`download_updated_files`
method, which makes it trivial for users to ensure they always have the most up
to date data. :py:mod:`pysat` developers highly encourage the development of
this method, when possible.

.. code:: python

    def list_remote_files(tag='', inst_id='', start=None, stop=None, ...):
        return list_like

This method is called by several internal :py:mod:`pysat` functions, and can be
directly called by the user through the :py:meth:`inst.remote_file_list` method.
The user can search for subsets of files through optional keywords, such as:

.. code:: python

    inst.remote_file_list(year=2019)
    inst.remote_file_list(year=2019, month=1, day=1)


Logging
-------

:py:mod:`pysat` is connected to the Python logging module. This allows users to
set the desired level of direct feedback, as well as where feedback statements
are delivered. The following line in each module is encouraged at the top-level
so that the instrument module can provide feedback using the same mechanism

.. code:: Python

    logger = pysat.logger


Within any instrument module,

.. code:: Python

    pysat.logger.info(information_string)
    pysat.logger.warning(warning_string)
    pysat.logger.debug(debug_string)

will direct information, warnings, and debug statements appropriately.


.. _rst_new_inst-test:

Testing Support
===============
All modules defined in the ``__init__.py`` for pysat/instruments are
automatically tested when :py:mod:`pysat` code is tested. To support testing all
of the required routines, additional information is required by :py:mod:`pysat`.

Below is example code from the :py:mod:`pysatMadrigal` Instrument module,
dmsp_ivm.py. The attributes are set at the top level simply by defining
variable names with the proper info. The various satellites within DMSP, F11,
F12, F13 are separated out using the inst_id parameter. 'utd' is used as a tag
to delineate that the data contains the UTD developed quality flags.

.. code:: python

   # ------------------------------------------
   # Instrument attributes

   platform = 'dmsp'
   name = 'ivm'
   tags = {'utd': 'UTDallas DMSP data processing',
           '': 'Level 2 data processing'}
   inst_ids = {'f11': ['utd', ''], 'f12': ['utd', ''], 'f13': ['utd', ''],
               'f14': ['utd', ''], 'f15': ['utd', ''], 'f16': [''], 'f17': [''],
               'f18': ['']}

   # ...more useful code bits here...

   # ------------------------------------------
   # Instrument test attributes

   _test_dates = {
       'f11': {tag: dt.datetime(1998, 1, 2) for tag in inst_ids['f11']},
       'f12': {tag: dt.datetime(1998, 1, 2) for tag in inst_ids['f12']},
       'f13': {tag: dt.datetime(1998, 1, 2) for tag in inst_ids['f13']},
       'f14': {tag: dt.datetime(1998, 1, 2) for tag in inst_ids['f14']},
       'f15': {tag: dt.datetime(2017, 12, 30) for tag in inst_ids['f15']},
       'f16': {tag: dt.datetime(2009, 1, 1) for tag in inst_ids['f16']},
       'f17': {tag: dt.datetime(2009, 1, 1) for tag in inst_ids['f17']},
       'f18': {tag: dt.datetime(2017, 12, 30) for tag in inst_ids['f18']}}

   # ...more useful code bits follow...


The rationale behind the variable names is explained above under
:ref:`rst_new_inst-naming`.  What is important here are the
:py:attr:`_test_dates`. Each of these points to a specific date for which the
unit tests will attempt to download and load data as part of end-to-end testing.
Make sure that the data exists for the given date. The tags without test dates
will not be tested. The leading underscore in :py:attr:`_test_dates` ensures
that this information is not added to the instrument's meta attributes, so it
will not be present in Input/Output operations.

The standardized :py:mod:`pysat` tests are available in
:py:mod:`pysat.tests.instrument_test_class`. The test collection in
test_instruments.py imports this class, collects a list of all available
instruments (including potential :py:data:`tag`/:py:data:`inst_id`
combinations), and runs the tests using pytestmark.  By default,
:py:mod:`pysat` assumes that your instrument has a fully functional download
routine, and will run an end-to-end test.  If this is not the case, see the next
section.

Another important test is for warnings and the re-setting of clean levels that
may come up when cleaning data. These may be specified using the
:py:attr:`_clean_warn` attribute, which should point to a dictionary that has a
tuple of four elements as the value. The first element should be 'logger',
'warning', or 'error', specifying the method through which the warning is being
reported. The second element specifies either the logging level (as a string)
or the warning/error type (e.g., ``ValueError``). The third element provides the
warning message as a string and the final element provides the expected clean
level after running the clean routine.

.. code:: python

   # ------------------------------------------
   # Instrument test attributes

   _clean_warn = {inst_id: {tag: {'dusty': ('logger', 'WARN', "I am a warning!", 'clean')} for tag in inst_ids[inst_id]} for inst_id in inst_ids.keys()}


   
.. _rst_test-special:

Special Test Configurations
---------------------------

No Download Available
^^^^^^^^^^^^^^^^^^^^^

Some instruments simply don't have download routines available.  It could be
that data is not yet publicly available, or it may be a model run that is
locally generated.  To let the test routines know this is the case, the
:py:attr:`_test_download` flag is used.  This flag uses the same dictionary
structure as :py:attr:`_test_dates`.

For instance, say we have an instrument team that wants to use :py:mod:`pysat`
to manage their data products.  Level 1 data is locally generated by the team,
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

        return


.. _rst_test-temp:

Supported Instrument Templates
------------------------------

Instrument templates may be found at :py:mod:`pysat.instruments.templates`
and supporting methods may be found at :py:mod:`pysat.instruments.methods`.

General
^^^^^^^

A general instrument template is included with :py:mod:`pysat`,
:py:mod:`pysat.instruments.templates.template_instrument`, that has the full set
of required and optional methods, and docstrings, that may be used as a starting
point for adding a new instrument to :py:mod:`pysat`.

Note that there are general supporting methods for adding an Instrument.
See :ref:`api-methods-general` for more.

This tells the test routines to skip the download and load tests for Level 1
data. Instead, the download function for this flag will be tested to see if it
has an appropriate user warning that downloads are not available.

Note that :py:mod:`pysat` assumes that this flag is True if no variable is
present. Thus, specifying only ``_test_download = {'': {'Level_1': False}}``
has the same effect, and Level 2 tests will still be run.

Load Options
^^^^^^^^^^^^

As there may be different ways to load data using custom keyword arguments, the
:py:attr:`_test_load_opt` attribute can be used to support testing of each
custom keyword argument option.  These should be included as a list that is
accessed through a dictionary with :py:attr:`inst_id` and :py:attr:`tag` keys.

.. code:: python

   platform = 'observatory'
   name = 'data'
   tags = {'historic': 'Historic data',
           'newfangled': 'Newfangled data, has different formatting options'}
   inst_ids = {'': ['historic', 'newfangled']}
   _test_dates = {'': {'historic': dt.datetime(1900, 1, 1),
                       'newfangled': dt.datetime(2000, 1, 1)}}
   _test_load_opt = {'': {'newfangled': [{'historic_format': True},
                                         {'historic_format': False}]}}


FTP Access
^^^^^^^^^^

Another thing to note about testing is that the CI environment used to
automate the tests is not compatible with FTP downloads.  For this reason,
HTTPS access is preferred whenever possible.  However, if this is not the case,
the :py:attr:`_test_download_ci` flag can be used.  This behaves similarly,
except that it only runs the download tests locally and will skip them if
on a CI server.

.. code:: python

   platform = 'newsat'
   name = 'data'
   tags = {'Level_1': 'Level 1 data, FTP accessible',
           'Level_2': 'Level 2 data, available via the web'}
   inst_ids = {'': ['Level_1', 'Level_2']}
   _test_dates = {'': {'Level_1': dt.datetime(2020, 1, 1),
                       'Level_2': dt.datetime(2020, 1, 1)}}
   _test_download_ci = {'': {'Level_1': False}}

Note that here we use the streamlined flag definition and only call out the
tag that is False.  The other is True by default.

Password Protected Data
^^^^^^^^^^^^^^^^^^^^^^^

Another potential issue is that some instruments have download routines,
but should not undergo automated download tests because it would require
the  user to save a password in a potentially public location.  The
:py:attr:`_password_req` flag is used to skip both the download tests and the
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
