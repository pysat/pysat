"""
Creates a constellation for testing difference with two small identical
test instruments
"""
import pysat

inst1 = pysat.Instrument('pysat', 'testing', clean_level='clean',
                         num_samples=6000)
inst2 = pysat.Instrument('pysat', 'testing', clean_level='clean',
                         num_samples=6000)
instruments = [inst1, inst2]
