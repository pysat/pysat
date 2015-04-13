# -*- coding: utf-8 -*-
"""
Created on Fri Aug 10 00:57:36 2012

@author: rstoneba
"""

import os
# make sure a pysat directory exists
if not os.path.isdir(os.path.join(os.getenv('HOME'), '.pysat')):
    # create directory
    print ''.join(('Creating .pysat directory. Run pysat.utils.set_data_dir to set the path',
                   'to top-level directory containing science data.'))
    os.mkdir(os.path.join(os.getenv('HOME'), '.pysat'))
    with open(os.path.join(os.getenv('HOME'), '.pysat', 'data_path.txt'),'w') as f:
        f.write('')
else:
    # load up stored data path
    with open(os.path.join(os.getenv('HOME'), '.pysat', 'data_path.txt'),'r') as f:
        data_dir = f.readline()
    #else:
    #    print 'tried to open file'
del f

from . import instruments
from . import utils
from .instrument import Instrument

from .meta import Meta
from .files import Files


__all__ = ['coords','ssnl', 'instruments', 'wvlt', 'utils','meta','files','paths']


