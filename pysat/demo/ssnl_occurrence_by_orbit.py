'''
Demonstrates iterating over an instrument data set by orbit and determining
the occurrent probability of an event occurring.
'''

import os
import pysat
import matplotlib.pyplot as plt
import pandas as pds
import numpy as np

# set the directory to save plots to
results_dir = ''

# select vefi dc magnetometer data, use longitude to determine where
# there are changes in the orbit (local time info not in file)
vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b', clean_level=None, 
                        orbit_index='longitude', orbit_type='longitude')

# set limits on dates analysis will cover, inclusive
start = pds.datetime(2010,5,9)
stop = pds.datetime(2010,5,12)

# if there is no vefi dc magnetometer data on your system, then run command below
# where start and stop are pandas datetimes (from above)
# pysat will automatically register the addition of this data at the end of download
vefi.download(start, stop)

# leave bounds unassigned to cover the whole dataset (comment out lines below)
vefi.bounds = (start,stop)

# perform occurrence probability calculation
# any data added by custom functions is available within routine below
ans = pysat.ssnl.occur_prob.by_orbit2D(vefi, [0,360,144], 'longitude', 
                [-13,13,104], 'latitude', ['dB_mer'], [0.], returnBins=True)

# plot occurrence probability
f, axarr = plt.subplots(2,1, sharex=True, sharey=True)
masked = np.ma.array(ans['dB_mer']['prob'], mask=np.isnan(ans['dB_mer']['prob']))                                   
im=axarr[0].pcolor(ans['dB_mer']['binx'], ans['dB_mer']['biny'], masked)
axarr[0].set_title('Occurrence Probability Delta-B Meridional > 0')
axarr[0].set_ylabel('Latitude')
axarr[0].set_yticks((-13,-10,-5,0,5,10,13))
axarr[0].set_ylim((ans['dB_mer']['biny'][0],ans['dB_mer']['biny'][-1]))
plt.colorbar(im,ax=axarr[0], label='Occurrence Probability')

im=axarr[1].pcolor(ans['dB_mer']['binx'], ans['dB_mer']['biny'],ans['dB_mer']['count'])
axarr[1].set_xlabel('Longitude')  
axarr[1].set_xticks((0,60,120,180,240,300,360))
axarr[1].set_xlim((ans['dB_mer']['binx'][0],ans['dB_mer']['binx'][-1]))
axarr[1].set_ylabel('Latitude')
axarr[1].set_title('Number of Orbits in Bin')

plt.colorbar(im,ax=axarr[1], label='Counts')
f.tight_layout()                                 
plt.show()
plt.savefig(os.path.join(results_dir,'ssnl_occurrence_by_orbit_demo') )
