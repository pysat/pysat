"""
Creates a constellation with 5 testing instruments

Attributes
----------
instruments : list
    List of pysat.Instrument objects

"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean')
               for i in range(5)]
