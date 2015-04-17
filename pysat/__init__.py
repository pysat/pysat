# -*- coding: utf-8 -*-
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
    if data_dir == '':
        print 'Run pysat.utils.set_data_dir to set the path to top-level directory containing science data.'
del f

import instruments
import utils
from _instrument import Instrument
import ssnl

from _meta import Meta
from _files import Files


__all__ = ['ssnl','instruments', 'utils','meta','files']


