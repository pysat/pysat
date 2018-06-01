import scipy
import scipy.integrate
import numpy as np


def geocentric_to_ecef(latitude, longitude, altitude):
    """Convert geocentric coordinates into ECEF
    
    Parameters
    ----------
    latitude : float or array_like
        Geocentric latitude
    longitude : float or array_like
        Geocentric longitude
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
    """Convert ECEF into geocentric coordinates"""

    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    colatitude = np.rad2deg(np.arccos(z / r))
    longitude = np.rad2deg(np.arctan2(y, x))
    latitude = 90. - colatitude

    return latitude, longitude, r - ref_height


def geodetic_to_ecef(latitude, longitude, altitude):
    """Convert geodetic coordinates into ECEF"""

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
    """Convert ECEF to Geodetic WGS84 coordinates."""
    method = method or 'closed'
    # calculate satellite position in ECEF coordinates
    b = 6356.75231424518
    a = 6378.1370
    ellip = np.sqrt(1. - b ** 2 / a ** 2)

    # first eccentricity squared
    e2 = ellip ** 2  # 6.6943799901377997E-3

    longitude = np.arctan2(y, x)
    p = np.sqrt(x ** 2 + y ** 2)
    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    #    # convenient calculation parameters
    # # http://danceswithcode.net/engineeringnotes/geodetic_to_ecef/geodetic_to_ecef.html

    # closed form solution
    # need to find source
    if method == 'closed':
        e_prime = np.sqrt((a ** 2 - b ** 2) / b ** 2)
        theta = np.arctan2(z * a, p * b)
        latitude = np.arctan2(z + e_prime ** 2 * b * np.sin(theta) ** 3, p - ellip ** 2 * a * np.cos(theta) ** 3)
        ## trying this out
        # theta = np.arctan2(p*b, z*a)
        # latitude = np.arctan2(p-ellip**2*a*np.cos(theta)**3, z+e_prime**2*b*np.sin(theta)**3)
        r_n = a / np.sqrt(1. - ellip ** 2 * np.sin(latitude) ** 2)
        h = p / np.cos(latitude) - r_n

    # another possibility
    # http://ir.lib.ncku.edu.tw/bitstream/987654321/39750/1/3011200501001.pdf

    # comparison of techniques

    ## iterative method
    # http://www.oc.nps.edu/oc2902w/coord/coordcvt.pdf
    if method == 'iterative':
        latitude = np.arctan2(p, z)
        r_n = a / np.sqrt(1. - ellip ** 2 * np.sin(latitude) ** 2)
        for i in np.arange(6):
            # print latitude
            r_n = a / np.sqrt(1. - ellip ** 2 * np.sin(latitude) ** 2)
            h = p / np.cos(latitude) - r_n
            latitude = np.arctan(z / p / (1. - ellip ** 2 * (r_n / (r_n + h))))
            # print h
        # final ellipsoidal height update
        h = p / np.cos(latitude) - r_n

    return np.rad2deg(latitude), np.rad2deg(longitude), h

def enu_to_ecef_basis(east, north, up, glat, glong, alt):
    """Converts from East, North, Up components to ECEF"""
    pass
    