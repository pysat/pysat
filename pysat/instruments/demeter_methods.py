# -*- coding: utf-8 -*-
"""Provides non-instrument routines for DEMETER microsatellite data"""

from __future__ import absolute_import, division, print_function

import pandas as pds
import numpy as np
import pysat
import sys

def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    """ Download 

    """
    url = 'https://cdpp-archive.cnes.fr/'
    print('Data must be downloaded by registered users at: {:s}'.format(url))
    raise RuntimeError('not written yet')

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

    if sys.version_info.major == 2:
        decoded = codecs.encode(chunk, 'hex').decode('hex')
    else:
        decoded = bytes.fromhex(codecs.encode(chunk, 'hex'))

    return struct.unpack("!f", decoded)

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
    import codecs # ensures encode is python 2/3 compliant
    import datetime as dt

    block_size = 38 # Position block is 38 bytes
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

    data = [int(codecs.encode(chunk[0], 'hex'), 16), # P field
            int(codecs.encode(chunk[1:4], 'hex'), 16), # Days since 1/1/1950
            int(codecs.encode(chunk[4:8], 'hex'), 16), # Millisec in day
            dtime, # UT timestamp
            int(codecs.encode(chunk[22:24], 'hex'), 16), # Orbit number
            bool(int(codecs.encode(chunk[24:26], 'hex'), 16))] # Orbit type

    meta = {'telemetry station':chunk[26:34],
            'software processing version':int(codecs.encode(chunk[34], 'hex'),
                                              16),
            'software processing subversion':int(codecs.encode(chunk[35],
                                                               'hex'), 16),
            'calibration file version':int(codecs.encode(chunk[36], 'hex'), 16),
            'calibration file subversion':int(codecs.encode(chunk[37], 'hex'),
                                              16),
            'data names':['P_field', 'epoch_time', 'time_of_day', 'UT',
                          'orbit_number', 'orbit_type'],
            'data units':{'P_field':'N/A', 'epoch_time':'days since 1/1/1950',
                          'time_of_day':'ms', 'UT':'datetime',
                          'orbit_number':'N/A', 'orbit_type':'N/A'}}

    return data, meta

def load_location_parameters(fhandle):
    """ Load the orbital and geomagnetic parameter block (block 1 for each time)

    Parameters
    ------------
    fhandle : (file handle)
        File handle

    Returns
    ----------
    data : list
        List of data values containing: geoc lat, geoc lon, alt, lt, geom lat,
        geom lon, mlt, inv lat, L-shell, geoc lat of conj point, geoc lon of
        conj point, geoc lat of N conj point at 110 km, geoc lon of N conj point
        at 110 km, geoc lat of S conj point at 110 km, geoc lon of S conj point
        at 110 km, components of magnetic field at sat point, proton gyrofreq
        at sat point, solar position in geog coords
    meta : dict
        Dictionary with meta data for keys: 'software processing version',
        'software processing subversion', 'data names', 'data units'

    """
    import codecs # ensures encode is python 2/3 compliant

    block_size = 90 # Position block is 90 bytes
    chunk = fhandle.read(block_size)

    if len(chunk) != block_size:
        return list(), dict()

    data = [bytes_to_float(chunk[0:4]), # geocentric latitude
            bytes_to_float(chunk[4:8]), # geocentric longitude
            bytes_to_float(chunk[8:12]), # altitude
            bytes_to_float(chunk[12:16]), # LT hours of day
            bytes_to_float(chunk[16:20]), # geomagnetic latitude
            bytes_to_float(chunk[20:24]), # geomagnetic longitude
            bytes_to_float(chunk[24:28]), # MLT in hours
            bytes_to_float(chunk[28:32]), # invariant latitude
            bytes_to_float(chunk[32:36]), # Mc Ilwain parameter L
            bytes_to_float(chunk[36:40]), # geocentric latitude of conj point
            bytes_to_float(chunk[40:44]), # geocentric longitude of conj point
            bytes_to_float(chunk[44:48]), # geoc lat of N conj point at 110 km
            bytes_to_float(chunk[48:52]), # geoc lon of N conj point at 110 km
            bytes_to_float(chunk[52:56]), # geoc lat of S conj point at 110 km
            bytes_to_float(chunk[56:60]), # geoc lon of S conj point at 110 km
            bytes_to_float(chunk[60:64]), # mag field component at sat point
            bytes_to_float(chunk[64:68]), # mag field component at sat point
            bytes_to_float(chunk[68:72]), # mag field component at sat point
            bytes_to_float(chunk[72:76]), # Proton gyrofrequency at sat oint
            bytes_to_float(chunk[76:80]), # Xs in geographic coordinate system
            bytes_to_float(chunk[80:84]), # Ys in geographic coordinate system
            bytes_to_float(chunk[84:88])] # Zs in geographic coordinate system

    meta = {'software processing version':int(codecs.encode(chunk[88], 'hex'),
                                              16),
            'software processing subversion':int(codecs.encode(chunk[89],
                                                               'hex'), 16),
            'data names':['glat', 'glon', 'altitude', 'LT', 'mlat', 'mlon',
                          'MLT', 'ilat', 'L', 'glat_conj', 'glon_conj',
                          'glat_conj_N_110km', 'glon_conj_N_110km',
                          'glat_conj_S_110km', 'glon_conj_S_110km',
                          'mag_comp_1', 'mag_comp_2', 'mag_comp_3',
                          'proton_gyrofreq', 'Xs', 'Ys', 'Zs'],
            'data units':{'glat':'degrees', 'glon':'degrees', 'altitude':'km',
                          'LT':'h', 'mlat':'degrees', 'mlon':'degrees',
                          'MLT':'h', 'ilat':'degrees', 'L':'Earth_Radii',
                          'glat_conj':'degrees', 'glon_conj':'degrees',
                          'glat_conj_N_110km':'degrees',
                          'glon_conj_N_110km':'degrees',
                          'glat_conj_S_110km':'degrees',
                          'glon_conj_S_110km':'degrees', 'mag_comp_1':'nT',
                          'mag_comp_2':'nT', 'mag_comp_3':'nT',
                          'proton_gyrofreq':'Hz', 'Xs':'N/A', 'Ys':'N/A',
                          'Zs':'N/A'}}

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
    import codecs # ensures encode is python 2/3 compliant

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
        data.append(bytes_to_float(chunk[i:i+4])) # Matrix element

        # Save data name and units
        data_names("{:s}_{:d}{:d}".format("sat2geo" if i <= 32 else "geo2lgm",
                                          j, k))
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

    meta = {'software processing version':int(codecs.encode(chunk[74], 'hex'),
                                              16),
            'software processing subversion':int(codecs.encode(chunk[75],
                                                               'hex'), 16),
            'data names':data_names, 'data units':data_units}

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
                        data_unit[ekey] = emeta[ekey]

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
