from __future__ import print_function
from __future__ import absolute_import

import functools

import numpy as np
import pandas as pds
from pysat import Series, DataFrame


def extract_modelled_observations(inst=None, model=None, inst_name=[],
                                  mod_name=[], mod_datetime_name=None,
                                  mod_time_name=None, mod_units=[],
                                  sel_name=None, method='linear',
                                  model_label='model'):
    """Extracts instrument-aligned data from a modelled data set

    Parameters
    ----------
    inst : pysat.Instrument instance
        instrument object for which modelled data will be extracted
    model : xarray Dataset
        modelled data set
    inst_name : list of strings
        list of names of the data series to use for determing instrument
        location
    mod_name : list of strings
        list of names of the data series to use for determing model locations
        in the same order as inst_name.  These must make up a regular grid.
    mod_datetime_name : string
        Name of the data series in the model Dataset containing datetime info
    mod_time_name : string
        Name of the time coordinate in the model Dataset
    mod_units : list of strings
        units for each of the mod_name location attributes.  Currently
        supports: rad/radian(s), deg/degree(s), h/hr(s)/hour(s), m, km, and cm 
    sel_name : list of strings or NoneType
        list of names of modelled data indices to append to instrument object,
        or None to append all modelled data (default=None)
    method : string
        Interpolation method.  Supported are 'linear', 'nearest', and
        'splinef2d'.  The last is only supported for 2D data and is not
        recommended here.  (default='linear')
    model_label : string
        name of model, used to identify interpolated data values in instrument
        (default="model")

    Returns
    -------
    Adds modelled data to the instrument

    Notes
    --------
    For best results, select clean instrument data after alignment with model

    """
    from scipy import interpolate

    # Test input
    if inst is None:
        raise ValueError('Must provide a pysat instrument object')

    if model is None:
        raise ValueError('Must provide modelled data')

    if mod_datetime_name is None:
        raise ValueError('Need datetime key for model datasets')

    if mod_time_name is None:
        raise ValueError('Need time coordinate name for model datasets')

    if len(inst_name) == 0:
        estr = 'Must provide instrument location attribute names as a list'
        raise ValueError(estr)

    if len(inst_name) != len(mod_name):
        estr = 'Must provide the same number of instrument and model '
        estr += 'location attribute names as a list'
        raise ValueError(estr)

    if len(mod_name) != len(mod_units):
        raise ValueError('Must provide units for each model location attribute')

    inst_scale = np.ones(shape=len(inst_name), dtype=float)
    for i,ii in enumerate(inst_name):
        if not ii in list(inst.data.keys()):
            raise ValueError('Unknown instrument location index {:}'.format(ii))
        inst_scale[i] = scale_units(mod_units[i], inst.meta.data.units[ii])

    # Determine which data to interpolate and initialize the interpolated output
    if sel_name is None:
        sel_name = list(model.data_vars.keys())

    for mi in mod_name:
        if mi in sel_name:
            sel_name.pop(sel_name.index(mi))

    # Determine the model time resolution
    tm_sec = (np.array(model.data_vars[mod_datetime_name][1:]) -
              np.array(model.data_vars[mod_datetime_name][:-1])).min()
    tm_sec /= np.timedelta64(1, 's')
    ti_sec = (inst.data.index[1:] - inst.data.index[:-1]).min().total_seconds()
    min_del = tm_sec if tm_sec < ti_sec else ti_sec

    # Determine which instrument observations are within the model time
    # resolution of a model run
    mind = list()
    iind = list()
    for i,tt in enumerate(np.array(model.data_vars[mod_datetime_name])):
        del_sec = abs(tt - inst.data.index).total_seconds()
        if del_sec.min() < min_del:
            iind.append(del_sec.argmin())
            mind.append(i)

    # Determine the model coordinates closest to the satellite track
    interp_data = dict()
    inst_coord = {kk:getattr(inst.data, inst_name[i]) * inst_scale[i]
                  for i,kk in enumerate(mod_name)}
    for i,ii in enumerate(iind):
        # Cycle through each model data type, since it may not depend on
        # all the dimensions
        for mdat in sel_name:
            # Determine the dimension values
            dims = list(model.data_vars[mdat].dims)
            ndim = model.data_vars[mdat].data.shape
            indices = tuple([mind[i] if kk == mod_time_name
                             else slice(0,ndim[k]) for k,kk in enumerate(dims)])

            # Construct the data needed for interpolation
            points = [model.coords[kk].data for kk in dims if kk in mod_name]

            if len(points) > 0:
                xi = [inst_coord[kk][ii] for kk in dims if kk in mod_name]
                values = model.data_vars[mdat].data[indices]

                # Interpolate the desired value
                yi = interpolate.interpn(points, values, xi, method=method)

                # Save the output
                attr_name = "{:s}_{:s}".format(model_label, mdat)
                if not attr_name in interp_data.keys():
                    interp_data[attr_name] = \
                        np.empty(shape=inst.data.index.shape,
                                 dtype=float) * np.nan
                interp_data[attr_name][ii] = yi[0]

    # Update the instrument object
    for mdat in interp_data.keys():
        inst[mdat] = pds.Series(interp_data[mdat], index=inst.data.index)

    return

def scale_units(out_unit, in_unit):
    """ Determine the scaling factor between two units

    Parameters
    -------------
    out_unit : str
        Desired unit after scaling
    in_unit : str
        Unit to be scaled

    Returns
    -----------
    unit_scale : float
        Scaling factor that will convert from in_units to out_units

    Notes
    -------
    Accepted units include degrees ('deg', 'degree', 'degrees'),
    radians ('rad', 'radian', 'radians'),
    hours ('h', 'hr', 'hrs', 'hour', 'hours'), and lengths ('m', 'km', 'cm').
    Can convert between degrees, radians, and hours or different lengths.

    Example
    -----------
    ::
    import numpy as np
    two_pi = 2.0 * np.pi
    scale = scale_units("deg", "RAD")
    two_pi *= scale
    two_pi # will show 360.0


    """

    accepted_units = {'deg':['deg', 'degree', 'degrees'],
                      'rad':['rad', 'radian', 'radians'],
                      'h':['h', 'hr', 'hrs', 'hours'],
                      'm':['m', 'km', 'cm'],
                      'm/s':['m/s', 'cm/s', 'km/s']}

    scales = {'deg':180.0, 'rad':np.pi, 'h':12.0,
              'm':1.0, 'km':0.001, 'cm':100.0,
              'm/s':1.0, 'cm/s':100.0, 'km/s':0.001}

    # Test input and determine transformation type
    out_key = None
    in_key = None
    for kk in accepted_units.keys():
        if out_unit.lower() in accepted_units[kk]:
            out_key = kk
        if in_unit.lower() in accepted_units[kk]:
            in_key = kk
    
    if out_key is None:
        raise ValueError('Unknown output unit {:}'.format(out_unit))
    
    if in_key is None:
        raise ValueError('Unknown input unit {:}'.format(in_unit))

    if out_key == 'm' or out_key == 'm/s':
        if in_key != out_key:
            raise ValueError('Cannot scale {:s} and {:s}'.format(out_unit,
                                                                 in_unit))
        unit_scale = scales[out_unit.lower()] / scales[in_unit.lower()]
    else:
        if in_key == 'm':
            raise ValueError('Cannot scale {:s} and {:s}'.format(out_unit,
                                                                 in_unit))
        unit_scale = scales[out_key] / scales[in_key]

    return unit_scale

    
