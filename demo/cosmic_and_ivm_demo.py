import pysat
import pandas as pds
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt

# dates for demo
ssnDays = 67
startDate = pds.datetime(2009,12,21) - pds.DateOffset(days=ssnDays)
stopDate = pds.datetime(2009,12,21) + pds.DateOffset(days=ssnDays)

# define functions to customize data for application
def geo2mag(incoord):
    """geographic coordinate to magnetic coordinate (coarse):

    Parameters
    ----------
    incoord : numpy.array of shape (2,*)
        array([[glat0,glat1,glat2,...],[glon0,glon1,glon2,...]), 
        where glat, glon are geographic latitude and longitude
        (or if you have only one point it is [[glat,glon]]).

    Warnings
    --------
    Calculation of geomagnetic coordinates is approximate.
    Coordinates are for a geomagnetic dipole, not the full field.
    Location of geomagnetic dipole set for 2010.
    
    Returns
    -------    
    array([mlat0,mlat1,...],[mlon0,mlon1,...]])
    
    Note
    ----
    Routine is generally verified as coarsely correct using 2010 values from
    http://wdc.kugi.kyoto-u.ac.jp/igrf/gggm/index.html.
    
    Examples
    --------
    mag =  geo2mag(np.array([[80.08,287.789]]).T).T
    print mag  
    print 'We should get [90,0]'

    mag =  geo2mag(np.array([[90,0]]).T).T
    print mag  
    print 'We should get something close to [80.02, 180]'


    # kyoto, japan
    mag =  geo2mag(np.array([[35.,135.45]]).T).T
    print mag  
    print 'We should get something close to [25.87, -154.94]'    
    
    """

    from numpy import pi, cos, sin, arctan2, sqrt, dot

    # SOME 'constants' for location of northern mag pole
    lat = 80.08#79.3
    lon = -72.211+360.#287.789 # or 71.41W
    r = 1.0

    # convert first to radians
    lon, lat = [x*pi/180 for x in lon, lat]

    glat = incoord[0] * pi / 180.0
    glon = incoord[1] * pi / 180.0
    galt = glat * 0. + r

    coord = np.vstack([glat,glon,galt])

    # convert to rectangular coordinates
    x = coord[2]*cos(coord[0])*cos(coord[1])
    y = coord[2]*cos(coord[0])*sin(coord[1])
    z = coord[2]*sin(coord[0])
    xyz = np.vstack((x,y,z))

    # computer 1st rotation matrix:
    geo2maglon = np.zeros((3,3), dtype='float64')
    geo2maglon[0,0] = cos(lon)
    geo2maglon[0,1] = sin(lon)
    geo2maglon[1,0] = -sin(lon)
    geo2maglon[1,1] = cos(lon)
    geo2maglon[2,2] = 1.
    out = dot(geo2maglon , xyz)

    tomaglat = np.zeros((3,3), dtype='float64')
    tomaglat[0,0] = cos(.5*pi-lat)
    tomaglat[0,2] = -sin(.5*pi-lat)
    tomaglat[2,0] = sin(.5*pi-lat)
    tomaglat[2,2] = cos(.5*pi-lat)
    tomaglat[1,1] = 1.
    out = dot(tomaglat , out)

    mlat = arctan2(out[2],
            sqrt(out[0]*out[0] + out[1]*out[1]))
    mlat = mlat * 180 / pi
    mlon = arctan2(out[1], out[0])
    mlon = mlon * 180 / pi

    outcoord = np.vstack((mlat, mlon))
    return outcoord

def addApexLong(inst, *arg, **kwarg):
    magCoords = geo2mag.geo2mag(np.array([inst.data.edmaxlat, inst.data.edmaxlon]))
    idx,= np.where(magCoords[1,:]< 0)
    magCoords[1,idx] += 360.
    return( ['mlat','apex_long'], [magCoords[0,:], magCoords[1,:]] )

def restrictMLAT(inst, maxMLAT = None):
    inst.data = inst.data[np.abs(inst.data.mlat) < maxMLAT]
    return 

def filterMLAT(inst, mlatRange=None):
    if mlatRange is not None:
        inst.data = inst.data[(np.abs(inst['mlat']) >= mlatRange[0]) & 
                                (np.abs(inst['mlat']) <= mlatRange[1])]
    return

def addlogNm(inst, *arg, **kwarg):
    lognm = np.log10(inst['edmax'])
    lognm.name = 'lognm'
    return lognm
    
def addTopsideScaleHeight(cosmic):
    from scipy.stats import mode
    
    output = cosmic['edmaxlon'].copy()
    output.name = 'thf2'
    
    for i,profile in enumerate(cosmic['profiles']):
        profile = profile[(profile['ELEC_dens'] >= (1./np.e)*cosmic['edmax'].iloc[i]) & (profile.index >= cosmic['edmaxalt'].iloc[i]) ]
        # want the first altitude where density drops below NmF2/e
        # first, resample such that we know all altitudes in between samples are there
        if len(profile) > 10:
            i1 = profile.index[1:]
            i2 = profile.index[0:-1]
            modeDiff = mode(i1.values - i2.values)[0][0]
            profile = profile.reindex(np.arange(profile.index[0],profile.index[-1]+modeDiff,modeDiff))
            # ensure there are no gaps, if so, remove all data above gap
            idx, = np.where(profile['ELEC_dens'].isnull())
            if len(idx) > 0:
                profile = profile.iloc[0:idx[0]]
        
        if len(profile) > 10:
            # make sure density at highest altitude is near Nm/e
            if( profile['ELEC_dens'].iloc[-1]/profile['ELEC_dens'].iloc[0] < .4):
                altDiff = profile.index.values[-1] - profile.index.values[0]
                if altDiff >= 500:
                    altDiff = np.nan
                output[i] = altDiff
            else:
                output[i] = np.nan
        else:
            output[i] = np.nan
        
    return output

# instantiate IVM Object
ivm = pysat.Instrument(platform='cnofs', name='ivm', tag='', clean_level='clean')
# restrict meausurements to those near geomagnetic equator
ivm.custom.add(restrictMLAT, 'modify', maxMLAT=25.)
# perform seasonal average
ivm.bounds = (startDate, stopDate)
ivmResults = pysat.ssnl.avg.median2D(ivm, [0,360,24], 'alon',
                  [0,24,24], 'mlt', ['ionVelmeridional'])

# create COSMIC instrument object
cosmic = pysat.Instrument(platform='cosmic2013', name='gps',tag='ionprf',
             clean_level='clean', altitude_bin=3)
# apply custom functions to all data that is loaded through cosmic
cosmic.custom.add(addApexLong, 'add')
# select locations near the magnetic equator
cosmic.custom.add(filterMLAT, 'modify', mlatRange=(0.,10.) )
# take the log of NmF2 and add to the dataframe
cosmic.custom.add(addlogNm, 'add')
# calculates the height above hmF2 to reach Ne < NmF2/e
cosmic.custom.add(addTopsideScaleHeight, 'add')

# do an average of multiple COSMIC data products from startDate through stopDate
# a mixture of 1D and 2D data is averaged
cosmic.bounds = (startDate, stopDate)
cosmicResults = pysat.ssnl.avg.median2D(cosmic, [0,360,24], 'apex_long',
       [0,24,24],'edmaxlct', ['profiles', 'edmaxalt', 'lognm', 'thf2'])

# the work is done, plot the results

#make IVM and COSMIC plots
f, axarr = plt.subplots(4, sharex=True, sharey=True, figsize=(8.5,11))
cax = []
#meridional ion drift average
merDrifts = ivmResults['ionVelmeridional']['median']
x_arr = ivmResults['ionVelmeridional']['bin_x']
y_arr = ivmResults['ionVelmeridional']['bin_y']


#mask out NaN values
masked = np.ma.array(merDrifts, mask=np.isnan(merDrifts))
#do plot, NaN values are white
cax.append(axarr[0].pcolor(x_arr, y_arr, masked, vmax = 30., vmin = -30., edgecolors='none') )
axarr[0].set_ylim(0,24)
axarr[0].set_yticks([0,6,12,18,24])
axarr[0].set_xlim(0,360)
axarr[0].set_xticks(np.arange(0,420,60))
axarr[0].set_ylabel('Magnetic Local Time')
axarr[0].set_title('IVM Meridional Ion Drifts')             
cbar0 = f.colorbar(cax[0], ax=axarr[0])
cbar0.set_label('Ion Drift (m/s)')

maxDens = cosmicResults['lognm']['median']
cx_arr = cosmicResults['lognm']['bin_x']
cy_arr = cosmicResults['lognm']['bin_y']

# mask out NaN values
masked = np.ma.array(maxDens, mask=np.isnan(maxDens))
# do plot, NaN values are white
cax.append( axarr[1].pcolor(cx_arr, cy_arr, masked, vmax = 6.1, vmin = 4.8, edgecolors='none')  )
axarr[1].set_title('COSMIC Log Density Maximum') 
axarr[1].set_ylabel('Solar Local Time')
cbar1 = f.colorbar(cax[1], ax = axarr[1])         
cbar1.set_label('Log Density')

maxAlt = cosmicResults['edmaxalt']['median']
# mask out NaN values
masked = np.ma.array(maxAlt, mask=np.isnan(maxAlt))
# do plot, NaN values are white
cax.append( axarr[2].pcolor(cx_arr, cy_arr, masked, vmax =375., vmin = 200., edgecolors='none') )       
axarr[2].set_title('COSMIC Altitude Density Maximum')  
axarr[2].set_ylabel('Solar Local Time')           
cbar = f.colorbar(cax[2], ax = axarr[2])
cbar.set_label('Altitude (km)')


maxTh = cosmicResults['thf2']['median']
# mask out NaN values
masked = np.ma.array(maxTh, mask=np.isnan(maxTh))
# do plot, NaN values are white
cax.append( axarr[3].pcolor(cx_arr, cy_arr, masked, vmax =225., vmin = 75., edgecolors='none') )       
axarr[3].set_title('COSMIC Topside Scale Height')      
axarr[3].set_ylabel('Solar Local Time')       
cbar = f.colorbar(cax[3], ax = axarr[3])
cbar.set_label('Scale Height (km)')
axarr[3].set_xlabel('Apex Longitude')
f.tight_layout()
f.savefig('1D_params.png')


# make COSMIC profile plots
# 6 pages of plots, 4 plots per page
for k in np.arange(6):
    f, axarr = plt.subplots(4, sharex=True, figsize=(8.5,11))
    # iterate over a group of four sectors at a time (4 plots per page)
    for (j,sector) in enumerate(np.transpose(cosmicResults['profiles']['median'])[k*4:(k+1)*4]):
        # iterate over all local times within longitude sector
        for (i,ltview) in enumerate(sector):
            if ltview is not None:
                # plot a given longitude/local time profile
                temp = pds.DataFrame(ltview['ELEC_dens'])
                # produce a grid covering plot region ( y values determined by profile)
                xx, yy = np.meshgrid(np.array([i,i+1]), temp.index.values) 
                filtered = ma.array(np.log10(temp.values), mask = pds.isnull(temp))
                graph = axarr[j].pcolormesh(xx,yy,filtered, vmin=3., vmax=6.5)
        cbar = f.colorbar(graph, ax=axarr[j])
        cbar.set_label('Log Density')
        axarr[j].set_xlim(0,24)
        axarr[j].set_ylim(50.,700.)
        axarr[j].set_yticks([50., 200., 350., 500., 650.])
        axarr[j].set_ylabel('Altitude (km)')
        axarr[j].set_title('Apex Longitudes %i-%i' % (4*k*15+j*15, 4*k*15+(j+1)*15) )
    
    axarr[-1].set_xticks([0.,6.,12.,18.,24.])
    axarr[-1].set_xlabel('Solar Local Time of Profile Maximum Density')
    f.tight_layout()
    f.savefig('cosmic_part%i' % (k))  