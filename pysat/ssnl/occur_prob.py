from __future__ import print_function
from __future__ import absolute_import

"""Occurrence probability routines, daily or by orbit.

Routines calculate the occurrence of an event greater than a supplied gate
occuring at least once per day, or once per orbit. The probability is
calculated as the (number of times with at least one hit in bin)/(number
of times in the bin).The data used to determine the occurrence must be 1D. 
If a property of a 2D or higher dataset is needed attach a custom function 
that performs the check and returns a 1D Series.

Note
----
The included routines use the bounds attached to the supplied instrument 
object as the season of interest.

"""

import numpy as np

def daily2D(inst, bin1, label1, bin2, label2, data_label, gate, returnBins=False):
    """2D Daily Occurrence Probability of data_label > gate over a season.
    
    If data_label is greater than gate at least once per day, 
    then a 100% occurrence probability results.Season delineated by the bounds
    attached to Instrument object. 
    Prob = (# of times with at least one hit)/(# of times in bin)

    Parameters
    ----------
    inst: pysat.Instrument()
        Instrument to use for calculating occurrence probability
    binx: list
        [min, max, number of bins]
    labelx: string 
        name for data product for binx
    data_label: list of strings 
        identifies data product(s) to calculate occurrence probability
        e.g. inst[data_label]
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence
    returnBins: Boolean
        if True, return arrays with values of bin edges, useful for pcolor

    Returns
    -------
    occur_prob : dictionary
        A dict of dicts indexed by data_label. Each entry is dict with entries
        'prob' for the probability and 'count' for the number of days with any
        data; 'bin_x' and 'bin_y' are also returned if requested. Note that arrays
        are organized for direct plotting, y values along rows, x along columns.
    
    Note
    ----
    Season delineated by the bounds attached to Instrument object.
    
    """
    
    return _occurrence2D(inst, bin1, label1, bin2, label2, data_label, gate,
                        by_orbit=False, returnBins=returnBins)


def by_orbit2D(inst, bin1, label1, bin2, label2, data_label, gate, returnBins=False):
    """2D Occurrence Probability of data_label orbit-by-orbit over a season.
    
    If data_label is greater than gate atleast once per orbit, then a 
    100% occurrence probability results. Season delineated by the bounds
    attached to Instrument object.
    Prob = (# of times with at least one hit)/(# of times in bin)
    
    Parameters
    ----------
    inst: pysat.Instrument()
        Instrument to use for calculating occurrence probability
    binx: list
        [min value, max value, number of bins]
    labelx: string 
        identifies data product for binx
    data_label: list of strings 
        identifies data product(s) to calculate occurrence probability
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence
    returnBins: Boolean
        if True, return arrays with values of bin edges, useful for pcolor

    Returns
    -------
    occur_prob : dictionary
        A dict of dicts indexed by data_label. Each entry is dict with entries
        'prob' for the probability and 'count' for the number of orbits with any
        data; 'bin_x' and 'bin_y' are also returned if requested. Note that arrays
        are organized for direct plotting, y values along rows, x along columns.

    Note
    ----
    Season delineated by the bounds attached to Instrument object.
    
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
    arrx = np.arange(numx)
    arry = np.arange(numy)
    arrz = np.arange(numz)

    # create arrays to store all values
    total = np.zeros((numz, numy, numx))
    hits = np.zeros((numz, numy, numx))
    if by_orbit:
        inst.load(date=inst.bounds[0][0])
        iterator = inst.orbits
    else:
        iterator = inst

    for i,inst in enumerate(iterator):
        if len(inst.data) != 0:
            xind = np.digitize(inst.data[label1], binx)-1
            for xi in arrx:
                xindex, = np.where(xind==xi)
                if len(xindex)>0:
                    yData = inst.data.iloc[xindex]
                    yind = np.digitize(yData[label2], biny)-1
                    for yj in arry:
                        yindex, = np.where(yind==yj)
                        if len(yindex) > 0:
                            # iterate over the different data_labels
                            for zk in arrz:
                                zdata = yData.ix[yindex,data_label[zk]]
                                if np.any(np.isfinite(zdata)):    
                                    total[zk,yj,xi] += 1.
                                    if np.any(zdata > gate[zk]):
                                        hits[zk,yj,xi] += 1.
                               
    # all of the loading and storing data is done
    # get probability
    prob = hits/total
    # make nicer dictionary output
    output = {}
    for i,label in enumerate(data_label):
        output[label] = {'prob': prob[i,:,:], 'count':total[i,:,:]}
        if returnBins:
            output[label]['bin_x'] = binx
            output[label]['bin_y'] = biny
    # clean up
    del iterator
    return output
        
        
def daily3D(inst, bin1, label1, bin2, label2, bin3, label3, 
            data_label, gate, returnBins=False):
    """3D Daily Occurrence Probability of data_label > gate over a season.
    
    If data_label is greater than gate atleast once per day, 
    then a 100% occurrence probability results. Season delineated by 
    the bounds attached to Instrument object.
    Prob = (# of times with at least one hit)/(# of times in bin)

    Parameters
    ----------
    inst: pysat.Instrument()
        Instrument to use for calculating occurrence probability
    binx: list
        [min, max, number of bins]
    labelx: string 
        name for data product for binx
    data_label: list of strings 
        identifies data product(s) to calculate occurrence probability
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence
    returnBins: Boolean
        if True, return arrays with values of bin edges, useful for pcolor

    Returns
    -------
    occur_prob : dictionary
        A dict of dicts indexed by data_label. Each entry is dict with entries
        'prob' for the probability and 'count' for the number of days with any
        data; 'bin_x', 'bin_y', and 'bin_z' are also returned if requested. Note
        that arrays are organized for direct plotting, z,y,x.

    Note
    ----
    Season delineated by the bounds attached to Instrument object.    
            
    """
        
    return _occurrence3D(inst, bin1, label1, bin2, label2, bin3, label3, 
                        data_label, gate, returnBins=returnBins, by_orbit=False)
           

def by_orbit3D(inst, bin1, label1, bin2, label2, bin3, label3, 
                data_label, gate, returnBins=False):
    """3D Occurrence Probability of data_label orbit-by-orbit over a season.
    
    If data_label is greater than gate atleast once per orbit, then a 
    100% occurrence probability results. Season delineated by the bounds
    attached to Instrument object.
    Prob = (# of times with at least one hit)/(# of times in bin)

    Parameters
    ----------
    inst: pysat.Instrument()
        Instrument to use for calculating occurrence probability
    binx: list
        [min value, max value, number of bins]
    labelx: string 
        identifies data product for binx
    data_label: list of strings 
        identifies data product(s) to calculate occurrence probability
    gate: list of values 
        values that data_label must achieve to be counted as an occurrence
    returnBins: Boolean
        if True, return arrays with values of bin edges, useful for pcolor

    Returns
    -------
    occur_prob : dictionary
        A dict of dicts indexed by data_label. Each entry is dict with entries
        'prob' for the probability and 'count' for the number of orbits with any
        data; 'bin_x', 'bin_y', and 'bin_z' are also returned if requested. Note
        that arrays are organized for direct plotting, z,y,x.

    Note
    ----
    Season delineated by the bounds attached to Instrument object.    
            
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
            output[label]['bin_x'] = binx
            output[label]['bin_y'] = biny
            output[label]['bin_z'] = biny
    # clean up
    del iterator
    return output    