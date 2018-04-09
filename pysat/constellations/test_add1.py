import pysat

"""
Creates an instrument used to test the constellation class's addition function.
The result of adding the dummy1 signals from this instrument should always be 0
"""

instruments = [
    #put in test instruments 1 and 2 from the addition testing branch here
    pysat.Instrument('pysat', 'testing', clean_level='clean')        
]
