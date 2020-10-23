# -*- coding: utf-8 -*-
"""Provides generalized routines for integrating instruments into pysat.
"""

import datetime as dt
import logging
import numpy as np
import pandas as pds

import pysat


logger = logging.getLogger(__name__)


def list_files(tag=None, inst_id=None, data_path=None, format_str=None,
               supported_tags=None, fake_daily_files_from_monthly=False,
               two_digit_year_break=None, delimiter=None):
    """Return a Pandas Series of every file for chosen Instrument data.

    This routine provides a standard interfacefor pysat instrument modules.

    Parameters
    ----------
    tag : string or NoneType
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    inst_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : string or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)
    supported_tags : dict or NoneType
        keys are inst_id, each containing a dict keyed by tag
        where the values file format template strings. (default=None)
    fake_daily_files_from_monthly : bool
        Some instrument data files are stored by month, interfering with daily
        file loading assumed by pysat. If True, this flag appends daily dates
        to monthly files internally. These dates are used by load routine in
        this module to provide data by day. (default=False)
    two_digit_year_break : int or NoneType
        If filenames only store two digits for the year, then '1900' will be
        added for years >= two_digit_year_break and '2000' will be added for
        years < two_digit_year_break. If None, then four-digit years are
        assumed. (default=None)
    delimiter : string or NoneType
        Delimiter string upon which files will be split (e.g., '.'). If None,
        filenames will be parsed presuming a fixed width format. (default=None)

    Returns
    -------
    out : pysat.Files.from_os : pysat._files.Files
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

    # Test the input
    if data_path is None:
        estr = ''.join(('A directory must be passed to the loading routine ',
                        'for <Instrument Code>'))
        raise ValueError(estr)

    if format_str is None:
        try:
            format_str = supported_tags[inst_id][tag]
        except KeyError as kerr:
            raise ValueError(' '.join(('Unknown inst_id or tag:',
                                       str(kerr))))

    # Get the series of files
    out = pysat.Files.from_os(data_path=data_path, format_str=format_str,
                              two_digit_year_break=two_digit_year_break,
                              delimiter=delimiter)

    # If the data is monthly, pad the series
    # TODO: take file frequency as an input to allow e.g., weekly files
    if (not out.empty) and fake_daily_files_from_monthly:
        emonth = out.index[-1]
        out.loc[out.index[-1] + pds.DateOffset(months=1)
                - pds.DateOffset(days=1)] = out.iloc[-1]
        new_out = out.asfreq('D')

        for i, out_month in enumerate(out.index):
            if(out_month.month == emonth.month
               and out_month.year == emonth.year):
                out_month = emonth

            mrange = pds.date_range(start=out_month, periods=2, freq='MS')
            irange = pds.date_range(*mrange.values, freq="D").values[:-1]
            new_out[irange] = out.loc[out_month]

        # Assign the non-NaN files to out and add days to the filenames
        out = new_out.dropna()
        out = out + '_' + out.index.strftime('%Y-%m-%d')

    return out


def convert_timestamp_to_datetime(inst, sec_mult=1.0, epoch_name='Epoch'):
    """Use datetime instead of timestamp for Epoch

    Parameters
    ----------
    inst : pysat.Instrument
        associated pysat.Instrument object
    sec_mult : float
        Multiplier needed to convert epoch time to seconds (default=1.0)
    epoch_name : str
        variable name for instrument index (default='Epoch')

    """

    inst.data[epoch_name] = pds.to_datetime(
        [dt.datetime.utcfromtimestamp(int(np.floor(x * sec_mult)))
         for x in inst.data[epoch_name]])
    return


def remove_leading_text(inst, target=None):
    """Removes leading text on variable names

    Parameters
    ----------
    inst : pysat.Instrument
        associated pysat.Instrument object
    target : str or list of strings
        Leading string to remove. If none supplied, returns unmodified

    """

    if target is None:
        return
    elif isinstance(target, str):
        target = [target]
    elif (not isinstance(target, list)) or (not isinstance(target[0], str)):
        raise ValueError('target must be a string or list of strings')

    for prepend_str in target:

        if isinstance(inst.data, pds.DataFrame):
            inst.data = inst.data.rename(
                columns=lambda x: x.split(prepend_str)[-1])
        else:
            map_keys = {}
            for key in inst.data.variables.keys():
                map_keys[key] = key.split(prepend_str)[-1]
            inst.data = inst.data.rename(name_dict=map_keys)

        inst.meta.data = inst.meta.data.rename(
            index=lambda x: x.split(prepend_str)[-1])
        orig_keys = [kk for kk in inst.meta.keys_nD()]
        for keynd in orig_keys:
            if keynd.find(prepend_str) >= 0:
                new_key = keynd.split(prepend_str)[-1]
                new_meta = inst.meta.pop(keynd)
                new_meta.data = new_meta.data.rename(
                    index=lambda x: x.split(prepend_str)[-1])
                inst.meta[new_key] = new_meta

    return
