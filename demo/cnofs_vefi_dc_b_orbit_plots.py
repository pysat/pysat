"""
Demonstrates iterating over an instrument data set by orbit and plotting the
results.
"""

import datetime as dt
import os
import matplotlib.pyplot as plt
import pysat

# set the directory to save plots to
results_dir = ''

# select vefi dc magnetometer data, use longitude to determine where
# there are changes in the orbit (local time info not in file)
orbit_info = {'index': 'longitude', 'kind': 'longitude'}
vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b',
                        clean_level=None, orbit_info=orbit_info)

# set limits on dates analysis will cover, inclusive
start = dt.datetime(2010, 5, 9)
stop = dt.datetime(2010, 5, 12)

# if there is no vefi dc magnetometer data on your system, then run command
# below where start and stop are pandas datetimes (from above)
# pysat will automatically register the addition of this data at the end of
# download
vefi.download(start, stop)

# leave bounds unassigned to cover the whole dataset (comment out lines below)
vefi.bounds = (start, stop)

for orbit_count, vefi in enumerate(vefi.orbits):
    # for each loop pysat puts a copy of the next available orbit into
    # vefi.data
    # changing .data at this level does not alter other orbits
    # reloading the same orbit will erase any changes made

    # satellite data can have time gaps, which leads to plots
    # with erroneous lines connecting measurements on both sides of the gap
    # command below fills in any data gaps using a 1-second cadence with NaNs
    # see pandas documentation for more info
    vefi.data = vefi.data.resample('1S', fill_method='ffill', limit=1,
                                   label='left')

    f, ax = plt.subplots(7, sharex=True, figsize=(8.5, 11))

    ax[0].plot(vefi['longitude'], vefi['B_flag'])
    ax[0].set_title(' - '.join((vefi.data.index[0].ctime(),
                                vefi.data.index[-1].ctime())))
    ax[0].set_ylabel('Interp. Flag')
    ax[0].set_ylim((0, 2))

    ax[1].plot(vefi['longitude'], vefi['B_north'])
    ax[1].set_title(vefi.meta['B_north'].long_name)
    ax[1].set_ylabel(vefi.meta['B_north'].units)

    ax[2].plot(vefi['longitude'], vefi['B_up'])
    ax[2].set_title(vefi.meta['B_up'].long_name)
    ax[2].set_ylabel(vefi.meta['B_up'].units)

    ax[3].plot(vefi['longitude'], vefi['B_west'])
    ax[3].set_title(vefi.meta['B_west'].long_name)
    ax[3].set_ylabel(vefi.meta['B_west'].units)

    ax[4].plot(vefi['longitude'], vefi['dB_mer'])
    ax[4].set_title(vefi.meta['dB_mer'].long_name)
    ax[4].set_ylabel(vefi.meta['dB_mer'].units)

    ax[5].plot(vefi['longitude'], vefi['dB_par'])
    ax[5].set_title(vefi.meta['dB_par'].long_name)
    ax[5].set_ylabel(vefi.meta['dB_par'].units)

    ax[6].plot(vefi['longitude'], vefi['dB_zon'])
    ax[6].set_title(vefi.meta['dB_zon'].long_name)
    ax[6].set_ylabel(vefi.meta['dB_zon'].units)
    ax[6].set_xlabel(vefi.meta['longitude'].long_name)
    ax[6].set_xticks([0, 60, 120, 180, 240, 300, 360])
    ax[6].set_xlim((0, 360))

    f.tight_layout()
    plt.savefig(os.path.join(results_dir,
                             'orbit_{num:05}.png').format(num=orbit_count))
    plt.close()
