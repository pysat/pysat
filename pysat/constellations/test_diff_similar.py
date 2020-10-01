import pysat

"""
Creates a constellation for testing difference with two small similar test
instruments
"""

inst1 = pysat.Instrument('pysat', 'testing',
                         clean_level='clean',
                         tag='mlt_offset',
                         inst_id='6000')
inst2 = pysat.Instrument('pysat', 'testing',
                         clean_level='clean',
                         inst_id='6000')
instruments = [inst1, inst2]
