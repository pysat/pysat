"""
Creates a constellation with 5 testing instruments
"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean')
               for i in range(5)]
