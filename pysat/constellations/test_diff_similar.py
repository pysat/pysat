"""
Creates a constellation for testing difference with two small similar test
instruments
"""
import pysat

inst1 = pysat.Instrument('pysat', 'testing', clean_level='clean',
                         num_samples=6000)  # MLT offset was here, not supported
inst2 = pysat.Instrument('pysat', 'testing', clean_level='clean',
                         num_samples=6000)

instruments = [inst1, inst2]
