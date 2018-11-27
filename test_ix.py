# Test code for pandas ix deprecation tests
# Delete before merge!

import pysat

date = pysat.datetime(2011,6,29)
ivm = pysat.Instrument(platform='cnofs', name='ivm',clean_level='none')
ivm.load(date=date)

# By name
print(ivm['Ni'])
# By position
print(ivm[0,'Ni'])
# Slicing by row
print(ivm[0:10,'Ni'])
'''
# By Date
inst[datetime, 'name']
# Slicing by date, inclusive
inst[datetime1:datetime2, 'name']
# Slicing by name and row/date
inst[datetime1:datetime1, 'name1':'name2']
'''
