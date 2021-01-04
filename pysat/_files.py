import datetime as dt
import inspect
import numpy as np
import os
import warnings

import pandas as pds
from pysat import pysat_dir, logger, params, Instrument
from pysat.utils import files as futils
from pysat.utils.time import filter_datetime_input


class Files(object):
    """Maintains collection of files plus associated methods.

    Interfaces with the `list_files` method for a given instrument
    support module to create an ordered collection of files in time,
    used primarily by the pysat.Instrument object to identify files
    to be loaded. The Files class mediates access to the files by
    datetime and contains helper methods for determining the presence of
    new files and filtering out empty files.

    Parameters
    -----------
    sat : pysat.Instrument
        Instrument object
    manual_org : boolean
        If True, then pysat will look directly in pysat data directory
        for data files and will not use default /platform/name/tag/inst_id
        (default=False)
    directory_format : string or NoneType
        directory naming structure in string format. Variables such as
        platform, name, and tag will be filled in as needed using python
        string formatting. The default directory structure would be
        expressed as '{platform}/{name}/{tag}/{inst_id}' where
        '/' is platform appropriate. (default=None)
    update_files : boolean
        If True, immediately query filesystem for instrument files and
        store (default=False)
    file_format : str or NoneType
        File naming structure in string format.  Variables such as year,
        month, and inst_id will be filled in as needed using python string
        formatting.  The default file format structure is supplied in the
        instrument list_files routine. (default=None)
    write_to_disk : boolean
        If true, the list of Instrument files will be written to disk.
        Setting this to False prevents a rare condition when running
        multiple pysat processes.
    ignore_empty_files : boolean
        if True, the list of files found will be checked to
        ensure the filesizes are greater than zero. Empty files are
        removed from the stored list of files.

    Attributes
    ----------
    start_date : datetime
        date of first file, used as default start bound for instrument
        object
    stop_date : datetime
        date of last file, used as default stop bound for instrument
        object
    data_path : string
        path to the directory containing instrument files,
        top_dir/platform/name/tag/
    data_paths: list of str
        Available paths that pysat will use when looking for files. The
        class uses the first directory with relevant data, stored in data_path.
    files : pandas.Series
        Filenames indexed by time. Leading pysat path information not stored.
    home_path : str
        Directory used for class storage
    list_files_generator : generator
        Experimental feature for Instruments that internally generate data
        and thus don't have a defined supported date range.
    list_files_rtn : method
        Method used to locate relevant files on the local system. Provided
        by associated pysat.Instrument object.
    multi_file_day : boolean
        Flag copied from associated pysat.Instrument object that indicates
        when data for day n may be found in files for days n-1, or n+1
    sat_info : dict
        Contains pysat.Instrument parameters 'platform', 'name', 'tag',
        and 'inst_id', identifying the source of the files.
    stored_file_name : str
        File used by this class to store file information

    Note
    ----
    User should generally use the interface provided by a pysat.Instrument
    instance. Exceptions are the classmethod from_os, provided to assist
    in generating the appropriate output for an instrument routine.

    Examples
    --------
    ::

        # convenient file access
        inst = pysat.Instrument(platform=platform, name=name, tag=tag,
                                inst_id=inst_id)
        # first file
        inst.files[0]

        # files from start up to stop (exclusive on stop)
        start = dt.datetime(2009,1,1)
        stop = dt.datetime(2009,1,3)
        print(vefi.files[start:stop])

        # files for date
        print(vefi.files[start])

        # files by slicing
        print(vefi.files[0:4])

        # get a list of new files
        # new files are those that weren't present the last time
        # a given instrument's file list was stored
        new_files = vefi.files.get_new()

        # search pysat appropriate directory for instrument files and
        # update Files instance.
        vefi.files.refresh()

    """

    def __init__(self, sat, manual_org=False, directory_format=None,
                 update_files=False, file_format=None, write_to_disk=True,
                 ignore_empty_files=False):

        # Update file list an instantiation flag
        self.update_files = update_files

        # Location of directory to store file information in
        self.home_path = os.path.join(pysat_dir, 'instruments')

        # Assign base default dates and an empty list of files
        self.start_date = None
        self.stop_date = None
        self.files = pds.Series(None, dtype='object')

        # Grab Instrument info
        self.sat_info = {'platform': sat.platform, 'name': sat.name,
                         'tag': sat.tag, 'inst_id': sat.inst_id}
        self.list_files_rtn = sat._list_files_rtn

        # Check if routine is actually a generator method
        if inspect.isgeneratorfunction(self.list_files_rtn):
            self.list_files_generator = self.list_files_rtn()
            # Instrument iteration methods require a date range
            # So, do we just pick dates far into future and past?
            self.start_date = dt.datetime(1900, 1, 1)
            self.stop_date = dt.datetime(2100, 1, 1)
        else:
            self.list_files_generator = None

        self.multi_file_day = sat.multi_file_day

        # Filename that stores list of Instrument files
        self.stored_file_name = '_'.join((self.sat_info['platform'],
                                          self.sat_info['name'],
                                          self.sat_info['tag'],
                                          self.sat_info['inst_id'],
                                          'stored_file_info.txt'))

        # flag for setting simple organization of files, only
        # look under pysat_data_dir
        self.manual_org = manual_org

        # Get template for sub-directories under main pysat data directories
        if directory_format is None:
            # Assign stored template if user doesn't provide one
            # TODO: Should we just error here? This ensures the settings are
            # dominated by the Instrument object.
            directory_format = params['directory_format']
        self.directory_format = directory_format

        # User-specified file format
        self.file_format = file_format

        if manual_org:
            self.sub_dir_path = ''
        else:
            # construct subdirectory path
            self.sub_dir_path = \
                self.directory_format.format(**self.sat_info)
            self.sub_dir_path = os.path.normpath(self.sub_dir_path)

        # Ensure we have at least one path for pysat data directory
        if len(params['data_dirs']) == 0:
            raise RuntimeError(" ".join(("pysat's data_dirs has not been set. ",
                                         "Please set a top-level directory ",
                                         "path to store data using ",
                                         "`pysat.params['data_dirs'] = path`")))

        # Get list of potential data directory paths from pysat. Construct
        # possible locations for data. Ensure path always ends with directory
        # separator.
        self.data_paths = [os.path.join(pdir, self.sub_dir_path)
                           for pdir in params['data_dirs']]
        self.data_paths = [os.path.join(os.path.normpath(pdir), '')
                           for pdir in self.data_paths]

        # Only one of the above paths will actually be used when loading data.
        # The actual value of data_path is determined in refresh().
        # If there are files present, then that path is stored along with a
        # list of found files in ~/.pysat. This stored info is retrieved by
        # _load. We start here with the first directory for cases where there
        # are no files.
        self.data_path = self.data_paths[0]

        # Store write to disk preference
        self.write_to_disk = write_to_disk
        if not self.write_to_disk:
            # Using blank memory rather than loading from disk
            self._previous_file_list = pds.Series([], dtype='a')
            self._current_file_list = pds.Series([], dtype='a')

        # Store ignore_empty_files preference
        self.ignore_empty_files = ignore_empty_files

        if self.sat_info['platform'] != '':
            if self.list_files_generator is None:
                # Typical instrument with files, not generated data.
                if self.update_files:
                    self.refresh()
                else:
                    # Load stored file info
                    info = self._load()
                    if info.empty:
                        # Didn't find stored information. Search local system.
                        self.refresh()
                    else:
                        # Attach the data loaded
                        self._attach_files(info)

    # slicing via date and index filename is inclusive slicing,
    # date and index are normal non-inclusive end point

    def __getitem__(self, key):
        if self.list_files_generator is not None:
            # Return generated filename
            return self.list_files_generator(key)

        if isinstance(key, slice):
            try:
                try:
                    # Assume key is integer (including list or slice)
                    out = self.files.iloc[key]
                except TypeError:
                    # Assume key is something else
                    out = self.files.loc[key]
            except IndexError as err:
                raise IndexError(''.join((str(err), '\n',
                                          'Date requested outside file ',
                                          'bounds.')))
            if isinstance(key.start, dt.datetime):
                # enforce exclusive slicing on datetime
                if len(out) > 1:
                    if out.index[-1] >= key.stop:
                        return out[:-1]
                    else:
                        return out
                elif len(out) == 1:
                    if out.index[0] >= key.stop:
                        return pds.Series([], dtype='a')
                    else:
                        return out
                else:
                    return out
            else:
                # not a datetime
                return out
        else:
            try:
                return self.files.iloc[key]
            except TypeError:
                return self.files.loc[key]

    def __repr__(self):
        inst_repr = Instrument(**self.sat_info).__repr__()

        out_str = "".join(["Files(", inst_repr, ", manual_org=",
                           "{:}, directory_format='".format(self.manual_org),
                           self.directory_format, "', update_files=",
                           "{:}, file_format=".format(self.update_files),
                           "{:}, ".format(self.file_format.__repr__()),
                           "write_to_disk={:}, ".format(self.write_to_disk),
                           "ignore_empty_files=",
                           "{:})".format(self.ignore_empty_files),
                           " -> {:d} Local files".format(len(self.files))])

        return out_str

    def __str__(self):
        num_files = len(self.files)
        output_str = 'Local File Statistics\n'
        output_str += '---------------------\n'
        output_str += 'Number of files: {:d}\n'.format(num_files)

        if num_files > 0:
            output_str += 'Date Range: '
            output_str += self.files.index[0].strftime('%d %B %Y')
            output_str += ' --- '
            output_str += self.files.index[-1].strftime('%d %B %Y')

        return output_str

    def _attach_files(self, files_info):
        """Attaches stored file lists to self.files

        Parameters
        ----------
        files_info : pandas.Series
            Filenames indexed by datetime

        """

        if not files_info.empty:

            # Attach data
            self.files = files_info

            # Ensure times are unique.
            self._ensure_unique_file_datetimes()

            # Filter for empty files.
            if self.ignore_empty_files:
                self._filter_empty_files(path=self.data_path)

            # Extract date information from first and last files
            if not self.files.empty:
                self.start_date = filter_datetime_input(self.files.index[0])
                self.stop_date = filter_datetime_input(self.files.index[-1])
            else:
                # No files found
                self.start_date = None
                self.stop_date = None
        else:
            # No files found
            self.start_date = None
            self.stop_date = None
            # Convert to object type. Necessary when Series is empty,
            # enables == checks with strings
            self.files = files_info.astype(np.dtype('O'))

    def _ensure_unique_file_datetimes(self):
        """Update the file list (self.files) to ensure uniqueness"""

        # Check if files are unique.
        unique_files = len(self.files.index.unique()) == len(self.files)

        if not self.multi_file_day and not unique_files:
            # Give user feedback about the issue
            estr = 'Duplicate datetimes in stored filename '
            estr = '{:s}information.\nKeeping one of each '.format(estr)
            estr = '{:s}of the duplicates, dropping the rest. '.format(estr)
            estr = '{:s}Please ensure the file datetimes '.format(estr)
            estr = '{:s}are unique at the microsecond level.'.format(estr)
            logger.warning(estr)
            ind = self.files.index.duplicated()
            logger.warning(self.files.index[ind].unique())

            # Downselect to unique file datetimes
            idx = np.unique(self.files.index, return_index=True)
            self.files = self.files.iloc[idx[1]]

        return

    def _filter_empty_files(self, path):
        """Update the file list (self.files) with empty files removed

        Parameters
        ----------
        path : str
            Path to top-level containing files
        """

        keep_index = []
        for i, fi in enumerate(self.files):
            # Create full path for each file
            fi_path = os.path.join(path, fi)
            # Ensure it exists
            if os.path.exists(fi_path) and (os.path.getsize(fi_path) > 0):
                # Store if not empty
                keep_index.append(i)

        # Remove filenames for empty files as needed
        dropped_num = len(self.files.index) - len(keep_index)
        if dropped_num > 0:
            logger.info(' '.join(('Removing', str(dropped_num),
                                  'empty files from Instrument list.')))
            self.files = self.files.iloc[keep_index]

        return

    def _load(self, prev_version=False, update_path=True):
        """Load stored filelist

        Parameters
        ----------
        prev_version : boolean
            if True, will load previous version of file list
        update_path : boolean
            If True, the path written to stored info will be
            assigned to self.data_path. (default=True)

        Returns
        -------
        pandas.Series
            file path names, indexed by datetime. Series is empty if no
            files are found.

        """

        fname = self.stored_file_name
        if prev_version:
            # Archived file list storage filename
            fname = os.path.join(self.home_path, 'archive', fname)
        else:
            # Current file list storage filename
            fname = os.path.join(self.home_path, fname)

        if os.path.isfile(fname) and (os.path.getsize(fname) > 0):
            if self.write_to_disk:
                # Load data stored on the local drive.
                loaded = pds.read_csv(fname, index_col=0, parse_dates=True,
                                      squeeze=True, header=0)
                if update_path:
                    # Store the data_path from the .csv onto Files
                    self.data_path = loaded.name

                # Ensure the name of returned Series is None for consistency
                loaded.name = None

                return loaded
            else:
                # Grab content from memory rather than local disk.
                if prev_version:
                    return self._previous_file_list
                else:
                    return self._current_file_list
        else:
            # Storage file not present.
            return pds.Series([], dtype='a')

    def _remove_data_dir_path(self, inp=None, path=None):
        """Remove the data directory path from filenames"""
        if path is None:
            estr = 'A path is required.'
            raise ValueError(estr)

        if inp is not None:
            split_str = os.path.join(path, '')
            return inp.apply(lambda x: x.split(split_str)[-1])

    def _store(self):
        """Store self.files onto filesystem"""

        name = self.stored_file_name
        # check if current file data is different than stored file list
        # if so, move file list to previous file list, store current to file
        # if not, do nothing
        stored_files = self._load(update_path=False)
        if len(stored_files) != len(self.files):
            # The number of items is different, things are new
            new_flag = True
        elif len(stored_files) == len(self.files):
            # The number of items is the same, check specifically for equality
            if stored_files.eq(self.files).all():
                new_flag = False
            else:
                # Stored and new data are not equal, there are new files
                new_flag = True

        if new_flag:
            if self.write_to_disk:
                stored_files.to_csv(os.path.join(self.home_path,
                                                 'archive', name),
                                    date_format='%Y-%m-%d %H:%M:%S.%f',
                                    header=[self.data_path])
                self.files.to_csv(os.path.join(self.home_path, name),
                                  date_format='%Y-%m-%d %H:%M:%S.%f',
                                  header=[self.data_path])
            else:
                self._previous_file_list = stored_files
                self._current_file_list = self.files.copy()
        return

    def get_file_array(self, start, stop):
        """Return a list of filenames between and including start and stop.

        Parameters
        ----------
        start: array_like or single string
            filenames for start of returned filelist
        stop: array_like or single string
            filenames inclusive of the ending of list provided by the stop
            time

        Returns
        -------
            list of filenames between and including start and stop times over
            all intervals.

        """
        if hasattr(start, '__iter__') and hasattr(stop, '__iter__'):
            files = []
            for (sta, stp) in zip(start, stop):
                id1 = self.get_index(sta)
                id2 = self.get_index(stp)
                files.extend(self.files.iloc[id1:(id2 + 1)])
        elif hasattr(start, '__iter__') or hasattr(stop, '__iter__'):
            estr = 'Either both or none of the inputs need to be iterable'
            raise ValueError(estr)
        else:
            id1 = self.get_index(start)
            id2 = self.get_index(stop)
            files = self.files[id1:(id2 + 1)].to_list()
        return files

    def get_index(self, fname):
        """Return index for a given filename.

        Parameters
        ----------
        fname : string
            filename

        Note
        ----
        If fname not found in the file information already attached
        to the instrument.files instance, then a files.refresh() call
        is made.

        """

        idx, = np.where(fname == self.files)
        if len(idx) == 0:
            # filename not in index, try reloading files from disk
            self.refresh()
            idx, = np.where(fname == np.array(self.files))

            if len(idx) == 0:
                raise ValueError(' '.join(('Could not find "{:}"'.format(fname),
                                           'in available file list. Valid',
                                           'Example:', self.files.iloc[0])))
        # return a scalar rather than array - otherwise introduces array to
        # index warnings.
        return idx[0]

    def get_new(self):
        """List new files since last recorded file state.

        pysat stores filenames in the user_home/.pysat directory. Returns
        a list of all new fileanmes since the last known change to files.
        Filenames are stored if there is a change and either update_files
        is True at instrument object level or files.refresh() is called.

        Returns
        -------
        pandas.Series
            files are indexed by datetime

        """

        # refresh files
        self.refresh()
        # current files
        new_info = self._load(update_path=False)
        # previous set of files
        old_info = self._load(prev_version=True, update_path=False)
        new_files = new_info[-new_info.isin(old_info)]
        return new_files

    def refresh(self):
        """Update list of files, if there are detected changes.

        Calls underlying list_files_rtn for the particular science instrument.
        Typically, these routines search in the pysat provided path,
        where the top level is set by `pysat.params['data_dirs'] = path`
        and the instrument specific sub-directories are generated from
        the template, `self.directory_format`.

        """

        if self.list_files_generator is not None:
            estr = ''.join(('refresh() does not work with list generators'))
            raise RuntimeError(estr)

        output_str = '{platform} {name} {tag} {inst_id}'
        output_str = output_str.format(**self.sat_info)
        output_str = " ".join(("pysat is searching for", output_str, "files."))
        output_str = " ".join(output_str.split())  # Remove duplicate whitespace
        logger.info(output_str)

        # Check all potential directory locations for files.
        # Stop as soon as we find some.
        for path in self.data_paths:
            info = self.list_files_rtn(tag=self.sat_info['tag'],
                                       inst_id=self.sat_info['inst_id'],
                                       data_path=path,
                                       format_str=self.file_format)
            # Ensure the name of returned Series is None for consistency
            info.name = None

            # If we find some files, this is the one directory we store.
            # If I don't remove the directory paths then loading by filename
            # becomes more of a challenge. Plus, more memory to store, more
            # difficult for a human to parse when browsing a list, etc. The
            # approach here provides for most of the potential functionality
            # of multiple directories while still leaving the 'single' directory
            # focus and features of the original pysat intact.
            if not info.empty:
                self.data_path = path
                info = self._remove_data_dir_path(info, path=path)
                break

        # Feedback to info on number of files located
        logger.info('Found {:d} local files.'.format(len(info)))

        if not info.empty:
            # Sort files to ensure they are in order
            info = info.sort_index()

        elif params['warn_empty_file_list']:
            # Warn user if no files found, if pysat.param set
            pstrs = "\n".join(self.data_paths)
            estr = "".join(("Unable to find any files that match the supplied ",
                            "template: ", self.file_format, "\n",
                            "In the following directories: \n", pstrs))
            logger.warning(estr)

        # Attach Series of files to object
        self._attach_files(info)

        # Store - to disk, if enabled
        self._store()

    @classmethod
    def from_os(cls, data_path=None, format_str=None,
                two_digit_year_break=None, delimiter=None):
        """
        Produces a list of files and and formats it for Files class.

        Requires fixed_width or delimited filename

        Parameters
        ----------
        data_path : string
            Top level directory to search files for. This directory
            is provided by pysat to the instrument_module.list_files
            functions as data_path.
        format_str : string with python format codes
            Provides the naming pattern of the instrument files and the
            locations of date information so an ordered list may be produced.
            Supports 'year', 'month', 'day', 'hour', 'minute', 'second',
            'version', 'revision', and 'cycle'
            Ex: 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
        two_digit_year_break : int or None
            If filenames only store two digits for the year, then
            '1900' will be added for years >= two_digit_year_break
            and '2000' will be added for years < two_digit_year_break.
            If None, then four-digit years are assumed. (default=None)
        delimiter : string or NoneType
            Delimiter string upon which files will be split (e.g., '.'). If
            None, filenames will be parsed presuming a fixed width format.
            (default=None)

        Note
        ----
        Does not produce a Files instance, but the proper output
        from instrument_module.list_files method.

        The '?' may be used to indicate a set number of spaces for a variable
        part of the name that need not be extracted.
        'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v??.cdf'

        """

        if data_path is None:
            raise ValueError(" ".join(("Must supply instrument directory path",
                                       "(dir_path)")))

        # parse format string to figure out the search string to use
        # to identify files in the filesystem
        # different option required if filename is delimited
        if delimiter is None:
            wildcard = False
        else:
            wildcard = True
        search_dict = \
            futils.construct_searchstring_from_format(format_str,
                                                      wildcard=wildcard)
        search_str = search_dict['search_string']
        # perform local file search
        files = futils.search_local_system_formatted_filename(data_path,
                                                              search_str)
        # we have a list of files, now we need to extract the information
        # pull of data from the areas identified by format_str
        if delimiter is None:
            stored = futils.parse_fixed_width_filenames(files, format_str)
        else:
            stored = futils.parse_delimited_filenames(files, format_str,
                                                      delimiter)
        # process the parsed filenames and return a properly formatted Series
        return futils.process_parsed_filenames(stored, two_digit_year_break)


def process_parsed_filenames(stored, two_digit_year_break=None):
    """Accepts dict with data parsed from filenames and creates
    a pandas Series object formatted for the Files class.

    .. deprecated:: 3.0.0
      This function will be removed in pysat 4.0.0, please use the version under
      pysat.utils.files

    Parameters
    ----------
    stored : orderedDict
        Dict produced by parse_fixed_width_filenames or
        parse_delimited_filenames
    two_digit_year_break : int
        If filenames only store two digits for the year, then
        '1900' will be added for years >= two_digit_year_break
        and '2000' will be added for years < two_digit_year_break.

    Returns
    -------
    pandas.Series
        Series, indexed by datetime, with file strings

    Note
    ----
        If two files have the same date and time information in the
        filename then the file with the higher version/revision/cycle is used.
        Series returned only has one file der datetime. Version is required
        for this filtering, revision and cycle are optional.

    """

    funcname = "process_parsed_filenames"
    warnings.warn(' '.join(["_files.{:s} is".format(funcname),
                            "deprecated and will be removed in a future",
                            "version. Please use",
                            "pysat.utils.files.{:s}.".format(funcname)]),
                  DeprecationWarning, stacklevel=2)

    return futils.process_parsed_filenames(stored, two_digit_year_break)


def parse_fixed_width_filenames(files, format_str):
    """Parses list of files, extracting data identified by format_str

    .. deprecated:: 3.0.0
      This function will be removed in pysat 4.0.0, please use the version under
      pysat.utils.files

    Parameters
    ----------
    files : list
        List of files
    format_str : string with python format codes
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', and 'cycle'
        Ex: 'instrument_{year:4d}{month:02d}{day:02d}_v{version:02d}.cdf'

    Returns
    -------
    OrderedDict
        Information parsed from filenames
        'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', 'cycle'
        'files' - input list of files

    """

    funcname = "parse_fixed_width_filenames"
    warnings.warn(' '.join(["_files.{:s} is".format(funcname),
                            "deprecated and will be removed in a future",
                            "version. Please use",
                            "pysat.utils.files.{:s}.".format(funcname)]),
                  DeprecationWarning, stacklevel=2)

    return futils.parse_fixed_width_filenames(files, format_str)


def parse_delimited_filenames(files, format_str, delimiter):
    """Parses list of files, extracting data identified by format_str

    .. deprecated:: 3.0.0
      This function will be removed in pysat 4.0.0, please use the version under
      pysat.utils.files

    Parameters
    ----------
    files : list
        List of files
    format_str : string with python format codes
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', 'cycle'
        Ex: 'instrument_{year:4d}{month:02d}{day:02d}_v{version:02d}.cdf'
    delimiter : string
        Delimiter string upon which files will be split (e.g., '.')

    Returns
    -------
    OrderedDict
        Information parsed from filenames
        'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', 'cycle'
        'files' - input list of files
        'format_str' - formatted string from input

    """

    funcname = "parse_delimited_filenames"
    warnings.warn(' '.join(["_files.{:s} is".format(funcname),
                            "deprecated and will be removed in a future",
                            "version. Please use",
                            "pysat.utils.files.{:s}.".format(funcname)]),
                  DeprecationWarning, stacklevel=2)

    return futils.parse_delimited_filenames(files, format_str, delimiter)


def construct_searchstring_from_format(format_str, wildcard=False):
    """
    Parses format file string and returns string formatted for searching.

    .. deprecated:: 3.0.0
      This function will be removed in pysat 4.0.0, please use the version under
      pysat.utils.files

    Parameters
    ----------
    format_str : string with python format codes
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', and 'cycle'
        Ex: 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
    wildcard : bool
        if True, replaces the ? sequence with a * . This option may be well
        suited when dealing with delimited filenames.

    Returns
    -------
    dict
        'search_string' format_str with data to be parsed replaced with ?
        'keys' keys for data to be parsed
        'lengths' string length for data to be parsed
        'string_blocks' the filenames are broken down into fixed width
            segments and '' strings are placed in locations where data will
            eventually be parsed from a list of filenames. A standards
            compliant filename can be constructed by starting with
            string_blocks, adding keys in order, and replacing the '' locations
            with data of length length.

    Note
    ----
        The '?' may be used to indicate a set number of spaces for a variable
        part of the name that need not be extracted.
        'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v??.cdf'

    """

    funcname = "construct_searchstring_from_format"
    warnings.warn(' '.join(["_files.{:s} is".format(funcname),
                            "deprecated and will be removed in a future",
                            "version. Please use",
                            "pysat.utils.files.{:s}.".format(funcname)]),
                  DeprecationWarning, stacklevel=2)

    return futils.construct_searchstring_from_format(format_str, wildcard)


def search_local_system_formatted_filename(data_path, search_str):
    """
    Parses format file string and returns string formatted for searching.

    .. deprecated:: 3.0.0
      This function will be removed in pysat 4.0.0, please use the version under
      pysat.utils.files

    Parameters
    ----------
    data_path : string
        Top level directory to search files for. This directory
        is provided by pysat to the instrument_module.list_files
        functions as data_path.
    search_str : string
        String to search local file system for
        Ex: 'cnofs_cindi_ivm_500ms_????????_v??.cdf'
            'cnofs_cinfi_ivm_500ms_*_v??.cdf'

    Returns
    -------
    list
        list of files matching the format_str

    Note
    ----
    The use of ?s (1 ? per character) rather than the full wildcard *
    provides a more specific filename search string that limits the
    false positive rate.

    """

    funcname = "search_local_system_formatted_filename"
    warnings.warn(' '.join(["_files.{:s} is".format(funcname),
                            "deprecated and will be removed in a future",
                            "version. Please use",
                            "pysat.utils.files.{:s}.".format(funcname)]),
                  DeprecationWarning, stacklevel=2)

    return futils.search_local_system_formatted_filename(data_path, search_str)
