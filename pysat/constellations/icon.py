"""
Creates a constellation from NASA ICON instrumentation

.. deprecated:: 2.3.0
  This routine has been deprecated in pysat 3.0.0, and will be accessible
  in `pysatNASA.constellations.icon`

"""

import warnings

import pysat


warnings.warn(" ".join(["This constellation",
                        "has been removed from the pysat-managed",
                        "Instruments in pysat 3.0.0, and now resides in",
                        "pysatNASA:",
                        "https://github.com/pysat/pysatNASA"]),
              DeprecationWarning, stacklevel=2)

ivm = pysat.Instrument('icon', 'ivm', sat_id='a', tag='level_2',
                       clean_level='clean', update_files=True)
euv = pysat.Instrument('icon', 'euv', sat_id='', tag='level_2',
                       clean_level='clean', update_files=True)
fuv = pysat.Instrument('icon', 'fuv', sat_id='', tag='level_2',
                       clean_level='clean', update_files=True)
mighti_green = pysat.Instrument('icon', 'mighti', sat_id='green',
                                tag='level_2', clean_level='clean',
                                update_files=True)
mighti_red = pysat.Instrument('icon', 'mighti', sat_id='red', tag='level_2',
                              clean_level='clean', update_files=True)

instruments = [ivm, euv, fuv, mighti_green, mighti_red]
