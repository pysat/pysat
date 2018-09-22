# -*- coding: utf-8 -*-
"""
Produces satellite orbit data. Orbit is simulated using 
Two Line Elements (TLEs) and SGP4. Satellite position is coupled
to several space science models to simulate the atmosphere the 
satellite is in.

"""

from __future__ import print_function
from __future__ import absolute_import

# basestring abstract type is removed in Python 3 and is replaced by str
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str
import os

import pandas as pds
import numpy as np
import pysat

# pysat required parameters
platform = 'pysat'
name = 'sgp4'
# dictionary of data 'tags' and corresponding description
tags = {'':'Satellite simulation data set'}
# dictionary of satellite IDs, list of corresponding tags
sat_ids = {'':['']}
test_dates = {'':{'':pysat.datetime(2018,1,1)}}

        
def init(self):
    """
    Adds custom calculations to orbit simulation.
    This routine is run once, and only once, upon instantiation.
    
    Adds quasi-dipole coordiantes, velocity calculation in ECEF coords,
    adds the attitude vectors of spacecraft assuming x is ram pointing and
    z is generally nadir, adds ionospheric parameters from the Interational
    Reference Ionosphere (IRI), as well as simulated winds from the
    Horiontal Wind Model (HWM).
    
    """
    
    self.custom.add(add_quasi_dipole_coordinates, 'modify')
    self.custom.add(add_aacgm_coordinates, 'modify')
    self.custom.add(calculate_ecef_velocity, 'modify')
    self.custom.add(add_sc_attitude_vectors, 'modify')
    self.custom.add(add_iri_thermal_plasma, 'modify')
    self.custom.add(add_hwm_winds_and_ecef_vectors, 'modify')
    self.custom.add(add_igrf, 'modify')
    # project simulated vectors onto s/c basis
    # IGRF
    # create metadata to be added along with vector projection
    in_meta = {'desc':'IGRF geomagnetic field expressed in the s/c basis.',
               'units':'nT'}
    # project IGRF
    self.custom.add(project_ecef_vector_onto_sc, 'modify', 'end', 'B_ecef_x', 'B_ecef_y', 'B_ecef_z',
                                                           'B_sc_x', 'B_sc_y', 'B_sc_z',
                                                           meta=[in_meta.copy(), in_meta.copy(), in_meta.copy()])
    # project total wind vector
    self.custom.add(project_hwm_onto_sc, 'modify')
    # neutral parameters
    self.custom.add(add_msis, 'modify')
                
def load(fnames, tag=None, sat_id=None, obs_long=0., obs_lat=0., obs_alt=0., 
                                        TLE1=None, TLE2=None):
    """		          
    Returns data and metadata in the format required by pysat. Finds position		
    of satellite in both ECI and ECEF co-ordinates.
    
    Routine is directly called by pysat and not the user.		
    		
    Parameters		
    ----------		
    fnames : list-like collection		
        File name that contains date in its name. 		
    tag : string		
        Identifies a particular subset of satellite data		
    sat_id : string		
        Satellite ID			
    obs_long: float		
        Longitude of the observer on the Earth's surface		
    obs_lat: float		
        Latitude of the observer on the Earth's surface			
    obs_alt: float		
        Altitude of the observer on the Earth's surface		
    TLE1 : string
        First string for Two Line Element. Must be in TLE format	          
    TLE2 : string
        Second string for Two Line Element. Must be in TLE format	          
        
    Example
    -------
      inst = pysat.Instrument('pysat', 'sgp4', 
              TLE1='1 25544U 98067A   18135.61844383  .00002728  00000-0  48567-4 0  9998',
              TLE2='2 25544  51.6402 181.0633 0004018  88.8954  22.2246 15.54059185113452')
      inst.load(2018, 1)
      
    """          
    
    import sgp4
    # wgs72 is the most commonly used gravity model in satellite tracking community
    from sgp4.earth_gravity import wgs72
    from sgp4.io import twoline2rv
    import ephem
    import pysatMagVect

    # TLEs (Two Line Elements for ISS)   
    # format of TLEs is fixed and available from wikipedia... 
    # lines encode list of orbital elements of an Earth-orbiting object 
    # for a given point in time        
    line1 = ('1 25544U 98067A   18135.61844383  .00002728  00000-0  48567-4 0  9998')
    line2 = ('2 25544  51.6402 181.0633 0004018  88.8954  22.2246 15.54059185113452')
    # use ISS defaults if not provided by user
    if TLE1 is not None:
        line1 = TLE1
    if TLE2 is not None:
        line2 = TLE2
    
    # create satellite from TLEs and assuming a gravity model
    # according to module webpage, wgs72 is common
    satellite = twoline2rv(line1, line2, wgs72)

    # grab date from filename
    parts = os.path.split(fnames[0])[-1].split('-')
    yr = int(parts[0])
    month = int(parts[1])
    day = int(parts[2][0:2])
    date = pysat.datetime(yr, month, day)
    
    # create timing at 1 Hz (for 1 day)
    times = pds.date_range(start=date, end=date+pds.DateOffset(seconds=86399), freq='1S')
    # reduce requirements if on testing server
    # TODO Remove this when testing resources are higher
    on_travis = os.environ.get('ONTRAVIS') == 'True'
    if on_travis:
        times = times[0:100]
        
    # create list to hold satellite position, velocity
    position = []
    velocity = []
    for time in times:
        # orbit propagator - computes x,y,z position and velocity
        pos, vel = satellite.propagate(time.year, time.month, time.day, 
                                       time.hour, time.minute, time.second)
        # print (pos)
        position.extend(pos)
        velocity.extend(vel)
        
    # put data into DataFrame
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
    
    # the observer's (ground station) position on the Earth surface
    site = ephem.Observer()
    site.lon = str(obs_long)   
    site.lat = str(obs_lat)   
    site.elevation = obs_alt 
    
    # The first parameter in readtle() is the satellite name
    sat = ephem.readtle('pysat' , line1, line2)
    output_params = []
    for time in times:
        lp = {}
        site.date = time
        sat.compute(site)
        # parameters relative to the ground station
        lp['obs_sat_az_angle'] = ephem.degrees(sat.az)
        lp['obs_sat_el_angle'] = ephem.degrees(sat.alt)
        # total distance away
        lp['obs_sat_slant_range'] = sat.range
        # satellite location 
        # sub latitude point
        lp['glat'] = np.degrees(sat.sublat)
        # sublongitude point
        lp['glong'] = np.degrees(sat.sublong)
        # elevation of sat in m, stored as km
        lp['alt'] = sat.elevation/1000.
        # get ECEF position of satellite
        lp['x'], lp['y'], lp['z'] = pysatMagVect.geodetic_to_ecef(lp['glat'], lp['glong'], lp['alt'])
        output_params.append(lp)
    output = pds.DataFrame(output_params, index=times)
    # modify input object to include calculated parameters
    data[['glong', 'glat', 'alt']] = output[['glong', 'glat', 'alt']]
    data[['position_ecef_x', 'position_ecef_y', 'position_ecef_z']] = output[['x', 'y', 'z']]
    data['obs_sat_az_angle'] = output['obs_sat_az_angle']
    data['obs_sat_el_angle'] = output['obs_sat_el_angle']
    data['obs_sat_slant_range'] = output['obs_sat_slant_range']
    return data, meta.copy()

# create metadata corresponding to variables in load routine just above
# made once here rather than regenerate every load call
meta = pysat.Meta()
meta['Epoch'] = {'units':'Milliseconds since 1970-1-1',
                 'Bin_Location': 0.5,
                 'notes': 'UTC time at middle of geophysical measurement.',
                 'desc': 'UTC seconds',
                 'long_name':'Time index in milliseconds'
                }
meta['position_eci_x'] = {'units':'km',
                          'long_name':'ECI x-position',
                          'desc':'Earth Centered Inertial x-position of satellite.',
                          'label':'ECI-X'}
meta['position_eci_y'] = {'units':'km',
                          'long_name':'ECI y-position',
                          'desc':'Earth Centered Inertial y-position of satellite.',
                          'label':'ECI-Y'}
meta['position_eci_z'] = {'units':'km',
                          'long_name':'ECI z-position',
                          'desc':'Earth Centered Inertial z-position of satellite.',
                          'label':'ECI-Z'}
meta['velocity_eci_x'] = {'units':'km/s', 
                          'desc':'Satellite velocity along ECI-x',
                          'long_name': 'Satellite velocity ECI-x'}
meta['velocity_eci_y'] = {'units':'km/s', 
                          'desc':'Satellite velocity along ECI-y',
                          'long_name': 'Satellite velocity ECI-y'}
meta['velocity_eci_z'] = {'units':'km/s', 
                          'desc':'Satellite velocity along ECI-z',
                          'long_name': 'Satellite velocity ECI-z'}

meta['glong'] = {'units':'degrees',
                 'long_name':'Geodetic longitude',
                 'desc':'WGS84 geodetic longitude'}
meta['glat'] = {'units':'degrees',
                'long_name':'Geodetic latitude',
                'desc':'WGS84 geodetic latitude'}
meta['alt'] = {'units':'km',
               'long_name':'Geodetic height',
               'desc':"WGS84 height above Earth's surface"}
meta['position_ecef_x'] = {'units':'km','desc':'ECEF x co-ordinate of satellite'}
meta['position_ecef_y'] = {'units':'km','desc':'ECEF y co-ordinate of satellite'}
meta['position_ecef_z'] = {'units':'km','desc':'ECEF z co-ordinate of satellite'}
meta['obs_sat_az_angle'] = {'units':'degrees','desc':'Azimuth of satellite from ground station'}
meta['obs_sat_el_angle'] = {'units':'degrees','desc':'Elevation of satellite from ground station'}
meta['obs_sat_slant_range'] = {'units':'km','desc':'Distance of satellite from ground station'}


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2017,12,1), pysat.datetime(2018,12,1)) 
    # file list is effectively just the date in string format - '%D' works only in Mac. '%x' workins in both Windows and Mac
    names = [ data_path+date.strftime('%Y-%m-%d')+'.nofile' for date in index]
    return pysat.Series(names, index=index)


def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    """ Data is simulated so no download routine is possible. Simple pass function"""
    pass


def add_sc_attitude_vectors(inst):
    
    """
    Add attitude vectors for spacecraft assuming ram pointing. 
     
    Presumes spacecraft is pointed along the velocity vector (x), z is
    generally nadir pointing (positive towards Earth), and y completes the 
    right handed system (generally southward).
    
    Notes
    -----
        Expects velocity and position of spacecraft in Earth Centered
        Earth Fixed (ECEF) coordinates to be in the instrument object
        and named velocity_ecef_* (*=x,y,z) and position_ecef_* (*=x,y,z)
    
        Adds attitude vectors for spacecraft in the ECEF basis by calculating the scalar
        product of each attitude vector with each component of ECEF. 

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object
        
    Returns
    -------
    None
        Modifies pysat.Instrument object in place to include S/C attitude unit
        vectors, expressed in ECEF basis. Vectors are named sc_(x,y,z)hat_ecef_(x,y,z).
        sc_xhat_ecef_x is the spacecraft unit vector along x (positive along velocity vector)
        reported in ECEF, ECEF x-component.

    """
    import pysatMagVect

    # ram pointing is along velocity vector
    inst['sc_xhat_ecef_x'], inst['sc_xhat_ecef_y'], inst['sc_xhat_ecef_z'] = \
        pysatMagVect.normalize_vector(inst['velocity_ecef_x'], inst['velocity_ecef_y'], inst['velocity_ecef_z'])
    
    # begin with z along Nadir (towards Earth)
    # if orbit isn't perfectly circular, then the s/c z vector won't
    # point exactly along nadir. However, nadir pointing is close enough
    # to the true z (in the orbital plane) that we can use it to get y, 
    # and use x and y to get the real z
    inst['sc_zhat_ecef_x'], inst['sc_zhat_ecef_y'], inst['sc_zhat_ecef_z'] = \
        pysatMagVect.normalize_vector(-inst['position_ecef_x'], -inst['position_ecef_y'], -inst['position_ecef_z'])    
    
    # get y vector assuming right hand rule
    # Z x X = Y
    inst['sc_yhat_ecef_x'], inst['sc_yhat_ecef_y'], inst['sc_yhat_ecef_z'] = \
        pysatMagVect.cross_product(inst['sc_zhat_ecef_x'], inst['sc_zhat_ecef_y'], inst['sc_zhat_ecef_z'],
                                   inst['sc_xhat_ecef_x'], inst['sc_xhat_ecef_y'], inst['sc_xhat_ecef_z'])
    # normalize since Xhat and Zhat from above may not be orthogonal
    inst['sc_yhat_ecef_x'], inst['sc_yhat_ecef_y'], inst['sc_yhat_ecef_z'] = \
        pysatMagVect.normalize_vector(inst['sc_yhat_ecef_x'], inst['sc_yhat_ecef_y'], inst['sc_yhat_ecef_z'])
    
    # strictly, need to recalculate Zhat so that it is consistent with RHS
    # just created
    # Z = X x Y      
    inst['sc_zhat_ecef_x'], inst['sc_zhat_ecef_y'], inst['sc_zhat_ecef_z'] = \
        pysatMagVect.cross_product(inst['sc_xhat_ecef_x'], inst['sc_xhat_ecef_y'], inst['sc_xhat_ecef_z'],
                                   inst['sc_yhat_ecef_x'], inst['sc_yhat_ecef_y'], inst['sc_yhat_ecef_z'])
    
    # Adding metadata
    inst.meta['sc_xhat_ecef_x'] = {'units':'', 
                                   'desc':'S/C attitude (x-direction, ram) unit vector, expressed in ECEF basis, x-component'}
    inst.meta['sc_xhat_ecef_y'] = {'units':'',
                                   'desc':'S/C attitude (x-direction, ram) unit vector, expressed in ECEF basis, y-component'}
    inst.meta['sc_xhat_ecef_z'] = {'units':'',
                                   'desc':'S/C attitude (x-direction, ram) unit vector, expressed in ECEF basis, z-component'}
    
    inst.meta['sc_zhat_ecef_x'] = {'units':'',
                                   'desc':'S/C attitude (z-direction, generally nadir) unit vector, expressed in ECEF basis, x-component'}
    inst.meta['sc_zhat_ecef_y'] = {'units':'',
                                   'desc':'S/C attitude (z-direction, generally nadir) unit vector, expressed in ECEF basis, y-component'}
    inst.meta['sc_zhat_ecef_z'] = {'units':'',
                                   'desc':'S/C attitude (z-direction, generally nadir) unit vector, expressed in ECEF basis, z-component'}
    
    inst.meta['sc_yhat_ecef_x'] = {'units':'',
                                   'desc':'S/C attitude (y-direction, generally south) unit vector, expressed in ECEF basis, x-component'}
    inst.meta['sc_yhat_ecef_y'] = {'units':'',
                                   'desc':'S/C attitude (y-direction, generally south) unit vector, expressed in ECEF basis, y-component'}
    inst.meta['sc_yhat_ecef_z'] = {'units':'',
                                   'desc':'S/C attitude (y-direction, generally south) unit vector, expressed in ECEF basis, z-component'}    
    
    # check what magnitudes we get
    mag = np.sqrt(inst['sc_zhat_ecef_x']**2 + inst['sc_zhat_ecef_y']**2 + 
                    inst['sc_zhat_ecef_z']**2)
    idx, = np.where( (mag < .999999999) | (mag > 1.000000001))
    if len(idx) > 0:
        print (mag[idx])
        raise RuntimeError('Unit vector generation failure. Not sufficently orthogonal.')

    return

def calculate_ecef_velocity(inst):
    """
    Calculates spacecraft velocity in ECEF frame.
    
    Presumes that the spacecraft velocity in ECEF is in 
    the input instrument object as position_ecef_*. Uses a symmetric
    difference to calculate the velocity thus endpoints will be
    set to NaN. Routine should be run using pysat data padding feature
    to create valid end points.
    
    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object
        
    Returns
    -------
    None
        Modifies pysat.Instrument object in place to include ECEF velocity 
        using naming scheme velocity_ecef_* (*=x,y,z)
        
    """
    
    x = inst['position_ecef_x']
    vel_x = (x.values[2:] - x.values[0:-2])/2.

    y = inst['position_ecef_y']
    vel_y = (y.values[2:] - y.values[0:-2])/2.

    z = inst['position_ecef_z']
    vel_z = (z.values[2:] - z.values[0:-2])/2.
    
    inst[1:-1, 'velocity_ecef_x'] = vel_x
    inst[1:-1, 'velocity_ecef_y'] = vel_y
    inst[1:-1, 'velocity_ecef_z'] = vel_z
    
    inst.meta['velocity_ecef_x'] = {'units':'km/s',
                                    'desc':'Velocity of satellite calculated with respect to ECEF frame.'}
    inst.meta['velocity_ecef_y'] = {'units':'km/s',
                                    'desc':'Velocity of satellite calculated with respect to ECEF frame.'}
    inst.meta['velocity_ecef_z'] = {'units':'km/s',
                                    'desc':'Velocity of satellite calculated with respect to ECEF frame.'}
    return
    
def add_quasi_dipole_coordinates(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ 
    Uses Apexpy package to add quasi-dipole coordinates to instrument object.
    
    The Quasi-Dipole coordinate system includes both the tilt and offset of the 
    geomagnetic field to calculate the latitude, longitude, and local time
    of the spacecraft with respect to the geomagnetic field.
    
    This system is preferred over AACGM near the equator for LEO satellites.
    
    Example
    -------
        # function added velow modifies the inst object upon every inst.load call
        inst.custom.add(add_quasi_dipole_coordinates, 'modify', glat_label='custom_label')
    
    Parameters
    ----------
    inst : pysat.Instrument
        Designed with pysat_sgp4 in mind
    glat_label : string
        label used in inst to identify WGS84 geodetic latitude (degrees)
    glong_label : string
        label used in inst to identify WGS84 geodetic longitude (degrees)
    alt_label : string
        label used in inst to identify WGS84 geodetic altitude (km, height above surface)
        
    Returns
    -------
    inst
        Input pysat.Instrument object modified to include quasi-dipole coordinates, 'qd_lat'
        for magnetic latitude, 'qd_long' for longitude, and 'mlt' for magnetic local time.
        
    """
        
    import apexpy
    ap = apexpy.Apex(date=inst.date)
    
    qd_lat = []; qd_lon = []; mlt = []
    for lat, lon, alt, time in zip(inst[glat_label], inst[glong_label], inst[alt_label], 
                                   inst.data.index):
        # quasi-dipole latitude and longitude from geodetic coords
        tlat, tlon = ap.geo2qd(lat, lon, alt)
        qd_lat.append(tlat)
        qd_lon.append(tlon)
        mlt.append(ap.mlon2mlt(tlon, time))
        
    inst['qd_lat'] = qd_lat
    inst['qd_long'] = qd_lon
    inst['mlt'] = mlt
    
    inst.meta['qd_lat'] = {'units':'degrees','long_name':'Quasi dipole latitude'}
    inst.meta['qd_long'] = {'units':'degrees','long_name':'Quasi dipole longitude'}
    inst.meta['qd_mlt'] = {'units':'hrs','long_name':'Magnetic local time'}    
    
    return

def add_aacgm_coordinates(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ 
    Uses AACGMV2 package to add AACGM coordinates to instrument object.
    
    The Altitude Adjusted Corrected Geomagnetic Coordinates library is used
    to calculate the latitude, longitude, and local time
    of the spacecraft with respect to the geomagnetic field.
    
    Example
    -------
        # function added velow modifies the inst object upon every inst.load call
        inst.custom.add(add_quasi_dipole_coordinates, 'modify', glat_label='custom_label')
    
    Parameters
    ----------
    inst : pysat.Instrument
        Designed with pysat_sgp4 in mind
    glat_label : string
        label used in inst to identify WGS84 geodetic latitude (degrees N)
    glong_label : string
        label used in inst to identify WGS84 geodetic longitude (degrees E)
    alt_label : string
        label used in inst to identify WGS84 geodetic altitude (km, height above surface)
        
    Returns
    -------
    inst
        Input pysat.Instrument object modified to include quasi-dipole coordinates, 'aacgm_lat'
        for magnetic latitude, 'aacgm_long' for longitude, and 'aacgm_mlt' for magnetic local time.
        
    """
        
    import aacgmv2

    aalat = []; aalon = []; mlt = []
    for lat, lon, alt, time in zip(inst[glat_label], inst[glong_label], inst[alt_label], 
                                   inst.data.index):
        # aacgmv2 latitude and longitude from geodetic coords
        tlat, tlon, tmlt = aacgmv2.get_aacgm_coord(lat, lon, alt, time)
        aalat.append(tlat)
        aalon.append(tlon)
        mlt.append(tmlt)
        
    inst['aacgm_lat'] = aalat
    inst['aacgm_long'] = aalon
    inst['aacgm_mlt'] = mlt
    
    inst.meta['aacgm_lat'] = {'units':'degrees','long_name':'AACGM latitude'}
    inst.meta['aacgm_long'] = {'units':'degrees','long_name':'AACGM longitude'}
    inst.meta['aacgm_mlt'] = {'units':'hrs','long_name':'AACGM Magnetic local time'}    
    
    return

    
def add_iri_thermal_plasma(inst, glat_label='glat', glong_label='glong', 
                                 alt_label='alt'):
    """ 
    Uses IRI (International Reference Ionosphere) model to simulate an ionosphere.
    
    Uses pyglow module to run IRI. Configured to use actual solar parameters to run 
    model.
    
    Example
    -------
        # function added velow modifies the inst object upon every inst.load call
        inst.custom.add(add_iri_thermal_plasma, 'modify', glat_label='custom_label')
    
    Parameters
    ----------
    inst : pysat.Instrument
        Designed with pysat_sgp4 in mind
    glat_label : string
        label used in inst to identify WGS84 geodetic latitude (degrees)
    glong_label : string
        label used in inst to identify WGS84 geodetic longitude (degrees)
    alt_label : string
        label used in inst to identify WGS84 geodetic altitude (km, height above surface)
        
    Returns
    -------
    inst
        Input pysat.Instrument object modified to include thermal plasma parameters.
        'ion_temp' for ion temperature in Kelvin
        'e_temp' for electron temperature in Kelvin
        'ion_dens' for the total ion density (O+ and H+)
        'frac_dens_o' for the fraction of total density that is O+
        'frac_dens_h' for the fraction of total density that is H+
        
    """

    import pyglow
    from pyglow.pyglow import Point
    
    iri_params = []
    # print 'IRI Simulations'
    for time,lat,lon,alt in zip(inst.data.index, inst[glat_label], inst[glong_label], inst[alt_label]):
        # Point class is instantiated. Its parameters are a function of time and spatial location
        pt = Point(time,lat,lon,alt)
        pt.run_iri()
        iri = {}
        # After the model is run, its members like Ti, ni[O+], etc. can be accessed
        iri['ion_temp'] = pt.Ti
        iri['e_temp'] = pt.Te
        iri['ion_dens'] = pt.ni['O+'] + pt.ni['H+'] + pt.ni['HE+']#pt.ne - pt.ni['NO+'] - pt.ni['O2+'] - pt.ni['HE+']
        iri['frac_dens_o'] = pt.ni['O+']/iri['ion_dens']
        iri['frac_dens_h'] = pt.ni['H+']/iri['ion_dens']
        iri['frac_dens_he'] = pt.ni['HE+']/iri['ion_dens']
        iri_params.append(iri)        
    # print 'Complete.'
    iri = pds.DataFrame(iri_params)
    iri.index = inst.data.index
    inst[iri.keys()] = iri
    
    inst.meta['ion_temp'] = {'units':'Kelvin','long_name':'Ion Temperature'}
    inst.meta['ion_dens'] = {'units':'N/cc','long_name':'Ion Density',
                             'desc':'Total ion density including O+ and H+ from IRI model run.'}
    inst.meta['frac_dens_o'] = {'units':'','long_name':'Fractional O+ Density'}
    inst.meta['frac_dens_h'] = {'units':'','long_name':'Fractional H+ Density'}
    

def add_hwm_winds_and_ecef_vectors(inst, glat_label='glat', glong_label='glong', 
                                         alt_label='alt'):
    """ 
    Uses HWM (Horizontal Wind Model) model to obtain neutral wind details.
    
    Uses pyglow module to run HWM. Configured to use actual solar parameters to run 
    model.
    
    Example
    -------
        # function added velow modifies the inst object upon every inst.load call
        inst.custom.add(add_hwm_winds_and_ecef_vectors, 'modify', glat_label='custom_label')
    
    Parameters
    ----------
    inst : pysat.Instrument
        Designed with pysat_sgp4 in mind
    glat_label : string
        label used in inst to identify WGS84 geodetic latitude (degrees)
    glong_label : string
        label used in inst to identify WGS84 geodetic longitude (degrees)
    alt_label : string
        label used in inst to identify WGS84 geodetic altitude (km, height above surface)
        
    Returns
    -------
    inst
        Input pysat.Instrument object modified to include HWM winds.
        'zonal_wind' for the east/west winds (u in model) in m/s
        'meiridional_wind' for the north/south winds (v in model) in m/s
        'unit_zonal_wind_ecef_*' (*=x,y,z) is the zonal vector expressed in the ECEF basis
        'unit_mer_wind_ecef_*' (*=x,y,z) is the meridional vector expressed in the ECEF basis
        'sim_inst_wind_*' (*=x,y,z) is the projection of the total wind vector onto s/c basis
        
    """

    import pyglow
    import pysatMagVect

    hwm_params = []
    for time,lat,lon,alt in zip(inst.data.index, inst[glat_label], inst[glong_label], inst[alt_label]):
        # Point class is instantiated. 
        # Its parameters are a function of time and spatial location
        pt = pyglow.Point(time,lat,lon,alt)
        pt.run_hwm()
        hwm = {}
        hwm['zonal_wind'] = pt.u
        hwm['meridional_wind'] = pt.v
        hwm_params.append(hwm)        
    # print 'Complete.'
    hwm = pds.DataFrame(hwm_params)
    hwm.index = inst.data.index
    inst[['zonal_wind', 'meridional_wind']] = hwm[['zonal_wind', 'meridional_wind']]
    
    # calculate zonal unit vector in ECEF
    # zonal wind: east - west; positive east
    # EW direction is tangent to XY location of S/C in ECEF coordinates
    mag = np.sqrt(inst['position_ecef_x']**2 + inst['position_ecef_y']**2)
    inst['unit_zonal_wind_ecef_x'] = -inst['position_ecef_y']/mag
    inst['unit_zonal_wind_ecef_y'] = inst['position_ecef_x']/mag
    inst['unit_zonal_wind_ecef_z'] = 0*inst['position_ecef_x']
    
    # calculate meridional unit vector in ECEF
    # meridional wind: north - south; positive north
    # mer direction completes RHS of position and zonal vector
    unit_pos_x, unit_pos_y, unit_pos_z = \
        pysatMagVect.normalize_vector(-inst['position_ecef_x'], -inst['position_ecef_y'], -inst['position_ecef_z'])    
    
    # mer = r x zonal
    inst['unit_mer_wind_ecef_x'], inst['unit_mer_wind_ecef_y'], inst['unit_mer_wind_ecef_z'] = \
        pysatMagVect.cross_product(unit_pos_x, unit_pos_y, unit_pos_z,
                                   inst['unit_zonal_wind_ecef_x'], inst['unit_zonal_wind_ecef_y'], inst['unit_zonal_wind_ecef_z'])
    
    # Adding metadata information                                
    inst.meta['zonal_wind'] = {'units':'m/s','long_name':'Zonal Wind', 
                               'desc':'HWM model zonal wind'}
    inst.meta['meridional_wind'] = {'units':'m/s','long_name':'Meridional Wind', 
                                    'desc':'HWM model meridional wind'}
    inst.meta['unit_zonal_wind_ecef_x'] = {'units':'',
                                           'long_name':'Zonal Wind Unit ECEF x-vector', 
                                           'desc':'x-value of zonal wind unit vector in ECEF co ordinates'}
    inst.meta['unit_zonal_wind_ecef_y'] = {'units':'', 
                                           'long_name':'Zonal Wind Unit ECEF y-vector', 
                                           'desc':'y-value of zonal wind unit vector in ECEF co ordinates'}
    inst.meta['unit_zonal_wind_ecef_z'] = {'units':'',
                                           'long_name':'Zonal Wind Unit ECEF z-vector', 
                                           'desc':'z-value of zonal wind unit vector in ECEF co ordinates'}
    inst.meta['unit_mer_wind_ecef_x'] = {'units':'',
                                         'long_name':'Meridional Wind Unit ECEF x-vector', 
                                         'desc':'x-value of meridional wind unit vector in ECEF co ordinates'}
    inst.meta['unit_mer_wind_ecef_y'] = {'units':'',
                                         'long_name':'Meridional Wind Unit ECEF y-vector', 
                                         'desc':'y-value of meridional wind unit vector in ECEF co ordinates'}
    inst.meta['unit_mer_wind_ecef_z'] = {'units':'',
                                         'long_name':'Meridional Wind Unit ECEF z-vector', 
                                         'desc':'z-value of meridional wind unit vector in ECEF co ordinates'}
    return


def add_igrf(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ 
    Uses International Geomagnetic Reference Field (IGRF) model to obtain geomagnetic field values.
    
    Uses pyglow module to run IGRF. Configured to use actual solar parameters to run 
    model.
    
    Example
    -------
        # function added velow modifies the inst object upon every inst.load call
        inst.custom.add(add_igrf, 'modify', glat_label='custom_label')
    
    Parameters
    ----------
    inst : pysat.Instrument
        Designed with pysat_sgp4 in mind
    glat_label : string
        label used in inst to identify WGS84 geodetic latitude (degrees)
    glong_label : string
        label used in inst to identify WGS84 geodetic longitude (degrees)
    alt_label : string
        label used in inst to identify WGS84 geodetic altitude (km, height above surface)
        
    Returns
    -------
    inst
        Input pysat.Instrument object modified to include HWM winds.
        'B' total geomagnetic field
        'B_east' Geomagnetic field component along east/west directions (+ east)
        'B_north' Geomagnetic field component along north/south directions (+ north)
        'B_up' Geomagnetic field component along up/down directions (+ up)
        'B_ecef_x' Geomagnetic field component along ECEF x
        'B_ecef_y' Geomagnetic field component along ECEF y
        'B_ecef_z' Geomagnetic field component along ECEF z
        
    """
    
    import pyglow
    from pyglow.pyglow import Point
    import pysatMagVect
    
    igrf_params = []
    # print 'IRI Simulations'
    for time,lat,lon,alt in zip(inst.data.index, inst[glat_label], inst[glong_label], inst[alt_label]):
        pt = Point(time,lat,lon,alt)
        pt.run_igrf()
        igrf = {}
        igrf['B'] = pt.B
        igrf['B_east'] = pt.Bx
        igrf['B_north'] = pt.By
        igrf['B_up'] = pt.Bz
        igrf_params.append(igrf)        
    # print 'Complete.'
    igrf = pds.DataFrame(igrf_params)
    igrf.index = inst.data.index
    inst[igrf.keys()] = igrf
    
    # convert magnetic field in East/north/up to ECEF basis
    x, y, z = pysatMagVect.enu_to_ecef_vector(inst['B_east'], inst['B_north'], inst['B_up'],
                                              inst[glat_label], inst[glong_label])
    inst['B_ecef_x'] = x
    inst['B_ecef_y'] = y
    inst['B_ecef_z'] = z
    
    # metadata
    inst.meta['B'] = {'units':'nT',
                      'desc':'Total geomagnetic field from IGRF.'}
    inst.meta['B_east'] = {'units':'nT',
                           'desc':'Geomagnetic field from IGRF expressed using the East/North/Up (ENU) basis.'}
    inst.meta['B_north'] = {'units':'nT',
                            'desc':'Geomagnetic field from IGRF expressed using the East/North/Up (ENU) basis.'}
    inst.meta['B_up'] = {'units':'nT',
                         'desc':'Geomagnetic field from IGRF expressed using the East/North/Up (ENU) basis.'}

    inst.meta['B_ecef_x'] = {'units':'nT',
                             'desc':'Geomagnetic field from IGRF expressed using the Earth Centered Earth Fixed (ECEF) basis.'}
    inst.meta['B_ecef_y'] = {'units':'nT',
                             'desc':'Geomagnetic field from IGRF expressed using the Earth Centered Earth Fixed (ECEF) basis.'}
    inst.meta['B_ecef_z'] = {'units':'nT',
                             'desc':'Geomagnetic field from IGRF expressed using the Earth Centered Earth Fixed (ECEF) basis.'}
    return


def add_msis(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ 
    Uses MSIS model to obtain thermospheric values.
    
    Uses pyglow module to run MSIS. Configured to use actual solar parameters to run 
    model.
    
    Example
    -------
        # function added velow modifies the inst object upon every inst.load call
        inst.custom.add(add_msis, 'modify', glat_label='custom_label')
    
    Parameters
    ----------
    inst : pysat.Instrument
        Designed with pysat_sgp4 in mind
    glat_label : string
        label used in inst to identify WGS84 geodetic latitude (degrees)
    glong_label : string
        label used in inst to identify WGS84 geodetic longitude (degrees)
    alt_label : string
        label used in inst to identify WGS84 geodetic altitude (km, height above surface)
        
    Returns
    -------
    inst
        Input pysat.Instrument object modified to include MSIS values winds.
        'Nn' total neutral density particles/cm^3
        'Nn_N' Nitrogen number density (particles/cm^3)
        'Nn_N2' N2 number density (particles/cm^3)
        'Nn_O' Oxygen number density (particles/cm^3)
        'Nn_O2' O2 number density (particles/cm^3)
        'Tn_msis' Temperature from MSIS (Kelvin)
        
    """
    
    import pyglow
    from pyglow.pyglow import Point
    
    msis_params = []
    # print 'IRI Simulations'
    for time,lat,lon,alt in zip(inst.data.index, inst[glat_label], inst[glong_label], inst[alt_label]):
        pt = Point(time,lat,lon,alt)
        pt.run_msis()
        msis = {}
        total = 0
        for key in pt.nn.keys():
            total += pt.nn[key]
        msis['Nn'] = total
        msis['Nn_N'] = pt.nn['N']
        msis['Nn_N2'] = pt.nn['N2']
        msis['Nn_O'] = pt.nn['O']
        msis['Nn_O2'] = pt.nn['O2']
        msis['Tn_msis'] = pt.Tn_msis
        msis_params.append(msis)        
    # print 'Complete.'
    msis = pds.DataFrame(msis_params)
    msis.index = inst.data.index
    inst[msis.keys()] = msis
    
    # metadata
    inst.meta['Nn'] = {'units':'cm^-3',
                       'desc':'Total neutral number particle density from MSIS.'}
    inst.meta['Nn_N'] = {'units':'cm^-3',
                         'desc':'Total nitrogen number particle density from MSIS.'}
    inst.meta['Nn_N2'] = {'units':'cm^-3',
                          'desc':'Total N2 number particle density from MSIS.'}
    inst.meta['Nn_O'] = {'units':'cm^-3',
                         'desc':'Total oxygen number particle density from MSIS.'}
    inst.meta['Nn_O2'] = {'units':'cm^-3',
                          'desc':'Total O2 number particle density from MSIS.'}
    inst.meta['Tn_msis'] = {'units':'K',
                            'desc':'Neutral temperature from MSIS.'}

    return

def project_ecef_vector_onto_sc(inst, x_label, y_label, z_label, 
                                new_x_label, new_y_label, new_z_label,
                                meta=None):
    """Express input vector using s/c attitude directions
    
    x - ram pointing
    y - generally southward
    z - generally nadir
    
    Parameters
    ----------
    x_label : string
        Label used to get ECEF-X component of vector to be projected
    y_label : string
        Label used to get ECEF-Y component of vector to be projected
    z_label : string
        Label used to get ECEF-Z component of vector to be projected
    new_x_label : string
        Label used to set X component of projected vector
    new_y_label : string
        Label used to set Y component of projected vector
    new_z_label : string
        Label used to set Z component of projected vector
    meta : array_like of dicts (None)
        Dicts contain metadata to be assigned.
    """
    
    import pysatMagVect

    x, y, z = pysatMagVect.project_ecef_vector_onto_basis(inst[x_label], inst[y_label], inst[z_label],
                                                          inst['sc_xhat_ecef_x'], inst['sc_xhat_ecef_y'], inst['sc_xhat_ecef_z'],
                                                          inst['sc_yhat_ecef_x'], inst['sc_yhat_ecef_y'], inst['sc_yhat_ecef_z'],
                                                          inst['sc_zhat_ecef_x'], inst['sc_zhat_ecef_y'], inst['sc_zhat_ecef_z'])
    inst[new_x_label] = x
    inst[new_y_label] = y
    inst[new_z_label] = z
    
    if meta is not None:
        inst.meta[new_x_label] = meta[0]
        inst.meta[new_y_label] = meta[1]
        inst.meta[new_z_label] = meta[2]
    
    return


def project_hwm_onto_sc(inst):
    
    import pysatMagVect

    total_wind_x = inst['zonal_wind']*inst['unit_zonal_wind_ecef_x'] + inst['meridional_wind']*inst['unit_mer_wind_ecef_x']
    total_wind_y = inst['zonal_wind']*inst['unit_zonal_wind_ecef_y'] + inst['meridional_wind']*inst['unit_mer_wind_ecef_y']
    total_wind_z = inst['zonal_wind']*inst['unit_zonal_wind_ecef_z'] + inst['meridional_wind']*inst['unit_mer_wind_ecef_z']

    x, y, z = pysatMagVect.project_ecef_vector_onto_basis(total_wind_x, total_wind_y, total_wind_z,
                                                          inst['sc_xhat_ecef_x'], inst['sc_xhat_ecef_y'], inst['sc_xhat_ecef_z'],
                                                          inst['sc_yhat_ecef_x'], inst['sc_yhat_ecef_y'], inst['sc_yhat_ecef_z'],
                                                          inst['sc_zhat_ecef_x'], inst['sc_zhat_ecef_y'], inst['sc_zhat_ecef_z'])
    inst['sim_wind_sc_x'] = x
    inst['sim_wind_sc_y'] = y
    inst['sim_wind_sc_z'] = z
    
    inst.meta['sim_wind_sc_x'] = {'units':'m/s','long_name':'Simulated x-vector instrument wind', 
                                  'desc':'Wind from model as measured by instrument in its x-direction'}
    inst.meta['sim_wind_sc_y'] = {'units':'m/s','long_name':'Simulated y-vector instrument wind', 
                                  'desc':'Wind from model as measured by instrument in its y-direction'}
    inst.meta['sim_wind_sc_z'] = {'units':'m/s','long_name':'Simulated z-vector instrument wind', 
                                  'desc':'Wind from model as measured by instrument in its z-direction'}

    return


def plot_simulated_data(ivm, filename=None):

    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.collections import LineCollection
    from mpl_toolkits.basemap import Basemap
    
    if filename is None:
        out_fname = './summary_orbit_simulated_data.png'
    else:
        out_fname = filename
        

    # make monotonically increasing longitude signal
    diff = ivm['glong'].diff()

    idx, = np.where(diff < 0.)
    for item in idx:
        ivm[item:, 'glong'] += 360.

    idx, = np.where((ivm['fit_type'] == 0)  | (ivm['fit_type'] == 1))
    ivm.data = ivm.data.ix[idx,:]

    f = plt.figure(figsize=(8.5,7))
    
    time1 = ivm.data.index[0].strftime('%Y-%h-%d %H:%M:%S')
    if ivm.data.index[0].date() == ivm.data.index[-1].date():
        time2 = ivm.data.index[-1].strftime('%H:%M:%S')
    else:
        time2 = ivm.data.index[-1].strftime('%Y-%h-%d %H:%M:%S')
    # Overall Plot Title
    plt.suptitle(''.join(('SPORT IVM ', time1,' -- ',time2)), fontsize=18)
    
    # create grid for plots
    gs = gridspec.GridSpec(5, 2, width_ratios=[12,1])
    
    ax = f.add_subplot(gs[0,0])
    plt.plot(np.log10(ivm['ion_dens']), 'k', label='total')
    plt.plot(np.log10(ivm['ion_dens']*ivm['frac_dens_o']), 'r', label='O+')
    plt.plot(np.log10(ivm['ion_dens']*ivm['frac_dens_h']), 'b', label='H+')
    # plt.plot(np.log10(ivm['ion_dens']*ivm['frac_dens_he']), 'g', label='He+')
    plt.legend(loc=(01.01, 0.15))
    ax.set_title('Log Ion Density')
    ax.set_ylabel('Log Density (N/cc)')
    ax.set_ylim([1., 6.])
    ax.axes.get_xaxis().set_visible(False)
    
    
    ax2 = f.add_subplot(gs[1,0], sharex=ax)
    plt.plot(ivm['ion_temp'])
    plt.legend(loc=(1.01, 0.15))
    ax2.set_title('Ion Temperature')
    ax2.set_ylabel('Temp (K)')
    ax2.set_ylim([500., 1500.])
    ax2.axes.get_xaxis().set_visible(False)

    # determine altitudes greater than 770 km
    # idx, = np.where(ivm['alt'] > 770.)

    ax3 = f.add_subplot(gs[2,0], sharex=ax)
    plt.plot(ivm['sim_wind_sc_x'], color='b', linestyle='--')
    plt.plot(ivm['sim_wind_sc_y'], color='r', linestyle='--')
    plt.plot(ivm['sim_wind_sc_z'], color='g', linestyle='--')
    ax3.set_title('Neutral Winds in S/C X, Y, and Z')
    ax3.set_ylabel('Velocity (m/s)')
    ax3.set_ylim([-200., 200.])
    ax3.axes.get_xaxis().set_visible(False)
    plt.legend(loc=(1.01, 0.15))
    ax3.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
    # # xlabels = [label[0:6] for label in xlabels]
    # plt.setp(ax3.xaxis.get_majorticklabels(), rotation=20, ha='right')

    ax4 = f.add_subplot(gs[3,0], sharex=ax)
    plt.plot(ivm['B_sc_x']*1e5, color='b', linestyle='--')
    plt.plot(ivm['B_sc_y']*1e5, color='r', linestyle='--')
    plt.plot(ivm['B_sc_z']*1e5, color='g', linestyle='--')
    ax4.set_title('Magnetic Field in S/C X, Y, and Z')
    ax4.set_ylabel('Gauss')
    ax4.set_ylim([-3.5, 3.5])
    # ax3.axes.get_xaxis().set_visible(False)
    plt.legend(loc=(1.01, 0.15))
    ax4.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
    # # xlabels = [label[0:6] for label in xlabels]
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=20, ha='right')
        
    # ivm info
    ax6 = f.add_subplot(gs[4,0])
    
    # do world plot if time to be plotted is less than 285 minutes, less than 3 orbits
    time_diff = ivm.data.index[-1] - ivm.data.index[0]
    if time_diff > pds.Timedelta(minutes=285):
    #    # do long time plot
        ivm['glat'].plot(label='glat')#legend=True, label='mlat')
        ivm['mlt'].plot(label='mlt')#legend=True, label='mlt')
        plt.title('Satellite Position')
        plt.legend(['mlat', 'mlt'], loc=(1.01, 0.15))
    #    ivm['glong'].plot(secondary_y = True, label='glong')#legend=True, secondary_y = True, label='glong')
    
    else:
    
        # make map the same size as the other plots
        s1pos = plt.get(ax,'position').bounds
        s6pos = plt.get(ax6, 'position').bounds
        ax6.set_position( [s1pos[0], s6pos[1]+.008, s1pos[2], s1pos[3]])
        
        #fix longitude range for plot. Pad longitude so that first sample aligned with
        #ivm measurement sample
        lon0 = ivm[0,'glong']
        lon1 = ivm[-1,'glong']
        # print (lon0, lon1)

        # enforce minimal longitude window, keep graphics from being too disturbed
        if (lon1-lon0) < 90:
            lon0 -= 45.
            lon1 += 45.
        if lon1 > 720:
            lon0 -= 360.
            lon1 -= 360.
            ivm[:, 'glong'] -= 360.
        # print (lon0, lon1)
        
        m=Basemap(projection='mill', llcrnrlat=-60, urcrnrlat=60., urcrnrlon=lon1.copy(), \
        llcrnrlon=lon0.copy(), resolution='c', ax=ax6, fix_aspect=False)
        # m is an object which manages drawing to the map
        # it also acts as a transformation function for geo coords to plotting coords
        
        # coastlines
        m.drawcoastlines(ax=ax6)
        # get first longitude meridian to plot
        plon=np.ceil(lon0/60.)*60.
        m.drawmeridians(np.arange(plon, plon+360.-22.5, 60), labels=[0,0,0,1], ax=ax6)
        m.drawparallels(np.arange(-20,20,20))
        # time midway through ivm to plot terminator locations
        midDate = ivm.data.index[len(ivm.data.index)//2]
        
        # plot day/night terminators
        try:
            cs=m.nightshade(midDate)
        except ValueError:
            pass
                
        x, y = m(ivm['glong'].values, ivm['glat'].values)
        points = np.array([x,y]).T.reshape(-1,1,2)
        segments = np.concatenate([points[:-1],points[1:]], axis=1)
        plot_norm = plt.Normalize(300,500)
        try:
            plot_cmap = plt.get_cmap('viridis')
        except:
            plot_cmap = plt.get_cmap('jet')
        
        lc = LineCollection(segments, cmap=plot_cmap, norm=plot_norm, linewidths=5.0)
        lc.set_array(ivm['alt'].values)
        sm = plt.cm.ScalarMappable(cmap=plot_cmap, norm=plot_norm)
        sm._A = []
        
        ax6.add_collection(lc)
        
        
        ax6_bar = f.add_subplot(gs[4,1])
        #plt.colorbar(sm)
        cbar = plt.colorbar(cax=ax6_bar, ax=ax6, mappable=sm,
                            orientation='vertical',
                            ticks=[300., 400., 500.])
        plt.xlabel('Altitude')
        plt.ylabel('km')
                    
                            
    f.tight_layout()
    # buffer for overall title
    f.subplots_adjust(bottom=0.06, top=0.91, right=.91)
    plt.subplots_adjust(hspace = .44)

    plt.savefig(out_fname)

    return
  
