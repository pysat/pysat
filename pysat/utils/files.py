#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import collections
import glob
import numpy as np
import os
import re
import shutil
import string

import pandas as pds

from pysat.utils.time import create_datetime_index
from pysat.utils._core import available_instruments


def process_parsed_filenames(stored, two_digit_year_break=None):
    """Create a Files pandas Series of filenames from a formatted dict

    Parameters
    ----------
    stored : collections.orderedDict
        Dict produced by parse_fixed_width_filenames or
        parse_delimited_filenames
    two_digit_year_break : int or NoneType
        If filenames only store two digits for the year, then
        '1900' will be added for years >= two_digit_year_break
        and '2000' will be added for years < two_digit_year_break.
        If None, then four-digit years are assumed.
        (default=None)

    Returns
    -------
    pds.Series
        Series, indexed by datetime, with file strings

    Note
    ----
    If two files have the same date and time information in the filename then
    the file with the higher version/revision/cycle is used. Series returned
    only has one file per datetime. Version is required for this filtering,
    revision and cycle are optional.

    """

    search_dict = construct_searchstring_from_format(stored['format_str'])
    keys = search_dict['keys']

    if len(stored['files']) > 0:
        # Deal with the possibility of two digit years. Years above
        # or equal to break are considered to be 1900+, while
        # years below break are considered to be 2000+
        if two_digit_year_break is not None:
            idx, = np.where(np.array(stored['year'])
                            >= two_digit_year_break)
            stored['year'][idx] = stored['year'][idx] + 1900
            idx, = np.where(np.array(stored['year']) < two_digit_year_break)
            stored['year'][idx] = stored['year'][idx] + 2000

        # Need to sort the information for things to work
        rec_arr = [stored[key] for key in keys]
        rec_arr.append(stored['files'])

        # Sort all arrays by creating a sortable records array
        # withs keys corresponding to the files
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
    format_str : str
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports string formatting codes 'year', 'month', 'day', 'hour',
        'minute', 'second', 'version', 'revision', and 'cycle'. For example,
        `instrument_{year:4d}{month:02d}{day:02d}_v{version:02d}.cdf`

    Returns
    -------
    stored : collections.OrderedDict
        Information parsed from filenames that inclues: 'year', 'month', 'day',
        'hour', 'minute', 'second', 'version', 'revision', and 'cycle'.  Also
        includes 'files', an input list of files, and 'format_str', a formatted
        string from input

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
    format_str : str
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports string formatting codes 'year', 'month', 'day', 'hour',
        'minute', 'second', 'version', 'revision', and 'cycle'. For example,
        `instrument_{year:4d}{month:02d}{day:02d}_v{version:02d}.cdf`
    delimiter : string
        Delimiter string upon which files will be split (e.g., '.')

    Returns
    -------
    stored : collections.OrderedDict
        Information parsed from filenames that inclues: 'year', 'month', 'day',
        'hour', 'minute', 'second', 'version', 'revision', and 'cycle'.  Also
        includes 'files', an input list of files, and 'format_str', a formatted
        string from input

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
    """Parses format file string and returns string formatted for searching.

    Parameters
    ----------
    format_str : str
        Provides the naming pattern of the instrument files and the
        locations of date information so an ordered list may be produced.
        Supports 'year', 'month', 'day', 'hour', 'minute', 'second', 'version',
        'revision', and 'cycle'. For example,
        `instrument_{year:04d}{month:02d}{day:02d}_v{version:02d}.cdf`
    wildcard : bool
        If True, replaces the ? sequence with a * . This option may be well
        suited when dealing with delimited filenames.

    Returns
    -------
    out_dict : dict
        An output dict with the following keys:
        - 'search_string' (format_str with data to be parsed replaced with ?)
        - 'keys' (keys for data to be parsed)
        - 'lengths' (string length for data to be parsed)
        - 'string_blocks' (the filenames are broken into fixed width segments).

    Note
    ----
    The '?' may be used to indicate a set number of spaces for a variable
    part of the name that need not be extracted.
    `cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v??.cdf`

    A standards compliant filename can be constructed by starting with
    string_blocks, adding keys in order, and replacing the '' locations
    with data of length length.

    """

    out_dict = {'search_string': '',
                'keys': [],
                'lengths': [],
                'string_blocks': []}
    if format_str is None:
        raise ValueError("Must supply a filename template (format_str).")

    # Parse format string to figure out how to construct the search string
    # to identify files in the filesystem
    form = string.Formatter()
    for snip in form.parse(format_str):
        # Collect all of the format keywords. Replace them in the string with
        # the '?' wildcard. The numnber of '?'s corresponds to the length of
        # data to be parsed. The length is obtained from format keywords so
        # that we know later on where to parse information out from.
        out_dict['search_string'] += snip[0]
        out_dict['string_blocks'].append(snip[0])

        if snip[1] is not None:
            out_dict['keys'].append(snip[1])

            # Try and determine formatting width
            temp = re.findall(r'\d+', snip[2])

            if temp:
                # There are items, try and grab width
                for i in temp:
                    # Make sure there is truly something there
                    if i != 0:
                        # Store length and add to the search string
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
        String used to search for local files. For example,
        `cnofs_cindi_ivm_500ms_????????_v??.cdf` or `inst-name-*-v??.cdf`

    Returns
    -------
    files : list
        list of files matching the specified file format

    Note
    ----
    The use of ?s (1 ? per character) rather than the full wildcard * provides
    a more specific filename search string that limits the false positive rate.

    """

    # Perform local file search
    abs_search_str = os.path.join(data_path, search_str)
    files = glob.glob(abs_search_str)

    # Remove the specified data_path portion
    files = [sfile.split(data_path)[-1] for sfile in files]

    # Return the desired filename information
    return files


def update_data_directory_structure(new_template, test_run=True,
                                    full_breakdown=False,
                                    remove_empty_dirs=False):
    """Update pysat data directory structure to match supplied template

    Translates all of pysat's managed science files to a new
    directory structure. By default, pysat uses the template string stored in
    pysat.params['directory_format'] to organize files. This method makes
    it possible to transition an existing pysat installation so it works
    with the supplied new template.

    Parameters
    ----------
    new_template : str
        New directory template string. The default value for pysat is
         `os.path.join(('{platform}', '{name}', '{tag}', '{inst_id}'))`
    test_run : bool
        If True, a printout of all proposed changes will be made, but the
        directory changes will not be enacted. (default=True)
    full_breakdown : bool
        If True, a full path for every file is printed to terminal.
        (default=False)
    remove_empty_dirs : bool
        If True, all directories that had pysat.Instrument data moved
        to another location and are now empty are deleted. Traverses
        the directory chain up to the top-level directories in
        `pysat.params['data_dirs']`. (default=False)

    Note
    ----
    After updating the data directory structures users should nominally
    assign `new_template` as the directory format via
    ::

        pysat.params['directory_format'] = new_template

    """

    # Import required here to avoid circular import
    from pysat import Instrument

    # Get a list of supported instruments
    # Best solved with an upcoming method in pull #633
    insts = available_instruments()

    if test_run:
        print('Performing a test run. No files will be moved.\n')

    if len(insts.keys()) == 0:
        ostr = ''.join(('No registered instruments detected. Please register ',
                        'supporting instrument modules using the ',
                        '`pysat.utils.registry` module.'))
        print(ostr)

    for platform in insts.keys():
        for name in insts[platform].keys():
            for inst_id in insts[platform][name]['inst_ids_tags'].keys():
                tkeys = insts[platform][name]['inst_ids_tags'][inst_id].keys()
                for tag in tkeys:

                    # Get a list of current Instrument files. Some Instruments
                    # construct filenames so we start by taking only the
                    # unique ones.
                    inst = Instrument(platform=platform, name=name,
                                      inst_id=inst_id, tag=tag,
                                      update_files=True)
                    flist = inst.files.files.values
                    flist = np.unique(flist)

                    # Existing full directory path, including template.
                    curr_path = inst.files.data_path

                    # Figure out which top-level directory these files are in by
                    # removing existing directory template information.
                    # pysat supports multiple paths so we need to get
                    # which of those this particular instrument uses.
                    currdir = inst.files.data_path.split(
                        inst.files.sub_dir_path)[0]

                    # Create instrument with new information
                    new_inst = Instrument(platform=platform, name=name,
                                          inst_id=inst_id, tag=tag,
                                          update_files=False,
                                          directory_format=new_template)

                    # Get new formatted directory template
                    subdir = new_inst.files.sub_dir_path

                    # Make new path using correct top_level data directory but
                    # with new template. new_inst won't find files and thus
                    # defaults to the first of all pysat data_dirs though
                    # we know better.
                    new_path = os.path.join(currdir, subdir, '')
                    print(' '.join(('Working on Instrument:', platform, name,
                                    tag, inst_id)))
                    if curr_path == new_path:
                        print('No change in directory needed.\n')
                        break

                    print('Current path :  ' + curr_path)
                    print('Proposed path:  ' + new_path)

                    # Construct full paths in lists for old and new filenames
                    old_files = [os.path.join(inst.files.data_path, ifile)
                                 for ifile in flist]

                    # Determine which of these files exist.
                    old_exists = [os.path.isfile(ofile) for ofile in old_files]
                    idx, = np.where(old_exists)

                    if len(idx) == 0:
                        # If none of the files actually exists, likely that
                        # instruments.methods.general.list_files is appending
                        # a date to the end of the filename.
                        exists = [os.path.isfile(ofile[:-11]) for ofile in
                                  old_files]
                        if np.all(exists):
                            flist = [ifile[:-11] for ifile in flist]
                            flist = np.unique(flist)
                            old_files = [os.path.join(inst.files.data_path,
                                                      ifile)
                                         for ifile in flist]
                        else:
                            # Files don't exist as written and taking of
                            # a trailing date didn't fix everything.
                            raise ValueError()
                    elif len(idx) < len(old_files):
                        ostr = ' '.join(('{:d} out of {:d} expected files',
                                         'were not found. It is likely',
                                         'that', platform, name,
                                         'is using a combination of internally',
                                         'modified file names and regular ',
                                         'names and must be moved manually.\n'))
                        ostr = ostr.format(len(idx), len(old_files))
                        print(ostr)
                        break

                    # User feedback
                    if len(old_files) == 0:
                        print('No files found.\n')
                    else:
                        print('{:d} files located.\n'.format(
                            len(old_files)))

                    # Based on the files that do exist, construct new
                    # path names with the updated directory template.
                    new_files = [os.path.join(currdir, subdir, ifile)
                                 for ifile in flist]

                    # Some instruments may have additional directories below
                    # those expected by pysat. Get a list of all those unique
                    # directories and create as needed.
                    new_dirs = [os.path.split(ifile)[0] for ifile in new_files]
                    new_dirs = np.unique(new_dirs)
                    if not test_run:
                        for ndir in new_dirs:
                            # Create needed directories if actually moving files
                            check_and_make_path(ndir)

                    # Ready to iterate through list of files and move them
                    for ofile, nfile in zip(old_files, new_files):
                        if full_breakdown:
                            # Print the proposed changes so user may verify
                            ostr = ''.join(('Will move: ', ofile, '\n',
                                            '       to: ', nfile))
                            print(ostr)

                        if not test_run:
                            # Move files if not in test mode
                            if not os.path.isfile(nfile):
                                # Move the file now
                                shutil.move(ofile, nfile)
                            else:
                                # New file
                                ostr = ''.join(nfile, ' already exists.')
                                print(ostr)

                    if full_breakdown and (len(old_files) > 0):
                        # Sometimes include a newline to maintain consistent
                        # line spacing.
                        print('')

                    if len(old_files) > 0:
                        # No missing files and there are actually
                        # files on the disk to deal with.

                        # Get new list of files from Instrument
                        new_inst = Instrument(platform=platform, name=name,
                                              inst_id=inst_id, tag=tag,
                                              update_files=True,
                                              directory_format=new_template)

                        # Check on number of files before and after
                        nnew = len(new_inst.files.files)
                        nold = len(inst.files.files)
                        if not test_run:
                            if nnew != nold:
                                estr = ' '.join(('Number of files before and',
                                                 'after not the same.',
                                                 'Something has gone wrong for',
                                                 platform, name, tag, inst_id))
                                raise ValueError(estr)

                            print(' '.join(('All', platform, name, tag, inst_id,
                                            'files moved and accounted for.',
                                            '\n')))

                            # Number of files checks out. Time to remove old
                            # directories if there are no real files in there.
                            # First, get full directory path of previous inst
                            wpath = inst.files.data_path
                            while wpath != currdir and (len(wpath)
                                                        > len(currdir)):
                                # Only continue while we are at a level
                                # lower than the top-level pysat data directory.
                                if len(os.listdir(wpath)) == 0:
                                    # Directory is empty, remove it.
                                    print(''.join((wpath, ' is empty and ',
                                                   'could be removed.')))
                                    if remove_empty_dirs:
                                        shutil.rmtree(wpath)
                                        print(''.join(('Removing: ', wpath)))
                                else:
                                    print(''.join(('Directory is not empty: ',
                                                   wpath, '\nEnding cleanup.',
                                                   '\n')))
                                    break

                                # Take off last path and start working up
                                # the directory chain.
                                wpath = os.path.sep.join(wpath.split(
                                    os.path.sep)[:-2])
                            else:
                                print('\n')

    return


def check_and_make_path(path):
    """Checks if path exists, creates it if it doesn't.

    Parameters
    ----------
    path : string
        Directory path without any file names. Creates all
        necessary directories to complete the path.

    Raises
    ------
    ValueError
        If input path and internally constructed path are not equal.

    """

    if not os.path.exists(path):
        # Make path, checking to see that each level exists before attempting
        root_path, local_dir = os.path.split(path)

        # Check that we have a remotely valid path
        if len(root_path) == 0:
            raise ValueError('Invalid path specification.')

        # Iterate through given path until we hit a directory that exists.
        make_dir = list()
        while not os.path.exists(root_path):
            if len(local_dir) > 0:
                # Avoid case where input is path='/stuff/level/'.
                # The trailing '/' leads to a local_dir=''
                make_dir.append(local_dir)
            root_path, local_dir = os.path.split(root_path)

        if len(local_dir) > 0:
            # Avoid case where input is path='/stuff/level/'.
            # The trailing '/' leads to a local_dir=''
            make_dir.append(local_dir)

        while len(make_dir) > 0:
            local_dir = make_dir.pop()
            root_path = os.path.join(root_path, local_dir)
            os.mkdir(root_path)

        if os.path.normpath(root_path) != os.path.normpath(path):
            raise ValueError('Desired and constructed paths differ')

    return
