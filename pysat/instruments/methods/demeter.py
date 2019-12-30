# -*- coding: utf-8 -*-
"""Provides non-instrument routines for DEMETER microsatellite data"""

from __future__ import absolute_import, division, print_function

import numpy as np
import pysat

import logging
logger = logging.getLogger(__name__)


def download(date_array, tag, sat_id, data_path=None, user=None,
             password=None):
    """ Download

    """
    url = 'https://cdpp-archive.cnes.fr/'
    logger.info('Data must be downloaded by registered users at: {:s}'.format(url))
    return


def list_remote_files(tag, sat_id):
    """Lists files available for Demeter.

    Note
    ----
    Unfortunately, obtaining a list of remote files is not
    avilable for this instrument. This function is expected
    by pysat thus it is located here as a placeholder.

    Parameters
    ----------
    tag : (string or NoneType)
        Denotes type of file to load.  Accepted types are <tag strings>.
        (default=None)
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)

    """

    logger.info('Remote file lists are not supported for Demeter.')
    return


def bytes_to_float(chunk):
    """ Convert a chunk of bytes to a float

    Parameters
    ------------
    chunk : string or bytes
       A chunk of bytes

    Returns
    --------
    value : float
        A 32 bit float

    """
    import sys
    import struct
    import codecs

    chunk_code = codecs.encode(chunk, 'hex')

    if sys.version_info.major == 2:
        decoded = chunk_code.decode('hex')
    elif hasattr(chunk_code, "decode"):
        decoded = bytes.fromhex(chunk_code.decode('utf-8'))
    else:
        decoded = bytes.fromhex(chunk_code)

    return struct.unpack("!f", decoded)[0]


def load_general_header(fhandle):
    """ Load the general header block (block 1 for each time)

    Parameters
    ------------
    fhandle : (file handle)
        File handle

    Returns
    ----------
    data : list
        List of data values containing: P field,
        Number of days from 01/01/1950, number of miliseconds in the day,
        UT as datetime, Orbit number, downward (False) upward (True) indicator
    meta : dict
        Dictionary with meta data for keys: 'telemetry station',
        'software processing version', 'software processing subversion',
        'calibration file version', and 'calibration file subversion',
        'data names', 'data units'

    """
    import codecs  # ensures encode is python 2/3 compliant
    import datetime as dt

    block_size = 38  # Position block is 38 bytes
    chunk = fhandle.read(block_size)

    if len(chunk) != block_size:
        return list(), dict()

    # Extract UT timestamp for conversion into datetime object
    year = int(codecs.encode(chunk[8:10], 'hex'), 16)
    month = int(codecs.encode(chunk[10:12], 'hex'), 16)
    day = int(codecs.encode(chunk[12:14], 'hex'), 16)
    hour = int(codecs.encode(chunk[14:16], 'hex'), 16)
    minute = int(codecs.encode(chunk[16:18], 'hex'), 16)
    sec = int(codecs.encode(chunk[18:20], 'hex'), 16)
    microsec = int(codecs.encode(chunk[20:22], 'hex'), 16) * 1000
    dtime = dt.datetime(year, month, day, hour, minute, sec, microsec)

    data = [int(codecs.encode(chunk[:1], 'hex'), 16),  # P field
            int(codecs.encode(chunk[1:4], 'hex'), 16),  # Days since 1/1/1950
            int(codecs.encode(chunk[4:8], 'hex'), 16),  # Millisec in day
            dtime,  # UT timestamp
            int(codecs.encode(chunk[22:24], 'hex'), 16),  # Orbit number
            bool(int(codecs.encode(chunk[24:26], 'hex'), 16))]  # Orbit type

    meta = {'telemetry station': chunk[26:34],
            'software processing version': int(codecs.encode(chunk[34:35],
                                                             'hex'), 16),
            'software processing subversion': int(codecs.encode(chunk[35:36],
                                                                'hex'), 16),
            'calibration file version': int(codecs.encode(chunk[36:37], 'hex'),
                                            16),
            'calibration file subversion': int(codecs.encode(chunk[37:38],
                                                             'hex'), 16),
            'data names': ['P_field', 'epoch_time', 'time_of_day', 'UT',
                           'orbit_number', 'orbit_type'],
            'data units': {'P_field': 'N/A',
                           'epoch_time': 'days since 1/1/1950',
                           'time_of_day': 'ms', 'UT': 'datetime',
                           'orbit_number': 'N/A', 'orbit_type': 'N/A'}}

    return data, meta


def load_location_parameters(fhandle):
    """ Load the orbital and geomagnetic parameter block (block 1 for each
    time)

    Parameters
    ------------
    fhandle : (file handle)
        File handle

    Returns
    ----------
    data : list
        List of data values containing: geoc lat, geoc lon, alt, lt, geom
        lat, geom lon, mlt, inv lat, L-shell, geoc lat of conj point, geoc
        lon of conj point, geoc lat of N conj point at 110 km, geoc lon of
        N conj point at 110 km, geoc lat of S conj point at 110 km, geoc
        lon of S conj point at 110 km, components of magnetic field at sat
        point, proton gyrofreq at sat point, solar position in geog coords
    meta : dict
        Dictionary with meta data for keys: 'software processing version',
        'software processing subversion', 'data names', 'data units'

    """
    import codecs  # ensures encode is python 2/3 compliant

    block_size = 90  # Position block is 90 bytes
    chunk = fhandle.read(block_size)

    if len(chunk) != block_size:
        return list(), dict()

    data = [bytes_to_float(chunk[0:4]),  # geocentric latitude
            bytes_to_float(chunk[4:8]),  # geocentric longitude
            bytes_to_float(chunk[8:12]),  # altitude
            bytes_to_float(chunk[12:16]),  # LT hours of day
            bytes_to_float(chunk[16:20]),  # geomagnetic latitude
            bytes_to_float(chunk[20:24]),  # geomagnetic longitude
            bytes_to_float(chunk[24:28]),  # MLT in hours
            bytes_to_float(chunk[28:32]),  # invariant latitude
            bytes_to_float(chunk[32:36]),  # Mc Ilwain parameter L
            bytes_to_float(chunk[36:40]),  # geocentric latitude of conj point
            bytes_to_float(chunk[40:44]),  # geocentric longitude of conj point
            bytes_to_float(chunk[44:48]),  # geoc lat of N conj point at 110 km
            bytes_to_float(chunk[48:52]),  # geoc lon of N conj point at 110 km
            bytes_to_float(chunk[52:56]),  # geoc lat of S conj point at 110 km
            bytes_to_float(chunk[56:60]),  # geoc lon of S conj point at 110 km
            bytes_to_float(chunk[60:64]),  # mag field component at sat point
            bytes_to_float(chunk[64:68]),  # mag field component at sat point
            bytes_to_float(chunk[68:72]),  # mag field component at sat point
            bytes_to_float(chunk[72:76]),  # Proton gyrofrequency at sat oint
            bytes_to_float(chunk[76:80]),  # Xs in geographic coordinate system
            bytes_to_float(chunk[80:84]),  # Ys in geographic coordinate system
            bytes_to_float(chunk[84:88])]  # Zs in geographic coordinate system

    meta = {'software processing version': int(codecs.encode(chunk[88:89],
                                                             'hex'), 16),
            'software processing subversion': int(codecs.encode(chunk[89:90],
                                                                'hex'), 16),
            'data names': ['glat', 'glon', 'altitude', 'LT', 'mlat', 'mlon',
                           'MLT', 'ilat', 'L', 'glat_conj', 'glon_conj',
                           'glat_conj_N_110km', 'glon_conj_N_110km',
                           'glat_conj_S_110km', 'glon_conj_S_110km',
                           'mag_comp_1', 'mag_comp_2', 'mag_comp_3',
                           'proton_gyrofreq', 'Xs', 'Ys', 'Zs'],
            'data units': {'glat': 'degrees',
                           'glon': 'degrees',
                           'altitude': 'km',
                           'LT': 'h',
                           'mlat': 'degrees',
                           'mlon': 'degrees',
                           'MLT': 'h',
                           'ilat': 'degrees',
                           'L': 'Earth_Radii',
                           'glat_conj': 'degrees',
                           'glon_conj': 'degrees',
                           'glat_conj_N_110km': 'degrees',
                           'glon_conj_N_110km': 'degrees',
                           'glat_conj_S_110km': 'degrees',
                           'glon_conj_S_110km': 'degrees',
                           'mag_comp_1': 'nT',
                           'mag_comp_2': 'nT',
                           'mag_comp_3': 'nT',
                           'proton_gyrofreq': 'Hz',
                           'Xs': 'N/A',
                           'Ys': 'N/A',
                           'Zs': 'N/A'}}

    return data, meta


def load_attitude_parameters(fhandle):
    """ Load the attitude parameter block (block 1 for each time)

    Parameters
    ------------
    fhandle : (file handle)
        File handle

    Returns
    ----------
    data : list
        list of data values containing: matrix elements from satellite coord
        system to geographic coordinate system, matrix elements from geographic
        coordinate system to local geomagnetic coordinate system, quality
        index of attitude parameters.
    meta : dict
        Dictionary with meta data for keys: 'software processing version',
        'software processing subversion', 'data names', 'data units'

    """
    import codecs  # ensures encode is python 2/3 compliant

    block_size = 76  # Position block is 76 bytes
    chunk = fhandle.read(block_size)
    data = list()

    if len(chunk) != block_size:
        return data, dict()

    i = 0
    j = 1
    k = 1
    data_names = list()
    data_units = dict()
    while i < 72:
        data.append(bytes_to_float(chunk[i:i+4]))  # Matrix element

        # Save data name and units
        data_names.append("{:s}_{:d}{:d}".format("sat2geo" if i <= 32
                                                 else "geo2lgm", j, k))
        data_units[data_names[-1]] = 'unitless'

        # Cycle to next chunk of data
        i += 4

        # Determine the next matrix index
        if k == 3:
            k = 1
            j = j + 1 if j < 3 else 1
        else:
            k += 1

    # Save quality flag
    data.append(int(codecs.encode(chunk[72:74], 'hex'), 16))
    data_names.append('attitude_flag')
    data_units[data_names[-1]] = 'unitless'

    meta = {'software processing version': int(codecs.encode(chunk[74:75],
                                                             'hex'), 16),
            'software processing subversion': int(codecs.encode(chunk[75:76],
                                                                'hex'), 16),
            'data names': data_names, 'data units': data_units}

    return data, meta


def load_binary_file(fname, load_experiment_data):
    """ Load the binary data from a DEMETER file

    Parameters
    ------------
    fname : string
        Filename
    load_experiment_data : function
        Function to load experiment data, taking the file handle as input

    Returns
    ----------
    data : np.array
        Data from file stored in a numpy array
    meta : dict
        Meta data for file, including data names and units
    """

    data = list()
    meta = dict()

    with open(fname, "rb") as f:
        # Cycle through teach time, which consists of four blocks
        gdata, meta = load_general_header(f)

        while len(gdata) > 0:
            ldata, lmeta = load_location_parameters(f)
            adata, ameta = load_attitude_parameters(f)
            edata, emeta = load_experiment_data(f)

            # Combine and save the meta data
            if len(data) == 0:
                meta['data names'].extend(lmeta['data names'])
                meta['data units'].update(lmeta['data units'])
                meta['data names'].extend(ameta['data names'])
                meta['data units'].update(ameta['data units'])

                for ekey in emeta.keys():
                    if ekey == 'data names':
                        meta[ekey].extend(emeta[ekey])
                    elif ekey == 'data units':
                        meta[ekey].update(emeta[ekey])
                    else:
                        meta[ekey] = emeta[ekey]

            # Combine and save the data
            gdata.extend(ldata)
            gdata.extend(adata)
            gdata.extend(edata)
            data.append(gdata)

            # Cycle to the next time chunk
            gdata, _ = load_general_header(f)

        # Having read the file, close file handle and recast the data
        f.close()
        data = np.array(data)

    return data, meta


def set_metadata(name, meta_dict):
    """ Set metadata for each DEMETER instrument, using dict containing
    metadata

    Parameters
    ------------
    name : string
        DEMETER instrument name
    meta_dict : dict
        Dictionary containing metadata information and data attributes.  Data
        attributes are available in the keys 'data names' and 'data units'

    Returns
    ----------
    meta : pysat.Meta
        Meta class boject

    """

    # Define the acknowledgements and references
    ackn = {'iap': ' '.join(["This work is based on observations with the",
                             "plasma analyser IAP embarked on the satellite",
                             "DEMETER launched by CNES (Centre National",
                             "d'Etudes Spatiales). The author thanks J.J.",
                             "Berthelier the PI of this instrument for the use",
                             "of the data, and CDPP (Centre des Données de la",
                             "Physique des Plasmas) for the provision of these",
                             "data."]),
            'ice': ' '.join(["This work is based on observations with the",
                             "electric field instrument ICE embarked on the",
                             "satellite DEMETER launched by CNES (Centre",
                             "National d'Etudes Spatiales). The author thanks",
                             "J.J. Berthelier the PI of this instrument for",
                             "the use of the data, and CDPP (Centre des",
                             "Données de la Physique des Plasmas) for the",
                             "provision of these data."]),
            'imsc': ' '.join(["This work is based on observations with the",
                              "magnetic field instrument IMSC embarked on the",
                              "satellite DEMETER launched by CNES (Centre",
                              "National d'Etudes Spatiales). The author thanks",
                              "M. Parrot the PI of this instrument for the use",
                              "of the data, and CDPP (Centre des Données de la",
                              "Physique des Plasmas) for the provision of",
                              "these data."]),
            'rnf': ' '.join(["This work is based on observations with the",
                             "neural network RNF embarked on the satellite",
                             "DEMETER launched by CNES (Centre National",
                             "d'Etudes Spatiales). The author thanks J.L.",
                             "Pinçon the PI of this instrument for the use",
                             "of the data, and CDPP (Centre des Données de",
                             "la Physique des Plasmas) for the provision of",
                             "these data."]),
            'idp': ' '.join(["This work is based on observations with the",
                             "particle spectrometer instrument IDP embarked on",
                             "the satellite DEMETER launched by CNES (Centre",
                             "National d'Etudes Spatiales). The author thanks",
                             "J.A. Sauvaud the PI of this instrument for the",
                             "use of the data, and CDPP (Centre des Données",
                             "de la Physique des Plasmas) for the provision of",
                             "these data."]),
            'isl': ' '.join(["This work is based on observations with the",
                             "Langmuir probe ISL embarked on the satellite",
                             "DEMETER launched by CNES (Centre National",
                             "d'Etudes Spatiales). The author thanks J.P.",
                             "Lebreton the PI of this instrument for the use",
                             "of the data, and CDPP (Centre des Données de la",
                             "Physique des Plasmas) for the provision of these",
                             "data."])}

    refs = {'iap': ' '.join(['Berthelier at al., 2006. IAP, the thermal plasma',
                             'analyzer on DEMETER, Planet. and Space Sci.,',
                             '54(5), pp 487-501.'])}

    if name not in refs.keys():
        refs[name] = 'Instrument reference information available at ' + \
            'https://demeter.cnes.fr/en/DEMETER/A_publications.htm'

    # Define the long-form names for non-instrument specific data
    long_name = {'P_field': 'P field',
                 'epoch_time': 'Number of days from 01/01/1950',
                 'time_of_day': 'Number of milliseconds in the day',
                 'UT': 'Universal Time of the first point of the data array',
                 'orbit_number': 'Orbit number',
                 'orbit_type': 'Sub-orbit type: False=downward, True=upward',
                 'glat': 'Geocentric Latitude',
                 'glon': 'Geocentric Longitude',
                 'altitude': 'Altitude',
                 'LT': 'Local Time',
                 'mlat': 'Geomagnetic Latitude',
                 'mlon': 'Geomagnetic Longitude',
                 'MLT': 'Magnetic Local Time',
                 'ilat': 'Invarient Latitude',
                 'L': 'Mc Ilwain Parameter L',
                 'glat_conj': ' '.join(['Geocentric latitude of the conjugate',
                                        'point at the satellite altitude']),
                 'glon_conj': ' '.join(['Geocentric longitude of the conjugate',
                                        'point at the satellite altitude']),
                 'glat_conj_N_110km': ' '.join(['Geocentric latitude of North',
                                                'conjugate point at altitude',
                                                '110 km']),
                 'glon_conj_N_110km': ' '.join(['Geocentric longitude of North',
                                                'conjugate point at altitude',
                                                '110 km']),
                 'glat_conj_S_110km': ' '.join(['Geocentric latitude of South',
                                                'conjugate point at altitude',
                                                '110 km']),
                 'glon_conj_S_110km': ' '.join(['Geocentric longitude of South',
                                                'conjugate point at altitude',
                                                '110 km']),
                 'mag_comp_1': ' '.join(['Component of the magnetic field',
                                         'model at the satellite point']),
                 'mag_comp_2': ' '.join(['Component of the magnetic field',
                                         'model at the satellite point']),
                 'mag_comp_3': ' '.join(['Component of the magnetic field',
                                         'model at the satellite point']),
                 'proton_gyrofreq': 'Proton gyrofrequency at satellite point',
                 'Xs': 'Solar position in geographic coordinate system',
                 'Ys': 'Solar position in geographic coordinate system',
                 'Zs': 'Solar position in geographic coordinate system',
                 'sat2geo_11': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_12': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_13': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_21': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_22': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_23': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_31': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_32': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'sat2geo_33': ' '.join(['Conversion matrix from satellite to',
                                         'geographic coordinate system']),
                 'geo2lgm_11': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_12': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_13': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_21': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_22': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_23': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_31': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_32': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'geo2lgm_33': ' '.join(['Conversion matrix from geographic to',
                                         'geomagnetic coordinate system']),
                 'attitude_flag': 'Quality index of attitude parameters',
                 'status_flag_00': 'Housekeeping and status',
                 'status_flag_01': 'Housekeeping and status',
                 'status_flag_02': 'Housekeeping and status',
                 'status_flag_03': 'Housekeeping and status',
                 'status_flag_04': 'Housekeeping and status',
                 'status_flag_05': 'Housekeeping and status',
                 'status_flag_06': 'Housekeeping and status',
                 'status_flag_07': 'Housekeeping and status',
                 'status_flag_08': 'Housekeeping and status',
                 'status_flag_09': 'Housekeeping and status',
                 'status_flag_10': 'Housekeeping and status',
                 'status_flag_11': 'Housekeeping and status',
                 'status_flag_12': 'Housekeeping and status',
                 'status_flag_13': 'Housekeeping and status',
                 'status_flag_14': 'Housekeeping and status',
                 'status_flag_15': 'Housekeeping and status',
                 'status_flag_16': 'Housekeeping and status',
                 'status_flag_17': 'Housekeeping and status',
                 'status_flag_18': 'Housekeeping and status',
                 'status_flag_19': 'Housekeeping and status',
                 'status_flag_20': 'Housekeeping and status',
                 'status_flag_21': 'Housekeeping and status',
                 'status_flag_22': 'Housekeeping and status',
                 'status_flag_23': 'Housekeeping and status',
                 'status_flag_24': 'Housekeeping and status',
                 'status_flag_25': 'Housekeeping and status',
                 'status_flag_26': 'Housekeeping and status',
                 'status_flag_27': 'Housekeeping and status',
                 'status_flag_28': 'Housekeeping and status',
                 'status_flag_29': 'Housekeeping and status',
                 'status_flag_30': 'Housekeeping and status',
                 'status_flag_31': 'Housekeeping and status', }
    long_inst = {'iap': {'time_resolution': 'Time resolution',
                         'H+_density': 'H+ density',
                         'He+_density': 'He+ density',
                         'O+_density': 'O+ density',
                         'Ion_temperature': 'Ion temperature',
                         'iv_Oz': 'Ion velocity along the satellite z axis',
                         'iv_negOz_angle': ' '.join(['Angle between the ion',
                                                     'velocity and -z axis',
                                                     '(ram direction) of',
                                                     'satellite']),
                         'iv_xOy_Ox_angle': ' '.join(['Angle between',
                                                      'projection of the ion',
                                                      'velocity on the x-y',
                                                      'plane and satellite',
                                                      'x axis']),
                         'satellite_potential': 'Satellite potential'}}

    if name not in long_inst.keys():
        logger.warning('no long-form names available for {:s}'.format(name))

        long_inst[name] = {nn: nn for nn in meta_dict['data names']}

    # Initialise the meta data
    meta = pysat.Meta()
    for cc in meta_dict['data names']:
        # Determine the long instrument name
        if cc in long_inst[name].keys():
            ll = long_inst[name][cc]
        else:
            ll = long_name[cc]

        # Assign the data units, long names, acknowledgements, and references
        meta[cc] = {'units': meta_dict['data units'][cc], 'long_name': ll}

    # Set the remaining metadata
    meta_dict['acknowledgements'] = ackn[name]
    meta_dict['reference'] = refs[name]
    mkeys = list(meta_dict.keys())
    mkeys.pop(mkeys.index('data names'))
    mkeys.pop(mkeys.index('data units'))

    meta.info = {cc: meta_dict[cc] for cc in mkeys}

    return meta
