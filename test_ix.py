# Test code for pandas ix deprecation tests
# Delete before pull request!

import pysat

date = pysat.datetime(2011,6,29)
ivm = pysat.Instrument(platform='cnofs', name='ivm',clean_level='none')
ivm.load(date=date)

# By name
print('input => Ni')
print(ivm['Ni'])
print('\n')

# By position
print('input => 0, Ni')
print(ivm[0,'Ni'])
print('\n')

# Slicing by row
print('input => 0:10, Ni')
print(ivm[0:10,'Ni'])
print('\n')

# By Date
date = pysat.datetime(2011,6,29,23,59,58)
print('input => date, Ni')
print(ivm[date, 'Ni'])
print('\n')

# Slicing by date, inclusive
a = pysat.datetime(2011,6,29,3,0,0)
b = pysat.datetime(2011,6,29,3,0,20)
print('input => a:b, Ni')
print(ivm[a:b, 'Ni'])
print('\n')

# Slicing by name and row/date
print('input => a:b, zpos:zvel')
print(ivm[a:b, 'zpos':'zvel'])
print('\n')
