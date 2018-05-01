import pysat

"""
Creates an instrument used to test the constellation class's addition function.
The result of adding the dummy1 signals from this instrument should always be 0
"""

instruments = [
    pysat.Instrument('pysat', 'testadd1', clean_level='clean'),
    pysat.Instrument('pysat', 'testadd2', clean_level='clean')
]
