import pysat

"""
Creates an instrument used to test the constellation class's addition function.

"""

instruments = [pysat.Instrument('pysat', 'testadd', tag='A',
                                clean_level='clean'),
               pysat.Instrument('pysat', 'testadd', tag='C',
                                clean_level='clean')]
