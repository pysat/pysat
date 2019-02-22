'''
Demonstrates iterating over an instrument data set by orbit and determining
the occurrent probability of an event occurring.
'''

import os
import pysat
import matplotlib.pyplot as plt
import numpy as np

# set the directory to save plots to
results_dir = ''

# select vefi dc magnetometer data, use longitude to determine where
# there are changes in the orbit (local time info not in file)
orbit_info = {'index': 'longitude', 'kind': 'longitude'}
vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b',
                        clean_level=None, orbit_info=orbit_info)


# define function to remove flagged values
def filter_vefi(inst):
    idx, = np.where(vefi['B_flag'] == 0)
    vefi.data = vefi.data.iloc[idx]
    return


vefi.custom.add(filter_vefi, 'modify')
# set limits on dates analysis will cover, inclusive
start = pysat.datetime(2010, 5, 9)
stop = pysat.datetime(2010, 5, 15)

# if there is no vefi dc magnetometer data on your system, then run command
# below where start and stop are pandas datetimes (from above)
# pysat will automatically register the addition of this data at the end of
# download
vefi.download(start, stop)

# leave bounds unassigned to cover the whole dataset (comment out lines below)
vefi.bounds = (start, stop)

# perform occurrence probability calculation
# any data added by custom functions is available within routine below
ans = pysat.ssnl.occur_prob.by_orbit2D(vefi, [0, 360, 144], 'longitude',
                                       [-13, 13, 104], 'latitude', ['dB_mer'],
                                       [0.], returnBins=True)

# a dict indexed by data_label is returned
# in this case, only one, we'll pull it out
ans = ans['dB_mer']
# plot occurrence probability
f, axarr = plt.subplots(2, 1, sharex=True, sharey=True)
masked = np.ma.array(ans['prob'], mask=np.isnan(ans['prob']))
im = axarr[0].pcolor(ans['bin_x'], ans['bin_y'], masked)
axarr[0].set_title('Occurrence Probability Delta-B Meridional > 0')
axarr[0].set_ylabel('Latitude')
axarr[0].set_yticks((-13, -10, -5, 0, 5, 10, 13))
axarr[0].set_ylim((ans['bin_y'][0], ans['bin_y'][-1]))
plt.colorbar(im, ax=axarr[0], label='Occurrence Probability')

im = axarr[1].pcolor(ans['bin_x'], ans['bin_y'], ans['count'])
axarr[1].set_title('Number of Orbits in Bin')
axarr[1].set_xlabel('Longitude')
axarr[1].set_xticks((0, 60, 120, 180, 240, 300, 360))
axarr[1].set_xlim((ans['bin_x'][0], ans['bin_x'][-1]))
axarr[1].set_ylabel('Latitude')
plt.colorbar(im, ax=axarr[1], label='Counts')

f.tight_layout()
plt.savefig(os.path.join(results_dir, 'ssnl_occurrence_by_orbit_demo'))
plt.close()
