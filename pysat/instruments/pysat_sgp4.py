# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""
from __future__ import print_function
from __future__ import absolute_import
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str

import pandas as pds
import numpy as np
import pysat
import pysat.models

# pysat required parameters
platform = 'pysat'
name = 'sgp4'
# dictionary of data 'tags' and corresponding description
tags = {'':'Satellite simulation data set'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2009,1,1)}}



        
def init(self):
    self.custom.add(pysat.models.add_quasi_dipole_coordinates, 'modify')
    self.custom.add(calculate_ecef_velocity, 'modify')
    self.custom.add(sc_look_vectors, 'modify')
    self.custom.add(pysat.models.add_iri_thermal_plasma, 'modify')
    self.custom.add(pysat.models.add_hwm_winds_and_ecef_vectors, 'modify')
                
def load(fnames, tag=None, sat_id=None, obs_long=0., obs_lat=0., obs_alt=0.):
        
    import sgp4
    from sgp4.earth_gravity import wgs72
    from sgp4.io import twoline2rv
    import ephem
    import pysat.coords

    # lines define something
    line1 = ('1 00005U 58002B   00179.78495062  '
            '.00000023  00000-0  28098-4 0  4753')
    line2 = ('2 00005  34.2682 348.7242 1859667 '
            '331.7664  19.3264 10.82419157413667')
            
    line1 = ('1 25544U 98067A   18135.61844383  .00002728  00000-0  48567-4 0  9998')
    line2 = ('2 25544  51.6402 181.0633 0004018  88.8954  22.2246 15.54059185113452')


    satellite = twoline2rv(line1, line2, wgs72)

    # grab date from filename
    parts = fnames[0].split('/')
    yr = int('20'+parts[-1][0:2])
    month = int(parts[-3])
    day = int(parts[-2])
    date = pysat.datetime(yr, month, day)
    
    # create timing at 1 Hz
    times = pds.date_range(start=date, end=date+pds.DateOffset(seconds=86399), freq='1S')
    
    # create list to hold satellite position, velocity
    position = []
    velocity = []
    for time in times:
        # orbit propagator
        pos, vel = satellite.propagate(time.year, time.month, time.day, 
                                       time.hour, time.minute, time.second)
        # print (pos)
        position.extend(pos)
        velocity.extend(vel)
        

    data = pysat.DataFrame({'position_eci_x': position[::3], 
                            'position_eci_y': position[1::3], 
                            'position_eci_z': position[2::3],
                            'velocity_eci_x': velocity[::3], 
                            'velocity_eci_y': velocity[1::3], 
                            'velocity_eci_z': velocity[2::3]}, 
                            index=times)
    data.index.name = 'Epoch'
    
    # add position and velocity in ECEF
    # add call for GEI/ECEF translation here
    # instead, since available, I'll use an orbit predictor from another
    # package that outputs in ECEF
    # it also supports ground station calculations
    
    site = ephem.Observer()
    site.lon = str(obs_long)   # +E -104.77 here
    site.lat = str(obs_lat)   # +N 38.95   here
    site.elevation = obs_alt # meters    0 here
    #epoch = time.time()
    sat = ephem.readtle('pysat' , line1, line2)
    sat_az_angle = [] # azimuth of satellite from ground station
    sat_el_angle = []
    sat_slant_range = []
    ecef_x = []
    ecef_y = []
    ecef_z = []
    sublat = []
    sublong = []
    satelev = []
    for time in times:
        site.date = time
        sat.compute(site)
    
        sat_az_angle.append(ephem.degrees(sat.az))
        sat_el_angle.append(ephem.degrees(sat.alt))
        
        # satellite location 
        # total distance away
        sat_slant_range.append(sat.range)
        # sub latitude point
        sublat.append(np.degrees(sat.sublat))
        # sublongitude point
        sublong.append(np.degrees(sat.sublong))
        # elevation of sat in m, stored as km
        satelev.append(sat.elevation/1000.)
        # get ECEF position of satellite
        x, y, z = pysat.coords.geodetic_to_ecef(sublat[-1], sublong[-1], satelev[-1])
        
        # x, y, z = aer2ecef(sat_az_angle[-1], sat_el_angle[-1], sat_slant_range[-1],
        #                     obs_lat, obs_long, obs_alt)
        ecef_x.append(x)
        ecef_y.append(y)
        ecef_z.append(z)
        
    data['glong'] = sublong
    data['glat'] = sublat
    data['alt'] = satelev
    data['position_ecef_x'] = ecef_x
    data['position_ecef_y'] = ecef_y
    data['position_ecef_z'] = ecef_z
    data['obs_sat_az_angle'] = sat_az_angle
    data['obs_sat_el_angle'] = sat_el_angle
    data['obs_sat_slant_range'] = sat_slant_range
    
    return data, meta.copy()


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2000,1,1), pysat.datetime(2018,12,31)) 
    names = [ data_path+date.strftime('%D')+'.nofile' for date in index]
    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    pass


def sc_look_vectors(inst):
    
    # add look direction of S/C vectors

    # ram pointing is along velocity vector
    mag = np.sqrt(inst['velocity_ecef_x']**2 + inst['velocity_ecef_y']**2 + 
                    inst['velocity_ecef_z']**2)
    inst['sc_xhat_ecef_x'] = inst['velocity_ecef_x']/mag
    inst['sc_xhat_ecef_y'] = inst['velocity_ecef_y']/mag
    inst['sc_xhat_ecef_z'] = inst['velocity_ecef_z']/mag
    
    # begin with z along Nadir (towards Earth)
    mag = np.sqrt(inst['position_ecef_x']**2 + inst['position_ecef_y']**2 + inst['position_ecef_z']**2)
    inst['sc_zhat_ecef_x'] = -inst['position_ecef_x']/mag
    inst['sc_zhat_ecef_y'] = -inst['position_ecef_y']/mag
    inst['sc_zhat_ecef_z'] = -inst['position_ecef_z']/mag
    
    
    # get y vector assuming right hand rule
    # X x Z = -Y
    # Y = Z x X      yx = ZyXz - XyZz
    inst['sc_yhat_ecef_x'] = inst['sc_zhat_ecef_y']*inst['sc_xhat_ecef_z'] - inst['sc_xhat_ecef_y']*inst['sc_zhat_ecef_z']
    # Yy = -(ZxXz - ZzXx)
    inst['sc_yhat_ecef_y'] = -(inst['sc_zhat_ecef_x']*inst['sc_xhat_ecef_z'] - inst['sc_xhat_ecef_x']*inst['sc_zhat_ecef_z'])
    # Yz = ZxXy - ZyXx
    inst['sc_yhat_ecef_z'] = inst['sc_zhat_ecef_x']*inst['sc_xhat_ecef_y'] - inst['sc_xhat_ecef_x']*inst['sc_zhat_ecef_y']
    # normalize since Xhat and Zhat from above may not be orthogonal
    mag = np.sqrt(inst['sc_yhat_ecef_x']**2 + inst['sc_yhat_ecef_y']**2 + 
                    inst['sc_yhat_ecef_z']**2)
    inst['sc_yhat_ecef_x'] = inst['sc_yhat_ecef_x']/mag
    inst['sc_yhat_ecef_y'] = inst['sc_yhat_ecef_y']/mag
    inst['sc_yhat_ecef_z'] = inst['sc_yhat_ecef_z']/mag
    
    # strictly, need to recalculate Zhat so that it is consistent with RHS
    # just created
    # Z = X x Y      Zx = XyYz - YyXz
    inst['sc_zhat_ecef_x'] = inst['sc_xhat_ecef_y']*inst['sc_yhat_ecef_z'] - inst['sc_yhat_ecef_y']*inst['sc_xhat_ecef_z']
    # Zy = -(XxYz - YzXx)
    inst['sc_zhat_ecef_y'] = -(inst['sc_xhat_ecef_x']*inst['sc_yhat_ecef_z'] - inst['sc_yhat_ecef_x']*inst['sc_xhat_ecef_z'])
    # Zz = XxYy - YxXy
    inst['sc_zhat_ecef_z'] = inst['sc_xhat_ecef_x']*inst['sc_yhat_ecef_y'] - inst['sc_yhat_ecef_x']*inst['sc_xhat_ecef_y']
    # normalize since Xhat and Zhat from above may not be orthogonal
    mag = np.sqrt(inst['sc_zhat_ecef_x']**2 + inst['sc_zhat_ecef_y']**2 + 
                    inst['sc_zhat_ecef_z']**2)
    # print (mag)
    idx, = np.where( (mag < .99999999) | (mag > 1.00000001))
    if len(idx) > 0:
        raise RuntimeError('Unit vector generation failure')
    

def calculate_ecef_velocity(inst):
    
    x = inst['position_ecef_x']
    vel_x = x.values[2:] - x.values[0:-2]
    vel_x /= 2.

    y = inst['position_ecef_y']
    vel_y = y.values[2:] - y.values[0:-2]
    vel_y /= 2.

    z = inst['position_ecef_z']
    vel_z = z.values[2:] - z.values[0:-2]
    vel_z /= 2.
    
    inst[1:-1, 'velocity_ecef_x'] = vel_x
    inst[1:-1, 'velocity_ecef_y'] = vel_y
    inst[1:-1, 'velocity_ecef_z'] = vel_z
    
def aer2ecef(azimuthDeg, elevationDeg, slantRange, obs_lat, obs_long, obs_alt):

    # site ecef in kilometers
    sitex, sitey, sitez = pysat.coords.geodetic_to_ecef(obs_lat, obs_long, obs_alt)
    # site ecef in meters
    sitex *= 1000.
    sitey *= 1000.
    sitez *= 1000.

    # some needed calculations
    slat = np.sin(np.radians(obs_lat))
    slon = np.sin(np.radians(obs_long))
    clat = np.cos(np.radians(obs_lat))
    clon = np.cos(np.radians(obs_long))

    azRad = np.radians(azimuthDeg)
    elRad = np.radians(elevationDeg)

    # az,el,range to sez convertion
    south  = -slantRange * np.cos(elRad) * np.cos(azRad)
    east   =  slantRange * np.cos(elRad) * np.sin(azRad)
    zenith =  slantRange * np.sin(elRad)


    x = ( slat * clon * south) + (-slon * east) + (clat * clon * zenith) + sitex
    y = ( slat * slon * south) + ( clon * east) + (clat * slon * zenith) + sitey
    z = (-clat *        south) + ( slat * zenith) + sitez

    return x, y, z
    

meta = pysat.Meta()
meta['uts'] = {'units':'s', 
               'long_name':'Universal Time', 
               'custom':False}
meta['Epoch'] = {'units':'Milliseconds since 1970-1-1',
                 'Bin_Location': 0.5,
                 'notes': 'UTC time at middle of geophysical measurement.',
                 'desc': 'UTC seconds',
                }
meta['mlt'] = {'units':'hours', 
               'long_name':'Magnetic Local Time',
               'label': 'MLT',
               'axis': 'MLT',
               'desc': 'Magnetic Local Time',
               'value_min': 0.,
               'value_max': 24.,
               'notes': ('Magnetic Local Time is the solar local time of the field line '
                        'at the location where the field crosses the magnetic equator. '
                        'In this case we just simulate 0-24 with a '
                        'consistent orbital period and an offste with SLT.'),
               'fill': np.nan,
               'scale': 'linear'}
meta['slt'] = {'units':'hours', 
               'long_name':'Solar Local Time',
               'label': 'SLT',
               'axis': 'SLT',
               'desc': 'Solar Local Time',
               'value_min': 0.,
               'value_max': 24.,
               'notes': ('Solar Local Time is the local time (zenith angle of sun) '
                         'of the given locaiton. Overhead noon, +/- 90 is 6, 18 SLT .'),
               'fill': np.nan,
               'scale': 'linear'}
meta['orbit_num'] = {'units':'', 
                     'long_name':'Orbit Number',
                     'label': 'Orbit Number',
                     'axis': 'Orbit Number',
                     'desc': 'Orbit Number',
                     'value_min': 0.,
                     'value_max': 25000.,
                     'notes': ('Number of orbits since the start of the mission. '
                               'For this simulation we use the number of 5820 second periods '
                               'since the start, 2008-01-01.'),
                     'fill': np.nan,
                     'scale': 'linear'}

meta['longitude'] = {'units':'degrees', 'long_name':'Longitude'} 
meta['latitude'] = {'units':'degrees', 'long_name':'Latitude'} 
meta['dummy1'] = {'units':'', 'long_name':'dummy1'}
meta['dummy2'] = {'units':'', 'long_name':'dummy2'}
meta['dummy3'] = {'units':'', 'long_name':'dummy3'}
meta['dummy4'] = {'units':'', 'long_name':'dummy4'}
meta['string_dummy'] = {'units':'', 'long_name':'string_dummy'}
meta['unicode_dummy'] = {'units':'', 'long_name':'unicode_dummy'}
meta['int8_dummy'] = {'units':'', 'long_name':'int8_dummy'}
meta['int16_dummy'] = {'units':'', 'long_name':'int16_dummy'}
meta['int32_dummy'] = {'units':'', 'long_name':'int32_dummy'}
meta['int64_dummy'] = {'units':'', 'long_name':'int64_dummy'}
