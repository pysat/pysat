import pysat
"""
Creates a constellation with 5 testing instruments
"""

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean')
               for i in range(5)]
