# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
import os
# make sure a pysat directory exists
if not os.path.isdir(os.path.join(os.getenv('HOME'), '.pysat')):
    # create directory
    print(''.join(('Creating .pysat directory. Run pysat.utils.set_data_dir to set the path',
                   ' to top-level directory containing science data.')))
    os.mkdir(os.path.join(os.getenv('HOME'), '.pysat'))
    with open(os.path.join(os.getenv('HOME'), '.pysat', 'data_path.txt'),'w') as f:
        f.write('')
        #f.close()
    data_dir=''
else:
    # load up stored data path
    with open(os.path.join(os.getenv('HOME'), '.pysat', 'data_path.txt'),'r') as f:
        data_dir = f.readline()
    if data_dir == '':
        print('Run pysat.utils.set_data_dir to set the path to top-level directory containing science data.')
#del f

from pandas import Panel, DataFrame, Series, datetime
from . import utils
from ._instrument import Instrument
from ._meta import Meta
from ._files import Files
from ._custom import Custom
from ._orbits import Orbits
from . import instruments

from . import ssnl



__all__ = ['ssnl','instruments', 'utils']


