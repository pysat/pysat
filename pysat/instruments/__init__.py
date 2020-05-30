# -*- coding: utf-8 -*-
"""
pysat.instruments is a pysat module that provides
the interface for pysat to download, load, manage,
modify and analyze science data.  Each instrument
is contained within a subpackage of this set.
"""

__all__ = ['champ_star', 'cnofs_ivm', 'cnofs_plp', 'cnofs_vefi', 'cosmic_gps',
           'de2_lang', 'de2_nacs', 'de2_rpa', 'de2_wats',
           'demeter_iap',
           'icon_ivm', 'icon_euv', 'icon_fuv', 'icon_mighti',
           'iss_fpmu',  'omni_hro', 'rocsat1_ivm',
           'sport_ivm', 'superdarn_grdex', 'supermag_magnetometer',
           'sw_dst', 'sw_kp', 'sw_f107', 'timed_saber', 'timed_see',
           'pysat_testing', 'pysat_testing_xarray', 'pysat_testing2d',
           'pysat_testing2d_xarray', 'pysat_testmodel']

for inst in __all__:
    exec("from pysat.instruments import {x}".format(x=inst))
