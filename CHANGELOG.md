Change Log
==========
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

[3.0.6] - 2022-12-21
--------------------
* Bug Fix
  * Ensure pysat tests do not store temporary directory to file
  * Updated links for supported instruments in documentation
* Deprecations
  * `pysat_testing2d_xarray` instrument deprecated and replaced by
    `pysat_ndtesting`
* Maintenance
  * Updated pytest syntax to remove nose backwards-compatibility
  * Fixed NEP29 compliance
  * Updated Github Actions versions
  * Improved docstrings
  * Fixed a bug where a deprecation warning was thrown incorrectly
  * Add pysatModels to pysat instrument count
  * Update contributing document
  * Added support for testing with python 3.6, updated reported
    minimum supported Python version to 3.6

[3.0.5] - 2022-10-14
--------------------
* Maintenance
  * Update usage of logger throughout code.
  * Update NEP29 minimum CI numpy version to 1.20
* Bug Fix
   * Updated meta.py so that internal assignment of None to children is not
     converted to NaN when using pandas>=1.5.0

[3.0.4] - 2022-08-29
--------------------
* Maintenance
  * Removed version cap on xarray
* Bug Fix
   * Improved compatibility with xarray 2022.06 when accessing data via slices
   * Fixed a bug for fractional seconds in `methods.testing.generate_times`.
   * Fixed a bug for testing FTP instruments in a CI environment.

[3.0.3] - 2022-07-29
--------------------
* Maintenance
   * Added temporary version limit to xarray due to change in indexing


[3.0.2] - 2022-07-22
--------------------
* New Features
   * Added the property `empty_partial` to the Constellation class
   * Added the option to apply custom functions at the Constellation or
     Instrument level within the Constellation class
   * Added option to load Constellation for registered Instruments using lists
     of platforms, names, tags, and/or inst_ids, which are new attributes
   * Added hidden Constellation methods to determine unique attribute elements
     and set Instrument attributes across all instruments
   * Added hidden Constellation method to sequentially call Instrument methods
   * Extended Constellation unit tests
   * Added more quality checks to the Constellation initialization
   * Standardized Instrument instantiation to always define `inst_module`
   * Extended testing options for `pysat.utils.testing` functions
   * Added `start_time` keyword for test instruments
   * Added `max_latitude` keyword for non-model test instruments
   * Added `_test_download_ci` as a standard attribute for `pysat.Instrument`
   * Added a testing model similar to TIEGCM to
     `pysat.instruments.pysat_testmodel` as tag='pressure_levels'.
   * Added the capability to test loading with optional kwargs through
     `_test_load_opt` instrument attribute
   * Added `rename` and `add_epoch_metadata` methods to the Meta class
   * Added I/O utilities to the utility module, extracting existing methods
     from the Instrument class and core utility module.
   * Added a warning evaluation and directory creation functions to
     `pysat.utils.testing`.
   * Added the ability to only download new files if remote file listing
     capabilities are not available for the Instrument.
   * Added kwargs for epoch units and origin in `pysat.utils.io.load_netcdf`.
   * Vectorized `Meta.var_case_name` and `Meta.attr_case_name` to support
     list of str as input as well as str.
   * Added a time function to calculate decimal year from datetime.
   * Allow `Instrument.rename` to take a fuction or mapping dict as input,
     after adapting routine to use `Meta.rename`
   * Added an update method and type evaluation method to MetaLabels.
   * Added a new MetaHeader class for holding global metadata.
   * Added a pysat Instrument for loading pysat-written NetCDF4 files.
   * Allowed MetaLabels to be expanded through setting new Meta data values.
   * Added support for user variables when parsing template filenames
     in `pysat.utils.files`.
   * Improved robustness of parsing delimited files.
   * Updated `pysat.Instrument.pandas_format` so that changes to setting
     are immediately reflected by changes to Instrument object.
   * Added a test function for bad class/function/method input to reduce
     duplicate code and improve message test combliance
   * Added support for filtering basic netCDF4 metadata when loading via
     `pysat.utils.io.load_netcdf`.
   * Added support for user developed functions to filter metadata as it
     loaded from disk but before assignment to a `pysat.Meta` instance.
   * Added `meta.to_dict` to support creating more compliant
     netCDF files.
   * Added `meta.default_to_netcdf_translation_table`,
     `default_from_netcdf_translation_table` and
     `apply_table_translation` to `pysat.utils.io` to support
     improved compatability of pysat netcdf files without user code
     changes.
   * Added `drop_meta_labels` kwarg to `pysat.utils.io.load_netcdf` to
     support easy removal of unwanted metadata during loading.
   * Added support for `meta_processor` in `pysat.utils.io.load_netcdf`
     and `pysat.utils.io.inst_to_netcdf` enabling developers to easily modify
     metadata before it is loaded from/written to storage.
   * Intermediate missing directories are now created as needed when writing
     files using `pysat.utils.io.inst_to_netcdf`.
   * Condensed code present in both pandas and xarray into
     `pysat.utils.io.meta_array_expander`.
   * Non-default Meta.labels are now retained by Instrument if defined by
     underlying support module.
   * Made test data more consistent across pysat testing instruments.
   * Added `pysat.Instrument.vars_no_time` function to return data variables
     excluding the main time index.
   * Added support for additional metdata and other file handling options
     to general 'pysat', 'netcdf' instrument.
   * Added keyword `decode_times` to flag using xarray or pysat processing
     of times when loading a file via `pysat.utils.io.load_netcdf`.
   * Added `pysat.utils.io.xarray_all_vars` which returns a list of all variables,
     coordinates, and dimensions.
   * Added more volume units to `pysat.utils.scale_units`
   * Added `assert_isinstance` and `assert_hasattr` to `pysat.utils.testing`
* Deprecations
   * Removed `freq` as a standard kwarg for `pysat.Instruments.download`
   * Deprecated `_test_download_travis` as a standard attribute for
     `pysat.Instrument`.  The function is replaced by `_test_download_ci`
   * Deprecated
     `pysat.tests.instrument_test_class.initialize_test_inst_and_date`,
     which is moved to `pysat.tests.classes.cls_instrument_library`.
   * Deprecated `pysat.tests.instrument_test_class.InstTestClass`, which is
     replaced by `pysat.tests.classes.cls_instrument_library.InstLibTests`.
   * Deprecated `pysat.Instrument._filter_netcdf4_metadata` and replaced it
     with `pysat.utils.io.filter_netcdf4_metadata`.
   * Changed `fname` from a kwarg to an arg in `pysat.Instruments.to_netcdf4`
   * Deprecated support for 2D pandas datasets
   * Deprecated `pysat.instruments.pysat_testing_xarray`
   * Deprecated usage of higher order metadata
   * Deprecated `pysat.Instrument.generic_meta_translator` which is replaced
     by `pysat.utils.io.apply_table_translation_to_file`.
   * Deprecated the general instrument method, `convert_timestamp_to_datetime`,
     which is replaced by new functionality in `load_netcdf`.
* Documentation
   * Moved logo to 'docs\images'
   * Improved consistency of headers throughout documentation
   * Added more reference labels to documentation
   * Implemented use of Python formatting in documentation examples
   * Fixed bad section labels in docstrings
   * Fixed noindex warning
   * Fixed redirecting links
   * Made changelog style and line length consistent
   * Added a paragraph describing how to access Instrument sub-module
     docstrings from an instantiated Instrument in an interactive session
   * Updated examples in docstrings
   * Improved docstring style and consistency
   * Added docstring linting via flake-docstrings and hacking to CI tests
   * Added clarification to the tutorials
   * Added limitations to the `listify` docstring
   * Updated image link in `README.md` to display in more environments.
   * Updated `tag` and `inst_id` keywords and docstrings to new standards
   * Added example for version checking when writing tests for packages that
     rely on pysat
* Bug Fix
   * Fixed default MetaLabel specification in `pysat.utils.load_netcdf4`
   * Fixed `parse_delimited_filename` output consistency and ability to handle
     leading and trailing non-parsed text in filenames (e.g., file extensions)
   * Added `decode_timedelta=False` for loading xarray from netcdf4 (#823)
   * Closed links to open files when loading data through xarray (#887)
   * Fixed an issue in generating filenames for `pysat.Instrument._iter_list`
   * Allow `tag` and `inst_id` to be specified as None (#892)
   * Fixed a bug in `pysat.utils.time.create_datetime_index` (#906)
   * Fixed a bug in `pysat.utils.scale_units` and ensured '/cc' compatibility.
   * Added a warning if `inst_module` and `platform`/`name` are used to
     instantiate an instrument (#850). In case of this, `inst_module` takes
     priority.
   * Fixed a bug when instantiating empty `pysat.Instrument()` (#851)
   * Fixed IndexError encountered when loading a multi-day file by filename with
     no data for that day.
   * Added logging output when metadata not assigned due to a lack of
     instrument data (#924)
   * Fixed a bug where empty check for xarray instruments fail when time not
     present. (#922)
   * Improved feedback when users try to set meta with an array.
   * Fixed a bug that expected special treatment by `Instrument.data` type in
     `utils.coords.update_longitude`
   * Fixed pysat_testmodel Instrument longitude range
   * Corrected link to testing badge in README.md
   * `from_os` now always returns a sorted Series.
   * Moved function call for Instrument modules init function to end of
     pysat.Instrument instantiation to ensure Instrument is complete when passed
     to init.
   * Refactored `pysat.Instrument.generic_meta_translator` to use
     `pysat.Meta.to_dict` and the latest metadata label standards.
   * Prevent stale data paths stored by pysat from being reassigned if
     path is no longer in `pysat.params['data_dirs']`.
   * Added missing metadata in testing instruments.
   * Corrected identification of string data for xarray in
     `pysat.Instrument._get_data_info`.
* Maintenance
   * Added unit tests for deprecation warnings related to io_utils reorg.
   * Added missing unit tests for `pysat.utils.time`
   * Added missing unit tests for `pysat.utils.file.parse_delimited_filename`
   * Streamlined unit tests for `test_orbits`
   * Moved metadata generation for test instruments to `methods.testing`
   * Added integration tests for test instrument kwargs
   * Updated class declaration to be consistent with python 3 standards
   * Update usage of caplog and capsys in unit tests
   * Reorganized tests for the `pysat.Instrument` class into multiple files
   * Updated unit tests for `pysat.Instrument` with pytest.mark.parametrize
   * Update minimum numpy in CI tests to 1.19 following NEP29
   * Made `InstLibTests` more portable to streamline user implementation of the
     standard end-to-end instrument tests.
   * Moved test classes to `pysat.tests.classes`
   * Reorganized the core test_instrument.py as a series of classes
   * Separated MetaLabels tests from Meta test class
   * Organized and reduced duplication in the Meta test class
   * Added CI reports for supported data products
   * Added a cap on coveralls to ensure success of continuous integration
   * Updated tests in `test_meta` to search all warnings, not just the first
   * Updated pandas syntax to be compatible with pandas 2.0 (pandas 1.4
     deprecations)
   * Cleaned up excess variables upon import
   * Removed `data_path` check from `pysat.instruments.methods.general.list_files`
   * Compatible with netCDF v1.6.0

[3.0.1] - 2021-07-28
--------------------
* New Features
   * Added a routine for loading CSV files into a pandas DataFrame from a list
     of filenames.
   * Added check for supported `tag` and `inst_id` at pysat.Instrument
     instantiation. (#784)
   * Expanded Constellation utility by:
      * Adding common properties: `empty`, `index`, `date`, `today`,
        `yesterday`, `tomorrow`, and `variables` (#764)
      * Improving the printed output to inform user of the Constellation
        contents (#764)
      * Added methods to download data and create a common time index. (#764)
   * Added utils.listify, a function that returns a list of whatever is input.
     (#766)
    * Added a warning for download requests that result in an empty date range.
* Deprecations
* Documentation
   * Added missing information about date formatting to file listing docstrings.
   * Added example for registering external instrument support. (#837)
* Bug Fix
   * Changed pysat.Instruments.orbits iteration to return a copy of the
     Instrument rather than the Instrument itself. Provides robustness against
     garbage collection. (#770)
   * Improved error messages for cases where slice of data may not exist (#761)
   * Improved windows compatibility (#57, #790)
   * Fixed Instrument.load bug that prevented use of instrument specific kwargs
   * Added pytest as a package requirement (#819)
   * Fixed pysat.utils.listify for empty list inputs (#830)
* Maintenance
   * Changed pysat.Instrument from treating all support functions as partial
     functions to retaining the original form provided by developer
   * Migrates CI testing to Github Actions
   * Improved maintenance of documentation build
   * Added a check for use of reserved keywords at instantiation
   * Tests compatible with pysatSpaceWeather 0.0.4 (#782)
   * Improved pandas 1.3.0 compliance

[3.0.0] - 2021-04-01
--------------------
* New Features
   * Added registry module for registering custom external instruments
   * Added Meta.mutable flag to control attribute mutability
   * Added MetaLabels class to manage metadata labeling
   * Unit tests are now pytest compatible, use parametrize, and have improved
     messages when failures are encountered
   * Added altitudes to test instruments
   * New flags added to instruments to streamline unit testing:
     `_test_download`, `_test_download_travis`, `_password_req`
   * `strict_time_flag` now defaults to True
   * Use of start/stop notation in remote_file_list
   * Added variable rename method to Instrument object (#91)
   * Added support for loading more than one day/file (#56)
   * Added support for iterating over a dataset a with a loaded data width and
     stepsize larger than a single day/file
   * Added check for inconsistent inputs when loading data via Instrument
   * Added file locking for thread-safe behavior (#304)
   * Allow the Instrument object to be initialized with optional kwargs for any
     of the standard methods (not just load).
   * Added support for 'cycle' in addition to 'version' and 'revision' for
     filename conventions.
   * Integrated Custom class directly into Instrument to support mixed use
     of Constellation/Instrument objects in code (#540)
   * Made underlying custom data structures visible (#529)
   * Updated data_mode method name to custom_attach for the Constellation
     object (#540)
   * Added a display utility for discovering pysat Instrument data sets.
   * Added testing utility functions.
   * Added support for multiple pysat data directories
   * Reorganized .pysat directory to store instrument information under
     .pysat/instruments and .pysat/instruments/archive
   * Added pysat.params, a central location to store and modify pysat default
     parameters. File stored at .pysat/pysat_settings.json
   * Added `warn_empty_file_list` to pysat.params to provide a warning if no
     Instrument files are found. Default is False.
   * Updated default pysat directory organization template
   * Added support for dual specification of Instruments to include in a
     Constellation
   * Added function to transition pysat managed data files to a user
     provided template.
   * Allow `directory_format` input to `Instrument` to be a function
   * Adopted standard for bounds. `stop` is an inclusive bound, `end` is
     exclusive
   * Added support for SLT calculations outside [0, 24)
   * Added support for continuous SLT calculations when loading multiple days
   * Instrument support functions now respond to local changes in
     Instrument.kwargs
   * Added support for pysat.Instrument, Files, and Orbits equality comparisons
   * Added .copy function to Instrument, Files, and Orbits classes
   * Updated Parameters to ensure paths provided for pysat.params['data_dirs']
     are created if they don't already exist
   * Added funtion to get file attributes, utils.files.get_file_information
* Deprecations
   * Migraged instruments to pysatMadrigal, pysatNASA, pysatSpaceWeather,
     pysatIncubator, pysatModels, pysatCDAAC, and pysatMissions
   * Migrated file methods to pysat.utils.files (#336)
   * Renamed `sat_id` Instrument keyword argument to `inst_id`
   * Removed ssnl
   * Removed utils.stats
   * Removed model_utils
   * Removed deprecated pandas.Panel
   * Import datetime class from datetime module, not pandas
   * Import DataFrame and Series classes directly from pandas, not pysat
   * Removed coords.scale_units
   * Removed time.season_date_range
   * Moved methods.nasa_cdaweb.list_files to methods.general
   * DeprecationWarning for strict_time_flag only triggered if sloppy data is
     found
   * Changed the custom function attachment input to allow keyword argument use
     when additional function input is required
   * Removed python 2.7 syntax
   * Removed utils.coords.geodetic_to_geocentric
   * Removed utils.coords.geodetic_to_geocentric_horizontal
   * Removed utils.coords.spherical_to_cartesian
   * Removed utils.coords.global_to_local_cartesian
   * Removed utils.coords.local_horizontal_to_global_geo
   * Addressed several Warnings raised by incorrect use of dependent packages
   * Deprecated use of `inst_id` for number of simulated samples for test
     instruments
   * Removed writing of custom Meta attributes when producing netCDF4 files
   * Removed unneeded description.txt file, using README instead
   * Changed `pysat.instruments.methods.general.list_files` kwarg
     `fake_monthly_files_from_daily` to `file_cadence`
   * Changed name of Instrument method `default` to `preprocess`
   * Removed `pysat.data_dir`. Information now at `pysat.params['data_dirs']`.
   * Moved `pysat.Instrument._filter_datetime_input` to
     `pysat.utils.time.filter_datetime_input`
   * Deprecated `pysat.utils.set_data_dir`
   * Changed `name` kwarg in Constellation to `const_module`
   * Removed unnecessary Instrument attribute `labels`
   * Removed unnecessary Instrument kwargs
   * Removed the Custom class, incorporating it into Instrument
   * Removed deprecated calls to 'modify' type custom functions
* Documentation
   * Added info on how to register new instruments
   * Fixed description of `tag` and `inst_id` behaviour in testing instruments
   * Added a tutorial for developers of instrument libraries for pysat
   * Updated instrument templates
   * Added .zenodo.json file, to improve specification of authors in citation
   * Improved `__str__` and `__repr__` functions for basic classes
   * Improved docstring readability and consistency
   * Added Travis-CI testing for the documentation
   * Added a style guide for developers
   * Updated loading data flow figure
   * Scrubbed the documentation, ensuring examples, tutorials, and descriptions
     match the current implementation and code structure
* Bug Fix
   * Updated Instrument.concat_func to behave as described in the docstring
   * Fixed custom instrument attribute persistence upon load
   * Improved string handling robustness when writing netCDF4 files in Python 3
   * Improved pandas 1.1.0 compatibility in tests
   * Fixed coupling of two_digit_year_break keyword to underlying method in
     methods.general.list_files
   * Fixed additional file date range for monthly data with gaps
   * Fixed custom Meta attributes removal when transferred to instrument (#615)
   * Corrected iteration over Instrument within list comprehension
   * Removed unused input arguments
   * Corrects Instrument today, yesterday, and tomorrow methods by implementing
     datetime.datetime.utcnow
   * Ensured pysat.Meta instances are immutable at Instrument instantiation
   * Removed weak reference back to Instrument within Files class
   * Fixed access of xarray data with more than one dimension (#471)
   * Improved robustness of `eval(inst.__repr__())` (#636)
   * Fixed `calc_solar_local_time` for data sets with longitude coordinates
   * Fixed .copy() when pysat.Instrument instantiated with `inst_module` (#728)
   * Modified storage of Instrument.kwargs to include all methods so that
     `eval(Instrument.__repr__())` works in more cases
   * Modified storage of Instrument.kwargs to only include user supplied
     keywords
   * Improved robustness when working with file dates that aren't centered on
     midnight
   * Added basic valid path check to `pysat.utils.files.check_and_make_path`
* Maintenance
   * nose dependency removed from unit tests
   * Specified `dtype` for empty pandas.Series for forward compatibility
   * Removed wildcard imports, relative imports
   * Include flake8 check as part of testing suites
   * Improved unit testing coverage of instrument functions and instrument
     object
   * Added tests for Instrument attributes `acknowledgements` and `references`
   * Removed implicit conversion to integers in
     methods.general.convert_timestamp_to_datetime
   * Simplified internal logic in Instrument class
   * Moved setup metadata to setup.cfg
   * Improved instrument tests for files
   * Used dt.timedelta instead of pds.DateOffSet where possible
   * Reduced code duplication throughout package
   * Reduced unused code snippets throughout
   * Ensured download start time is used
   * Condensed testing support functions into methods/testing.py
   * Fixed a bug with usage of numpy.dtype for numpy 1.20 compatibility
   * Updated usage of pds.index.to_native_types() to pds.index.astype(str)
     for pandas 2.0 compatibility (#737)
   * Check type as float rather than np.float for future numpy compatibility
     (#740)
   * Verified usage of inst.loc[slice, keyword] will continue to work in
     pandas 2.0 (#738)

[2.3.0] - 2021-04-01
--------------------
* Allow use of new Instrument kwarg, `inst_id` (replaces `sat_id`)
* Allow limited use of new list_files kwarg, `file_cadance`
* Added support for `pysat.params['data_dirs']`, the replacement
  for `pysat.data_dir` in pysat 3.0.0
* Deprecation warnings added to:
   * Instrument class (old meta labels, `sat_id`, `default`, `multi_file_day`,
     `manual_org`, and `_filter_datetime_input`, `data_dir`)
   * pysat.instruments.methods.general.list_files kwarg
     `fake_montly_files_from_daily`
   * pysat.instruments.methods.testing.generate_times kwarg `sat_id`
   * Constellation class kwarg `name`
   * Custom class
   * functions from `_files` class
   * functions from `ssnl` module
   * Instrument modules:
      * the pysatCDAAC: cosmic_gps
      * the pysatIncubator: champ_star, demeter_iap, superdarn_grdex,
        supermag_magnetometer
      * the pysatMadrigal: jro_isr, dmsp_ivm
      * the pysatSpaceWeather: sw_dst, sw_f107, sw_kp
      * the pysatModels: ucar_tiegcm
      * the pysatNASA: cnofs_ivm, cnofs_plp, cnofs_vefi, de2_lang, de2_nacs,
        de2_rpa, de2_wats, icon_euv, icon_fuv, icon_ivm, icon_might, iss_fpmu,
        omni_hro, rocsat1_ivm, sport_ivm, timed_saber, timed_see
   * The usage of a numeric string for `sat_id` to specify number of points
     in test instruments
   * SpaceWeather, Incubator (DEMETER), Madrigal, CDAWeb, and ICON instrument
     methods
   * The DE2 and ICON Constellation objects
   * pysat.utils.set_data_dir
* Documentation
   * Updated docstrings with deprecation notes
* Bug Fix
   * Closes files after download in NASA CDAWeb methods
   * Updated the ICON constellation object to reflect new instrument standards
* Added version cap for numpy

[2.2.2] - 2020-12-31
--------------------
* New Features
   * netCDF4 files produced using `to_netcdf4()` now have an unlimited
     time dimension
* Documentation
   * Updated guidance on numpy version for installation
* Bug Fix
   * Updated madrigal methods to simplify compound data types and enable
     creation of netCDF4 files using `self.to_netcdf4()`.
   * Updated ICON support for latest file organization on SSL servers

[2.2.1] - 2020-07-29
--------------------
* Documentation
   * Improved organization of documentation on ReadTheDocs
* Bug Fix
   * Adopted .readthedocs.yml to restore online documentation on ReadTheDocs
   * Modified MANIFEST.in to include pysat_testing instruments
   * Rename default branch as `main`

[2.2.0] - 2020-07-24
--------------------
* New Features
   * Decreased time to load COSMIC GPS data by about 50%
   * Added DE2 Langmuir Probe, NACS, RPA, and WATS instruments
   * Updated `test_files.py` to be pytest compatible
   * Added check to ensure non-pysat keywords supplied at instantiation
     are supported by underlying data set methods
   * Updates to instrument testing objects for consistency
   * Changed madrigal methods to use `madrigalWeb` as a module rather than
     calling it externally
   * Added warning when FillValue metadata could lead to unexpected results
     when writing a netCDF4 file
   * Use conda to manage Travis CI test environment
   * Update ICON instrument file structure
   * Added NaN filter for metadata when writing netCDF4 files
   * Test instruments now part of compiled package for development elsewhere
   * Reviewed and improved documentation
   * Custom instrument keywords and defaults are now always found in inst.kwargs
   * Added support for ~ and $ variables when setting pysat data dir
   * Added custom.attach to make transitions to v3.0 easier
* Deprecation Warning
   * custom.add will be renamed custom.attach in pysat 3.0.0
   * Several functions in coords will be removed in pysat 3.0.0.  These
     functions will move to pysatMadrigal
      * geodetic_to_geocentric
      * geodetic_to_geocentric_horizontal
      * spherical_to_cartesian
      * global_to_local_cartesian
      * local_horizontal_to_global_geo
   * methods.nasa_cdaweb.list_files will move to methods.general.list_files in
     pysat 3.0.0.
* Documentation
   * Fixed description of tag and sat_id behaviour in testing instruments
   * Added discussion of github install, develop branches, and reqs to docs
* Bug Fix
   * `_files._attach_files` now checks for an empty file list before appending
   * Fixed boolean logic when checking for start and stop dates in
     `_instrument.download`
   * Fixed loading of COSMIC atmPrf files
   * Fixed feedback from COSMIC GPS when data not found on remote server
   * Fixed deprecation warning for pysat.utils.coords.scale_units
   * Fixed a bug when trying to combine empty f107 lists
   * Fixed a bug where `remote_file_list` would fail for some instruments.
   * Made import of methods more robust
   * Fixed `SettingWithCopyWarning` in `cnofs_ivm` cleaning routine
   * Fixed cosmic load method definition to include altitude_bin
   * Fixed pysat_testing method definition to include mangle_file_dates keyword
   * Added small time offsets (< 1s) to ensure COSMIC files and data have unique
     times
   * Updates to Travis CI environment
   * Removed `inplace` use in xarray `assign` function, which is no longer
     allowed
   * Removed old code and incorrect comments from F10.7 support
   * Updated use of numpy.linspace to be compatible with numpy 1.18.
   * Fixed output of orbit_info during print(inst)
   * Fixed a bug when requesting non-existent files from CDAWeb (#426)
   * Improved compatibility of parse_delimited_filenames (#439)
   * Fixed bug assigning dates to COSMIC files
   * Fixed bug limiting local time orbit breakdowns for instruments much slower
     than 1 Hz

[2.1.0] - 2019-11-18
--------------------
* New Features
   * Added new velocity format options to utils.coords.scale_units
   * Improved failure messages for utils.coords.scale_units
   * Added some tests for model_utils
   * Added option to to_netCDF that names variables in the written file
     based upon the strings in the Instrument.meta object
   * Improved compatibility with NASA ICON's file standards
   * Improved file downloading for Kp
   * Added keyword ignore_empty_files to pysat.Instrument and Files objects
     to filter out empty files from the stored file list
   * Added slice and list ability to meta
   * Converted all print statements to logging statements
   * Updated cleaning routines for C/NOFS IVM
   * Added S4 scintillation data to the cosmic-gps instrument
   * pysat no longer creates a default data directory. User must specify
     location
   * User set custom attributes are transparently stored within Meta object and
     are available via both Instrument and Meta.
   * Improved robustness of required library specification across multiple
     platforms
* Code Restructure
   * Move `computational_form` to `ssnl`, old version is deprecated
   * Move `scale_units` to `utils._core`, old version is deprecated
   * Replace `season_date_range` with `create_date_range`, old version is
     deprecated
   * Added deprecation warnings to stat functions
   * Added deprecation warnings to `ssnl` and `model_utils`
   * Removed `pysat_sgp4` instrument
   * Added cleaning steps to the C/NOFS IVM ion fraction data
* Bug fix
   * Fixed implementation of utils routines in model_utils and jro_isr
   * Fixed error catching bug in model_utils
   * Updated Instrument.concat_data for consistency across pandas and xarray.
     Includes support for user provided keywords.
   * Fixed error introduced by upstream change in NOAA F10.7 file format
   * Fixed bugs in DEMETER file reading introduced by changes in codecs
   * Fixed issue with data access via Instrument object using time and name
     slicing and xarray. Added unit test.
   * Updated travis.yml to work under pysat organization
   * Added missing requirements (matplotlib, netCDF4)
   * Fixed a bug when trying to combine empty kp lists
   * Updated travis.yml to work with python 2.7.15 and beyond
   * Unit tests reload pysat_testing_xarray for xarray tests
   * Updated setup.py to not overwrite default `open` command from `codecs`
   * Updated Travis CI settings to allow forks to run tests on local travis
     accounts
   * Fixed keep method to be case insensitive
   * Fixed a bug with COSMIC GPS downloads
   * Fixed selection bugs in the DEMETER IAP, CNOFS IVM, and model_utils
     routines
   * Updated URL link in setup.py
* Documentation
   * Added info on how to cite the code and package.
   * Updated instrument docstring
   * Corrected pysat.Instrument examples using COSMIC

[2.0.0] - 2019-07-11
--------------------
* New Features
   * `pysatData` directory created in user's home directory if no directory
     specified
   * Added preliminary support for `xarray` to the `instrument` object
   * Support for `today`, `tomorrow`, and `yesterday` as datetime objects
   * Added `model_utils`, featuring preliminary support for data-model
     comparison
   * Added support for 1d median in seasonal averages
   * Added routine to convert from kp to Ap
   * Added `pyglow` integration support for python 3.x
   * Added option to check that loaded data has a unique and monotonic time
     index. Will be enforced in a future version.
   * Refactored data access through the Instrument object and expanded testing.
   * Added .empty attribute to Instrument object, True when no data loaded.
   * Added .index access mechanism to Instrument object, providing consistent
     access to the pandas DatetimeIndex associated with loaded data.
   * Added mechanism to return a list of loaded variables, .variables.
   * Added Instrument method to concat input data with data already loaded into
     Instrument object.
   * Updated format of printed dates to day month name and year,
     01 January 2001.
   * Added Instrument property .date, returns date of loaded data.
   * Added download_updated_files, Instrument method that downloads any remote
     data not currently on the local machine.
   * Added remote_date_range, an Instrument method that returns first and last
     date for remote data.
   * Download method now defaults to most recent data (near now).
   * Improves input handling for datetime parameters that are more precise than
     just year, month, and day, where appropriate
   * Added merging routines to allow combination of measured and forecasted Kp
     and F10.7 indexes into a single instrument object
   * Files class internally refactored to improve robustness.
   * Added feature to handle delimited filenames, in addition to fixed_width
     names.
   * Exposed methods to allow users to more easily benefit from features in
     Files. Used to support remote_file_lists and make data downloads more
     convenient.
   * Expanded testing with Files.
   * Updated keyword names to be more complete. 'sec' to 'second', etc.
   * Updated Files access mechanisms to remove deprecated calls and improve
     robustness.
* Code restructure
   * Moved instrument templates and methods to subdirectories
   * Moved utils into multiple subdirectories to aid with organization
* Instrument Updates
   * NASA CDAWeb download now uses https protocol rather than FTP
   * `_instrument.py` supports xarray
   * Support for listing files from remote server
   * COSMIC RO data unified into single instrument object
   * Added support for DEMETER IAP
   * Added support for DMSP IVM Level 2 data.  Uses OpenMadrigal.
   * Added routines to update DMSP ephemeris and drifts
   * Added warnings to instruments without download support
   * Added preliminary support for ICON FUV and MIGHTI
   * Added support for Jicamarca Radio Observatory ISR
   * Added support for F10.7 and more Kp forecast products
   * Added instrument templates for Madrigal, CDAWeb, and netcdf_pandas
   * Added support for TIMED SABER
   * Added support for UCAR TIEGCM
   * OMNI HRO instrument now uses CDAWeb methods
   * Switched download methods for CDAWeb and COSMIC data to use `requests`
   * Added Madrigal methods
   * Removed support for SuperDARN and SuperMAG downloads while server changes
     are sorted out
* Updates to travis configuration
   * Tests run for python 2.7 and 3.7
   * Added display port to test plots
* Updates to community docs
   * Added Issue templates
   * Added Pull Request Template
   * Added note for PR to be made to develop, not master
* Style updates throughout
   * Consistent documentation for docstrings and instruments
   * Cleaned up commented code lines
   * PEP8 scrub
* Documentation
   * Added FAQ section
   * Added "powered by pysat" logo
   * Updated supported instruments
* Unit Test Updates
   * Dropped instrument templates from coverage
   * Added multiple output options for `pysat_testing` object to aid with
    constellation tests. Removed old constellation test objects.
   * Added test data for space weather indices to speed up testing
   * Cyclic data for test instruments now generated from single test method
   * Test objects for xarray added
   * Added test for parsed delimited files
   * Removed ftp downloads from travis tests, still will run locally
* Bug fixes
   * `pandas.ix` notation replaced with `pandas.loc` and `pandas.iloc`
     throughout
   * Fixed a bug that forced user into interactive mode in `ssnl.plot`
   * Bug fixes and cleanup in demo codes
   * Fix for orbit iteration when less than one orbit of data exists. Fix now
     covers multiple days with less than one orbit.
   * Fixed a bug in python 3.7 caused by change in behaviour of StopIteration
     (#207)
   * Update to use of `len` on xarray to handle new behaviour (#130)
   * Updated import of reload statements now that python 3.3 has reached end of
     life
   * Updated deprecated behaviour of `get_duplicates`, `.apply`, and `.to_csv`
    when using pandas
   * Fixed bug in assigning units to metadata (#162)
   * Fixed timing bug introduced by reading only the first date/data pair from
     each line in the 45-day file data blocks

[1.2.0] - 2018-09-24
--------------------
* SuperMAG support added
* Increased data access robustness when using integer indexing
* Added template for supporting netCDF4 based instruments (pysat_netCDF4)
* Added support for MSIS within the pysat satellite simulation (based on sgp4)
* Added plotting routine to sgp4
* Initial support for the upcoming NASA/INPE SPORT Ion Velocity Meter (IVM)
* Fixed bug triggerd when invoking multi_file_day option in Instrument object

[1.1.0] - 2018-07-05
--------------------
* Initial support for Constellation objects, which allows operations and
  analysis on mixed groups of Instrument objects. Developed by UT Dallas senior
  undergraduate computer science students (UTDesign 2018).
* Bug fixes when iterating by file
* Added pysat_sgp4, a Two Line Element based satellite orbit propagator that is
  coupled with ionosphere, thermosphere, and geomagnetic models. Supports
  projecting these quantities onto the relevant spacecraft frame to create
  signals suitable for satellite data simulation and testing. Routine uses
  pyglow, pysatMagVect, sgp4, and pyEphem.
* Further along the road toward windows compatibility
* Fixed orbit number reporting in orbits.current
* Added support for Defense Meteorological Satellite Program (DMSP) Ion Velocity
  Meter (IVM) data. Downloads from the Madrigal database.
* Added support for both sat_id and tag variations within filenames in the NASA
  CDAWeb template
* Updated docummentation covering requirements for adding new instruments to
  pysat

[1.0.1] - 2018-05-06
--------------------
* Improved robustness of Meta object when working with high and low order data
* Improved Meta test coverage
* Added dayside reconnection calculation for OMNI-HRO data
* Improved test behavior when instrument data could not be downloaded

[1.0.0] - 2018-04-29
--------------------
* Improved consistency when handling higher order metadata
* Improved translation of metadata within netCDF4 files to pysat standard
* Added pysatCDF as package requirement
* PEP8 upgrades throughout
* Updated load_netCDF4 routine to support ICON EUV files natively
* to_netCDF4 function updated to be consistent with load_netCDF4
* Meta object upgraded to handle more attributes by default
* Meta object has been upgraded to preserve case of variable and attribute names
* Metadata access is case insensitive for ease of use
* Changes to units_label or name_label are automatically applied to underlying
  metadata
* Improved handling of custom units and name labels at Instrument level
* Additional functions added to Meta object, attrs, keys, keys_nD, has_attr,
  routines that return preserved case
* Additional unit tests for Meta added
* Reduced resources required for unit tests
* Improved windows compatibility
* Added more unit tests for seasonal averages
* Added more simulated data types to pysat_testing2D
* Added initial support for ICON EUV
* Added initial support for ICON IVM
* Added support for version/revision numbers in filenames within Files class
  constructor from_os

[0.6.0] - 2017-08-11
--------------------
* Many changes since the last note here.
* Unit tests have been expanded significantly, bug fixes as appropriate.
* Coverage is over 80%
* There are new requirements on loading routines to support testing.
* Instrument object prints out nice information to command line
* Attributes in netCDF and similar files are transferred to the Instrument
  object as part of loading
* Added attribute 'empty', True if there is no data
* Orbit support significantly improved, multiple orbit types are supported
* Added concat to Meta
* Python 3 compatible
* Corrected intersection of data_padding and multi_file_day
* Added support for higher order MetaData objects, needed for DataFrame within
  DataFrames
* Windows compatibility
* Additional scientific instrument support
* Initial support for sat_id in Instrument
* Files class will now remove duplicate file times rather than simply raise an
  exception

[0.3.3] - 2016-01-07
--------------------
* Added manual_org flag to Instrument instantion. Simple file management flag.
* Improved COSMIC demo plotting
* Improved support for instruments with no files

[0.3.2] - 2015-12-01
--------------------
* Fixed error raised by pysat.utils.set_data_dir
* Partial unit test coverage for files class
* File tracking more robust
* Download methods now log off from server at the end of download
* Improved to_netcdf3 and load_netcdf3 routines, netcdf files produced pass
  standards check

[0.3.1] - 2015-07-21
--------------------
* Added missing file close statement in SuperDARN load command
* Fixed COSMIC UTS bug
* Fixed check for unique datetimes associated with files
* Improved instrument docstrings
* Added step size (freq) keyword to bounds and download methods
* Added C/NOFS IVM and COSMIC GPS demo
* Added support for OMNI data, 1 and 5 min files, time shifted to magnetopause
* Moving toward Python 3 compatibility
* PEP8 improvements
* Fixed demo ssnl_occurence_by_orbit file, replaced `binx` with `bin_x`
* Doubled loading performance for SuperDARN grdex files (3 seconds down to 1.5)

[0.3.0] - 2015-06-18
--------------------
* Improved polar orbit determination
* Added file sorting in files.from_os constructor to ensure datetime index is
  correct
* Added Instrument instantiation option, multi_file_day (good when data for
  day n is in a file labeled by day n-1, or n+1)
* Chaged binx to bin_x in return statements
* Improved PEP-8 compatibility
* Fixed bad path call in meta.from_csv
* Added simple averaging by day/file/orbit instrument independent routines
* Added instrument independent seasonal averaging routines
* Improved loading performance for cosmic2013
* Made pysat import statements more specific
* Fixed bad import call on load_netcdf3
* Fixed tab/space issues
* Improved performance of comsic 2013 data loading

[0.2.2] - 2015-05-17
--------------------
* Expanded coverage in tutorial documentation
* Expanded test coverage for pysat.Meta()
* Improved robustness of Meta __setitem__
* Updated C/NOFS VEFI method to exempt empty file errors
* Updated C/NOFS VEFI download method to remove empty files
* Updated C/NOFS VEFI instrument module to use metadata from CDF file
* Updated superdarn cleaning method to remove empty velocity frames
* Updated Instrument download method to update bounds if bounds are default
* Updated C/NOFS IVM download method to remove empty files
* Updated C/NOFS IVM instrument module to use metadata from CDF file
* Performance improvements to seasonal occurrence probability
* Improved docstrings

[0.2.1] - 2015-04-29
--------------------
* Removed spacepy and netCDF from setup.py requirements. Both of
  these packages require non-python code to function properly.
  pysat now builds correctly as determined by travis-cl.
  Installation instructions have been updated.

[0.2.0] - 2015-04-27
--------------------
* Added information to docstrings.
* Expanded unit test coverage and associated bugs.
* Changed signature for pysat.Instrument, orbit information
  condensed into a single dictionary. pad changed from a boolean
  to accepting a pandas.DateOffest or dictionary.
* Changed doy parameter in create_datetime_index to day.
* Changed Instrument.query_files to update_files
* Improved performance of cnofs_ivm code
