# -*- coding: utf-8 -*-
"""
pysat.instruments.methods is a pysat module that provides
specific functions for instruments and classes of instruments.
Each set of methods is contained within a subpackage of this set.
"""

from pysat.instruments.templates import (madrigal_pandas, netcdf_pandas,
                                         template_instrument,
                                         template_cdaweb_instrument)

__all__ = ['madrigal_pandas', 'netcdf_pandas', 'template_instrument',
           'template_cdaweb_instrument']
