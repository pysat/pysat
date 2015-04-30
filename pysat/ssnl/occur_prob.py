"""
Occurrence probability routines, daily or by orbit.
"""

import numpy as np

def daily2D(inst, bin1, label1, bin2, label2, data_label, gate, returnBins=False):
    """2D Daily Occurrence Probability of data_label > gate over a season.
    
    If data_label is greater than gate atleast once per day, 
    then a 100% occurrence probability results. Season delineated by 
    the bounds attached to Instrument object.

    Parameters
    ----------
    binx: list
        [min, max, number of bins]
    labelx: string 
        name for data product for binx
    data_label: list of strings 
        identifies data product(s) to calculate occurrence probability
        e.g. inst[data_label]
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence

    Returns
    -------
    Returns a dict with numpy arrays, 'prob' for the probability and
    'count' for the number of days with any data.'binx' and 'biny' are also
    returned if requested. Note that arrays are organized for direct 
    plotting, y values along rows, x along columns.
    
    """
    
    return _occurrence2D(inst, bin1, label1, bin2, label2, data_label, gate,
                        by_orbit=False, returnBins=returnBins)


def by_orbit2D(inst, bin1, label1, bin2, label2, data_label, gate, returnBins=False):
    """2D Occurrence Probability of data_label orbit-by-orbit over a season.
    
    If data_label is greater than gate atleast once per orbit, then a 
    100% occurrence probability results. Season delineated by the bounds
    attached to Instrument object.

    Parameters
    ----------
    binx: list
        [min value, max value, number of bins]
    labelx: string 
        identifies data product for binx
    data_label: list of strings 
        identifyies data product(s) to calculate occurrence probability
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence

    Returns
    -------
    Returns a dict with numpy arrays, 'prob' for the probability and
    'count' for the number of days with any data.'binx' and 'biny' are also
    returned if requested. Note that arrays are organized for direct 
    plotting, y values along rows, x along columns
    
    """
    
    return _occurrence2D(inst, bin1, label1, bin2, label2, data_label, gate,
                        by_orbit=True, returnBins=returnBins)

                                                                                                
def _occurrence2D(inst, bin1, label1, bin2, label2, data_label, gate, 
                by_orbit=False, returnBins=False):
    if not hasattr(data_label, '__iter__'):
        raise ValueError('Data label must be list-like group of variable names.')
    if not hasattr(gate, '__iter__'):
        raise ValueError('Gate levels must be list-like group of variable names.')
    if len(gate) != len(data_label):
        raise ValueError('Must have a gate value for each data_label')

    #create bins
    binx = np.linspace(bin1[0], bin1[1], bin1[2]+1)
    biny = np.linspace(bin2[0], bin2[1], bin2[2]+1)

    numx = len(binx)-1
    numy = len(biny)-1
    numz = len(data_label)

    # create arrays to store all values
    total = np.zeros((numz, numy, numx))
    hits = np.zeros((numz, numy, numx))
    if by_orbit:
        inst.load(date=inst.bounds[0][0])
        iterator = inst.orbits
    else:
        iterator = inst
    # do loop to iterate over given iterator
    for i,inst in enumerate(iterator):
        if len(inst.data) != 0:
            xind = np.digitize(inst.data[label1], binx)-1
            for xi in xrange(numx):
                xindex, = np.where(xind==xi)
                if len(xindex)>0:
                    yData = inst.data.ix[xindex]
                    yind = np.digitize(yData[label2], biny)-1
                    for yj in xrange(numy):
                        yindex, = np.where(yind==yj)
                        if len(yindex) > 0:
                            # iterate over the different data_labels
                            for zk in xrange(numz):
                                zdata = yData.ix[yindex,data_label[zk]]
                                idx, = np.where(np.isfinite(zdata))
                                if len(idx) > 0:
                                    total[zk,yj,xi] += 1.
                                    idx, = np.where( zdata > gate[zk]  )
                                    if len(idx) > 0:
                                        hits[zk,yj,xi] += 1.
                               
    # all of the loading and storing data is done
    # get probability
    prob = hits/total
    # make nicer dictionary output
    output = {}
    for i,label in enumerate(data_label):
        output[label] = {'prob': prob[i,:,:], 'count':total[i,:,:]}
        if returnBins:
            output[label]['binx'] = binx
            output[label]['biny'] = biny
    # clean up
    del iterator
    return output
        
        
def daily3D(inst, bin1, label1, bin2, label2, bin3, label3, 
            data_label, gate, returnBins=False):
    """3D Daily Occurrence Probability of data_label > gate over a season.
    
    If data_label is greater than gate atleast once per day, 
    then a 100% occurrence probability results. Season delineated by 
    the bounds attached to Instrument object.

    Parameters
    ----------
    binx: list
        [min, max, number of bins]
    labelx: string 
        name for data product for binx
    data_label: list of strings 
        identifies data product(s) to calculate occurrence probability
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence

    Returns
    -------
    Returns a dict with numpy arrays, 'prob' for the probability and
    'count' for the number of days with any data.'binx', 'biny', and 'binz'
    are also returned if requested. Note that arrays are organized for direct 
    plotting, z,y,x.
    
    """
        
    return _occurrence3D(inst, bin1, label1, bin2, label2, bin3, label3, 
                        data_label, gate, returnBins=returnBins, by_orbit=False)
           

def by_orbit3D(inst, bin1, label1, bin2, label2, bin3, label3, 
                data_label, gate, returnBins=False):
    """3D Occurrence Probability of data_label orbit-by-orbit over a season.
    
    If data_label is greater than gate atleast once per orbit, then a 
    100% occurrence probability results. Season delineated by the bounds
    attached to Instrument object.

    Parameters
    ----------
    binx: list
        [min value, max value, number of bins]
    labelx: string 
        identifies data product for binx
    data_label: list of strings 
        identifyies data product(s) to calculate occurrence probability
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence

    Returns
    -------
    Returns a dict with numpy arrays, 'prob' for the probability and
    'count' for the number of days with any data.'binx' and 'biny' are also
    returned if requested. Note that arrays are organized for direct 
    plotting, z,y,x
    
    """
        
    return _occurrence3D(inst, bin1, label1, bin2, label2, bin3, label3, 
                        data_label, gate, returnBins=returnBins, by_orbit=True)

                                     
                                                                                                               
def _occurrence3D(inst, start, stop, bin1, label1, bin2, label2, bin3, label3, 
                    data_label, gate, returnBins=False, by_orbit=False):

    if not hasattr(data_label, '__iter__'):
        raise ValueError('Data label must be list-like group of variable names.')
    if not hasattr(gate, '__iter__'):
        raise ValueError('Gate levels must be list-like group of variable names.')
    if len(gate) != len(data_label):
        raise ValueError('Must have a gate value for each data_label')

    #create bins
    binx = np.linspace(bin1[0], bin1[1], bin1[2]+1)
    biny = np.linspace(bin2[0], bin2[1], bin2[2]+1)
    binz = np.linspace(bin3[0], bin3[1], bin3[2]+1)

    numx = len(binx)-1
    numy = len(biny)-1
    numz = len(binz)-1
    numd = len(data_label)

    #create array to store all values before taking median
    yarr = np.arange(numy)
    xarr = np.arange(numx)
    zarr = np.arange(numz)
    darr = np.arange(numd)

    total = np.zeros((numd, numz, numy, numx))
    hits = np.zeros((numd, numz, numy, numx))

    if by_orbit:
        iterator = inst.orbits
    else:
        iterator = inst
    # do loop to iterate over given season
    for i,sat in enumerate(iterator):

        if len(sat.data) != 0:
            xind = np.digitize(sat.data[label1], binx)-1
            for xi in xarr:
                xindex, = np.where(xind==xi)
                if len(xindex)>0:
                    yData = sat.data.ix[xindex]
                    yind = np.digitize(yData[label2], biny)-1
                    for yj in yarr:
                        yindex, = np.where(yind==yj)
                        if len(yindex) > 0:
                            zData = yData.ix[yindex]
                            zind = np.digitize(zData[label3], binz)-1
                            for zk in zarr:
                                zindex, = np.where(zind==zk)
                                if len(zindex) > 0:
                                    for di in darr:
                                        ddata = zData.ix[zindex,data_label[di]]
                                        idx, = np.where(np.isfinite(ddata))
                                        if len(idx) > 0:
                                            total[di,zk,yj,xi] += 1
                                            idx, = np.where( ddata > gate[di]  )
                                            if len(idx) > 0:
                                                hits[di,zk,yj,xi] += 1
                                
                               
    #all of the loading and storing data is done
    #prob = np.zeros((numz, numy, numx))
    prob = hits/total

    # make nicer dictionary output
    output = {}
    for i,label in enumerate(data_label):
        output[label] = {'prob': prob[i,:,:,:], 'count':total[i,:,:,:]}
        if returnBins:
            output[label]['binx'] = binx
            output[label]['biny'] = biny
            output[label]['binz'] = biny
    # clean up
    del iterator
    return output    