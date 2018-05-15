import pysat
import pandas as pds

def add_quasi_dipole_coordinates(inst, glat_label='glat', glong_label='glong', 
                                       alt_label='alt'):
    """ """
    import apexpy
    ap = apexpy.Apex(date=inst.date)
    
    qd_lat = []; qd_lon = []
    for lat, lon, alt in zip(inst[glat_label], inst[glong_label], inst[alt_label]):
        # quasi-dipole latitude and longitude from geodetic coords
        tlat, tlon = ap.geo2qd(lat, lon, alt)
        qd_lat.append(tlat)
        qd_lon.append(tlon)
        
    inst['qd_lat'] = qd_lat
    inst['qd_long'] = qd_lon
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
        iri['ion_dens'] = pt.ni['O+'] + pt.ni['H+'] #pt.ne - pt.ni['NO+'] - pt.ni['O2+'] - pt.ni['HE+']
        iri['frac_dens_o'] = pt.ni['O+']/iri['ion_dens']
        iri['frac_dens_h'] = pt.ni['H+']/iri['ion_dens']
        iri_params.append(iri)        
    # print 'Complete.'
    iri = pds.DataFrame(iri_params)
    iri.index = inst.data.index
    inst[['ion_temp', 'ion_dens', 'frac_dens_o', 'frac_dens_h']] = iri

        