"""
Creates a constellation from NASA DE2 instrumentation

.. deprecated:: 2.3.0
  This routine has been deprecated in pysat 3.0.0, and will be accessible
  in `pysatNASA.constellations.de2`

"""

import warnings

import pysat


warnings.warn(" ".join(["This constellation",
                        "has been removed from the pysat-managed",
                        "Instruments in pysat 3.0.0, and now resides in",
                        "pysatNASA:",
                        "https://github.com/pysat/pysatNASA"]),
              DeprecationWarning, stacklevel=2)

lang = pysat.Instrument(platform='de2', name='lang')
nacs = pysat.Instrument(platform='de2', name='nacs')
rpa = pysat.Instrument(platform='de2', name='rpa')
wats = pysat.Instrument(platform='de2', name='wats')

instruments = [lang, nacs, rpa, wats]
