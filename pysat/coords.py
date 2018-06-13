import scipy
import scipy.integrate
import numpy as np


def geocentric_to_ecef(latitude, longitude, altitude):
    """Convert geocentric coordinates into ECEF
    
    Parameters
    ----------
    latitude : float or array_like
        Geocentric latitude (degrees)
    longitude : float or array_like
        Geocentric longitude (degrees)
    altitude : float or array_like
        Height (km) above presumed spherical Earth with radius 6371 km.
        
    Returns
    -------
    x, y, z
        numpy arrays of x, y, z locations in km
        
    """

    r = 6371. + altitude
    # colatitude = 90. - latitude
    x = r * np.cos(np.deg2rad(latitude)) * np.cos(np.deg2rad(longitude))
    y = r * np.cos(np.deg2rad(latitude)) * np.sin(np.deg2rad(longitude))
    z = r * np.sin(np.deg2rad(latitude))

    return x, y, z


def ecef_to_geocentric(x, y, z, ref_height=6371.):
    """Convert ECEF into geocentric coordinates
    
    Parameters
    ----------
    x : float or array_like
        ECEF-X in km
    y : float or array_like
        ECEF-Y in km
    z : float or array_like
        ECEF-Z in km
    ref_height : float or array_like
        Reference radius used for calculating height
    Returns
    -------
    latitude, longitude, altitude
        numpy arrays of locations in degrees, degrees, and km
        
    """

    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    colatitude = np.rad2deg(np.arccos(z / r))
    longitude = np.rad2deg(np.arctan2(y, x))
    latitude = 90. - colatitude

    return latitude, longitude, r - ref_height


def geodetic_to_ecef(latitude, longitude, altitude):
    """Convert WGS84 geodetic coordinates into ECEF
    
    Parameters
    ----------
    latitude : float or array_like
        Geodetic latitude (degrees)
    longitude : float or array_like
        Geodetic longitude (degrees)
    altitude : float or array_like
        Geodetic Height (km) above WGS84 reference ellipsoid.
        
    Returns
    -------
    x, y, z
        numpy arrays of x, y, z locations in km
        
    """

    b = 6356.75231424518
    a = 6378.1370
    ellip = np.sqrt(1. - b ** 2 / a ** 2)
    r_n = a / np.sqrt(1. - ellip ** 2 * np.sin(np.deg2rad(latitude)) ** 2)

    # colatitude = 90. - latitude
    x = (r_n + altitude) * np.cos(np.deg2rad(latitude)) * np.cos(np.deg2rad(longitude))
    y = (r_n + altitude) * np.cos(np.deg2rad(latitude)) * np.sin(np.deg2rad(longitude))
    z = (r_n * (1. - ellip ** 2) + altitude) * np.sin(np.deg2rad(latitude))

    return x, y, z


def ecef_to_geodetic(x, y, z, method=None):
    """Convert ECEF into Geodetic WGS84 coordinates
    
    Parameters
    ----------
    x : float or array_like
        ECEF-X in km
    y : float or array_like
        ECEF-Y in km
    z : float or array_like
        ECEF-Z in km
    method : 'iterative' or 'closed' ('closed' is deafult)
        String selects method of conversion. Closed for mathematical
        solution (http://www.epsg.org/Portals/0/373-07-2.pdf , page 96 section 2.2.1)
        or iterative (http://www.oc.nps.edu/oc2902w/coord/coordcvt.pdf).
        
    Returns
    -------
    latitude, longitude, altitude
        numpy arrays of locations in degrees, degrees, and km
        
    """
    
    method = method or 'closed'
    # calculate satellite position in ECEF coordinates
    b = 6356.75231424518
    a = 6378.1370
    ellip = np.sqrt(1. - b ** 2 / a ** 2)

    # first eccentricity squared
    e2 = ellip ** 2  # 6.6943799901377997E-3

    longitude = np.arctan2(y, x)
    p = np.sqrt(x ** 2 + y ** 2)
    # r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    #    # convenient calculation parameters
    # # http://danceswithcode.net/engineeringnotes/geodetic_to_ecef/geodetic_to_ecef.html

    # closed form solution
    # need to find source
    # a source, http://www.epsg.org/Portals/0/373-07-2.pdf , page 96 section 2.2.1
    if method == 'closed':
        e_prime = np.sqrt((a**2 - b**2) / b**2)
        theta = np.arctan2(z*a, p*b)
        latitude = np.arctan2(z + e_prime**2*b*np.sin(theta)**3, p - e2*a*np.cos(theta)**3)
        ## trying this out
        # theta = np.arctan2(p*b, z*a)
        # latitude = np.arctan2(p-ellip**2*a*np.cos(theta)**3, z+e_prime**2*b*np.sin(theta)**3)
        r_n = a / np.sqrt(1. - e2 * np.sin(latitude) ** 2)
        h = p / np.cos(latitude) - r_n

    # another possibility
    # http://ir.lib.ncku.edu.tw/bitstream/987654321/39750/1/3011200501001.pdf

    ## iterative method
    # http://www.oc.nps.edu/oc2902w/coord/coordcvt.pdf
    if method == 'iterative':
        latitude = np.arctan2(p, z)
        r_n = a / np.sqrt(1. - e2*np.sin(latitude)**2)
        for i in np.arange(6):
            # print latitude
            r_n = a / np.sqrt(1. - e2*np.sin(latitude)**2)
            h = p / np.cos(latitude) - r_n
            latitude = np.arctan(z / p / (1. - e2 * (r_n / (r_n + h))))
            # print h
        # final ellipsoidal height update
        h = p / np.cos(latitude) - r_n

    return np.rad2deg(latitude), np.rad2deg(longitude), h

def enu_to_ecef_vector(east, north, up, glat, glong):
    """Converts vector from East, North, Up components to ECEF
    
    Position of vector in geospace may be specified in either
    geocentric or geodetic coordinates, with corresponding expression
    of the vector using radial or ellipsoidal unit vectors.
    
    Parameters
    ----------
    east : float or array-like
        Eastward component of vector
    north : float or array-like
        Northward component of vector
    up : float or array-like
        Upward component of vector
    latitude : float or array_like
        Geodetic or geocentric latitude (degrees)
    longitude : float or array_like
        Geodetic or geocentric longitude (degrees)
    
    Returns
    -------
    x, y, z
        Vector components along ECEF x, y, and z directions
    
    """
    
    # convert lat and lon in degrees to radians
    rlat = np.radians(glat)
    rlon = np.radians(glong)
    
    x = -east*np.sin(rlat) - north*np.cos(rlat)*np.sin(rlon) + up*np.cos(rlat)*np.cos(rlon)
    y = east*np.cos(rlat) - north*np.sin(rlat)*np.sin(rlon) + up*np.sin(rlat)*np.cos(rlon)
    z = north*np.cos(rlon) + up*np.sin(rlon)

    return x, y, z

def ecef_to_enu_vector(x, y, z, glat, glong):
    """Converts vector from ECEF X,Y,Z components to East, North, Up
    
    Position of vector in geospace may be specified in either
    geocentric or geodetic coordinates, with corresponding expression
    of the vector using radial or ellipsoidal unit vectors.
    
    Parameters
    ----------
    x : float or array-like
        ECEF-X component of vector
    y : float or array-like
        ECEF-Y component of vector
    z : float or array-like
        ECEF-Z component of vector
    latitude : float or array_like
        Geodetic or geocentric latitude (degrees)
    longitude : float or array_like
        Geodetic or geocentric longitude (degrees)
    
    Returns
    -------
    east, north, up
        Vector components along east, north, and up directions
    
    """

    # convert lat and lon in degrees to radians
    rlat = np.radians(glat)
    rlon = np.radians(glong)
    
    east = -x*np.sin(rlat) + y*np.cos(rlat)
    north = -x*np.cos(rlat)*np.sin(rlon) - y*np.sin(rlat)*np.sin(rlon) + z*np.cos(rlon)
    up = x*np.cos(rlat)*np.sin(rlon) + y*np.sin(rlat)*np.cos(rlon)+ z*np.sin(rlon)

    return east, north, up


def project_ecef_vector_onto_basis(x, y, z, xx, xy, xz, yx, yy, yz, zx, zy, zz):
    """Projects vector in ecef onto different basis, with components also expressed in ECEF
    
    Parameters
    ----------
    x : float or array-like
        ECEF-X component of vector
    y : float or array-like
        ECEF-Y component of vector
    z : float or array-like
        ECEF-Z component of vector
    xx : float or array-like
        ECEF-X component of the x unit vector of new basis 
    xy : float or array-like
        ECEF-Y component of the x unit vector of new basis 
    xz : float or array-like
        ECEF-Z component of the x unit vector of new basis 
    
    """
    
    out_x = x*xx + y*xy + z*xz
    out_y = x*yx + y*yy + z*yz
    out_z = x*zx + y*zy + z*zz
    
    return out_x, out_y, out_z