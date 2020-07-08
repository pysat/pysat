# -*- coding: utf-8 -*-
"""Provides generalized routines for integrating instruments into pysat.
"""

from __future__ import absolute_import, division, print_function

import datetime as dt
import logging
import pandas as pds


logger = logging.getLogger(__name__)


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
    target : str
        Leading string to remove. If none supplied,
        ICON project standards are used to identify and remove
        leading text

    """

    if target is not None:
        prepend_str = target

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
            new_key = keynd.split(prepend_str)[-1]
            new_meta = inst.meta.pop(keynd)
            new_meta.data.rename(index=lambda x: x.split(prepend_str)[-1],
                                 inplace=True)
            inst.meta[new_key] = new_meta

    return
