# -*- coding: utf-8 -*-
"""
pysat.instruments is a pysat module that provides
the interface for pysat to download, load, manage,
modify and analyze science data.  Each instrument
is contained within a subpackage of this set.
"""

__all__ = ['champ_star', 'cnofs_ivm', 'cnofs_plp', 'cnofs_vefi',
           'cosmic_gps', 'demeter_iap', 'dmsp_ivm',
           'icon_ivm', 'icon_euv', 'icon_fuv', 'icon_mighti',
           'iss_fpmu',  'jro_isr', 'omni_hro', 'pysat_sgp4', 'rocsat1_ivm',
           'sport_ivm', 'superdarn_grdex', 'supermag_magnetometer',
           'sw_dst', 'sw_kp', 'sw_f107', 'timed_saber', 'timed_see',
           'ucar_tiegcm', ]

from . import *
