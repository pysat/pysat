# -*- coding: utf-8 -*-
"""Provides generalized routines for integrating instruments into pysat."""

import datetime as dt
import numpy as np
import pandas as pds
import warnings

import pysat

logger = pysat.logger


def is_daily_file_cadence(file_cadence):
    """Evaluate file cadence to see if it is daily or greater than daily.

    Parameters
    ----------
    file_cadence : dt.timedelta or pds.DateOffset
        pysat assumes a daily file cadence, but some instrument data file
        contain longer periods of time.  This parameter allows the specification
        of regular file cadences greater than or equal to a day (e.g., weekly,
        monthly, or yearly). (default=dt.timedelta(days=1))

    Returns
    -------
    is_daily : bool
        True if the cadence is daily or less, False if the cadence is greater
        than daily

    """
    is_daily = True

    if hasattr(file_cadence, 'days'):
        if file_cadence.days > 1:
            is_daily = False
    else:
        if not (hasattr(file_cadence, 'microseconds')
                or hasattr(file_cadence, 'seconds')
                or hasattr(file_cadence, 'minutes')
                or hasattr(file_cadence, 'hours')):
            is_daily = False

    return is_daily


def list_files(tag='', inst_id='', data_path='', format_str=None,
               supported_tags=None, file_cadence=dt.timedelta(days=1),
               two_digit_year_break=None, delimiter=None):
    """Return a Pandas Series of every file for chosen Instrument data.

    This routine provides a standard interface for pysat instrument modules.

    Parameters
    ----------
    tag : str
        Tag name used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    inst_id : str
        Instrument ID used to identify particular data set to be loaded.
        This input is nominally provided by pysat itself. (default='')
    data_path : str
        Path to data directory. This input is nominally provided by pysat
        itself. (default='')
    format_str : string or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. See `Files.from_os`
        `format_str` kwarg for more details. (default=None)
    supported_tags : dict or NoneType
        Keys are `inst_id`, each containing a dict keyed by `tag`
        where the values are file format template strings. (default=None)
    file_cadence : dt.timedelta or pds.DateOffset
        pysat assumes a daily file cadence, but some instrument data file
        contain longer periods of time.  This parameter allows the specification
        of regular file cadences greater than or equal to a day (e.g., weekly,
        monthly, or yearly). (default=dt.timedelta(days=1))
    two_digit_year_break : int or NoneType
        If filenames only store two digits for the year, then '1900' will be
        added for years >= two_digit_year_break and '2000' will be added for
        years < two_digit_year_break. If None, then four-digit years are
        assumed. (default=None)
    delimiter : str or NoneType
        Delimiter string upon which files will be split (e.g., '.'). If None,
        filenames will be parsed presuming a fixed width format. (default=None)

    Returns
    -------
    out : pysat.Files.from_os : pysat._files.Files
        A class containing the verified available files

    See Also
    --------
    pysat.Files.from_os

    Note
    ----
    This function is intended to be invoked by pysat and not the end user.

    Examples
    --------
    ::

        from pysat.instruments.methods import general as mm_gen
        fname = 'instrument_{year:04d}{month:02d}{day:02d}_v{version:02}.cdf'
        supported_tags = {'tag_name': fname}
        list_files = functools.partial(mm_gen.list_files,
                                       supported_tags=supported_tags)

    """

    if format_str is None:
        # pyast performs a check against `inst_id` and `tag` before calling
        # `list_files`. However, supported_tags is a non-pysat input.
        try:
            format_str = supported_tags[inst_id][tag]
        except KeyError as kerr:
            raise ValueError(' '.join(('Unknown inst_id or tag:',
                                       str(kerr))))

    # Get the series of files
    out = pysat.Files.from_os(data_path=data_path, format_str=format_str,
                              two_digit_year_break=two_digit_year_break,
                              delimiter=delimiter)

    # If the data is not daily, pad the series.  Both pds.DateOffset and
    # dt.timedelta contain the 'days' attribute, so evaluate using that
    if not out.empty and not is_daily_file_cadence(file_cadence):
        emonth = out.index[-1]
        out.loc[out.index[-1] + file_cadence
                - dt.timedelta(days=1)] = out.iloc[-1]
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


def convert_timestamp_to_datetime(inst, sec_mult=1.0, epoch_name='time'):
    """Use datetime instead of timestamp for Epoch.

    .. deprecated:: 3.0.2
        This routine has been deprecated with the addition of the kwargs
        `epoch_unit` and `epoch_origin` to `pysat.utils.io.load_netcdf4`.
        This routing will be removed in 3.2.0.

    Parameters
    ----------
    inst : pysat.Instrument
        associated pysat.Instrument object
    sec_mult : float
        Multiplier needed to convert epoch time to seconds (default=1.0)
    epoch_name : str
        variable name for instrument index (default='Epoch')

    Note
    ----
    If the variable represented by epoch_name is not a float64, data is passed
    through unchanged.

    """

    warnings.warn(" ".join(["New kwargs added to `pysat.utils.io.load_netCDF4`",
                            "for generalized handling, deprecated",
                            "function will be removed in pysat 3.2.0+"]),
                  DeprecationWarning, stacklevel=2)

    if inst.data[epoch_name].dtype == 'float64':
        inst.data[epoch_name] = pds.to_datetime(
            [dt.datetime.utcfromtimestamp(int(np.floor(epoch_time * sec_mult)))
             for epoch_time in inst.data[epoch_name]])

    return


def remove_leading_text(inst, target=None):
    """Remove leading text on variable names.

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


def filename_creator(value, format_str=None, start_date=None, stop_date=None):
    """Create filenames as needed to support use of generated pysat data sets.

    Parameters
    ----------
    value : slice
        Datetime slice, see _instrument.py,
        fname = self.files[date:(date + inc)]
    format_str : str or NoneType
        File format template string (default=None)
    start_date : datetime.datetime or NoneType
        First date supported (default=None)
    stop_date: datetime.datetime or NoneType
        Last date supported (default=None)

    Returns
    -------
    pandas.Series
        Created filenames from format_str indexed by datetime

    Raises
    ------
    NotImplementedError
        This method is a stub to support development of a potential feature
        slated for a future release.

    """

    estr = ''.join(('This feature has not been implemented yet and is here ',
                    'to support experimentation by the pysat team. If you are ',
                    'here intentionally, please contact the pysat developers ',
                    'at pysat.developers@gmail.com or pysat.slack.com and let ',
                    'us know what you are trying to accomplish so we can ',
                    'evaluate supporting the desired use case.'))
    raise NotImplementedError(estr)

    return


def load_csv_data(fnames, read_csv_kwargs=None):
    """Load CSV data from a list of files into a single DataFrame.

    Parameters
    ----------
    fnames : array-like
        Series, list, or array of filenames
    read_csv_kwargs : dict or NoneType
        Dict of kwargs to apply to `pds.read_csv`. (default=None)

    Returns
    -------
    data : pds.DataFrame
        Data frame with data from all files in the fnames list

    See Also
    --------
    pds.read_csv

    """
    # Ensure the filename input is array-like
    fnames = np.asarray(fnames)
    if fnames.shape == ():
        fnames = np.asarray([fnames])

    # Initialize the optional kwargs
    if read_csv_kwargs is None:
        read_csv_kwargs = {}

    # Create a list of data frames from each file
    fdata = []
    for fname in fnames:
        fdata.append(pds.read_csv(fname, **read_csv_kwargs))

    data = pds.DataFrame() if len(fdata) == 0 else pds.concat(fdata, axis=0)
    return data
