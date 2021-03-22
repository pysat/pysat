"""
Creates a constellation from NASA ICON instrumentation

.. deprecated:: 2.3.0
  This routine has been deprecated in pysat 3.0.0, and will be accessible
  in `pysatNASA.constellations.icon`

"""

import pysat

ivm = pysat.Instrument('icon', 'ivm', sat_id='a', tag='',
                       clean_level='clean', update_files=True)
euv = pysat.Instrument('icon', 'euv', sat_id='', tag='',
                       clean_level='clean', update_files=True)

instruments = [ivm, euv]
