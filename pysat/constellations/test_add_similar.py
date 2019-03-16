import pysat

"""
Creates an instrument used to test the constellation class's addition function.

"""

instruments = [pysat.Instrument('pysat', 'testadd',
                                clean_level='clean'),
               pysat.Instrument('pysat', 'testadd', tag='plus10',
                                clean_level='clean')]
