from __future__ import print_function
from __future__ import absolute_import

import string
import os
import weakref
import re
import glob
import numpy as np
import pandas as pds
from pysat import data_dir as data_dir

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
    data_path : string
        path to the directory containing instrument files,
        top_dir/platform/name/tag/
    manual_org : bool
        if True, then Files will look directly in pysat data directory
        for data files and will not use /platform/name/tag
    update_files : bool
        updates files on instantiation if True

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
                                sat_id=sat_id)
        # first file
        inst.files[0]

        # files from start up to stop (exclusive on stop)
        start = pysat.datetime(2009,1,1)
        stop = pysat.datetime(2009,1,3)
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
        """ Initialization for Files class object

        Parameters
        -----------
        sat : pysat._instrument.Instrument
            Instrument object
        manual_org : boolian
            If True, then pysat will look directly in pysat data directory
            for data files and will not use default /platform/name/tag
            (default=False)
        directory_format : string or NoneType
            directory naming structure in string format. Variables such as
            platform, name, and tag will be filled in as needed using python
            string formatting. The default directory structure would be
            expressed as '{platform}/{name}/{tag}' (default=None)
        update_files : boolean
            If True, immediately query filesystem for instrument files and
            store
            (default=False)
        file_format : str or NoneType
            File naming structure in string format.  Variables such as year,
            month, and sat_id will be filled in as needed using python string
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

        # pysat.Instrument object
        self._sat = weakref.proxy(sat)
        # location of .pysat file
        self.home_path = os.path.join(os.path.expanduser('~'), '.pysat')
        self.start_date = None
        self.stop_date = None
        self.files = pds.Series(None)
        # location of stored files
        self.stored_file_name = ''.join((self._sat.platform, '_',
                                         self._sat.name, '_', self._sat.tag,
                                         '_', self._sat.sat_id,
                                         '_stored_file_info.txt'))

        # flag for setting simple organization of files, only
        # look under pysat_data_dir
        self.manual_org = manual_org
        # path for sub-directories under pysat data path
        if directory_format is None:
            directory_format = os.path.join('{platform}', '{name}', '{tag}')
        self.directory_format = directory_format

        # user-specified file format
        self.file_format = file_format

        if manual_org:
            self.sub_dir_path = ''
        else:
            # construct subdirectory path
            self.sub_dir_path = \
                    self.directory_format.format(name=self._sat.name,
                                                 platform=self._sat.platform,
                                                 tag=self._sat.tag,
                                                 sat_id=self._sat.sat_id)
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
        -----------
        file_info :
            Stored file information

        Returns
        ---------
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
            # # of items is different, things are new
            new_flag = True
        elif len(stored_files) == len(self.files):
            # # of items equal, check specifically for equality
            if stored_files.eq(self.files).all():
                new_flag = False
            else:
                # not equal, there are new files
                new_flag = True

        if new_flag:

            if self.write_to_disk:
                stored_files.to_csv(os.path.join(self.home_path,
                                                 'previous_'+name),
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
            fname = os.path.join(self.home_path, 'previous_'+fname)
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

        Calls underlying list_rtn for the particular science instrument.
        Typically, these routines search in the pysat provided path,
        pysat_data_dir/platform/name/tag/,
        where pysat_data_dir is set by pysat.utils.set_data_dir(path=path).


        """

        output_str = '{platform} {name} {tag} {sat_id}'
        output_str = output_str.format(platform=self._sat.platform,
                                       name=self._sat.name, tag=self._sat.tag,
                                       sat_id=self._sat.sat_id)
        output_str = " ".join(("pysat is searching for", output_str, "files."))
        output_str = " ".join(output_str.split())
        logger.info(output_str)

        info = self._sat._list_rtn(tag=self._sat.tag, sat_id=self._sat.sat_id,
                                   data_path=self.data_path,
                                   format_str=self.file_format)
        info = self._remove_data_dir_path(info)
        if not info.empty:
            if self.ignore_empty_files:
                self._filter_empty_files()
            logger.info('Found {ll:d} of them.'.format(ll=len(info)))
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
                raise ValueError('Could not find "' + fname +
                                 '" in available file list. Valid Example: ' +
                                 self.files.iloc[0])
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
            if isinstance(key.start, pds.datetime):
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

    def get_file_array(self, start, end):
        """Return a list of filenames between and including start and end.

        Parameters
        ----------
            start: array_like or single string
                filenames for start of returned filelist
            stop: array_like or single string
                filenames inclusive end of list

        Returns
        -------
            list of filenames between and including start and end over all
            intervals.

        """
        if hasattr(start, '__iter__') & hasattr(end, '__iter__'):
            files = []
            for (sta, stp) in zip(start, end):
                id1 = self.get_index(sta)
                id2 = self.get_index(stp)
                files.extend(self.files.iloc[id1:id2+1])
        elif hasattr(start, '__iter__') | hasattr(end, '__iter__'):
            estr = 'Either both or none of the inputs need to be iterable'
            raise ValueError(estr)
        else:
            id1 = self.get_index(start)
            id2 = self.get_index(end)
            files = self.files[id1:id2+1].to_list()
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
            'version', and 'revision'
            Ex: 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
        two_digit_year_break : int
            If filenames only store two digits for the year, then
            '1900' will be added for years >= two_digit_year_break
            and '2000' will be added for years < two_digit_year_break.
        delimiter : string (None)
            If set, then filename will be processed using delimiter rather
            than assuming a fixed width

        Note
        ----
        Does not produce a Files instance, but the proper output
        from instrument_module.list_files method.

        The '?' may be used to indicate a set number of spaces for a variable
        part of the name that need not be extracted.
        'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v??.cdf'

        """

        if data_path is None:
            raise ValueError("Must supply instrument directory path " +
                             "(dir_path)")

        # parse format string to figure out the search string to use
        # to identify files in the filesystem
        # different option required if filename is delimited
        if delimiter is None:
            wildcard = False
        else:
            wildcard = True
        search_dict = construct_searchstring_from_format(format_str,
                                                         wildcard=wildcard)
        search_str = search_dict['search_string']
        # perform local file search
        files = search_local_system_formatted_filename(data_path, search_str)
        # we have a list of files, now we need to extract the information
        # pull of data from the areas identified by format_str
        if delimiter is None:
            stored = parse_fixed_width_filenames(files, format_str)
        else:
            stored = parse_delimited_filenames(files, format_str, delimiter)
        # process the parsed filenames and return a properly formatted Series
        return process_parsed_filenames(stored, two_digit_year_break)


def process_parsed_filenames(stored, two_digit_year_break=None):
    """Accepts dict with data parsed from filenames and creates
    a pandas Series object formatted for the Files class.

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
        filename then the file with the higher version/revision is used.
        Series returned only has one file der datetime. Version is required
        for this filtering, revision is optional.

    """

    from pysat.utils.time import create_datetime_index

    search_dict = construct_searchstring_from_format(stored['format_str'])
    keys = search_dict['keys']

    if len(stored['files']) > 0:
        # deal with the possibility of two digit years
        # years above or equal to break are considered to be 1900+
        # years below break are considered to be 2000+
        if two_digit_year_break is not None:
            idx, = np.where(np.array(stored['year']) >=
                            two_digit_year_break)
            stored['year'][idx] = stored['year'][idx] + 1900
            idx, = np.where(np.array(stored['year']) < two_digit_year_break)
            stored['year'][idx] = stored['year'][idx] + 2000

        # need to sort the information for things to work
        rec_arr = [stored[key] for key in keys]
        rec_arr.append(stored['files'])
        # sort all arrays
        # create a sortable records array
        # keys with files
        val_keys = keys + ['files']
        rec_arr = np.rec.fromarrays(rec_arr, names=val_keys)
        rec_arr.sort(order=val_keys, axis=0)

        # pull out sorted info
        for key in keys:
            stored[key] = rec_arr[key]
        files = rec_arr['files']

        # add hour and minute information to 'second'
        if stored['second'] is None:
            stored['second'] = np.zeros(len(files))
        if stored['hour'] is not None:
            stored['second'] += 3600 * stored['hour']
        if stored['minute'] is not None:
            stored['second'] += 60 * stored['minute']
        # version shouldn't be set to zero
        # version is required to remove duplicate datetimes
        if stored['revision'] is None:
            stored['revision'] = np.zeros(len(files))

        index = create_datetime_index(year=stored['year'],
                                      month=stored['month'],
                                      day=stored['day'],
                                      uts=stored['second'])

        # if version and revision are supplied
        # use these parameters to weed out files that have been replaced
        # with updated versions
        # first, check for duplicate index times
        dups = index[index.duplicated()].unique()
        if (len(dups) > 0) and (stored['version'] is not None):
            # we have duplicates
            # keep the highest version/revision combo
            version = pds.Series(stored['version'], index=index)
            revision = pds.Series(stored['revision'], index=index)
            revive = version * 100000. + revision
            frame = pds.DataFrame({'files': files, 'revive': revive,
                                   'time': index}, index=index)
            frame = frame.sort_values(by=['time', 'revive'],
                                      ascending=[True, False])
            frame = frame.drop_duplicates(subset='time', keep='first')

            return frame['files']
        else:
            return pds.Series(files, index=index)
    else:
        return pds.Series(None)


def parse_fixed_width_filenames(files, format_str):
    """Parses list of files, extracting data identified by format_str

    Parameters
    ----------
    files : list
        List of files
    format_str : string with python format codes
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        and 'revision'
        Ex: 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'

    Returns
    -------
    OrderedDict
        Information parsed from filenames
        'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision'
        'files' - input list of files

    """

    import collections

    # create storage for data to be parsed from filenames
    stored = collections.OrderedDict()
    stored['year'] = []
    stored['month'] = []
    stored['day'] = []
    stored['hour'] = []
    stored['minute'] = []
    stored['second'] = []
    stored['version'] = []
    stored['revision'] = []

    if len(files) == 0:
        stored['files'] = []
        # include format string as convenience for later functions
        stored['format_str'] = format_str
        return stored

    # parse format string to get information needed to parse filenames
    search_dict = construct_searchstring_from_format(format_str)
    snips = search_dict['string_blocks']
    lengths = search_dict['lengths']
    keys = search_dict['keys']

    # determine the locations the date/version information in a filename is
    # stored use these indices to slice out date from filenames
    idx = 0
    begin_key = []
    end_key = []
    for i, snip in enumerate(snips):
        idx += len(snip)
        if i < (len(lengths)):
            begin_key.append(idx)
            idx += lengths[i]
            end_key.append(idx)
    max_len = idx
    # setting up negative indexing to pick out filenames
    key_str_idx = [np.array(begin_key, dtype=int) - max_len,
                   np.array(end_key, dtype=int) - max_len]
    # need to parse out dates for datetime index
    for i, temp in enumerate(files):
        for j, key in enumerate(keys):
            val = temp[key_str_idx[0][j]:key_str_idx[1][j]]
            stored[key].append(val)
    # convert to numpy arrays
    for key in stored.keys():
        stored[key] = np.array(stored[key]).astype(int)
        if len(stored[key]) == 0:
            stored[key] = None
    # include files in output
    stored['files'] = files
    # include format string as convenience for later functions
    stored['format_str'] = format_str

    return stored


def parse_delimited_filenames(files, format_str, delimiter):
    """Parses list of files, extracting data identified by format_str

    Parameters
    ----------
    files : list
        List of files
    format_str : string with python format codes
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        and 'revision'
        Ex: 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'

    Returns
    -------
    OrderedDict
        Information parsed from filenames
        'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision'
        'files' - input list of files
        'format_str' - formatted string from input

    """

    import collections

    # create storage for data to be parsed from filenames
    ordered_keys = ['year', 'month', 'day', 'hour', 'minute', 'second',
                    'version', 'revision']
    stored = collections.OrderedDict({kk: list() for kk in ordered_keys})

    # exit early if there are no files
    if len(files) == 0:
        stored['files'] = []
        # include format string as convenience for later functions
        stored['format_str'] = format_str
        return stored

    # parse format string to get information needed to parse filenames
    search_dict = construct_searchstring_from_format(format_str, wildcard=True)
    snips = search_dict['string_blocks']
    keys = search_dict['keys']

    # going to parse string on delimiter
    # it is possible that other regions have the delimiter but aren't
    # going to be parsed out
    # so apply delimiter breakdown to the string blocks as a guide
    pblock = []
    parsed_block = [snip.split(delimiter) for snip in snips]
    for _ in parsed_block:
        if _ != ['', '']:
            if _[0] == '':
                _ = _[1:]
            if _[-1] == '':
                _ = _[:-1]
            pblock.extend(_)
        pblock.append('')
    parsed_block = pblock[:-1]
    # need to parse out dates for datetime index
    for temp in files:
        split_name = temp.split(delimiter)
        idx = 0
        for sname, bname in zip(split_name, parsed_block):
            if bname == '':
                # areas with data to be parsed are indicated with a
                # '' in parsed_block
                stored[keys[idx]].append(sname)
                idx += 1

    # convert to numpy arrays
    for key in stored.keys():
        try:
            # Assume key value is numeric integer
            stored[key] = np.array(stored[key]).astype(int)
        except ValueError:
            # Store key value as string
            stored[key] = np.array(stored[key])
        if len(stored[key]) == 0:
            stored[key] = None
    # include files in output
    stored['files'] = files
    # include format string as convenience for later functions
    stored['format_str'] = format_str

    return stored


def construct_searchstring_from_format(format_str, wildcard=False):
    """
    Parses format file string and returns string formatted for searching.

    Parameters
    ----------
    format_str : string with python format codes
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        and 'revision'
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

    if format_str is None:
        raise ValueError("Must supply a filename template (format_str).")

    # parse format string to figure out how to construct the search string
    # to identify files in the filesystem
    search_str = ''
    form = string.Formatter()
    # stores the keywords extracted from format_string
    keys = []
    # and length of string
    snips = []
    lengths = []
    for snip in form.parse(format_str):
        # collect all of the format keywords
        # replace them in the string with the '?' wildcard
        # numnber of ?s goes with length of data to be parsed
        # length grabbed from format keywords so we know
        # later on where to parse information out from
        search_str += snip[0]
        snips.append(snip[0])
        if snip[1] is not None:
            keys.append(snip[1])
            # try and determine formatting width
            temp = re.findall(r'\d+', snip[2])
            if temp:
                # there are items, try and grab width
                for i in temp:
                    # make sure there is truly something there
                    if i != 0:
                        # store length and add to the search string
                        lengths.append(int(i))
                        if not wildcard:
                            search_str += '?'*int(i)
                        else:
                            search_str += '*'
                        break
            else:
                raise ValueError("Couldn't determine formatting width")

    return {'search_string': search_str,
            'keys': keys,
            'lengths': lengths,
            'string_blocks': snips}


def search_local_system_formatted_filename(data_path, search_str):
    """
    Parses format file string and returns string formatted for searching.

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

    # perform local file search
    abs_search_str = os.path.join(data_path, search_str)
    files = glob.glob(abs_search_str)
    # remove data_path portion
    files = [sfile.split(data_path)[-1] for sfile in files]
    # return info
    return files
