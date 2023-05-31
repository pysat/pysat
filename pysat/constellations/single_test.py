"""Create a constellation with one testing instrument.

Attributes
----------
instruments : list
    List of pysat.Instrument objects

"""

import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                num_samples=10, update_files=True)]
