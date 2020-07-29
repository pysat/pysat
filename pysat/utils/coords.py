"""
pysat.utils.coords - coordinate transformations for pysat
=========================================

pysat.utils.coords contains a number of coordinate-transformation
functions used throughout the pysat package.
"""

import numpy as np
import pandas as pds
import warnings


def adjust_cyclic_data(samples, high=2.0*np.pi, low=0.0):
    """Adjust cyclic values such as longitude to a different scale

    Parameters
    -----------
    samples : array_like
        Input array
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
    axis : int or NoneType
        Axis along which standard deviations are computed.  The default is to
        compute the standard deviation of the flattened array

    Returns
    --------
    out_samples : float
        Circular standard deviation

    """

    out_samples = np.asarray(samples)
    sample_range = high - low
    out_samples[out_samples >= high] -= sample_range
    out_samples[out_samples < low] += sample_range

    return out_samples


def update_longitude(inst, lon_name=None, high=180.0, low=-180.0):
    """ Update longitude to the desired range

    Parameters
    ------------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data
    high : float
        Highest allowed longitude value (default=180.0)
    low : float
        Lowest allowed longitude value (default=-180.0)

    Returns
    ---------
    updates instrument data in column 'lon_name'

    """

    from pysat.utils.coords import adjust_cyclic_data

    if lon_name not in inst.data.keys():
        raise ValueError('uknown longitude variable name')

    new_lon = adjust_cyclic_data(inst[lon_name], high=high, low=low)

    # Update based on data type
    if inst.pandas_format:
        inst[lon_name] = new_lon
    else:
        inst[lon_name].data = new_lon

    return


def calc_solar_local_time(inst, lon_name=None, slt_name='slt'):
    """ Append solar local time to an instrument object

    Parameters
    ------------
    inst : pysat.Instrument instance
        instrument object to be updated
    lon_name : string
        name of the longtiude data key (assumes data are in degrees)
    slt_name : string
        name of the output solar local time data key (default='slt')

    Returns
    ---------
    updates instrument data in column specified by slt_name

    """

    import datetime as dt

    if lon_name not in inst.data.keys():
        raise ValueError('uknown longitude variable name')

    # Convert from numpy epoch nanoseconds to UT seconds of day
    ut_hr = list()
    for nptime in inst.index.values.astype(int):
        # Numpy times come out in nanoseconds and timestamp converts
        # from seconds
        dtime = dt.datetime.utcfromtimestamp(nptime * 1.0e-9)
        ut_hr.append((dtime.hour * 3600.0 + dtime.minute * 60.0 +
                      dtime.second + dtime.microsecond * 1.0e-6) / 3600.0)
    # Calculate solar local time
    slt = np.array([t + inst[lon_name][i] / 15.0 for i, t in enumerate(ut_hr)])

    # Ensure that solar local time falls between 0 and 24 hours
    slt = np.mod(slt, 24.0)

    # Add the solar local time to the instrument
    if inst.pandas_format:
        inst[slt_name] = pds.Series(slt, index=inst.data.index)
    else:
        inst.data = inst.data.assign({slt_name: (inst.data.coords.keys(), slt)})

    # Add units to the metadata
    inst.meta[slt_name] = {inst.meta.units_label: 'h',
                           inst.meta.name_label: "Solar Local Time",
                           inst.meta.desc_label: "Solar local time",
                           inst.meta.plot_label: "SLT",
                           inst.meta.axis_label: "SLT",
                           inst.meta.scale_label: "linear",
                           inst.meta.min_label: 0.0,
                           inst.meta.max_label: 24.0,
                           inst.meta.fill_label: np.nan}

    return


def scale_units(out_unit, in_unit):
    """Deprecated function, moved to pysat.utils._core"""

    import warnings
    from pysat import utils

    warnings.warn(' '.join(["utils.coords.scale_units is deprecated, use",
                            "pysat.utils.scale_units instead"]),
                  DeprecationWarning, stacklevel=2)
    unit_scale = utils.scale_units(out_unit, in_unit)

    return unit_scale


def geodetic_to_geocentric(lat_in, lon_in=None, inverse=False):
    """Converts position from geodetic to geocentric or vice-versa.

    .. deprecated:: 2.2.0
      `geodetic_to_geocentric` will be removed in pysat 3.0.0, it will
      be added to pysatMadrigal

    Parameters
    ----------
    lat_in : float
        latitude in degrees.
    lon_in : float or NoneType
        longitude in degrees.  Remains unchanged, so does not need to be
        included. (default=None)
    inverse : bool
        False for geodetic to geocentric, True for geocentric to geodetic.
        (default=False)

    Returns
    -------
    lat_out : float
        latitude [degree] (geocentric/detic if inverse=False/True)
    lon_out : float or NoneType
        longitude [degree] (geocentric/detic if inverse=False/True)
    rad_earth : float
        Earth radius [km] (geocentric/detic if inverse=False/True)

    Notes
    -----
    Uses WGS-84 values

    References
    ----------
    Based on J.M. Ruohoniemi's geopack and R.J. Barnes radar.pro

    """

    warnings.warn(' '.join(["coords.geodetic_to_geocentric is deprecated and",
                            "will be removed in pysat 3.0.0. This function ",
                            "will move to the new pysatMadrigal package."]),
                  DeprecationWarning, stacklevel=2)

    rad_eq = 6378.1370  # WGS-84 semi-major axis
    flat = 1.0 / 298.257223563  # WGS-84 flattening
    rad_pol = rad_eq * (1.0 - flat)  # WGS-84 semi-minor axis

    # The ratio between the semi-major and minor axis is used several times
    rad_ratio_sq = (rad_eq / rad_pol)**2

    # Calculate the square of the second eccentricity (e')
    eprime_sq = rad_ratio_sq - 1.0

    # Calculate the tangent of the input latitude
    tan_in = np.tan(np.radians(lat_in))

    # If converting from geodetic to geocentric, take the inverse of the
    # radius ratio
    if not inverse:
        rad_ratio_sq = 1.0 / rad_ratio_sq

    # Calculate the output latitude
    lat_out = np.degrees(np.arctan(rad_ratio_sq * tan_in))

    # Calculate the Earth radius at this latitude
    rad_earth = rad_eq / np.sqrt(1.0 + eprime_sq *
                                 np.sin(np.radians(lat_out))**2)

    # longitude remains unchanged
    lon_out = lon_in

    return lat_out, lon_out, rad_earth


def geodetic_to_geocentric_horizontal(lat_in, lon_in, az_in, el_in,
                                      inverse=False):
    """Converts from local horizontal coordinates in a geodetic system to local
    horizontal coordinates in a geocentric system

    .. deprecated:: 2.2.0
      `geodetic_to_geocentric_horizontal` will be removed in pysat 3.0.0, it
      will be added to pysatMadrigal

    Parameters
    ----------
    lat_in : float
        latitude in degrees of the local horizontal coordinate system center
    lon_in : float
        longitude in degrees of the local horizontal coordinate system center
    az_in : float
        azimuth in degrees within the local horizontal coordinate system
    el_in : float
        elevation in degrees within the local horizontal coordinate system
    inverse : bool
        False for geodetic to geocentric, True for inverse (default=False)

    Returns
    -------
    lat_out : float
        latitude in degrees of the converted horizontal coordinate system
        center
    lon_out : float
        longitude in degrees of the converted horizontal coordinate system
        center
    rad_earth : float
        Earth radius in km at the geocentric/detic (False/True) location
    az_out : float
        azimuth in degrees of the converted horizontal coordinate system
    el_out : float
        elevation in degrees of the converted horizontal coordinate system

    References
    ----------
    Based on J.M. Ruohoniemi's geopack and R.J. Barnes radar.pro

    """

    warnings.warn(' '.join(["coords.geodetic_to_geocentric_horizontal is",
                            "deprecated and will be removed in pysat 3.0.0.",
                            "This function will move to the new pysatMadrigal",
                            "package."]),
                  DeprecationWarning, stacklevel=2)

    az = np.radians(az_in)
    el = np.radians(el_in)

    # Transform the location of the local horizontal coordinate system center
    lat_out, lon_out, rad_earth = geodetic_to_geocentric(lat_in, lon_in,
                                                         inverse=inverse)

    # Calcualte the deviation from vertical in radians
    dev_vert = np.radians(lat_in - lat_out)

    # Calculate cartesian coordinated in local system
    x_local = np.cos(el) * np.sin(az)
    y_local = np.cos(el) * np.cos(az)
    z_local = np.sin(el)

    # Now rotate system about the x axis to align local vertical vector
    # with Earth radial vector
    x_out = x_local
    y_out = y_local * np.cos(dev_vert) + z_local * np.sin(dev_vert)
    z_out = -y_local * np.sin(dev_vert) + z_local * np.cos(dev_vert)

    # Transform the azimuth and elevation angles
    az_out = np.degrees(np.arctan2(x_out, y_out))
    el_out = np.degrees(np.arctan(z_out / np.sqrt(x_out**2 + y_out**2)))

    return lat_out, lon_out, rad_earth, az_out, el_out


def spherical_to_cartesian(az_in, el_in, r_in, inverse=False):
    """Convert a position from spherical to cartesian, or vice-versa

    .. deprecated:: 2.2.0
      `spherical_to_cartesian` will be removed in pysat 3.0.0, it will
      be added to pysatMadrigal

    Parameters
    ----------
    az_in : float
        azimuth/longitude in degrees or cartesian x in km (inverse=False/True)
    el_in : float
        elevation/latitude in degrees or cartesian y in km (inverse=False/True)
    r_in : float
        distance from origin in km or cartesian z in km (inverse=False/True)
    inverse : boolian
        False to go from spherical to cartesian and True for the inverse

    Returns
    -------
    x_out : float
        cartesian x in km or azimuth/longitude in degrees (inverse=False/True)
    y_out : float
        cartesian y in km or elevation/latitude in degrees (inverse=False/True)
    z_out : float
        cartesian z in km or distance from origin in km (inverse=False/True)

    Notes
    ------
    This transform is the same for local or global spherical/cartesian
    transformations.

    Returns elevation angle (angle from the xy plane) rather than zenith angle
    (angle from the z-axis)

    """

    warnings.warn(' '.join(["coords.spherical_to_cartesian is deprecated and",
                            "will be removed in pysat 3.0.0. This function ",
                            "will move to the new pysatMadrigal package."]),
                  DeprecationWarning, stacklevel=2)

    if inverse:
        # Cartesian to Spherical
        xy_sq = az_in**2 + el_in**2
        z_out = np.sqrt(xy_sq + r_in**2)  # This is r
        y_out = np.degrees(np.arctan2(np.sqrt(xy_sq), r_in))  # This is zenith
        y_out = 90.0 - y_out  # This is the elevation
        x_out = np.degrees(np.arctan2(el_in, az_in))  # This is azimuth
    else:
        # Spherical coordinate system uses zenith angle (degrees from the
        # z-axis) and not the elevation angle (degrees from the x-y plane)
        zen_in = np.radians(90.0 - el_in)

        # Spherical to Cartesian
        x_out = r_in * np.sin(zen_in) * np.cos(np.radians(az_in))
        y_out = r_in * np.sin(zen_in) * np.sin(np.radians(az_in))
        z_out = r_in * np.cos(zen_in)

    return x_out, y_out, z_out


def global_to_local_cartesian(x_in, y_in, z_in, lat_cent, lon_cent, rad_cent,
                              inverse=False):
    """Converts a position from global to local cartesian or vice-versa

    .. deprecated:: 2.2.0
      `global_to_local_cartesian` will be removed in pysat 3.0.0, it will
      be added to pysatMadrigal

    Parameters
    ----------
    x_in : float
        global or local cartesian x in km (inverse=False/True)
    y_in : float
        global or local cartesian y in km (inverse=False/True)
    z_in : float
        global or local cartesian z in km (inverse=False/True)
    lat_cent : float
        geocentric latitude in degrees of local cartesian system origin
    lon_cent : float
        geocentric longitude in degrees of local cartesian system origin
    rad_cent : float
        distance from center of the Earth in km of local cartesian system
        origin
    inverse : bool
        False to convert from global to local cartesian coodiantes, and True
        for the inverse (default=False)

    Returns
    -------
    x_out : float
        local or global cartesian x in km (inverse=False/True)
    y_out : float
        local or global cartesian y in km (inverse=False/True)
    z_out : float
        local or global cartesian z in km (inverse=False/True)

    Notes
    -------
    The global cartesian coordinate system has its origin at the center of the
    Earth, while the local system has its origin specified by the input
    latitude, longitude, and radius.  The global system has x intersecting
    the equatorial plane and the prime meridian, z pointing North along the
    rotational axis, and y completing the right-handed coodinate system.
    The local system has z pointing up, y pointing North, and x pointing East.

    """

    warnings.warn(' '.join(["coords.global_to_local_cartesian is deprecated",
                            "and will be removed in pysat 3.0.0. This function",
                            "will move to the new pysatMadrigal package."]),
                  DeprecationWarning, stacklevel=2)

    # Get the global cartesian coordinates of local origin
    x_cent, y_cent, z_cent = spherical_to_cartesian(lon_cent, lat_cent,
                                                    rad_cent)

    # Get the amount of rotation needed to align the x-axis with the
    # Earth's rotational axis
    ax_rot = np.radians(90.0 - lat_cent)

    # Get the amount of rotation needed to align the global x-axis with the
    # prime meridian
    mer_rot = np.radians(lon_cent - 90.0)

    if inverse:
        # Rotate about the x-axis to align the z-axis with the Earth's
        # rotational axis
        xrot = x_in
        yrot = y_in * np.cos(ax_rot) - z_in * np.sin(ax_rot)
        zrot = y_in * np.sin(ax_rot) + z_in * np.cos(ax_rot)

        # Rotate about the global z-axis to get the global x-axis aligned
        # with the prime meridian and translate the local center to the
        # global origin
        x_out = xrot * np.cos(mer_rot) - yrot * np.sin(mer_rot) + x_cent
        y_out = xrot * np.sin(mer_rot) + yrot * np.cos(mer_rot) + y_cent
        z_out = zrot + z_cent
    else:
        # Translate global origin to the local origin
        xtrans = x_in - x_cent
        ytrans = y_in - y_cent
        ztrans = z_in - z_cent

        # Rotate about the global z-axis to get the local x-axis pointing East
        xrot = xtrans * np.cos(-mer_rot) - ytrans * np.sin(-mer_rot)
        yrot = xtrans * np.sin(-mer_rot) + ytrans * np.cos(-mer_rot)
        zrot = ztrans

        # Rotate about the x-axis to get the z-axis pointing up
        x_out = xrot
        y_out = yrot * np.cos(-ax_rot) - zrot * np.sin(-ax_rot)
        z_out = yrot * np.sin(-ax_rot) + zrot * np.cos(-ax_rot)

    return x_out, y_out, z_out


def local_horizontal_to_global_geo(az, el, dist, lat_orig, lon_orig, alt_orig,
                                   geodetic=True):
    """ Convert from local horizontal coordinates to geodetic or geocentric
    coordinates

    .. deprecated:: 2.2.0
      `local_horizontal_to_global_geo` will be removed in pysat 3.0.0, it will
      be added to pysatMadrigal

    Parameters
    ----------
    az : float
        Azimuth (angle from North) of point in degrees
    el : float
        Elevation (angle from ground) of point in degrees
    dist : float
        Distance from origin to point in km
    lat_orig : float
        Latitude of origin in degrees
    lon_orig : float
        Longitude of origin in degrees
    alt_orig : float
        Altitude of origin in km from the surface of the Earth
    geodetic : bool
        True if origin coordinates are geodetic, False if they are geocentric.
        Will return coordinates in the same system as the origin input.
        (default=True)

    Returns
    -------
    lat_pnt : float
        Latitude of point in degrees
    lon_pnt : float
        Longitude of point in degrees
    rad_pnt : float
        Distance to the point from the centre of the Earth in km

    References
    ----------
    Based on J.M. Ruohoniemi's geopack and R.J. Barnes radar.pro

    """

    warnings.warn(' '.join(["coords.local_horizontal_to_global_geo is ",
                            "deprecated and will be removed in pysat 3.0.0.",
                            "This function will move to the new pysatMadrigal",
                            "package."]),
                  DeprecationWarning, stacklevel=2)

    # If the data are in geodetic coordiantes, convert to geocentric
    if geodetic:
        (glat, glon, rearth, gaz, gel) = \
            geodetic_to_geocentric_horizontal(lat_orig, lon_orig, az, el,
                                              inverse=False)
        grad = rearth + alt_orig
    else:
        glat = lat_orig
        glon = lon_orig
        grad = alt_orig + 6371.0  # Add the mean earth radius in km
        gaz = az
        gel = el

    # Convert from local horizontal to local cartesian coordiantes
    x_loc, y_loc, z_loc = spherical_to_cartesian(gaz, gel, dist, inverse=False)

    # Convert from local to global cartesian coordiantes
    x_glob, y_glob, z_glob = global_to_local_cartesian(x_loc, y_loc, z_loc,
                                                       glat, glon, grad,
                                                       inverse=True)

    # Convert from global cartesian to geocentric coordinates
    lon_pnt, lat_pnt, rad_pnt = spherical_to_cartesian(x_glob, y_glob, z_glob,
                                                       inverse=True)

    # Convert from geocentric to geodetic, if desired
    if geodetic:
        lat_pnt, lon_pnt, rearth = geodetic_to_geocentric(lat_pnt, lon_pnt,
                                                          inverse=True)
        rad_pnt = rearth + rad_pnt - 6371.0

    return lat_pnt, lon_pnt, rad_pnt
