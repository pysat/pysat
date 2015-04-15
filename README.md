#What is it
pysat is a Python package providing a simple, flexible, and powerful interface
for downloading, loading, cleaning, managing, processing, and analyzing scientific 
measurements. Though pysat was initially designed for in-situ
satellite based measurements it aims to support all instruments in space science.

#Main Features
* Single interface for a wide variety of science data sets.
* Single interface to download data for all supported instruments.
* Data model (modified pandas) that supports a combination of 1D, 2D, 3D, and nD data in a single structure
* Instrument independent analysis routines.
* Science data pipeline tasks of identifying files, loading, and cleaning
data sets are built into the instrument object. 
* Supports the automatic application of arbitray custom functions 
 upon each load. This nano-kernel funcitonality ensures that any routine that
 interacts with the instrument object receives properly processed data.
* Supports metadata consistent with the netCDF CF-1.6 standard. Each variable 
has a name, long name, and units. Note units are informational only.
* Simplifies data management
  * Iterates by day/file using the for loop, manual next/prev methods, or any iterative
  method.
  * Iterate through a data set orbit-by-orbit; orbits are calculated on the fly
from loaded data and span day/month/year breaks.
  * Iterate over custom seasons
* Supports rigorous time-series calculations. Frequently these methods need
time to spin up and down to produce accurate analysis. The instrument object
appends real data for a buffer on each end of desired data, applies the custom 
functions, then removes buffer data before presenting output. The time
series code does not need to do anything to support this behavior. 
* Uses pandas for the underlying underlying data structure;
capable of handling the many forms scientific measurements take in a consistent
manner.
  * pandas has been forked to accomodate the assignment of pandas Series/
  Dateframes as single elements of a Series/Dataframe.
* Includes helper functions to reduce the barrier to adding new science instruments to pysat


#Installation
* Clone repositories for both pysat and the forked pandas.
* Follow normal instructions for installing pandas on forked pandas.
* For pysat, ensure pythonpath includes pysat.
* Run pysat.utils.set_data_dir('path to top level data dir')
* Nominal organization of data is top_dir/platform/name/tag/*/files

#Quick Demo
The core functionality is exposed through the Instrument object, providing a single
location to obtain instrument data and properties. See pysat/demo for more.
```
import pysat
ivm = pysat.Instrument(platform='cnofs', name='ivm', tag='', clean_level='clean')
# 1-second thermal plasma parameters
ivm.load(2009,1)

vefi = pysat.Instrument('cnofs','vefi','dc_b', 'clean')
# 1-second mag field data
vefi.load(date=pds.datetime(2009,1,1))

cosmic = pysat.Istrument('cosmic', 'gps', 'ionprf')
# gps occultation, vertical electron density profiles
cosmic.load(fname='filename')
or
cosmic.load(2009,1)
```
pysat calls functions written specifically for the given instrument, in this
case the Ion Velocity Meter onboard C/NOFS, part of the Coupled Ion
Neutral Dynamics Investigation (CINDI), to enable loading and cleaning.

##Data Access
* ivm['name'] or ivm.data['name'] or ivm.data.ix['name']
* ivm[row,'name'], ivm[row1:row2,'name'], ivm[[1,2,3], 'name']
* ivm[datetime,'name'], ivm[datetime1:datetime2,'name']
* complete pandas data object exposed in ivm.data

##Data Assignment
```
ivm['new_data'] = new_data
```
#####Assignment with metadata
```
ivm['double_mlt'] = {'data':2.*inst['mlt'], 'name':'double_mlt', 
            'long_name':'Double MLT', 'units':'hours'}
```
##Custom Functions
Science analysis is built upon custom data processing, thus custom functions 
may be attached to the Instrument object. Each function is 
run automatically when new data is loaded.

#####Modify Functions
The instrument object is passed to function without copying, modify in place
```
def custom_func_modify(inst, optional_param=False):
    inst['double_mlt'] = 2.*inst['mlt']
```    
#####Add Functions
A copy of the instrument is passed to function, data to be added is returned
```
def custom_func_add(inst, optional_param=False):
    return 2*.inst['mlt']
```
#####Add Function Including Metadata
```
def custom_func_add(inst, optional_param1=False, optional_param2=False):
    return {'data':2.*inst['mlt'], 'name':'double_mlt', 
            'long_name':'doubledouble', 'units':'hours'}
```
#####Attaching Custom Function
```
ivm.custom.add(custom_func_modify, 'modify', optional_param2=True)
ivm.load(2009,1)
print ivm['double_mlt']
```
```
ivm.custom.add(custom_func_add, 'add', optional_param2=True)
ivm.bounds = (start,stop)
custom_complicated_analysis_over_season(ivm)
```
The output of custom_func_modify will always be available from instrument object, regardless
of what level the science analysis is performed.

##Iterate over Dataset
#####Iterate by day
Each loop loads a new day of instrument data, with custom processing
```
for ivm in ivm:
    print 'new day of double mlt ivm data ', ivm['double_mlt']
```   
#####Iterate over custom season
```
import pandas as pd
start = [pd.datetime(2009,1,1), pd.datetime(2010,1,1)]
stop = [pd.datetime(2009,4,1), pd.datetime(2010,4,1)]
ivm.bounds = (start, stop)
for ivm in ivm:
    print 'A new day of data in custom season, ', ivm.date.strftime('%y/%m/%d')
    print 'Year, doy ', ivm.yr, ivm.doy
```
#####Iterate by orbit over custom season:
```
ivm = pysat.Instrument(name='cindi_ivm', tag='rs', clean_level='clean',
                        orbit_index='mlt', orbit_type='local time')
start = [pd.datetime(2009,1,1), pd.datetime(2010,1,1)]
stop = [pd.datetime(2009,4,1), pd.datetime(2010,4,1)]
ivm.bounds = (start, stop)
for ivm in ivm.orbits:
    print 'next available orbit ', ivm.data
```
#Data Model
The base object is the pandas DataFrame, "similar" to an excel spreadsheet
with labeled rows and columns. Nominally rows are indexed by time, while
columns span the different data types. This accomodates 1D data quite well.
For higher order data sets, a pandas series or pandas DataFrame may also be stored
within each cell of a column, with 1D or other dimensional data in other columns.
This set up allows for all data types to be stored in a single data object.

A powerfule feature of pandas is auto-alignment of data based upon the index.
Thus, the profiles or images stored as above do not need to have the same sizes.
Math operations across series and dataframes are aligned and missing data is treated as dictated.

#Adding a new instrument to pysat
pysat works by calling modules written for specific instruments
that load and process the data consistent with the pysat standard. The name
of the module corresponds to the name field when initializing a pysat
instrument object. The module should be placed in the pysat instruments
directory or in the user specified location (via mechanism to be added) 
for automatic discovery. A compatible module may also be supplied directly
to pysat.Instrument(inst_module=input module).

Three functions are required:
* list_files routine that returns a pandas Series
with filenames ordered in time. 
  * The
  nominal location of data is pysat_data_dir/platform/name/tag, provided in data_path, where pysat_data_dir
  is specified by user in pysat settings.
```
def list_files(tag=None, data_path=None):
    return pysat.Files object
```
  * pysat.Files.from_os is a convenience constructor provided for filenames that include time information in the filename and utilize a constant field width. The location and format of the time information is specified using standard python formatting and keywords year, month, day, hour, minute, second. 
```
def list_files(tag=None, data_path=None):
    return pysat.Files.from_os(data_path=data_path, 
                    format_str='rs{year:4d}{day:03d}-ivm.hdf')
```                                

* load routine that returns a tuple with (data, pysat metadata object)
```
def load(fnames, tag=None):
    return data, meta
```
* download routine to fetch data from the internet
```
def download(date_array, data_path=None, user=None, password=None):
    return
```
* pysat meta object obtained from pysat.Meta(). Use pandas DataFrame indexed
by name with columns for units and long_name. Additional arbitrary columns allowed.
Convenience function from_csv provided.
* init routine, initialize any specific instrument info. Runs once. (optional)
```
def init(inst):
    return None
```
* default routine, runs once per instrument load. inst is pysat instrument object. (optional)
```
def default(inst):
    return None
```
* clean routine, cleans instrument for levels supplied in inst.clean_level. (optional)
  * 'clean' : expectation of good data
  * 'dusty' : probably good data, use with caution
  * 'dirty' : minimal cleaning, only blatant instrument errors removed
  * 'none'  : no cleaning, routine not called
```
def clean(inst):
    return None
```


