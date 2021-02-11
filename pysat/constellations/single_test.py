"""
Create a constellation with one testing instrument
"""

import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                update_files=True)]
