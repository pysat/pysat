# -*- coding: utf-8 -*-
"""SuperDARN data support for grdex files(Alpha Level!)

Properties
----------
platform
    'superdarn'
name
    'grdex'
tag
    'north' or 'south' for Northern/Southern hemisphere data

Note
----
Requires davitpy and davitpy to load SuperDARN files.
Uses environment variables set by davitpy to download files
from Virginia Tech SuperDARN data servers. davitpy routines
are used to load SuperDARN data.

This material is based upon work supported by the
National Science Foundation under Grant Number 1259508.

Any opinions, findings, and conclusions or recommendations expressed in this
material are those of the author(s) and do not necessarily reflect the views
of the National Science Foundation.


Warnings
--------
Cleaning only removes entries that have 0 vectors, grdex files
are constituted from what it is thought to be good data.

"""

from __future__ import print_function
from __future__ import absolute_import
import functools

import pandas as pds
import numpy as np

import pysat

import logging
logger = logging.getLogger(__name__)


platform = 'superdarn'
name = 'grdex'
tags = {'north': '',
        'south': ''}
sat_ids = {'': ['north', 'south']}
_test_dates = {'': {'north': pysat.datetime(2009, 1, 1),
                    'south': pysat.datetime(2009, 1, 1)}}


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    Returns
    --------
    Void : (NoneType)
        Object modified in place.


    """

    # reset the list_remote_files routine to include the data path
    # now conveniently included with instrument object
    self._list_remote_rtn = \
        functools.partial(list_remote_files,
                          data_path=self.files.data_path,
                          format_str=self.files.file_format)

    # data acknowledgement from SuperDARN
    # coped from SD Documents area of VT SuperDARN webpage
    # http://vt.superdarn.org/tiki-list_file_gallery.php?galleryId=81
    # How to acknowledge use of SuperDARN Data - 2017
    logger.info('Authors should acknowledge the use of SuperDARN data. ' +
          'SuperDARN is a collection of radars funded by national scientific ' +
          'funding agencies of Australia, Canada, China, France, Italy, ' +
          'Japan, Norway, South Africa, United Kingdom and the United States ' +
          'of America.')
    return


def list_remote_files(tag, sat_id, data_path=None, format_str=None):
    """Lists remote files available for SuperDARN.

    Note
    ----
    This routine currently fakes the list but
    produces the desired effect of keeping data current.
    Begins with data in 1985. (this needs to be checked)

    Parameters
    ----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)

    Returns
    -------
    pandas.Series
        Series indexed by date that stores the filename for each date.

    """

    # given the function of SuperMAG, create a fake list of files
    # starting 01 Jan 1970, through today
    now = pysat.datetime.now()
    now = pysat.datetime(now.year, now.month, now.day)
    # create a list of dates with appropriate frequency
    index = pds.period_range(pysat.datetime(1985, 1, 1), now, freq='D')
    # pre fill in blank strings
    remote_files = pds.Series([''] * len(index), index=index)

    # pysat compares both dates and filenames when determining
    # which files it needs to download
    # so we need to ensure that filename for dates that overlap
    # are the same or data that is already present will be redownloaded

    # need to get a list of the current files attached to
    # the Instrument object. In this case, the object hasn't
    # been passed in.....
    #   that is ok, we can just call list_files right here
    #   except we don't have the data path
    # the init function above is used to reset the
    # lost_remote_files method with one where the
    # data path and format_str are set
    local_files = list_files(tag, sat_id, data_path, format_str)
    # iterating directly since pandas is complaining about periods
    # between different between indexes
    for time, fname in local_files.iteritems():
        remote_files.loc[time] = fname
    return remote_files


def list_files(tag='north', sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : string
        Denotes type of file to load.  Accepted types are 'north' and 'south'.
        (default='north')
    sat_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : string or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files
    """

    if format_str is None and tag is not None:
        if tag == 'north' or tag == 'south':
            hemi_fmt = ''.join(('{year:4d}{month:02d}{day:02d}.', tag,
                                '.grdex'))
            return pysat.Files.from_os(data_path=data_path,
                                       format_str=hemi_fmt)
        else:
            estr = 'Unrecognized tag name for SuperDARN, north or south.'
            raise ValueError(estr)
    elif format_str is None:
        estr = 'A tag name must be passed to SuperDARN.'
        raise ValueError(estr)
    else:
        return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def load(fnames, tag=None, sat_id=None):
    import davitpy
    if len(fnames) <= 0:
        return pysat.DataFrame(None), pysat.Meta(None)
    elif len(fnames) == 1:

        myPtr = davitpy.pydarn.sdio.sdDataPtr(sTime=pysat.datetime(1980, 1, 1),
                                              fileType='grdex',
                                              eTime=pysat.datetime(2250, 1, 1),
                                              hemi=tag,
                                              fileName=fnames[0])
        myPtr.open()

        in_list = []
        in_dict = {'stid': [],
                   'channel': [],
                   'noisemean': [],
                   'noisesd': [],
                   'gsct': [],
                   'nvec': [],
                   'pmax': [],
                   'start_time': [],
                   'end_time': [],
                   'vemax': [],
                   'vemin': [],
                   'pmin': [],
                   'programid': [],
                   'wmax': [],
                   'wmin': [],
                   'freq': []}

        while True:
            info = myPtr.readRec()
            if info is None:
                myPtr.close()
                break

            drift_frame = pds.DataFrame.from_records(info.vector.__dict__,
                                                     nrows=len(info.pmax),
                                                     index=info.vector.index)
            drift_frame['partial'] = 1
            drift_frame.drop('index', axis=1, inplace=True)
            drift_frame.index.name = 'index'
            sum_vec = 0
            for nvec in info.nvec:
                in_list.append(drift_frame.iloc[sum_vec:sum_vec+nvec])
                sum_vec += nvec

            in_dict['stid'].extend(info.stid)
            in_dict['channel'].extend(info.channel)
            in_dict['noisemean'].extend(info.noisemean)
            in_dict['noisesd'].extend(info.noisesd)
            in_dict['gsct'].extend(info.gsct)
            in_dict['nvec'].extend(info.nvec)
            in_dict['pmax'].extend(info.pmax)
            in_dict['start_time'].extend([info.sTime]*len(info.pmax))
            in_dict['end_time'].extend([info.eTime]*len(info.pmax))
            in_dict['vemax'].extend(info.vemax)
            in_dict['vemin'].extend(info.vemin)
            in_dict['pmin'].extend(info.pmin)
            in_dict['programid'].extend(info.programid)
            in_dict['wmax'].extend(info.wmax)
            in_dict['wmin'].extend(info.wmin)
            in_dict['freq'].extend(info.freq)

        output = pds.DataFrame(in_dict)
        output['vector'] = in_list
        output.index = output.start_time
        output.drop('start_time', axis=1, inplace=True)

        return output, pysat.Meta()
    else:
        raise ValueError('Only one filename currently supported.')


# def default(ivm):
#
#    return

def clean(self):
    # remove data when there are no vectors
    idx, = np.where(self['nvec'] > 0)
    self.data = self.data.iloc[idx]

    return


def download(date_array, tag, sat_id, data_path, user=None, password=None):
    """
    Download SuperDARN data from Virginia Tech organized for loading by pysat.

    """

    import warnings

    warnings.warn(" ".join(("Downloads for SuperDARN currently not supported,",
                            "but will be added in a future version.")))
