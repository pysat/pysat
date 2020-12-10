import collections
import glob
import numpy as np
import os
import re
import string

import pandas as pds

from pysat.utils.time import create_datetime_index


def process_parsed_filenames(stored, two_digit_year_break=None):
    """Accepts dict with data parsed from filenames and creates
    a pandas Series object formatted for the Files class.

    Parameters
    ----------
    stored : orderedDict
        Dict produced by parse_fixed_width_filenames or
        parse_delimited_filenames
    two_digit_year_break : int or None
        If filenames only store two digits for the year, then
        '1900' will be added for years >= two_digit_year_break
        and '2000' will be added for years < two_digit_year_break.
        If None, then four-digit years are assumed.
        (default=None)

    Returns
    -------
    pandas.Series
        Series, indexed by datetime, with file strings

    Note
    ----
        If two files have the same date and time information in the
        filename then the file with the higher version/revision/cycle is used.
        Series returned only has one file per datetime. Version is required
        for this filtering, revision and cycle are optional.

    """

    search_dict = construct_searchstring_from_format(stored['format_str'])
    keys = search_dict['keys']

    if len(stored['files']) > 0:
        # deal with the possibility of two digit years
        # years above or equal to break are considered to be 1900+
        # years below break are considered to be 2000+
        if two_digit_year_break is not None:
            idx, = np.where(np.array(stored['year'])
                            >= two_digit_year_break)
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
        if stored['cycle'] is None:
            stored['cycle'] = np.zeros(len(files))

        index = create_datetime_index(year=stored['year'],
                                      month=stored['month'],
                                      day=stored['day'],
                                      uts=stored['second'])

        # if version, revision, and cycle are supplied
        # use these parameters to weed out files that have been replaced
        # with updated versions
        # first, check for duplicate index times
        dups = index[index.duplicated()].unique()
        if (len(dups) > 0) and (stored['version'] is not None):
            # we have duplicates
            # keep the highest version/revision combo
            version = pds.Series(stored['version'], index=index)
            revision = pds.Series(stored['revision'], index=index)
            cycle = pds.Series(stored['cycle'], index=index)
            revive = version * 100000. + revision + cycle * 1e-5
            frame = pds.DataFrame({'files': files, 'revive': revive,
                                   'time': index}, index=index)
            frame = frame.sort_values(by=['time', 'revive'],
                                      ascending=[True, False])
            frame = frame.drop_duplicates(subset='time', keep='first')

            return frame['files']
        else:
            return pds.Series(files, index=index)
    else:
        return pds.Series(None, dtype='object')


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
        'revision', and 'cycle'
        Ex: 'instrument_{year:4d}{month:02d}{day:02d}_v{version:02d}.cdf'

    Returns
    -------
    stored : OrderedDict
        Information parsed from filenames
        'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', 'cycle'
        'files' - input list of files

    """

    # create storage for data to be parsed from filenames
    ordered_keys = ['year', 'month', 'day', 'hour', 'minute', 'second',
                    'version', 'revision', 'cycle']
    stored = collections.OrderedDict({kk: list() for kk in ordered_keys})

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
        'revision', and 'cycle'
        Ex: 'instrument_{year:4d}{month:02d}{day:02d}_v{version:02d}.cdf'
    delimiter : string
        Delimiter string upon which files will be split (e.g., '.')

    Returns
    -------
    stored : OrderedDict
        Information parsed from filenames
        'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', 'cycle'
        'files' - input list of files
        'format_str' - formatted string from input

    """

    # create storage for data to be parsed from filenames
    ordered_keys = ['year', 'month', 'day', 'hour', 'minute', 'second',
                    'version', 'revision', 'cycle']
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
    for block in parsed_block:
        if block != ['', '']:
            if block[0] == '':
                block = block[1:]
            if block[-1] == '':
                block = block[:-1]
            pblock.extend(block)
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
        'revision', and 'cycle'
        Ex: 'instrument_{year:04d}{month:02d}{day:02d}_v{version:02d}.cdf'
    wildcard : bool
        if True, replaces the ? sequence with a * . This option may be well
        suited when dealing with delimited filenames.

    Returns
    -------
    out_dict : dict
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

    out_dict = {'search_string': '',
                'keys': [],
                'lengths': [],
                'string_blocks': []}
    if format_str is None:
        raise ValueError("Must supply a filename template (format_str).")

    # parse format string to figure out how to construct the search string
    # to identify files in the filesystem
    form = string.Formatter()
    for snip in form.parse(format_str):
        # collect all of the format keywords
        # replace them in the string with the '?' wildcard
        # numnber of ?s goes with length of data to be parsed
        # length grabbed from format keywords so we know
        # later on where to parse information out from
        out_dict['search_string'] += snip[0]
        out_dict['string_blocks'].append(snip[0])
        if snip[1] is not None:
            out_dict['keys'].append(snip[1])
            # try and determine formatting width
            temp = re.findall(r'\d+', snip[2])
            if temp:
                # there are items, try and grab width
                for i in temp:
                    # make sure there is truly something there
                    if i != 0:
                        # store length and add to the search string
                        out_dict['lengths'].append(int(i))
                        if not wildcard:
                            out_dict['search_string'] += '?' * int(i)
                        else:
                            out_dict['search_string'] += '*'
                        break
            else:
                raise ValueError("Couldn't determine formatting width")

    return out_dict


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
    files : list
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
