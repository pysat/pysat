# -*- coding: utf-8 -*-
"""Provides generalized routines for integrating instruments into pysat.
"""

from __future__ import absolute_import, division, print_function

import pandas as pds

import logging
logger = logging.getLogger(__name__)


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

    Returns
    -------
    None
        Modifies Instrument object in place


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
