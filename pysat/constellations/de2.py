import pysat
"""
Creates a constellation from NASA ICON instrumentation
"""


lang = pysat.Instrument(platform='de2', name='lang')
nacs = pysat.Instrument(platform='de2', name='nacs')
rpa = pysat.Instrument(platform='de2', name='rpa')
wats = pysat.Instrument(platform='de2', name='wats')

instruments = [lang, nacs, rpa, wats]
