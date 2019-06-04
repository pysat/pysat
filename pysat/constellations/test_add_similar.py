import pysat

"""
Creates an instrument used to test the constellation class's addition function.

"""

instruments = [pysat.Instrument('pysat', 'testing', tag='ascend',
                                clean_level='clean'),
               pysat.Instrument('pysat', 'testing', tag='plus10',
                                clean_level='clean')]
