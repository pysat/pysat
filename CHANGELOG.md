# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased][unreleased]
### Changed

## [0.2.1] - 2015-04-29
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

