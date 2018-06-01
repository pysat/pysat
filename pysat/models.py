import pysat

import pandas as pds
import numpy as np

def add_quasi_dipole_coordinates(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ """
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
    return
    
def add_iri_thermal_plasma(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ """
    import pyglow
    from pyglow.pyglow import Point
    
    iri_params = []
    # print 'IRI Simulations'
    for time,lat,lon,alt in zip(inst.data.index, inst[glat_label], inst[glong_label], inst[alt_label]):
        pt = Point(time,lat,lon,alt)
        pt.run_iri()
        iri = {}
        iri['ion_temp'] = pt.Ti
        iri['e_temp'] = pt.Te
        iri['ion_dens'] = pt.ni['O+'] + pt.ni['H+'] #pt.ne - pt.ni['NO+'] - pt.ni['O2+'] - pt.ni['HE+']
        iri['frac_dens_o'] = pt.ni['O+']/iri['ion_dens']
        iri['frac_dens_h'] = pt.ni['H+']/iri['ion_dens']
        iri_params.append(iri)        
    # print 'Complete.'
    iri = pds.DataFrame(iri_params)
    iri.index = inst.data.index
    inst[iri.keys()] = iri

def add_hwm_winds_and_ecef_vectors(inst, glat_label='glat', glong_label='glong', 
                                         alt_label='alt'):
    """ """
    import pyglow
    hwm_params = []
    for time,lat,lon,alt in zip(inst.data.index, inst[glat_label], inst[glong_label], inst[alt_label]):
        pt = pyglow.Point(time,lat,lon,alt)
        pt.run_hwm()
        hwm = {}
        hwm['zonal_wind'] = pt.u
        hwm['meridional_wind'] = pt.v
        hwm_params.append(hwm)        
    # print 'Complete.'
    hwm = pds.DataFrame(hwm_params)
    hwm.index = inst.data.index
    inst[['zonal_wind', 'meridional_wind']] = hwm
    
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
    mag = np.sqrt(inst['position_ecef_x']**2 + inst['position_ecef_y']**2 + inst['position_ecef_z']**2)
    unit_pos_x = inst['position_ecef_x']/mag
    unit_pos_y = inst['position_ecef_y']/mag
    unit_pos_z = inst['position_ecef_z']/mag
    
    # mer = r x zonal
    inst['unit_mer_wind_ecef_x'] = unit_pos_y*inst['unit_zonal_wind_ecef_z'] - unit_pos_z*inst['unit_zonal_wind_ecef_y']
    inst['unit_mer_wind_ecef_y'] = -(unit_pos_x*inst['unit_zonal_wind_ecef_z'] - unit_pos_z*inst['unit_zonal_wind_ecef_x'])
    inst['unit_mer_wind_ecef_z'] = unit_pos_x*inst['unit_zonal_wind_ecef_y'] - unit_pos_y*inst['unit_zonal_wind_ecef_x']
    
    inst['sim_inst_wind_x'] = (inst['meridional_wind']*(inst['sc_xhat_ecef_x']*inst['unit_mer_wind_ecef_x'] + 
                                    inst['sc_xhat_ecef_y']*inst['unit_mer_wind_ecef_y'] + 
                                    inst['sc_xhat_ecef_z']*inst['unit_mer_wind_ecef_z']) + 
                              inst['zonal_wind']*(inst['sc_xhat_ecef_x']*inst['unit_zonal_wind_ecef_x'] + 
                                    inst['sc_xhat_ecef_y']*inst['unit_zonal_wind_ecef_y'] + 
                                    inst['sc_xhat_ecef_z']*inst['unit_zonal_wind_ecef_z']))

    inst['sim_inst_wind_y'] = (inst['meridional_wind']*(inst['sc_yhat_ecef_x']*inst['unit_mer_wind_ecef_x'] + 
                                    inst['sc_yhat_ecef_y']*inst['unit_mer_wind_ecef_y'] + 
                                    inst['sc_yhat_ecef_z']*inst['unit_mer_wind_ecef_z']) + 
                              inst['zonal_wind']*(inst['sc_yhat_ecef_x']*inst['unit_zonal_wind_ecef_x'] + 
                                    inst['sc_yhat_ecef_y']*inst['unit_zonal_wind_ecef_y'] + 
                                    inst['sc_yhat_ecef_z']*inst['unit_zonal_wind_ecef_z']))

    inst['sim_inst_wind_z'] = (inst['meridional_wind']*(inst['sc_zhat_ecef_x']*inst['unit_mer_wind_ecef_x'] + 
                                    inst['sc_zhat_ecef_y']*inst['unit_mer_wind_ecef_y'] + 
                                    inst['sc_zhat_ecef_z']*inst['unit_mer_wind_ecef_z']) + 
                              inst['zonal_wind']*(inst['sc_zhat_ecef_x']*inst['unit_zonal_wind_ecef_x'] + 
                                    inst['sc_zhat_ecef_y']*inst['unit_zonal_wind_ecef_y'] + 
                                    inst['sc_zhat_ecef_z']*inst['unit_zonal_wind_ecef_z']))


def add_igrf(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ """
    import pyglow
    from pyglow.pyglow import Point
    
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

