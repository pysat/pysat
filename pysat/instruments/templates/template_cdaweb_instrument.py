# -*- coding: utf-8 -*-
"""This is a template for a pysat.Instrument support file that
utilizes CDAWeb methods. Copy and modify this file as needed when adding a
new Instrument to pysat.

This is a good area to introduce the instrument, provide background
on the mission, operations, instrumenation, and measurements.

Also a good place to provide contact information. This text will
be included in the pysat API documentation.

Properties
----------
platform
    *List platform string here*
name
    *List name string here*
sat_id
    *List supported sat_ids here*
tag
    *List supported tag strings here*

Note
----
- Optional section, remove if no notes


Warnings
--------
- Optional section, remove if no warnings
- Two blank lines needed afterward for proper formatting


Examples
--------
::

    Example code can go here


Authors
-------
Author name and institution

"""

from __future__ import print_function
from __future__ import absolute_import

import functools
import numpy as np
import sys
import pandas as pds
import pysat

# CDAWeb methods prewritten for pysat
from pysat.instruments.methods import nasa_cdaweb as cdw

# the platform and name strings associated with this instrument
# need to be defined at the top level
# these attributes will be copied over to the Instrument object by pysat
# the strings used here should also be used to name this file
# platform_name.py
platform = ''
name = ''

# dictionary of data 'tags' and corresponding description
tags = {'': 'description 1',  # this is the default
        'tag_string': 'description 2'}

# Let pysat know if there are multiple satellite platforms supported
# by these routines
# define a dictionary keyed by satellite ID, each with a list of
# corresponding tags
# sat_ids = {'a':['L1', 'L0'], 'b':['L1', 'L2'], 'c':['L1', 'L3']}
sat_ids = {'': ['']}

# Define good days to download data for when pysat undergoes testing.
# format is outer dictionary has sat_id as the key
# each sat_id has a dictionary of test dates keyed by tag string
# _test_dates = {'a':{'L0':pysat.datetime(2019,1,1),
#                     'L1':pysat.datetime(2019,1,2)},
#                'b':{'L1':pysat.datetime(2019,3,1),
#                     'L2':pysat.datetime(2019,11,23),}}
_test_dates = {'': {'': pysat.datetime(2019, 1, 1)}}

# Additional information needs to be defined
# to support the CDAWeb list files routine
# We need to define a filename format string for every
# supported combination of sat_id and tag string
# fname1 = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
# fname2 = 'cnofs_vefi_acfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
# supported_tags = {'sat1':{'tag1':fname1},
#                   'sat2':{'tag2':fname2}}
# you can use format keywords year, month, day, hour, min, sec,
# version and revision
# see code docstring for latest
fname = 'cnofs_vefi_bfield_1sec_{year:04d}{month:02d}{day:02d}_v05.cdf'
supported_tags = {'': {'': fname}}
# use the CDAWeb methods list files routine
# the command below presets some of the methods inputs, leaving
# those provided by pysat available when invoked
list_files = functools.partial(cdw.list_files,
                               supported_tags=supported_tags)

#
# support load routine
#
# use the default CDAWeb method
# no other information needs to be supplied here
# pysatCDF is used to load data
load = cdw.load

#
# support download routine
#
# to use the default CDAWeb method
# we need to provide additional information
# directory location on CDAWeb ftp server
# formatting template for filenames on CDAWeb
# formatting template for files saved to the local disk
# a dictionary needs to be created for each sat_id and tag
# combination along with the file format template
# outer dict keyed by sat_id, inner dict keyed by tag
basic_tag = {'dir': '/pub/data/cnofs/vefi/bfield_1sec',
             'remote_fname': '{year:4d}/' + fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)

# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)


# code should be defined below as needed
def default(self):
    """Default customization function.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue).

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    return


# code should be defined below as needed
def clean(inst):
    """Routine to return PLATFORM/NAME data cleaned to the specified level

    Cleaning level is specified in inst.clean_level and pysat
    will accept user input for several strings. The clean_level is
    specified at instantiation of the Instrument object.

    'clean' All parameters should be good, suitable for statistical and
            case studies
    'dusty' All paramers should generally be good though same may
            not be great
    'dirty' There are data areas that have issues, data should be used
            with caution
    'none'  No cleaning applied, routine not called in this case.


    Parameters
    -----------
    inst : pysat.Instrument
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    """

    return
