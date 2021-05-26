"""
Creates a constellation with 5 testing instruments

Attributes
----------
instruments : list
    List of pysat.Instrument objects

"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                num_samples=10),
               pysat.Instrument('pysat', 'testing2d', clean_level='clean'),
               pysat.Instrument('pysat', 'testing2d_xarray',
                                clean_level='clean'),
               pysat.Instrument('pysat', 'testing_xarray', clean_level='clean'),
               pysat.Instrument('pysat', 'testmodel', clean_level='clean')]
