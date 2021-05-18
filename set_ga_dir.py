import os
import pysat

here = os.path.abspath('.')
pysat.params['data_dirs'] = os.path.join(here, 'pysatData')
