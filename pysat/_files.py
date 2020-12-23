import datetime as dt
import numpy as np
import os
import warnings
import weakref

import pandas as pds
from pysat import data_dir as data_dir
from pysat.utils import files as futils
from pysat import logger


class Files(object):
    """Maintains collection of files for instrument object.

    Uses the list_files functions for each specific instrument
    to create an ordered collection of files in time. Used by
    instrument object to load the correct files. Files also
    contains helper methods for determining the presence of
    new files and creating an ordered list of files.

    Attributes
    ----------
    base_path : string
        path to .pysat directory in user home
    start_date : datetime
        date of first file, used as default start bound for instrument
        object
    stop_date : datetime
        date of last file, used as default stop bound for instrument
        object
    update_files : boolean
        If True, immediately query filesystem for instrument files and
        store
        (default=False)
    file_format : str or NoneType
        File naming structure in string format.  Variables such as year,
        month, and inst_id will be filled in as needed using python string
        formatting.  The default file format structure is supplied in the
        instrument list_files routine. (default=None)

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

    def __init__(self, sat, directory_format=None,
                 update_files=False, file_format=None, write_to_disk=True,
                 ignore_empty_files=False):
        """ Initialization for Files class object

        Parameters
        -----------
        sat : pysat._instrument.Instrument
            Instrument object
        directory_format : string or NoneType
            directory naming structure in string format. Variables such as
            platform, name, and tag will be filled in as needed using python
            string formatting. The default directory structure would be
            expressed as '{platform}/{name}/{tag}'.
            If None, the default directory structure is used
            (default=None)
        update_files : boolean
            If True, immediately query filesystem for instrument files and
            store
            (default=False)
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
            ensure the filesiizes are greater than zero. Empty files are
            removed from the stored list of files.
        """

        # Set the hidden variables
        self._sat = weakref.proxy(sat)
        self._update_files = update_files

        # location of .pysat file
        self.home_path = os.path.join(os.path.expanduser('~'), '.pysat')
        self.start_date = None
        self.stop_date = None
        self.files = pds.Series(None, dtype='object')
        # location of stored files
        self.stored_file_name = ''.join((self._sat.platform, '_',
                                         self._sat.name, '_', self._sat.tag,
                                         '_', self._sat.inst_id,
                                         '_stored_file_info.txt'))

        # path for sub-directories under pysat data path
        if directory_format is None:
            directory_format = os.path.join('{platform}', '{name}', '{tag}')
        self.directory_format = directory_format

        # user-specified file format
        self.file_format = file_format

        # construct subdirectory path
        self.sub_dir_path = self.directory_format.format(
            name=self._sat.name, platform=self._sat.platform,
            tag=self._sat.tag, inst_id=self._sat.inst_id)
        # ensure we have a path for pysat data directory
        if data_dir == '':
            raise RuntimeError(" ".join(("pysat's data_dir is None. Set a",
                                         "directory using",
                                         "pysat.utils.set_data_dir.")))
        # make sure path always ends with directory seperator
        self.data_path = os.path.join(data_dir, self.sub_dir_path)
        if self.data_path[-2] == os.path.sep:
            self.data_path = self.data_path[:-1]
        elif self.data_path[-1] != os.path.sep:
            self.data_path = os.path.join(self.data_path, '')

        # store write to disk preference
        self.write_to_disk = write_to_disk
        if self.write_to_disk is False:
            # using blank memory rather than loading from disk
            self._previous_file_list = pds.Series([], dtype='a')
            self._current_file_list = pds.Series([], dtype='a')

        # store ignore_empty_files preference
        self.ignore_empty_files = ignore_empty_files

        if self._sat.platform != '':
            # load stored file info
            info = self._load()
            if not info.empty:
                self._attach_files(info)
                if update_files:
                    self.refresh()
            else:
                # couldn't find stored info, load file list and then store
                self.refresh()

    def __repr__(self):
        # Because the local Instrument object is weakly referenced, it may
        # not always be accessible
        try:
            inst_repr = self._sat.__repr__()
        except ReferenceError:
            inst_repr = "Instrument(weakly referenced)"

        out_str = "".join(["Files(", inst_repr, ", directory_format=",
                           "'{:}'".format(self.directory_format),
                           ", update_files=",
                           "{:}, file_format=".format(self._update_files),
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

    def _filter_empty_files(self):
        """Update the file list (files) with empty files ignored"""

        keep_index = []
        for i, fi in enumerate(self.files):
            # create full path
            fi_path = os.path.join(self.data_path, fi)
            # ensure it exists
            if os.path.exists(fi_path):
                # check for size
                if os.path.getsize(fi_path) > 0:
                    # store if not empty
                    keep_index.append(i)
        # remove filenames as needed
        dropped_num = len(self.files.index) - len(keep_index)
        if dropped_num > 0:
            print(' '.join(('Removing', str(dropped_num),
                  'empty files from Instrument list.')))
            self.files = self.files.iloc[keep_index]

    def _attach_files(self, files_info):
        """Attach results of instrument list_files routine to Instrument object

        Parameters
        ----------
        file_info :
            Stored file information

        Returns
        -------
        updates the file list (files), start_date, and stop_date attributes
        of the Files class object.

        """

        if not files_info.empty:
            unique_files = len(files_info.index.unique()) != len(files_info)
            if (not self._sat.multi_file_day and unique_files):
                estr = 'Duplicate datetimes in provided file '
                estr = '{:s}information.\nKeeping one of each '.format(estr)
                estr = '{:s}of the duplicates, dropping the rest.'.format(estr)
                logger.warning(estr)
                ind = files_info.index.duplicated()
                logger.warning(files_info.index[ind].unique())

                idx = np.unique(files_info.index, return_index=True)
                files_info = files_info.iloc[idx[1]]
                # raise ValueError('List of files must have unique datetimes.')

            self.files = files_info.sort_index()
            # filter for empty files here (in addition to refresh)
            if self.ignore_empty_files:
                self._filter_empty_files()
            # extract date information
            if not self.files.empty:
                self.start_date = \
                    self._sat._filter_datetime_input(self.files.index[0])
                self.stop_date = \
                    self._sat._filter_datetime_input(self.files.index[-1])
            else:
                self.start_date = None
                self.stop_date = None
        else:
            self.start_date = None
            self.stop_date = None
            # convert to object type
            # necessary if Series is empty, enables == checks with strings
            self.files = files_info.astype(np.dtype('O'))

    def _store(self):
        """Store currently loaded filelist for instrument onto filesystem"""

        name = self.stored_file_name
        # check if current file data is different than stored file list
        # if so, move file list to previous file list, store current to file
        # if not, do nothing
        stored_files = self._load()
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
                                                 'previous_' + name),
                                    date_format='%Y-%m-%d %H:%M:%S.%f',
                                    header=False)
                self.files.to_csv(os.path.join(self.home_path, name),
                                  date_format='%Y-%m-%d %H:%M:%S.%f',
                                  header=False)
            else:
                self._previous_file_list = stored_files
                self._current_file_list = self.files.copy()
        return

    def _load(self, prev_version=False):
        """Load stored filelist and return as Pandas Series

        Parameters
        ----------
        prev_version : boolean
            if True, will load previous version of file list

        Returns
        -------
        pandas.Series
            Full path file names are indexed by datetime
            Series is empty if there is no file list to load

        """

        fname = self.stored_file_name
        if prev_version:
            fname = os.path.join(self.home_path, 'previous_' + fname)
        else:
            fname = os.path.join(self.home_path, fname)

        if os.path.isfile(fname) and (os.path.getsize(fname) > 0):
            if self.write_to_disk:
                return pds.read_csv(fname, index_col=0, parse_dates=True,
                                    squeeze=True, header=None)
            else:
                # grab files from memory
                if prev_version:
                    return self._previous_file_list
                else:
                    return self._current_file_list
        else:
            return pds.Series([], dtype='a')

    def refresh(self):
        """Update list of files, if there are changes.

        Calls underlying list_files_rtn for the particular science instrument.
        Typically, these routines search in the pysat provided path,
        pysat_data_dir/platform/name/tag/,
        where pysat_data_dir is set by pysat.utils.set_data_dir(path=path).


        """

        output_str = '{platform} {name} {tag} {inst_id}'
        output_str = output_str.format(platform=self._sat.platform,
                                       name=self._sat.name, tag=self._sat.tag,
                                       inst_id=self._sat.inst_id)
        output_str = " ".join(("pysat is searching for", output_str, "files."))
        output_str = " ".join(output_str.split())  # Remove duplicate whitespace
        logger.info(output_str)

        info = self._sat._list_files_rtn(tag=self._sat.tag,
                                         inst_id=self._sat.inst_id,
                                         data_path=self.data_path,
                                         format_str=self.file_format)
        info = self._remove_data_dir_path(info)
        if not info.empty:
            if self.ignore_empty_files:
                self._filter_empty_files()
            logger.info('Found {:d} local files.'.format(len(info)))
        else:
            estr = "Unable to find any files that match the supplied template."
            estr += " If you have the necessary files please check pysat "
            estr += "settings and file locations (e.g. pysat.pysat_dir)."
            logger.warning(estr)
        # attach to object
        self._attach_files(info)
        # store - to disk, if enabled
        self._store()

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
        new_info = self._load()
        # previous set of files
        old_info = self._load(prev_version=True)
        new_files = new_info[-new_info.isin(old_info)]
        return new_files

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

    # slicing via date and index filename is inclusive slicing,
    # date and index are normal non-inclusive end point

    def __getitem__(self, key):
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

    def _remove_data_dir_path(self, inp=None):
        """Remove the data directory path from filenames"""
        if inp is not None:
            split_str = os.path.join(self.data_path, '')
            return inp.apply(lambda x: x.split(split_str)[-1])

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
