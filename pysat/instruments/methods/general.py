# -*- coding: utf-8 -*-
"""Provides generalized routines for integrating instruments into pysat.
"""

from __future__ import absolute_import, division, print_function

import datetime as dt
import logging
import pandas as pds

import pysat


logger = logging.getLogger(__name__)


def list_files(tag=None, sat_id=None, data_path=None, format_str=None,
               supported_tags=None, fake_daily_files_from_monthly=False,
               two_digit_year_break=None):
    """Return a Pandas Series of every file for chosen satellite data.

    This routine provides a standard interfacefor pysat instrument modules.

    Parameters
    -----------
    tag : string or NoneType
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    sat_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : string or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)
    supported_tags : dict or NoneType
        keys are sat_id, each containing a dict keyed by tag
        where the values file format template strings. (default=None)
    fake_daily_files_from_monthly : bool
        Some CDAWeb instrument data files are stored by month, interfering
        with pysat's functionality of loading by day. This flag, when true,
        appends daily dates to monthly files internally. These dates are
        used by load routine in this module to provide data by day.
    two_digit_year_break : int
        If filenames only store two digits for the year, then
        '1900' will be added for years >= two_digit_year_break
        and '2000' will be added for years < two_digit_year_break.

    Returns
    --------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    Examples
    --------
    ::

        fname = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
        supported_tags = {'dc_b': fname}
        list_files = functools.partial(nasa_cdaweb.list_files,
                                       supported_tags=supported_tags)

        fname = 'cnofs_cindi_ivm_500ms_{year:4d}{month:02d}{day:02d}_v01.cdf'
        supported_tags = {'': fname}
        list_files = functools.partial(mm_gen.list_files,
                                       supported_tags=supported_tags)

    """

    if data_path is not None:
        if format_str is None:
            try:
                format_str = supported_tags[sat_id][tag]
            except KeyError as estr:
                raise ValueError(' '.join(('Unknown sat_id or tag:',
                                           str(estr))))
        out = pysat.Files.from_os(data_path=data_path,
                                  format_str=format_str)

        if (not out.empty) and fake_daily_files_from_monthly:
            out.loc[out.index[-1] + pds.DateOffset(months=1)
                    - pds.DateOffset(days=1)] = out.iloc[-1]
            out = out.asfreq('D', 'pad')
            out = out + '_' + out.index.strftime('%Y-%m-%d')
            return out

        return out
    else:
        estr = ''.join(('A directory must be passed to the loading routine ',
                        'for <Instrument Code>'))
        raise ValueError(estr)


def convert_timestamp_to_datetime(inst, sec_mult=1.0):
    """Use datetime instead of timestamp for Epoch

    Parameters
    ----------
    inst : pysat.Instrument
        associated pysat.Instrument object
    sec_mult : float
        Multiplier needed to convert epoch time to seconds (default=1.0)

    """

    inst.data['Epoch'] = \
        pds.to_datetime([dt.datetime.utcfromtimestamp(x * sec_mult)
                         for x in inst.data['Epoch']])
    return


def remove_leading_text(inst, target=None):
    """Removes leading text on variable names
    Parameters
    ----------
    inst : pysat.Instrument
        associated pysat.Instrument object
    target : str or list of strings
        Leading string to remove. If none supplied, returns unmodified
    Returns
    -------
    None
        Modifies Instrument object in place
    """

    if target is None:
        return
    elif isinstance(target, str):
        target = [target]
    elif (not isinstance(target, list)) or (not isinstance(target[0], str)):
        raise ValueError('target must be a string or list of strings')

    for prepend_str in target:

        if isinstance(inst.data, pds.DataFrame):
            inst.data.rename(columns=lambda x: x.split(prepend_str)[-1],
                             inplace=True)
        else:
            map = {}
            for key in inst.data.variables.keys():
                map[key] = key.split(prepend_str)[-1]
            inst.data = inst.data.rename(name_dict=map)

        inst.meta.data.rename(index=lambda x: x.split(prepend_str)[-1],
                              inplace=True)
        orig_keys = inst.meta.keys_nD()
        for keynd in orig_keys:
            if keynd.find(prepend_str) >= 0:
                new_key = keynd.split(prepend_str)[-1]
                new_meta = inst.meta.pop(keynd)
                new_meta.data.rename(index=lambda x: x.split(prepend_str)[-1],
                                     inplace=True)
                inst.meta[new_key] = new_meta

    return
