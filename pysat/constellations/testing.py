"""Create a constellation with 5 testing instruments.

Attributes
----------
instruments : list
    List of pysat.Instrument objects

Note
----
Each instrument has a different sample size to test the common_index

"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                num_samples=10, use_header=True),
               pysat.Instrument('pysat', 'ndtesting', clean_level='clean',
                                num_samples=16, use_header=True),
               pysat.Instrument('pysat', 'testmodel', clean_level='clean',
                                num_samples=18, use_header=True)]
