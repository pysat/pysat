import pysat

"""
Creates a constellationfor testing difference with two small test instruments
"""

inst1 = pysat.Instrument('pysat', 'testing', clean_level='clean')
inst2 = pysat.Instrument('pysat', 'testing', clean_level='clean')
instruments = [inst1, inst2]
