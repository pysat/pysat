"""
Creates a constellation from NASA DE2 instrumentation

.. deprecated:: 2.3.0
  This routine has been deprecated in pysat 3.0.0, and will be accessible
  in `pysatNASA.constellations.de2`

"""

import pysat

lang = pysat.Instrument(platform='de2', name='lang')
nacs = pysat.Instrument(platform='de2', name='nacs')
rpa = pysat.Instrument(platform='de2', name='rpa')
wats = pysat.Instrument(platform='de2', name='wats')

instruments = [lang, nacs, rpa, wats]
