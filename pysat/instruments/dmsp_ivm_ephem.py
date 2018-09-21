# -*- coding: utf-8 -*-
"""Supports the Defense Meteorological Satellite Program.

Parameters
----------
sat_id : {'f11, f12, f13, f14, f15, f16, f17, f18, f19'}

        
"""

import pandas as pds
import numpy as np
import pysat
import sys

# from spacepy import pycdf
import pysatCDF

def list_files(tag=None, data_path=None, sat_id=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data"""
    if data_path is not None:
        return pysat.Files.from_os(data_path=data_path, \
            format_str='*/*/dmsp-' + sat_id + \
            '_ephemeris_eci-geo-aacgm_{year:04d}{month:02d}{day:02d}_v01a.cdf')
    else:
        raise ValueError ('A directory must be passed to the loading routine' \
                          + ' for DMSP IVM Ephem')
            

def load(fnames, tag=None, sat_id=None):
    if len(fnames) <= 0 :
        return pysat.DataFrame(None), pysat.Meta(None)
    else:
         cdf = pysatCDF.CDF(fnames[0])
        # data = {}
        # meta = pysat.Meta()
        #
        # multi_dim_key = ['SC_ECI', 'SC_ECI_VELOCITY', 'SC_ECI_LABEL']
        # for key in cdf.keys():
        #     if key not in multi_dim_key:
        #         data[key] = cdf[key][...]
        #     try:
        #         meta[key] = {'units':cdf[key].attrs['UNITS'],
        #                     'long_name':cdf[key].attrs['LABLAXIS'],
        #                     'description':cdf[key].attrs['CATDESC']}
        #     except KeyError:
        #         pass
        #
        # epoch = data.pop('Epoch')
        # cdf.close()

    # data = pysat.DataFrame(data, index=epoch)
    data, meta = cdf.to_pysat(flatten_twod=True)
    return data, meta
                                

def clean(dmsp):
    return

def download(date_array, tag, data_path=None, user=None, password=None):
    """
    start and stop should be datetimes
    """
    import os
    import ftplib

    raise ValueError("DMSP Download method doesn't do anything yet.")
    return
    
