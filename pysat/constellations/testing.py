"""Create a constellation with 5 testing instruments.

Attributes
----------
instruments : list
    List of pysat.Instrument objects

"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                num_samples=10, use_header=True),
               pysat.Instrument('pysat', 'testing2d', clean_level='clean',
                                use_header=True),
               pysat.Instrument('pysat', 'ndtesting', clean_level='clean',
                                use_header=True),
               pysat.Instrument('pysat', 'testing_xarray', clean_level='clean',
                                use_header=True),
               pysat.Instrument('pysat', 'testmodel', clean_level='clean',
                                use_header=True)]
