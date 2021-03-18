import pysat

"""
Creates a constellation for testing difference with two small identical
test instruments
"""

inst1 = pysat.Instrument('pysat', 'testing',
                         clean_level='clean',
                         num_samples=6000)
inst2 = pysat.Instrument('pysat', 'testing',
                         clean_level='clean',
                         num_samples=6000)
instruments = [inst1, inst2]
