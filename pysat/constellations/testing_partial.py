"""Create a constellation where not all instruments have loadable data.

Attributes
----------
instruments : list
    List of pysat.Instrument objects

"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                num_samples=10, use_header=True),
               pysat.Instrument('pysat', 'testing', tag='no_download',
                                clean_level='clean', use_header=True)]
