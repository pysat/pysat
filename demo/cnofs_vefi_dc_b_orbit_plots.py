import os
import pysat
import matplotlib.pyplot as plt

# set the directory to save plots to
results_dir = ''

vefi = pysat.Instrument('cnofs_vefi', 'dc_b', None, orbit_index='longitude',
                orbit_type='longitude')

for orbit_count, vefi in enumerate(vefi.orbits):
    vefi.data = vefi.data.resample('1S',  fill_method='ffill', limit=1, label='left' )
    f, ax = plt.subplots(7, sharex=True, figsize=(8.5,11))
    
    ax[0].plot(vefi['longitude'], vefi['B_flag'])
    ax[0].set_title( vefi.data.index[0].ctime() +' - ' +  vefi.data.index[-1].ctime() )
    ax[0].set_ylabel('Interp. Flag')
    ax[0].set_ylim((0,2))
    
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
    ax[6].set_xticks([0,60,120,180,240,300,360])
    ax[6].set_xlim((0,360))   
    f.tight_layout()
    plt.savefig(os.path.join(results_dir,'orbit_%05i.png' % orbit_count ) )
    plt.close()
    
	
    
