# Test code for pandas ix deprecation tests
# Delete before merge!

import pysat

date = pysat.datetime(2011,6,29)
ivm = pysat.Instrument(platform='cnofs', name='ivm',clean_level='none')
ivm.load(date=date)

print(ivm['Ni',0:10])
