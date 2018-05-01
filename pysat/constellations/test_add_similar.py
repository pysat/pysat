import pysat

"""
Creates an instrument used to test the constellation class's addition function.

"""

instruments = [
    pysat.Instrument('pysat', 'testadd1', clean_level='clean'),
    pysat.Instrument('pysat', 'testadd3', clean_level='clean')
]
