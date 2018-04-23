import pysat

"""
Creates a constellationfor testing difference with two  test instruments
"""

inst1 = pysat.Instrument('pysat', 'testsmall', clean_level='clean')
inst2 = pysat.Instrument('pysat', 'testsmall2', clean_level='clean')
instruments = [inst1, inst2]
