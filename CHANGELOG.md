# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Pending][]

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

