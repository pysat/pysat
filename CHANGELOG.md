# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [2.0.0] - 2019-07-??
 - New Features
   - `pysatData` directory created in user's home directory if no directory specified
   - Added preliminary support for `xarray` to the `instrument` object
   - Support for `today`, `tomorrow`, and `yesterday` as datetime objects
   - Added `model_utils`, featuring preliminary support for data-model comparison
   - Added support for 1d median in seasonal averages
   - Added routine to convert from kp to Ap
   - Added `pyglow` integration support for python 3.x
   - Added option to check that loaded data has a unique and monotonic time index. Will be enforced in a future version.
   - Refactored data access through the Instrument object and expanded testing.
   - Added .empty attribute to Instrument object, True when no data loaded.
   - Added .index access mechanism to Instrument object, providing consistent access to the pandas DatetimeIndex associated with loaded data.
   - Added mechanism to return a list of loaded variables, .variables.
   - Added Instrument method to concat input data with data already loaded into Instrument object.
   - Updated format of printed dates to day month name and year, 01 January 2001.
   - Added Instrument property .date, returns date of loaded data.
   - Added download_updated_files, Instrument method that downloads any remote data not currently on the local machine.
   - Added remote_date_range, an Instrument method that returns first and last date for remote data.
   - Download method now defaults to most recent data (near now).
   - Improves input handling for datetime parameters that are more precise than just year, month, and day, where appropriate
   - Added merging routines to allow combination of measured and forecasted Kp and F10.7 indexes into a single instrument object
   - Files class internally refactored to improve robustness.
   - Added feature to handle delimited filenames, in addition to fixed_width names.
   - Exposed methods to allow users to more easily benefit from features in Files. Used to support remote_file_lists and make data downloads more convenient.
   - Expanded testing with Files.
   - Updated keyword names to be more complete. 'sec' to 'second', etc.
   - Updated Files access mechanisms to remove deprecated calls and improve robustness.
 - Code restructure
   - Moved instrument templates and methods to subdirectories
   - Moved utils into multiple subdirectories to aid with organization
 - Instrument Updates
   - NASA CDAWeb download now uses https protocol rather than FTP
   - `_instrument.py` supports xarray
   - Support for listing files from remote server
   - COSMIC RO data unified into single instrument object
   - Added support for DEMETER IAP
   - Added support for DMSP IVM Level 2 data.  Uses OpenMadrigal.
   - Added routines to update DMSP ephemeris and drifts
   - Added warnings to instruments without download support
   - Added preliminary support for ICON FUV and MIGHTI
   - Added support for Jicamarca Radio Observatory ISR
   - Added support for F10.7 and more Kp forecast products
   - Added instrument templates for Madrigal, CDAWeb, and netcdf_pandas
   - Added support for TIMED SABER
   - Added support for UCAR TIEGCM
   - OMNI HRO instrument now uses CDAWeb methods
   - Switched download methods for CDAWeb and COSMIC data to use `requests`
   - Added Madrigal methods
   - Removed support for SuperDARN and SuperMAG downloads while server changes are sorted out
 - Updates to travis configuration
   - Tests run for python 2.7 and 3.7
   - Added display port to test plots
 - Updates to community docs
   - Added Issue templates
   - Added Pull Request Template
   - Added note for PR to be made to develop, not master
 - Style updates throughout
   - Consistent documentation for docstrings and instruments
   - Cleaned up commented code lines
   - PEP8 scrub
 - Documentation
   - Added FAQ section
   - Added "powered by pysat" logo
   - Updated supported instruments
 - Unit Test Updates
   - Dropped instrument templates from coverage
   - Added multiple output options for `pysat_testing` object to aid with constellation tests. Removed old constellation test objects.
   - Added test data for space weather indices to speed up testing
   - Cyclic data for test instruments now generated from single test method
   - test objects for xarray added
   - Added test for parsed delimited files
   - Removed ftp downloads from travis tests, still will run locally
 - Bug fixes
   - `pandas.ix` notation replaced with `pandas.loc` and `pandas.iloc` throughout
   - Fixed a bug that forced user into interactive mode in `ssnl.plot`
   - Bug fixes and cleanup in demo codes
   - Fix for orbit iteration when less than one orbit of data exists. Fix now covers multiple days with less than one orbit.
   - Fixed a bug in python 3.7 caused by change in behaviour of StopIteration (#207)
   - Update to use of `len` on xarray to handle new behaviour (#130)
   - Updated import of reload statements now that python 3.3 has reached end of life
   - Updated deprecated behaviour of `get_duplicates`, `.apply`, and `.to_csv` when using pandas
   - Fixed bug in assigning units to metadata (#162)
   - Fixed timing bug introduced by reading only the first date/data pair from each line in the 45-day file data blocks


## [1.2.0] - 2018-09-24
 - SuperMAG support added
 - Increased data access robustness when using integer indexing
 - Added template for supporting netCDF4 based instruments (pysat_netCDF4)
 - Added support for MSIS within the pysat satellite simulation (based on sgp4)
 - Added plotting routine to sgp4
 - Initial support for the upcoming NASA/INPE SPORT Ion Velocity Meter (IVM)
 - Fixed bug triggerd when invoking multi_file_day option in Instrument object

## [1.1.0] - 2018-07-05
 - Initial support for Constellation objects, which allows operations and analysis on mixed groups of Instrument objects. Developed by UT Dallas senior undergraduate computer science students (UTDesign 2018).
 - Bug fixes when iterating by file
 - Added pysat_sgp4, a Two Line Element based satellite orbit propagator that is coupled with ionosphere, thermosphere, and geomagnetic models. Supports projecting these quantities onto the relevant spacecraft frame to create signals suitable for satellite data simulation and testing. Routine uses pyglow, pysatMagVect, sgp4, and pyEphem.
 - Further along the road toward windows compatibility
 - Fixed orbit number reporting in orbits.current
 - Added support for Defense Meteorological Satellite Program (DMSP) Ion Velocity Meter (IVM) data. Downloads from the Madrigal database (https://openmadrigal.org)
 - Added support for both sat_id and tag variations within filenames in the NASA CDAWeb template
 - Updated docummentation covering requirements for adding new instruments to pysat

## [1.0.1] - 2018-05-06
 - Improved robustness of Meta object when working with high and low order data
 - Improved Meta test coverage
 - Added dayside reconnection calculation for OMNI-HRO data
 - Improved test behavior when instrument data could not be downloaded

## [1.0.0] - 2018-04-29
 - Improved consistency when handling higher order metadata
 - Improved translation of metadata within netCDF4 files to pysat standard
 - Added pysatCDF as package requirement
 - PEP8 upgrades throughout
 - Updated load_netCDF4 routine to support ICON EUV files natively
 - to_netCDF4 function updated to be consistent with load_netCDF4
 - Meta object upgraded to handle more attributes by default
 - Meta object has been upgraded to preserve case of variable and attribute names
 - Metadata access is case insensitive for ease of use
 - Changes to units_label or name_label are automatically applied to underlying metadata
 - Improved handling of custom units and name labels at Instrument level
 - Additional functions added to Meta object, attrs, keys, keys_nD, has_attr, routines that return preserved case
 - Additional unit tests for Meta added
 - Reduced resources required for unit tests
 - Improved windows compatibility
 - Added more unit tests for seasonal averages
 - Added more simulated data types to pysat_testing2D
 - Added initial support for ICON EUV
 - Added initial support for ICON IVM
 - Added support for version/revision numbers in filenames within Files class constructor from_os


## [0.6.0] - 2017-08-11
 - Many changes since the last note here.
 - Unit tests have been expanded significantly, bug fixes as appropriate.
 - Coverage is over 80%
 - There are new requirements on loading routines to support testing.
 - Instrument object prints out nice information to command line
 - Attributes in netCDF and similar files are transferred to the Instrument object as part of loading
 - Added attribute 'empty', True if there is no data
 - Orbit support significantly improved, multiple orbit types are supported
 - Added concat to Meta
 - Python 3 compatible
 - Corrected intersection of data_padding and multi_file_day
 - Added support for higher order MetaData objects, needed for DataFrame within DataFrames
 - Windows compatibility
 - Additional scientific instrument support


### Changed
 - Initial support for sat_id in Instrument
 - Files class will now remove duplicate file times rather than simply raise an exception

## [0.3.3] - 2016-01-07
### Changed
 - Added manual_org flag to Instrument instantion. Simple file management flag.
 - Improved COSMIC demo plotting
 - Improved support for instruments with no files

## [0.3.2] - 2015-12-01
### Changed
 - Fixed error raised by pysat.utils.set_data_dir
 - Partial unit test coverage for files class
 - File tracking more robust
 - Download methods now log off from server at the end of download
 - Improved to_netcdf3 and load_netcdf3 routines, netcdf files produced pass standards check

## [0.3.1] - 2015-07-21
### Changed
 - Added missing file close statement in SuperDARN load command
 - Fixed COSMIC UTS bug
 - Fixed check for unique datetimes associated with files
 - Improved instrument docstrings
 - Added step size (freq) keyword to bounds and download methods
 - Added C/NOFS IVM and COSMIC GPS demo
 - Added support for OMNI data, 1 and 5 min files, time shifted to magnetopause
 - Moving toward python 3 compatibility
 - PEP 8 improvements
 - fixed demo ssnl_occurence_by_orbit file, replaced binx with bin_x
 - Doubled loading performance for SuperDARN grdex files (3 seconds down to 1.5)

## [0.3] - 2015-06-18
### Changed
 - Improved polar orbit determination
 - Added file sorting in files.from_os constructor to ensure datetime index is correct
 - Added Instrument instantiation option, multi_file_day
  - good when data for day n is in a file labeled by day n-1, or n+1
 - Chaged binx to bin_x in return statements
 - Improved PEP-8 compatibility
 - Fixed bad path call in meta.from_csv
 - Added simple averaging by day/file/orbit instrument independent routines
 - Added instrument independent seasonal averaging routines
 - Improved loading performance for cosmic2013
 - made pysat import statements more specific
 - fixed bad import call on load_netcdf3
 - fixed tab/space issues
 - Improved performance of comsic 2013 data loading

## [0.2.2] - 2015-05-17
### Changed
 - Expanded coverage in tutorial documentation
 - Expanded test coverage for pysat.Meta()
 - Improved robustness of Meta __setitem__
 - Updated C/NOFS VEFI method to exempt empty file errors
 - Updated C/NOFS VEFI download method to remove empty files
 - Updated C/NOFS VEFI instrument module to use metadata from CDF file
 - Updated superdarn cleaning method to remove empty velocity frames
 - Updated Instrument download method to update bounds if bounds are default
 - Updated C/NOFS IVM download method to remove empty files
 - Updated C/NOFS IVM instrument module to use metadata from CDF file
 - Performance improvements to seasonal occurrence probability
 - Improved docstrings

## [0.2.1] - 2015-04-29
### Changed
- Removed spacepy and netCDF from setup.py requirements. Both of
  these packages require non-python code to function properly.
  pysat now builds correctly as determined by travis-cl.
  Installation instructions have been updated.

## [0.2.0] - 2015-04-27
### Changed
- Added information to docstrings.
- Expanded unit test coverage and associated bugs.
- Changed signature for pysat.Instrument, orbit information
  condensed into a single dictionary. pad changed from a boolean
  to accepting a pandas.DateOffest or dictionary.
- Changed doy parameter in create_datetime_index to day.
- Changed Instrument.query_files to update_files
- Improved performance of cnofs_ivm code
